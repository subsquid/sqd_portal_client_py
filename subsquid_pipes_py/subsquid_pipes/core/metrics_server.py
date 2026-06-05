from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict

from .types import BatchCtx


@dataclass
class Metrics:
    batches: int = 0
    blocks: int = 0
    requests: DefaultDict[int, int] = field(default_factory=lambda: defaultdict(int))


class MetricsServer:
    def __init__(self, *, reporter: Any | None = None) -> None:
        self.metrics = Metrics()
        self.reporter = reporter
        self.logger = None
        self._running = False

    def set_logger(self, logger) -> None:
        self.logger = logger

    async def start(self) -> None:
        self._running = True
        if self.logger:
            self.logger.info('metrics.start')

    async def stop(self) -> None:
        if self.logger:
            self.logger.info('metrics.stop')
        self._running = False

    def add_batch_context(self, ctx: BatchCtx) -> None:
        self.metrics.batches += 1
        self.metrics.blocks += ctx.state.current.number - ctx.state.initial + 1
        for code, count in ctx.meta.requests.items():
            self.metrics.requests[int(code)] += count
        if self.reporter is not None:
            self.reporter(self.metrics)


def noop_metrics_server() -> MetricsServer:
    server = MetricsServer()

    async def _noop(*_args, **_kwargs):
        return None

    server.start = _noop  # type: ignore[assignment]
    server.stop = _noop  # type: ignore[assignment]
    return server


__all__ = ['MetricsServer', 'Metrics', 'noop_metrics_server']
