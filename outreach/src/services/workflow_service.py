"""
Workflow Service

Manages the execution of conversation workflows and decision trees.
"""
import json
from typing import Dict, Any, Optional, List
from uuid import UUID

from ..models.workflow import Workflow, WorkflowStep, WorkflowStatus
from ..repositories.workflow_repository import WorkflowRepository

class WorkflowExecutionError(Exception):
    """Exception raised for errors in workflow execution."""
    pass

class WorkflowService:
    """Service for managing workflow execution and state."""
    
    def __init__(self, workflow_repository: WorkflowRepository):
        self.workflow_repo = workflow_repository
    
    async def execute_step(self, workflow_id: UUID, step_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific step in a workflow, using the template config for dynamic logic.
        """
        template_config = context.get('template_config')
        if not template_config:
            raise WorkflowExecutionError("No template_config found in context")
        # Find the stage in the template config matching step_id
        stages = template_config.get('stages', [])
        stage = next((s for s in stages if s.get('id') == step_id), None)
        if not stage:
            raise WorkflowExecutionError(f"Stage {step_id} not found in template config")
        # Handle the stage type (message, input, decision, etc.)
        stage_type = stage.get('type', 'message')
        if stage_type == 'message':
            # Send message using template
            msg = stage.get('message', '').format(**context)
            result = await self._handle_send_message({'content': msg}, context)
        elif stage_type == 'input':
            # Collect input (simulate or integrate with input handler)
            result = await self._handle_collect_input({'prompt': stage.get('prompt', '')}, context)
        elif stage_type == 'decision':
            # Evaluate decision/branching logic
            decision = stage.get('decision', {})
            result = await self._handle_decision(decision, context)
        else:
            raise WorkflowExecutionError(f"Unknown stage type: {stage_type}")
        # Determine next step from template decision tree
        next_stage = None
        if stage_type == 'decision':
            # Use decision tree branching
            branches = stage.get('branches', [])
            for branch in branches:
                condition = branch.get('condition')
                try:
                    if condition is None or eval(condition, {}, {**context, **result}):
                        next_stage = branch.get('next_stage_id')
                        break
                except Exception:
                    continue
        else:
            # Default to next_stage_id if present
            next_stage = stage.get('next_stage_id')
        return {
            'success': True,
            'result': result,
            'next_step_id': next_stage,
            'updated_context': context
        }
    
    async def _execute_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a workflow action with the given context."""
        action_type = action.get('type')
        
        # This is a simplified example - in a real implementation, you would have
        # specific handlers for different action types
        if action_type == 'send_message':
            return await self._handle_send_message(action, context)
        elif action_type == 'collect_input':
            return await self._handle_collect_input(action, context)
        elif action_type == 'make_decision':
            return await self._handle_decision(action, context)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    async def _handle_send_message(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send message action."""
        # In a real implementation, this would integrate with a messaging service
        return {
            'status': 'message_sent',
            'message': action.get('content', '').format(**context)
        }
    
    async def _handle_collect_input(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collect input action."""
        # In a real implementation, this would wait for and process user input
        return {
            'status': 'input_received',
            'input': context.get('user_input', '')
        }
    
    async def _handle_decision(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle decision point in workflow."""
        # Simple condition evaluation - in a real implementation, use a proper expression evaluator
        condition = action.get('condition', '')
        try:
            result = eval(condition, {}, context)
            return {
                'status': 'decision_made',
                'result': bool(result)
            }
        except Exception as e:
            raise WorkflowExecutionError(f"Error evaluating condition: {str(e)}")
    
    def _determine_next_step(self, current_step: WorkflowStep, result: Dict[str, Any], context: Dict[str, Any] = None) -> Optional[str]:
        """Determine the next step based on the current step's result and context."""
        if not current_step.transitions:
            return None
        # Support both string ("next_step_id") and dict ({'next_step_id': ..., 'condition': ...}) transitions
        for transition in current_step.transitions:
            if isinstance(transition, str):
                return transition  # Just the next step id
            elif isinstance(transition, dict):
                eval_context = dict(result)
                if context:
                    eval_context.update(context)
                if transition.get('condition') is None or eval(transition['condition'], {}, eval_context):
                    return transition['next_step_id']
        return None
