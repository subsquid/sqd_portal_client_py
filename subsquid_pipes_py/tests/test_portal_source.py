from __future__ import annotations

import asyncio

import pytest

import httpx
from subsquid_pipes.evm import evm_portal_source
from subsquid_pipes.portal_client import ForkException

from .helpers.mock_portal import close_mock_portal, create_finalized_mock_portal, create_mock_portal
from .helpers.runtime import block_transformer, read_all


def test_portal_source_streams_all_blocks() -> None:
    async def run() -> None:
        mock_portal = create_mock_portal(
            [
                {
                    'statusCode': 200,
                    'data': [
                        {'header': {'number': 1, 'hash': '0x123'}},
                        {'header': {'number': 2, 'hash': '0x456'}},
                    ],
                }
            ]
        )
        try:
            stream = evm_portal_source(portal=mock_portal.client, query={'from': 0, 'to': 2}).pipe(block_transformer())
            result = await read_all(stream)
            assert result == [
                {'number': 1, 'hash': '0x123'},
                {'number': 2, 'hash': '0x456'},
            ]
        finally:
            await close_mock_portal(mock_portal)

    asyncio.run(run())


def test_portal_source_retries_by_default() -> None:
    async def run() -> None:
        mock_portal = create_mock_portal(
            [
                {'statusCode': 200, 'data': [{'header': {'number': 1, 'hash': '0x123'}}]},
                *[{'statusCode': 503} for _ in range(10)],
                {'statusCode': 200, 'data': [{'header': {'number': 2, 'hash': '0x456'}}]},
            ]
        )
        try:
            client = mock_portal.make_client(retry_schedule=(0.0,))
            stream = evm_portal_source(portal=client, query={'from': 0, 'to': 2}).pipe(block_transformer())
            result = await read_all(stream)
            assert result == [
                {'number': 1, 'hash': '0x123'},
                {'number': 2, 'hash': '0x456'},
            ]
        finally:
            await close_mock_portal(mock_portal)

    asyncio.run(run())


def test_portal_source_raises_after_max_retries() -> None:
    async def run() -> None:
        mock_portal = create_mock_portal(
            [
                {'statusCode': 200, 'data': [{'header': {'number': 1, 'hash': '0x123'}}]},
                *[{'statusCode': 503} for _ in range(2)],
            ]
        )
        try:
            client = mock_portal.make_client(retry_attempts=1, retry_schedule=(0.0,))
            stream = evm_portal_source(portal=client, query={'from': 0, 'to': 2}).pipe(block_transformer())
            with pytest.raises(httpx.HTTPStatusError):
                await read_all(stream)
        finally:
            await close_mock_portal(mock_portal)

    asyncio.run(run())


def test_portal_source_propagates_fork_exception() -> None:
    async def run() -> None:
        mock_portal = create_mock_portal(
            [
                {
                    'statusCode': 200,
                    'data': [
                        {
                            'header': {
                                'number': 100_000_000,
                                'hash': '0x100000000',
                            }
                        }
                    ],
                },
                {
                    'statusCode': 409,
                    'data': {
                        'previousBlocks': [
                            {'number': 99_999_999, 'hash': '0x99999999__1'},
                            {'number': 100_000_000, 'hash': '0x100000000__1'},
                        ]
                    },
                    'validateRequest': lambda req: _assert_fork_request(req),
                },
            ]
        )
        try:
            client = mock_portal.make_client(retry_attempts=0)
            stream = evm_portal_source(portal=client, query={'from': 0, 'to': 100_000_001}).pipe(block_transformer())
            with pytest.raises(ForkException):
                await read_all(stream)
        finally:
            await close_mock_portal(mock_portal)

    asyncio.run(run())


def test_portal_source_finalized_stream() -> None:
    async def run() -> None:
        mock_portal = create_finalized_mock_portal(
            [
                {
                    'statusCode': 200,
                    'data': [
                        {'header': {'number': 1, 'hash': '0x123'}},
                        {'header': {'number': 2, 'hash': '0x456'}},
                    ],
                }
            ]
        )
        try:
            client = mock_portal.client
            stream = evm_portal_source(portal=client, query={'from': 0, 'to': 2}).pipe(block_transformer())
            result = await read_all(stream)
            assert [b['number'] for b in result] == [1, 2]
        finally:
            await close_mock_portal(mock_portal)

    asyncio.run(run())


def _assert_fork_request(request: dict) -> None:
    assert request['fromBlock'] == 100_000_001
    assert request['parentBlockHash'] == '0x100000000'
