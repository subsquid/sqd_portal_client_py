# sqd_py

A lightweight Python client for querying blockchain data from the [SQD Network](https://sqd.dev). Supports EVM chains (Ethereum, Binance, etc.) and Solana.

## Features

- 🚀 **Async-first** - Built on `aiohttp` for efficient concurrent data fetching
- 🔗 **Multi-chain support** - Query Ethereum, Binance, Solana and more
- 📦 **Type-safe** - Full type hints with Pydantic models
- 🎯 **Flexible queries** - Filter transactions, logs, and more with a fluent API

## Installation

```bash
pip install sqd_py
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add sqd_py
```

## Quick Start

```python
import asyncio
from sqd import SQD, Dataset, EvmFields

async def main():
    # Create client for Ethereum mainnet
    sqd = SQD(dataset=Dataset.ETHEREUM, portal_url="https://portal.sqd.dev")
    
    # Query transactions
    query = sqd.get_transactions(
        address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        from_block=17_000_000,
        to_block=17_000_010,
        include_fields=[
            EvmFields.TransactionField.hash,
            EvmFields.TransactionField.from_,
            EvmFields.TransactionField.gasUsed,
        ],
    )
    
    # Stream results asynchronously
    async for transaction in query:
        print(transaction)

if __name__ == "__main__":
    asyncio.run(main())
```

### Querying Logs

```python
from sqd import SQD, Dataset, EvmFields

sqd = SQD(dataset=Dataset.ETHEREUM)

# Query ERC-20 Transfer events
query = sqd.get_logs(
    address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
    from_block=17_000_000,
    to_block=17_000_100,
    topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer
    include_fields=[
        EvmFields.LogField.logIndex,
        EvmFields.LogField.transactionHash,
    ],
)
```

### Chaining Queries

```python
# Build complex queries by chaining
query = sqd.get_transactions(
    address="0x...",
    from_block=17_000_000,
    to_block=17_000_010,
).get_logs(
    address="0x...",
    topic0="0x...",
)

async for data in query:
    print(data)
```

### Solana Support

```python
from sqd import SQD, Dataset, SolanaFields

sqd = SQD(dataset=Dataset.SOLANA)
# Query Solana data similarly...
```

## Supported Datasets

| Chain | Dataset Enum |
|-------|--------------|
| Ethereum | `Dataset.ETHEREUM` |
| Binance Smart Chain | `Dataset.BINANCE` |
| Solana | `Dataset.SOLANA` |

You can also use string identifiers like `"ethereum-mainnet"`, `"binance-mainnet"`, etc.

## API Reference

### `SQD(dataset, portal_url, stream_type)`

Main entry point for creating queries.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset` | `Dataset \| str` | *required* | The blockchain dataset to query |
| `portal_url` | `str` | `"https://portal.sqd.dev"` | SQD portal URL |
| `stream_type` | `"finalized" \| "realtime"` | `"realtime"` | Data stream type |

### Query Methods

- `get_transactions(address, from_block, to_block, include_fields)` - Query transactions
- `get_logs(address, from_block, to_block, topic0, include_fields)` - Query event logs

## Requirements

- Python 3.10+
- aiohttp >= 3.9.0

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [SQD Network](https://sqd.dev)
- [Documentation](https://docs.sqd.dev)
- [GitHub Repository](https://github.com/subsquid/sqd-portal-client-py)
