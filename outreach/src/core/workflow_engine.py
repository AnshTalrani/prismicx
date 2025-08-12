"""
Workflow Engine

Manages the execution of conversation workflows with state management
and decision tree navigation.
"""
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from enum import Enum
import json
import yaml
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowStepType(str, Enum):
    MESSAGE = "message"
    INPUT = "input"
    DECISION = "decision"
    ACTION = "action"

class WorkflowStep(BaseModel):
    step_id: str
    step_type: WorkflowStepType
    config: Dict[str, Any] = {}
    next_steps: List[Dict[str, str]] = []

class WorkflowExecution(BaseModel):
    execution_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    current_step_id: str
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    context: Dict[str, Any] = {}

class WorkflowEngine:
    """Manages workflow execution and state transitions."""
    
    def __init__(self, workflow_repository):
        self.workflow_repo = workflow_repository
        self._executions = {}
    
    async def start_execution(self, workflow_id: UUID, context: dict = None) -> WorkflowExecution:
        """Start a new workflow execution."""
        workflow = await self.workflow_repo.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            current_step_id=workflow['start_step'],
            context=context or {}
        )
        
        self._executions[execution.execution_id] = execution
        return execution
    
    async def execute_step(self, execution_id: UUID, step_input: dict = None) -> dict:
        """Execute the current step in a workflow execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
            
        workflow = await self.workflow_repo.get(execution.workflow_id)
        step = workflow['steps'].get(execution.current_step_id)
        
        if not step:
            execution.status = WorkflowStatus.FAILED
            raise ValueError(f"Step {execution.current_step_id} not found")
        
        # Process the step
        handler = getattr(self, f"_handle_{step.step_type}_step", None)
        if not handler:
            raise ValueError(f"No handler for step type: {step.step_type}")
            
        result = await handler(step, execution, step_input or {})
        
        # Update execution state
        execution.context.update(result.get('context_updates', {}))
        
        # Handle step transition
        if result.get('next_step_id'):
            execution.current_step_id = result['next_step_id']
        elif not result.get('is_complete', False):
            execution.status = WorkflowStatus.COMPLETED
            
        return {
            'status': execution.status,
            'current_step': execution.current_step_id,
            'output': result.get('output', {})
        }
    
    async def _handle_message_step(self, step: WorkflowStep, execution: WorkflowExecution, step_input: dict) -> dict:
        """Handle a message step."""
        return {
            'output': {'message': step.config.get('content', '')},
            'next_step_id': self._get_next_step(step, {})
        }
    
    async def _handle_decision_step(self, step: WorkflowStep, execution: WorkflowExecution, step_input: dict) -> dict:
        """Handle a decision step."""
        condition = step.config.get('condition')
        if condition and eval(condition, {}, execution.context):
            return {'next_step_id': step.config.get('true_step')}
        return {'next_step_id': step.config.get('false_step')}
    
    def _get_next_step(self, step: WorkflowStep, context: dict) -> Optional[str]:
        """Determine the next step based on conditions."""
        for transition in step.next_steps:
            if not transition.get('condition') or eval(transition['condition'], {}, context):
                return transition['next_step_id']
        return None
