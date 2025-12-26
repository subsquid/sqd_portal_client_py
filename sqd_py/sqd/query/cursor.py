import asyncio
from logging import getLogger
from typing import Any, AsyncIterator, Dict, Optional, Tuple, Union

from tqdm import tqdm

import aiohttp

from ..transport import stream_query_output_async
from ..utils import create_session

logger = getLogger(__name__)


class QueryCursor(AsyncIterator[Dict[str, Any]]):
    """Async iterator that streams query results from the SQD portal.

    Handles pagination automatically - continues fetching until to_block is reached
    or no more data is available. Fetches ahead in a background task, optionally
    using parallel workers if shards > 1 and to_block is set.
    """

    def __init__(
        self,
        query: "BaseSQDQuery",
        *,
        session: Optional[aiohttp.ClientSession] = None,
        show_progress: bool = False,
        shards: int = 1,
    ) -> None:
        self._query = query
        self._session = session
        self._owns_session = session is None
        self._show_progress = show_progress and tqdm is not None
        self._shards = shards

        # State
        self._current_from_block: int = query.from_block
        self._last_block_number: Optional[int] = None
        self._finished = False
        self._headers: Dict[str, str] = {}

        # Progress bar
        self._pbar: Optional[tqdm] = None

        # Background fetching
        self._queue: asyncio.Queue[
            Union[Tuple[Dict[str, Any], Dict[str, str]], Exception, None]
        ] = asyncio.Queue(maxsize=2000)
        self._worker_task: Optional[asyncio.Task] = None

    def __aiter__(self) -> "QueryCursor":
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._fetch_loop())
        return self

    async def __anext__(self) -> Dict[str, Any]:
        if self._worker_task is None:
            # Just in case __anext__ called without __aiter__
            self._worker_task = asyncio.create_task(self._fetch_loop())

        try:
            item_or_error = await self._queue.get()
        except (asyncio.CancelledError, KeyboardInterrupt):
            await self._graceful_shutdown()
            raise

        if item_or_error is None:
            await self.close()
            raise StopAsyncIteration

        if isinstance(item_or_error, Exception):
            await self.close()
            raise item_or_error

        item, headers = item_or_error
        self._headers = headers
        return item

    async def _fetch_loop(self) -> None:
        """Background task to fetch items and put them in the queue."""
        try:
            if self._session is None:
                self._session = create_session()

            # Determine effective to_block
            effective_to_block = self._query.to_block

            if self._shards > 1 and effective_to_block is None:
                # Probe to get head block number
                effective_to_block = await self._probe_head_block()
                if effective_to_block is not None:
                    logger.info("Discovered head block: %d", effective_to_block)
                else:
                    logger.warning(
                        "Could not discover head block. Falling back to single worker."
                    )

            # Now initialize progress bar with the effective to_block
            self._effective_to_block = effective_to_block
            self._init_progress_bar_if_needed()

            if self._shards > 1 and effective_to_block is not None:
                await self._run_parallel_workers(effective_to_block)
            else:
                await self._run_serial_worker()

            # Signal completion
            await self._queue.put(None)

        except asyncio.CancelledError:
            # Task cancelled, just exit
            pass
        except Exception as e:
            await self._queue.put(e)

    async def _probe_head_block(self) -> Optional[int]:
        """Get the latest available block number from the /head endpoint."""
        try:
            head_url = f"{self._query.portal_url}/datasets/{self._query.dataset}/head"

            async with self._session.get(head_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("number")
                else:
                    logger.warning("Head endpoint returned status %d", resp.status)

        except Exception as e:
            logger.warning("Failed to get head block: %s", e)

        return None

    async def _run_serial_worker(self) -> None:
        """Single-threaded fetching logic (original behavior)."""
        while not self._finished:
            # Create a new iterator for the current block range
            query = self._query._copy(from_block=self._current_from_block)
            iterator = stream_query_output_async(
                query.endpoint(),
                query.to_sqd_string(),
                self._session,
            )

            # Iterate and buffer
            received_any = False
            async for item, headers in iterator:
                received_any = True
                self._process_item(item)
                await self._queue.put((item, headers))

            # Handle stream completion
            if not received_any:
                logger.info("No more blocks available")
                self._finished = True
            else:
                self._handle_serial_stream_completion()

    async def _run_parallel_workers(self, effective_to_block: int) -> None:
        """Run multiple workers for different block ranges."""
        total_blocks = effective_to_block - self._query.from_block + 1
        blocks_per_shard = (
            total_blocks + self._shards - 1
        ) // self._shards  # Ceiling division

        tasks = []
        for i in range(self._shards):
            start = self._query.from_block + (i * blocks_per_shard)
            if start > effective_to_block:
                break
            end = min(start + blocks_per_shard - 1, effective_to_block)

            # Create a sub-query for this shard
            shard_query = self._query._copy(from_block=start, to_block=end)
            tasks.append(asyncio.create_task(self._shard_worker(shard_query)))

        # Wait for all shards to complete
        await asyncio.gather(*tasks)

    async def _shard_worker(self, query: "BaseSQDQuery") -> None:
        """Worker for a specific shard range."""
        current_from = query.from_block
        finished = False

        while not finished:
            sub_query = query._copy(from_block=current_from)
            iterator = stream_query_output_async(
                sub_query.endpoint(),
                sub_query.to_sqd_string(),
                self._session,
            )

            received_any = False
            last_block_in_batch = None

            async for item, headers in iterator:
                received_any = True

                # Check bounds (server might send more than requested if not strict if strict is not supported by endpoint,
                # but BaseSQDQuery sends toBlock in payload, so server should respect it.)

                # Track last block for pagination
                header = item.get("header")
                if header:
                    block_number = header.get("number")
                    if block_number is not None:
                        last_block_in_batch = block_number
                        # Update global progress safely
                        # We just increment by 1 for density-agnostic progress or we can track blocks processed
                        if self._pbar:
                            self._pbar.update(1)

                await self._queue.put((item, headers))

            if not received_any:
                finished = True
            else:
                # Pagination logic for shard
                if last_block_in_batch is not None:
                    current_from = last_block_in_batch + 1
                    if query.to_block is not None and current_from > query.to_block:
                        finished = True
                    # Reset
                    last_block_in_batch = None
                else:
                    finished = True

    def _process_item(self, item: Dict[str, Any]) -> None:
        """Extract block number and update progress (legacy serial)."""
        header = item.get("header")
        if header:
            block_number = header.get("number")
            if block_number is not None:
                self._last_block_number = block_number
                if self._pbar:
                    self._update_progress(block_number)

    def _handle_serial_stream_completion(self) -> None:
        """Advance pagination or mark as finished based on last stream result."""
        if self._last_block_number is None:
            self._finished = True
            return

        self._current_from_block = self._last_block_number + 1

        if self._query.to_block is not None:
            if self._current_from_block > self._query.to_block:
                logger.info("Finished. Reached target block %d", self._query.to_block)
                self._finished = True

        self._last_block_number = None

    # ------------------------------------------------------------------ #
    # Progress Bar Handling
    # ------------------------------------------------------------------ #

    def _init_progress_bar_if_needed(self) -> None:
        """Initialize tqdm progress bar if enabled."""
        # Use effective_to_block if available, otherwise fall back to query.to_block
        to_block = getattr(self, "_effective_to_block", None) or self._query.to_block

        if self._show_progress and to_block is not None and self._pbar is None:
            total_blocks = to_block - self._query.from_block + 1
            self._pbar = tqdm(
                total=total_blocks,
                desc=f"Syncing {self._query.dataset}",
                unit="blocks",
                unit_scale=True,
                initial=0,
            )

    def _update_progress(self, block_number: int) -> None:
        """Update progress bar (serial version)."""
        if self._pbar:
            current_progress = block_number - self._query.from_block + 1
            delta = current_progress - self._pbar.n
            if delta > 0:
                self._pbar.update(delta)

    def close_progress(self) -> None:
        if self._pbar:
            self._pbar.close()
            self._pbar = None

    # ------------------------------------------------------------------ #
    # Session Management
    # ------------------------------------------------------------------ #

    async def _close_session_if_owned(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def _graceful_shutdown(self) -> None:
        """Handle graceful shutdown on interrupt (Ctrl+C)."""
        logger.info("Shutting down gracefully...")
        if self._last_block_number is not None:
            logger.info("Last processed block: %d", self._last_block_number)
        await self.close()

    async def close(self) -> None:
        """Explicitly close resources."""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        self.close_progress()
        await self._close_session_if_owned()

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def headers(self) -> Dict[str, str]:
        """Response headers from the last request."""
        return self._headers

    @property
    def last_block_number(self) -> Optional[int]:
        """Last block number received."""
        return self._last_block_number
