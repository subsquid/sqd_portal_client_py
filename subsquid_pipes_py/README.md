# Subsquid Pipes (Python)

Experimental Python rewrite of the `@subsquid/pipes` runtime SDK. The project mirrors the TypeScript API surface (portal sources, transformers, targets, metrics, and EVM helpers) while providing an asyncio-first implementation.

## Features
- Async portal streaming client with fork detection
- Composable transformer pipeline with lifecycle hooks and profiling spans
- Built-in portal progress tracker, metrics hooks, and persistent aggregators
- EVM query builder and portal convenience wrappers

## Installation
```bash
pip install -e .
```

## Quick start
```python
from subsquid_pipes.evm import evm_portal_source, common_abis
from subsquid_pipes.core import create_transformer

source = evm_portal_source({
    "portal": "https://portal.sqd.dev/datasets/ethereum-mainnet",
    "query": {"range": {"from": 18_000_000}},
})

pipeline = source.pipe(
    create_transformer({
        "profiler": {"id": "print-transfers"},
        "transform": lambda batch, ctx: ctx.logger.info(
            "batch",
            blocks=len(batch["blocks"]),
            finalized=ctx.head.finalized.number if ctx.head.finalized else None,
        )
    })
)
```

## Status
The package is under heavy development and not production-ready yet. See `docs/ts_runtime_surface.md` for the TypeScript parity contract.
