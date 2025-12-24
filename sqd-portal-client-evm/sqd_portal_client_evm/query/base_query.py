from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, FrozenSet, Literal, Mapping, NamedTuple, Optional, Sequence, TypeVar, cast


class FieldValue(NamedTuple):
    """A field value containing category and field name."""
    category: str
    field_name: str


def _freeze_field_map(
    default_fields: Dict[str, Sequence[Enum]],
) -> dict[str, FrozenSet[str]]:
    return {
        category: frozenset(enum_value.value for enum_value in enum_values)
        for category, enum_values in default_fields.items()
    }


def _freeze_field_values(
    raw_fields: Dict[str, Sequence[str]],
) -> Mapping[str, FrozenSet[str]]:
    return {category: frozenset(values) for category, values in raw_fields.items()}


Q = TypeVar("Q", bound="BaseSQDQuery")


@dataclass(frozen=True, kw_only=True)
class BaseSQDQuery:
    """Immutable base query representation shared by chain-specific builders."""

    # Connection config (previously on factory)
    dataset: str
    portal_url: str
    stream_type: Literal["finalized", "realtime"]
    
    # Query state
    from_block: int = 0
    to_block: Optional[int] = None
    query_type: str = ""
    _fields: Mapping[str, FrozenSet[str]] = field(default_factory=dict)
    
    @staticmethod
    def _default_field_map():
        raise NotImplementedError
    
    # ------------------------------------------------------------------ #
    # Field helpers
    # ------------------------------------------------------------------ #
    def add_fields(
        self: Q, include_fields: Optional[Sequence[Enum]]
    ) -> Q:
        """Add specific fields to include in the query response.
        
        Args:
            include_fields: Sequence of field enums (e.g., TransactionField, LogField)
                           Each enum value should be a FieldValue(category, field_name).
        """
        if not include_fields:
            return self

        mutable: Dict[str, set[str]] = {
            category: set(values) for category, values in self._fields.items()
        }
        for f in include_fields:
            # f.value is a FieldValue(category, field_name)
            mutable.setdefault(f.value.category, set()).add(f.value.field_name)

        return self._copy(_fields=_freeze_field_values(mutable))

    def _update_block_range(
        self: Q, from_block: int, to_block: Optional[int]
    ) -> Q:
        new_from = min(self.from_block, from_block) if self.from_block >= 0 else from_block
        new_to = self.to_block
        if to_block is not None:
            if new_to is None:
                new_to = to_block
            else:
                new_to = max(new_to, to_block)

        if new_from == self.from_block and new_to == self.to_block:
            return self

        return cast(Q, self._copy(from_block=new_from, to_block=new_to))

    # ------------------------------------------------------------------ #
    # Payload helpers
    # ------------------------------------------------------------------ #
    def _base_payload(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "type": self.query_type,
            "fromBlock": self.from_block,
        }
        if self.to_block is not None:
            payload["toBlock"] = self.to_block
        return payload

    def _chain_payload(self) -> Dict[str, object]:
        raise NotImplementedError

    def to_payload(self) -> Dict[str, object]:
        payload = self._base_payload()
        payload.update(self._chain_payload())

        fields_payload = {
            category: {field_name: True for field_name in sorted(field_names)}
            for category, field_names in self._fields.items()
            if field_names
        }
        if fields_payload:
            payload["fields"] = fields_payload

        return payload

    def to_sqd_string(self) -> str:
        return json.dumps(self.to_payload(), separators=(",", ":"))

    def endpoint(self) -> str:
        if self.stream_type == 'realtime':
            _endpoint = 'stream'
        else:
            _endpoint = f'{self.stream_type}-stream'
        return (
            f"{self.portal_url}/datasets/"
            f"{self.dataset}/{_endpoint}"
        )

    # ------------------------------------------------------------------ #
    # Async iterator factory
    # ------------------------------------------------------------------ #
    def __aiter__(self):
        from .cursor import QueryCursor

        return QueryCursor(self)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _copy(self, **changes: object) -> BaseSQDQuery:
        return replace(self, **changes)


__all__ = ["BaseSQDQuery", "FieldValue", "_freeze_field_map"]

