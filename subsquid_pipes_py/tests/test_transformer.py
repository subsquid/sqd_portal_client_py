from __future__ import annotations

import asyncio
from datetime import datetime


from subsquid_pipes.core.metrics_server import MetricsServer
from subsquid_pipes.core.profiling import Span
from subsquid_pipes.core.transformer import create_transformer
from subsquid_pipes.core.types import BatchCtx, BatchMeta, BatchState, BlockCursor, HeadState


def _ctx() -> BatchCtx:
    return BatchCtx(
        head=HeadState(finalized=None, unfinalized=None),
        state=BatchState(
            initial=0,
            current=BlockCursor(number=0, hash='0x0'),
            last=10,
            rollback_chain=[],
        ),
        meta=BatchMeta(bytes_size=0, requests={}, last_block_received_at=datetime.utcnow()),
        query={'url': 'http://localhost', 'hash': 'abc', 'raw': {}},
        profiler=Span.root('test', True),
        metrics=MetricsServer().metrics,
        logger=None,
    )


def test_transformer_pipeline_executes_in_order():
    pipeline = create_transformer(
        {
            'profiler': {'id': 'first'},
            'transform': lambda data, ctx: data + ['first'],
        }
    ).pipe(
        {
            'profiler': {'id': 'second'},
            'transform': lambda data, ctx: data + ['second'],
        }
    )

    result = asyncio.run(pipeline.transform([], _ctx()))
    assert result == ['first', 'second']
