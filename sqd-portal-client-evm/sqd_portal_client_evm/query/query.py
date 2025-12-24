from __future__ import annotations

from typing import Literal, overload

from sqd_portal_client_evm.query.evm_factory import EVMQueryFactory
from sqd_portal_client_evm.query.solana_factory import SolanaQueryFactory
from .base_query import BaseSQDQuery
from .evm_query import LogField, TransactionField
from .solana_query import (
    BalanceField,
    InstructionField,
    RewardField,
    SolanaBlockField,
    SolanaLogField,
    SolanaTransactionField,
    TokenBalanceField,
)
from ..dataset import SolanaDataset, EvmDataset, Dataset


@overload
def SQD(
    *,
    dataset: SolanaDataset,
    portal_url: str = "https://portal.sqd.dev",
    stream_type: Literal["finalized", "realtime"] = "realtime",
) -> SolanaQueryFactory: ...


@overload
def SQD(
    *,
    dataset: EvmDataset,
    portal_url: str = "https://portal.sqd.dev",
    stream_type: Literal["finalized", "realtime"] = "realtime",
) -> EVMQueryFactory: ...


def SQD(
    *,
    dataset: Dataset,
    portal_url: str = "https://portal.sqd.dev",
    stream_type: Literal["finalized", "realtime"] = "realtime",
) -> EVMQueryFactory | SolanaQueryFactory:
    """
    Return the strongly typed query builder that matches the selected dataset.
    ```
    sqd = SQD(dataset=Dataset.ETHEREUM)
    sqd.get_transactions(...)
    ```
    """
    dataset_enum = _normalize_dataset(dataset)
    query_type = _infer_query_type(dataset_enum)
    if query_type == "solana":
        return SolanaQueryFactory(
            dataset=dataset_enum, portal_url=portal_url, stream_type=stream_type
        )
    return EVMQueryFactory(
        dataset=dataset_enum, portal_url=portal_url, stream_type=stream_type
    )


def _normalize_dataset(dataset: Dataset | str) -> Dataset:
    if isinstance(dataset, Dataset):
        return dataset
    try:
        return Dataset(dataset)
    except ValueError as exc:
        raise ValueError(f"Unsupported dataset '{dataset}'") from exc


def _infer_query_type(dataset: Dataset) -> Literal["evm", "solana"]:
    if "solana" in dataset.value.lower():
        return "solana"
    return "evm"


SQDQuery = BaseSQDQuery

__all__ = [
    "SQD",
    "SQDQuery",
    "TransactionField",
    "LogField",
    "InstructionField",
    "SolanaTransactionField",
    "SolanaLogField",
    "BalanceField",
    "TokenBalanceField",
    "RewardField",
    "SolanaBlockField",
]
