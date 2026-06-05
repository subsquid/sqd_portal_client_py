from collections.abc import AsyncIterator
from logging import getLogger

import aiohttp
import ujson as json_lib

from sqd.utils import create_session

JSONDecodeError = json_lib.JSONDecodeError

logger = getLogger(__name__)


async def handle_response_errors(resp: aiohttp.ClientResponse) -> None:
    # Check for HTTP errors
    if resp.status == 204:
        return  # No content
    elif resp.status == 400:
        error_text = await resp.text()
        raise ValueError(f"Bad request (400): {error_text}")
    elif resp.status == 404:
        error_text = await resp.text()
        raise ValueError(f"Dataset not found (404): {error_text}")
    elif resp.status == 409:
        error_text = await resp.text()
        raise ValueError(f"Conflict (409): {error_text}")
    elif resp.status == 429:
        error_text = await resp.text()
        retry_after = resp.headers.get("Retry-After")
        error_msg = f"Rate limit exceeded (429): {error_text}"
        if retry_after:
            error_msg += f"\nRetry after: {retry_after} seconds"
        raise ValueError(error_msg)
    elif resp.status == 500:
        error_text = await resp.text()
        raise ValueError(f"Internal server error (500): {error_text}")
    elif resp.status == 503:
        error_text = await resp.text()
        retry_after = resp.headers.get("Retry-After")
        error_msg = f"Service unavailable (503): {error_text}"
        if retry_after:
            error_msg += f"\nRetry after: {retry_after} seconds"
        raise ValueError(error_msg)
    elif resp.status != 200:
        error_text = await resp.text()
        raise ValueError(f"API request failed with status {resp.status}: {error_text}")


headers = {
    "Content-Type": "application/json",
    "User-Agent": "sqd_portal_client_py/0",
    "Accept-Encoding": "gzip",
}


async def stream_query_output_async(
    portal_endpoint_url: str,
    query: str,
    session: aiohttp.ClientSession | None = None,
    timeout: aiohttp.ClientTimeout | None = None,
) -> AsyncIterator[tuple[dict[str, object], dict[str, str]]]:
    """Stream JSON lines from the API, yielding each line as it arrives.

    Uses chunked reading with manual line buffering to handle arbitrarily
    large JSON lines that exceed aiohttp's default readline limit.

    Performance optimizations:
    - Accepts gzip/deflate compression
    - Uses bytearray for efficient buffer operations
    - Parses JSON directly from bytes (ujson)
    - Batches buffer clearing to avoid O(N^2) memory movement
    - Uses find() instead of index() to avoid exception overhead

    Yields:
        Tuple of (parsed_json_object, response_headers)
    """

    should_close_session = session is None
    if session is None:
        session = create_session()
    try:
        async with session.post(
            portal_endpoint_url,
            data=query,
            headers=headers,
            timeout=timeout,
        ) as resp:
            response_headers = dict(resp.headers)
            await handle_response_errors(resp)
            if resp.status == 204:
                return  # No content

            buffer = bytearray()
            newline = ord(b"\n")

            async for chunk, _ in resp.content.iter_chunks():
                if len(chunk) == 0:
                    return

                buffer.extend(chunk)

                start_offset = 0
                while True:
                    idx = buffer.find(newline, start_offset)
                    if idx == -1:
                        break

                    line = buffer[start_offset:idx]
                    start_offset = idx + 1

                    if line and not line.isspace():
                        try:
                            # ujson can parse bytes directly
                            yield json_lib.loads(line), response_headers
                        except JSONDecodeError as e:
                            logger.warning(
                                "Failed to parse JSON: %s", line[:100].decode()
                            )
                            raise ValueError(
                                f"Failed to parse JSON: {line[:200].decode()}"
                            ) from e

                # Remove processed portion of the buffer in one go
                if start_offset > 0:
                    del buffer[:start_offset]

            # Process any remaining content in buffer (last line without newline)
            if buffer and not buffer.isspace():
                try:
                    yield json_lib.loads(buffer), response_headers
                except JSONDecodeError as e:
                    logger.warning("Failed to parse JSON: %s", buffer[:100].decode())
                    raise ValueError(
                        f"Failed to parse JSON: {buffer[:200].decode()}"
                    ) from e

    finally:
        if should_close_session:
            await session.close()


async def fetch_query_output_async(
    portal_endpoint_url: str,
    query: str,
    session: aiohttp.ClientSession | None = None,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    """Fetch all query output at once (non-streaming).

    For large responses, prefer stream_query_output_async.
    """
    results = []
    headers = {}

    async for item, response_headers in stream_query_output_async(
        portal_endpoint_url, query, session
    ):
        results.append(item)
        headers = response_headers

    return results, headers
