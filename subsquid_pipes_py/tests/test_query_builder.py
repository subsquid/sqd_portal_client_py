from __future__ import annotations

import asyncio

from subsquid_pipes.core.query_builder import Range
from subsquid_pipes.evm import EvmQueryBuilder


class _Portal:
    async def get_head(self):
        return {'number': 42, 'hash': '0xabc'}


def test_calculate_ranges_resolves_latest_keyword():
    builder = EvmQueryBuilder()
    builder.add_log(range={'from': 'latest', 'to': 50}, request={'address': ['0x1']})

    ranges = asyncio.run(builder.calculate_ranges(portal=_Portal(), bound=None))
    assert ranges['bounded'][0].range.from_block == 42
    assert ranges['bounded'][0].range.to_block == 50


def test_calculate_ranges_adds_default_range_when_empty():
    builder = EvmQueryBuilder()
    ranges = asyncio.run(builder.calculate_ranges(portal=_Portal(), bound=None))
    assert ranges['bounded'][0].range.from_block == 0
    assert ranges['bounded'][0].range.to_block is None


def test_latest_uses_bound_when_provided():
    builder = EvmQueryBuilder()
    builder.add_range({'from': 'latest'})
    ranges = asyncio.run(builder.calculate_ranges(portal=_Portal(), bound=Range(from_block=10, to_block=None)))
    assert ranges['bounded'][0].range.from_block == 10


def test_include_all_blocks_sets_flag():
    builder = EvmQueryBuilder()
    builder.include_all_blocks({'from': 0, 'to': 10})
    result = asyncio.run(builder.calculate_ranges(portal=_Portal(), bound=None))
    assert result['bounded'][0].request['includeAllBlocks'] is True
