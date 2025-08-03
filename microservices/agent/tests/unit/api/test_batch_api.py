import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app

client = TestClient(app)


@pytest.fixture
def mock_batch_processor():
    """Mock batch processor."""
    processor = MagicMock()
    processor.request_service = AsyncMock()
    processor.request_service.process_batch = AsyncMock(return_value={
        "status": "created",
        "batch_id": "test_batch_123"
    })
    # Return the exact structure expected by the API
    processor.get_batch_status = AsyncMock(return_value={
        "batch_id": "test_batch_123",
        "status": "completed",
        "items_processed": 5,
        "items_total": 5
    })
    return processor


def test_create_matrix_batch(mock_batch_processor, monkeypatch):
    """Test creating a matrix batch."""
    # Mock the BatchRequest.create_from_components method
    from unittest.mock import patch, MagicMock
    mock_batch_request = MagicMock()
    mock_batch_request.id = "test_batch_123"
    
    with patch('src.domain.entities.request.BatchRequest.create_from_components', return_value=mock_batch_request):
        monkeypatch.setattr("src.api.dependencies.get_batch_processor", lambda: mock_batch_processor)
        
        response = client.post("/api/batch/matrix", json={
            "source": "test_source",
            "template_id": "test_template",
            "items": [{"id": "1"}, {"id": "2"}],
            "processing_method": "individual",
            "data_source_type": "users",
            "metadata": {"test": "data"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert data["status"] == "created"


def test_create_user_batch(mock_batch_processor, monkeypatch):
    """Test creating a user batch."""
    from unittest.mock import patch, MagicMock
    mock_batch_request = MagicMock()
    mock_batch_request.id = "test_batch_123"
    
    with patch('src.domain.entities.request.BatchRequest.create_user_batch', return_value=mock_batch_request):
        monkeypatch.setattr("src.api.dependencies.get_batch_processor", lambda: mock_batch_processor)
        
        response = client.post("/api/batch/user_batch", json={
            "source": "test_source",
            "template_id": "test_template",
            "items": [{"user_id": "1"}, {"user_id": "2"}],
            "metadata": {"test": "data"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert data["status"] == "created"


def test_create_category_batch(mock_batch_processor, monkeypatch):
    """Test creating a category batch."""
    from unittest.mock import patch, MagicMock
    mock_batch_request = MagicMock()
    mock_batch_request.id = "test_batch_123"
    
    with patch('src.domain.entities.request.BatchRequest.create_category_batch', return_value=mock_batch_request):
        monkeypatch.setattr("src.api.dependencies.get_batch_processor", lambda: mock_batch_processor)
        
        response = client.post("/api/batch/category_batch", json={
            "source": "test_source",
            "template_id": "test_template",
            "items": [{"category_id": "1"}, {"category_id": "2"}],
            "metadata": {"test": "data"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert data["status"] == "created"


def test_get_batch_status(mock_batch_processor, monkeypatch):
    """Test getting batch status."""
    # Mock the dependencies module to return our mock
    monkeypatch.setattr("src.api.dependencies._batch_processor", mock_batch_processor)
    
    response = client.get("/api/batch/status/test_batch_123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["batch_id"] == "test_batch_123"
    assert data["status"] == "completed"


def test_get_batch_status_not_found(mock_batch_processor, monkeypatch):
    """Test getting status for non-existent batch."""
    mock_batch_processor.get_batch_status = AsyncMock(return_value=None)
    # Mock the dependencies module to return our mock
    monkeypatch.setattr("src.api.dependencies._batch_processor", mock_batch_processor)
    
    response = client.get("/api/batch/status/nonexistent_batch")
    
    assert response.status_code == 404


def test_batch_request_missing_fields():
    """Test batch request with missing required fields."""
    response = client.post("/api/batch/matrix", json={
        "source": "test_source"
        # Missing template_id, items, data_source_type
    })
    
    assert response.status_code == 422  # Validation error
