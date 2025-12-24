from __future__ import annotations

from typing import Literal, Optional, Sequence

from ..dataset import Dataset
from .factory import BaseQueryFactory
from .evm_query import EVMQuery, LogField, TransactionField


class EVMQueryFactory(BaseQueryFactory):
    """Build EVM queries for a given SQD client."""

    def __init__(
        self,
        *,
        dataset: Dataset,
        portal_url: str,
        stream_type: Literal["finalized", "realtime"],
    ) -> None:
        super().__init__(
            dataset=dataset, portal_url=portal_url, stream_type=stream_type
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
    ) -> EVMQuery:
        query = EVMQuery.create(
            client=self,
            from_block=from_block,
            to_block=to_block,
        )
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
        address: Optional[str] = None,
        from_block: int,
        to_block: Optional[int] = None,
        topic0: Optional[str] = None,
        topic1: Optional[str] = None,
        topic2: Optional[str] = None,
        topic3: Optional[str] = None,
        include_fields: Optional[Sequence[LogField]] = None,
    ) -> EVMQuery:
        query = EVMQuery.create(
            client=self,
            from_block=from_block,
            to_block=to_block,
        )
        query = query.add_logs_request(
            address=address,
            topic0=topic0,
            topic1=topic1,
            topic2=topic2,
            topic3=topic3,
        )
        return query.add_fields(include_fields)


__all__ = ["EVMQueryFactory"]
