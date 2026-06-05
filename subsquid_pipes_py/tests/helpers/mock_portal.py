from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

import httpx

from subsquid_pipes.portal_client import PortalClient, PortalClientOptions


class _PortalDispatcher:
    def __init__(self, responses: List[dict], finalized: bool) -> None:
        self.responses = responses
        self.finalized = finalized
        self.request_count = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == '/metadata':
            return httpx.Response(200, json={'dataset': 'mock-dataset', 'real_time': True})

        stream_path = '/finalized-stream' if self.finalized else '/stream'
        if request.url.path != stream_path:
            return httpx.Response(404)

        if self.request_count >= len(self.responses):
            self.request_count += 1
            return httpx.Response(500)

        mock_resp = self.responses[self.request_count]
        self.request_count += 1

        validator: Optional[Callable[[Any], Any]] = mock_resp.get('validateRequest')  # type: ignore[assignment]
        if validator is not None:
            payload = json.loads(request.content.decode('utf-8') or 'null')
            validator(payload)

        status_code = mock_resp['statusCode']
        if status_code == 200:
            headers = {'Content-Type': 'application/jsonl'}
            finalized_head = mock_resp.get('finalizedHead')
            if finalized_head:
                headers['X-Sqd-Finalized-Head-Number'] = str(finalized_head['number'])
                headers['X-Sqd-Finalized-Head-Hash'] = finalized_head['hash']
            body = ''.join(json.dumps(item) + '\n' for item in mock_resp['data']).encode('utf-8')
            return httpx.Response(200, headers=headers, stream=httpx.ByteStream(body))
        if status_code == 409:
            return httpx.Response(409, json=mock_resp['data'])
        return httpx.Response(status_code)


@dataclass
class MockPortal:
    responses: List[dict]
    finalized: bool
    dispatcher: _PortalDispatcher = field(init=False)
    transport: httpx.MockTransport = field(init=False)
    url: str = 'https://mock-portal.local'
    _clients: List[httpx.AsyncClient] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.dispatcher = _PortalDispatcher(self.responses, self.finalized)
        self.transport = httpx.MockTransport(self.dispatcher)
        self.client = self.make_client()

    def _new_http_client(self) -> httpx.AsyncClient:
        client = httpx.AsyncClient(transport=self.transport, base_url=self.url)
        self._clients.append(client)
        return client

    def make_client(self, **overrides: Any) -> PortalClient:
        http_client = self._new_http_client()
        options = PortalClientOptions(
            url=self.url,
            finalized=self.finalized,
            http=http_client,
            **overrides,
        )
        return PortalClient(options)

    async def aclose(self) -> None:
        await asyncio.gather(*(client.aclose() for client in self._clients))


def create_mock_portal(responses: List[dict], *, finalized: bool = False) -> MockPortal:
    return MockPortal(responses=responses, finalized=finalized)


def create_finalized_mock_portal(responses: List[dict]) -> MockPortal:
    return create_mock_portal(responses, finalized=True)


async def close_mock_portal(mock_portal: Optional[MockPortal]) -> None:
    if mock_portal is None:
        return
    await mock_portal.aclose()
