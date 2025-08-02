from flask import Blueprint, jsonify, request, current_app
import logging
from services.config_service import ConfigService
from repositories.user_insight_repo import UserInsightRepository
from repositories.extension_repo import UserExtensionRepository

logger = logging.getLogger(__name__)
config_bp = Blueprint('config', __name__, url_prefix='/api/v1/config')


@config_bp.route('/insight-structure', methods=['GET'])
def get_insight_structure():
    """Get the current user insight structure template."""
    config_service = current_app.config.get('config_service')
    if not config_service:
        return jsonify({"error": "Config service not initialized"}), 500
    
    structure = config_service.get_insight_structure()
    return jsonify(structure)


@config_bp.route('/default-topics', methods=['GET'])
def get_default_topics():
    """Get the default topics for new users."""
    config_service = current_app.config.get('config_service')
    if not config_service:
        return jsonify({"error": "Config service not initialized"}), 500
    
    topics = config_service.get_default_topics()
    return jsonify(topics)


@config_bp.route('/extension-types', methods=['GET'])
def get_extension_types():
    """Get all configured extension types."""
    config_service = current_app.config.get('config_service')
    if not config_service:
        return jsonify({"error": "Config service not initialized"}), 500
    
    # Get list of extension types
    types = config_service.get_all_extension_types()
    
    # Get configuration for each type
    result = {}
    for ext_type in types:
        result[ext_type] = config_service.get_extension_type_config(ext_type)
    
    return jsonify(result)


@config_bp.route('/extension-type/<extension_type>', methods=['GET'])
def get_extension_type(extension_type):
    """Get configuration for a specific extension type."""
    config_service = current_app.config.get('config_service')
    if not config_service:
        return jsonify({"error": "Config service not initialized"}), 500
    
    config = config_service.get_extension_type_config(extension_type)
    if not config:
        return jsonify({"error": f"Extension type '{extension_type}' not found"}), 404
    
    return jsonify(config)


# Admin routes for managing configurations
admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin/config')


@admin_bp.route('/reload', methods=['POST'])
def reload_config():
    """
    Reload all configuration templates and automatically migrate existing data.
    
    This endpoint reloads all templates from disk and if changes are detected,
    automatically migrates all existing user insights and extensions.
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    # Get the config service
    config_service = current_app.config.get('config_service')
    if not config_service:
        return jsonify({"error": "Config service not initialized"}), 500
    
    # Get repositories for automatic migration
    insight_repo = UserInsightRepository()
    extension_repo = UserExtensionRepository()
    
    # Set repositories in config service (they might not be there if service was created at startup)
    config_service.insight_repo = insight_repo
    config_service.extension_repo = extension_repo
    
    # Reload configs with auto_migrate=True (mandatory migrations)
    try:
        result = config_service.reload_configs(auto_migrate=True)
        
        # Close repository connections
        insight_repo.close()
        extension_repo.close()
        
        return jsonify({
            "status": "success",
            "message": "Configuration reloaded successfully",
            "reload_details": result
        })
    except Exception as e:
        logger.error(f"Error reloading configuration: {e}")
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/migrate', methods=['POST'])
def migrate_data():
    """
    Manually trigger migration of existing data to match current templates.
    
    This endpoint can be used if automatic migration was skipped or failed,
    but normally migrations are automatically performed during config reload.
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    # Get the config service
    config_service = current_app.config.get('config_service')
    if not config_service:
        return jsonify({"error": "Config service not initialized"}), 500
    
    try:
        # Create repositories
        insight_repo = UserInsightRepository()
        extension_repo = UserExtensionRepository()
        
        # Run migrations
        insight_results = config_service.migrate_existing_insights(insight_repo)
        extension_results = config_service.migrate_extensions(extension_repo)
        
        # Close repository connections
        insight_repo.close()
        extension_repo.close()
        
        return jsonify({
            "status": "success",
            "insight_migration": insight_results,
            "extension_migration": extension_results
        })
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return jsonify({"error": str(e)}), 500


def init_app(app):
    """Initialize the config routes with the Flask app."""
    app.register_blueprint(config_bp)
    app.register_blueprint(admin_bp)
    
    # Initialize config service if not already done
    if 'config_service' not in app.config:
        config_path = app.config.get('CONFIG_PATH')
        app.config['config_service'] = ConfigService(config_path=config_path)
        logger.info("Initialized config service") 