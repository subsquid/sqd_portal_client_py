from typing import Literal, overload

from sqd.dataset import Dataset, EvmDataset, SolanaDataset
from sqd.query.evm.query import EVMQuery
from sqd.query.solana.query import SolanaQuery
from sqd.utils import _normalize_dataset


@overload
def SQD(  # noqa: N802
    *,
    dataset: SolanaDataset | Literal["solana-mainnet"],
    portal_url: str = "https://portal.sqd.dev",
    stream_type: Literal["finalized", "realtime"] = "realtime",
) -> SolanaQuery: ...


@overload
def SQD(  # noqa: N802
    *,
    dataset: EvmDataset | str,
    portal_url: str = "https://portal.sqd.dev",
    stream_type: Literal["finalized", "realtime"] = "realtime",
) -> EVMQuery: ...


def SQD(  # noqa: N802
    *,
    dataset: Dataset | str,
    portal_url: str = "https://portal.sqd.dev",
    stream_type: Literal["finalized", "realtime"] = "realtime",
) -> EVMQuery | SolanaQuery:
    """
    Create a query builder for the specified dataset.

    This is the main entry point for building SQD queries.

    Args:
        dataset: Dataset to query (e.g., 'ethereum-mainnet', 'arbitrum-one', 'solana-mainnet')
        portal_url: SQD portal URL
        stream_type: Type of stream ('finalized' or 'realtime')

    Returns:
        EVMQuery for EVM chains or SolanaQuery for Solana

    Example:
        sqd = SQD(dataset='ethereum-mainnet')
        query = sqd.get_transactions(from_block=17_000_000, address='0x...')
        async for tx in query:
            print(tx)
    """
    dataset_str = str(_normalize_dataset(dataset))

    if _is_solana(dataset_str):
        return SolanaQuery.create(
            dataset=dataset_str,
            portal_url=portal_url,
            stream_type=stream_type,
        )
    else:
        return EVMQuery.create(
            dataset=dataset_str,
            portal_url=portal_url,
            stream_type=stream_type,
        )


def _is_solana(dataset: str) -> bool:
    """Check if the dataset is a Solana dataset."""
    return "solana" in dataset.lower()


__all__ = ["SQD"]
