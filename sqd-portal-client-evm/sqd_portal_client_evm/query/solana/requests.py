"""
Solana Request classes for SQD Portal Client

This module provides Solana-specific request classes for filtering blockchain data.
"""

from dataclasses import dataclass
from typing import Optional

from sqd_portal_client_evm.utils import _request_to_sqd_string


@dataclass(frozen=True, kw_only=True)
class InstructionsRequest:
    """
    Request for filtering Solana instructions by various criteria.

    Args:
        programId: List of program IDs that executed the instructions
        d1, d2, d4, d8: Byte discriminators for instruction data
        mentionsAccount: Accounts mentioned in the instruction
        a0-a15: Accounts at specific positions in the accounts array
        isCommitted: Whether the instruction was committed
        transaction: Include parent transaction
        transactionBalances: Include SOL balance updates
        transactionTokenBalances: Include token balance updates
        transactionInstructions: Include sibling instructions
        innerInstructions: Include inner instructions (subtrees)
        logs: Include logs produced by the instruction
    """

    programId: Optional[list[str]] = None
    d1: Optional[list[str]] = None
    d2: Optional[list[str]] = None
    d4: Optional[list[str]] = None
    d8: Optional[list[str]] = None
    mentionsAccount: Optional[list[str]] = None
    a0: Optional[list[str]] = None
    a1: Optional[list[str]] = None
    a2: Optional[list[str]] = None
    a3: Optional[list[str]] = None
    a4: Optional[list[str]] = None
    a5: Optional[list[str]] = None
    a6: Optional[list[str]] = None
    a7: Optional[list[str]] = None
    a8: Optional[list[str]] = None
    a9: Optional[list[str]] = None
    a10: Optional[list[str]] = None
    a11: Optional[list[str]] = None
    a12: Optional[list[str]] = None
    a13: Optional[list[str]] = None
    a14: Optional[list[str]] = None
    a15: Optional[list[str]] = None
    isCommitted: Optional[bool] = None
    transaction: bool = False
    transactionBalances: bool = False
    transactionTokenBalances: bool = False
    transactionInstructions: bool = False
    innerInstructions: bool = False
    logs: bool = False

    def to_sqd_string(self):
        return _request_to_sqd_string(self)


@dataclass(frozen=True, kw_only=True)
class SolanaTransactionsRequest:
    """
    Request for filtering Solana transactions by various criteria.

    Args:
        feePayer: List of fee payer addresses
        mentionsAccount: Accounts mentioned in the transaction
        instructions: Include instructions executed by the transaction
        balances: Include SOL balance updates
        tokenBalances: Include token balance updates
        logs: Include logs produced by the transaction
    """

    feePayer: Optional[list[str]] = None
    mentionsAccount: Optional[list[str]] = None
    instructions: bool = False
    balances: bool = False
    tokenBalances: bool = False
    logs: bool = False

    def to_sqd_string(self):
        return _request_to_sqd_string(self)


@dataclass(frozen=True, kw_only=True)
class BalancesRequest:
    """
    Request for filtering SOL balance updates.

    Args:
        account: List of account addresses
        transaction: Include parent transaction
        transactionInstructions: Include instructions from parent transaction
    """

    account: Optional[list[str]] = None
    transaction: bool = False
    transactionInstructions: bool = False

    def to_sqd_string(self):
        return _request_to_sqd_string(self)


@dataclass(frozen=True, kw_only=True)
class TokenBalancesRequest:
    """
    Request for filtering token balance updates.

    Args:
        account: List of token account addresses
        preProgramId, postProgramId: Program IDs before/after
        preMint, postMint: Mint addresses before/after
        preOwner, postOwner: Owner addresses before/after
        transaction: Include parent transaction
        transactionInstructions: Include instructions from parent transaction
    """

    account: Optional[list[str]] = None
    preProgramId: Optional[list[str]] = None
    postProgramId: Optional[list[str]] = None
    preMint: Optional[list[str]] = None
    postMint: Optional[list[str]] = None
    preOwner: Optional[list[str]] = None
    postOwner: Optional[list[str]] = None
    transaction: bool = False
    transactionInstructions: bool = False

    def to_sqd_string(self):
        return _request_to_sqd_string(self)


@dataclass(frozen=True, kw_only=True)
class RewardsRequest:
    """
    Request for filtering rewards data.

    Args:
        pubkey: List of public keys that received rewards
    """

    pubkey: Optional[list[str]] = None

    def to_sqd_string(self):
        return _request_to_sqd_string(self)


@dataclass(frozen=True, kw_only=True)
class SolanaLogsRequest:
    """
    Request for filtering Solana log messages.

    Args:
        programId: List of program IDs that produced the logs
        kind: List of log kinds ('log', 'data', 'other')
        instruction: Include parent instruction
        transaction: Include parent transaction
    """

    programId: Optional[list[str]] = None
    kind: Optional[list[str]] = None
    instruction: bool = False
    transaction: bool = False

    def to_sqd_string(self):
        return _request_to_sqd_string(self)
