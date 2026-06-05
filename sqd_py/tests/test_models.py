"""Tests for sqd.models dataclasses."""

import pytest

from sqd.models import BlockHead, ConflictResponse, DatasetMetadata, StreamResponse


class TestDatasetMetadata:
    """Tests for DatasetMetadata model."""

    def test_from_dict_success(self):
        """Test creating DatasetMetadata from a valid dictionary."""
        data = {
            "dataset": "ethereum-mainnet",
            "aliases": ["eth-mainnet", "ethereum"],
            "real_time": True,
            "start_block": 0,
        }
        metadata = DatasetMetadata.from_dict(data)

        assert metadata.dataset == "ethereum-mainnet"
        assert metadata.aliases == ["eth-mainnet", "ethereum"]
        assert metadata.real_time is True
        assert metadata.start_block == 0

    def test_from_dict_empty_aliases(self):
        """Test creating DatasetMetadata with empty aliases."""
        data = {
            "dataset": "binance-mainnet",
            "aliases": [],
            "real_time": False,
            "start_block": 1000,
        }
        metadata = DatasetMetadata.from_dict(data)

        assert metadata.dataset == "binance-mainnet"
        assert metadata.aliases == []
        assert metadata.real_time is False
        assert metadata.start_block == 1000

    def test_from_dict_missing_field(self):
        """Test that missing required fields raise KeyError."""
        data = {
            "dataset": "ethereum-mainnet",
            "aliases": [],
            # missing real_time and start_block
        }
        with pytest.raises(KeyError):
            DatasetMetadata.from_dict(data)


class TestBlockHead:
    """Tests for BlockHead model."""

    def test_from_dict_success(self):
        """Test creating BlockHead from a valid dictionary."""
        data = {
            "number": 17000000,
            "hash": "0xabc123def456",
        }
        head = BlockHead.from_dict(data)

        assert head.number == 17000000
        assert head.hash == "0xabc123def456"

    def test_from_dict_optional_fields(self):
        """Test creating BlockHead with missing optional fields."""
        data = {}
        head = BlockHead.from_dict(data)

        assert head.number is None
        assert head.hash is None

    def test_from_dict_partial_fields(self):
        """Test creating BlockHead with only number."""
        data = {"number": 12345}
        head = BlockHead.from_dict(data)

        assert head.number == 12345
        assert head.hash is None


class TestConflictResponse:
    """Tests for ConflictResponse model."""

    def test_from_dict_success(self):
        """Test creating ConflictResponse from a valid dictionary."""
        data = {
            "previousBlocks": [
                {"number": 100, "hash": "0xabc"},
                {"number": 99, "hash": "0xdef"},
            ]
        }
        response = ConflictResponse.from_dict(data)

        assert len(response.previousBlocks) == 2
        assert response.previousBlocks[0]["number"] == 100
        assert response.previousBlocks[1]["hash"] == "0xdef"

    def test_from_dict_empty_previous_blocks(self):
        """Test creating ConflictResponse with empty previous blocks."""
        data = {"previousBlocks": []}
        response = ConflictResponse.from_dict(data)

        assert response.previousBlocks == []

    def test_from_dict_missing_field(self):
        """Test that missing required fields raise KeyError."""
        data = {}
        with pytest.raises(KeyError):
            ConflictResponse.from_dict(data)


class TestStreamResponse:
    """Tests for StreamResponse model."""

    def test_from_response_with_headers(self):
        """Test creating StreamResponse with finalized head headers."""
        response_data = [
            {"block": {"number": 1}},
            {"block": {"number": 2}},
        ]
        headers = {
            "X-Sqd-Finalized-Head-Number": "17000000",
            "X-Sqd-Finalized-Head-Hash": "0xabc123",
        }

        response = StreamResponse.from_response(response_data, headers)

        assert response.data == response_data
        assert response.finalized_head_number == 17000000
        assert response.finalized_head_hash == "0xabc123"

    def test_from_response_without_headers(self):
        """Test creating StreamResponse without finalized head headers."""
        response_data = [{"block": {"number": 1}}]
        headers = {}

        response = StreamResponse.from_response(response_data, headers)

        assert response.data == response_data
        assert response.finalized_head_number is None
        assert response.finalized_head_hash is None

    def test_from_response_empty_data(self):
        """Test creating StreamResponse with empty data."""
        response = StreamResponse.from_response([], {})

        assert response.data == []
        assert response.finalized_head_number is None
        assert response.finalized_head_hash is None
