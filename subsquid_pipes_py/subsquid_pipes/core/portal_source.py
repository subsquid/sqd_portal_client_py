from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Generic, Iterable, List, Optional, Protocol, TypeVar

from .logger import Logger, create_default_logger
from .metrics_server import MetricsServer, noop_metrics_server
from .profiling import DummyProfiler, Span
from .query_builder import QueryBuilder, Range, hash_query
from .target import Target
from .transformer import Transformer, TransformerOptions, create_transformer
from .types import BatchCtx, BatchMeta, BatchState, BlockCursor, HeadState, PortalBatch
from ..portal_client import ForkException, PortalClient, PortalClientOptions

T = TypeVar('T')
Q = TypeVar('Q', bound=QueryBuilder)


class PortalCache(Protocol):
    def get_stream(self, *, portal: PortalClient, query: dict[str, Any], logger: Logger):
        ...


@dataclass
class PortalSourceOptions(Generic[Q]):
    portal: PortalClient | PortalClientOptions | str
    query: Q
    logger: Logger | None = None
    cache: PortalCache | None = None
    profiler: bool = True
    metrics: MetricsServer | None = None
    transformers: List[Transformer[Any, Any, Any]] | None = None


class PortalSource(Generic[Q, T]):
    def __init__(self, options: PortalSourceOptions[Q]) -> None:
        self._logger = options.logger or create_default_logger()
        self._portal = (
            options.portal
            if isinstance(options.portal, PortalClient)
            else PortalClient(
                options.portal
                if isinstance(options.portal, PortalClientOptions)
                else PortalClientOptions(url=str(options.portal))
            )
        )
        self._query_builder = options.query
        self._cache = options.cache
        self._profiler_enabled = options.profiler
        self._metrics = options.metrics or noop_metrics_server()
        self._metrics.set_logger(self._logger)
        self._transformers: List[Transformer[Any, Any, Any]] = options.transformers or []
        self._started = False

    def pipe(self, transformer_or_options: Transformer[Any, Any, Any] | TransformerOptions[Any, Any, Any] | Any):
        if isinstance(transformer_or_options, Transformer):
            transformer = transformer_or_options
        elif callable(transformer_or_options):
            transformer = create_transformer({'transform': transformer_or_options})
        else:
            transformer = create_transformer(transformer_or_options)
        transformers = [*self._transformers, transformer]
        return PortalSource(
            PortalSourceOptions(
                portal=self._portal,
                query=self._query_builder,
                logger=self._logger,
                cache=self._cache,
                profiler=self._profiler_enabled,
                metrics=self._metrics,
                transformers=transformers,
            )
        )

    async def __aiter__(self) -> AsyncIterator[PortalBatch]:
        await self._configure()
        try:
            async for batch in self._read():
                yield batch
                self._batch_end(batch.ctx)
        finally:
            await self._stop()

    async def pipe_to(self, target: Target) -> None:
        async def reader(cursor: BlockCursor | None = None) -> AsyncIterator[PortalBatch]:
            await self._configure()
            while True:
                try:
                    async for batch in self._read(cursor):
                        yield batch
                        self._batch_end(batch.ctx)
                    return
                except ForkException as exc:
                    fork_handler = getattr(target, 'fork', None)
                    if fork_handler is None:
                        raise
                    forked_cursor = await fork_handler(exc.previous_blocks)
                    if forked_cursor is None:
                        raise RuntimeError('Target did not return a cursor after fork')
                    await self._fork_transformers(forked_cursor)
                    cursor = forked_cursor
                finally:
                    await self._stop()

        await target.write(read=reader, logger=self._logger)

    async def _configure(self) -> None:
        profiler = Span.root('configure', self._profiler_enabled)
        span = profiler.start('transformers')
        ctx = {'query_builder': self._query_builder, 'portal': self._portal, 'logger': self._logger}
        await asyncio.gather(*(t.query(ctx) for t in self._transformers))
        span.end()
        profiler.end()

    async def _start(self, state: dict[str, Any]) -> None:
        if self._started:
            return
        profiler = Span.root('start', self._profiler_enabled)
        span = profiler.start('transformers')
        ctx = {'state': state, 'metrics': self._metrics.metrics}
        await asyncio.gather(*(t.start(ctx) for t in self._transformers))
        span.end()
        await self._metrics.start()
        profiler.end()
        self._started = True

    async def _stop(self) -> None:
        if not self._started:
            return
        profiler = Span.root('stop', self._profiler_enabled)
        span = profiler.start('transformers')
        await asyncio.gather(*(t.stop({'logger': self._logger}) for t in self._transformers))
        span.end()
        profiler.end()
        await self._metrics.stop()
        self._started = False

    async def _read(self, cursor: BlockCursor | None = None) -> AsyncIterator[PortalBatch]:
        # Ensure block cursor fields are always requested
        self._query_builder.add_fields({'block': {'hash': True, 'number': True}})
        bound = Range(from_block=cursor.number + 1 if cursor else 0, to_block=None) if cursor else None
        ranges = await self._query_builder.calculate_ranges(portal=self._portal, bound=bound)
        raw = ranges['raw']
        bounded = ranges['bounded']
        initial = raw[0].range.from_block if raw else 0
        last_target = (
            bounded[-1].range.to_block
            if bounded and bounded[-1].range.to_block is not None
            else (raw[-1].range.to_block if raw and raw[-1].range.to_block is not None else initial)
        )
        await self._start(
            {
                'initial': initial,
                'current': cursor or BlockCursor(number=initial, hash='0x0'),
                'last': last_target,
            }
        )
        metadata = await self._portal.get_metadata()
        if not metadata.get('real_time', True):
            self._logger.warning('dataset is not real-time', dataset=metadata.get('dataset'))
        for request in bounded:
            query = {
                'type': self._query_builder.get_type(),
                'fields': self._query_builder.get_fields(),
                'fromBlock': request.range.from_block,
                'toBlock': request.range.to_block,
                'parentBlockHash': cursor.hash if cursor else None,
                **request.request,
            }
            stream = self._portal.get_stream(query)
            async for batch in stream:
                if not batch.blocks:
                    continue
                last_block = batch.blocks[-1]
                head = HeadState(finalized=batch.finalized_head, unfinalized=None)
                ctx = BatchCtx(
                    head=head,
                    state=BatchState(
                        initial=initial,
                        current=BlockCursor(
                            number=last_block['header']['number'],
                            hash=last_block['header']['hash'],
                            timestamp=last_block['header'].get('timestamp'),
                        ),
                        last=request.range.to_block or last_block['header']['number'],
                        rollback_chain=[
                            BlockCursor(
                                number=b['header']['number'],
                                hash=b['header']['hash'],
                                timestamp=b['header'].get('timestamp'),
                            )
                            for b in batch.blocks
                        ],
                    ),
                    meta=BatchMeta(
                        bytes_size=batch.meta['bytes'],
                        requests=batch.meta['requests'],
                        last_block_received_at=batch.meta['lastBlockReceivedAt'],
                    ),
                    query={'url': self._portal.get_url(), 'hash': hash_query(query), 'raw': query},
                    profiler=Span.root('batch', self._profiler_enabled),
                    metrics=self._metrics.metrics,
                    logger=self._logger,
                )
                data = await self._apply_transformers(ctx, {'blocks': batch.blocks})
                yield PortalBatch(data=data, ctx=ctx)

    async def _apply_transformers(self, ctx: BatchCtx, data: T) -> T:
        current = data
        for transformer in self._transformers:
            current = await transformer.transform(current, ctx)
        return current

    def _batch_end(self, ctx: BatchCtx) -> None:
        if isinstance(ctx.profiler, Span):
            ctx.profiler.end()
        self._metrics.add_batch_context(ctx)

    async def _fork_transformers(self, cursor: BlockCursor) -> None:
        profiler = Span.root('fork', self._profiler_enabled)
        span = profiler.start('transformers_rollback')
        ctx = {'logger': self._logger}
        await asyncio.gather(*(t.fork(cursor, ctx) for t in self._transformers))
        span.end()
        profiler.end()


__all__ = ['PortalSource', 'PortalSourceOptions', 'PortalBatch']
