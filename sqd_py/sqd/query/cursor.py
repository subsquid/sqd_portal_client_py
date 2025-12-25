import asyncio
from logging import getLogger
from typing import Any, AsyncIterator, Dict, Optional

import aiohttp
from tqdm import tqdm

from ..transport import stream_query_output_async

logger = getLogger(__name__)


class QueryCursor(AsyncIterator[Dict[str, Any]]):
    """Async iterator that streams query results from the SQD portal.

    Handles pagination automatically - continues fetching until to_block is reached.
    """

    def __init__(
        self,
        query: "BaseSQDQuery",
        *,
        session: Optional[aiohttp.ClientSession] = None,
        show_progress: bool = False,
    ) -> None:
        self._query = query
        self._session = session
        self._owns_session = session is None
        self._iterator: Optional[AsyncIterator] = None
        self._headers: Dict[str, str] = {}
        self._current_from_block: int = query.from_block
        self._last_block_number: Optional[int] = None
        self._finished = False
        self._show_progress = show_progress
        self._pbar: Optional[tqdm] = None

    def _init_progress_bar(self) -> None:
        """Initialize progress bar if enabled and to_block is set."""
        if (
            self._show_progress
            and self._query.to_block is not None
            and self._pbar is None
        ):
            total_blocks = self._query.to_block - self._query.from_block + 1

            self._pbar = tqdm(
                total=total_blocks,
                desc=f"Syncing {self._query.dataset}",
                unit="blocks",
                unit_scale=True,
            )

    def _update_progress(self, block_number: int) -> None:
        """Update progress bar position."""
        if self._pbar is not None:
            progress = block_number - self._query.from_block + 1
            self._pbar.update(progress - self._pbar.n)

    def _close_progress_bar(self) -> None:
        """Close progress bar if active."""
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None

    def __aiter__(self) -> "QueryCursor":
        self._init_progress_bar()

        return self

    async def __anext__(self) -> Dict[str, Any]:
        while True:
            # Create session if needed
            if self._session is None:
                self._session = aiohttp.ClientSession()

            # Start new request if we don't have an active iterator
            if self._iterator is None:
                if self._finished:
                    self._close_progress_bar()
                    if self._owns_session and self._session:
                        await self._session.close()
                    raise StopAsyncIteration

                # Update query with current from_block for pagination
                query = self._query._copy(from_block=self._current_from_block)

                self._iterator = stream_query_output_async(
                    query.endpoint(),
                    query.to_sqd_string(),
                    self._session,
                )

            try:
                item, self._headers = await self._iterator.__anext__()

                # Track the last block number we've seen
                header = item.get("header", {})
                block_number = header.get("number")
                if block_number is not None:
                    self._last_block_number = block_number
                    self._update_progress(block_number)

                return item

            except StopAsyncIteration:
                # Current stream exhausted, check if we need to continue
                self._iterator = None

                if self._last_block_number is not None:
                    # Continue from next block
                    self._current_from_block = self._last_block_number + 1

                    # Check if we've reached the target
                    if self._query.to_block is not None:
                        if self._current_from_block > self._query.to_block:
                            logger.info(
                                "Finished. Reached target block %d",
                                self._query.to_block,
                            )
                            self._close_progress_bar()
                            self._finished = True
                            if self._owns_session and self._session:
                                await self._session.close()
                            raise StopAsyncIteration
                else:
                    # No blocks received, we're done
                    logger.info("No more blocks available")
                    self._close_progress_bar()
                    self._finished = True
                    if self._owns_session and self._session:
                        await self._session.close()
                    raise StopAsyncIteration

                # Continue to next iteration to start new request
                continue
            except asyncio.CancelledError:
                # Handle Ctrl+C gracefully
                self._close_progress_bar()
                if self._owns_session and self._session:
                    await self._session.close()
                raise
            except Exception as e:
                # On error, clean up
                self._close_progress_bar()
                if self._owns_session and self._session:
                    await self._session.close()
                raise e

    @property
    def headers(self) -> Dict[str, str]:
        """Response headers from the last request."""
        return self._headers

    @property
    def last_block_number(self) -> Optional[int]:
        """Last block number received."""
        return self._last_block_number


__all__ = ["QueryCursor"]
