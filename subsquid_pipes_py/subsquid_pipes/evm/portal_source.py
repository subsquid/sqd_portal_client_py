from __future__ import annotations

from typing import Any, Dict

from ..core import PortalSource, PortalSourceOptions, create_default_logger, create_transformer, progress_tracker
from ..core.metrics_server import MetricsServer
from ..core.progress_tracker import ProgressTrackerOptions
from ..core.transformer import Transformer
from ..portal_client import PortalClient, PortalClientOptions
from .query_builder import EvmQueryBuilder


def evm_portal_source(
    *,
    portal: str | PortalClientOptions | PortalClient,
    query: Dict[str, Any] | EvmQueryBuilder | None = None,
    cache=None,
    metrics: MetricsServer | None = None,
    logger=None,
    progress: ProgressTrackerOptions | None = None,
) -> PortalSource:
    logger = logger or create_default_logger()
    builder = (
        query
        if isinstance(query, EvmQueryBuilder)
        else EvmQueryBuilder()
    )
    if isinstance(query, dict):
        builder.add_range(query)
    transformers: list[Transformer[Any, Any, Any]] = []
    if progress:
        transformers.append(progress_tracker(progress))
    transformers.append(
        create_transformer(
            {
                'profiler': {'id': 'normalize-data'},
                'transform': lambda data, ctx: data,
            }
        )
    )
    return PortalSource(
        PortalSourceOptions(
            portal=portal,
            query=builder,
            logger=logger,
            cache=cache,
            metrics=metrics,
            transformers=transformers,
        )
    )


__all__ = ['evm_portal_source']
