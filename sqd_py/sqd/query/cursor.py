import asyncio
import signal
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any

import aiohttp

from sqd.query import NoopProgressHandler, ProgressHandler, TqdmProgressHandler
from sqd.query.base_query import BaseSQDQuery
from sqd.transport import stream_query_output_async
from sqd.utils import create_session

logger = getLogger(__name__)

# Maximum number of parallel shards (based on benchmarks, 15 is optimal)
MAX_SHARDS = 15


class _SwitchToLiveSentinel:
    """Sentinel value to signal switch from parallel catchup to live mode.

    This flows through the queue after all parallel catchup blocks,
    ensuring the consumer processes all catchup blocks before switching.
    """

    def __init__(self, resume_from: int, max_processed: int) -> None:
        self.resume_from = resume_from
        self.max_processed = max_processed


class QueryCursor(AsyncIterator[dict[str, Any]]):
    """Async iterator that streams query results from the SQD portal.

    Handles pagination automatically - continues fetching until to_block is reached
    or no more data is available. Fetches ahead in a background task, optionally
    using parallel workers if shards > 1 and to_block is set.
    """

    def __init__(
        self,
        query: "BaseSQDQuery",
        *,
        session: aiohttp.ClientSession | None = None,
        show_progress: bool = False,
        progress_handler: ProgressHandler | None = None,
        shards: int = 1,
        poll_interval: float = 5.0,
    ) -> None:
        self._query = query
        self._session = session
        self._owns_session = session is None
        self._shards = min(shards, MAX_SHARDS)
        self._poll_interval = poll_interval

        # Progress handler
        if progress_handler is not None:
            self._progress = progress_handler
        elif show_progress:
            self._progress = TqdmProgressHandler()
        else:
            self._progress = NoopProgressHandler()

        # State
        self._current_from_block: int = query.from_block
        self._last_block_number: int | None = None
        self._finished = False
        self._headers: dict[str, str] = {}
        self._shutdown_requested = False
        self._closed = False

        # Background fetching
        self._queue: asyncio.Queue[
            tuple[dict[str, Any], dict[str, str]]
            | Exception
            | None
            | _SwitchToLiveSentinel
        ] = asyncio.Queue(maxsize=20000)
        self._worker_task: asyncio.Task[None] | None = None

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

                def make_handler(s: signal.Signals) -> Any:
                    return lambda: asyncio.create_task(self._handle_signal(s))

                loop.add_signal_handler(sig, make_handler(sig))
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

    async def __anext__(self) -> dict[str, Any]:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._fetch_loop())

        while True:
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

            # Handle switchover sentinel: trigger live mode switch and continue
            if isinstance(item_or_error, _SwitchToLiveSentinel):
                logger.info(
                    "Switching to live mode. Resuming from block %d (max processed: %d)",
                    item_or_error.resume_from,
                    item_or_error.max_processed,
                )
                self._progress.on_switch_to_live(self._last_block_number)
                continue  # Get next item from queue (now in live mode)

            item, headers = item_or_error
            self._headers = headers
            self._progress.on_block(item.get("header", {}).get("number", -1))
            return item

    async def _fetch_loop(self) -> None:
        """Background task to fetch items and put them in the queue."""
        try:
            if self._session is None:
                self._session = create_session()

            # Determine effective to_block and mode
            effective_to_block = self._query.to_block
            infinite_mode = self._query.to_block is None

            # For parallel mode, always probe head block to avoid creating shards
            # for blocks that don't exist yet
            if self._shards > 1:
                head_block = await self._probe_head_block()
                if head_block is not None:
                    logger.info("Discovered head block: %d", head_block)
                    if infinite_mode:
                        # Infinite mode: use head as effective_to_block
                        effective_to_block = head_block
                    elif (
                        effective_to_block is not None
                        and effective_to_block > head_block
                    ):
                        # User's to_block is beyond head - clamp it
                        logger.warning(
                            "Requested to_block=%d is beyond head block=%d, clamping",
                            effective_to_block,
                            head_block,
                        )
                        effective_to_block = head_block
                else:
                    logger.warning(
                        "Could not discover head block. Falling back to single worker."
                    )
                    # Can't use parallel mode without knowing head
                    self._shards = 1

            # Initialize progress handler
            self._effective_to_block = effective_to_block
            self._progress.on_start(
                dataset=self._query.dataset,
                from_block=self._query.from_block,
                to_block=effective_to_block,
            )

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
                        "Parallel fetching complete (max block: %d). "
                        "Waiting for consumer to process queued blocks...",
                        self._max_parallel_block,
                    )
                    self._current_from_block = resume_from
                    self._last_block_number = self._max_parallel_block  # Sync state

                    # Queue sentinel so switch happens after consumer processes all catchup blocks
                    await self._queue.put(
                        _SwitchToLiveSentinel(resume_from, self._max_parallel_block)
                    )

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

    async def _probe_head_block(self) -> int | None:
        """Get the latest available block number from the /head endpoint."""
        try:
            head_url = f"{self._query.portal_url}/datasets/{self._query.dataset}/head"

            if self._session is None:
                return None

            async with self._session.get(head_url) as resp:
                if resp.status == 200:
                    data: dict[str, Any] = await resp.json()
                    result = data.get("number")
                    if isinstance(result, int):
                        return result
                    return None
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
            query = self._query.copy(
                from_block=self._current_from_block,
                to_block=None if infinite_mode else self._query.to_block,
            )
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
                    if self._last_block_number is not None:
                        self._progress.on_waiting(self._last_block_number)
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
        shard_queues: list[
            asyncio.Queue[tuple[dict[str, Any], dict[str, str]] | None]
        ] = []
        tasks: list[asyncio.Task[None]] = []

        for i in range(self._shards):
            start = self._query.from_block + (i * blocks_per_shard)
            if start > effective_to_block:
                break
            end = min(start + blocks_per_shard - 1, effective_to_block)

            # Each shard gets its own queue with a limit to prevent memory blowup
            # if early shards stall while later ones race ahead
            shard_queue: asyncio.Queue[tuple[dict[str, Any], dict[str, str]] | None] = (
                asyncio.Queue()
            )
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

        # If shutdown was requested, cancel the drain task to avoid waiting
        if self._shutdown_requested:
            drain_task.cancel()
            try:
                await drain_task
            except asyncio.CancelledError:
                pass
            return

        # Wait for drain task to finish processing everything
        await drain_task

    async def _drain_shards_in_order(
        self,
        shard_queues: list[asyncio.Queue[tuple[dict[str, Any], dict[str, str]] | None]],
    ) -> None:
        """Drain shard queues sequentially to maintain block order.

        Stops draining immediately when shutdown is requested to prevent
        forwarding additional blocks to the consumer.
        """
        for i, shard_queue in enumerate(shard_queues):
            while True:
                # Check shutdown before waiting for next item
                if self._shutdown_requested:
                    logger.debug(
                        "Shutdown requested, stopping drain at shard %d/%d",
                        i + 1,
                        len(shard_queues),
                    )
                    return

                # Get item from current shard's queue
                item = await shard_queue.get()

                # None is the signal that this shard is finished
                if item is None:
                    break

                # Check shutdown after getting item (another opportunity to exit quickly)
                if self._shutdown_requested:
                    logger.debug(
                        "Shutdown requested, stopping drain at shard %d/%d (after get)",
                        i + 1,
                        len(shard_queues),
                    )
                    return

                # Forward to main queue
                await self._queue.put(item)

            logger.debug("Drained shard %d/%d", i + 1, len(shard_queues))

    async def _shard_worker(
        self,
        query: BaseSQDQuery,
        shard_queue: asyncio.Queue[tuple[dict[str, Any], dict[str, str]] | None],
    ) -> None:
        """Worker for a specific shard range. Writes to shard-specific queue."""
        current_from = query.from_block
        finished = False

        try:
            while not finished and not self._shutdown_requested:
                sub_query = query.copy(from_block=current_from)
                logger.debug(
                    "Shard [%d-%d] starting request from block %d",
                    query.from_block,
                    query.to_block,
                    current_from,
                )
                iterator = stream_query_output_async(
                    sub_query.endpoint(),
                    sub_query.to_sqd_string(),
                    self._session,
                )

                received_any = False
                last_block_in_batch = None

                async for item, headers in iterator:
                    # Check for shutdown in the inner loop to stop quickly
                    if self._shutdown_requested:
                        logger.debug(
                            "Shard [%d-%d] shutdown requested, stopping fetch",
                            query.from_block,
                            query.to_block,
                        )
                        return

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

                    # Put in shard-specific queue (not main queue)
                    await shard_queue.put((item, headers))

                if not received_any:
                    logger.debug(
                        "Shard [%d-%d] received no data, finishing",
                        query.from_block,
                        query.to_block,
                    )
                    finished = True
                else:
                    # Pagination logic for shard
                    if last_block_in_batch is not None:
                        current_from = last_block_in_batch + 1
                        if query.to_block is not None and current_from > query.to_block:
                            logger.debug(
                                "Shard [%d-%d] completed - reached to_block",
                                query.from_block,
                                query.to_block,
                            )
                            finished = True
                        last_block_in_batch = None
                    else:
                        logger.debug(
                            "Shard [%d-%d] no last_block_in_batch, finishing",
                            query.from_block,
                            query.to_block,
                        )
                        finished = True
        finally:
            # Signal completion of this shard
            logger.debug(
                "Shard [%d-%d] putting None to signal completion",
                query.from_block,
                query.to_block,
            )
            await shard_queue.put(None)

    def _process_item(self, item: dict[str, Any]) -> None:
        """Extract block number and update progress."""
        header = item.get("header")
        if header:
            block_number = header.get("number")
            if block_number is not None:
                self._last_block_number = block_number
                self._progress.on_block(block_number)

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

        self._progress.on_close()
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
    def headers(self) -> dict[str, str]:
        """Response headers from the last request."""
        return self._headers

    @property
    def last_block_number(self) -> int | None:
        """Last block number received."""
        return self._last_block_number
