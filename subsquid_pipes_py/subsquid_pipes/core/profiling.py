from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, Sequence

__all__ = ['ProfilerOptions', 'Profiler', 'Span', 'DummyProfiler']

ProfilerOptions = dict[str, Any] | None


class Profiler(Protocol):
    name: str

    def start(self, name: str) -> 'Profiler':
        ...

    async def measure(self, name: str, fn: Callable[['Profiler'], Any]) -> Any:
        ...

    def add_labels(self, labels: Sequence[str] | str) -> 'Profiler':
        ...

    def add_transformer_exemplar(self, data: Any) -> 'Profiler':
        ...

    def end(self) -> 'Profiler':
        ...


@dataclass
class Span:
    name: str
    enabled: bool = True
    started: float = field(default_factory=time.perf_counter)
    elapsed: float = 0.0
    labels: list[str] = field(default_factory=list)
    children: list['Span'] = field(default_factory=list)
    data: Any | None = None

    @classmethod
    def root(cls, name: str, enabled: bool) -> 'Profiler':
        return cls(name=name, enabled=enabled) if enabled else DummyProfiler()

    def start(self, name: str) -> 'Span':
        child = Span(name=name, enabled=self.enabled)
        self.children.append(child)
        return child

    async def measure(self, name: str, fn: Callable[['Profiler'], Any]) -> Any:
        span = self.start(name)
        try:
            result = await fn(span)
        finally:
            span.end()
        return result

    def add_labels(self, labels: Sequence[str] | str) -> 'Span':
        if isinstance(labels, str):
            self.labels.append(labels)
        else:
            self.labels.extend(labels)
        return self

    def add_transformer_exemplar(self, data: Any) -> 'Span':
        self.data = _pack_exemplar(data)
        return self

    def end(self) -> 'Span':
        self.elapsed = time.perf_counter() - self.started
        return self

    def pretty(self, level: int = 0) -> str:
        indent = ' ' * level
        children = '\n'.join(child.pretty(level + 1) for child in self.children)
        line = f"{indent}[{self.name}] {self.elapsed*1000:.2f}ms"
        return f"{line}\n{children}" if children else line


@dataclass
class DummyProfiler:
    name: str = 'noop'

    def start(self, name: str) -> 'DummyProfiler':
        return self

    async def measure(self, name: str, fn: Callable[['Profiler'], Any]) -> Any:
        return await fn(self)

    def add_labels(self, labels: Sequence[str] | str) -> 'DummyProfiler':
        return self

    def add_transformer_exemplar(self, data: Any) -> 'DummyProfiler':
        return self

    def end(self) -> 'DummyProfiler':
        return self


def _pack_exemplar(value: Any) -> Any:
    if isinstance(value, list):
        if len(value) <= 10 and all(isinstance(v, (str, int, float, bool)) for v in value):
            return value
        if len(value) > 10:
            return [_pack_exemplar(value[0]), f"... {len(value) - 1} more ..."]
        return [_pack_exemplar(v) for v in value]
    if isinstance(value, dict):
        return {k: _pack_exemplar(v) for k, v in value.items()}
    return value
