# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-01-08

### Added

- Added `from_block` and `to_block` parameters to all EVM request types (`TransactionsRequest`, `LogsRequest`, `TracesRequest`, `StateDiffsRequest`) for per-request block range filtering
- Updated `add_transactions_request()` and `add_state_diffs_request()` methods to accept block range parameters

## [0.1.2] - 2026-01-06

### Changed

- Added default `None` values to all optional parameters in `EVMQuery` request builder methods (`add_transactions_request`, `add_logs_request`) to make them easier to call directly

## [0.1.1] - 2026-01-05

### Changed

- Improved README documentation

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

[0.1.3]: https://github.com/subsquid/sqd-portal-client-py/releases/tag/v0.1.3
[0.1.2]: https://github.com/subsquid/sqd-portal-client-py/releases/tag/v0.1.2
[0.1.1]: https://github.com/subsquid/sqd-portal-client-py/releases/tag/v0.1.1
[0.1.0]: https://github.com/subsquid/sqd-portal-client-py/releases/tag/v0.1.0
