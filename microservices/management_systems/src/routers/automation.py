"""
API router for automation functionality.
Provides endpoints for managing automation rules, triggers, and conditions.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..services.automation_service import get_automation_service
from ..automation.automation_engine import AutomationEngine

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])

# Request/Response models
class TriggerInfo(BaseModel):
    """Information about an available automation trigger."""
    id: str
    name: str
    description: str
    required_data: List[str] = []
    
class ConditionModel(BaseModel):
    """A condition for when an automation should run."""
    field: Optional[str] = None
    value: Optional[Any] = None
    operator: Optional[str] = "equals"
    type: str

class ActionModel(BaseModel):
    """An action to take when automation conditions are met."""
    type: str
    parameters: Dict[str, Any] = {}

class AutomationRuleCreate(BaseModel):
    """Request model for creating an automation rule."""
    name: str
    description: Optional[str] = None
    module_type: str
    trigger_id: str
    conditions: List[ConditionModel] = []
    actions: List[ActionModel] = []
    is_active: bool = True

class AutomationRuleResponse(BaseModel):
    """Response model for an automation rule."""
    id: str
    name: str
    description: Optional[str] = None
    module_type: str
    trigger_id: str
    conditions: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    is_active: bool
    created_at: str
    updated_at: str

@router.get("/triggers", response_model=List[TriggerInfo])
async def get_automation_triggers(
    module_type: Optional[str] = Query(None, description="Filter triggers by module type")
):
    """
    Get available automation triggers, optionally filtered by module type.
    """
    try:
        automation_service = get_automation_service()
        return automation_service.get_available_triggers(module_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve triggers: {str(e)}")

@router.post("/rules", response_model=AutomationRuleResponse)
async def create_automation_rule(rule: AutomationRuleCreate):
    """
    Create a new automation rule.
    """
    try:
        automation_service = get_automation_service()
        result = automation_service.create_automation_rule(
            name=rule.name,
            description=rule.description,
            module_type=rule.module_type,
            trigger_id=rule.trigger_id,
            conditions=[condition.dict() for condition in rule.conditions],
            actions=[action.dict() for action in rule.actions],
            is_active=rule.is_active
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create automation rule: {str(e)}")

@router.get("/rules", response_model=List[AutomationRuleResponse])
async def get_automation_rules(
    module_type: Optional[str] = Query(None, description="Filter rules by module type"),
    trigger_id: Optional[str] = Query(None, description="Filter rules by trigger ID"),
    is_active: Optional[bool] = Query(None, description="Filter rules by active status")
):
    """
    Get automation rules with optional filtering.
    """
    try:
        automation_service = get_automation_service()
        return automation_service.get_automation_rules(module_type, trigger_id, is_active)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve automation rules: {str(e)}")

@router.get("/rules/{rule_id}", response_model=AutomationRuleResponse)
async def get_automation_rule(rule_id: str = Path(..., description="The ID of the rule to retrieve")):
    """
    Get a specific automation rule by ID.
    """
    try:
        automation_service = get_automation_service()
        rule = automation_service.get_automation_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Automation rule {rule_id} not found")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve automation rule: {str(e)}")

@router.put("/rules/{rule_id}/toggle", response_model=AutomationRuleResponse)
async def toggle_automation_rule(
    rule_id: str = Path(..., description="The ID of the rule to toggle"),
    is_active: bool = Query(..., description="New active status")
):
    """
    Toggle an automation rule's active status.
    """
    try:
        automation_service = get_automation_service()
        rule = automation_service.update_rule_status(rule_id, is_active)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Automation rule {rule_id} not found")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle automation rule: {str(e)}")
        
@router.delete("/rules/{rule_id}")
async def delete_automation_rule(rule_id: str = Path(..., description="The ID of the rule to delete")):
    """
    Delete an automation rule.
    """
    try:
        automation_service = get_automation_service()
        success = automation_service.delete_automation_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Automation rule {rule_id} not found")
        return {"message": f"Automation rule {rule_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete automation rule: {str(e)}") 