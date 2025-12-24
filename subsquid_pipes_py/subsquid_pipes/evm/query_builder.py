from __future__ import annotations

from typing import Any, Dict, List, TypedDict

from ..core.portal_range import PortalRange, parse_portal_range
from ..core.query_builder import QueryBuilder, Range, RangeRequest


class LogRequest(TypedDict, total=False):
    address: List[str]
    topic0: List[str]


class TransactionRequest(TypedDict, total=False):
    from_: List[str]
    to: List[str]


DataRequest = Dict[str, Any]
FieldSelection = Dict[str, Any]


class EvmQueryBuilder(QueryBuilder[FieldSelection, DataRequest]):
    def __init__(self) -> None:
        super().__init__()

    def get_type(self) -> str:
        return 'evm'

    def add_fields(self, fields: FieldSelection) -> 'EvmQueryBuilder':
        return super().add_fields(fields)  # type: ignore[return-value]

    def add_range(self, range_like: dict[str, Any] | PortalRange) -> 'EvmQueryBuilder':
        parsed = parse_portal_range(range_like)
        request = RangeRequest(range=Range(from_block=parsed.from_block, to_block=parsed.to_block), request={})
        self.requests.append(request)
        return self

    def add_log(self, *, range: dict[str, Any], request: LogRequest) -> 'EvmQueryBuilder':
        parsed = parse_portal_range(range)
        self.requests.append(RangeRequest(range=Range(from_block=parsed.from_block, to_block=parsed.to_block), request={'logs': [request]}))
        return self

    def add_transaction(self, *, range: dict[str, Any], request: TransactionRequest) -> 'EvmQueryBuilder':
        parsed = parse_portal_range(range)
        self.requests.append(
            RangeRequest(range=Range(from_block=parsed.from_block, to_block=parsed.to_block), request={'transactions': [request]})
        )
        return self

    def include_all_blocks(self, range_like: dict[str, Any] | PortalRange) -> 'EvmQueryBuilder':
        parsed = parse_portal_range(range_like)
        self.requests.append(
            RangeRequest(range=Range(from_block=parsed.from_block, to_block=parsed.to_block), request={'includeAllBlocks': True})
        )
        return self

    def merge_data_requests(self, *requests: DataRequest) -> DataRequest:
        merged: DataRequest = {}
        include_all_blocks = False
        for req in requests:
            if req.get('includeAllBlocks'):
                include_all_blocks = True
            for key, value in req.items():
                if key == 'includeAllBlocks':
                    continue
                merged.setdefault(key, [])
                merged[key].extend(value)
        if include_all_blocks:
            merged['includeAllBlocks'] = True
        return merged


__all__ = ['EvmQueryBuilder']
