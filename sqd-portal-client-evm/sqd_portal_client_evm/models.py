from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class DatasetMetadata:
    """Dataset metadata response from /metadata endpoint."""

    dataset: str
    aliases: List[str]
    real_time: bool
    start_block: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetMetadata":
        return cls(
            dataset=data["dataset"],
            aliases=data["aliases"],
            real_time=data["real_time"],
            start_block=data["start_block"],
        )


@dataclass
class BlockHead:
    """Block head response from /head and /finalized-head endpoints."""

    number: Optional[int]
    hash: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockHead":
        return cls(number=data.get("number"), hash=data.get("hash"))


@dataclass
class ConflictResponse:
    """Conflict response from API when there's a parent block hash mismatch."""

    previousBlocks: List[Dict[str, Union[int, str]]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConflictResponse":
        return cls(previousBlocks=data["previousBlocks"])


@dataclass
class StreamResponse:
    """Response from streaming endpoints with metadata."""

    data: List[Dict[str, Any]]
    finalized_head_number: Optional[int] = None
    finalized_head_hash: Optional[str] = None

    @classmethod
    def from_response(
        cls, response_data: List[Dict[str, Any]], response_headers: Dict[str, str]
    ) -> "StreamResponse":
        return cls(
            data=response_data,
            finalized_head_number=int(
                response_headers.get("X-Sqd-Finalized-Head-Number", 0)
            )
            if response_headers.get("X-Sqd-Finalized-Head-Number")
            else None,
            finalized_head_hash=response_headers.get("X-Sqd-Finalized-Head-Hash"),
        )
