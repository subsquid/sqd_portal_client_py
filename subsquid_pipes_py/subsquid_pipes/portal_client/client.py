from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterable, AsyncIterator, Dict, Iterable, List, Optional, Sequence
from urllib.error import HTTPError

import anyio
import httpx

from ..core.types import BlockCursor
from .fork_exception import ForkException

USER_AGENT = 'subsquid-pipes-python'


@dataclass(slots=True)
class PortalClientOptions:
    url: str
    finalized: bool = False
    min_bytes: int = 10 * 1024 * 1024
    max_bytes: Optional[int] = None
    max_idle_time: float = 0.3
    max_wait_time: float = 5.0
    head_poll_interval: float = 0.0
    retry_attempts: int = 10
    retry_schedule: Sequence[float] = field(default_factory=lambda: (0.0,))
    http: httpx.AsyncClient | None = None


@dataclass(slots=True)
class PortalStreamData:
    blocks: list[dict]
    finalized_head: BlockCursor | None
    meta: Dict[str, Any]


PortalStream = AsyncIterator[PortalStreamData]


class PortalClient:
    def __init__(self, options: PortalClientOptions) -> None:
        self._options = options
        self._client = options.http or httpx.AsyncClient(headers={'User-Agent': USER_AGENT})
        self._url = httpx.URL(options.url)

    def get_url(self) -> str:
        return str(self._url)

    async def get_metadata(self) -> dict[str, Any]:
        response = await self._client.get(self._dataset_url('metadata'))
        response.raise_for_status()
        return response.json()

    async def get_head(self, *, finalized: bool | None = None) -> dict[str, Any] | None:
        path = 'finalized-head' if (finalized if finalized is not None else self._options.finalized) else 'head'
        response = await self._client.get(self._dataset_url(path))
        if response.status_code == 204:
            return None
        response.raise_for_status()
        body = response.json()
        return body if body else None

    def get_stream(self, query: dict[str, Any], *, finalized: bool | None = None) -> PortalStream:
        settings = {
            'finalized': finalized if finalized is not None else self._options.finalized,
            'min_bytes': self._options.min_bytes,
            'max_bytes': self._options.max_bytes or self._options.min_bytes,
            'max_idle_time': self._options.max_idle_time,
            'head_poll_interval': self._options.head_poll_interval,
            'retry_attempts': self._options.retry_attempts,
            'retry_schedule': list(self._options.retry_schedule) or [0.0],
        }

        async def iterator() -> AsyncIterator[PortalStreamData]:
            from_block = query.get('fromBlock', 0)
            to_block = query.get('toBlock')
            parent_block_hash = query.get('parentBlockHash')
            while True:
                if to_block is not None and from_block > to_block:
                    break
                request_payload = dict(query)
                request_payload['fromBlock'] = from_block
                request_payload['parentBlockHash'] = parent_block_hash
                path = 'finalized-stream' if settings['finalized'] else 'stream'
                status_counts: Dict[int, int] = defaultdict(int)
                finalized_head = None
                retries = 0
                while True:
                    try:
                        async with self._client.stream('POST', self._dataset_url(path), json=request_payload) as response:
                            status_counts[response.status_code] += 1
                            if response.status_code == 204:
                                meta = {
                                    'bytes': 0,
                                    'requestedFromBlock': from_block,
                                    'lastBlockReceivedAt': datetime.utcnow(),
                                    'requests': dict(status_counts),
                                }
                                yield PortalStreamData(blocks=[], finalized_head=None, meta=meta)
                                if settings['head_poll_interval'] > 0:
                                    await anyio.sleep(settings['head_poll_interval'] / 1000)
                                break
                            if response.status_code == 409:
                                raise self._fork_from_response(response)
                            if response.is_error:
                                await response.aread()
                                raise HTTPError(response.url, response.status_code, response.text, response.headers, None)
                            finalized_head = _read_finalized_header(response)
                            current_blocks: list[dict] = []
                            current_bytes = 0
                            async for lines in split_lines(response.aiter_bytes()):
                                for raw in lines:
                                    if not raw:
                                        continue
                                    current_bytes += len(raw)
                                    block = json.loads(raw)
                                    current_blocks.append(block)
                                    from_block = block['header']['number'] + 1
                                    parent_block_hash = block['header']['hash']
                                    if current_bytes >= settings['min_bytes']:
                                        meta = {
                                            'bytes': current_bytes,
                                            'requestedFromBlock': request_payload['fromBlock'],
                                            'lastBlockReceivedAt': datetime.utcnow(),
                                            'requests': dict(status_counts),
                                        }
                                        yield PortalStreamData(blocks=current_blocks, finalized_head=finalized_head, meta=meta)
                                        current_blocks = []
                                        current_bytes = 0
                            if current_blocks:
                                meta = {
                                    'bytes': current_bytes,
                                    'requestedFromBlock': request_payload['fromBlock'],
                                    'lastBlockReceivedAt': datetime.utcnow(),
                                    'requests': dict(status_counts),
                                }
                                yield PortalStreamData(blocks=current_blocks, finalized_head=finalized_head, meta=meta)
                            break
                    except ForkException:
                        raise
                    except httpx.HTTPStatusError as err:
                        status = err.response.status_code
                        if status == 409:
                            raise self._fork_from_response(err.response)
                        if status in (500, 503) and retries < settings['retry_attempts']:
                            delay = settings['retry_schedule'][min(retries, len(settings['retry_schedule']) - 1)]
                            retries += 1
                            if delay:
                                await anyio.sleep(delay / 1000)
                            continue
                        raise
                if finalized_head and to_block is None:
                    break
                if to_block is not None and from_block > to_block:
                    break
            return

        return iterator()

    def _fork_from_response(self, response: httpx.Response) -> ForkException:
        payload = response.json()
        previous_blocks = []
        for block in payload.get('previousBlocks', []):
            ref = block.get('header') if isinstance(block, dict) and 'header' in block else block
            previous_blocks.append(BlockCursor(number=ref['number'], hash=ref['hash']))
        return ForkException(previous_blocks=previous_blocks, query=payload.get('query'))

    def _dataset_url(self, path: str) -> str:
        url = self._url.copy_with()
        new_path = url.path.rstrip('/') + f'/{path}'
        return str(url.copy_with(path=new_path))


def _read_finalized_header(response: httpx.Response) -> BlockCursor | None:
    number = response.headers.get('X-Sqd-Finalized-Head-Number')
    hash_ = response.headers.get('X-Sqd-Finalized-Head-Hash')
    if number is None or hash_ is None:
        return None
    return BlockCursor(number=int(number), hash=hash_)


class LineSplitter:
    def __init__(self) -> None:
        self._line = ''

    def push(self, data: bytes) -> List[str]:
        if not data:
            return []
        fragment = data.decode('utf-8')
        if not fragment:
            return []
        fragment = self._line + fragment
        parts = fragment.split('\n')
        self._line = parts.pop() if parts else ''
        return [line for line in parts if line]

    def end(self) -> Optional[str]:
        if self._line:
            last = self._line
            self._line = ''
            return last
        return None


async def split_lines(chunks: AsyncIterable[bytes]) -> AsyncIterator[List[str]]:
    splitter = LineSplitter()
    async for chunk in chunks:
        lines = splitter.push(chunk)
        if lines:
            yield lines
    last = splitter.end()
    if last:
        yield [last]


__all__ = ['PortalClient', 'PortalClientOptions', 'PortalStreamData', 'PortalStream', 'split_lines']
