"""Contract tests for API schema validation."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_openapi_schema_exists():
    """Test that OpenAPI schema is generated."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema


def test_conversation_endpoint_schema():
    """Test conversation endpoint schema."""
    response = client.get("/openapi.json")
    schema = response.json()
    
    # Check POST /conversations exists
    assert "/v1/conversations" in schema["paths"]
    assert "post" in schema["paths"]["/v1/conversations"]
    
    # Check response schema
    post_schema = schema["paths"]["/v1/conversations"]["post"]
    assert "responses" in post_schema
    assert "201" in post_schema["responses"]


def test_message_endpoint_schema():
    """Test message endpoint schema."""
    response = client.get("/openapi.json")
    schema = response.json()
    
    # Check POST /conversations/{session_id}/messages exists
    assert "/v1/conversations/{session_id}/messages" in schema["paths"]
    assert "post" in schema["paths"]["/v1/conversations/{session_id}/messages"]

