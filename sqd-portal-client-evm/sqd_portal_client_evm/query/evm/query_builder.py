"""
EVM Query Builder for SQD Portal Client

This module provides EVM-specific query functionality for the SQD Network portal.
"""
from dataclasses import field, dataclass
from typing import Optional

try:
    import ujson as json_lib
except ImportError:
    import json as json_lib

from sqd_portal_client_evm.query.evm.fields import EVMFields
from sqd_portal_client_evm.query.evm.requests import (
    TransactionsRequest,
    LogsRequest,
    StateDiffsRequest,
    TracesRequest,
    _validate_address, _request_to_sqd_string,
)
from ...base.base import _Fields


@dataclass
class EVMQueryBuilder:
    """
    Builder class for EVM queries with convenient method chaining.
    """
    from_block: int = 0
    to_block: Optional[int] = None
    transactions_requests: list[TransactionsRequest] = field(default_factory=list)
    logs_requests: list[LogsRequest] = field(default_factory=list)
    state_diffs_requests: list[StateDiffsRequest] = field(default_factory=list)
    traces_requests: list[TracesRequest] = field(default_factory=list)
    fields: Optional[_Fields] = None
    type = 'evm'

    @classmethod
    def get_transactions(
            cls,
            from_address: Optional[str] = None,
            to_address: Optional[str] = None,
            sighash: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_logs: bool = False,
            include_traces: bool = False,
            include_state_diffs: bool = False,
            fields: Optional[EVMFields] = None,
    ) -> EVMQueryBuilder:
        """
        Create an EVM transaction query.

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
            query = Query.evm().get_transactions(from_address='0x123...', from_block=17000000)
        """
        request = TransactionsRequest(
            from_=[_validate_address(from_address)] if from_address else None,
            to=[_validate_address(to_address)] if to_address else None,
            sighash=[sighash] if sighash else None,
            logs=include_logs,
            traces=include_traces,
            stateDiffs=include_state_diffs,
        )

        return cls(
            from_block=from_block,
            to_block=to_block,
            transactions_requests=[request],
            fields=fields or EVMFields.minimal_fields(),
        )

    @classmethod
    def get_logs(
            cls,
            contract_address: Optional[str] = None,
            topic0: Optional[str] = None,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_transaction: bool = True,
            fields: Optional[EVMFields] = None,
    ) -> EVMQueryBuilder:
        """
        Create an EVM logs query.

        Args:
            contract_address: Contract address to get logs from
            topic0: Event signature hash (first topic)
            from_block: Starting block number
            to_block: Ending block number (optional)
            include_transaction: Include the triggering transaction
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.evm().get_logs(contract_address='0x123...', from_block=17000000)
        """
        if contract_address:
            request = LogsRequest(
                address=[_validate_address(contract_address)],
                transaction=include_transaction,
            )
        else:
            # Create a basic logs request
            request = LogsRequest(topic0=[topic0] if topic0 else None)

        return cls(
            from_block=from_block,
            to_block=to_block,
            logs_requests=[request],
            fields=fields or EVMFields.minimalEVMFields(),
        )

    @classmethod
    def get_erc20_transfers(
            cls,
            token_address: str,
            from_block: int = 0,
            to_block: Optional[int] = None,
            include_transaction: bool = True,
            fields: Optional[EVMFields] = None,
    ) -> EVMQueryBuilder:
        """
        Create an EVM ERC-20 transfers query.

        Args:
            token_address: ERC-20 token contract address
            from_block: Starting block number
            to_block: Ending block number (optional)
            include_transaction: Include the transfer transaction
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.evm().get_erc20_transfers('0xa0b86a33e6c6...', from_block=17000000)
        """
        request = LogsRequest(
            address=[_validate_address(token_address)],
            topic0=[
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ],
            transaction=include_transaction,
        )

        return cls(
            from_block=from_block,
            to_block=to_block,
            logs_requests=[request],
            fields=fields or EVMFields.minimalEVMFields(),
        )

    @classmethod
    def get_state_diffs(
            cls,
            contract_address: str,
            from_block: int = 0,
            to_block: Optional[int] = None,
            fields: Optional[EVMFields] = None,
    ) -> EVMQueryBuilder:
        """
        Create an EVM state diffs query.

        Args:
            contract_address: Contract address to get state changes for
            from_block: Starting block number
            to_block: Ending block number (optional)
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.evm().get_state_diffs('0x123...', from_block=17000000)
        """
        request = StateDiffsRequest(address=[_validate_address(contract_address)])

        # Import here to avoid circular imports
        return cls(
            from_block=from_block,
            to_block=to_block,
            state_diffs_requests=[request],
            fields=fields or EVMFields.minimalEVMFields(),
        )

    @classmethod
    def get_traces(
            cls,
            contract_address: str,
            from_block: int = 0,
            to_block: Optional[int] = None,
            fields: Optional[EVMFields] = None,
    ) -> EVMQueryBuilder:
        """
        Create an EVM traces query.

        Args:
            contract_address: Contract address to get traces for
            from_block: Starting block number
            to_block: Ending block number (optional)
            fields: Fields to include (default: minimal fields)

        Example:
            query = Query.evm().get_traces('0x123...', from_block=17000000)
        """
        request = TracesRequest(address=[_validate_address(contract_address)])

        # Import here to avoid circular imports

        return cls(
            from_block=from_block,
            to_block=to_block,
            traces_requests=[request],
            fields=fields or EVMFields.minimalEVMFields(),
        )

    def to_sqd_string(self):
        """Convert query builder to SQD API string format"""
        # Build the complete query structure
        query_dict = {
            "type": self.type,
            "fromBlock": self.from_block,
        }

        if self.to_block is not None:
            query_dict["toBlock"] = self.to_block

        if self.fields is not None:
            if hasattr(self.fields, 'to_sqd_string'):
                # Parse the JSON string back to dict for consistency
                query_dict["fields"] = json_lib.loads(self.fields.to_sqd_string())
            else:
                # Fallback for other field formats
                query_dict["fields"] = self.fields

        # Add requests if any exist
        requests_dict = {}

        if self.transactions_requests:
            requests_dict["transactions"] = [
                {k: v for k, v in _request_to_sqd_string(r).items() if v is not None}
                for r in self.transactions_requests
            ]

        if self.logs_requests:
            requests_dict["logs"] = [
                {k: v for k, v in _request_to_sqd_string(r).items() if v is not None}
                for r in self.logs_requests
            ]

        if self.state_diffs_requests:
            requests_dict["stateDiffs"] = [
                {k: v for k, v in _request_to_sqd_string(r).items() if v is not None}
                for r in self.state_diffs_requests
            ]

        if self.traces_requests:
            requests_dict["traces"] = [
                {k: v for k, v in _request_to_sqd_string(r).items() if v is not None}
                for r in self.traces_requests
            ]

        if requests_dict:
            query_dict["requests"] = requests_dict

        return json_lib.dumps(query_dict, separators=(",", ":"))
