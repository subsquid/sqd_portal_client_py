from enum import StrEnum
from typing import Literal, TypeAlias


class Dataset(StrEnum):
    ETHEREUM = "ethereum-mainnet"
    BINANCE  = "binance-mainnet"
    SOLANA   = "solana-mainnet"


EvmDataset = Literal[
    Dataset.ETHEREUM,
    Dataset.BINANCE,
]

SolanaDataset: TypeAlias = Literal[
    Dataset.SOLANA,
]
