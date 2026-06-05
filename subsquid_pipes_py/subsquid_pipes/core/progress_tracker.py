from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .transformer import create_transformer


@dataclass(slots=True)
class StartState:
    initial: int
    last: int


@dataclass(slots=True)
class ProgressState:
    current: int
    last: int
    finalized: int | None

    @property
    def percentage(self) -> float:
        span = max(self.last - self.current, 1)
        processed = self.current
        return min(100.0, (processed / self.last) * 100)


@dataclass
class ProgressTrackerOptions:
    logger: any = None
    interval: float | None = None
    on_start: Callable[[StartState], None] | None = None
    on_progress: Callable[[ProgressState], None] | None = None


def progress_tracker(options: ProgressTrackerOptions):
    async def _start(ctx):
        state = StartState(initial=ctx['state']['initial'], last=ctx['state'].get('last', ctx['state']['initial']))
        if options.on_start:
            options.on_start(state)
        if options.logger:
            options.logger.info('progress.start', initial=state.initial, last=state.last)

    async def _transform(data, batch_ctx):
        progress = ProgressState(
            current=batch_ctx.state.current.number,
            last=batch_ctx.state.last,
            finalized=batch_ctx.head.finalized.number if batch_ctx.head.finalized else None,
        )
        batch_ctx.state.progress = progress
        if options.on_progress:
            options.on_progress(progress)
        if options.logger:
            options.logger.debug('progress.tick', current=progress.current, last=progress.last)
        return data

    return create_transformer({
        'profiler': {'id': 'progress-tracker'},
        'start': _start,
        'transform': _transform,
    })


__all__ = ['progress_tracker', 'ProgressTrackerOptions', 'ProgressState', 'StartState']
