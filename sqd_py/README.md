# sqd_py

Python client for querying blockchain data from [SQD Network](https://sqd.dev).

## Installation

```bash
pip install sqd_py
```

## Quick Start

```python
import asyncio
from sqd import SQD, Dataset, EvmFields

async def main():
    sqd = SQD(dataset=Dataset.ETHEREUM)
    
    query = sqd.get_transactions(
        from_block=17_000_000,
        to_block=17_000_010,
        address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    )
    
    async for block in query:
        for tx in block.get("transactions", []):
            print(tx["hash"])

asyncio.run(main())
```

## Usage

### Querying Logs

```python
query = sqd.get_logs(
    from_block=17_000_000,
    to_block=17_000_100,
    address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
)

async for block in query:
    for log in block.get("logs", []):
        print(log)
```

### ERC-20 Transfers

```python
query = sqd.get_transfers(
    from_block=17_000_000,
    to_block=17_100_000,
    contract_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
)

async for block in query.with_progress(shards=15):
    for log in block.get("logs", []):
        print(log)
```

### Selecting Fields

```python
query = sqd.get_transactions(
    from_block=17_000_000,
    to_block=17_000_010,
    include_fields=[
        EvmFields.TransactionField.hash,
        EvmFields.TransactionField.from_,
        EvmFields.TransactionField.gasUsed,
    ],
)
```

### Chaining Queries

```python
query = sqd.get_transactions(
    from_block=17_000_000,
    to_block=17_000_010,
    address="0x...",
).get_logs(
    address="0x...",
    topic0="0x...",
)

async for block in query:
    # block contains both transactions and logs
    pass
```

### Progress Bar

```python
async for block in query.with_progress(shards=15):
    pass
```

The `shards` parameter controls parallel fetching for historical data.

## Supported Datasets

| Chain | Dataset |
|-------|---------|
| Ethereum | `Dataset.ETHEREUM` or `"ethereum-mainnet"` |
| Binance Smart Chain | `Dataset.BINANCE` or `"binance-mainnet"` |
| Solana | `Dataset.SOLANA` or `"solana-mainnet"` |

## API

### SQD

```python
SQD(
    dataset: Dataset | str,
    portal_url: str = "https://portal.sqd.dev",
    stream_type: Literal["finalized", "realtime"] = "realtime",
)
```

### Query Methods

**EVM:**
- `get_blocks(from_block, to_block, ...)`
- `get_transactions(from_block, address, to_block, ...)`
- `get_logs(from_block, address, topic0, to_block, ...)`
- `get_transfers(from_block, contract_address, ...)`
- `get_traces(from_block, to_block, ...)`
- `get_state_diffs(from_block, to_block, ...)`

### Iteration

- `async for block in query` — default iteration
- `query.with_progress(shards=N)` — with progress bar and parallel fetching

## Requirements

- Python 3.10+
- aiohttp >= 3.9.0
- tqdm >= 4.67.1
- ujson >= 5.11.0

## License

MIT
