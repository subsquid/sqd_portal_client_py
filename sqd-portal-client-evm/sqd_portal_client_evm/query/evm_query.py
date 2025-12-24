from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Literal, Optional, Sequence, Tuple

from sqd_portal_client_evm.query.base_query import FieldValue, BaseSQDQuery, _freeze_field_map
from sqd_portal_client_evm.query.evm import TransactionsRequest, LogsRequest, StateDiffsRequest, TracesRequest, \
    EVMFields
from sqd_portal_client_evm.utils import _request_to_sqd_string, validate_evm_address


class TransactionField(Enum):
    """Fields available for transaction queries."""
    TRANSACTION_HASH = FieldValue("transaction", EVMFields.Transaction.hash)
    TRANSACTION_INDEX = FieldValue("transaction", EVMFields.Transaction.transactionIndex.value)
    BLOCK_NUMBER = FieldValue("block", EVMFields.Block.number.value)
    FROM_ADDRESS = FieldValue("transaction", EVMFields.Transaction.from_.value)
    TO_ADDRESS = FieldValue("transaction", EVMFields.Transaction.to.value)
    GAS_USED = FieldValue("transaction", EVMFields.Transaction.gasUsed.value)


class LogField(Enum):
    """Fields available for log queries."""
    LOG_INDEX = FieldValue("log", EVMFields.Log.logIndex.value)
    TRANSACTION_HASH = FieldValue("log", EVMFields.Log.transactionHash.value)
    TRANSACTION_INDEX = FieldValue("log", EVMFields.Log.transactionIndex.value)
    ADDRESS = FieldValue("log", EVMFields.Log.address.value)
    TOPICS = FieldValue("log", EVMFields.Log.topics.value)
    BLOCK_NUMBER = FieldValue("block", EVMFields.Block.number.value)


@dataclass(frozen=True, kw_only=True)
class EVMQuery(BaseSQDQuery):
    """Immutable EVM query representation.
    
    This class serves as both a query builder and the query itself.
    Use the class methods or SQD() function to create instances.
    
    Example:
        sqd = SQD(dataset='ethereum-mainnet')
        query = sqd.get_transactions(from_block=17_000_000, address='0x...')
        async for tx in query:
            print(tx)
    """
    
    _transactions_requests: Tuple[TransactionsRequest, ...] = field(default_factory=tuple)
    _logs_requests: Tuple[LogsRequest, ...] = field(default_factory=tuple)
    _state_diffs_requests: Tuple[StateDiffsRequest, ...] = field(default_factory=tuple)
    _traces_requests: Tuple[TracesRequest, ...] = field(default_factory=tuple)
    
    # ------------------------------------------------------------------ #
    # Factory methods (entry points)
    # ------------------------------------------------------------------ #
    @classmethod
    def create(
            cls,
            *,
            dataset: str,
            portal_url: str = "https://portal.sqd.dev",
            stream_type: Literal["finalized", "realtime"] = "realtime",
    ) -> "EVMQuery":
        """Create a new EVM query builder with the given configuration.
        
        Args:
            dataset: Dataset to query (e.g., 'ethereum-mainnet', 'arbitrum-one')
            portal_url: SQD portal URL
            stream_type: Type of stream ('finalized' or 'realtime')
            
        Returns:
            A new EVMQuery instance ready for building queries.
        """
        return cls(
            dataset=dataset,
            portal_url=portal_url,
            stream_type=stream_type,
            query_type="evm",
        )
    
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
            include_fields: Optional[Sequence[TransactionField]] = None,
    ) -> "EVMQuery":
        """Query transactions matching the specified criteria.
        
        Args:
            from_block: Starting block number (required)
            address: Address to filter by (sender)
            from_address: Sender address (overrides address)
            to_address: Recipient address
            sighash: Method signature hash to filter by
            to_block: Ending block number
            include_logs: Include transaction logs
            include_traces: Include transaction traces
            include_state_diffs: Include state changes
            include_fields: Specific fields to include in response
            
        Returns:
            A new EVMQuery with the transaction request added.
        """
        query = self._copy(from_block=from_block, to_block=to_block)
        query = query.add_transactions_request(
            from_address=from_address or address,
            to_address=to_address,
            sighash=sighash,
            include_logs=include_logs,
            include_traces=include_traces,
            include_state_diffs=include_state_diffs,
        )
        return query.add_fields(include_fields)
    
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
            include_fields: Optional[Sequence[LogField]] = None,
    ) -> "EVMQuery":
        """Query event logs matching the specified criteria.
        
        Args:
            from_block: Starting block number (required)
            address: Contract address to filter by
            to_block: Ending block number
            topic0: Event signature hash (first topic)
            topic1: First indexed parameter (second topic)
            topic2: Second indexed parameter (third topic)
            topic3: Third indexed parameter (fourth topic)
            include_fields: Specific fields to include in response
            
        Returns:
            A new EVMQuery with the logs request added.
        """
        query = self._copy(from_block=from_block, to_block=to_block)
        query = query.add_logs_request(
            address=address,
            topic0=topic0,
            topic1=topic1,
            topic2=topic2,
            topic3=topic3,
        )
        return query.add_fields(include_fields)
    
    @staticmethod
    def _default_field_map() -> Dict[str, list[Enum]]:
        return {
            "block": [v for v in EVMFields.Block],
            "transaction": [v for v in EVMFields.Transaction],
            "log": [v for v in EVMFields.Log],
            "stateDiff": [v for v in EVMFields.StateDiff],
            "trace": [v for v in EVMFields.Trace],
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
    ) -> "EVMQuery":
        request = LogsRequest(
            address=[validate_evm_address(address)] if address else None,
            topic0=[topic0] if topic0 else None,
            topic1=[topic1] if topic1 else None,
            topic2=[topic2] if topic2 else None,
            topic3=[topic3] if topic3 else None,
        )
        return self._copy(_logs_requests=self._logs_requests + (request,))
    
    def add_traces_request(self, address: str) -> "EVMQuery":
        request = TracesRequest(address=[validate_evm_address(address)])
        return self._copy(_traces_requests=self._traces_requests + (request,))
    
    def add_state_diffs_request(self, address: str) -> "EVMQuery":
        request = StateDiffsRequest(address=[validate_evm_address(address)])
        return self._copy(
            _state_diffs_requests=self._state_diffs_requests + (request,)
        )
    
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
