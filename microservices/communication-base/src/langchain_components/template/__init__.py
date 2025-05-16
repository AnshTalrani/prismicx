"""
Template system for managing prompts and context injection.

This package provides components for managing, customizing, and compiling
prompt templates with relevant context for different bot types.
"""

from .template_registry import TemplateRegistry
from .context_injector import ContextInjector
from .template_compiler import TemplateCompiler

__all__ = [
    "TemplateRegistry",
    "ContextInjector",
    "TemplateCompiler"
] 