import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app

client = TestClient(app)


@pytest.fixture
def mock_bot_handler():
    """Mock consultancy bot handler."""
    handler = AsyncMock()
    handler.handle_request = AsyncMock(return_value={
        "session_id": "test_session",
        "user_id": "test_user",
        "content": "Test response",
        "status": "success"
    })
    handler.handle_notification = AsyncMock(return_value={
        "session_id": "test_session",
        "status": "acknowledged",
        "notification_type": "test"
    })
    return handler


def test_bot_request_endpoint(mock_bot_handler, monkeypatch):
    """Test the bot request endpoint."""
    # Mock the dependency and ensure it returns the expected response
    mock_bot_handler.handle_request.return_value = {
        "session_id": "test_session",
        "user_id": "test_user",
        "content": "Test response",
        "status": "success"
    }
    
    # Mock the dependencies module to return our mock
    monkeypatch.setattr("src.api.dependencies._consultancy_bot_handler", mock_bot_handler)
    
    response = client.post("/bot/request", json={
        "text": "Hello, I need help",
        "user_id": "test_user",
        "session_id": "test_session",
        "urgency": "normal"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session"
    assert data["user_id"] == "test_user"
    assert data["status"] == "success"


def test_bot_notification_endpoint(mock_bot_handler, monkeypatch):
    """Test the bot notification endpoint."""
    # Mock the dependency and ensure it returns the expected response
    mock_bot_handler.handle_notification.return_value = {
        "session_id": "test_session",
        "status": "acknowledged",
        "notification_type": "message_received"
    }
    
    # Mock the dependencies module to return our mock
    monkeypatch.setattr("src.api.dependencies._consultancy_bot_handler", mock_bot_handler)
    
    response = client.post("/bot/notification", json={
        "session_id": "test_session",
        "user_id": "test_user",
        "notification_type": "message_received",
        "data": {"message": "test"}
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session"
    assert data["status"] == "acknowledged"


def test_bot_request_missing_fields():
    """Test bot request with missing required fields."""
    response = client.post("/bot/request", json={
        "text": "Hello"
        # Missing user_id and session_id
    })
    
    assert response.status_code == 422  # Validation error


def test_bot_notification_missing_fields():
    """Test bot notification with missing required fields."""
    response = client.post("/bot/notification", json={
        "session_id": "test_session"
        # Missing user_id and notification_type
    })
    
    assert response.status_code == 422  # Validation error
