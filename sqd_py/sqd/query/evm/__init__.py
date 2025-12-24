"""
EVM Query Package

This package provides EVM-specific query functionality for the SQD Portal Client.
"""

from .fields import BlockField, TransactionField, LogField, TraceField, StateDiffField
from .requests import (
    TransactionsRequest,
    LogsRequest,
    StateDiffsRequest,
    TracesRequest,
)

__all__ = [
    # Request classes
    "TransactionsRequest",
    "LogsRequest",
    "StateDiffsRequest",
    "TracesRequest",
    # Field enums
    "BlockField",
    "TransactionField",
    "LogField",
    "TraceField",
    "StateDiffField",
]
