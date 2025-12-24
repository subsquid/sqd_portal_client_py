from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NumberLike = int | str


@dataclass(slots=True)
class PortalRange:
    from_block: int | Literal['latest']
    to_block: int | None = None


def parse_portal_range(range_like: dict[str, NumberLike] | PortalRange) -> PortalRange:
    if isinstance(range_like, PortalRange):
        return range_like
    start = range_like.get('from')
    end = range_like.get('to')
    if start == 'latest':
        from_block: int | Literal['latest'] = 'latest'
    else:
        from_block = int(_normalize_block_number(start))
    to_block = int(_normalize_block_number(end)) if end is not None else None
    return PortalRange(from_block=from_block, to_block=to_block)


def _normalize_block_number(value: NumberLike | None) -> int:
    if value is None:
        raise ValueError('Block boundary cannot be None')
    if isinstance(value, int):
        return value
    sanitized = value.replace(',', '').strip()
    if sanitized.startswith('0x'):
        return int(sanitized, 16)
    return int(sanitized, 10)


__all__ = ['PortalRange', 'parse_portal_range']
