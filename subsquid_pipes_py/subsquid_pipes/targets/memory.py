from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..core.target import Target
from ..core.types import PortalBatch


@dataclass
class MemoryTarget(Target):
    batches: List[PortalBatch] = field(default_factory=list)

    async def write(self, *, read, logger) -> None:  # type: ignore[override]
        async for batch in read():
            self.batches.append(batch)
            logger.info('memory-target.batch', cursor=batch.ctx.state.current.number)

    async def fork(self, previous_blocks):  # type: ignore[override]
        return previous_blocks[-1] if previous_blocks else None


__all__ = ['MemoryTarget']
