"""
Solana Query Package

This package provides Solana-specific query functionality for the SQD Portal Client.
"""

from .fields import (
    BalanceField,
    InstructionField,
    RewardField,
    SolanaBlockField,
    SolanaLogField,
    SolanaTransactionField,
    TokenBalanceField,
)
from .requests import (
    BalancesRequest,
    InstructionsRequest,
    RewardsRequest,
    SolanaLogsRequest,
    SolanaTransactionsRequest,
    TokenBalancesRequest,
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
