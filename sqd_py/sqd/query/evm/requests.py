"""
EVM Request classes for SQD Portal Client

This module provides EVM-specific request classes for filtering blockchain data.
All fields and options match the SQD Portal OpenAPI specification.
"""

from dataclasses import dataclass

from sqd.utils import validate_evm_address


@dataclass(frozen=True, kw_only=True)
class TransactionsRequest:
    """
    Request for filtering transactions by various criteria.

    Args:
        from_: List of sender addresses
        to: List of recipient addresses
        sighash: List of method signature hashes (e.g., ['0xa9059cbb'] for transfer)
        logs: Include all logs emitted by matching transactions
        traces: Include all traces for matching transactions
        stateDiffs: Include all state diffs caused by matching transactions
    """

    fromBlock: list[int] | None = None
    toBlock: list[int] | None = None
    from_: list[str] | None = None
    to: list[str] | None = None
    sighash: list[str] | None = None
    logs: bool = False
    traces: bool = False
    stateDiffs: bool = False

    @classmethod
    def from_address(cls, address: str) -> "TransactionsRequest":
        """Create a request to get all transactions from a specific address."""
        return cls(from_=[validate_evm_address(address)])

    @classmethod
    def to_address(cls, address: str) -> "TransactionsRequest":
        """Create a request to get all transactions to a specific address."""
        return cls(to=[validate_evm_address(address)])


@dataclass(frozen=True, kw_only=True)
class LogsRequest:
    """
    Request for filtering event logs by various criteria.

    Args:
        address: List of contract addresses emitting the logs
        topic0: List of event signature hashes (first topic)
        topic1: List of first indexed parameter values
        topic2: List of second indexed parameter values
        topic3: List of third indexed parameter values
        transaction: Fetch parent transactions for matching logs
        transactionTraces: Fetch traces for parent transactions
        transactionLogs: Fetch all logs emitted by parent transactions
    """

    fromBlock: list[int] | None = None
    toBlock: list[int] | None = None
    address: list[str] | None = None
    topic0: list[str] | None = None
    topic1: list[str] | None = None
    topic2: list[str] | None = None
    topic3: list[str] | None = None
    transaction: bool = False
    transactionTraces: bool = False
    transactionLogs: bool = False

    @classmethod
    def transfer_event(cls, token_address: str) -> "LogsRequest":
        """Create a request for ERC-20 Transfer events."""
        return cls(
            address=[token_address],
            topic0=[
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ],
        )


@dataclass(frozen=True, kw_only=True)
class TracesRequest:
    """
    Request for filtering transaction execution traces (per OpenAPI spec).

    Args:
        type: Type of trace (create, call, suicide, reward)
        createFrom: Address initiating a create trace
        callFrom: Address initiating a call trace
        callTo: Address receiving a call trace
        callSighash: Function signature hash for call traces
        suicideRefundAddress: Refund address for suicide traces
        rewardAuthor: Author receiving a reward trace
        transaction: Fetch parent transactions for matching traces
        transactionLogs: Fetch all logs emitted by parent transactions
        subtraces: Fetch all subtraces of matching traces
        parents: Fetch parent traces of matching traces
    """

    fromBlock: list[int] | None = None
    toBlock: list[int] | None = None
    type: list[str] | None = None  # create, call, suicide, reward
    createFrom: list[str] | None = None
    callFrom: list[str] | None = None
    callTo: list[str] | None = None
    callSighash: list[str] | None = None
    suicideRefundAddress: list[str] | None = None
    rewardAuthor: list[str] | None = None
    transaction: bool = False
    transactionLogs: bool = False
    subtraces: bool = False
    parents: bool = False

    @classmethod
    def calls_to(cls, address: str) -> "TracesRequest":
        """Create a request to get call traces to a specific address."""
        return cls(type=["call"], callTo=[validate_evm_address(address)])

    @classmethod
    def creates_from(cls, address: str) -> "TracesRequest":
        """Create a request to get create traces from a specific address."""
        return cls(type=["create"], createFrom=[validate_evm_address(address)])


@dataclass(frozen=True, kw_only=True)
class StateDiffsRequest:
    """
    Request for filtering state changes (per OpenAPI spec).

    Args:
        address: List of contract/account addresses
        key: List of storage keys or special keys (balance, code, nonce)
        kind: Type of state change (=, +, *, -)
        transaction: Fetch parent transactions for matching state diffs
    """

    fromBlock: list[int] | None = None
    toBlock: list[int] | None = None
    address: list[str] | None = None
    key: list[str] | None = None
    kind: list[str] | None = None  # '=', '+', '*', '-'
    transaction: bool = False

    @classmethod
    def for_contract(cls, address: str) -> "StateDiffsRequest":
        """Create a request to get state changes for a specific contract."""
        return cls(address=[validate_evm_address(address)])

    @classmethod
    def balance_changes(cls, address: str) -> "StateDiffsRequest":
        """Create a request to get balance changes for a specific address."""
        return cls(address=[validate_evm_address(address)], key=["balance"])


__all__ = [
    "TransactionsRequest",
    "LogsRequest",
    "TracesRequest",
    "StateDiffsRequest",
]
