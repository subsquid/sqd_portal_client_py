from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class BlockCursor:
    number: int
    hash: str
    timestamp: Optional[int] = None


@dataclass(slots=True)
class HeadState:
    finalized: Optional[BlockCursor] = None
    unfinalized: Optional[BlockCursor] = None


@dataclass(slots=True)
class BatchState:
    initial: int
    current: BlockCursor
    last: int
    rollback_chain: List[BlockCursor] = field(default_factory=list)
    progress: Any | None = None


@dataclass(slots=True)
class BatchMeta:
    bytes_size: int
    requests: Dict[int, int]
    last_block_received_at: datetime


@dataclass(slots=True)
class BatchCtx:
    head: HeadState
    state: BatchState
    meta: BatchMeta
    query: Dict[str, Any]
    profiler: Any
    metrics: Any
    logger: Any


@dataclass(slots=True)
class PortalBatch:
    data: Any
    ctx: BatchCtx


__all__ = [
    'BlockCursor',
    'HeadState',
    'BatchState',
    'BatchMeta',
    'BatchCtx',
    'PortalBatch',
]
