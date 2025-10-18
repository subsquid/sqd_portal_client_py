import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

import aiohttp
import requests

from .dataset import Dataset
from .query import Query
from .transport import fetch_query_output, fetch_query_output_async


@dataclass
class DatasetMetadata:
    """Dataset metadata response from /metadata endpoint."""
    dataset: str
    aliases: List[str]
    real_time: bool
    start_block: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetMetadata':
        return cls(
            dataset=data['dataset'],
            aliases=data['aliases'],
            real_time=data['real_time'],
            start_block=data['start_block']
        )


@dataclass
class BlockHead:
    """Block head response from /head and /finalized-head endpoints."""
    number: Optional[int]
    hash: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockHead':
        return cls(
            number=data.get('number'),
            hash=data.get('hash')
        )


@dataclass
class ConflictResponse:
    """Conflict response from API when there's a parent block hash mismatch."""
    previousBlocks: List[Dict[str, Union[int, str]]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConflictResponse':
        return cls(previousBlocks=data['previousBlocks'])


@dataclass
class StreamResponse:
    """Response from streaming endpoints with metadata."""
    data: List[Dict[str, Any]]
    finalized_head_number: Optional[int] = None
    finalized_head_hash: Optional[str] = None

    @classmethod
    def from_response(cls, response_data: List[Dict[str, Any]], response_headers: Dict[str, str]) -> 'StreamResponse':
        return cls(
            data=response_data,
            finalized_head_number=int(response_headers.get('X-Sqd-Finalized-Head-Number', 0)) if response_headers.get('X-Sqd-Finalized-Head-Number') else None,
            finalized_head_hash=response_headers.get('X-Sqd-Finalized-Head-Hash')
        )


def get_data(
        *,
        dataset: Dataset | str,
        query: Query | str,
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype',
        stream_type: str = 'finalized'
):
    """
    Get data from SQD portal using a query.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: Query object or query string
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        StreamResponse with data and metadata headers

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    if stream_type not in ['finalized', 'stream']:
        raise ValueError(f"Invalid stream_type: {stream_type}. Must be 'finalized' or 'stream'")

    endpoint = f'{portal_url}/datasets/{dataset.value}/{stream_type}-stream'

    # Convert Query object to string if needed
    if isinstance(query, Query):
        str_query = query.to_sqd_string()
    else:
        str_query = query

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
            error_msg += "\nThis could be due to:\n" \
                         "1. Invalid query format\n" \
                         "2. Network connectivity issues\n" \
                         "3. SQD API being unavailable\n" \
                         "4. Invalid dataset or portal URL"
        elif "Failed to parse API response" in str(e):
            error_msg += "\nThis could be due to:\n" \
                         "1. Unexpected response format from API\n" \
                         "2. API returning HTML error page instead of JSON"
        raise ValueError(error_msg) from e


def validate_query_format(query: Query | str) -> tuple[bool, str]:
    """
    Validate query format against OpenAPI DataQuery schema and provide helpful feedback.

    Args:
        query: Query object or string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if isinstance(query, Query):
            query_str = query.to_sqd_string()
        else:
            query_str = query

        # Try to parse the JSON to check format
        import json
        parsed = json.loads(query_str)

        # Check required fields according to OpenAPI DataQuery schema
        if 'type' not in parsed:
            return False, "Missing required field: 'type'"

        if 'fromBlock' not in parsed:
            return False, "Missing required field: 'fromBlock'"

        # Validate field types and values
        query_content = parsed

        # Type must be 'evm' for this API
        if query_content.get('type') != 'evm':
            return False, f"Invalid type: expected 'evm', got '{query_content.get('type')}'"

        # fromBlock must be integer >= 0
        from_block = query_content.get('fromBlock')
        if not isinstance(from_block, int) or from_block < 0:
            return False, f"Invalid fromBlock: must be non-negative integer, got {from_block}"

        # toBlock must be integer >= fromBlock if provided
        to_block = query_content.get('toBlock')
        if to_block is not None:
            if not isinstance(to_block, int):
                return False, f"Invalid toBlock: must be integer, got {to_block}"
            if to_block < from_block:
                return False, f"Invalid toBlock: must be >= fromBlock ({from_block}), got {to_block}"

        # parentBlockHash must be string if provided
        parent_hash = query_content.get('parentBlockHash')
        if parent_hash is not None and not isinstance(parent_hash, str):
            return False, f"Invalid parentBlockHash: must be string, got {type(parent_hash)}"

        # includeAllBlocks must be boolean if provided
        include_all = query_content.get('includeAllBlocks')
        if include_all is not None and not isinstance(include_all, bool):
            return False, f"Invalid includeAllBlocks: must be boolean, got {type(include_all)}"

        # fields must be object if provided
        fields = query_content.get('fields')
        if fields is not None and not isinstance(fields, dict):
            return False, f"Invalid fields: must be object, got {type(fields)}"

        # Validate request arrays
        for request_type in ['logs', 'transactions', 'traces', 'stateDiffs']:
            requests = query_content.get(f'{request_type}Requests', query_content.get(request_type, []))
            if requests and not isinstance(requests, list):
                return False, f"Invalid {request_type}: must be array, got {type(requests)}"

        return True, "Query format is valid according to OpenAPI schema"

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {e}"
    except Exception as e:
        return False, f"Query validation failed: {e}"


async def get_data_async(
        *,
        dataset: Dataset | str,
        query: Query | str,
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype',
        session: Optional[aiohttp.ClientSession] = None,
        stream_type: str = 'finalized'
):
    """
    Async version of get_data function.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: Query object or query string
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        session: Optional aiohttp session for connection reuse
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        StreamResponse with data and metadata headers

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    if stream_type not in ['finalized', 'stream']:
        raise ValueError(f"Invalid stream_type: {stream_type}. Must be 'finalized' or 'stream'")

    endpoint = f'{portal_url}/datasets/{dataset.value}/{stream_type}-stream'

    # Convert Query object to string if needed
    if isinstance(query, Query):
        str_query = query.to_sqd_string()
    else:
        str_query = query

        print(f"Executing async query: {str_query}")
    try:
        response_data, response_headers = await fetch_query_output_async(endpoint, str_query, session)
        return StreamResponse.from_response(response_data, response_headers)
    except ValueError as e:
        # Re-raise ValueError exceptions as-is (they have specific API error info)
        raise e
    except Exception as e:
        # Provide more helpful error messages for unexpected errors
        error_msg = f"Failed to execute async query: {e}"
        if "API request failed" in str(e):
            error_msg += "\nThis could be due to:\n" \
                         "1. Invalid query format\n" \
                         "2. Network connectivity issues\n" \
                         "3. SQD API being unavailable\n" \
                         "4. Invalid dataset or portal URL"
        elif "Failed to parse API response" in str(e):
            error_msg += "\nThis could be due to:\n" \
                         "1. Unexpected response format from API\n" \
                         "2. API returning HTML error page instead of JSON"
        raise ValueError(error_msg) from e


def get_multiple_data(
        queries: List[tuple],
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype',
        stream_type: str = 'finalized'
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

    Example:
        queries = [
            (Dataset.ETHEREUM, Query.transactions(from_address='0x123...', from_block=1000)),
            (Dataset.ETHEREUM, Query.logs_from_contract('0x456...', from_block=2000)),
        ]
        results = get_multiple_data(queries)
    """
    results = []
    for dataset, query in queries:
        result = get_data(dataset=dataset, query=query, portal_url=portal_url, flattening=flattening, stream_type=stream_type)
        results.append(result)
    return results


async def get_multiple_data_async(
        queries: List[tuple],
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype',
        session: Optional[aiohttp.ClientSession] = None,
        max_concurrency: int = 10,
        stream_type: str = 'finalized'
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

    Example:
        queries = [
            (Dataset.ETHEREUM, Query.transactions(from_address='0x123...', from_block=1000)),
            (Dataset.ETHEREUM, Query.logs_from_contract('0x456...', from_block=2000)),
        ]
        results = await get_multiple_data_async(queries)
    """

    async def execute_query(dataset_query_pair):
        dataset, query = dataset_query_pair
        return await get_data_async(
            dataset=dataset,
            query=query,
            portal_url=portal_url,
            flattening=flattening,
            session=session,
            stream_type=stream_type
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
        queries: List[Query],
        dataset: Dataset | str,
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype',
        stream_type: str = 'finalized'
) -> List[StreamResponse]:
    """
    Execute multiple queries using the same dataset sequentially.

    Args:
        queries: List of Query objects
        dataset: Dataset to use for all queries
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        List of StreamResponse objects

    Example:
        queries = [
            Query.transactions(from_address='0x123...', from_block=1000, to_block=2000),
            Query.logs_from_contract('0x456...', from_block=1500, to_block=2500),
        ]
        results = chain_queries(queries, Dataset.ETHEREUM)
    """
    return get_multiple_data([(dataset, query) for query in queries], portal_url, flattening, stream_type)


async def chain_queries_async(
        queries: List[Query],
        dataset: Dataset | str,
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype',
        session: Optional[aiohttp.ClientSession] = None,
        max_concurrency: int = 10,
        stream_type: str = 'finalized'
) -> List[StreamResponse]:
    """
    Execute multiple queries using the same dataset concurrently.

    Args:
        queries: List of Query objects
        dataset: Dataset to use for all queries
        portal_url: SQD portal URL
        flattening: Result flattening strategy (deprecated - kept for compatibility)
        session: Shared aiohttp session for connection reuse
        max_concurrency: Maximum number of concurrent requests
        stream_type: Type of stream to use ('finalized' or 'stream')

    Returns:
        List of StreamResponse objects

    Example:
        queries = [
            Query.transactions(from_address='0x123...', from_block=1000, to_block=2000),
            Query.logs_from_contract('0x456...', from_block=1500, to_block=2500),
        ]
        results = await chain_queries_async(queries, Dataset.ETHEREUM)
    """
    query_tuples = [(dataset, query) for query in queries]
    return await get_multiple_data_async(query_tuples, portal_url, flattening, session, max_concurrency, stream_type)


def combine_query_results(results: List[StreamResponse], combine_strategy: str = 'concatenate') -> List[Dict[str, Any]]:
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
    if combine_strategy == 'concatenate':
        # Flatten all results into a single list
        combined = []
        for result in results:
            combined.extend(result.data)
        return combined

    elif combine_strategy == 'merge':
        # Merge results by common keys (assuming dict results)
        if not results:
            return []

        merged = {}
        for result in results:
            for item in result.data:
                if isinstance(item, dict):
                    key = item.get('id') or item.get('hash') or str(item)
                    merged[key] = item

        return list(merged.values())

    elif combine_strategy == 'zip':
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


def filter_combined_results(
        combined_results: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Filter combined query results based on criteria.

    Args:
        combined_results: Results from combine_query_results (list of data items)
        filters: Dictionary of field-value pairs to filter by

    Returns:
        Filtered results (list of data items)

    Example:
        filters = {'block_height': 17000000, 'address': '0x123...'}
        filtered = filter_combined_results(combined, filters)
    """
    if not filters:
        return combined_results

    filtered = []
    for item in combined_results:
        if isinstance(item, dict):
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered.append(item)

    return filtered


# =============================================================================
# NEW ENDPOINT METHODS (based on OpenAPI specification)
# =============================================================================

def get_dataset_metadata(
    *,
    dataset: Dataset | str,
    portal_url: str = 'https://portal.sqd.dev'
) -> DatasetMetadata:
    """
    Get dataset metadata including name, aliases, start block, and real-time status.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        portal_url: SQD portal URL

    Returns:
        DatasetMetadata object with dataset information

    Raises:
        ValueError: If the API request fails (with specific error details)
    """
    endpoint = f'{portal_url}/datasets/{dataset.value}/metadata'

    try:
        resp = requests.get(endpoint)
        if resp.status_code == 404:
            raise ValueError(f"Dataset not found (404): {resp.text}")
        elif resp.status_code != 200:
            raise ValueError(f"API request failed with status {resp.status_code}: {resp.text}")

        data = resp.json()
        return DatasetMetadata.from_dict(data)
    except ValueError:
        # Re-raise ValueError as-is (it has specific API error info)
        raise
    except Exception as e:
        raise ValueError(f"Failed to get dataset metadata: {e}") from e


def get_head(
    *,
    dataset: Dataset | str,
    portal_url: str = 'https://portal.sqd.dev'
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
    endpoint = f'{portal_url}/datasets/{dataset.value}/head'

    try:
        resp = requests.get(endpoint)
        if resp.status_code == 404:
            raise ValueError(f"Dataset not found (404): {resp.text}")
        elif resp.status_code != 200:
            raise ValueError(f"API request failed with status {resp.status_code}: {resp.text}")

        data = resp.json()
        return BlockHead.from_dict(data)
    except ValueError:
        # Re-raise ValueError as-is (it has specific API error info)
        raise
    except Exception as e:
        raise ValueError(f"Failed to get head block: {e}") from e


def get_finalized_head(
    *,
    dataset: Dataset | str,
    portal_url: str = 'https://portal.sqd.dev'
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
    endpoint = f'{portal_url}/datasets/{dataset.value}/finalized-head'

    try:
        resp = requests.get(endpoint)
        if resp.status_code == 404:
            raise ValueError(f"Dataset not found (404): {resp.text}")
        elif resp.status_code != 200:
            raise ValueError(f"API request failed with status {resp.status_code}: {resp.text}")

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
    query: Query | str,
    portal_url: str = 'https://portal.sqd.dev',
    include_all_blocks: bool = False
) -> StreamResponse:
    """
    Stream blocks matching the query (may include real-time data).

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: Query object or query string
        portal_url: SQD portal URL
        include_all_blocks: If true, includes blocks with no matching data

    Returns:
        StreamResponse with data and metadata headers

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    endpoint = f'{portal_url}/datasets/{dataset.value}/stream'

    # Convert Query object to string if needed
    if isinstance(query, Query):
        str_query = query.to_sqd_string()
    else:
        str_query = query

    print(f"Executing stream query: {str_query}")
    try:
        response_data, response_headers = fetch_query_output(endpoint, str_query)
        return StreamResponse.from_response(response_data, response_headers)
    except Exception as e:
        error_msg = f"Failed to execute stream query: {e}"
        if "API request failed" in str(e):
            error_msg += "\nThis could be due to:\n" \
                         "1. Invalid query format\n" \
                         "2. Network connectivity issues\n" \
                         "3. SQD API being unavailable\n" \
                         "4. Invalid dataset or portal URL"
        raise ValueError(error_msg) from e


async def get_stream_async(
    *,
    dataset: Dataset | str,
    query: Query | str,
    portal_url: str = 'https://portal.sqd.dev',
    session: Optional[aiohttp.ClientSession] = None,
    include_all_blocks: bool = False
) -> StreamResponse:
    """
    Async version of get_stream.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: Query object or query string
        portal_url: SQD portal URL
        session: Optional aiohttp session for connection reuse
        include_all_blocks: If true, includes blocks with no matching data

    Returns:
        StreamResponse with data and metadata headers

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    endpoint = f'{portal_url}/datasets/{dataset.value}/stream'

    # Convert Query object to string if needed
    if isinstance(query, Query):
        str_query = query.to_sqd_string()
    else:
        str_query = query

    print(f"Executing async stream query: {str_query}")
    try:
        response_data, response_headers = await fetch_query_output_async(endpoint, str_query, session)
        return StreamResponse.from_response(response_data, response_headers)
    except Exception as e:
        error_msg = f"Failed to execute async stream query: {e}"
        if "API request failed" in str(e):
            error_msg += "\nThis could be due to:\n" \
                         "1. Invalid query format\n" \
                         "2. Network connectivity issues\n" \
                         "3. SQD API being unavailable\n" \
                         "4. Invalid dataset or portal URL"
        raise ValueError(error_msg) from e


# =============================================================================
# QUERY CHAIN CLASS
# =============================================================================

class QueryChain:
    """
    Fluent interface for chaining multiple queries together.

    Example:
        chain = QueryChain(Dataset.ETHEREUM)
        results = (chain
            .add(Query.transactions(from_address='0x123...', from_block=1000))
            .add(Query.logs_from_contract('0x456...', from_block=2000))
            .execute()
        )
    """

    def __init__(self, dataset: Dataset | str, portal_url: str = 'https://portal.sqd.dev'):
        self.dataset = dataset
        self.portal_url = portal_url
        self.queries: List[Query] = []

    def add(self, query: Query) -> 'QueryChain':
        """Add a query to the chain."""
        self.queries.append(query)
        return self

    def execute(self, flattening: Optional[str] = 'by_itemtype', stream_type: str = 'finalized') -> List[StreamResponse]:
        """Execute all queries in the chain sequentially."""
        return chain_queries(self.queries, self.dataset, self.portal_url, flattening, stream_type)

    async def execute_async(
            self,
            flattening: Optional[str] = 'by_itemtype',
            session: Optional[aiohttp.ClientSession] = None,
            max_concurrency: int = 10,
            stream_type: str = 'finalized'
    ) -> List[StreamResponse]:
        """Execute all queries in the chain concurrently."""
        return await chain_queries_async(
            self.queries, self.dataset, self.portal_url, flattening, session, max_concurrency, stream_type
        )
