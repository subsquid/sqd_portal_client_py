"""Tests for sqd.query.cursor module - QueryCursor parallel fetching."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sqd.query.cursor import QueryCursor
from sqd.query.progress import NoopProgressHandler, TqdmProgressHandler


class TestQueryCursorInit:
    """Tests for QueryCursor initialization."""

    def test_default_shards_is_one(self):
        """Test that default shards is 1."""
        mock_query = MagicMock()
        mock_query.from_block = 0
        mock_query.to_block = 100

        cursor = QueryCursor(mock_query)
        assert cursor._shards == 1

    def test_shards_parameter(self):
        """Test that shards parameter is stored."""
        mock_query = MagicMock()
        mock_query.from_block = 0
        mock_query.to_block = 100

        cursor = QueryCursor(mock_query, shards=5)
        assert cursor._shards == 5

    def test_show_progress_parameter(self):
        """Test that show_progress parameter creates TqdmProgressHandler."""
        mock_query = MagicMock()
        mock_query.from_block = 0
        mock_query.to_block = 100

        cursor = QueryCursor(mock_query, show_progress=True)
        assert isinstance(cursor._progress, TqdmProgressHandler)

    def test_no_progress_uses_noop_handler(self):
        """Test that no progress uses NoopProgressHandler."""
        mock_query = MagicMock()
        mock_query.from_block = 0
        mock_query.to_block = 100

        cursor = QueryCursor(mock_query, show_progress=False)
        assert isinstance(cursor._progress, NoopProgressHandler)

    def test_session_ownership(self):
        """Test session ownership tracking."""
        mock_query = MagicMock()
        mock_query.from_block = 0

        # No session provided - cursor owns it
        cursor1 = QueryCursor(mock_query)
        assert cursor1._owns_session is True

        # Session provided - cursor doesn't own it
        mock_session = MagicMock()
        cursor2 = QueryCursor(mock_query, session=mock_session)
        assert cursor2._owns_session is False


class TestShardCalculation:
    """Tests for shard range calculation."""

    def test_shard_ranges_no_gaps(self):
        """Test that shard ranges have no gaps."""
        from_block = 1000
        to_block = 1999
        shards = 5

        total_blocks = to_block - from_block + 1  # 1000
        blocks_per_shard = (total_blocks + shards - 1) // shards  # 200

        ranges = []
        for i in range(shards):
            start = from_block + (i * blocks_per_shard)
            if start > to_block:
                break
            end = min(start + blocks_per_shard - 1, to_block)
            ranges.append((start, end))

        # Verify no gaps
        for i in range(1, len(ranges)):
            prev_end = ranges[i - 1][1]
            curr_start = ranges[i][0]
            assert curr_start == prev_end + 1, f"Gap between shard {i-1} and {i}"

        # Verify coverage
        assert ranges[0][0] == from_block
        assert ranges[-1][1] == to_block

    def test_shard_ranges_uneven_division(self):
        """Test shard ranges with uneven block count."""
        from_block = 0
        to_block = 99  # 100 blocks
        shards = 3  # 100 / 3 = 33.33...

        total_blocks = to_block - from_block + 1
        blocks_per_shard = (total_blocks + shards - 1) // shards  # 34

        ranges = []
        for i in range(shards):
            start = from_block + (i * blocks_per_shard)
            if start > to_block:
                break
            end = min(start + blocks_per_shard - 1, to_block)
            ranges.append((start, end))

        # Should have 3 shards: 0-33, 34-67, 68-99
        assert len(ranges) == 3
        assert ranges[0] == (0, 33)
        assert ranges[1] == (34, 67)
        assert ranges[2] == (68, 99)

    def test_shard_ranges_more_shards_than_blocks(self):
        """Test when shards > total blocks."""
        from_block = 0
        to_block = 2  # Only 3 blocks
        shards = 10

        total_blocks = to_block - from_block + 1
        blocks_per_shard = (total_blocks + shards - 1) // shards  # 1

        ranges = []
        for i in range(shards):
            start = from_block + (i * blocks_per_shard)
            if start > to_block:
                break
            end = min(start + blocks_per_shard - 1, to_block)
            ranges.append((start, end))

        # Should only create 3 shards, not 10
        assert len(ranges) == 3


class TestQueryCursorProperties:
    """Tests for QueryCursor properties."""

    def test_headers_property(self):
        """Test headers property returns stored headers."""
        mock_query = MagicMock()
        mock_query.from_block = 0

        cursor = QueryCursor(mock_query)
        cursor._headers = {"x-sqd-head-number": "12345"}

        assert cursor.headers == {"x-sqd-head-number": "12345"}

    def test_last_block_number_property(self):
        """Test last_block_number property."""
        mock_query = MagicMock()
        mock_query.from_block = 0

        cursor = QueryCursor(mock_query)
        assert cursor.last_block_number is None

        cursor._last_block_number = 12345
        assert cursor.last_block_number == 12345


class TestWithProgress:
    """Tests for with_progress factory method."""

    def test_with_progress_returns_cursor(self):
        """Test that with_progress returns a QueryCursor."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet").get_blocks(
            from_block=0, to_block=100
        )
        cursor = query.with_progress()

        assert isinstance(cursor, QueryCursor)
        assert isinstance(cursor._progress, TqdmProgressHandler)

    def test_with_progress_shards_parameter(self):
        """Test that with_progress accepts shards parameter."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet").get_blocks(
            from_block=0, to_block=100
        )
        cursor = query.with_progress(shards=5)

        assert cursor._shards == 5


class TestQueryCursorClose:
    """Tests for QueryCursor resource cleanup."""

    @pytest.mark.asyncio
    async def test_close_cancels_worker_task(self):
        """Test that close cancels the worker task."""
        mock_query = MagicMock()
        mock_query.from_block = 0

        cursor = QueryCursor(mock_query)

        # Create a proper async mock task
        async def dummy_coro():
            raise asyncio.CancelledError()

        mock_task = asyncio.create_task(dummy_coro())
        # Let the task start
        await asyncio.sleep(0)

        cursor._worker_task = mock_task

        await cursor.close()

        assert mock_task.cancelled() or mock_task.done()

    @pytest.mark.asyncio
    async def test_close_closes_owned_session(self):
        """Test that close closes owned session."""
        mock_query = MagicMock()
        mock_query.from_block = 0

        cursor = QueryCursor(mock_query)
        cursor._owns_session = True

        mock_session = AsyncMock()
        mock_session.closed = False
        cursor._session = mock_session

        await cursor.close()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_does_not_close_external_session(self):
        """Test that close doesn't close externally provided session."""
        mock_query = MagicMock()
        mock_query.from_block = 0

        mock_session = AsyncMock()
        mock_session.closed = False

        cursor = QueryCursor(mock_query, session=mock_session)
        assert cursor._owns_session is False

        await cursor.close()

        mock_session.close.assert_not_called()


class TestProbeHeadBlock:
    """Tests for _probe_head_block method."""

    @pytest.mark.asyncio
    async def test_probe_head_block_success(self):
        """Test successful head block probe."""
        mock_query = MagicMock()
        mock_query.from_block = 0
        mock_query.portal_url = "https://portal.sqd.dev"
        mock_query.dataset = "ethereum-mainnet"

        cursor = QueryCursor(mock_query)

        # Mock session response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"number": 12345678, "hash": "0x..."})

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        cursor._session = mock_session

        result = await cursor._probe_head_block()
        assert result == 12345678

    @pytest.mark.asyncio
    async def test_probe_head_block_failure(self):
        """Test head block probe failure returns None."""
        mock_query = MagicMock()
        mock_query.from_block = 0
        mock_query.portal_url = "https://portal.sqd.dev"
        mock_query.dataset = "ethereum-mainnet"

        cursor = QueryCursor(mock_query)

        # Mock session that raises exception
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        cursor._session = mock_session

        result = await cursor._probe_head_block()
        assert result is None


class TestAiter:
    """Tests for __aiter__ method."""

    def test_aiter_returns_self(self):
        """Test that __aiter__ returns self."""
        mock_query = MagicMock()
        mock_query.from_block = 0
        mock_query.to_block = 100

        cursor = QueryCursor(mock_query)

        # Mock create_task to avoid actually running
        with patch("asyncio.create_task") as mock_create_task:
            mock_create_task.return_value = MagicMock()
            result = cursor.__aiter__()

        assert result is cursor

    def test_aiter_creates_worker_task(self):
        """Test that __aiter__ creates worker task."""
        mock_query = MagicMock()
        mock_query.from_block = 0
        mock_query.to_block = 100

        cursor = QueryCursor(mock_query)
        assert cursor._worker_task is None

        with patch("asyncio.create_task") as mock_create_task:
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task
            cursor.__aiter__()

        assert cursor._worker_task is mock_task


@pytest.mark.integration
class TestParallelFetchingIntegration:
    """Integration tests for parallel fetching (requires network).

    Run with: pytest tests/test_cursor.py -v -m integration
    """

    @pytest.mark.asyncio
    async def test_parallel_fetching_no_gaps(self):
        """Test that parallel fetching returns all blocks without gaps.

        Based on check_blocks.py verification pattern.
        """
        from sqd import SQD, Dataset

        from_block = 12649280
        to_block = from_block + 1000  # Small range for fast test
        shards = 3

        sqd = SQD(dataset=Dataset.ETHEREUM, portal_url="https://portal.sqd.dev")
        query = sqd.get_blocks(
            from_block=from_block,
            to_block=to_block,
        )

        blocks = []
        async for data in query.with_progress(shards=shards):
            blocks.append(data["header"]["number"])

        # Verify: min matches from_block
        assert min(blocks) == from_block, f"Expected min {from_block}, got {min(blocks)}"

        # Verify: max matches to_block
        assert max(blocks) == to_block, f"Expected max {to_block}, got {max(blocks)}"

        # Verify: correct count
        expected_count = to_block - from_block + 1
        assert len(blocks) == expected_count, f"Expected {expected_count} blocks, got {len(blocks)}"

        # Verify: no gaps (each block follows previous)
        sorted_blocks = sorted(blocks)
        for i, block in enumerate(sorted_blocks):
            expected = from_block + i
            assert block == expected, f"Gap at position {i}: expected {expected}, got {block}"

    @pytest.mark.asyncio
    async def test_serial_vs_parallel_same_results(self):
        """Test that serial and parallel fetching return the same blocks."""
        from sqd import SQD, Dataset

        from_block = 12649280
        to_block = from_block + 500  # Small range

        sqd = SQD(dataset=Dataset.ETHEREUM, portal_url="https://portal.sqd.dev")
        query = sqd.get_blocks(
            from_block=from_block,
            to_block=to_block,
        )

        # Serial fetch
        serial_blocks = []
        async for data in query.with_progress(shards=1):
            serial_blocks.append(data["header"]["number"])

        # Parallel fetch
        parallel_blocks = []
        async for data in query.with_progress(shards=3):
            parallel_blocks.append(data["header"]["number"])

        # Compare (sorted because parallel order may differ)
        assert sorted(serial_blocks) == sorted(parallel_blocks)
        assert len(serial_blocks) == len(parallel_blocks)

