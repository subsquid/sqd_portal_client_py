"""
SQD Portal Client Query Module

This module provides the main query interface for building SQD (Subsquid) Network portal queries.

Basic Usage:
    from sqd_portal_client_evm import get_data, Dataset
    # Query proxy class is defined below

    # Simple EVM queries using builder pattern
    query = Query.evm.get_transactions(from_address='0x123...', from_block=17000000)
    data = get_data(dataset=Dataset.ETHEREUM, query=query)

    # Simple Solana queries using builder pattern
    query = Query.solana.get_instructions(program_id='11111111111111111111111111111112', from_block=200000000)
    data = get_data(dataset=Dataset.SOLANA, query=query)

    # Manual query construction for advanced use cases (not recommended - use builders instead)
    # query = Query(  # This internal class should not be used directly
    #     from_block=1000000,
    #     to_block=1000100,
    #     transactionsRequests=[
    #         Query.TransactionsRequest(from_=['0x123...'], to=['0x456...'])
    #     ],
    #     fields=Query.Fields.minimal_fields()
    # )
    data = get_data(dataset=Dataset.ETHEREUM, query=query)
"""

try:
    import ujson as json_lib
except ImportError:
    import json as json_lib

# Import EVM and Solana specific modules
from sqd_portal_client_evm.query.evm import EVMQueryBuilder
from .solana import SolanaQueryBuilder
from .base.base import _Fields


# Main Query proxy class - this is what users will use
class Query:
    """
    Main query factory class for building SQD Network portal queries.

    This class provides access to EVM and Solana query builders through simple attributes.

    Basic usage:
        # Access EVM query builder
        evm_builder = Query.evm

        # Access Solana query builder
        solana_builder = Query.solana

        # Create queries using the builders
        query = Query.evm.get_transactions(from_address='0x123...', from_block=17000000)
        query = Query.solana.get_instructions(program_id='11111111111111111111111111111112', from_block=200000000)

        # Or create queries directly
        query = Query(from_block=1000, to_block=2000, transactionsRequests=[])
    """

    # Query builders as class attributes
    evm: EVMQueryBuilder = EVMQueryBuilder()
    solana: SolanaQueryBuilder = SolanaQueryBuilder()
    Fields = _Fields
