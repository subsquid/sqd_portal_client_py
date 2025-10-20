"""
SQD Portal Client Query Package

This package provides a clean, organized interface for building SQD (Subsquid) Network portal queries.

The package is organized into subpackages:
- evm/: EVM-specific query builders, fields, and requests
- solana/: Solana-specific query builders, fields, and requests

Basic Usage:
    from sqd_portal_client_evm.query import Query

    # Use the proxy class
    query = Query.evm.get_transactions(from_address='0x123...', from_block=17000000)
    query = Query.solana.get_instructions(program_id='11111111111111111111111111111112', from_block=200000000)
"""

from .query import Query

__all__ = ["Query"]
