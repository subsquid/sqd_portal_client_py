import asyncio
import signal
import sys
from logging import getLogger
from sys import prefix
from typing import Any, AsyncIterator, Dict, Optional, Tuple, Union

import aiohttp
from tqdm import tqdm

from ..transport import stream_query_output_async
from ..utils import create_session

logger = getLogger(__name__)

# Maximum number of parallel shards (based on benchmarks, 15 is optimal)
MAX_SHARDS = 15


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
        poll_interval: float = 5.0,
    ) -> None:
        self._query = query
        self._session = session
        self._owns_session = session is None
        self._show_progress = show_progress and tqdm is not None
        self._shards = min(shards, MAX_SHARDS)
        self._poll_interval = poll_interval

        # State
        self._current_from_block: int = query.from_block
        self._last_block_number: Optional[int] = None
        self._finished = False
        self._headers: Dict[str, str] = {}
        self._shutdown_requested = False
        self._closed = False
        # Progress bar
        self._pbar: Optional[tqdm] = None

        # Background fetching
        self._queue: asyncio.Queue[
            Union[Tuple[Dict[str, Any], Dict[str, str]], Exception, None]
        ] = asyncio.Queue(maxsize=-1)
        self._worker_task: Optional[asyncio.Task] = None

        # Track max block across parallel shards for correct serial mode resume
        self._max_parallel_block: int = 0
        self._parallel_lock = asyncio.Lock()

    def __aiter__(self) -> "QueryCursor":
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._fetch_loop())
            self._register_signal_handlers()
        return self

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (e.g., in tests)
            return

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(
                    sig, lambda s=sig: asyncio.create_task(self._handle_signal(s))
                )
            except (NotImplementedError, RuntimeError):
                # Signal handlers not supported on this platform (e.g., Windows)
                pass

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal."""
        if self._shutdown_requested:
            return  # Already shutting down

        logger.info("Received signal %s, initiating graceful shutdown...", sig.name)
        self._shutdown_requested = True
        await self._graceful_shutdown()

        # Signal end of iteration by putting None in queue
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            pass

    async def __anext__(self) -> Dict[str, Any]:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._fetch_loop())

        try:
            item_or_error = await self._queue.get()
        except asyncio.CancelledError:
            if not self._shutdown_requested:
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

            # Determine effective to_block and mode
            effective_to_block = self._query.to_block
            infinite_mode = self._query.to_block is None

            if self._shards > 1 and infinite_mode:
                # Probe to get head block number for parallel catchup
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
                # Run parallel workers to catch up
                await self._run_parallel_workers(effective_to_block)

                # If infinite mode, switch to serial for continuous polling
                if infinite_mode and not self._shutdown_requested:
                    # Use actual max block processed, not the initial head block
                    resume_from = (
                        self._max_parallel_block + 1
                        if self._max_parallel_block > 0
                        else effective_to_block + 1
                    )
                    logger.info(
                        "Parallel catchup complete. Switching to serial mode for live updates. "
                        "Resuming from block %d (max processed: %d)",
                        resume_from,
                        self._max_parallel_block,
                    )
                    self._current_from_block = resume_from
                    self._last_block_number = self._max_parallel_block  # Sync state
                    self._switch_to_live_progress()  # Switch to live mode progress bar
                    await self._run_serial_worker()
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
        """Single-threaded fetching logic.

        If to_block is not set, continues indefinitely, polling for new blocks.
        """
        infinite_mode = self._query.to_block is None

        while not self._finished and not self._shutdown_requested:
            # Create a new iterator for the current block range
            query = self._query.copy(from_block=self._current_from_block, to_block=None)
            try:
                timeout = aiohttp.ClientTimeout(sock_read=60)

                iterator = stream_query_output_async(
                    query.endpoint(),
                    query.to_sqd_string(),
                    self._session,
                    timeout=timeout,
                )

                # Use manual iteration to enforce strict progress timeout
                # 60s timeout ensures we don't hang if server sends heartbeats but no valid data for too long
                async_iter = iterator.__aiter__()

                received_any = False
                while True:
                    try:
                        # Wait at most 60 seconds for the next block
                        item_or_headers = await asyncio.wait_for(
                            async_iter.__anext__(), timeout=60.0
                        )
                        item, headers = item_or_headers

                        received_any = True
                        self._process_item(item)
                        await self._queue.put((item, headers))
                    except StopAsyncIteration:
                        break
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                logger.warning(
                    "Connection error while polling (will retry): %s: %s",
                    type(e).__name__,
                    e,
                )
                # Force a small sleep to avoid tight loop on persistent network failure
                await asyncio.sleep(1.0)
                continue

            # Handle stream completion
            if not received_any:
                if infinite_mode:
                    # Wait and poll again for new blocks
                    logger.debug(
                        "Caught up at block %s. Polling again in %.1fs...",
                        self._current_from_block,
                        self._poll_interval,
                    )
                    self._update_live_progress_waiting()
                    await asyncio.sleep(self._poll_interval)
                else:
                    logger.info("No more blocks available")
                    self._finished = True
            else:
                self._handle_serial_stream_completion()

    async def _run_parallel_workers(self, effective_to_block: int) -> None:
        """Run multiple workers for different block ranges with ordered output.

        Each shard fetches its range in parallel but writes to its own queue.
        We then drain the queues sequentially (shard 0, then shard 1, etc.) to
        guarantee blocks are emitted in ascending order.
        """
        total_blocks = effective_to_block - self._query.from_block + 1
        blocks_per_shard = (
            total_blocks + self._shards - 1
        ) // self._shards  # Ceiling division

        # Create per-shard queues and tasks
        shard_queues: list[asyncio.Queue] = []
        tasks = []

        for i in range(self._shards):
            start = self._query.from_block + (i * blocks_per_shard)
            if start > effective_to_block:
                break
            end = min(start + blocks_per_shard - 1, effective_to_block)

            # Each shard gets its own queue with a limit to prevent memory blowup
            # if early shards stall while later ones race ahead
            shard_queue: asyncio.Queue = asyncio.Queue(maxsize=2000)
            shard_queues.append(shard_queue)

            # Create a sub-query for this shard
            shard_query = self._query.copy(from_block=start, to_block=end)
            tasks.append(
                asyncio.create_task(self._shard_worker(shard_query, shard_queue))
            )

        # Start a task to drain shard queues sequentially into the main queue
        drain_task = asyncio.create_task(self._drain_shards_in_order(shard_queues))

        # Wait for all fetch tasks to complete
        await asyncio.gather(*tasks)

        # Wait for drain task to finish processing everything
        await drain_task

    async def _drain_shards_in_order(self, shard_queues: list[asyncio.Queue]) -> None:
        """Drain shard queues sequentially to maintain block order."""
        for i, shard_queue in enumerate(shard_queues):
            while True:
                # Get item from current shard's queue
                item = await shard_queue.get()

                # None is the signal that this shard is finished
                if item is None:
                    break

                # Forward to main queue
                await self._queue.put(item)

            logger.debug("Drained shard %d/%d", i + 1, len(shard_queues))

    async def _shard_worker(
        self, query: "BaseSQDQuery", shard_queue: asyncio.Queue
    ) -> None:
        """Worker for a specific shard range. Writes to shard-specific queue."""
        current_from = query.from_block
        finished = False

        try:
            while not finished and not self._shutdown_requested:
                sub_query = query.copy(from_block=current_from)
                iterator = stream_query_output_async(
                    sub_query.endpoint(),
                    sub_query.to_sqd_string(),
                    self._session,
                )

                received_any = False
                last_block_in_batch = None

                async for item, headers in iterator:
                    received_any = True

                    # Track last block for pagination and progress
                    header = item.get("header")
                    if header:
                        block_number = header.get("number")
                        if block_number is not None:
                            last_block_in_batch = block_number
                            # Update global max block for correct serial resume
                            async with self._parallel_lock:
                                if block_number > self._max_parallel_block:
                                    self._max_parallel_block = block_number
                            # Update global progress safely
                            if self._pbar is not None:
                                self._pbar.update(1)

                    # Put in shard-specific queue (not main queue)
                    await shard_queue.put((item, headers))

                if not received_any:
                    finished = True
                else:
                    # Pagination logic for shard
                    if last_block_in_batch is not None:
                        current_from = last_block_in_batch + 1
                        if query.to_block is not None and current_from > query.to_block:
                            finished = True
                        last_block_in_batch = None
                    else:
                        finished = True
        finally:
            # Signal completion of this shard
            await shard_queue.put(None)

    def _process_item(self, item: Dict[str, Any]) -> None:
        """Extract block number and update progress (legacy serial)."""
        header = item.get("header")
        if header:
            block_number = header.get("number")
            if block_number is not None:
                self._last_block_number = block_number
                if self._pbar is not None:
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
        if not self._show_progress or self._pbar is not None:
            return

        # Use effective_to_block if available, otherwise fall back to query.to_block
        to_block = getattr(self, "_effective_to_block", None) or self._query.to_block

        if to_block is not None:
            # Finite mode: show progress towards to_block
            total_blocks = to_block - self._query.from_block + 1
            self._pbar = tqdm(
                total=total_blocks,
                desc=f"Syncing {self._query.dataset}",
                unit="blocks",
                unit_scale=True,
                initial=0,
            )
        else:
            # Infinite mode: show block count without total
            self._pbar = tqdm(
                desc=f"Syncing {self._query.dataset}",
                unit="blocks",
                unit_scale=True,
            )

    def _update_progress(self, block_number: int) -> None:
        """Update progress bar."""
        if self._pbar is not None:
            if self._pbar.total is not None:
                # Finite mode: update relative to from_block
                current_progress = block_number - self._query.from_block + 1
                delta = current_progress - self._pbar.n
                if delta > 0:
                    self._pbar.update(delta)
                # Show current block in postfix for finite mode
                self._pbar.set_postfix(block=block_number, refresh=True)
            else:
                # Live/infinite mode: just increment by 1 and show block number in desc
                self._pbar.update(1)
                self._pbar.set_description_str(
                    f"{self._query.dataset} | block {block_number} |", refresh=True
                )

    def close_progress(self) -> None:
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None

    def _switch_to_live_progress(self) -> None:
        """Switch from catchup progress bar to live mode showing current block."""
        if self._pbar is not None:
            self._pbar.close()

        if self._show_progress:
            # Use effective_to_block as starting point since parallel workers
            # don't update _last_block_number
            last_block = self._last_block_number or getattr(
                self, "_effective_to_block", None
            )

            self._pbar = tqdm(
                total=None,
                unit="blocks",
                unit_scale=True,
                bar_format="Live {desc} {n_fmt} new [{elapsed}, {rate_fmt}]",
                dynamic_ncols=True,
                file=sys.stderr,
            )
            self._pbar.set_description_str(f"{self._query.dataset}")
            if last_block is not None:
                self._last_block_number = last_block  # Sync state

    def _update_live_progress_waiting(self) -> None:
        """Update live progress bar to show waiting status."""
        if self._pbar is not None and self._last_block_number is not None:
            self._pbar.set_description_str(
                f"{self._query.dataset} | block {self._last_block_number} (waiting...) |"
            )
            self._pbar.refresh()

    # ------------------------------------------------------------------ #
    # Session Management
    # ------------------------------------------------------------------ #

    async def _close_session_if_owned(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def _graceful_shutdown(self) -> None:
        """Handle graceful shutdown on interrupt (Ctrl+C)."""
        if self._closed:
            return  # Already closed

        logger.info("Shutting down gracefully...")
        if self._last_block_number is not None:
            logger.info("Last processed block: %d", self._last_block_number)
        await self.close()

    async def close(self) -> None:
        """Explicitly close resources."""
        if self._closed:
            return  # Already closed
        self._closed = True

        # Remove signal handlers
        self._remove_signal_handlers()

        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        self.close_progress()
        await self._close_session_if_owned()

    def _remove_signal_handlers(self) -> None:
        """Remove previously registered signal handlers."""
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.remove_signal_handler(sig)
                except (NotImplementedError, RuntimeError):
                    pass
        except RuntimeError:
            # No running loop
            pass

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
