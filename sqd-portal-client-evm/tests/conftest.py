import asyncio
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def sample_query():
    """A sample query for testing."""
    import sqd_portal_client_evm as sqd_client
    return sqd_client.Query.simple_block_range(1000, 2000)


@pytest.fixture
def sample_dataset():
    """A sample dataset for testing."""
    import sqd_portal_client_evm as sqd_client
    return sqd_client.Dataset.ETHEREUM


@pytest.fixture
def sample_address():
    """A sample Ethereum address for testing."""
    return "0x742d35Cc6634C0532925a3b8"


@pytest.fixture
def mock_response_data():
    """Sample response data for mocking."""
    return [
        {"id": 1, "data": "test1"},
        {"id": 2, "data": "test2"},
        {"id": 3, "data": "test3"}
    ]


@pytest.fixture
def mock_empty_response():
    """Empty response for testing."""
    return []


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_aiohttp_session():
    """Mock aiohttp session for async tests."""
    session = AsyncMock()
    return session
