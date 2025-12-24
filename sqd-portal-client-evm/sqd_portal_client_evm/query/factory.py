from __future__ import annotations

from typing import Literal, Optional, TYPE_CHECKING

import aiohttp

from sqd_portal_client_evm import Dataset
from sqd_portal_client_evm.query.base_query import BaseSQDQuery
from sqd_portal_client_evm.query.cursor import QueryCursor

if TYPE_CHECKING:  # pragma: no cover - imported only for typing
    from .evm_factory import EVMQueryFactory
    from .solana_factory import SolanaQueryFactory


class BaseQueryFactory:
    """Base factory that provides shared streaming helpers."""

    def __init__(
        self,
        *,
        dataset: Dataset,
        portal_url: str,
        stream_type: Literal["finalized", "realtime"],
    ) -> None:
        self.dataset = dataset
        self.portal_url = portal_url
        self.stream_type = stream_type

    def stream(
        self,
        query: BaseSQDQuery,
        *,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> "QueryCursor":
        if query.client is not self:
            raise ValueError("Query was built by a different factory.")

        return QueryCursor(query, session=session)


QueryFactory = BaseQueryFactory


def create_query_factory(
    query_type: Literal["evm", "solana"],
    *,
    dataset: Dataset,
    portal_url: str,
    stream_type: Literal["finalized", "realtime"] = "realtime",
) -> "EVMQueryFactory | SolanaQueryFactory":
    """
    Return the chain-specific factory that knows how to build queries for the
    current dataset.
    """
    if query_type == "evm":
        from .evm_factory import EVMQueryFactory

        return EVMQueryFactory(
            dataset=dataset, portal_url=portal_url, stream_type=stream_type
        )
    if query_type == "solana":
        from .solana_factory import SolanaQueryFactory

        return SolanaQueryFactory(
            dataset=dataset, portal_url=portal_url, stream_type=stream_type
        )
    raise ValueError(f"Unsupported query type: {query_type}")


__all__ = ["BaseQueryFactory", "create_query_factory", "QueryFactory"]
