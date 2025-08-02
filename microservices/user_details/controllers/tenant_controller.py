from flask import Blueprint, jsonify, request, current_app, g
import logging

from multitenant.services import TenantService
from multitenant.middleware import admin_required, tenant_required

logger = logging.getLogger(__name__)

tenant_bp = Blueprint('tenant', __name__, url_prefix='/api/v1/admin/tenants')


def get_tenant_service() -> TenantService:
    """Get the tenant service from the Flask app config."""
    tenant_service = current_app.config.get('tenant_service')
    if not tenant_service:
        tenant_service = TenantService()
        current_app.config['tenant_service'] = tenant_service
    return tenant_service


@tenant_bp.route('/', methods=['GET'])
@admin_required
def get_all_tenants():
    """Get all tenants (admin only)."""
    tenant_service = get_tenant_service()
    tenants = tenant_service.get_all_tenants()
    
    # Convert tenants to dictionaries for JSON serialization
    tenant_dicts = [t.to_dict() for t in tenants]
    
    return jsonify({
        "tenants": tenant_dicts,
        "count": len(tenant_dicts)
    })


@tenant_bp.route('/<tenant_id>', methods=['GET'])
@admin_required
def get_tenant(tenant_id):
    """Get a specific tenant by ID (admin only)."""
    tenant_service = get_tenant_service()
    tenant = tenant_service.get_tenant(tenant_id)
    
    if not tenant:
        return jsonify({
            "error": "Tenant not found",
            "message": f"No tenant found with ID: {tenant_id}"
        }), 404
    
    return jsonify(tenant.to_dict())


@tenant_bp.route('/', methods=['POST'])
@admin_required
def create_tenant():
    """Create a new tenant (admin only)."""
    data = request.json
    
    # Validate request data
    if not data:
        return jsonify({
            "error": "Invalid request",
            "message": "Request body must contain JSON data"
        }), 400
    
    # Extract required fields
    tenant_id = data.get('tenant_id')
    name = data.get('name')
    config = data.get('config')
    
    if not tenant_id or not name:
        return jsonify({
            "error": "Missing required fields",
            "message": "tenant_id and name are required"
        }), 400
    
    # Create tenant
    tenant_service = get_tenant_service()
    success, message = tenant_service.create_tenant(tenant_id, name, config)
    
    if success:
        # Get the newly created tenant
        tenant = tenant_service.get_tenant(tenant_id)
        return jsonify({
            "message": message,
            "tenant": tenant.to_dict()
        }), 201
    else:
        return jsonify({
            "error": "Tenant creation failed",
            "message": message
        }), 400


@tenant_bp.route('/<tenant_id>', methods=['PUT'])
@admin_required
def update_tenant(tenant_id):
    """Update an existing tenant (admin only)."""
    data = request.json
    
    # Validate request data
    if not data:
        return jsonify({
            "error": "Invalid request",
            "message": "Request body must contain JSON data"
        }), 400
    
    # Extract fields to update
    name = data.get('name')
    config = data.get('config')
    active = data.get('active')
    
    # Update tenant
    tenant_service = get_tenant_service()
    success, message = tenant_service.update_tenant(tenant_id, name, config, active)
    
    if success:
        # Get the updated tenant
        tenant = tenant_service.get_tenant(tenant_id)
        return jsonify({
            "message": message,
            "tenant": tenant.to_dict()
        })
    else:
        return jsonify({
            "error": "Tenant update failed",
            "message": message
        }), 404


@tenant_bp.route('/<tenant_id>', methods=['DELETE'])
@admin_required
def delete_tenant(tenant_id):
    """Delete a tenant (admin only)."""
    tenant_service = get_tenant_service()
    success, message = tenant_service.delete_tenant(tenant_id)
    
    if success:
        return jsonify({
            "message": message
        })
    else:
        return jsonify({
            "error": "Tenant deletion failed",
            "message": message
        }), 404


@tenant_bp.route('/<tenant_id>/activate', methods=['POST'])
@admin_required
def activate_tenant(tenant_id):
    """Activate a tenant (admin only)."""
    tenant_service = get_tenant_service()
    success, message = tenant_service.activate_tenant(tenant_id)
    
    if success:
        return jsonify({
            "message": message
        })
    else:
        return jsonify({
            "error": "Tenant activation failed",
            "message": message
        }), 404


@tenant_bp.route('/<tenant_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_tenant(tenant_id):
    """Deactivate a tenant (admin only)."""
    tenant_service = get_tenant_service()
    success, message = tenant_service.deactivate_tenant(tenant_id)
    
    if success:
        return jsonify({
            "message": message
        })
    else:
        return jsonify({
            "error": "Tenant deactivation failed",
            "message": message
        }), 404


@tenant_bp.route('/current', methods=['GET'])
@tenant_required
def get_current_tenant():
    """Get the current tenant information based on the X-Tenant-ID header."""
    tenant_id = g.tenant_id
    
    tenant_service = get_tenant_service()
    tenant = tenant_service.get_tenant(tenant_id)
    
    if not tenant:
        return jsonify({
            "error": "Tenant not found",
            "message": f"No tenant found with ID: {tenant_id}"
        }), 404
    
    # Return a limited version of the tenant information for security
    return jsonify({
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "active": tenant.active
    })


def init_app(app):
    """Initialize the tenant routes with the Flask app."""
    app.register_blueprint(tenant_bp)
    logger.info("Initialized tenant controller") 