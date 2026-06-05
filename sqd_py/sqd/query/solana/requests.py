"""
Solana Request classes for SQD Portal Client

This module provides Solana-specific request classes for filtering blockchain data.
"""

from dataclasses import dataclass

from sqd.utils import _request_to_sqd_string


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

    programId: list[str] | None = None
    d1: list[str] | None = None
    d2: list[str] | None = None
    d4: list[str] | None = None
    d8: list[str] | None = None
    mentionsAccount: list[str] | None = None
    a0: list[str] | None = None
    a1: list[str] | None = None
    a2: list[str] | None = None
    a3: list[str] | None = None
    a4: list[str] | None = None
    a5: list[str] | None = None
    a6: list[str] | None = None
    a7: list[str] | None = None
    a8: list[str] | None = None
    a9: list[str] | None = None
    a10: list[str] | None = None
    a11: list[str] | None = None
    a12: list[str] | None = None
    a13: list[str] | None = None
    a14: list[str] | None = None
    a15: list[str] | None = None
    isCommitted: bool | None = None
    transaction: bool = False
    transactionBalances: bool = False
    transactionTokenBalances: bool = False
    transactionInstructions: bool = False
    innerInstructions: bool = False
    logs: bool = False

    def to_sqd_string(self) -> dict[str, object]:
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

    feePayer: list[str] | None = None
    mentionsAccount: list[str] | None = None
    instructions: bool = False
    balances: bool = False
    tokenBalances: bool = False
    logs: bool = False

    def to_sqd_string(self) -> dict[str, object]:
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

    account: list[str] | None = None
    transaction: bool = False
    transactionInstructions: bool = False

    def to_sqd_string(self) -> dict[str, object]:
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

    account: list[str] | None = None
    preProgramId: list[str] | None = None
    postProgramId: list[str] | None = None
    preMint: list[str] | None = None
    postMint: list[str] | None = None
    preOwner: list[str] | None = None
    postOwner: list[str] | None = None
    transaction: bool = False
    transactionInstructions: bool = False

    def to_sqd_string(self) -> dict[str, object]:
        return _request_to_sqd_string(self)


@dataclass(frozen=True, kw_only=True)
class RewardsRequest:
    """
    Request for filtering rewards data.

    Args:
        pubkey: List of public keys that received rewards
    """

    pubkey: list[str] | None = None

    def to_sqd_string(self) -> dict[str, object]:
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

    programId: list[str] | None = None
    kind: list[str] | None = None
    instruction: bool = False
    transaction: bool = False

    def to_sqd_string(self) -> dict[str, object]:
        return _request_to_sqd_string(self)
