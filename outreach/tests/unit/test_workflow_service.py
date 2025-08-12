"""Minimal unit test for WorkflowService using mocks."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

class MockWorkflowStep:
    def __init__(self, step_id, action):
        self.step_id = step_id
        self.action = action
        self.transitions = []  # Add missing attribute

class MockWorkflow:
    def __init__(self, steps):
        self.steps = steps

try:
    from src.services.workflow_service import WorkflowService, WorkflowExecutionError
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
    from src.services.workflow_service import WorkflowService, WorkflowExecutionError

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

class MockWorkflowStep:
    def __init__(self, step_id, action):
        self.step_id = step_id
        self.action = action
        self.transitions = []

class MockWorkflow:
    def __init__(self, steps):
        self.steps = steps

WorkflowService = None
try:
    from src.services.workflow_service import WorkflowService
except Exception:
    pass

@pytest.mark.asyncio
async def test_execute_step_success():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    step = MockWorkflowStep("start", {"type": "send_message", "content": "Hello!"})
    workflow = MockWorkflow([step])
    mock_repo.get.return_value = workflow
    service = WorkflowService(mock_repo)
    service._execute_action = AsyncMock(return_value={"message": "Hello!"})
    template_config = {"stages": [
        {"id": "start", "type": "message", "message": "Hello!"}
    ]}
    result = await service.execute_step(uuid4(), "start", {"template_config": template_config})
    assert result is not None
    assert result['result'] == {'message': 'Hello!', 'status': 'message_sent'}

@pytest.mark.asyncio
async def test_execute_step_missing_workflow():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    mock_repo.get.return_value = None
    service = WorkflowService(mock_repo)
    with pytest.raises(Exception):
        await service.execute_step(uuid4(), "start", {})

@pytest.mark.asyncio
async def test_execute_step_missing_step():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    workflow = MockWorkflow([])
    mock_repo.get.return_value = workflow
    service = WorkflowService(mock_repo)
    with pytest.raises(Exception):
        await service.execute_step(uuid4(), "missing", {})

@pytest.mark.asyncio
async def test_execute_step_action_error():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    step = MockWorkflowStep("start", {"type": "send_message"})
    workflow = MockWorkflow([step])
    mock_repo.get.return_value = workflow
    service = WorkflowService(mock_repo)
    service._execute_action = AsyncMock(side_effect=Exception("Action error"))
    with pytest.raises(Exception):
        await service.execute_step(uuid4(), "start", {})

@pytest.mark.asyncio
async def test_execute_step_missing_action():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    step = MockWorkflowStep("start", None)
    workflow = MockWorkflow([step])
    mock_repo.get.return_value = workflow
    service = WorkflowService(mock_repo)
    with pytest.raises(Exception):
        await service.execute_step(uuid4(), "start", {})

@pytest.mark.asyncio
async def test_execute_step_with_transitions():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    step = MockWorkflowStep("start", {"type": "send_message"})
    step.transitions = ["next"]
    next_step = MockWorkflowStep("next", {"type": "noop"})
    workflow = MockWorkflow([step, next_step])
    mock_repo.get.return_value = workflow
    service = WorkflowService(mock_repo)
    service._execute_action = AsyncMock(return_value={"message": "ok"})
    template_config = {"stages": [
        {"id": "start", "type": "message", "message": "ok", "next_stage_id": "next"},
        {"id": "next", "type": "noop"}
    ]}
    result = await service.execute_step(uuid4(), "start", {"template_config": template_config})
    assert result['success'] is True
    assert result['next_step_id'] == "next"
    assert result['result'] == {"message": "ok", "status": "message_sent"}

@pytest.mark.asyncio
async def test_execute_step_empty_transitions():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    step = MockWorkflowStep("start", {"type": "noop"})
    step.transitions = []
    workflow = MockWorkflow([step])
    mock_repo.get.return_value = workflow
    service = WorkflowService(mock_repo)
    service._execute_action = AsyncMock(return_value={"message": "Done"})
    template_config = {"stages": [
        {"id": "start", "type": "message", "message": "Done", "next_stage_id": None}
    ]}
    result = await service.execute_step(uuid4(), "start", {"template_config": template_config})
    assert result['success'] is True
    assert result['next_step_id'] is None
    assert result['result'] == {'message': 'Done', 'status': 'message_sent'}

@pytest.mark.asyncio
async def test_execute_step_repo_exception():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    mock_repo.get.side_effect = Exception("Repo error")
    service = WorkflowService(mock_repo)
    with pytest.raises(Exception):
        await service.execute_step(uuid4(), "start", {})

@pytest.mark.asyncio
async def test_execute_step_with_extra_context():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    step = MockWorkflowStep("start", {"type": "send_message"})
    workflow = MockWorkflow([step])
    mock_repo.get.return_value = workflow
    service = WorkflowService(mock_repo)
    service._execute_action = AsyncMock(return_value={"message": "ok"})
    template_config = {"stages": [
        {"id": "start", "type": "message", "message": "ok"}
    ]}
    context = {"foo": "bar", "baz": 123, "template_config": template_config}
    result = await service.execute_step(uuid4(), "start", context)
    assert result['success'] is True
    assert result['result']['message'] == "ok"

@pytest.mark.asyncio
async def test_execute_step_invalid_action_type():
    if WorkflowService is None:
        pytest.skip("WorkflowService not available")
    mock_repo = AsyncMock()
    step = MockWorkflowStep("start", {"type": "unknown_action"})
    workflow = MockWorkflow([step])
    mock_repo.get.return_value = workflow
    service = WorkflowService(mock_repo)
    service._execute_action = AsyncMock(side_effect=Exception("Invalid action type"))
    with pytest.raises(Exception):
        await service.execute_step(uuid4(), "start", {})
