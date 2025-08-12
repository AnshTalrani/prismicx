"""Unit tests for the WorkflowRepository using real ORM model and schemas."""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import Workflow
from src.models.schemas import WorkflowCreate, WorkflowDefinition
from src.repositories.workflow_repository import WorkflowRepository

@pytest.mark.asyncio
async def test_create_workflow(monkeypatch):
    db_session = AsyncMock(spec=AsyncSession)
    repo = WorkflowRepository(db_session)
    workflow_create = WorkflowCreate(
        name="Test Workflow",
        description="A test workflow",
        definition=WorkflowDefinition(
            name="Test Workflow",
            description="A test definition",
            version="1.0",
            start_node_id="start",
            nodes={}
        ),
        is_active=True
    )
    # Patch model to skip actual DB
    monkeypatch.setattr(repo, "model", Workflow)
    monkeypatch.setattr(db_session, "add", AsyncMock())
    monkeypatch.setattr(db_session, "commit", AsyncMock())
    monkeypatch.setattr(db_session, "refresh", AsyncMock())
    workflow_obj = Workflow(
        id=uuid4(),
        name=workflow_create.name,
        description=workflow_create.description,
        definition=workflow_create.definition.dict(),
        version=1,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    monkeypatch.setattr(repo, "model", lambda **kwargs: workflow_obj)
    result = await repo.create(workflow_create)
    assert result.name == "Test Workflow"
    assert result.is_active is True
    assert result.version == 1

@pytest.mark.asyncio
async def test_get_workflow(monkeypatch):
    db_session = AsyncMock(spec=AsyncSession)
    repo = WorkflowRepository(db_session)
    workflow_id = uuid4()
    workflow_obj = Workflow(
        id=workflow_id,
        name="Test Workflow",
        description="A test workflow",
        definition={},
        version=1,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    class Result:
        def scalars(self):
            class S:
                def first(self_inner):
                    return workflow_obj
            return S()
    monkeypatch.setattr(db_session, "execute", AsyncMock(return_value=Result()))
    result = await repo.get(workflow_id)
    assert result.id == workflow_id
    assert result.name == "Test Workflow"
