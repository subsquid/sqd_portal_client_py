from typing import Any, AsyncIterator, Dict, Optional

import aiohttp

from ..models import StreamResponse
from ..transport import fetch_query_output_async
from .base_query import BaseSQDQuery


class QueryCursor(AsyncIterator[Dict[str, Any]]):
    """Async iterator that materializes a query via the SQD portal."""

    def __init__(
        self,
        query: BaseSQDQuery,
        *,
        session: Optional[aiohttp.ClientSession] = None,
        stream_response: Optional[StreamResponse] = None,
    ) -> None:
        self._query = query
        self._session = session
        self._stream_response = stream_response
        self._index = 0

    async def _ensure_response(self) -> None:
        if self._stream_response is not None:
            return

        response_data, response_headers = await fetch_query_output_async(
            self._query.endpoint(), self._query.to_sqd_string(), self._session
        )
        self._stream_response = StreamResponse.from_response(
            response_data, response_headers
        )

    def __aiter__(self) -> "QueryCursor":
        self._index = 0
        return self

    async def __anext__(self) -> Dict[str, Any]:
        await self._ensure_response()
        assert self._stream_response is not None  # mypy helper
        if self._index >= len(self._stream_response.data):
            raise StopAsyncIteration

        item = self._stream_response.data[self._index]
        self._index += 1
        return item


__all__ = ["QueryCursor"]
