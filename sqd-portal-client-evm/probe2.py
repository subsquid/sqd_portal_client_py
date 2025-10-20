"""
SQD Portal Client Examples - Query Chaining

This file demonstrates various ways to chain multiple queries together.
"""

from sqd_portal_client_evm import Dataset
from sqd_portal_client_evm.client import get_data
from sqd_portal_client_evm.query.query import Query

VITALIK_ETH = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045".lower()
USDC_ETH = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48".lower()

query = Query.evm.get_transactions(
    from_address=VITALIK_ETH, from_block=12312321, to_block=12313321
)

print(get_data(query=query, dataset=Dataset.ETHEREUM))
print()
