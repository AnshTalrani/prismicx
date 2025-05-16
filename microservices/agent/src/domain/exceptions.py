"""
Domain exceptions.

DEPRECATED: This module is deprecated. Use src.exceptions module instead.
"""
import warnings
from src.exceptions import (
    DomainError, ValidationError, ResourceNotFoundError, 
    BusinessRuleViolationError, ErrorType
)

# Issue a deprecation warning
warnings.warn(
    "The module 'domain/exceptions.py' is deprecated. Use 'src.exceptions' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backwards compatibility
__all__ = [
    'DomainError', 'ValidationError', 'ResourceNotFoundError', 
    'BusinessRuleViolationError', 'ErrorType'
]