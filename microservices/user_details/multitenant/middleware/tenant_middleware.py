import logging
from functools import wraps
from flask import request, g, jsonify, current_app

from ..services.tenant_service import TenantService

logger = logging.getLogger(__name__)


def get_tenant_service() -> TenantService:
    """Get the tenant service from the Flask app config."""
    tenant_service = current_app.config.get('tenant_service')
    if not tenant_service:
        tenant_service = TenantService()
        current_app.config['tenant_service'] = tenant_service
    return tenant_service


def tenant_required(f):
    """
    Decorator for Flask routes that require a valid tenant ID.
    
    This decorator:
    1. Extracts the tenant ID from the X-Tenant-ID header
    2. Validates that the tenant exists and is active
    3. Makes the tenant ID available in the Flask g object
    
    If no tenant ID is provided or the tenant is invalid, returns an error response.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = request.headers.get('X-Tenant-ID')
        
        if not tenant_id:
            return jsonify({
                "error": "Missing tenant ID",
                "message": "The X-Tenant-ID header is required"
            }), 400
        
        tenant_service = get_tenant_service()
        
        if not tenant_service.validate_tenant(tenant_id):
            return jsonify({
                "error": "Invalid tenant ID",
                "message": f"The tenant '{tenant_id}' does not exist or is inactive"
            }), 403
        
        # Store tenant ID in g for use in the route
        g.tenant_id = tenant_id
        
        # Call the decorated function
        return f(*args, **kwargs)
    
    return decorated_function


def tenant_aware(f):
    """
    Decorator for Flask routes that can use a tenant ID if provided.
    
    This decorator:
    1. Extracts the tenant ID from the X-Tenant-ID header if present
    2. Validates that the tenant exists and is active if provided
    3. Makes the tenant ID available in the Flask g object
    
    If no tenant ID is provided, the route will still work, but g.tenant_id will be None.
    If a tenant ID is provided but invalid, returns an error response.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = request.headers.get('X-Tenant-ID')
        
        if tenant_id:
            tenant_service = get_tenant_service()
            
            if not tenant_service.validate_tenant(tenant_id):
                return jsonify({
                    "error": "Invalid tenant ID",
                    "message": f"The tenant '{tenant_id}' does not exist or is inactive"
                }), 403
            
            # Store tenant ID in g for use in the route
            g.tenant_id = tenant_id
        else:
            # No tenant ID provided
            g.tenant_id = None
        
        # Call the decorated function
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Decorator for Flask routes that require admin privileges.
    
    This should be used in conjunction with authentication middleware,
    which would set g.is_admin based on the user's role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is an admin
        is_admin = getattr(g, 'is_admin', False)
        
        if not is_admin:
            return jsonify({
                "error": "Unauthorized",
                "message": "Admin privileges required for this operation"
            }), 403
        
        # Call the decorated function
        return f(*args, **kwargs)
    
    return decorated_function


def init_tenant_middleware(app):
    """
    Initialize the tenant middleware for a Flask app.
    
    This sets up the tenant service and registers middleware functions.
    
    Args:
        app: The Flask application
    """
    # Initialize tenant service
    if 'tenant_service' not in app.config:
        app.config['tenant_service'] = TenantService()
    
    # Register a before_request handler to set up tenant context
    @app.before_request
    def setup_tenant_context():
        # Skip for non-API routes
        if not request.path.startswith('/api/'):
            return
        
        # Skip for tenant management routes
        if request.path.startswith('/api/v1/admin/tenants'):
            return
        
        # Extract tenant ID from header
        tenant_id = request.headers.get('X-Tenant-ID')
        
        # Store in g for controllers to use
        g.tenant_id = tenant_id
        
        # Log the tenant ID for debugging
        if tenant_id:
            logger.debug(f"Request for tenant: {tenant_id}")
        else:
            logger.debug("No tenant ID provided in request") 