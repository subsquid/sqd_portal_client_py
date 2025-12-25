from logging import getLogger
from typing import AsyncIterator, Optional

import aiohttp
import ujson as json_lib

JSONDecodeError = json_lib.JSONDecodeError

logger = getLogger(__name__)

from tqdm.asyncio import tqdm


async def stream_query_output_async(
    portal_endpoint_url: str,
    query: str,
    session: Optional[aiohttp.ClientSession] = None,
) -> AsyncIterator[tuple[dict, dict]]:
    """Stream JSON lines from the API, yielding each line as it arrives.

    Uses chunked reading with manual line buffering to handle arbitrarily
    large JSON lines that exceed aiohttp's default readline limit.

    Yields:
        Tuple of (parsed_json_object, response_headers)
    """
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "sqd_portal_client_py/0",
    }

    should_close_session = session is None
    if session is None:
        session = aiohttp.ClientSession()

    try:
        async with session.post(
            portal_endpoint_url, data=query, headers=headers
        ) as resp:
            response_headers = dict(resp.headers)

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
                raise ValueError(
                    f"API request failed with status {resp.status}: {error_text}"
                )

            # Stream using iter_chunks with manual line buffering
            # This handles arbitrarily large lines without limit
            buffer = b""

            async for chunk, _ in resp.content.iter_chunks():
                buffer += chunk

                # Process complete lines from buffer
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line_str = line.decode("utf-8").strip()
                    if line_str:
                        try:
                            yield json_lib.loads(line_str), response_headers
                        except JSONDecodeError as e:
                            logger.warning("Failed to parse JSON: %s", line_str[:100])
                            raise ValueError(
                                f"Failed to parse JSON: {line_str[:200]}"
                            ) from e

            # Process any remaining content in buffer (last line without newline)
            if buffer.strip():
                line_str = buffer.decode("utf-8").strip()
                if line_str:
                    try:
                        yield json_lib.loads(line_str), response_headers
                    except JSONDecodeError as e:
                        logger.warning("Failed to parse JSON: %s", line_str[:100])
                        raise ValueError(
                            f"Failed to parse JSON: {line_str[:200]}"
                        ) from e

    finally:
        if should_close_session:
            await session.close()


async def fetch_query_output_async(
    portal_endpoint_url: str,
    query: str,
    session: Optional[aiohttp.ClientSession] = None,
) -> tuple[list[dict], dict]:
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
