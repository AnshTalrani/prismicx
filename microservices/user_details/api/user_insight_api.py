from flask import Flask, request, jsonify
import logging
import os
from repositories.user_insight_repo import UserInsightRepository
from repositories.extension_repo import UserExtensionRepository
from services.insight_service import InsightService
from services.config_service import ConfigService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize repositories
insight_repo = UserInsightRepository()
extension_repo = UserExtensionRepository()

# Initialize services
insight_service = InsightService(insight_repo, extension_repo)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


# User Insight Endpoints

@app.route('/api/v1/insights/<user_id>', methods=['GET'])
def get_user_insight(user_id):
    """Retrieve a user's complete insight data."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    insight = insight_service.get_user_insight(user_id, tenant_id)
    if not insight:
        return jsonify({"error": "User insight not found"}), 404
    
    return jsonify(insight)


@app.route('/api/v1/insights/<user_id>/topics/<topic_id>', methods=['GET'])
def get_user_topic(user_id, topic_id):
    """Retrieve a specific topic for a user."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    topic = insight_service.get_user_topic(user_id, tenant_id, topic_id)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404
    
    return jsonify(topic)


@app.route('/api/v1/insights/<user_id>', methods=['POST'])
def create_user_insight(user_id):
    """Create a new user insight."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    result = insight_service.create_user_insight(user_id, tenant_id)
    
    # Check if the result contains an error message
    if "error" in result:
        # Return 403 Forbidden if user is not eligible
        return jsonify(result), 403
    
    return jsonify(result), 201


@app.route('/api/v1/insights/<user_id>/topics', methods=['POST'])
def add_topic(user_id):
    """Add a new topic to a user's insights."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    topic_data = request.get_json()
    if not topic_data:
        return jsonify({"error": "Request body is required"}), 400
    
    result = insight_service.add_topic(user_id, tenant_id, topic_data)
    return jsonify(result), 201


@app.route('/api/v1/insights/<user_id>/topics/<topic_id>', methods=['PUT'])
def update_topic(user_id, topic_id):
    """Update an existing topic."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    topic_data = request.get_json()
    if not topic_data:
        return jsonify({"error": "Request body is required"}), 400
    
    result = insight_service.update_topic(user_id, tenant_id, topic_id, topic_data)
    if not result:
        return jsonify({"error": "Topic not found"}), 404
    
    return jsonify(result)


@app.route('/api/v1/insights/<user_id>/topics/<topic_id>', methods=['DELETE'])
def remove_topic(user_id, topic_id):
    """Remove a topic from a user's insights."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    success = insight_service.remove_topic(user_id, tenant_id, topic_id)
    if not success:
        return jsonify({"error": "Topic not found"}), 404
    
    return jsonify({"message": "Topic removed successfully"})


@app.route('/api/v1/insights/<user_id>/topics/<topic_id>/subtopics', methods=['POST'])
def add_subtopic(user_id, topic_id):
    """Add a new subtopic to a topic."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    subtopic_data = request.get_json()
    if not subtopic_data:
        return jsonify({"error": "Request body is required"}), 400
    
    result = insight_service.add_subtopic(user_id, tenant_id, topic_id, subtopic_data)
    if not result:
        return jsonify({"error": "Topic not found"}), 404
    
    return jsonify(result), 201


@app.route('/api/v1/insights/<user_id>/topics/<topic_id>/subtopics/<subtopic_id>', methods=['PUT'])
def update_subtopic(user_id, topic_id, subtopic_id):
    """Update an existing subtopic."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    subtopic_data = request.get_json()
    if not subtopic_data:
        return jsonify({"error": "Request body is required"}), 400
    
    result = insight_service.update_subtopic(user_id, tenant_id, topic_id, subtopic_id, subtopic_data)
    if not result:
        return jsonify({"error": "Subtopic not found"}), 404
    
    return jsonify(result)


@app.route('/api/v1/insights/<user_id>/topics/<topic_id>/subtopics/<subtopic_id>', methods=['DELETE'])
def remove_subtopic(user_id, topic_id, subtopic_id):
    """Remove a subtopic from a topic."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    success = insight_service.remove_subtopic(user_id, tenant_id, topic_id, subtopic_id)
    if not success:
        return jsonify({"error": "Subtopic not found"}), 404
    
    return jsonify({"message": "Subtopic removed successfully"})


# Cross-user Topic Operations

@app.route('/api/v1/topics/<topic_name>/users', methods=['GET'])
def get_users_by_topic(topic_name):
    """Find all users that have a specific topic, with their associated data."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    filter_criteria = request.args.get('filter', {})
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 20))
    
    users_data = insight_service.find_users_by_topic(
        topic_name, filter_criteria, page, page_size, tenant_id
    )
    
    return jsonify({
        "topic_name": topic_name,
        "page": page,
        "page_size": page_size,
        "users": users_data
    })


@app.route('/api/v1/topics/<topic_name>/summary', methods=['GET'])
def summarize_topic(topic_name):
    """Generate a summary of a specific topic across all users."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    summary = insight_service.summarize_topic(topic_name, tenant_id)
    
    return jsonify(summary)


@app.route('/api/v1/insights/<user_id>/snapshot', methods=['GET'])
def get_insight_snapshot(user_id):
    """Create a condensed view of user insights for quick decision making."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    snapshot = insight_service.generate_insight_snapshot(user_id, tenant_id)
    
    if 'error' in snapshot:
        return jsonify(snapshot), 404
    
    return jsonify(snapshot)


@app.route('/api/v1/insights/batch', methods=['POST'])
def process_batch_operations():
    """Process multiple operations in a single batch."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    operations = request.get_json()
    if not operations:
        return jsonify({"error": "Request body is required"}), 400
    
    results = insight_service.process_batch_operations(operations, tenant_id)
    
    return jsonify(results)


# Extension Endpoints

@app.route('/api/v1/extensions/<extension_id>', methods=['GET'])
def get_extension(extension_id):
    """Retrieve an extension by its ID."""
    extension = extension_repo.find_by_id(extension_id)
    if not extension:
        return jsonify({"error": "Extension not found"}), 404
    
    return jsonify(extension.to_dict())


@app.route('/api/v1/users/<user_id>/extensions', methods=['GET'])
def get_extensions_for_user(user_id):
    """Get all extensions for a user."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    extensions = extension_repo.find_by_user_id(user_id, tenant_id)
    
    return jsonify({
        "user_id": user_id,
        "extensions": [ext.to_dict() for ext in extensions]
    })


@app.route('/api/v1/users/<user_id>/extensions', methods=['POST'])
def create_extension(user_id):
    """Create a new extension for a user."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    extension_type = data.get('extension_type')
    if not extension_type:
        return jsonify({"error": "extension_type is required"}), 400
    
    # Create extension directly through the repository
    extension = extension_repo.create(
        user_id=user_id,
        tenant_id=tenant_id,
        extension_type=extension_type,
        name=data.get('name', f"{extension_type} Extension"),
        description=data.get('description', ''),
        enabled=data.get('enabled', True),
        priority=data.get('priority', 0),
        metadata=data.get('metadata', {})
    )
    
    # Add metrics if provided
    metrics = data.get('metrics', {})
    if metrics:
        extension_repo.add_metrics(
            extension_id=extension.id,
            usage_count=metrics.get('usage_count', 0),
            feedback_score=metrics.get('feedback_score'),
            last_used_at=metrics.get('last_used_at')
        )
    
    logger.info(f"Created extension {extension.id} for user {user_id}")
    return jsonify(extension.to_dict()), 201


@app.route('/api/v1/extensions/<extension_id>/metrics', methods=['PUT'])
def update_extension_metrics(extension_id):
    """Update the metrics of an extension."""
    metrics = request.get_json()
    if not metrics:
        return jsonify({"error": "Request body is required"}), 400
    
    # Check if extension exists
    extension = extension_repo.find_by_id(extension_id)
    if not extension:
        return jsonify({"error": "Extension not found"}), 404
    
    # Update metrics
    extension_metrics = extension_repo.update_metrics(
        extension_id=extension_id,
        usage_count=metrics.get('usage_count'),
        feedback_score=metrics.get('feedback_score'),
        last_used_at=metrics.get('last_used_at')
    )
    
    if not extension_metrics:
        return jsonify({"error": "Failed to update metrics"}), 500
    
    # Return the updated extension with metrics
    extension = extension_repo.find_by_id(extension_id)
    logger.info(f"Updated metrics for extension {extension_id}")
    return jsonify(extension.to_dict())


@app.route('/api/v1/extensions/<extension_id>/practicality', methods=['POST'])
def add_practicality(extension_id):
    """Add practicality factors to an extension."""
    practicality_data = request.get_json()
    if not practicality_data:
        return jsonify({"error": "Request body is required"}), 400
    
    # Check if extension exists
    extension = extension_repo.find_by_id(extension_id)
    if not extension:
        return jsonify({"error": "Extension not found"}), 404
    
    # Add practicality factors directly
    factors = practicality_data.get('factors', [])
    added_factors = []
    
    for factor in factors:
        factor_result = extension_repo.add_practicality_factor(
            extension_id=extension_id,
            factor_name=factor.get('name'),
            factor_value=factor.get('value'),
            factor_weight=factor.get('weight', 1.0)
        )
        if factor_result:
            added_factors.append(factor_result)
    
    logger.info(f"Added {len(added_factors)} practicality factors to extension {extension_id}")
    
    # Return the updated extension
    extension = extension_repo.find_by_id(extension_id)
    return jsonify(extension.to_dict())


@app.route('/api/v1/extensions/<extension_id>/practicality/factors/<factor_id>', methods=['DELETE'])
def remove_factor(extension_id, factor_id):
    """Remove a factor from an extension's practicality."""
    # Check if extension exists
    extension = extension_repo.find_by_id(extension_id)
    if not extension:
        return jsonify({"error": "Extension not found"}), 404
    
    # Remove the factor
    success = extension_repo.remove_practicality_factor(extension_id, factor_id)
    if not success:
        return jsonify({"error": "Factor not found or could not be removed"}), 404
    
    logger.info(f"Removed practicality factor {factor_id} from extension {extension_id}")
    
    # Return the updated extension
    extension = extension_repo.find_by_id(extension_id)
    return jsonify(extension.to_dict())


@app.route('/api/v1/extensions/<extension_id>', methods=['DELETE'])
def delete_extension(extension_id):
    """Delete an extension."""
    success = extension_repo.delete(extension_id)
    if not success:
        return jsonify({"error": "Extension not found or could not be deleted"}), 404
    
    logger.info(f"Deleted extension {extension_id}")
    return jsonify({"message": "Extension deleted successfully"})


# Configuration Management Endpoints

@app.route('/api/v1/admin/config/reload', methods=['POST'])
def reload_configurations():
    """Admin endpoint to reload configurations from disk."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    # In a production system, you would add authorization checks here
    # to ensure only admins can reload configurations
    
    insight_service.config_service.reload_configs()
    
    return jsonify({
        "status": "success",
        "message": "Configurations reloaded successfully",
        "last_reload": insight_service.config_service.last_reload.isoformat()
    })

@app.route('/api/v1/config/extension-types', methods=['GET'])
def get_extension_types():
    """Get all available extension types."""
    types = insight_service.config_service.get_all_extension_types()
    return jsonify({
        "extension_types": types
    })

@app.route('/api/v1/config/extension-types/<extension_type>', methods=['GET'])
def get_extension_type_config(extension_type):
    """Get configuration for a specific extension type."""
    config = insight_service.config_service.get_extension_type_config(extension_type)
    if not config:
        return jsonify({"error": f"Extension type '{extension_type}' not found"}), 404
    
    return jsonify(config)

@app.route('/api/v1/config/insight-structure', methods=['GET'])
def get_insight_structure():
    """Get the current user insight structure configuration."""
    structure = insight_service.config_service.get_insight_structure()
    return jsonify(structure)

@app.route('/api/v1/config/default-topics', methods=['GET'])
def get_default_topics():
    """Get the default topics configuration."""
    topics = insight_service.config_service.get_default_topics()
    return jsonify({
        "default_topics": topics
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 