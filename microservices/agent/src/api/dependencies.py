"""FastAPI dependency injection providers for the Agent microservice.

This module provides dependency functions that return service instances
for use in API endpoints. These functions are used with FastAPI's Depends()
to inject services into route handlers.
"""

# These will be set by main.py during startup
_batch_processor = None
_request_service = None
_template_service = None
_context_manager = None
_output_manager = None
_user_repository = None
_consultancy_bot_handler = None
_category_repository = None


def set_batch_processor(batch_processor):
    """Set the batch processor instance."""
    global _batch_processor
    _batch_processor = batch_processor


def set_request_service(request_service):
    """Set the request service instance."""
    global _request_service
    _request_service = request_service


def set_template_service(template_service):
    """Set the template service instance."""
    global _template_service
    _template_service = template_service


def set_context_manager(context_manager):
    """Set the context manager instance."""
    global _context_manager
    _context_manager = context_manager


def set_output_manager(output_manager):
    """Set the output manager instance."""
    global _output_manager
    _output_manager = output_manager


def set_user_repository(user_repository):
    """Set the user repository instance."""
    global _user_repository
    _user_repository = user_repository


def set_consultancy_bot_handler(consultancy_bot_handler):
    """Set the consultancy bot handler instance."""
    global _consultancy_bot_handler
    _consultancy_bot_handler = consultancy_bot_handler


def set_category_repository(category_repository):
    """Set the category repository instance."""
    global _category_repository
    _category_repository = category_repository


# Dependency functions for FastAPI
def get_batch_processor():
    """Get the batch processor instance."""
    return _batch_processor


def get_request_service():
    """Get the request service instance."""
    return _request_service


def get_template_service():
    """Get the template service instance."""
    return _template_service


def get_context_manager():
    """Get the context manager instance."""
    return _context_manager


def get_output_manager():
    """Get the output manager instance."""
    return _output_manager


def get_user_repository():
    """Get the user repository instance."""
    return _user_repository


def get_consultancy_bot_handler():
    """Get the consultancy bot handler instance."""
    return _consultancy_bot_handler


def get_category_repository():
    """Get the category repository instance."""
    return _category_repository
