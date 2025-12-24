import asyncio
from typing import Dict, Any, Optional, List

import aiohttp
import requests

from .dataset import Dataset
from .models import BlockHead, StreamResponse
from .query import SQDQuery
from .transport import fetch_query_output, fetch_query_output_async


def _normalize_dataset(dataset: Dataset | str) -> Dataset:
    """Ensure dataset inputs are always Dataset enum values."""
    if isinstance(dataset, Dataset):
        return dataset
    try:
        return Dataset(dataset)
    except ValueError as exc:
        raise ValueError(f"Unsupported dataset '{dataset}'") from exc


def _as_query_string(query: SQDQuery | str) -> str:
    return query.to_sqd_string() if isinstance(query, SQDQuery) else query


def get_data(
        *,
        dataset: Dataset | str,
        query: SQDQuery | str,
        portal_url: str = "https://portal.sqd.dev",
        flattening: Optional[str] = "by_itemtype",
        stream_type: str = "finalized",
) -> StreamResponse:
    """
    Get data from SQD portal using a query.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: SQDQuery (from `SQD` builder) or raw query string
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        StreamResponse with data and metadata headers

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    if stream_type not in ["finalized", "stream"]:
        raise ValueError(
            f"Invalid stream_type: {stream_type}. Must be 'finalized' or 'stream'"
        )

    dataset_enum = _normalize_dataset(dataset)
    endpoint = f"{portal_url}/datasets/{dataset_enum.value}/{stream_type}-stream"

    str_query = _as_query_string(query)

    print(f"Executing query: {str_query}")
    try:
        response_data, response_headers = fetch_query_output(endpoint, str_query)
        return StreamResponse.from_response(response_data, response_headers)
    except ValueError as e:
        # Re-raise ValueError exceptions as-is (they have specific API error info)
        raise e
    except Exception as e:
        # Provide more helpful error messages for unexpected errors
        error_msg = f"Failed to execute query: {e}"
        if "API request failed" in str(e):
            error_msg += (
                "\nThis could be due to:\n"
                "1. Invalid query format\n"
                "2. Network connectivity issues\n"
                "3. SQD API being unavailable\n"
                "4. Invalid dataset or portal URL"
            )
        elif "Failed to parse API response" in str(e):
            error_msg += (
                "\nThis could be due to:\n"
                "1. Unexpected response format from API\n"
                "2. API returning HTML error page instead of JSON"
            )
        raise ValueError(error_msg) from e


def validate_query_format(query: SQDQuery | str) -> tuple[bool, str]:
    """
    Validate query format against OpenAPI DataQuery schema and provide helpful feedback.

    Args:
        query: SQDQuery/EVM/Solana builder or string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        query_str = _as_query_string(query)

        # Try to parse the JSON to check format
        import json

        parsed = json.loads(query_str)

        # Check required fields according to OpenAPI DataQuery schema
        if "type" not in parsed:
            return False, "Missing required field: 'type'"

        if "fromBlock" not in parsed:
            hint = ""
            if "from_block" in parsed:
                hint = " (use camelCase `fromBlock` instead of `from_block`)"
            return False, "Missing required field: 'fromBlock'" + hint

        # Validate field types and values
        query_content = parsed

        # Type must be 'evm' or 'solana' for this API
        query_type = query_content.get("type")
        if query_type not in ["evm", "solana"]:
            return (
                False,
                f"Invalid type: expected 'evm' or 'solana', got '{query_type}'",
            )

        # from_block must be integer >= 0
        from_block = query_content.get("fromBlock")
        if not isinstance(from_block, int) or from_block < 0:
            return (
                False,
                f"Invalid fromBlock: must be non-negative integer, got {from_block}",
            )

        # to_block must be integer >= from_block if provided
        to_block = query_content.get("toBlock")
        if to_block is not None:
            if not isinstance(to_block, int):
                return False, f"Invalid toBlock: must be integer, got {to_block}"
            if to_block < from_block:
                return (
                    False,
                    f"Invalid toBlock: must be >= fromBlock ({from_block}), got {to_block}",
                )

        # parentBlockHash must be string if provided
        parent_hash = query_content.get("parentBlockHash")
        if parent_hash is not None and not isinstance(parent_hash, str):
            return (
                False,
                f"Invalid parentBlockHash: must be string, got {type(parent_hash)}",
            )

        # includeAllBlocks must be boolean if provided
        include_all = query_content.get("includeAllBlocks")
        if include_all is not None and not isinstance(include_all, bool):
            return (
                False,
                f"Invalid includeAllBlocks: must be boolean, got {type(include_all)}",
            )

        # fields must be object if provided
        fields = query_content.get("fields")
        if fields is not None and not isinstance(fields, dict):
            return False, f"Invalid fields: must be object, got {type(fields)}"

        # Validate request arrays for both EVM and Solana
        evm_request_types = ["logs", "transactions", "traces", "stateDiffs"]
        solana_request_types = [
            "instructions",
            "balances",
            "tokenBalances",
            "rewards",
            "logs",
        ]

        for request_type in evm_request_types + solana_request_types:
            requests = query_content.get(request_type)
            if requests is None:
                requests = query_content.get(f"{request_type}Requests")
            if requests and not isinstance(requests, list):
                return (
                    False,
                    f"Invalid {request_type}: must be array, got {type(requests)}",
                )

        return True, "Query format is valid according to OpenAPI schema"

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {e}"
    except Exception as e:
        return False, f"Query validation failed: {e}"


async def get_data_async(
        *,
        dataset: Dataset | str,
        query: SQDQuery | str,
        portal_url: str = "https://portal.sqd.dev",
        flattening: Optional[str] = "by_itemtype",
        session: Optional[aiohttp.ClientSession] = None,
        stream_type: str = "finalized",
) -> StreamResponse:
    """
    Async version of get_data function.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: SQDQuery (from `SQD`) or raw query string
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        session: Optional aiohttp session for connection reuse
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        StreamResponse with data and metadata headers

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    if stream_type not in ["finalized", "stream"]:
        raise ValueError(
            f"Invalid stream_type: {stream_type}. Must be 'finalized' or 'stream'"
        )

    dataset_enum = _normalize_dataset(dataset)
    endpoint = f"{portal_url}/datasets/{dataset_enum.value}/{stream_type}-stream"

    str_query = _as_query_string(query)

    print(f"Executing async query: {str_query}")
    try:
        response_data, response_headers = await fetch_query_output_async(
            endpoint, str_query, session
        )
        return StreamResponse.from_response(response_data, response_headers)
    except ValueError as e:
        # Re-raise ValueError exceptions as-is (they have specific API error info)
        raise e
    except Exception as e:
        # Provide more helpful error messages for unexpected errors
        error_msg = f"Failed to execute async query: {e}"
        if "API request failed" in str(e):
            error_msg += (
                "\nThis could be due to:\n"
                "1. Invalid query format\n"
                "2. Network connectivity issues\n"
                "3. SQD API being unavailable\n"
                "4. Invalid dataset or portal URL"
            )
        elif "Failed to parse API response" in str(e):
            error_msg += (
                "\nThis could be due to:\n"
                "1. Unexpected response format from API\n"
                "2. API returning HTML error page instead of JSON"
            )
        raise ValueError(error_msg) from e


def get_multiple_data(
        queries: List[tuple],
        portal_url: str = "https://portal.sqd.dev",
        flattening: Optional[str] = "by_itemtype",
        stream_type: str = "finalized",
) -> List[StreamResponse]:
    """
    Execute multiple queries sequentially and return results as a list.

    Args:
        queries: List of tuples, each containing (dataset, query) pairs
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        List of StreamResponse objects in the same order as input queries
    """
    results = []
    for dataset, query in queries:
        result = get_data(
            dataset=dataset,
            query=query,
            portal_url=portal_url,
            flattening=flattening,
            stream_type=stream_type,
        )
        results.append(result)
    return results


async def get_multiple_data_async(
        queries: List[tuple],
        portal_url: str = "https://portal.sqd.dev",
        flattening: Optional[str] = "by_itemtype",
        session: Optional[aiohttp.ClientSession] = None,
        max_concurrency: int = 10,
        stream_type: str = "finalized",
) -> List[StreamResponse]:
    """
    Execute multiple queries concurrently and return results as a list.

    Args:
        queries: List of tuples, each containing (dataset, query) pairs
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        session: Shared aiohttp session for connection reuse
        max_concurrency: Maximum number of concurrent requests
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        List of StreamResponse objects in the same order as input queries
    """

    async def execute_query(dataset_query_pair):
        dataset, query = dataset_query_pair
        return await get_data_async(
            dataset=dataset,
            query=query,
            portal_url=portal_url,
            flattening=flattening,
            session=session,
            stream_type=stream_type,
        )

    # Use semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrency)

    async def execute_with_semaphore(dataset_query_pair):
        async with semaphore:
            return await execute_query(dataset_query_pair)

    # Execute all queries concurrently
    tasks = [execute_with_semaphore(query) for query in queries]
    results = await asyncio.gather(*tasks)
    return results


def chain_queries(
        queries: List[SQDQuery],
        dataset: Dataset | str,
        portal_url: str = "https://portal.sqd.dev",
        flattening: Optional[str] = "by_itemtype",
        stream_type: str = "finalized",
) -> List[StreamResponse]:
    """
    Execute multiple queries using the same dataset sequentially.

    Args:
        queries: List of SQDQuery objects
        dataset: Dataset to use for all queries
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        List of StreamResponse objects

    Example:
        sqd = SQD(dataset=Dataset.ETHEREUM)
        queries = [
            sqd.get_transactions(address='0x123...', from_block=1000, to_block=2000),
            sqd.get_logs(address='0x456...', from_block=1500, to_block=2500),
        ]
        results = chain_queries(queries, Dataset.ETHEREUM)
    """
    return get_multiple_data(
        [(dataset, query) for query in queries], portal_url, flattening, stream_type
    )


async def chain_queries_async(
        queries: List[SQDQuery],
        dataset: Dataset | str,
        portal_url: str = "https://portal.sqd.dev",
        flattening: Optional[str] = "by_itemtype",
        session: Optional[aiohttp.ClientSession] = None,
        max_concurrency: int = 10,
        stream_type: str = "finalized",
) -> List[StreamResponse]:
    """
    Execute multiple queries using the same dataset concurrently.

    Args:
        queries: List of SQDQuery objects
        dataset: Dataset to use for all queries
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        session: Shared aiohttp session for connection reuse
        max_concurrency: Maximum number of concurrent requests
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        List of StreamResponse objects

    Example:
        sqd = SQD(dataset=Dataset.ETHEREUM)
        queries = [
            sqd.get_transactions(address='0x123...', from_block=1000, to_block=2000),
            sqd.get_logs(address='0x456...', from_block=1500, to_block=2500),
        ]
        results = await chain_queries_async(queries, Dataset.ETHEREUM)
    """
    query_tuples = [(dataset, query) for query in queries]
    return await get_multiple_data_async(
        query_tuples, portal_url, flattening, session, max_concurrency, stream_type
    )


def combine_query_results(
        results: List[StreamResponse], combine_strategy: str = "concatenate"
) -> List[Dict[str, Any]]:
    """
    Combine multiple query results using different strategies.

    Args:
        results: List of StreamResponse objects to combine
        combine_strategy: How to combine results ('concatenate', 'merge', 'zip')

    Returns:
        Combined results based on the strategy (list of data items)

    Example:
        results = [stream_response1, stream_response2, stream_response3]
        combined = combine_query_results(results, 'concatenate')
    """
    if combine_strategy == "concatenate":
        # Flatten all results into a single list
        combined = []
        for result in results:
            combined.extend(result.data)
        return combined

    elif combine_strategy == "merge":
        # Merge results by common keys (assuming dict results)
        if not results:
            return []

        merged = {}
        for result in results:
            for item in result.data:
                if isinstance(item, dict):
                    key = item.get("id") or item.get("hash") or str(item)
                    merged[key] = item

        return list(merged.values())

    elif combine_strategy == "zip":
        # Combine results element-wise (zip)
        if not results:
            return []

        max_len = max(len(r.data) for r in results)
        zipped = []

        for i in range(max_len):
            row = []
            for result in results:
                if i < len(result.data):
                    row.append(result.data[i])
                else:
                    row.append(None)
            zipped.append(row)

        return zipped

    else:
        raise ValueError(f"Unknown combine strategy: {combine_strategy}")


def get_head(
        *, dataset: Dataset | str, portal_url: str = "https://portal.sqd.dev"
) -> BlockHead:
    """
    Get the highest block available in the dataset (including real-time data).

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        portal_url: SQD portal URL

    Returns:
        BlockHead object with highest block information (null if no blocks available)

    Raises:
        ValueError: If the API request fails (with specific error details)
    """
    endpoint = f"{portal_url}/datasets/{dataset.value}/head"

    try:
        resp = requests.get(endpoint)
        if resp.status_code == 404:
            raise ValueError(f"Dataset not found (404): {resp.text}")
        elif resp.status_code != 200:
            raise ValueError(
                f"API request failed with status {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        return BlockHead.from_dict(data)
    except ValueError:
        # Re-raise ValueError as-is (it has specific API error info)
        raise
    except Exception as e:
        raise ValueError(f"Failed to get head block: {e}") from e


def get_finalized_head(
        *, dataset: Dataset | str, portal_url: str = "https://portal.sqd.dev"
) -> BlockHead:
    """
    Get the highest finalized block available in the dataset.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        portal_url: SQD portal URL

    Returns:
        BlockHead object with highest finalized block information (null if no blocks available)

    Raises:
        ValueError: If the API request fails (with specific error details)
    """
    endpoint = f"{portal_url}/datasets/{dataset.value}/finalized-head"

    try:
        resp = requests.get(endpoint)
        if resp.status_code == 404:
            raise ValueError(f"Dataset not found (404): {resp.text}")
        elif resp.status_code != 200:
            raise ValueError(
                f"API request failed with status {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        return BlockHead.from_dict(data)
    except ValueError:
        # Re-raise ValueError as-is (it has specific API error info)
        raise
    except Exception as e:
        raise ValueError(f"Failed to get finalized head block: {e}") from e


def get_stream(
        *,
        dataset: Dataset | str,
        query: SQDQuery | str,
        portal_url: str = "https://portal.sqd.dev",
        include_all_blocks: bool = False,
) -> StreamResponse:
    """
    Stream blocks matching the query (may include real-time data).

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: SQDQuery/EVM/Solana builder or query string
        portal_url: SQD portal URL
        include_all_blocks: If true, includes blocks with no matching data

    Returns:
        StreamResponse with data and metadata headers

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    endpoint = f"{portal_url}/datasets/{dataset.value}/stream"

    str_query = _as_query_string(query)

    print(f"Executing stream query: {str_query}")
    try:
        response_data, response_headers = fetch_query_output(endpoint, str_query)
        return StreamResponse.from_response(response_data, response_headers)
    except Exception as e:
        error_msg = f"Failed to execute stream query: {e}"
        if "API request failed" in str(e):
            error_msg += (
                "\nThis could be due to:\n"
                "1. Invalid query format\n"
                "2. Network connectivity issues\n"
                "3. SQD API being unavailable\n"
                "4. Invalid dataset or portal URL"
            )
        raise ValueError(error_msg) from e


async def get_stream_async(
        *,
        dataset: Dataset | str,
        query: SQDQuery | str,
        portal_url: str = "https://portal.sqd.dev",
        session: Optional[aiohttp.ClientSession] = None,
        include_all_blocks: bool = False,
) -> StreamResponse:
    """
    Async version of get_stream.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: SQDQuery/EVM/Solana builder or query string
        portal_url: SQD portal URL
        session: Optional aiohttp session for connection reuse
        include_all_blocks: If true, includes blocks with no matching data

    Returns:
        StreamResponse with data and metadata headers

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    endpoint = f"{portal_url}/datasets/{dataset.value}/stream"

    str_query = _as_query_string(query)

    print(f"Executing async stream query: {str_query}")
    try:
        response_data, response_headers = await fetch_query_output_async(
            endpoint, str_query, session
        )
        return StreamResponse.from_response(response_data, response_headers)
    except Exception as e:
        error_msg = f"Failed to execute async stream query: {e}"
        if "API request failed" in str(e):
            error_msg += (
                "\nThis could be due to:\n"
                "1. Invalid query format\n"
                "2. Network connectivity issues\n"
                "3. SQD API being unavailable\n"
                "4. Invalid dataset or portal URL"
            )
        raise ValueError(error_msg) from e


# =============================================================================
# QUERY CHAIN CLASS
# =============================================================================


class QueryChain:
    """
    Fluent interface for chaining multiple queries together.

    Example:
        sqd = SQD(dataset=Dataset.ETHEREUM)
        chain = QueryChain(Dataset.ETHEREUM)
        results = (
            chain.add(sqd.get_transactions(address='0x123...', from_block=1000))
            .add(sqd.get_logs(address='0x456...', from_block=2000))
            .execute()
        )
    """

    def __init__(
            self, dataset: Dataset | str, portal_url: str = "https://portal.sqd.dev"
    ):
        self.dataset = dataset
        self.portal_url = portal_url
        self.queries: List[SQDQuery] = []

    def add(self, query: SQDQuery) -> "QueryChain":
        """Add a query to the chain."""
        self.queries.append(query)
        return self

    def execute(
            self, flattening: Optional[str] = "by_itemtype", stream_type: str = "finalized"
    ) -> List[StreamResponse]:
        """Execute all queries in the chain sequentially."""
        return chain_queries(
            self.queries, self.dataset, self.portal_url, flattening, stream_type
        )

    async def execute_async(
            self,
            flattening: Optional[str] = "by_itemtype",
            session: Optional[aiohttp.ClientSession] = None,
            max_concurrency: int = 10,
            stream_type: str = "finalized",
    ) -> List[StreamResponse]:
        """Execute all queries in the chain concurrently."""
        return await chain_queries_async(
            self.queries,
            self.dataset,
            self.portal_url,
            flattening,
            session,
            max_concurrency,
            stream_type,
        )
