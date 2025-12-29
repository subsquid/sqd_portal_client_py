from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from sqd._compat import StrEnum

if TYPE_CHECKING:
    from sqd.query.cursor import QueryCursor


def _freeze_field_values(
    raw_fields: dict[str, Sequence[str]],
) -> Mapping[str, frozenset[str]]:
    return {category: frozenset(values) for category, values in raw_fields.items()}


Q = TypeVar("Q", bound="BaseSQDQuery")


@dataclass(frozen=True, kw_only=True)
class BaseSQDQuery:
    """Immutable base query representation shared by chain-specific builders."""

    # Connection config
    dataset: str
    portal_url: str
    stream_type: Literal["finalized", "realtime"]

    # Query state
    from_block: int = 0
    to_block: int | None = None
    query_type: str = ""
    _fields: Mapping[str, frozenset[str]] = field(default_factory=dict)

    # API options (per OpenAPI spec)
    include_all_blocks: bool = False
    parent_block_hash: str | None = None

    @staticmethod
    def _default_field_map() -> dict[str, list[StrEnum]]:
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Field helpers
    # ------------------------------------------------------------------ #
    def add_fields(self: Q, category: str, fields: Sequence[StrEnum] | None) -> Q:
        """Add specific fields to include in the query response.

        Args:
            category: The field category (e.g., 'transaction', 'log', 'block')
            fields: Sequence of field enums (e.g., TransactionField.hash)
        """

        if not fields:
            return self

        mutable: dict[str, set[str]] = {
            cat: set(values) for cat, values in self._fields.items()
        }
        for f in fields:
            mutable.setdefault(category, set()).add(str(f.value))

        return self._copy(_fields=_freeze_field_values(mutable))

    def _update_block_range(self: Q, from_block: int, to_block: int | None) -> Q:
        new_from = (
            min(self.from_block, from_block) if self.from_block >= 0 else from_block
        )
        new_to = self.to_block
        if to_block is not None:
            if new_to is None:
                new_to = to_block
            else:
                new_to = max(new_to, to_block)

        if new_from == self.from_block and new_to == self.to_block:
            return self

        return self._copy(from_block=new_from, to_block=new_to)

    # ------------------------------------------------------------------ #
    # Payload helpers
    # ------------------------------------------------------------------ #
    def _base_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.query_type,
            "fromBlock": self.from_block,
        }
        if self.to_block is not None:
            payload["toBlock"] = self.to_block
        if self.include_all_blocks:
            payload["includeAllBlocks"] = True
        if self.parent_block_hash:
            payload["parentBlockHash"] = self.parent_block_hash
        return payload

    def _chain_payload(self) -> dict[str, object]:
        raise NotImplementedError

    def to_payload(self) -> dict[str, object]:
        payload = self._base_payload()
        payload.update(self._chain_payload())

        # Start with default fields (always needed for pagination etc)
        default_fields = self._default_field_map()
        fields_dict: dict[str, set[str]] = {
            category: set(
                str(f.value) if hasattr(f, "value") else str(f) for f in fields
            )
            for category, fields in default_fields.items()
        }

        # Merge in user-specified fields
        for category, field_names in self._fields.items():
            if category not in fields_dict:
                fields_dict[category] = set()
            fields_dict[category].update(str(f) for f in field_names)

        # Convert to payload format
        fields_payload = {
            category: {field_name: True for field_name in sorted(field_names)}
            for category, field_names in fields_dict.items()
            if field_names
        }
        if fields_payload:
            payload["fields"] = fields_payload

        return payload

    def to_sqd_string(self) -> str:
        return json.dumps(self.to_payload(), separators=(",", ":"))

    def endpoint(self) -> str:
        if self.stream_type == "realtime":
            _endpoint = "stream"
        else:
            _endpoint = f"{self.stream_type}-stream"
        return f"{self.portal_url}/datasets/" f"{self.dataset}/{_endpoint}"

    # ------------------------------------------------------------------ #
    # Async iterator factory
    # ------------------------------------------------------------------ #
    def __aiter__(self) -> "QueryCursor":
        from sqd.query.cursor import QueryCursor

        return QueryCursor(self, shards=15)

    def with_progress(self, *, shards: int = 15) -> "QueryCursor":
        """Return an async iterator with a progress bar.

        Args:
            shards: Number of parallel workers to use for fetching.
                    Requires to_block to be set for parallel mode.

        Example:
            async for block in query.with_progress():
                process(block)
        """
        from sqd.query.cursor import QueryCursor

        return QueryCursor(self, show_progress=True, shards=shards)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def copy(self: Q, **changes: Any) -> Q:
        """Create a copy with the given changes. Preserves the concrete type."""
        return replace(self, **changes)  # type: ignore[return-value]

    def _copy(self: Q, **changes: Any) -> Q:
        """Internal copy method that preserves the concrete type."""
        return replace(self, **changes)  # type: ignore[return-value]


__all__ = ["BaseSQDQuery"]
