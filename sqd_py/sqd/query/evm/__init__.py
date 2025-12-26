"""
EVM Query Package

This package provides EVM-specific query functionality for the SQD Portal Client.
"""

from .decode import DecodedTransfer, decode_transfer, format_token_amount
from .fields import BlockField, LogField, StateDiffField, TraceField, TransactionField
from .requests import (
    LogsRequest,
    StateDiffsRequest,
    TracesRequest,
    TransactionsRequest,
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
    # Decode helpers
    "decode_transfer",
    "format_token_amount",
    "DecodedTransfer",
]

