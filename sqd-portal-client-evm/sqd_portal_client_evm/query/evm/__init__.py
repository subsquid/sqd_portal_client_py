"""
EVM Query Package

This package provides EVM-specific query functionality for the SQD Portal Client.
"""

from .query_builder import EVMQueryBuilder
from .requests import (
    TransactionsRequest,
    LogsRequest,
    StateDiffsRequest,
    TracesRequest,
    _validate_address,
    _request_to_sqd_string,
)

__all__ = [
    "EVMQueryBuilder",
    "TransactionsRequest",
    "LogsRequest",
    "StateDiffsRequest",
    "TracesRequest",
    "_validate_address",
    "_request_to_sqd_string",
]
