from enum import StrEnum


class EvmDataset(StrEnum):
    ETHEREUM = "ethereum-mainnet"
    BINANCE = "binance-mainnet"


class SolanaDataset(StrEnum):
    SOLANA = "solana-mainnet"

class Dataset:
    EVM = EvmDataset
    SOLANA = SolanaDataset

