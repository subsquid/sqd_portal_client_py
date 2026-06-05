from __future__ import annotations

from typing import Any, AsyncIterator, Awaitable, Callable, Protocol

from .types import BlockCursor, PortalBatch


ReadBatches = Callable[[BlockCursor | None], AsyncIterator[PortalBatch]]


class Target(Protocol):
    async def write(self, *, read: ReadBatches, logger: Any) -> None:
        ...

    async def fork(self, previous_blocks: list[BlockCursor]) -> BlockCursor | None:
        ...


def create_target(options: Target) -> Target:
    return options


__all__ = ['Target', 'create_target']
