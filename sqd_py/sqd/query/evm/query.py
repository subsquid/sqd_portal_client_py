from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, Sequence, Tuple

from sqd.query.base_query import BaseSQDQuery
from sqd.query.evm.fields import (
    TransactionField,
    LogField,
    TraceField,
    StateDiffField,
    BlockField,
)
from sqd.query.evm.requests import (
    TransactionsRequest,
    LogsRequest,
    StateDiffsRequest,
    TracesRequest,
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

    _transactions_requests: Tuple[TransactionsRequest, ...] = field(
        default_factory=tuple
    )
    _logs_requests: Tuple[LogsRequest, ...] = field(default_factory=tuple)
    _state_diffs_requests: Tuple[StateDiffsRequest, ...] = field(default_factory=tuple)
    _traces_requests: Tuple[TracesRequest, ...] = field(default_factory=tuple)

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
        to_block: Optional[int] = None,
        parent_block_hash: Optional[str] = None,
        include_fields: Optional[Sequence[BlockField]] = None,
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
        query = self._copy(
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
        address: Optional[str] = None,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None,
        sighash: Optional[str] = None,
        to_block: Optional[int] = None,
        include_logs: bool = False,
        include_traces: bool = False,
        include_state_diffs: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: Optional[str] = None,
        include_fields: Optional[Sequence[TransactionField]] = None,
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
        query = self._copy(
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
        address: Optional[str] = None,
        to_block: Optional[int] = None,
        topic0: Optional[str] = None,
        topic1: Optional[str] = None,
        topic2: Optional[str] = None,
        topic3: Optional[str] = None,
        include_transaction: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: Optional[str] = None,
        include_fields: Optional[Sequence[LogField]] = None,
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
        query = self._copy(
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

    def get_traces(
        self,
        *,
        from_block: int,
        to_block: Optional[int] = None,
        type: Optional[Literal["create", "call", "suicide", "reward"]] = None,
        call_to: Optional[str] = None,
        call_from: Optional[str] = None,
        call_sighash: Optional[str] = None,
        create_from: Optional[str] = None,
        include_transaction: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: Optional[str] = None,
        include_fields: Optional[Sequence[TraceField]] = None,
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
        query = self._copy(
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
        to_block: Optional[int] = None,
        address: Optional[str] = None,
        key: Optional[str] = None,
        kind: Optional[Literal["=", "+", "*", "-"]] = None,
        include_transaction: bool = False,
        include_all_blocks: bool = False,
        parent_block_hash: Optional[str] = None,
        include_fields: Optional[Sequence[StateDiffField]] = None,
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
        query = self._copy(
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
            "block": list(BlockField),
            "transaction": list(TransactionField),
            "log": list(LogField),
            "stateDiff": list(StateDiffField),
            "trace": list(TraceField),
        }

    # ------------------------------------------------------------------ #
    # Request builders (low-level)
    # ------------------------------------------------------------------ #
    def add_transactions_request(
        self,
        *,
        from_address: Optional[str],
        to_address: Optional[str],
        sighash: Optional[str],
        include_logs: bool,
        include_traces: bool,
        include_state_diffs: bool,
    ) -> "EVMQuery":
        request = TransactionsRequest(
            from_=[validate_evm_address(from_address)] if from_address else None,
            to=[validate_evm_address(to_address)] if to_address else None,
            sighash=[sighash] if sighash else None,
            logs=include_logs,
            traces=include_traces,
            stateDiffs=include_state_diffs,
        )
        return self._copy(
            _transactions_requests=self._transactions_requests + (request,)
        )

    def add_logs_request(
        self,
        *,
        address: Optional[str],
        topic0: Optional[str],
        topic1: Optional[str],
        topic2: Optional[str],
        topic3: Optional[str],
        include_transaction: bool = False,
    ) -> "EVMQuery":
        request = LogsRequest(
            address=[validate_evm_address(address)] if address else None,
            topic0=[topic0] if topic0 else None,
            topic1=[topic1] if topic1 else None,
            topic2=[topic2] if topic2 else None,
            topic3=[topic3] if topic3 else None,
            transaction=include_transaction,
        )
        return self._copy(_logs_requests=self._logs_requests + (request,))

    def add_traces_request(
        self,
        *,
        type: Optional[str] = None,
        call_to: Optional[str] = None,
        call_from: Optional[str] = None,
        call_sighash: Optional[str] = None,
        create_from: Optional[str] = None,
        include_transaction: bool = False,
    ) -> "EVMQuery":
        request = TracesRequest(
            type=[type] if type else None,
            callTo=[validate_evm_address(call_to)] if call_to else None,
            callFrom=[validate_evm_address(call_from)] if call_from else None,
            callSighash=[call_sighash] if call_sighash else None,
            createFrom=[validate_evm_address(create_from)] if create_from else None,
            transaction=include_transaction,
        )
        return self._copy(_traces_requests=self._traces_requests + (request,))

    def add_state_diffs_request(
        self,
        *,
        address: Optional[str] = None,
        key: Optional[str] = None,
        kind: Optional[str] = None,
        include_transaction: bool = False,
    ) -> "EVMQuery":
        request = StateDiffsRequest(
            address=[validate_evm_address(address)] if address else None,
            key=[key] if key else None,
            kind=[kind] if kind else None,
            transaction=include_transaction,
        )
        return self._copy(_state_diffs_requests=self._state_diffs_requests + (request,))

    # ------------------------------------------------------------------ #
    # Payload hooks
    # ------------------------------------------------------------------ #
    def _chain_payload(self) -> Dict[str, object]:
        payload: Dict[str, object] = {}
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
