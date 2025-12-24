# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-24

### Added

- Initial release
- `SQD` factory function for creating query builders
- `EVMQuery` for querying EVM chains (Ethereum, Binance)
- `SolanaQuery` for querying Solana blockchain
- Transaction and log querying with field selection
- Async streaming iteration over query results
- Support for `Dataset` enum with common chains
- `EvmFields` and `SolanaFields` for type-safe field selection
- Full type hints support (PEP 561 compatible)

[0.1.0]: https://github.com/subsquid/sqd-portal-client-py/releases/tag/v0.1.0
