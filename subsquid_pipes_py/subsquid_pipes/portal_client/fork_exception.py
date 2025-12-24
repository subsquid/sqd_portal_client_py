from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core.types import BlockCursor


@dataclass(slots=True)
class ForkException(Exception):
    previous_blocks: List[BlockCursor]
    query: dict | None = None

    def __str__(self) -> str:
        return f"Fork detected; previous blocks: {[b.number for b in self.previous_blocks]}"
