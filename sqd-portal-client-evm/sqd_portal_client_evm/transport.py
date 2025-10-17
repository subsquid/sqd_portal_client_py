import requests

try:
    import ujson as json_lib

    JSONDecodeError = json_lib.JSONDecodeError
except ImportError:
    import json as std_json

    json_lib = std_json
    JSONDecodeError = std_json.JSONDecodeError
import aiohttp
from typing import Optional


def fetch_query_output(
        portal_endpoint_url: str,
        query: str
) -> list[dict]:
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'sqd_portal_client_py/0'
    }

    resp = requests.post(
        portal_endpoint_url,
        data=query,
        headers=headers
    )

    # Check for HTTP errors
    if resp.status_code != 200:
        raise ValueError(f"API request failed with status {resp.status_code}: {resp.text}")

    response_text = resp.text
    print(response_text)

    # Handle empty response
    if not response_text.strip():
        return []

    # Try to parse as JSON lines
    try:
        return [json_lib.loads(jline) for jline in response_text.split('\n') if jline.strip()]
    except JSONDecodeError as e:
        # If it's not JSON lines, try to parse as single JSON object
        try:
            return [json_lib.loads(response_text)]
        except JSONDecodeError:
            raise ValueError(f"Failed to parse API response as JSON: {response_text[:200]}...") from e


async def fetch_query_output_async(
        portal_endpoint_url: str,
        query: str,
        session: Optional[aiohttp.ClientSession] = None
) -> list[dict]:
    """Async version of fetch_query_output using aiohttp."""
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'sqd_portal_client_py/0'
    }

    should_close_session = session is None
    if session is None:
        session = aiohttp.ClientSession()

    try:
        async with session.post(
                portal_endpoint_url,
                data=query,
                headers=headers
        ) as resp:
            # Check for HTTP errors
            if resp.status != 200:
                error_text = await resp.text()
                raise ValueError(f"API request failed with status {resp.status}: {error_text}")

            response_text = await resp.text()
            print(response_text)

            # Handle empty response
            if not response_text.strip():
                return []

            # Try to parse as JSON lines
            try:
                return [json_lib.loads(jline) for jline in response_text.split('\n') if jline.strip()]
            except JSONDecodeError as e:
                # If it's not JSON lines, try to parse as single JSON object
                try:
                    return [json_lib.loads(response_text)]
                except JSONDecodeError:
                    raise ValueError(f"Failed to parse API response as JSON: {response_text[:200]}...") from e
    finally:
        if should_close_session:
            await session.close()
