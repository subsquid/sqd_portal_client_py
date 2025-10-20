"""
EVM Request classes for SQD Portal Client

This module provides EVM-specific request classes for filtering blockchain data.
"""

from dataclasses import dataclass, asdict
from typing import Optional

try:
    import ujson as json_lib
except ImportError:
    import json as json_lib


def _validate_address(address: str) -> str:
    """
    Validate and normalize Ethereum address format.

    Args:
        address: Ethereum address string

    Returns:
        Normalized address (lowercase, 0x prefix)

    Raises:
        ValueError: If address format is invalid
    """
    if not address:
        raise ValueError("Address cannot be empty")

    address = address.lower()

    if not address.startswith("0x"):
        address = "0x" + address

    if len(address) != 42:
        raise ValueError(
            f"Invalid address length: {len(address)}. Expected 42 characters (including 0x prefix)"
        )

    # Basic hex validation
    try:
        int(address, 16)
    except ValueError:
        raise ValueError(f"Invalid address format: {address}")

    return address


def _request_to_sqd_string(r) -> dict:
    """Convert request object to SQD API dict format"""

    def correctFromUnderscore(k: str) -> str:
        return "from" if k == "from_" else k

    return {correctFromUnderscore(k): v for k, v in asdict(r).items() if v is not None}


@dataclass(frozen=True, kw_only=True)
class TransactionsRequest:
    """
    Request for filtering transactions by various criteria.

    Args:
        from_: List of sender addresses (e.g., ['0x123...', '0x456...'])
        to: List of recipient addresses (e.g., ['0x789...', '0xabc...'])
        sighash: List of method signatures (e.g., ['0xa9059cbb']) for specific function calls
        logs: Include transaction logs in results
        traces: Include transaction traces in results
        stateDiffs: Include state changes in results

    Example:
        # Get all transactions from a specific address
        request = TransactionsRequest(from_=['0x742d35Cc6634C0532925a3b8'])

        # Get transfers to a specific address
        request = TransactionsRequest(to=['0x742d35Cc6634C0532925a3b8'])

        # Get ERC-20 transfers (transfer method signature)
        request = TransactionsRequest(sighash=['0xa9059cbb'], logs=True)
    """

    from_: Optional[list[str]] = None
    to: Optional[list[str]] = None
    sighash: Optional[list[str]] = None
    logs: bool = False
    traces: bool = False
    stateDiffs: bool = False

    @classmethod
    def from_address(cls, address: str) -> "TransactionsRequest":
        """Create a request to get all transactions from a specific address."""
        return cls(from_=[_validate_address(address)])

    @classmethod
    def to_address(cls, address: str) -> "TransactionsRequest":
        """Create a request to get all transactions to a specific address."""
        return cls(to=[_validate_address(address)])

    @classmethod
    def transfer(
            cls, token_address: str, include_logs: bool = True
    ) -> "TransactionsRequest":
        """Create a request for ERC-20 transfer transactions."""
        return cls(sighash=["0xa9059cbb"], logs=include_logs)


@dataclass(frozen=True, kw_only=True)
class LogsRequest:
    """
    Request for filtering event logs by various criteria.

    Args:
        address: List of contract addresses that emitted the logs
        topic0: List of event signature hashes (first topic)
        topic1: List of first indexed parameter values (second topic)
        topic2: List of second indexed parameter values (third topic)
        topic3: List of third indexed parameter values (fourth topic)
        transaction: Include the transaction that triggered the log
        transactionTraces: Include traces related to the transaction
        transactionLogs: Include other logs from the same transaction

    Example:
        # Get all logs from a specific contract
        request = LogsRequest(address=['0x742d35Cc6634C0532925a3b8'])

        # Get Transfer events from an ERC-20 contract
        request = LogsRequest(
            address=['0x742d35Cc6634C0532925a3b8'],
            topic0=['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef']
        )
    """

    address: Optional[list[str]] = None
    topic0: Optional[list[str]] = None
    topic1: Optional[list[str]] = None
    topic2: Optional[list[str]] = None
    topic3: Optional[list[str]] = None
    transaction: bool = False
    transactionTraces: bool = False
    transactionLogs: bool = False

    @classmethod
    def from_contract(cls, address: str) -> "LogsRequest":
        """Create a request to get all logs from a specific contract."""
        return cls(address=[address])

    @classmethod
    def transfer_event(
            cls, token_address: str, include_transaction: bool = True
    ) -> "LogsRequest":
        """Create a request for ERC-20 Transfer events."""
        return cls(
            address=[token_address],
            topic0=[
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ],
            transaction=include_transaction,
        )


@dataclass(frozen=True, kw_only=True)
class StateDiffsRequest:
    """
    Request for filtering state changes (storage modifications).

    Args:
        address: List of contract addresses whose storage was modified

    Example:
        # Get state changes for a specific contract
        request = StateDiffsRequest(address=['0x742d35Cc6634C0532925a3b8'])
    """

    address: Optional[list[str]] = None

    @classmethod
    def for_contract(cls, address: str) -> "StateDiffsRequest":
        """Create a request to get state changes for a specific contract."""
        return cls(address=[address])


@dataclass(frozen=True, kw_only=True)
class TracesRequest:
    """
    Request for filtering transaction execution traces.

    Args:
        address: List of contract addresses that were called during execution

    Example:
        # Get traces involving a specific contract
        request = TracesRequest(address=['0x742d35Cc6634C0532925a3b8'])
    """

    address: Optional[list[str]] = None

    @classmethod
    def for_contract(cls, address: str) -> "TracesRequest":
        """Create a request to get traces for a specific contract."""
        return cls(address=[address])
