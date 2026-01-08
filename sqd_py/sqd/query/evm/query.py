from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from sqd.query.base_query import BaseSQDQuery
from sqd.query.evm.fields import (
    BlockField,
    LogField,
    StateDiffField,
    TraceField,
    TransactionField,
)
from sqd.query.evm.requests import (
    LogsRequest,
    StateDiffsRequest,
    TracesRequest,
    TransactionsRequest,
)
from sqd.utils import _request_to_sqd_string, validate_evm_address

# ============================================================================ #
# EVMQuery
# ============================================================================ #


@dataclass(frozen=True, kw_only=True)
class EVMQuery(BaseSQDQuery):
    """Immutable EVM query representation.

    Example:
        sqd = SQD(dataset='ethereum-mainnet')
        query = sqd.get_transactions(from_block=17_000_000, address='0x...')
        async for block in query:
            print(block)
    """

    _transactions_requests: tuple[TransactionsRequest, ...] = field(
        default_factory=tuple
    )
    _logs_requests: tuple[LogsRequest, ...] = field(default_factory=tuple)
    _state_diffs_requests: tuple[StateDiffsRequest, ...] = field(default_factory=tuple)
    _traces_requests: tuple[TracesRequest, ...] = field(default_factory=tuple)

    # ------------------------------------------------------------------ #
    # Factory methods
    # ------------------------------------------------------------------ #
    @classmethod
    def create(
        cls,
        *,
        dataset: str,
        portal_url: str = "https://portal.sqd.dev",
        stream_type: Literal["finalized", "realtime"] = "realtime",
    ) -> "EVMQuery":
        """Create a new EVM query builder."""
        return cls(
            dataset=dataset,
            portal_url=portal_url,
            stream_type=stream_type,
            query_type="evm",
        )

    def get_blocks(
        self,
        *,
        from_block: int,
        to_block: int | None = None,
        parent_block_hash: str | None = None,
        include_fields: Sequence[BlockField] | None = None,
    ) -> "EVMQuery":
        """Query block headers.

        Args:
            from_block: Starting block number (required)
            to_block: Ending block number
            parent_block_hash: Expected hash of parent of first block (for chain continuity)
            include_fields: Specific block fields to include

        Returns:
            EVMQuery configured to fetch blocks
        """
        query = self.copy(
            from_block=from_block,
            to_block=to_block,
            include_all_blocks=True,  # Always include blocks for this query type
            parent_block_hash=parent_block_hash,
        )
        return query.add_fields("block", include_fields)

    def get_transactions(
        self,
        *,
        from_block: int,
        address: str | None = None,
        from_address: str | None = None,
        to_address: str | None = None,
        sighash: str | None = None,
        to_block: int | None = None,
        include_logs: bool = False,
        include_traces: bool = False,
        include_state_diffs: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: str | None = None,
        include_fields: Sequence[TransactionField] | None = None,
    ) -> "EVMQuery":
        """Query transactions matching the specified criteria.

        Args:
            from_block: Starting block number (required)
            address: Address to filter by (sender)
            from_address: Sender address (overrides address)
            to_address: Recipient address
            sighash: Method signature hash (e.g., '0xa9059cbb' for transfer)
            to_block: Ending block number
            include_logs: Include logs emitted by matching transactions
            include_traces: Include traces for matching transactions
            include_state_diffs: Include state diffs caused by matching transactions
            include_all_blocks: Include blocks with no matching data
            parent_block_hash: Expected hash of parent of first block (for chain continuity)
            include_fields: Specific transaction fields to include
        """
        query = self.copy(
            from_block=from_block,
            to_block=to_block,
            include_all_blocks=include_all_blocks,
            parent_block_hash=parent_block_hash,
        )
        query = query.add_transactions_request(
            from_address=from_address or address,
            to_address=to_address,
            sighash=sighash,
            include_logs=include_logs,
            include_traces=include_traces,
            include_state_diffs=include_state_diffs,
        )
        return query.add_fields("transaction", include_fields)

    def get_logs(
        self,
        *,
        from_block: int,
        address: str | None = None,
        to_block: int | None = None,
        topic0: str | None = None,
        topic1: str | None = None,
        topic2: str | None = None,
        topic3: str | None = None,
        include_transaction: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: str | None = None,
        include_fields: Sequence[LogField] | None = None,
    ) -> "EVMQuery":
        """Query event logs matching the specified criteria.

        Args:
            from_block: Starting block number (required)
            address: Contract address to filter by
            to_block: Ending block number
            topic0: Event signature hash (first topic)
            topic1: First indexed parameter
            topic2: Second indexed parameter
            topic3: Third indexed parameter
            include_transaction: Fetch parent transactions for matching logs
            include_all_blocks: Include blocks with no matching data
            parent_block_hash: Expected hash of parent of first block
            include_fields: Specific log fields to include
        """
        query = self.copy(
            from_block=from_block,
            to_block=to_block,
            include_all_blocks=include_all_blocks,
            parent_block_hash=parent_block_hash,
        )
        query = query.add_logs_request(
            address=address,
            topic0=topic0,
            topic1=topic1,
            topic2=topic2,
            topic3=topic3,
            include_transaction=include_transaction,
        )
        return query.add_fields("log", include_fields)

    # ERC-20 Transfer event signature: Transfer(address,address,uint256)
    TRANSFER_TOPIC = (
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    )

    def get_transfers(
        self,
        *,
        from_block: int,
        contract_address: str | None = None,
        from_address: str | None = None,
        to_address: str | None = None,
        to_block: int | None = None,
        include_transaction: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: str | None = None,
        include_fields: Sequence[LogField] | None = None,
    ) -> "EVMQuery":
        """Query ERC-20/ERC-721 Transfer events.

        This is a convenience method that queries Transfer(address,address,uint256) events.

        Args:
            from_block: Starting block number (required)
            contract_address: Token contract address to filter by
            from_address: Filter by sender address (topic1)
            to_address: Filter by recipient address (topic2)
            to_block: Ending block number
            include_transaction: Fetch parent transactions for matching logs
            include_all_blocks: Include blocks with no matching data
            parent_block_hash: Expected hash of parent of first block
            include_fields: Specific log fields to include

        Example:
            # Get all USDC transfers
            query = sqd.get_transfers(
                from_block=17_000_000,
                contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            )

            # Get transfers TO a specific address
            query = sqd.get_transfers(
                from_block=17_000_000,
                to_address="0x742d35cc6634c0532925a3b844bc9e7595f5ab12",
            )
        """
        # Pad addresses to 32 bytes (64 hex chars) for topic matching
        topic1 = None
        topic2 = None
        if from_address:
            addr = validate_evm_address(from_address)
            topic1 = "0x" + addr[2:].zfill(64).lower()
        if to_address:
            addr = validate_evm_address(to_address)
            topic2 = "0x" + addr[2:].zfill(64).lower()

        return self.get_logs(
            from_block=from_block,
            to_block=to_block,
            address=contract_address,
            topic0=self.TRANSFER_TOPIC,
            topic1=topic1,
            topic2=topic2,
            include_transaction=include_transaction,
            include_all_blocks=include_all_blocks,
            parent_block_hash=parent_block_hash,
            include_fields=include_fields,
        )

    def get_traces(
        self,
        *,
        from_block: int,
        to_block: int | None = None,
        type: Literal["create", "call", "suicide", "reward"] | None = None,
        call_to: str | None = None,
        call_from: str | None = None,
        call_sighash: str | None = None,
        create_from: str | None = None,
        include_transaction: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: str | None = None,
        include_fields: Sequence[TraceField] | None = None,
    ) -> "EVMQuery":
        """Query traces matching the specified criteria.

        Args:
            from_block: Starting block number (required)
            to_block: Ending block number
            type: Type of trace (create, call, suicide, reward)
            call_to: Address receiving a call trace
            call_from: Address initiating a call trace
            call_sighash: Function signature hash for call traces
            create_from: Address initiating a create trace
            include_transaction: Fetch parent transactions
            include_all_blocks: Include blocks with no matching data
            parent_block_hash: Expected hash of parent of first block
            include_fields: Specific trace fields to include
        """
        query = self.copy(
            from_block=from_block,
            to_block=to_block,
            include_all_blocks=include_all_blocks,
            parent_block_hash=parent_block_hash,
        )
        query = query.add_traces_request(
            type=type,
            call_to=call_to,
            call_from=call_from,
            call_sighash=call_sighash,
            create_from=create_from,
            include_transaction=include_transaction,
        )
        return query.add_fields("trace", include_fields)

    def get_state_diffs(
        self,
        *,
        from_block: int,
        to_block: int | None = None,
        address: str | None = None,
        key: str | None = None,
        kind: Literal["=", "+", "*", "-"] | None = None,
        include_transaction: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: str | None = None,
        include_fields: Sequence[StateDiffField] | None = None,
    ) -> "EVMQuery":
        """Query state diffs matching the specified criteria.

        Args:
            from_block: Starting block number (required)
            to_block: Ending block number
            address: Contract or account address
            key: Storage key or special key (balance, code, nonce)
            kind: Type of state change (=, +, *, -)
            include_transaction: Fetch parent transactions
            include_all_blocks: Include blocks with no matching data
            parent_block_hash: Expected hash of parent of first block
            include_fields: Specific state diff fields to include
        """
        query = self.copy(
            from_block=from_block,
            to_block=to_block,
            include_all_blocks=include_all_blocks,
            parent_block_hash=parent_block_hash,
        )
        query = query.add_state_diffs_request(
            address=address,
            key=key,
            kind=kind,
            include_transaction=include_transaction,
        )
        return query.add_fields("stateDiff", include_fields)

    @staticmethod
    def _default_field_map() -> dict[str, list[str]]:
        return {
            "block": [BlockField.number, BlockField.timestamp],
        }

    # ------------------------------------------------------------------ #
    # Request builders (low-level)
    # ------------------------------------------------------------------ #
    def add_transactions_request(
        self,
        *,
        from_block: int | None = None,
        to_block: int | None = None,
        from_address: str | None = None,
        to_address: str | None = None,
        sighash: str | None = None,
        include_logs: bool = False,
        include_traces: bool = False,
        include_state_diffs: bool = False,
    ) -> "EVMQuery":
        request = TransactionsRequest(
            fromBlock=[from_block] if from_block else None,
            toBlock=[to_block] if to_block else None,
            from_=[validate_evm_address(from_address)] if from_address else None,
            to=[validate_evm_address(to_address)] if to_address else None,
            sighash=[sighash] if sighash else None,
            logs=include_logs,
            traces=include_traces,
            stateDiffs=include_state_diffs,
        )
        return self.copy(
            _transactions_requests=self._transactions_requests + (request,)
        )

    def add_logs_request(
        self,
        *,
        from_block: int | None = None,
        to_block: int | None = None,
        address: str | None = None,
        topic0: str | None = None,
        topic1: str | None = None,
        topic2: str | None = None,
        topic3: str | None = None,
        include_transaction: bool = False,
    ) -> "EVMQuery":
        request = LogsRequest(
            fromBlock=[from_block] if from_block else None,
            toBlock=[to_block] if to_block else None,
            address=[validate_evm_address(address)] if address else None,
            topic0=[topic0] if topic0 else None,
            topic1=[topic1] if topic1 else None,
            topic2=[topic2] if topic2 else None,
            topic3=[topic3] if topic3 else None,
            transaction=include_transaction,
        )
        return self.copy(_logs_requests=self._logs_requests + (request,))

    def add_traces_request(
        self,
        *,
        from_block: int | None = None,
        to_block: int | None = None,
        type: str | None = None,
        call_to: str | None = None,
        call_from: str | None = None,
        call_sighash: str | None = None,
        create_from: str | None = None,
        include_transaction: bool = False,
    ) -> "EVMQuery":
        request = TracesRequest(
            fromBlock=[from_block] if from_block else None,
            toBlock=[to_block] if to_block else None,
            type=[type] if type else None,
            callTo=[validate_evm_address(call_to)] if call_to else None,
            callFrom=[validate_evm_address(call_from)] if call_from else None,
            callSighash=[call_sighash] if call_sighash else None,
            createFrom=[validate_evm_address(create_from)] if create_from else None,
            transaction=include_transaction,
        )
        return self.copy(_traces_requests=self._traces_requests + (request,))

    def add_state_diffs_request(
        self,
        *,
        from_block: int | None = None,
        to_block: int | None = None,
        address: str | None = None,
        key: str | None = None,
        kind: str | None = None,
        include_transaction: bool = False,
    ) -> "EVMQuery":
        request = StateDiffsRequest(
            fromBlock=[from_block] if from_block else None,
            toBlock=[to_block] if to_block else None,
            address=[validate_evm_address(address)] if address else None,
            key=[key] if key else None,
            kind=[kind] if kind else None,
            transaction=include_transaction,
        )
        return self.copy(_state_diffs_requests=self._state_diffs_requests + (request,))

    # ------------------------------------------------------------------ #
    # Payload hooks
    # ------------------------------------------------------------------ #
    def _chain_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self._transactions_requests:
            payload["transactions"] = [
                _request_to_sqd_string(request)
                for request in self._transactions_requests
            ]

        if self._logs_requests:
            payload["logs"] = [
                _request_to_sqd_string(request) for request in self._logs_requests
            ]

        if self._state_diffs_requests:
            payload["stateDiffs"] = [
                _request_to_sqd_string(request)
                for request in self._state_diffs_requests
            ]

        if self._traces_requests:
            payload["traces"] = [
                _request_to_sqd_string(request) for request in self._traces_requests
            ]

        return payload


__all__ = [
    "EVMQuery",
    "BlockField",
    "TransactionField",
    "LogField",
    "TraceField",
    "StateDiffField",
]
