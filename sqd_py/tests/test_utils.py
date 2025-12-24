"""Tests for sqd.utils module."""

import pytest
from dataclasses import dataclass

from sqd.utils import validate_evm_address, _normalize_dataset, _request_to_sqd_string
from sqd.dataset import Dataset


class TestValidateEvmAddress:
    """Tests for EVM address validation."""

    def test_valid_lowercase_address(self):
        """Test validation of a lowercase address with 0x prefix."""
        address = "0x742d35cc6634c0532925a3b844bc9e7595f5ab12"
        result = validate_evm_address(address)
        assert result == "0x742d35cc6634c0532925a3b844bc9e7595f5ab12"

    def test_valid_uppercase_address(self):
        """Test that uppercase addresses are normalized to lowercase."""
        address = "0x742D35CC6634C0532925A3B844BC9E7595F5AB12"
        result = validate_evm_address(address)
        assert result == "0x742d35cc6634c0532925a3b844bc9e7595f5ab12"

    def test_valid_mixed_case_address(self):
        """Test that mixed case addresses are normalized to lowercase."""
        address = "0x742d35CC6634c0532925a3B844Bc9e7595F5aB12"
        result = validate_evm_address(address)
        assert result == "0x742d35cc6634c0532925a3b844bc9e7595f5ab12"

    def test_address_without_0x_prefix(self):
        """Test that addresses without 0x prefix get it added."""
        address = "742d35cc6634c0532925a3b844bc9e7595f5ab12"
        result = validate_evm_address(address)
        assert result == "0x742d35cc6634c0532925a3b844bc9e7595f5ab12"

    def test_empty_address_raises_error(self):
        """Test that empty address raises ValueError."""
        with pytest.raises(ValueError, match="Address cannot be empty"):
            validate_evm_address("")

    def test_short_address_raises_error(self):
        """Test that too short address raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address length"):
            validate_evm_address("0x742d35cc6634c0532925a3b844bc9e")

    def test_long_address_raises_error(self):
        """Test that too long address raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address length"):
            validate_evm_address("0x742d35cc6634c0532925a3b844bc9e7595f5ab12ab")

    def test_invalid_hex_raises_error(self):
        """Test that non-hex characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid address format"):
            validate_evm_address("0x742d35gg6634c0532925a3b844bc9e7595f5ab12")


class TestNormalizeDataset:
    """Tests for dataset normalization."""

    def test_valid_dataset_enum(self):
        """Test that Dataset enum values are returned as-is."""
        result = _normalize_dataset(Dataset.ETHEREUM)
        assert result == Dataset.ETHEREUM

    def test_valid_dataset_string_recognized(self):
        """Test that valid dataset strings are converted to enum."""
        result = _normalize_dataset("ethereum-mainnet")
        assert result == Dataset.ETHEREUM

    def test_unknown_dataset_string_returns_string(self):
        """Test that unknown dataset strings are returned as-is with warning."""
        # Unknown datasets are returned as strings (with a logged warning)
        result = _normalize_dataset("unknown-chain")
        assert result == "unknown-chain"
        assert isinstance(result, str)

    def test_solana_dataset(self):
        """Test Solana dataset normalization."""
        result = _normalize_dataset("solana-mainnet")
        assert result == Dataset.SOLANA

    def test_binance_dataset(self):
        """Test Binance dataset normalization."""
        result = _normalize_dataset("binance-mainnet")
        assert result == Dataset.BINANCE


class TestRequestToSqdString:
    """Tests for request payload conversion."""

    def test_basic_dataclass_conversion(self):
        """Test converting a basic dataclass to SQD payload."""

        @dataclass
        class TestRequest:
            address: str
            topic0: str

        request = TestRequest(address="0xabc", topic0="0xdef")
        result = _request_to_sqd_string(request)

        assert result == {"address": "0xabc", "topic0": "0xdef"}

    def test_from_field_normalization(self):
        """Test that from_ field gets normalized to 'from'."""

        @dataclass
        class TestRequest:
            from_: str
            to: str

        request = TestRequest(from_="0xabc", to="0xdef")
        result = _request_to_sqd_string(request)

        assert result == {"from": "0xabc", "to": "0xdef"}

    def test_none_values_are_filtered(self):
        """Test that None values are excluded from the result."""

        @dataclass
        class TestRequest:
            address: str
            topic0: str | None
            topic1: str | None

        request = TestRequest(address="0xabc", topic0=None, topic1="0xdef")
        result = _request_to_sqd_string(request)

        assert result == {"address": "0xabc", "topic1": "0xdef"}
        assert "topic0" not in result

    def test_all_none_values(self):
        """Test dataclass with all None values returns empty dict for non-None fields."""

        @dataclass
        class TestRequest:
            address: str
            topic0: str | None

        request = TestRequest(address="0xabc", topic0=None)
        result = _request_to_sqd_string(request)

        assert result == {"address": "0xabc"}
