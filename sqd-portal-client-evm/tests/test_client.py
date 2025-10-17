from unittest.mock import patch

import pytest

import sqd_portal_client_evm as sqd_client
from sqd_portal_client_evm.client import (
    get_data, get_data_async, get_multiple_data, get_multiple_data_async,
    chain_queries, chain_queries_async, combine_query_results,
    filter_combined_results, QueryChain, validate_query_format
)


class TestGetData:
    """Test synchronous get_data function."""

    @patch('sqd_portal_client_evm.client.fetch_query_output')
    def test_get_data_with_query_object(self, mock_fetch):
        """Test get_data with Query object."""
        mock_fetch.return_value = [{"data": "test"}]

        query = sqd_client.Query.simple_block_range(1000, 2000)
        result = get_data(
            dataset=sqd_client.Dataset.ETHEREUM,
            query=query,
            portal_url="https://test.com"
        )

        assert result == [{"data": "test"}]
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args[0]
        assert sqd_client.Dataset.ETHEREUM.value in call_args[0]  # endpoint URL
        assert '"fromBlock":1000' in call_args[1]  # query string

    @patch('sqd_portal_client_evm.client.fetch_query_output')
    def test_get_data_with_query_string(self, mock_fetch):
        """Test get_data with query string."""
        mock_fetch.return_value = [{"data": "test"}]

        query_str = '{"type": "evm", "fromBlock": 1000}'
        result = get_data(
            dataset=sqd_client.Dataset.ETHEREUM,
            query=query_str,
            portal_url="https://test.com"
        )

        assert result == [{"data": "test"}]
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args[0]
        assert call_args[1] == query_str

    @patch('sqd_portal_client_evm.client.fetch_query_output')
    def test_get_data_with_flattening(self, mock_fetch):
        """Test get_data with custom flattening."""
        mock_fetch.return_value = [{"data": "test"}]

        query = sqd_client.Query.simple_block_range(1000, 2000)
        result = get_data(
            dataset=sqd_client.Dataset.ETHEREUM,
            query=query,
            flattening="by_transaction"
        )

        assert result == [{"data": "test"}]
        # Verify that flattening parameter is passed through in endpoint URL
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args[0]
        assert sqd_client.Dataset.ETHEREUM.value in call_args[0]

    @patch('sqd_portal_client_evm.client.fetch_query_output')
    def test_get_data_fetch_error_propagation(self, mock_fetch):
        """Test that fetch errors are properly propagated."""
        mock_fetch.side_effect = ValueError("API request failed")

        query = sqd_client.Query.simple_block_range(1000, 2000)

        with pytest.raises(ValueError, match="Failed to execute query: API request failed"):
            get_data(dataset=sqd_client.Dataset.ETHEREUM, query=query)

    @patch('sqd_portal_client_evm.client.fetch_query_output')
    def test_get_data_default_portal_url(self, mock_fetch):
        """Test get_data with default portal URL."""
        mock_fetch.return_value = []

        query = sqd_client.Query.simple_block_range(1000, 2000)
        result = get_data(dataset=sqd_client.Dataset.ETHEREUM, query=query)

        assert result == []
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args[0]
        assert "portal.sqd.dev" in call_args[0]


class TestGetDataAsync:
    """Test asynchronous get_data_async function."""

    def test_get_data_async_structure(self):
        """Test that get_data_async function exists and has correct signature."""
        import inspect

        sig = inspect.signature(get_data_async)
        params = list(sig.parameters.keys())

        # Should have same params as get_data plus session
        assert 'dataset' in params
        assert 'query' in params
        assert 'portal_url' in params
        assert 'flattening' in params
        assert 'session' in params

        # Should be an async function
        assert inspect.iscoroutinefunction(get_data_async)


class TestGetMultipleData:
    """Test get_multiple_data function."""

    @patch('sqd_portal_client_evm.client.get_data')
    def test_get_multiple_data_sequential(self, mock_get_data):
        """Test get_multiple_data executes queries sequentially."""
        mock_get_data.side_effect = [
            [{"data": "result1"}],
            [{"data": "result2"}],
            [{"data": "result3"}]
        ]

        queries = [
            (sqd_client.Dataset.ETHEREUM, sqd_client.Query.simple_block_range(1000, 1100)),
            (sqd_client.Dataset.ETHEREUM, sqd_client.Query.simple_block_range(1100, 1200)),
            (sqd_client.Dataset.ETHEREUM, sqd_client.Query.simple_block_range(1200, 1300))
        ]

        results = get_multiple_data(queries, portal_url="https://test.com")

        assert len(results) == 3
        assert results[0] == [{"data": "result1"}]
        assert results[1] == [{"data": "result2"}]
        assert results[2] == [{"data": "result3"}]

        # Verify get_data was called 3 times
        assert mock_get_data.call_count == 3


class TestGetMultipleDataAsync:
    """Test get_multiple_data_async function."""

    def test_get_multiple_data_async_structure(self):
        """Test that get_multiple_data_async function exists and has correct signature."""
        import inspect

        sig = inspect.signature(get_multiple_data_async)
        params = list(sig.parameters.keys())

        # Should have queries, portal_url, flattening, session, max_concurrency
        assert 'queries' in params
        assert 'portal_url' in params
        assert 'flattening' in params
        assert 'session' in params
        assert 'max_concurrency' in params

        # Should be an async function
        assert inspect.iscoroutinefunction(get_multiple_data_async)


class TestChainQueries:
    """Test chain_queries function."""

    @patch('sqd_portal_client_evm.client.get_multiple_data')
    def test_chain_queries_same_dataset(self, mock_get_multiple_data):
        """Test chain_queries with same dataset for all queries."""
        mock_get_multiple_data.return_value = [
            [{"data": "result1"}],
            [{"data": "result2"}]
        ]

        queries = [
            sqd_client.Query.simple_block_range(1000, 1100),
            sqd_client.Query.simple_block_range(1100, 1200)
        ]

        results = chain_queries(
            queries,
            sqd_client.Dataset.ETHEREUM,
            portal_url="https://test.com"
        )

        assert len(results) == 2
        mock_get_multiple_data.assert_called_once()

        # Verify that queries were converted to tuples with the dataset
        call_args = mock_get_multiple_data.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0][0] == sqd_client.Dataset.ETHEREUM
        assert call_args[1][0] == sqd_client.Dataset.ETHEREUM


class TestChainQueriesAsync:
    """Test chain_queries_async function."""

    def test_chain_queries_async_structure(self):
        """Test that chain_queries_async function exists and has correct signature."""
        import inspect

        sig = inspect.signature(chain_queries_async)
        params = list(sig.parameters.keys())

        # Should have queries, dataset, portal_url, flattening, session, max_concurrency
        assert 'queries' in params
        assert 'dataset' in params
        assert 'portal_url' in params
        assert 'flattening' in params
        assert 'session' in params
        assert 'max_concurrency' in params

        # Should be an async function
        assert inspect.iscoroutinefunction(chain_queries_async)


class TestCombineQueryResults:
    """Test combine_query_results function."""

    def test_combine_concatenate(self):
        """Test concatenate strategy."""
        results = [
            [{"id": 1}, {"id": 2}],
            [{"id": 3}],
            [{"id": 4}, {"id": 5}, {"id": 6}]
        ]

        combined = combine_query_results(results, "concatenate")

        expected = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}, {"id": 6}]
        assert combined == expected

    def test_combine_merge(self):
        """Test merge strategy."""
        results = [
            [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}],
            [{"id": 1, "value": "updated_a"}, {"id": 3, "value": "c"}]
        ]

        combined = combine_query_results(results, "merge")

        # Should have 3 unique items (id 1 is overwritten)
        assert len(combined) == 3
        assert {"id": 1, "value": "updated_a"} in combined
        assert {"id": 2, "value": "b"} in combined
        assert {"id": 3, "value": "c"} in combined

    def test_combine_zip(self):
        """Test zip strategy."""
        results = [
            [{"id": 1}, {"id": 2}, {"id": 3}],
            [{"value": "a"}, {"value": "b"}, {"value": "c"}]
        ]

        combined = combine_query_results(results, "zip")

        expected = [
            [{"id": 1}, {"value": "a"}],
            [{"id": 2}, {"value": "b"}],
            [{"id": 3}, {"value": "c"}]
        ]
        assert combined == expected

    def test_combine_zip_unequal_lengths(self):
        """Test zip strategy with unequal list lengths."""
        results = [
            [{"id": 1}, {"id": 2}],
            [{"value": "a"}, {"value": "b"}, {"value": "c"}]
        ]

        combined = combine_query_results(results, "zip")

        expected = [
            [{"id": 1}, {"value": "a"}],
            [{"id": 2}, {"value": "b"}],
            [None, {"value": "c"}]
        ]
        assert combined == expected

    def test_combine_unknown_strategy(self):
        """Test unknown combine strategy raises error."""
        results = [[{"id": 1}]]

        with pytest.raises(ValueError, match="Unknown combine strategy"):
            combine_query_results(results, "unknown_strategy")


class TestFilterCombinedResults:
    """Test filter_combined_results function."""

    def test_filter_no_filters(self):
        """Test filtering with no filters returns original results."""
        results = [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}]

        filtered = filter_combined_results(results)

        assert filtered == results

    def test_filter_matching_criteria(self):
        """Test filtering with matching criteria."""
        results = [
            {"id": 1, "value": "a", "type": "test"},
            {"id": 2, "value": "b", "type": "other"},
            {"id": 3, "value": "c", "type": "test"}
        ]

        filters = {"type": "test"}
        filtered = filter_combined_results(results, filters)

        expected = [
            {"id": 1, "value": "a", "type": "test"},
            {"id": 3, "value": "c", "type": "test"}
        ]
        assert filtered == expected

    def test_filter_no_matches(self):
        """Test filtering with no matching criteria."""
        results = [
            {"id": 1, "value": "a", "type": "test"},
            {"id": 2, "value": "b", "type": "other"}
        ]

        filters = {"type": "nonexistent"}
        filtered = filter_combined_results(results, filters)

        assert filtered == []

    def test_filter_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        results = [
            {"id": 1, "value": "a", "type": "test", "status": "active"},
            {"id": 2, "value": "b", "type": "test", "status": "inactive"},
            {"id": 3, "value": "c", "type": "other", "status": "active"}
        ]

        filters = {"type": "test", "status": "active"}
        filtered = filter_combined_results(results, filters)

        expected = [{"id": 1, "value": "a", "type": "test", "status": "active"}]
        assert filtered == expected


class TestQueryChain:
    """Test QueryChain class."""

    def test_query_chain_creation(self):
        """Test QueryChain creation."""
        chain = QueryChain(sqd_client.Dataset.ETHEREUM)

        assert chain.dataset == sqd_client.Dataset.ETHEREUM
        assert chain.portal_url == "https://portal.sqd.dev"
        assert len(chain.queries) == 0

    def test_query_chain_with_custom_url(self):
        """Test QueryChain with custom portal URL."""
        chain = QueryChain(sqd_client.Dataset.ETHEREUM, "https://custom.sqd.dev")

        assert chain.portal_url == "https://custom.sqd.dev"

    def test_query_chain_add_queries(self):
        """Test adding queries to chain."""
        chain = QueryChain(sqd_client.Dataset.ETHEREUM)

        query1 = sqd_client.Query.simple_block_range(1000, 1100)
        query2 = sqd_client.Query.simple_block_range(1100, 1200)

        chain.add(query1).add(query2)

        assert len(chain.queries) == 2
        assert chain.queries[0] == query1
        assert chain.queries[1] == query2

    @patch('sqd_portal_client_evm.client.chain_queries')
    def test_query_chain_execute(self, mock_chain_queries):
        """Test QueryChain execute method."""
        mock_chain_queries.return_value = [{"data": "result"}]

        chain = QueryChain(sqd_client.Dataset.ETHEREUM)
        chain.add(sqd_client.Query.simple_block_range(1000, 1100))

        result = chain.execute(flattening="by_transaction")

        assert result == [{"data": "result"}]
        mock_chain_queries.assert_called_once_with(
            chain.queries,
            chain.dataset,
            chain.portal_url,
            "by_transaction"
        )

    def test_query_chain_execute_async_structure(self):
        """Test that QueryChain execute_async method exists and is async."""
        import inspect

        chain = QueryChain(sqd_client.Dataset.ETHEREUM)
        execute_async_method = getattr(chain, 'execute_async')

        # Should be an async method
        assert inspect.iscoroutinefunction(execute_async_method)


class TestValidateQueryFormat:
    """Test validate_query_format function."""

    def test_validate_query_format_valid_query_object(self):
        """Test validating a valid Query object."""
        query = sqd_client.Query.simple_block_range(1000, 2000)
        is_valid, message = validate_query_format(query)

        assert is_valid is True
        assert message == "Query format looks valid"

    def test_validate_query_format_valid_query_string(self):
        """Test validating a valid query string."""
        query_str = '{"type": "evm", "fromBlock": 1000, "toBlock": 2000, "fields": {}}'
        is_valid, message = validate_query_format(query_str)

        assert is_valid is True
        assert message == "Query format looks valid"

    def test_validate_query_format_invalid_json(self):
        """Test validating invalid JSON."""
        query_str = '{"type": "evm", invalid json}'
        is_valid, message = validate_query_format(query_str)

        assert is_valid is False
        assert "Invalid JSON format" in message

    def test_validate_query_format_missing_type(self):
        """Test validating query without type field."""
        query_str = '{"fromBlock": 1000}'
        is_valid, message = validate_query_format(query_str)

        assert is_valid is False
        assert "Query content should have 'type' field" in message

    def test_validate_query_format_wrong_type(self):
        """Test validating query with wrong type."""
        query_str = '{"type": "solana", "fromBlock": 1000}'
        is_valid, message = validate_query_format(query_str)

        assert is_valid is False
        assert "Expected type 'evm', got 'solana'" in message

    def test_validate_query_format_invalid_query_object(self):
        """Test validating Query object that raises exception."""

        # Create a mock Query that raises an exception during serialization
        class BadQuery:
            def to_sqd_string(self):
                raise ValueError("Bad query")

        is_valid, message = validate_query_format(BadQuery())

        assert is_valid is False
        assert "Query validation failed" in message
