"""
SQD Portal Client Query Package

This package provides a clean, organized interface for building SQD (Subsquid) Network portal queries.

The package is organized into subpackages:
- evm/: EVM-specific query builders, fields, and requests
- solana/: Solana-specific query builders, fields, and requests

Basic Usage:
    from sqd_portal_client_evm.query import SQD

    sqd = SQD(dataset=Dataset.ETHEREUM)
    query = sqd.get_transactions(address='0x123...', from_block=17_000_000)
    async for tx in query:
        print(tx)
"""

from .query import (
    SQD,
    SQDQuery,
    TransactionField,
    LogField,
    InstructionField,
    SolanaTransactionField,
    SolanaLogField,
    BalanceField,
    TokenBalanceField,
    RewardField,
    SolanaBlockField,
)

__all__ = [
    "SQD",
    "SQDQuery",
    "TransactionField",
    "LogField",
    "InstructionField",
    "SolanaTransactionField",
    "SolanaLogField",
    "BalanceField",
    "TokenBalanceField",
    "RewardField",
    "SolanaBlockField",
]
