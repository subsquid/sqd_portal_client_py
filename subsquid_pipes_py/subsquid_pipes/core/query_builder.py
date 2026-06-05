from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Literal, Optional, Protocol, Sequence, TypeVar

from .portal_range import PortalRange, parse_portal_range

F = TypeVar('F', bound=Dict[str, Any])
R = TypeVar('R', bound=Dict[str, Any])


@dataclass(slots=True)
class Range:
    from_block: int | Literal['latest']
    to_block: Optional[int] = None


@dataclass(slots=True)
class RangeRequest(Generic[R]):
    range: Range
    request: R


class Portal(Protocol):
    async def get_head(self) -> Optional[dict[str, int]]:
        ...


class QueryBuilder(Generic[F, R]):
    def __init__(self) -> None:
        self.fields: F = {}  # type: ignore[assignment]
        self.requests: List[RangeRequest[R]] = []

    def get_type(self) -> str:
        raise NotImplementedError

    def add_fields(self, fields: F) -> 'QueryBuilder[F, R]':
        self.fields = _merge_dicts(self.fields, fields)
        return self

    def get_fields(self) -> F:
        return self.fields

    def add_range(self, range_like: dict[str, Any] | PortalRange) -> 'QueryBuilder[F, R]':
        parsed = parse_portal_range(range_like)
        if parsed.from_block == 'latest':
            from_block = 'latest'
        else:
            from_block = int(parsed.from_block)
        request_range = Range(
            from_block=from_block if isinstance(from_block, int) else 0,
            to_block=parsed.to_block,
        )
        self.requests.append(RangeRequest(range=request_range, request={}))  # type: ignore[arg-type]
        return self

    def merge(self, other: 'QueryBuilder[F, R] | None') -> 'QueryBuilder[F, R]':
        if other is None:
            return self
        self.requests.extend(other.requests)
        self.add_fields(other.get_fields())
        return self

    def merge_data_requests(self, *requests: R) -> R:
        raise NotImplementedError

    async def calculate_ranges(self, *, portal: Portal, bound: Optional[Range] = None) -> dict[str, List[RangeRequest[R]]]:
        latest_number = None
        if any(getattr(req.range, 'from_block') == 'latest' for req in self.requests):
            head = await portal.get_head()
            latest_number = head['number'] if head else 0

        ranges: List[RangeRequest[R]] = []
        for req in self.requests:
            begin = req.range.from_block
            if begin == 'latest':
                begin = latest_number or 0
                if bound is not None:
                    begin = min(begin, bound.from_block)
            ranges.append(RangeRequest(range=Range(begin, req.range.to_block), request=req.request))

        if not ranges:
            default_range = RangeRequest(range=Range(bound.from_block if bound else 0, bound.to_block if bound else None), request={})  # type: ignore[arg-type]
            return {'raw': [default_range], 'bounded': [default_range]}

        merged = merge_range_requests(ranges, self.merge_data_requests)
        bounded = apply_range_bound(merged, bound)
        return {'raw': merged, 'bounded': bounded}


def merge_range_requests(
    requests: Sequence[RangeRequest[R]], merge: Callable[[R, R], R]
) -> List[RangeRequest[R]]:
    sorted_requests = sorted(requests, key=lambda r: r.range.from_block)
    result: List[RangeRequest[R]] = []
    for req in sorted_requests:
        if not result:
            result.append(req)
            continue
        last = result[-1]
        intersection = range_intersection(last.range, req.range)
        if not intersection:
            result.append(req)
            continue
        result.pop()
        result.extend(
            RangeRequest(range=segment, request=last.request)
            for segment in range_difference(last.range, intersection)
        )
        result.extend(
            RangeRequest(range=segment, request=req.request)
            for segment in range_difference(req.range, intersection)
        )
        merged_request = merge(last.request, req.request)
        result.append(RangeRequest(range=intersection, request=merged_request))
    return sorted(result, key=lambda r: r.range.from_block)


def apply_range_bound(requests: Sequence[RangeRequest[R]], bound: Optional[Range]) -> List[RangeRequest[R]]:
    if bound is None:
        return list(requests)
    bounded: List[RangeRequest[R]] = []
    for req in requests:
        intersection = range_intersection(req.range, bound)
        if intersection:
            bounded.append(RangeRequest(range=intersection, request=req.request))
    return bounded


def range_intersection(a: Range, b: Range) -> Optional[Range]:
    begin = max(a.from_block, b.from_block)
    end = _min_end(a.to_block, b.to_block)
    if end is not None and begin > end:
        return None
    return Range(begin, end)


def range_difference(a: Range, b: Range) -> List[Range]:
    intersection = range_intersection(a, b)
    if intersection is None:
        return [a]
    pieces: List[Range] = []
    if a.from_block < intersection.from_block:
        pieces.append(Range(a.from_block, intersection.from_block - 1))
    if intersection.to_block is not None:
        if a.to_block is None or intersection.to_block < a.to_block:
            pieces.append(Range(intersection.to_block + 1, a.to_block))
    elif a.to_block is not None:
        pieces.append(Range(intersection.to_block or (intersection.from_block + 1), a.to_block))
    return pieces


def _min_end(*ends: Optional[int]) -> Optional[int]:
    filtered = [e for e in ends if e is not None]
    return min(filtered) if filtered else None


def hash_query(query: Dict[str, Any]) -> str:
    trimmed = {k: v for k, v in query.items() if k not in {'fromBlock', 'toBlock', 'parentBlockHash'}}
    payload = json.dumps(trimmed, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(a)
    for key, value in b.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


