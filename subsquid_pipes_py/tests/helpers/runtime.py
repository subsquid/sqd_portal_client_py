from __future__ import annotations

from typing import Any, List

from subsquid_pipes.core import PortalBatch, create_transformer


def block_transformer():
    return create_transformer({
        'profiler': {'id': 'block-transformer'},
        'transform': lambda data, ctx: [block['header'] for block in data['blocks']],
    })


async def read_all(stream) -> List[Any]:
    results: List[Any] = []
    async for batch in stream:
        if isinstance(batch, PortalBatch):
            results.extend(batch.data)
        else:
            results.extend(batch)
    return results
