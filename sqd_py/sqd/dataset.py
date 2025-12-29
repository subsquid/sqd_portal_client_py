from typing import Literal, TypeAlias

from sqd._compat import StrEnum


class Dataset(StrEnum):
    ETHEREUM = "ethereum-mainnet"
    BINANCE = "binance-mainnet"
    SOLANA = "solana-mainnet"


EvmDataset: TypeAlias = Literal[
    "ethereum-mainnet",
    "binance-mainnet",
]

SolanaDataset: TypeAlias = Literal[
    "solana-mainnet",
]
