"""Tests for sqd.dataset module."""

from sqd.dataset import Dataset


class TestDataset:
    """Tests for Dataset enum."""

    def test_ethereum_value(self):
        """Test Ethereum dataset value."""
        assert Dataset.ETHEREUM == "ethereum-mainnet"
        assert Dataset.ETHEREUM.value == "ethereum-mainnet"

    def test_binance_value(self):
        """Test Binance dataset value."""
        assert Dataset.BINANCE == "binance-mainnet"
        assert Dataset.BINANCE.value == "binance-mainnet"

    def test_solana_value(self):
        """Test Solana dataset value."""
        assert Dataset.SOLANA == "solana-mainnet"
        assert Dataset.SOLANA.value == "solana-mainnet"

    def test_str_comparison(self):
        """Test that Dataset enum can be compared with strings."""
        assert Dataset.ETHEREUM == "ethereum-mainnet"
        assert str(Dataset.ETHEREUM) == "ethereum-mainnet"

    def test_dataset_membership(self):
        """Test that strings can be used to create Dataset enum."""
        dataset = Dataset("ethereum-mainnet")
        assert dataset == Dataset.ETHEREUM

    def test_invalid_dataset_raises_error(self):
        """Test that invalid dataset string raises ValueError."""
        import pytest

        with pytest.raises(ValueError):
            Dataset("invalid-chain")


class TestEvmDataset:
    """Tests for EvmDataset type alias."""

    def test_evm_datasets_are_literal(self):
        """Test that EVM datasets are part of the literal type."""
        # These should be valid EvmDataset values
        evm_chains = [Dataset.ETHEREUM, Dataset.BINANCE]
        for chain in evm_chains:
            assert isinstance(chain, Dataset)


class TestSolanaDataset:
    """Tests for SolanaDataset type alias."""

    def test_solana_dataset_is_literal(self):
        """Test that Solana dataset is part of the literal type."""
        assert isinstance(Dataset.SOLANA, Dataset)
