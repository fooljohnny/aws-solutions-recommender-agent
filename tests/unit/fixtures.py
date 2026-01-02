"""Unit test fixtures with mock LLM, AWS, and storage services."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = Mock()
    client.chat.completions.create = Mock(return_value=Mock(
        choices=[Mock(message=Mock(content='{"requirements": []}'))]
    ))
    return client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    client = Mock()
    client.messages.create = Mock(return_value=Mock(
        content=[Mock(text='{"requirements": []}')]
    ))
    return client


@pytest.fixture
def mock_dynamodb_client():
    """Mock DynamoDB client."""
    client = Mock()
    client.get_table = Mock(return_value=Mock(
        get_item=Mock(return_value={"Item": {}}),
        put_item=Mock(return_value={}),
        query=Mock(return_value={"Items": []}),
    ))
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    client = Mock()
    client.get = Mock(return_value=None)
    client.set = Mock(return_value=True)
    client.ping = Mock(return_value=True)
    client.exists = Mock(return_value=False)
    client.client.incr = Mock(return_value=1)
    client.client.expire = Mock(return_value=True)
    return client


@pytest.fixture
def mock_pricing_client():
    """Mock AWS Pricing API client."""
    client = Mock()
    client.get_price = Mock(return_value={
        "price": 0.05,
        "currency": "USD",
        "unit": "per hour",
    })
    return client


@pytest.fixture
def sample_conversation_data() -> Dict[str, Any]:
    """Sample conversation data for testing."""
    return {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_at": "2025-01-27T10:00:00Z",
        "expires_at": "2025-02-26T10:00:00Z",
    }


@pytest.fixture
def sample_message_data() -> Dict[str, Any]:
    """Sample message data for testing."""
    return {
        "message_id": "660e8400-e29b-41d4-a716-446655440001",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "role": "user",
        "content": "我需要一个Web应用架构",
    }

