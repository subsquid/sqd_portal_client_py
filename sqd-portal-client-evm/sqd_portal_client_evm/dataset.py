from enum import StrEnum


class EvmDataset(StrEnum):
    ETHEREUM = "ethereum-mainnet"
    BINANCE = "binance-mainnet"


class SolanaDataset(StrEnum):
    SOLANA = "solana-mainnet"
    
Dataset = EvmDataset | SolanaDataset