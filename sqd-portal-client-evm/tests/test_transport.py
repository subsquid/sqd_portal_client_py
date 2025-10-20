from unittest.mock import Mock, patch

import pytest

from sqd_portal_client_evm.transport import fetch_query_output


class TestFetchQueryOutput:
    """Test synchronous fetch_query_output function."""

    @patch("sqd_portal_client_evm.transport.requests.post")
    def test_fetch_query_output_success_json_lines(self, mock_post):
        """Test successful response with JSON lines."""
        # Mock response with JSON lines
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "item1"}\n{"data": "item2"}\n{"data": "item3"}'
        mock_post.return_value = mock_response

        result = fetch_query_output("https://test.com", '{"query": "test"}')

        assert len(result) == 3
        assert result[0] == {"data": "item1"}
        assert result[1] == {"data": "item2"}
        assert result[2] == {"data": "item3"}
        mock_post.assert_called_once()

    @patch("sqd_portal_client_evm.transport.requests.post")
    def test_fetch_query_output_success_single_json(self, mock_post):
        """Test successful response with single JSON object."""
        # Mock response with single JSON object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "single_item"}'
        mock_post.return_value = mock_response

        result = fetch_query_output("https://test.com", '{"query": "test"}')

        assert len(result) == 1
        assert result[0] == {"data": "single_item"}

    @patch("sqd_portal_client_evm.transport.requests.post")
    def test_fetch_query_output_empty_response(self, mock_post):
        """Test empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_post.return_value = mock_response

        result = fetch_query_output("https://test.com", '{"query": "test"}')

        assert result == []

    @patch("sqd_portal_client_evm.transport.requests.post")
    def test_fetch_query_output_whitespace_only_response(self, mock_post):
        """Test response with only whitespace."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "   \n\t  \n"
        mock_post.return_value = mock_response

        result = fetch_query_output("https://test.com", '{"query": "test"}')

        assert result == []

    @patch("sqd_portal_client_evm.transport.requests.post")
    def test_fetch_query_output_http_error(self, mock_post):
        """Test HTTP error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="API request failed with status 400"):
            fetch_query_output("https://test.com", '{"query": "test"}')

    @patch("sqd_portal_client_evm.transport.requests.post")
    def test_fetch_query_output_invalid_json_lines(self, mock_post):
        """Test invalid JSON lines response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "item1"}\ninvalid json\n{"data": "item3"}'
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to parse API response as JSON"):
            fetch_query_output("https://test.com", '{"query": "test"}')

    @patch("sqd_portal_client_evm.transport.requests.post")
    def test_fetch_query_output_invalid_single_json(self, mock_post):
        """Test invalid single JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "invalid json"
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to parse API response as JSON"):
            fetch_query_output("https://test.com", '{"query": "test"}')

    def test_fetch_query_output_request_headers(self):
        """Test that correct headers are sent."""
        with patch("sqd_portal_client_evm.transport.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"data": "test"}'
            mock_post.return_value = mock_response

            fetch_query_output("https://test.com", '{"query": "test"}')

            # Check that post was called with correct arguments
            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # Check URL and data
            assert call_args[0][0] == "https://test.com"
            assert call_args[1]["data"] == '{"query": "test"}'

            # Check headers
            headers = call_args[1]["headers"]
            assert headers["Content-Type"] == "application/json"
            assert headers["User-Agent"] == "sqd_portal_client_py/0"


class TestFetchQueryOutputAsync:
    """Test asynchronous fetch_query_output_async function."""

    def test_fetch_query_output_async_structure(self):
        """Test that the async function exists and has correct signature."""
        import inspect
        from sqd_portal_client_evm.transport import fetch_query_output_async

        sig = inspect.signature(fetch_query_output_async)
        params = list(sig.parameters.keys())

        # Should have portal_endpoint_url, query, and optional session
        assert "portal_endpoint_url" in params
        assert "query" in params
        assert "session" in params

        # Should be an async function
        assert inspect.iscoroutinefunction(fetch_query_output_async)
