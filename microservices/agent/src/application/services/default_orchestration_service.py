"""Default implementation of the `IOrchestrationService` interface.

This minimal stub exists to satisfy imports and unit-tests.  It simply echoes
back the input data without performing any heavy execution logic.  When the
real orchestration logic is implemented, this file can be extended or replaced
accordingly.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List

from src.application.interfaces.orchestration_service import IOrchestrationService
from src.domain.entities.execution_template import ExecutionTemplate

logger = logging.getLogger(__name__)


class DefaultOrchestrationService(IOrchestrationService):
    """Minimal orchestration service that returns mock results."""

    async def execute_template(self, template: ExecutionTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("Executing template %s with context keys %s", template.id if template else None, list(context.keys()))
        return {"status": "executed", "template_id": getattr(template, "id", None), "context": context}

    async def execute_step(self, step_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("Executing step with keys %s", list(step_data.keys()))
        return {"status": "step_executed", "step": step_data, "context": context}

    async def process_request(self, request_id: str, template: ExecutionTemplate, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, user: Optional[Any] = None) -> Dict[str, Any]:
        logger.debug("Processing request %s", request_id)
        return {"status": "request_processed", "request_id": request_id}

    async def process_batch_item(self, batch_id: str, item_id: str, template: ExecutionTemplate, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, batch_metadata: Optional[Dict[str, Any]] = None, source: Optional[str] = None, user: Optional[Any] = None) -> Dict[str, Any]:
        logger.debug("Processing batch item %s in batch %s", item_id, batch_id)
        return {"status": "batch_item_processed", "batch_id": batch_id, "item_id": item_id}

    async def process_data(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("Processing raw data with keys %s", list(data.keys()))
        return {"status": "data_processed", "data": data}

    async def execute_pipeline(self, steps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("Executing pipeline with %d steps", len(steps))
        return {"status": "pipeline_executed", "steps": steps}
