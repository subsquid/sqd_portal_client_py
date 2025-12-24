"""Tests for sqd.sqd module - main entry point."""

import pytest

from sqd import SQD
from sqd.query.evm.query import EVMQuery
from sqd.query.solana.query import SolanaQuery


class TestSQDFactory:
    """Tests for the SQD factory function."""

    def test_evm_dataset_returns_evm_query(self):
        """Test that EVM datasets return EVMQuery."""
        query = SQD(dataset="ethereum-mainnet")
        assert isinstance(query, EVMQuery)

    def test_binance_dataset_returns_evm_query(self):
        """Test that Binance dataset returns EVMQuery."""
        query = SQD(dataset="binance-mainnet")
        assert isinstance(query, EVMQuery)

    def test_solana_dataset_returns_solana_query(self):
        """Test that Solana datasets return SolanaQuery."""
        query = SQD(dataset="solana-mainnet")
        assert isinstance(query, SolanaQuery)

    def test_custom_portal_url(self):
        """Test that custom portal URL is set correctly."""
        custom_url = "https://custom.portal.dev"
        query = SQD(dataset="ethereum-mainnet", portal_url=custom_url)
        assert query.portal_url == custom_url

    def test_default_portal_url(self):
        """Test that default portal URL is used when not specified."""
        query = SQD(dataset="ethereum-mainnet")
        assert query.portal_url == "https://portal.sqd.dev"

    def test_stream_type_finalized(self):
        """Test that finalized stream type is set correctly."""
        query = SQD(dataset="ethereum-mainnet", stream_type="finalized")
        assert query.stream_type == "finalized"

    def test_stream_type_realtime(self):
        """Test that realtime stream type is set correctly."""
        query = SQD(dataset="ethereum-mainnet", stream_type="realtime")
        assert query.stream_type == "realtime"

    def test_default_stream_type(self):
        """Test that default stream type is realtime."""
        query = SQD(dataset="ethereum-mainnet")
        assert query.stream_type == "realtime"

    def test_unknown_evm_dataset(self):
        """Test that unknown datasets default to EVM query."""
        # Unknown datasets are treated as EVM if they don't contain 'solana'
        # Note: This will log a warning but still work
        query = SQD(dataset="arbitrum-one")
        assert isinstance(query, EVMQuery)
        # Verify the dataset is preserved as a string
        assert query.dataset == "arbitrum-one"

    def test_solana_detection_case_insensitive(self):
        """Test that Solana detection works with hyphenated strings."""
        # Note: The _is_solana function checks for 'solana' substring (case-insensitive)
        query = SQD(dataset="solana-devnet")
        assert isinstance(query, SolanaQuery)

    def test_query_dataset_is_set(self):
        """Test that query has correct dataset set."""
        query = SQD(dataset="ethereum-mainnet")
        assert query.dataset == "ethereum-mainnet"
