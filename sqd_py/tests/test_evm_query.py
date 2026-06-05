"""Tests for sqd.query.evm.query module - EVM query builder."""

import json

from sqd.query.evm.fields import (
    BlockField,
    LogField,
    StateDiffField,
    TraceField,
    TransactionField,
)
from sqd.query.evm.query import EVMQuery


class TestEVMQueryCreation:
    """Tests for EVMQuery creation."""

    def test_create_basic_query(self):
        """Test creating a basic EVM query."""
        query = EVMQuery.create(dataset="ethereum-mainnet")

        assert query.dataset == "ethereum-mainnet"
        assert query.portal_url == "https://portal.sqd.dev"
        assert query.stream_type == "realtime"
        assert query.from_block == 0
        assert query.to_block is None

    def test_create_with_custom_options(self):
        """Test creating query with custom options."""
        query = EVMQuery.create(
            dataset="ethereum-mainnet",
            portal_url="https://custom.sqd.dev",
            stream_type="finalized",
        )

        assert query.portal_url == "https://custom.sqd.dev"
        assert query.stream_type == "finalized"


class TestGetBlocks:
    """Tests for get_blocks method."""

    def test_get_blocks_basic(self):
        """Test basic blocks query."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_blocks(
            from_block=17_000_000,
        )

        assert query.from_block == 17_000_000
        assert query.include_all_blocks is True

    def test_get_blocks_with_to_block(self):
        """Test blocks query with to_block."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_blocks(
            from_block=17_000_000,
            to_block=17_000_100,
        )

        assert query.from_block == 17_000_000
        assert query.to_block == 17_000_100

    def test_get_blocks_with_fields(self):
        """Test blocks query with specific fields."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_blocks(
            from_block=17_000_000,
            include_fields=[BlockField.number, BlockField.hash, BlockField.timestamp],
        )

        payload = query.to_payload()
        assert "fields" in payload
        assert "block" in payload["fields"]
        assert payload["fields"]["block"]["number"] is True
        assert payload["fields"]["block"]["hash"] is True

    def test_get_blocks_always_includes_all_blocks(self):
        """Test that get_blocks always sets include_all_blocks=True."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_blocks(
            from_block=17_000_000,
        )

        payload = query.to_payload()
        assert payload.get("includeAllBlocks") is True


class TestGetTransactions:
    """Tests for get_transactions method."""

    def test_get_transactions_basic(self):
        """Test basic transaction query."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
        )

        assert query.from_block == 17_000_000
        assert query.query_type == "evm"

    def test_get_transactions_with_address(self):
        """Test transaction query with address filter."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            address="0x742d35cc6634c0532925a3b844bc9e7595f5ab12",
        )

        payload = query.to_payload()
        assert "transactions" in payload
        assert len(payload["transactions"]) >= 1

    def test_get_transactions_with_from_to_address(self):
        """Test transaction query with from and to address."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            from_address="0x742d35cc6634c0532925a3b844bc9e7595f5ab12",
            to_address="0xdac17f958d2ee523a2206206994597c13d831ec7",
        )

        payload = query.to_payload()
        assert "transactions" in payload

    def test_get_transactions_with_sighash(self):
        """Test transaction query with sighash filter."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            sighash="0xa9059cbb",  # ERC20 transfer
        )

        payload = query.to_payload()
        assert "transactions" in payload

    def test_get_transactions_with_to_block(self):
        """Test transaction query with to_block."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            to_block=17_001_000,
        )

        assert query.from_block == 17_000_000
        assert query.to_block == 17_001_000

    def test_get_transactions_include_all_blocks(self):
        """Test transaction query with include_all_blocks."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            include_all_blocks=True,
        )

        payload = query.to_payload()
        assert payload.get("includeAllBlocks") is True

    def test_get_transactions_with_fields(self):
        """Test transaction query with specific fields."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            include_fields=[TransactionField.hash, TransactionField.value],
        )

        payload = query.to_payload()
        assert "fields" in payload
        assert "transaction" in payload["fields"]


class TestGetLogs:
    """Tests for get_logs method."""

    def test_get_logs_basic(self):
        """Test basic log query."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_logs(
            from_block=17_000_000,
        )

        assert query.from_block == 17_000_000

    def test_get_logs_with_address(self):
        """Test log query with contract address."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_logs(
            from_block=17_000_000,
            address="0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
        )

        payload = query.to_payload()
        assert "logs" in payload

    def test_get_logs_with_topics(self):
        """Test log query with topic filters."""
        transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        query = EVMQuery.create(dataset="ethereum-mainnet").get_logs(
            from_block=17_000_000,
            topic0=transfer_topic,
        )

        payload = query.to_payload()
        assert "logs" in payload

    def test_get_logs_include_transaction(self):
        """Test log query including transaction data."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_logs(
            from_block=17_000_000,
            include_transaction=True,
        )

        payload = query.to_payload()
        # The include_transaction flag should add transaction to the request
        assert "logs" in payload


class TestGetTransfers:
    """Tests for get_transfers convenience method."""

    def test_get_transfers_returns_evm_query(self):
        """Test that get_transfers returns an EVMQuery."""
        result = EVMQuery.create(dataset="ethereum-mainnet").get_transfers(
            from_block=17_000_000,
        )

        assert isinstance(result, EVMQuery)

    def test_get_transfers_uses_transfer_topic(self):
        """Test that get_transfers uses the correct Transfer event signature."""
        result = EVMQuery.create(dataset="ethereum-mainnet").get_transfers(
            from_block=17_000_000,
        )

        payload = result.to_payload()
        logs_request = payload["logs"][0]
        assert "topic0" in logs_request
        # Transfer(address,address,uint256) signature
        assert logs_request["topic0"] == [
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        ]

    def test_get_transfers_with_contract_address(self):
        """Test transfers query filtered by token contract."""
        result = EVMQuery.create(dataset="ethereum-mainnet").get_transfers(
            from_block=17_000_000,
            contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        )

        payload = result.to_payload()
        logs_request = payload["logs"][0]
        assert "address" in logs_request

    def test_get_transfers_with_from_address(self):
        """Test transfers query filtered by sender address."""
        result = EVMQuery.create(dataset="ethereum-mainnet").get_transfers(
            from_block=17_000_000,
            from_address="0x742d35cc6634c0532925a3b844bc9e7595f5ab12",
        )

        payload = result.to_payload()
        logs_request = payload["logs"][0]
        # Address should be zero-padded to 32 bytes
        assert "topic1" in logs_request
        assert logs_request["topic1"][0].startswith("0x000000000000000000000000")


class TestGetTraces:
    """Tests for get_traces method."""

    def test_get_traces_basic(self):
        """Test basic traces query."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_traces(
            from_block=17_000_000,
        )

        assert query.from_block == 17_000_000

    def test_get_traces_with_type(self):
        """Test traces query with type filter."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_traces(
            from_block=17_000_000,
            type="call",
        )

        payload = query.to_payload()
        assert "traces" in payload

    def test_get_traces_with_call_filters(self):
        """Test traces query with call filters."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_traces(
            from_block=17_000_000,
            call_to="0x742d35cc6634c0532925a3b844bc9e7595f5ab12",
            call_from="0xdac17f958d2ee523a2206206994597c13d831ec7",
        )

        payload = query.to_payload()
        assert "traces" in payload


class TestGetStateDiffs:
    """Tests for get_state_diffs method."""

    def test_get_state_diffs_basic(self):
        """Test basic state diffs query."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_state_diffs(
            from_block=17_000_000,
        )

        assert query.from_block == 17_000_000

    def test_get_state_diffs_with_address(self):
        """Test state diffs query with address filter."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_state_diffs(
            from_block=17_000_000,
            address="0x742d35cc6634c0532925a3b844bc9e7595f5ab12",
        )

        payload = query.to_payload()
        assert "stateDiffs" in payload


class TestQueryPayload:
    """Tests for query payload generation."""

    def test_to_payload_structure(self):
        """Test that to_payload returns correct structure."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            to_block=17_001_000,
        )

        payload = query.to_payload()

        assert payload["type"] == "evm"
        assert payload["fromBlock"] == 17_000_000
        assert payload["toBlock"] == 17_001_000

    def test_to_sqd_string_is_valid_json(self):
        """Test that to_sqd_string returns valid JSON."""
        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
        )

        json_string = query.to_sqd_string()

        # Should be valid JSON
        parsed = json.loads(json_string)
        assert isinstance(parsed, dict)
        assert parsed["fromBlock"] == 17_000_000

    def test_endpoint_realtime(self):
        """Test endpoint generation for realtime stream."""
        query = EVMQuery.create(
            dataset="ethereum-mainnet",
            stream_type="realtime",
        )

        endpoint = query.endpoint()
        assert endpoint == "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"

    def test_endpoint_finalized(self):
        """Test endpoint generation for finalized stream."""
        query = EVMQuery.create(
            dataset="ethereum-mainnet",
            stream_type="finalized",
        )

        endpoint = query.endpoint()
        assert endpoint == "https://portal.sqd.dev/datasets/ethereum-mainnet/finalized-stream"


class TestQueryImmutability:
    """Tests for query immutability."""

    def test_get_transactions_returns_new_query(self):
        """Test that get_transactions returns a new query instance."""
        base_query = EVMQuery.create(dataset="ethereum-mainnet")
        new_query = base_query.get_transactions(from_block=17_000_000)

        assert base_query is not new_query
        assert base_query.from_block == 0
        assert new_query.from_block == 17_000_000

    def test_chained_queries_are_independent(self):
        """Test that chained queries don't modify original."""
        base_query = EVMQuery.create(dataset="ethereum-mainnet")
        query1 = base_query.get_transactions(from_block=17_000_000)
        query2 = base_query.get_logs(from_block=18_000_000)

        assert query1.from_block == 17_000_000
        assert query2.from_block == 18_000_000
        assert base_query.from_block == 0


class TestFieldEnums:
    """Tests for field enum values."""

    def test_transaction_field_from(self):
        """Test that TransactionField.from_ has correct value."""
        assert TransactionField.from_.value == "from"

    def test_transaction_field_hash(self):
        """Test TransactionField.hash value."""
        assert TransactionField.hash.value == "hash"

    def test_log_field_address(self):
        """Test LogField.address value."""
        assert LogField.address.value == "address"

    def test_trace_field_type(self):
        """Test TraceField.type value."""
        assert TraceField.type.value == "type"

    def test_state_diff_field_kind(self):
        """Test StateDiffField.kind value."""
        assert StateDiffField.kind.value == "kind"

    def test_block_field_number(self):
        """Test BlockField.number value."""
        assert BlockField.number.value == "number"
