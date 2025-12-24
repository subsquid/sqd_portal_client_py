from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, Tuple

from ..base.base import _Fields
from .base_query import BaseSQDQuery, _FieldEnum, _freeze_field_map
from .evm.fields import EVMFields
from .evm.requests import (
    LogsRequest,
    StateDiffsRequest,
    TracesRequest,
    TransactionsRequest,
    _request_to_sqd_string,
    _validate_address,
)


class TransactionField(_FieldEnum):
    TRANSACTION_HASH = ("transaction", EVMFields.Transaction.hash.value)
    TRANSACTION_INDEX = ("transaction", EVMFields.Transaction.transactionIndex.value)
    BLOCK_NUMBER = ("block", EVMFields.Block.number.value)
    FROM_ADDRESS = ("transaction", EVMFields.Transaction.from_.value)
    TO_ADDRESS = ("transaction", EVMFields.Transaction.to.value)
    GAS_USED = ("transaction", EVMFields.Transaction.gasUsed.value)


class LogField(_FieldEnum):
    LOG_INDEX = ("log", EVMFields.Log.logIndex.value)
    TRANSACTION_HASH = ("log", EVMFields.Log.transactionHash.value)
    TRANSACTION_INDEX = ("log", EVMFields.Log.transactionIndex.value)
    ADDRESS = ("log", EVMFields.Log.address.value)
    TOPICS = ("log", EVMFields.Log.topics.value)
    BLOCK_NUMBER = ("block", EVMFields.Block.number.value)


@dataclass(frozen=True, kw_only=True)
class EVMQuery(BaseSQDQuery):
    """Immutable EVM query representation."""

    _transactions_requests: Tuple[TransactionsRequest, ...] = field(
        default_factory=tuple
    )
    _logs_requests: Tuple[LogsRequest, ...] = field(default_factory=tuple)
    _state_diffs_requests: Tuple[StateDiffsRequest, ...] = field(
        default_factory=tuple
    )
    _traces_requests: Tuple[TracesRequest, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls, *, client, from_block: int, to_block: Optional[int]
    ) -> "EVMQuery":
        return cls(
            client=client,
            from_block=from_block,
            to_block=to_block,
            query_type="evm",
            _fields=_freeze_field_map(cls._default_field_map()),
        )

    @staticmethod
    def _default_field_map() -> Dict[str, Sequence[_FieldEnum]]:
        all_fields = _Fields.all_fields()
        return {
            "block": all_fields.block,
            "transaction": all_fields.transaction,
            "log": all_fields.log,
            "stateDiff": all_fields.stateDiff,
            "trace": all_fields.trace,
        }

    # ------------------------------------------------------------------ #
    # Request builders
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
            from_=[_validate_address(from_address)] if from_address else None,
            to=[_validate_address(to_address)] if to_address else None,
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
    ) -> "EVMQuery":
        request = LogsRequest(
            address=[_validate_address(address)] if address else None,
            topic0=[topic0] if topic0 else None,
            topic1=[topic1] if topic1 else None,
            topic2=[topic2] if topic2 else None,
            topic3=[topic3] if topic3 else None,
        )
        return self._copy(_logs_requests=self._logs_requests + (request,))

    def add_traces_request(self, address: str) -> "EVMQuery":
        request = TracesRequest(address=[_validate_address(address)])
        return self._copy(_traces_requests=self._traces_requests + (request,))

    def add_state_diffs_request(self, address: str) -> "EVMQuery":
        request = StateDiffsRequest(address=[_validate_address(address)])
        return self._copy(
            _state_diffs_requests=self._state_diffs_requests + (request,)
        )

    def get_logs(
        self,
        *,
        address: Optional[str] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        topic0: Optional[str] = None,
        topic1: Optional[str] = None,
        topic2: Optional[str] = None,
        topic3: Optional[str] = None,
        include_fields: Optional[Sequence[LogField]] = None,
    ) -> "EVMQuery":
        """Return a new query that includes the requested log filters."""
        query: EVMQuery = self
        if from_block is not None:
            query = query._update_block_range(from_block, to_block)
        query = query.add_logs_request(
            address=address,
            topic0=topic0,
            topic1=topic1,
            topic2=topic2,
            topic3=topic3,
        )
        query = query.add_fields(include_fields)
        return query

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


__all__ = ["EVMQuery", "TransactionField", "LogField"]
