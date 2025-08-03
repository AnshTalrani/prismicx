"""Pytest configuration for Agent microservice tests.
Ensures that the `src` package (microservice source) is importable when tests
are executed from the project root or any sub-directory.
"""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

# Calculate path to microservices/agent/src directory (two levels up from tests/)
SRC_DIR = Path(__file__).resolve().parents[2] / "src"

# Prepend to sys.path if not already present
if SRC_DIR.exists() and SRC_DIR.is_dir():
    sys.path.insert(0, str(SRC_DIR))

# Set test environment variables to avoid database connections
os.environ["USER_DB_HOST"] = "localhost"
os.environ["USER_DB_PORT"] = "5432"
os.environ["USER_DB_USER"] = "test_user"
os.environ["USER_DB_PASSWORD"] = "test_password"
os.environ["USER_DB_NAME"] = "test_db"
os.environ["TASK_REPOSITORY_URL"] = "http://localhost:8080"
os.environ["TASK_REPOSITORY_API_KEY"] = "test_key"
os.environ["CONFIG_SERVICE_URL"] = "http://localhost:8000"
os.environ["CONFIG_SERVICE_API_KEY"] = "test_key"


@pytest.fixture
def mock_user_repository():
    """Mock user repository to avoid database connections."""
    mock_repo = AsyncMock()
    mock_repo.validate_user_exists = AsyncMock(return_value=True)
    mock_repo.get_user = AsyncMock(return_value=MagicMock(id="test_user", name="Test User"))
    mock_repo.initialize = AsyncMock()
    mock_repo.close = AsyncMock()
    return mock_repo


@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch, mock_user_repository):
    """Auto-mock dependencies to avoid external service calls."""
    # Mock user repository in dependencies
    monkeypatch.setattr("src.api.dependencies._user_repository", mock_user_repository)
    
    # Mock database connections
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr("asyncpg.create_pool", AsyncMock(return_value=mock_pool))
    
    # Mock user repository initialization to avoid connection errors
    monkeypatch.setattr("src.infrastructure.repositories.user_repository.UserRepository.initialize", AsyncMock())
    monkeypatch.setattr("src.infrastructure.repositories.user_repository.UserRepository.validate_user_exists", AsyncMock(return_value=True))
