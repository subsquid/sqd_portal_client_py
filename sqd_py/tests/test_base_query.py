"""Tests for sqd.query.base_query module."""

import pytest

from sqd.query.base_query import _freeze_field_values


class TestFreezeFieldValues:
    """Tests for _freeze_field_values helper function."""

    def test_freeze_empty_dict(self):
        """Test freezing an empty dictionary."""
        result = _freeze_field_values({})
        assert result == {}

    def test_freeze_single_category(self):
        """Test freezing a single category."""
        raw = {"transaction": ["hash", "value", "from"]}
        result = _freeze_field_values(raw)

        assert "transaction" in result
        assert isinstance(result["transaction"], frozenset)
        assert result["transaction"] == frozenset(["hash", "value", "from"])

    def test_freeze_multiple_categories(self):
        """Test freezing multiple categories."""
        raw = {
            "transaction": ["hash"],
            "log": ["address", "topics"],
        }
        result = _freeze_field_values(raw)

        assert result["transaction"] == frozenset(["hash"])
        assert result["log"] == frozenset(["address", "topics"])

    def test_frozen_values_are_immutable(self):
        """Test that frozen values cannot be modified."""
        raw = {"transaction": ["hash"]}
        result = _freeze_field_values(raw)

        with pytest.raises(AttributeError):
            result["transaction"].add("new_field")


class TestBaseSQDQueryEndpoint:
    """Tests for BaseSQDQuery endpoint generation."""

    def test_endpoint_realtime(self):
        """Test endpoint for realtime stream."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(
            dataset="ethereum-mainnet",
            stream_type="realtime",
        )
        endpoint = query.endpoint()

        assert endpoint == "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"

    def test_endpoint_finalized(self):
        """Test endpoint for finalized stream."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(
            dataset="ethereum-mainnet",
            stream_type="finalized",
        )
        endpoint = query.endpoint()

        assert (
            endpoint
            == "https://portal.sqd.dev/datasets/ethereum-mainnet/finalized-stream"
        )

    def test_endpoint_custom_portal_url(self):
        """Test endpoint with custom portal URL."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(
            dataset="ethereum-mainnet",
            portal_url="https://custom.portal.dev",
        )
        endpoint = query.endpoint()

        assert endpoint == "https://custom.portal.dev/datasets/ethereum-mainnet/stream"

        query = EVMQuery.create(
            dataset="ethereum-mainnet",
            portal_url="https://custom.portal.dev",
            stream_type="finalized",
        )
        endpoint = query.endpoint()

        assert (
            endpoint
            == "https://custom.portal.dev/datasets/ethereum-mainnet/finalized-stream"
        )


class TestBaseSQDQueryBlockRange:
    """Tests for block range handling."""

    def test_initial_from_block(self):
        """Test initial from_block is 0."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet")
        assert query.from_block == 0
        assert query.to_block is None

    def test_update_block_range_sets_from(self):
        """Test that update_block_range keeps minimum from_block."""
        from sqd.query.evm.query import EVMQuery

        from_block = 1234567
        query = EVMQuery.create(dataset="ethereum-mainnet")
        # Note: _update_block_range takes minimum of current (0) and new from_block
        # So if from_block is 0, it stays 0 (the minimum)
        updated = query.get_logs(from_block=from_block)

        # from_block stays 0 because min(0, 17_000_000) = 0
        assert updated.from_block == from_block
        assert updated.to_block is None

    def test_update_block_range_sets_to(self):
        """Test that update_block_range sets to_block."""
        from sqd.query.evm.query import EVMQuery

        from_block = 17_000_000
        to_block = 17_001_000
        query = EVMQuery.create(dataset="ethereum-mainnet")
        updated = query.get_transactions(from_block=from_block, to_block=to_block)

        # from_block stays 0 because min(0, 17_000_000) = 0
        assert updated.from_block == from_block
        assert updated.to_block == to_block

    def test_multiple_updates_take_minimum_from(self):
        """Test that multiple updates take minimum from_block."""
        from sqd.query.evm.query import EVMQuery

        from_block = 16_000_000
        query = EVMQuery.create(dataset="ethereum-mainnet")
        query = query.get_logs(from_block=from_block + 100000, to_block=None)
        query = query.get_transactions(from_block=from_block, to_block=None)

        # Initial from_block is 0, so minimum stays 0
        assert query.from_block == from_block

    def test_multiple_updates_take_maximum_to(self):
        """Test that multiple updates take maximum to_block."""
        from sqd.query.evm.query import EVMQuery

        from_block = 17_000_000
        to_block = 17_002_000
        query = EVMQuery.create(dataset="ethereum-mainnet")
        query = query._update_block_range(
            from_block=from_block, to_block=to_block - 1000
        )
        query = query._update_block_range(from_block=from_block, to_block=to_block)

        assert query.to_block == to_block


class TestBaseSQDQueryFields:
    """Tests for field handling."""

    def test_add_fields_creates_new_query(self):
        """
        Test that add_fields returns a new query.
        Query is immutable and a new instance is returned to ensure thread-safety and predictable behavior.
        """
        from sqd.query.evm.query import EVMQuery
        from sqd.query.evm.fields import TransactionField

        query = EVMQuery.create(dataset="ethereum-mainnet")
        new_query = query.add_fields("transaction", [TransactionField.hash])

        assert query is not new_query

    def test_add_fields_adds_to_category(self):
        """Test that add_fields adds fields to the correct category."""
        from sqd.query.evm.query import EVMQuery
        from sqd.query.evm.fields import TransactionField

        query = EVMQuery.create(dataset="ethereum-mainnet")
        updated = query.add_fields(
            "transaction", [TransactionField.hash, TransactionField.value]
        )

        assert "hash" in updated._fields.get("transaction")
        assert "value" in updated._fields.get("transaction")

    def test_add_fields_with_none_returns_same(self):
        """Test that add_fields with None returns same query."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet")
        result = query.add_fields("transaction", None)

        assert result is query

    def test_add_fields_with_empty_list_returns_same(self):
        """Test that add_fields with empty list returns same query."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet")
        result = query.add_fields("transaction", [])

        assert result is query


class TestBaseSQDQueryPayload:
    """Tests for payload generation."""

    def test_base_payload_has_type(self):
        """Test that base payload includes query type."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000
        )
        payload = query._base_payload()

        assert "type" in payload

    def test_base_payload_has_from_block(self):
        """Test that base payload includes fromBlock."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000
        )
        payload = query._base_payload()

        assert "fromBlock" in payload
        assert payload["fromBlock"] == 17_000_000

    def test_base_payload_omits_to_block_when_none(self):
        """Test that toBlock is omitted when None."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000
        )
        payload = query._base_payload()

        assert "toBlock" not in payload

    def test_base_payload_includes_to_block_when_set(self):
        """Test that toBlock is included when set."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            to_block=17_001_000,
        )
        payload = query._base_payload()

        assert payload["toBlock"] == 17_001_000

    def test_payload_includes_fields_when_set(self):
        """Test that fields are included in payload."""
        from sqd.query.evm.query import EVMQuery
        from sqd.query.evm.fields import TransactionField

        query = EVMQuery.create(dataset="ethereum-mainnet").get_transactions(
            from_block=17_000_000,
            include_fields=[TransactionField.hash],
        )
        payload = query.to_payload()

        assert "fields" in payload
        assert "transaction" in payload["fields"]


class TestQueryIteration:
    """Tests for query async iteration."""

    def test_query_is_async_iterable(self):
        """Test that query has __aiter__ method."""
        from sqd.query.evm.query import EVMQuery

        query = EVMQuery.create(dataset="ethereum-mainnet")

        assert hasattr(query, "__aiter__")
        assert callable(query.__aiter__)

    def test_aiter_returns_cursor(self):
        """Test that __aiter__ returns a cursor."""
        from sqd.query.evm.query import EVMQuery
        from sqd.query.cursor import QueryCursor

        query = EVMQuery.create(dataset="ethereum-mainnet")
        cursor = query.__aiter__()

        assert isinstance(cursor, QueryCursor)
