"""
SQD Portal Client Query Builder

This module provides a user-friendly interface for building queries to the SQD (Subsquid) Network portal.

Basic Usage:
    from sqd_portal_client_evm import get_data, Dataset
    from sqd_portal_client_evm.query import Query, Fields

    # Simple transaction query
    query = Query(
        fromBlock=1000000,
        toBlock=1000100,
        transactionsRequests=[
            Query.TransactionsRequest(from_=['0x123...'], to=['0x456...'])
        ],
        fields=Query.Fields.all_fields()
    )

    data = get_data(dataset=Dataset.ETHEREUM, query=query)

    # Using convenience functions
    query = Query.transactions(from_address='0x123...', to_block=1000100)
    data = get_data(dataset=Dataset.ETHEREUM, query=query)
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Literal

try:
    import ujson as json_lib
except ImportError:
    import json as json_lib


def _request_to_sqd_string(r) -> str:
    def correctFromUnderscore(k: str) -> str:
        return 'from' if k == 'from_' else k

    return json_lib.dumps({correctFromUnderscore(k): v for k, v in asdict(r).items() if v is not None},
                          separators=(',', ':'))


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

    if not address.startswith('0x'):
        address = '0x' + address

    if len(address) != 42:
        raise ValueError(f"Invalid address length: {len(address)}. Expected 42 characters (including 0x prefix)")

    # Basic hex validation
    try:
        int(address, 16)
    except ValueError:
        raise ValueError(f"Invalid address format: {address}")

    return address


@dataclass(frozen=True, kw_only=True)
class Query:
    """
    Main query class for building SQD Network portal queries.

    This class allows you to query EVM blockchain data including transactions, logs, traces, and state changes.

    Basic usage:
        # Simple query for recent transactions
        query = Query(
            fromBlock=17000000,
            toBlock=17000100,
            transactionsRequests=[Query.TransactionsRequest.from_address('0x123...')],
            fields=Query.Fields.minimal_fields()
        )

        # Query specific contract events
        query = Query.logs_from_contract('0x742d35Cc6634C0532925a3b8', from_block=17000000)

    Args:
        fromBlock: Starting block number (default: 0)
        toBlock: Ending block number (optional, if None then no upper limit)
        transactionsRequests: List of transaction filters
        logsRequests: List of log filters
        stateDiffsRequests: List of state change filters
        tracesRequests: List of trace filters
        fields: Which fields to include in results
    """

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
            request = Query.TransactionsRequest(from_=['0x742d35Cc6634C0532925a3b8'])

            # Get transfers to a specific address
            request = Query.TransactionsRequest(to=['0x742d35Cc6634C0532925a3b8'])

            # Get ERC-20 transfers (transfer method signature)
            request = Query.TransactionsRequest(sighash=['0xa9059cbb'], logs=True)
        """
        from_: Optional[list[str]] = None
        to: Optional[list[str]] = None
        sighash: Optional[list[str]] = None
        logs: bool = False
        traces: bool = False
        stateDiffs: bool = False

        def to_sqd_string(self):
            return _request_to_sqd_string(self)

        @classmethod
        def from_address(cls, address: str) -> 'Query.TransactionsRequest':
            """Create a request to get all transactions from a specific address."""
            return cls(from_=[_validate_address(address)])

        @classmethod
        def to_address(cls, address: str) -> 'Query.TransactionsRequest':
            """Create a request to get all transactions to a specific address."""
            return cls(to=[_validate_address(address)])

        @classmethod
        def transfer(cls, token_address: str, include_logs: bool = True) -> 'Query.TransactionsRequest':
            """Create a request for ERC-20 transfer transactions."""
            return cls(sighash=['0xa9059cbb'], logs=include_logs)

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
            request = Query.LogsRequest(address=['0x742d35Cc6634C0532925a3b8'])

            # Get Transfer events from an ERC-20 contract
            request = Query.LogsRequest(
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
        def from_contract(cls, address: str) -> 'Query.LogsRequest':
            """Create a request to get all logs from a specific contract."""
            return cls(address=[address])

        @classmethod
        def transfer_event(cls, token_address: str, include_transaction: bool = True) -> 'Query.LogsRequest':
            """Create a request for ERC-20 Transfer events."""
            return cls(
                address=[token_address],
                topic0=['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'],
                transaction=include_transaction
            )

    @dataclass(frozen=True, kw_only=True)
    class StateDiffsRequest:
        """
        Request for filtering state changes (storage modifications).

        Args:
            address: List of contract addresses whose storage was modified

        Example:
            # Get state changes for a specific contract
            request = Query.StateDiffsRequest(address=['0x742d35Cc6634C0532925a3b8'])
        """
        address: Optional[list[str]] = None

        @classmethod
        def for_contract(cls, address: str) -> 'Query.StateDiffsRequest':
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
            request = Query.TracesRequest(address=['0x742d35Cc6634C0532925a3b8'])
        """
        address: Optional[list[str]] = None

        @classmethod
        def for_contract(cls, address: str) -> 'Query.TracesRequest':
            """Create a request to get traces for a specific contract."""
            return cls(address=[address])

    @dataclass(frozen=True, kw_only=True)
    class Fields:
        """
        Defines which fields to include in query results for different data types.

        Example:
            # Get block number, hash, and timestamp
            fields = Fields(
                block={cls.Block.number, cls.Block.hash, cls.Block.timestamp},
                transaction={cls.Transaction.hash}
            )

            # Get all available fields
            fields = cls.all_fields()
        """

        class Block(Enum):
            """Available block fields (must match SQD API field names exactly)"""
            hash = 'hash'
            number = 'number'  # Note: SQD API uses 'number' not 'height'
            parentHash = 'parentHash'
            timestamp = 'timestamp'
            transactionsRoot = 'transactionsRoot'
            receiptsRoot = 'receiptsRoot'
            stateRoot = 'stateRoot'
            logsBloom = 'logsBloom'
            miner = 'miner'
            size = 'size'
            gasLimit = 'gasLimit'
            gasUsed = 'gasUsed'

        class Transaction(Enum):
            """Available transaction fields"""
            hash = 'hash'
            transactionIndex = 'transactionIndex'
            nonce = 'nonce'
            from_ = 'from'
            to = 'to'
            input = 'input'
            value = 'value'
            gas = 'gas'
            gasPrice = 'gasPrice'
            maxFeePerGas = 'maxFeePerGas'
            maxPriorityFeePerGas = 'maxPriorityFeePerGas'
            v = 'v'
            r = 'r'
            s = 's'
            yParity = 'yParity'
            chainId = 'chainId'
            sighash = 'sighash'
            contractAddress = 'contractAddress'
            gasUsed = 'gasUsed'
            cumulativeGasUsed = 'cumulativeGasUsed'
            effectiveGasPrice = 'effectiveGasPrice'
            type = 'type'
            status = 'status'
            maxFeePerBlobGas = 'maxFeePerBlobGas'
            blobVersionedHashes = 'blobVersionedHashes'
            l1Fee = 'l1Fee'
            l1FeeScalar = 'l1FeeScalar'
            l1GasPrice = 'l1GasPrice'
            l1GasUsed = 'l1GasUsed'
            l1BlobBaseFee = 'l1BlobBaseFee'
            l1BlobBaseFeeScalar = 'l1BlobBaseFeeScalar'
            l1BaseFeeScalar = 'l1BaseFeeScalar'

        class Log(Enum):
            """Available log fields"""
            logIndex = 'logIndex'
            transactionIndex = 'transactionIndex'
            transactionHash = 'transactionHash'
            address = 'address'
            data = 'data'
            topics = 'topics'

        class StateDiff(Enum):
            """Available state diff fields"""
            transactionIndex = 'transactionIndex'

        class Trace(Enum):
            """Available trace fields"""
            transactionIndex = 'transactionIndex'
            traceAddress = 'traceAddress'

        block: set[Block] = field(default_factory=set)
        transaction: set[Transaction] = field(default_factory=set)
        log: set[Log] = field(default_factory=set)
        stateDiff: set[StateDiff] = field(default_factory=set)
        trace: set[Trace] = field(default_factory=set)

        @classmethod
        def all_fields(cls):
            """Get all available fields for all data types."""
            return cls(
                block=set(cls.Block),
                transaction=set(cls.Transaction),
                log=set(cls.Log),
                stateDiff=set(cls.StateDiff),
                trace=set(cls.Trace)
            )

        @classmethod
        def minimal_fields(cls):
            """Get minimal fields (just IDs and indexes)."""
            return cls(
                block={cls.Block.number},
                transaction={cls.Transaction.hash, cls.Transaction.transactionIndex},
                log={cls.Log.logIndex, cls.Log.transactionIndex},
                stateDiff={cls.StateDiff.transactionIndex},
                trace={cls.Trace.transactionIndex, cls.Trace.traceAddress}
            )

        @classmethod
        def block_only(cls):
            """Get only block fields."""
            return cls(block=set(cls.Block))

        @classmethod
        def transactions_only(cls):
            """Get only transaction fields."""
            return cls(transaction=set(cls.Transaction))

        def to_sqd_string(self):
            return json_lib.dumps({k: {f.value: True for f in v} for k, v in asdict(self).items() if len(v) > 0},
                                  separators=(',', ':'))

    fromBlock: int = 0
    toBlock: Optional[int] = None
    transactionsRequests: list[TransactionsRequest] = field(default_factory=list)
    logsRequests: list[LogsRequest] = field(default_factory=list)
    stateDiffsRequests: list[StateDiffsRequest] = field(default_factory=list)
    tracesRequests: list[TracesRequest] = field(default_factory=list)
    fields: 'Query.Fields'
    type: Literal['evm', 'solana'] = 'evm'

    def __post_init__(self):
        """Validate query parameters after initialization."""
        if self.fromBlock < 0:
            raise ValueError(f"fromBlock must be non-negative, got {self.fromBlock}")

        if self.toBlock is not None and self.toBlock < self.fromBlock:
            raise ValueError(f"toBlock ({self.toBlock}) must be greater than or equal to fromBlock ({self.fromBlock})")

        if not self.transactionsRequests and not self.logsRequests and not self.stateDiffsRequests and not self.tracesRequests:
            # This might be intentional for simple block range queries, so just warn
            import warnings
            warnings.warn(
                "Query has no request filters specified. This will return all data in the block range, "
                "which may be very large. Consider adding specific request filters.",
                UserWarning,
                stacklevel=2
            )

    @classmethod
    def transactions(
            cls,
            from_address: Optional[str] = None,
            to_address: Optional[str] = None,
            sighash: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_logs: bool = False,
            include_traces: bool = False,
            include_state_diffs: bool = False,
            fields: Optional['Query.Fields'] = None
    ) -> 'Query':
        """
        Create a query for transactions.

        Args:
            from_address: Filter transactions from this address
            to_address: Filter transactions to this address
            sighash: Filter by method signature (e.g., '0xa9059cbb' for transfers)
            from_block: Starting block number
            to_block: Ending block number (optional)
            include_logs: Include transaction logs
            include_traces: Include transaction traces
            include_state_diffs: Include state changes
            fields: Fields to include (default: minimal fields)

        Example:
            # Get all transactions from an address
            query = Query.transactions(from_address='0x123...', from_block=17000000)

            # Get ERC-20 transfers
            query = Query.transactions(sighash='0xa9059cbb', include_logs=True)
        """
        request = cls.TransactionsRequest(
            from_=[_validate_address(from_address)] if from_address else None,
            to=[_validate_address(to_address)] if to_address else None,
            sighash=[sighash] if sighash else None,
            logs=include_logs,
            traces=include_traces,
            stateDiffs=include_state_diffs
        )

        return cls(
            fromBlock=from_block,
            toBlock=to_block,
            transactionsRequests=[request],
            fields=fields or cls.Fields.minimal_fields()
        )

    @classmethod
    def logs_from_contract(
            cls,
            contract_address: str,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_transaction: bool = True,
            fields: Optional['Query.Fields'] = None
    ) -> 'Query':
        """
        Create a query for logs from a specific contract.

        Args:
            contract_address: Contract address to get logs from
            from_block: Starting block number
            to_block: Ending block number (optional)
            include_transaction: Include the triggering transaction
            fields: Fields to include (default: minimal fields)

        Example:
            # Get all logs from Uniswap V3 pool
            query = Query.logs_from_contract('0x123...', from_block=17000000)
        """
        request = cls.LogsRequest(address=[_validate_address(contract_address)], transaction=include_transaction)

        return cls(
            fromBlock=from_block,
            toBlock=to_block,
            logsRequests=[request],
            fields=fields or cls.Fields.minimal_fields()
        )

    @classmethod
    def erc20_transfers(
            cls,
            token_address: str,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_transaction: bool = True,
            fields: Optional['Query.Fields'] = None
    ) -> 'Query':
        """
        Create a query for ERC-20 token transfers.

        Args:
            token_address: ERC-20 token contract address
            from_block: Starting block number
            to_block: Ending block number (optional)
            include_transaction: Include the transfer transaction
            fields: Fields to include (default: minimal fields)

        Example:
            # Get USDC transfers from the last week
            query = Query.erc20_transfers('0xa0b86a33e6c6...', from_block=17000000)
        """
        request = cls.LogsRequest(
            address=[_validate_address(token_address)],
            topic0=['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'],
            transaction=include_transaction
        )

        return cls(
            fromBlock=from_block,
            toBlock=to_block,
            logsRequests=[request],
            fields=fields or cls.Fields.minimal_fields()
        )

    @classmethod
    def simple_block_range(
            cls,
            from_block: int,
            to_block: Optional[int] = None,
            fields: Optional['Query.Fields'] = None
    ) -> 'Query':
        """
        Create a simple query for all data in a block range.

        Args:
            from_block: Starting block number
            to_block: Ending block number (optional)
            fields: Fields to include (default: minimal fields)

        Example:
            # Get all data from blocks 17000000-17000100
            query = Query.simple_block_range(17000000, 17000100)
        """
        return cls(
            fromBlock=from_block,
            toBlock=to_block,
            fields=fields or cls.Fields.minimal_fields()
        )

    def to_sqd_string(self):
        requestsStrings = {
            'transactions': '[' + ','.join([r.to_sqd_string() for r in self.transactionsRequests]) + ']',
            'logs': '[' + ','.join([_request_to_sqd_string(r) for r in self.logsRequests]) + ']',
            'stateDiffs': '[' + ','.join([_request_to_sqd_string(r) for r in self.stateDiffsRequests]) + ']',
            'traces': '[' + ','.join([_request_to_sqd_string(r) for r in self.tracesRequests]) + ']'
        }
        requestsString = ','.join([f'"{k}":{v}' for k, v in requestsStrings.items() if v != '[]'])

        toBlockString = '' if self.toBlock is None else f'"toBlock":{self.toBlock}'

        # Build the middle part with proper comma handling
        middleParts = []
        if toBlockString:
            middleParts.append(toBlockString)
        if requestsString:
            middleParts.append(requestsString)

        middleString = ','.join(middleParts)

        return f'{{"type":"evm","fromBlock":{self.fromBlock},{middleString},"fields":{self.fields.to_sqd_string()}}}'
