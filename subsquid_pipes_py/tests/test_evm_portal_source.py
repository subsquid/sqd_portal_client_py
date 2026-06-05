from __future__ import annotations

import asyncio

from subsquid_pipes.evm import EvmQueryBuilder, evm_portal_source

from .helpers.mock_portal import close_mock_portal, create_mock_portal


def test_evm_portal_source_normalizes_optional_fields() -> None:
    async def run() -> None:
        mock_portal = create_mock_portal(
            [
                {
                    'statusCode': 200,
                    'data': [
                        {
                            'header': {'number': 1, 'hash': '0x123', 'timestamp': 1000},
                            'logs': [],
                            'traces': [],
                            'transactions': [],
                            'stateDiffs': [],
                        },
                    ],
                }
            ]
        )
        try:
            fields = {
                'log': {'address': True, 'data': True, 'topics': True},
                'block': {'number': True, 'hash': True, 'timestamp': True},
                'transaction': {'from': True, 'to': True, 'hash': True},
                'stateDiff': {'address': True, 'key': True},
                'trace': {'error': True},
            }
            query = EvmQueryBuilder().add_fields(fields).add_range({'from': 0, 'to': 1})
            source = evm_portal_source(
                portal=mock_portal.client,
                query=query,
            )
            async for batch in source:
                block = batch.data['blocks'][0]
                assert isinstance(block.get('logs'), list)
                assert isinstance(block.get('transactions'), list)
                assert isinstance(block.get('traces'), list)
                assert isinstance(block.get('stateDiffs'), list)
                break
        finally:
            await close_mock_portal(mock_portal)

    asyncio.run(run())
