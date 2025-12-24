"""
Solana Query Package

This package provides Solana-specific query functionality for the SQD Portal Client.
"""

from .requests import (
    InstructionsRequest,
    SolanaTransactionsRequest,
    BalancesRequest,
    TokenBalancesRequest,
    RewardsRequest,
    SolanaLogsRequest,
)
from .fields import (
    BalanceField,
    InstructionField,
    RewardField,
    SolanaBlockField,
    SolanaLogField,
    SolanaTransactionField,
    TokenBalanceField,
)

__all__ = [
    # request classes
    "InstructionsRequest",
    "SolanaTransactionsRequest",
    "BalancesRequest",
    "TokenBalancesRequest",
    "RewardsRequest",
    "SolanaLogsRequest",
    # field enums
    "BalanceField",
    "InstructionField",
    "RewardField",
    "SolanaBlockField",
    "SolanaLogField",
    "SolanaTransactionField",
    "TokenBalanceField",
]
