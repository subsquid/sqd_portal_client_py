from sqd_portal_client_evm import get_data_async, Query, Dataset
from sqd_portal_client_evm.client import validate_query_format

# Test with a simple query that has filters to avoid the warning
query = Query.transactions(from_address='0x742d35Cc6634C0532925a3b84444444444444444', from_block=17000000,
                           to_block=17000100)


async def main():
    try:
        print("Testing SQD Portal Client...")
        print(f"Query: {query.to_sqd_string()}")

        # Validate query format before sending
        is_valid, validation_msg = validate_query_format(query)
        print(f"Query validation: {'✓ Valid' if is_valid else '✗ Invalid'} - {validation_msg}")

        if not is_valid:
            print("Please fix the query format before proceeding.")
            return

        result = await get_data_async(query=query, dataset=Dataset.ETHEREUM)
        print(f"Success! Retrieved {len(result)} items")

        if result:
            print("Sample item keys:", list(result[0].keys()) if isinstance(result[0], dict) else type(result[0]))

    except Exception as e:
        print(f"Error: {e}")
        print("This might be expected if:")
        print("1. The SQD API is not accessible")
        print("2. The query format is still incorrect")
        print("3. Network connectivity issues")
        print("4. The dataset or portal URL is invalid")


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
