"""
Processing Module

This module provides the core processing functionality for analysis tasks.
It includes the ProcessingEngine, ComponentRegistry, and pipeline handling.
"""

from .processing_engine import ProcessingEngine
from .component_registry import ComponentRegistry
from .pipeline import Pipeline
from .pipeline_executor import PipelineExecutor

__all__ = [
    "ProcessingEngine",
    "ComponentRegistry",
    "Pipeline",
    "PipelineExecutor",
]





