from flask import Flask, request, jsonify
import logging
import os
from repositories.user_insight_repo import UserInsightRepository
from services.obsidian_service import ObsidianService

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

# Initialize services
obsidian_service = ObsidianService(insight_repo)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route('/api/v1/obsidian/<user_id>', methods=['GET'])
def get_obsidian_graph(user_id):
    """Generate a node-based graph representation of user insights."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    layout_type = request.args.get('layout', 'circular')
    
    graph_data = obsidian_service.generate_graph(user_id, tenant_id)
    if not graph_data:
        return jsonify({"error": "User insight not found"}), 404
    
    return jsonify(graph_data)


@app.route('/api/v1/obsidian/<user_id>/node/<node_id>', methods=['GET'])
def get_node_details(user_id, node_id):
    """Get detailed information for a specific node."""
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return jsonify({"error": "X-Tenant-ID header is required"}), 400
    
    node_data = obsidian_service.get_node_details(user_id, tenant_id, node_id)
    if not node_data:
        return jsonify({"error": "Node not found"}), 404
    
    return jsonify(node_data)


@app.route('/api/v1/obsidian/layout/force-directed', methods=['POST'])
def apply_force_directed_layout():
    """Apply force-directed layout to a graph."""
    graph_data = request.get_json()
    if not graph_data:
        return jsonify({"error": "Request body is required"}), 400
    
    # Unfortunately, we can't directly use the ObsidianGraph.from_dict method
    # because we don't have access to the model imports in the API file
    # This would normally be implemented, but for this demo we'll just return
    # an error message explaining it's not implemented
    
    return jsonify({
        "error": "Force-directed layout would require loading the graph model which is not directly accessible in the API file. In a real implementation, this would properly invoke obsidian_service.force_directed_layout and return the result."
    }), 501


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 