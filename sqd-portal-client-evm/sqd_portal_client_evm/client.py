import asyncio
from typing import List, Dict, Any

import aiohttp

from .dataset import Dataset
from .query import *
from .transport import fetch_query_output, fetch_query_output_async


def get_data(
        *,
        dataset: Dataset | str,
        query: Query | str,
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype'
):
    """
    Get data from SQD portal using a query.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: Query object or query string
        portal_url: SQD portal URL
        flattening: Result flattening strategy

    Returns:
        List of data items from the query

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    endpoint = f'{portal_url}/datasets/{dataset.value}/finalized-stream'

    # Convert Query object to string if needed
    if isinstance(query, Query):
        str_query = query.to_sqd_string()
    else:
        str_query = query

    print(f"Executing query: {str_query}")
    try:
        return fetch_query_output(endpoint, str_query)
    except Exception as e:
        # Provide more helpful error messages
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
    Validate query format and provide helpful feedback.

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

        # Check if it has the expected structure
        query_content = parsed
        if 'type' not in query_content:
            return False, "Query content should have 'type' field"

        if query_content.get('type') != 'evm':
            return False, f"Expected type 'evm', got '{query_content.get('type')}'"

        return True, "Query format looks valid"

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
        session: Optional[aiohttp.ClientSession] = None
):
    """
    Async version of get_data function.

    Args:
        dataset: Dataset to query (e.g., Dataset.ETHEREUM)
        query: Query object or query string
        portal_url: SQD portal URL
        flattening: Result flattening strategy
        session: Optional aiohttp session for connection reuse

    Returns:
        List of data items from the query

    Raises:
        ValueError: If the query is invalid or API returns an error
    """
    endpoint = f'{portal_url}/datasets/{dataset.value}/finalized-stream'

    # Convert Query object to string if needed
    if isinstance(query, Query):
        str_query = query.to_sqd_string()
    else:
        str_query = query

        print(f"Executing async query: {str_query}")
    try:
        return await fetch_query_output_async(endpoint, str_query, session)
    except Exception as e:
        # Provide more helpful error messages
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
        flattening: Optional[str] = 'by_itemtype'
) -> List[Any]:
    """
    Execute multiple queries sequentially and return results as a list.

    Args:
        queries: List of tuples, each containing (dataset, query) pairs
        portal_url: SQD portal URL
        flattening: Result flattening strategy

    Returns:
        List of query results in the same order as input queries

    Example:
        queries = [
            (Dataset.ETHEREUM, Query.transactions(from_address='0x123...', from_block=1000)),
            (Dataset.ETHEREUM, Query.logs_from_contract('0x456...', from_block=2000)),
        ]
        results = get_multiple_data(queries)
    """
    results = []
    for dataset, query in queries:
        result = get_data(dataset=dataset, query=query, portal_url=portal_url, flattening=flattening)
        results.append(result)
    return results


async def get_multiple_data_async(
        queries: List[tuple],
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype',
        session: Optional[aiohttp.ClientSession] = None,
        max_concurrency: int = 10
) -> List[Any]:
    """
    Execute multiple queries concurrently and return results as a list.

    Args:
        queries: List of tuples, each containing (dataset, query) pairs
        portal_url: SQD portal URL
        flattening: Result flattening strategy
        session: Shared aiohttp session for connection reuse
        max_concurrency: Maximum number of concurrent requests

    Returns:
        List of query results in the same order as input queries

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
            session=session
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
        flattening: Optional[str] = 'by_itemtype'
) -> List[Any]:
    """
    Execute multiple queries using the same dataset sequentially.

    Args:
        queries: List of Query objects
        dataset: Dataset to use for all queries
        portal_url: SQD portal URL
        flattening: Result flattening strategy

    Returns:
        List of query results

    Example:
        queries = [
            Query.transactions(from_address='0x123...', from_block=1000, to_block=2000),
            Query.logs_from_contract('0x456...', from_block=1500, to_block=2500),
        ]
        results = chain_queries(queries, Dataset.ETHEREUM)
    """
    return get_multiple_data([(dataset, query) for query in queries], portal_url, flattening)


async def chain_queries_async(
        queries: List[Query],
        dataset: Dataset | str,
        portal_url: str = 'https://portal.sqd.dev',
        flattening: Optional[str] = 'by_itemtype',
        session: Optional[aiohttp.ClientSession] = None,
        max_concurrency: int = 10
) -> List[Any]:
    """
    Execute multiple queries using the same dataset concurrently.

    Args:
        queries: List of Query objects
        dataset: Dataset to use for all queries
        portal_url: SQD portal URL
        flattening: Result flattening strategy
        session: Shared aiohttp session for connection reuse
        max_concurrency: Maximum number of concurrent requests

    Returns:
        List of query results

    Example:
        queries = [
            Query.transactions(from_address='0x123...', from_block=1000, to_block=2000),
            Query.logs_from_contract('0x456...', from_block=1500, to_block=2500),
        ]
        results = await chain_queries_async(queries, Dataset.ETHEREUM)
    """
    query_tuples = [(dataset, query) for query in queries]
    return await get_multiple_data_async(query_tuples, portal_url, flattening, session, max_concurrency)


def combine_query_results(results: List[Any], combine_strategy: str = 'concatenate') -> Any:
    """
    Combine multiple query results using different strategies.

    Args:
        results: List of query results to combine
        combine_strategy: How to combine results ('concatenate', 'merge', 'zip')

    Returns:
        Combined results based on the strategy

    Example:
        results = [transactions_data, logs_data, traces_data]
        combined = combine_query_results(results, 'concatenate')
    """
    if combine_strategy == 'concatenate':
        # Flatten all results into a single list
        combined = []
        for result in results:
            if isinstance(result, list):
                combined.extend(result)
            else:
                combined.append(result)
        return combined

    elif combine_strategy == 'merge':
        # Merge results by common keys (assuming dict results)
        if not results:
            return []

        merged = {}
        for result in results:
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        key = item.get('id') or item.get('hash') or str(item)
                        merged[key] = item
            elif isinstance(result, dict):
                key = result.get('id') or result.get('hash') or str(result)
                merged[key] = result

        return list(merged.values())

    elif combine_strategy == 'zip':
        # Combine results element-wise (zip)
        if not results or not all(isinstance(r, list) for r in results):
            return results

        max_len = max(len(r) for r in results)
        zipped = []

        for i in range(max_len):
            row = []
            for result in results:
                if i < len(result):
                    row.append(result[i])
                else:
                    row.append(None)
            zipped.append(row)

        return zipped

    else:
        raise ValueError(f"Unknown combine strategy: {combine_strategy}")


def filter_combined_results(
        combined_results: Any,
        filters: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Filter combined query results based on criteria.

    Args:
        combined_results: Results from combine_query_results
        filters: Dictionary of field-value pairs to filter by

    Returns:
        Filtered results

    Example:
        filters = {'block_height': 17000000, 'address': '0x123...'}
        filtered = filter_combined_results(combined, filters)
    """
    if not filters:
        return combined_results

    if isinstance(combined_results, list):
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
            elif isinstance(item, list):
                # For nested structures (like zipped results)
                filtered_item = filter_combined_results(item, filters)
                if filtered_item and any(x is not None for x in filtered_item):
                    filtered.append(filtered_item)
        return filtered

    return combined_results


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

    def execute(self, flattening: Optional[str] = 'by_itemtype') -> List[Any]:
        """Execute all queries in the chain sequentially."""
        return chain_queries(self.queries, self.dataset, self.portal_url, flattening)

    async def execute_async(
            self,
            flattening: Optional[str] = 'by_itemtype',
            session: Optional[aiohttp.ClientSession] = None,
            max_concurrency: int = 10
    ) -> List[Any]:
        """Execute all queries in the chain concurrently."""
        return await chain_queries_async(
            self.queries, self.dataset, self.portal_url, flattening, session, max_concurrency
        )
