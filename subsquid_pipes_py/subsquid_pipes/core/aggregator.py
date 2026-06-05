from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, TypeVar

from .transformer import create_transformer

T = TypeVar('T')
V = TypeVar('V')


@dataclass
class Aggregator(Generic[T, V]):
    getter: Callable[[T], V]
    update_final_value: Callable[[V, Optional[V]], V]
    calculate_value: Callable[[List[V], Optional[V]], V]
    finalized: Optional[V] = None
    unfinalized: List[V] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.unfinalized is None:
            self.unfinalized = []

    def aggregate(self, item: T, finalized: bool) -> None:
        value = self.getter(item)
        if finalized:
            self.finalized = self.update_final_value(value, self.finalized)
        else:
            self.unfinalized.append(value)

    def calculate(self) -> V:
        return self.calculate_value(self.unfinalized or [], self.finalized)

    def serialize(self) -> str:
        return json.dumps({'finalized': self.finalized, 'unfinalized': self.unfinalized})

    def reset_from_state(self, state: str | None) -> 'Aggregator[T, V]':
        if not state:
            self.finalized = None
            self.unfinalized = []
            return self
        data = json.loads(state)
        self.finalized = data.get('finalized')
        self.unfinalized = data.get('unfinalized') or []
        return self

    def clone(self) -> 'Aggregator[T, V]':
        return Aggregator(
            getter=self.getter,
            update_final_value=self.update_final_value,
            calculate_value=self.calculate_value,
        )


@dataclass
class AggregatorStore:
    path: str
    conn: sqlite3.Connection | None = None

    def init(self) -> None:
        self.conn = sqlite3.connect(self.path)
        self.conn.execute('PRAGMA journal_mode=WAL;')
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS aggregators (id TEXT, key TEXT, value TEXT, PRIMARY KEY(id, key))'
        )
        self.conn.commit()

    def load(self, aggregate_id: str, key: str) -> Optional[str]:
        assert self.conn is not None
        cursor = self.conn.execute('SELECT value FROM aggregators WHERE id = ? AND key = ?', (aggregate_id, key))
        row = cursor.fetchone()
        return row[0] if row else None

    def persist(self, rows: Iterable[tuple[str, str, str]]) -> None:
        assert self.conn is not None
        self.conn.executemany('INSERT OR REPLACE INTO aggregators(id, key, value) VALUES (?, ?, ?)', rows)
        self.conn.commit()


def sum_value(getter: Callable[[T], float]) -> Aggregator[T, float]:
    return Aggregator(
        getter=getter,
        update_final_value=lambda value, prev=None: (prev or 0.0) + value,
        calculate_value=lambda unfinalized, finalized=None: (finalized or 0.0)
        + sum(unfinalized),
    )


def min_value(getter: Callable[[T], float]) -> Aggregator[T, float]:
    return Aggregator(
        getter=getter,
        update_final_value=lambda value, prev=None: min(value, prev if prev is not None else value),
        calculate_value=lambda unfinalized, finalized=None: min(
            [finalized if finalized is not None else float('inf')] + (unfinalized or [float('inf')])
        ),
    )


def max_value(getter: Callable[[T], float]) -> Aggregator[T, float]:
    return Aggregator(
        getter=getter,
        update_final_value=lambda value, prev=None: max(value, prev if prev is not None else value),
        calculate_value=lambda unfinalized, finalized=None: max(
            [finalized if finalized is not None else float('-inf')] + (unfinalized or [float('-inf')])
        ),
    )


def first(getter: Callable[[T], V]) -> Aggregator[T, Optional[V]]:
    return Aggregator(
        getter=getter,
        update_final_value=lambda value, prev=None: prev if prev is not None else value,
        calculate_value=lambda unfinalized, finalized=None: finalized
        if finalized is not None
        else (unfinalized[0] if unfinalized else None),
    )


def last(getter: Callable[[T], V]) -> Aggregator[T, Optional[V]]:
    return Aggregator(
        getter=getter,
        update_final_value=lambda value, _: value,
        calculate_value=lambda unfinalized, finalized=None: (unfinalized[-1] if unfinalized else finalized),
    )


def create_aggregator(
    *,
    db_path: str,
    aggregate: Dict[str, Aggregator[T, Any]],
    group_by: Callable[[T], str],
    window: Callable[[T], Any] | None = None,
):
    store = AggregatorStore(db_path)

    async def _start(ctx):
        store.init()

    def aggregate_id(item: T) -> str:
        group = group_by(item)
        win = window(item).isoformat() if window else 'all'
        return f"{group}:{win}"

    async def _transform(items: list[T], ctx):  # type: ignore[override]
        rows: Dict[str, Dict[str, Aggregator[T, Any]]] = {}
        for item in items:
            agg_id = aggregate_id(item)
            rows.setdefault(agg_id, {})
            for key, agg in aggregate.items():
                if key not in rows[agg_id]:
                    rows[agg_id][key] = agg.clone()
                    rows[agg_id][key].reset_from_state(store.load(agg_id, key))
                finalized = (
                    ctx.head.finalized is None or item.get('blockNumber', 0) <= ctx.head.finalized.number
                )
                rows[agg_id][key].aggregate(item, finalized)
        result = {}
        updates = []
        for agg_id, aggs in rows.items():
            result[agg_id] = {'id': agg_id}
            for key, agg in aggs.items():
                result[agg_id][key] = agg.calculate()
                updates.append((agg_id, key, agg.serialize()))
        store.persist(updates)
        return result

    return create_transformer({
        'profiler': {'id': 'aggregator'},
        'start': _start,
        'transform': _transform,
    })


__all__ = [
    'Aggregator',
    'AggregatorStore',
    'create_aggregator',
    'sum_value',
    'min_value',
    'max_value',
    'first',
    'last',
]
