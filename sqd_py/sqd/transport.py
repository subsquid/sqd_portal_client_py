from logging import getLogger
from typing import Optional

import aiohttp
import ujson as json_lib

JSONDecodeError = json_lib.JSONDecodeError

logger = getLogger()


async def fetch_query_output_async(
    portal_endpoint_url: str,
    query: str,
    session: Optional[aiohttp.ClientSession] = None,
) -> tuple[list[dict], dict]:
    """Async version of fetch_query_output using aiohttp."""
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
            # Check for HTTP errors and handle them according to OpenAPI spec
            if resp.status == 204:
                # No content - requested block range is entirely above available range
                return [], dict(resp.headers)
            elif resp.status == 400:
                # Bad request - invalid query format or from_block below start_block
                error_text = await resp.text()
                raise ValueError(f"Bad request (400): {error_text}")
            elif resp.status == 404:
                # Dataset not found
                error_text = await resp.text()
                raise ValueError(f"Dataset not found (404): {error_text}")
            elif resp.status == 409:
                # Conflict - parent block hash mismatch
                error_text = await resp.text()
                raise ValueError(f"Conflict (409): {error_text}")
            elif resp.status == 429:
                # Rate limit exceeded
                error_text = await resp.text()
                retry_after = resp.headers.get("Retry-After")
                error_msg = f"Rate limit exceeded (429): {error_text}"
                if retry_after:
                    error_msg += f"\nRetry after: {retry_after} seconds"
                raise ValueError(error_msg)
            elif resp.status == 500:
                # Internal server error - don't retry
                error_text = await resp.text()
                raise ValueError(f"Internal server error (500): {error_text}")
            elif resp.status == 503:
                # Service unavailable - retry later
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

            response_text = await resp.text()
            logger.debug(
                "Async response: %s",
                response_text[:500] if len(response_text) > 500 else response_text,
            )

            # Handle empty response
            if not response_text.strip():
                return [], dict(resp.headers)

            # Try to parse as JSON lines
            try:
                data = [
                    json_lib.loads(jline)
                    for jline in response_text.split("\n")
                    if jline.strip()
                ]
                return data, dict(resp.headers)
            except JSONDecodeError as e:
                # If it's not JSON lines, try to parse as single JSON object
                try:
                    data = [json_lib.loads(response_text)]
                    return data, dict(resp.headers)
                except JSONDecodeError:
                    raise ValueError(
                        f"Failed to parse API response as JSON: {response_text[:200]}..."
                    ) from e
    finally:
        if should_close_session:
            await session.close()
