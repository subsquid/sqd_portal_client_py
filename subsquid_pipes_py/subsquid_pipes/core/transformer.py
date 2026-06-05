from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Generic, List, Optional, Protocol, TypeVar, overload

from .profiling import DummyProfiler, Profiler, Span
from .types import BatchCtx, BlockCursor

InT = TypeVar('InT')
OutT = TypeVar('OutT')
ResT = TypeVar('ResT')
QueryT = TypeVar('QueryT')


class QueryContext(Protocol[QueryT]):
    query_builder: QueryT
    portal: Any
    logger: Any


@dataclass
class TransformerOptions(Generic[InT, OutT, QueryT]):
    transform: Callable[[InT, BatchCtx], Awaitable[OutT]] | Callable[[InT, BatchCtx], OutT]
    profiler: Optional[dict[str, Any]] = None
    query: Optional[Callable[[QueryContext[QueryT]], Awaitable[None] | None]] = None
    start: Optional[Callable[[dict[str, Any]], Awaitable[None] | None]] = None
    stop: Optional[Callable[[dict[str, Any]], Awaitable[None] | None]] = None
    fork: Optional[Callable[[BlockCursor, dict[str, Any]], Awaitable[None] | None]] = None


@dataclass
class Transformer(Generic[InT, OutT, QueryT]):
    options: TransformerOptions[InT, OutT, QueryT]
    children: List['Transformer[Any, Any, QueryT]'] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.options, dict):  # type: ignore[arg-type]
            self.options = TransformerOptions(**self.options)  # type: ignore[assignment]

    def id(self) -> str:
        return (self.options.profiler or {}).get('id', 'anonymous')

    def set_id(self, identifier: str) -> None:
        if self.options.profiler is None:
            self.options.profiler = {}
        self.options.profiler['id'] = identifier

    async def query(self, ctx: QueryContext[QueryT]) -> None:
        if callable(self.options.query):
            await _maybe_await(self.options.query(ctx))
        await _fan_out(self.children, 'query', ctx)

    async def start(self, ctx: dict[str, Any]) -> None:
        if callable(self.options.start):
            await _maybe_await(self.options.start(ctx))
        await _fan_out(self.children, 'start', ctx)

    async def stop(self, ctx: dict[str, Any]) -> None:
        if callable(self.options.stop):
            await _maybe_await(self.options.stop(ctx))
        await _fan_out(self.children, 'stop', ctx)

    async def fork(self, cursor: BlockCursor, ctx: dict[str, Any]) -> None:
        if callable(self.options.fork):
            await _maybe_await(self.options.fork(cursor, ctx))
        await _fan_out(self.children, 'fork', cursor, ctx)

    async def transform(self, data: InT, ctx: BatchCtx) -> OutT:
        profiler: Profiler = ctx.profiler or DummyProfiler()
        span = profiler.start(self.id()) if isinstance(profiler, Span) else profiler
        result = await _maybe_await(self.options.transform(data, ctx))
        span.add_transformer_exemplar(result)
        current: Any = result
        for child in self.children:
            current = await child.transform(current, ctx)
        span.end()
        return current

    @overload
    def pipe(self, transformer: 'Transformer[OutT, ResT, QueryT]') -> 'Transformer[InT, ResT, QueryT]':
        ...

    @overload
    def pipe(self, transformer: TransformerOptions[OutT, ResT, QueryT]) -> 'Transformer[InT, ResT, QueryT]':
        ...

    @overload
    def pipe(self, transformer: Callable[[OutT, BatchCtx], ResT]) -> 'Transformer[InT, ResT, QueryT]':
        ...

    def pipe(self, transformer: Any) -> 'Transformer[InT, Any, QueryT]':
        if isinstance(transformer, Transformer):
            node = transformer
        elif isinstance(transformer, dict):
            node = Transformer(transformer)
        else:
            node = Transformer(TransformerOptions(transform=transformer))
        self.children.append(node)
        return self  # type: ignore[return-value]


def create_transformer(options: TransformerOptions[InT, OutT, QueryT] | dict) -> Transformer[InT, OutT, QueryT]:
    return Transformer(options)  # type: ignore[arg-type]


async def _fan_out(transformers: List[Transformer[Any, Any, Any]], method: str, *args: Any) -> None:
    for transformer in transformers:
        handler = getattr(transformer, method)
        await handler(*args)


def _is_awaitable(value: Any) -> bool:
    return hasattr(value, '__await__')


async def _maybe_await(value: Any) -> Any:
    if _is_awaitable(value):
        return await value
    return value
