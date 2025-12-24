from __future__ import annotations

import asyncio

from subsquid_pipes.portal_client import split_lines


async def _to_chunks(parts):
    for part in parts:
        yield part.encode('utf-8')


async def _read_lines(parts):
    results = []
    async for lines in split_lines(_to_chunks(parts)):
        results.extend(lines)
    return results


def test_split_lines_handles_multiple_lines_in_chunk():
    assert asyncio.run(_read_lines(['a\nb'])) == ['a', 'b']


def test_split_lines_handles_missing_newline():
    assert asyncio.run(_read_lines(['ab'])) == ['ab']


def test_split_lines_handles_cross_chunk_boundaries():
    assert asyncio.run(_read_lines(['a', '\n', 'b', '\n'])) == ['a', 'b']


def test_split_lines_drops_empty_lines():
    assert asyncio.run(_read_lines(['a\n\n', 'b\n'])) == ['a', 'b']
    assert asyncio.run(_read_lines(['\n\na\n\nb\n\n\n'])) == ['a', 'b']


def test_split_lines_emits_final_partial_line():
    assert asyncio.run(_read_lines(['a\nb', 'c'])) == ['a', 'bc']
