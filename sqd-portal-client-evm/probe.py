"""
SQD Portal Client Examples - Query Chaining

This file demonstrates various ways to chain multiple queries together.
"""

import asyncio

from sqd_portal_client_evm import Dataset
from sqd_portal_client_evm.client import (
    get_multiple_data,
    get_multiple_data_async,
    chain_queries,
    chain_queries_async,
    combine_query_results,
    filter_combined_results,
    QueryChain,
)
from sqd_portal_client_evm.query import Query

VITALIK_ETH = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045".lower()
USDC_ETH = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48".lower()

# =============================================================================
# BASIC QUERY CHAINING EXAMPLES
# =============================================================================


def example_basic_chaining():
    """Example 1: Basic sequential query chaining"""
    print("=== Example 1: Basic Sequential Query Chaining ===")

    # Define multiple queries
    queries = [
        (
            Dataset.ETHEREUM,
            Query.transactions(
                from_address=VITALIK_ETH, from_block=17000000, to_block=17000010
            ),
        ),
        (
            Dataset.ETHEREUM,
            Query.logs_from_contract(USDC_ETH, from_block=17000000, to_block=17000010),
        ),
        (
            Dataset.ETHEREUM,
            Query.simple_block_range(from_block=17000000, to_block=17000010),
        ),
    ]

    # Execute queries sequentially
    results = get_multiple_data(queries)
    print(f"Executed {len(results)} queries sequentially")
    for i, result in enumerate(results):
        print(
            f"Query {i + 1} returned {len(result) if isinstance(result, list) else 1} items"
        )

    return results


async def example_async_chaining():
    """Example 2: Async parallel query chaining"""
    print("\n=== Example 2: Async Parallel Query Chaining ===")

    # Define multiple queries
    queries = [
        (
            Dataset.ETHEREUM,
            Query.evm.get_transactions(
                from_address=VITALIK_ETH, from_block=17000000, to_block=17000010
            ),
        ),
        (
            Dataset.ETHEREUM,
            Query.evm.get_logs(USDC_ETH, from_block=17000000, to_block=17000010),
        ),
        (
            Dataset.ETHEREUM,
            Query.evm.get_erc20_transfers(
                USDC_ETH, from_block=17000000, to_block=17000010
            ),
        ),
    ]

    # Execute queries in parallel (concurrently)
    results = await get_multiple_data_async(queries, max_concurrency=3)
    print(f"Executed {len(results)} queries in parallel")
    for i, result in enumerate(results):
        print(
            f"Query {i + 1} returned {len(result) if isinstance(result, list) else 1} items"
        )

    return results


def example_same_dataset_chaining():
    """Example 3: Chaining queries with the same dataset"""
    print("\n=== Example 3: Same Dataset Query Chaining ===")

    # Define queries for the same dataset
    queries = [
        Query.transactions(
            from_address=VITALIK_ETH, from_block=17000000, to_block=17000010
        ),
        Query.logs_from_contract(USDC_ETH, from_block=17000000, to_block=17000010),
        Query.simple_block_range(from_block=17000000, to_block=17000010),
    ]

    # Execute all queries with the same dataset
    results = chain_queries(queries, Dataset.ETHEREUM)
    print(f"Executed {len(results)} queries with dataset {Dataset.ETHEREUM}")
    for i, result in enumerate(results):
        print(
            f"Query {i + 1} returned {len(result) if isinstance(result, list) else 1} items"
        )

    return results


async def example_fluent_chaining():
    """Example 4: Fluent interface for query chaining"""
    print("\n=== Example 4: Fluent Query Chaining ===")

    # Use the fluent QueryChain interface
    chain = QueryChain(Dataset.ETHEREUM)
    results = (
        chain.add(
            Query.transactions(
                from_address=VITALIK_ETH, from_block=17000000, to_block=17000010
            )
        )
        .add(Query.logs_from_contract(USDC_ETH, from_block=17000000, to_block=17000010))
        .add(Query.erc20_transfers(USDC_ETH, from_block=17000000, to_block=17000010))
        .execute()
    )

    print(f"Executed {len(results)} queries using fluent interface")
    for i, result in enumerate(results):
        print(
            f"Query {i + 1} returned {len(result) if isinstance(result, list) else 1} items"
        )

    return results


def example_result_combination():
    """Example 5: Combining and filtering query results"""
    print("\n=== Example 5: Result Combination and Filtering ===")

    # Get multiple results
    queries = [
        Query.transactions(
            from_address=VITALIK_ETH, from_block=17000000, to_block=17000010
        ),
        Query.logs_from_contract(USDC_ETH, from_block=17000000, to_block=17000010),
    ]

    results = chain_queries(queries, Dataset.ETHEREUM)

    # Combine results in different ways
    concatenated = combine_query_results(results, "concatenate")
    merged = combine_query_results(results, "merge")

    print(f"Original results: {len(results)} queries")
    print(
        f"Concatenated: {len(concatenated) if isinstance(concatenated, list) else 1} items"
    )
    print(f"Merged: {len(merged) if isinstance(merged, list) else 1} items")

    # Filter results
    filters = {"block_height": 17000050}  # Example filter
    filtered = filter_combined_results(concatenated, filters)
    print(
        f"Filtered results: {len(filtered) if isinstance(filtered, list) else 1} items"
    )

    return concatenated, merged, filtered


async def example_comprehensive_workflow():
    """Example 6: Comprehensive workflow with async chaining"""
    print("\n=== Example 6: Comprehensive Async Workflow ===")

    # Build a complex query chain
    queries = [
        Query.transactions(
            from_address=VITALIK_ETH, from_block=17000000, to_block=17000010
        ),
        Query.logs_from_contract(USDC_ETH, from_block=17000000, to_block=17000010),
        Query.erc20_transfers(USDC_ETH, from_block=17000000, to_block=17000010),
        Query.simple_block_range(from_block=17000000, to_block=17000010),
    ]

    # Execute all queries concurrently
    results = await chain_queries_async(queries, Dataset.ETHEREUM, max_concurrency=4)

    print(f"Executed {len(results)} queries concurrently")

    # Combine results
    combined = combine_query_results(results, "concatenate")
    print(f"Combined {len(results)} results into {len(combined)} total items")

    # Demonstrate filtering
    sample_filters = {"address": VITALIK_ETH}
    filtered = filter_combined_results(combined, sample_filters)
    print(f"After filtering: {len(filtered)} items match criteria")

    return results, combined, filtered


# =============================================================================
# RUN EXAMPLES (commented out to avoid execution during import)
# =============================================================================

if __name__ == "__main__":
    print("SQD Portal Client - Query Chaining Examples")
    print("=" * 50)

    # Run synchronous examples
    try:
        example_basic_chaining()
        example_same_dataset_chaining()
        example_result_combination()

        # Run async examples
        asyncio.run(example_async_chaining())
        asyncio.run(example_fluent_chaining())
        asyncio.run(example_comprehensive_workflow())

        print("\n" + "=" * 50)
        print("All examples completed successfully!")

    except Exception as e:
        print(f"Example execution failed: {e}")
        print(
            "Note: These examples require actual SQD portal access to run successfully."
        )
