from flask import Flask, request, jsonify
from repositories.user_insight_repository import UserInsightRepository
from repositories.user_insight_extension_repo import UserInsightExtensionRepo
from repositories.practicality_repository import PracticalityRepository
from validation.validation_module import ValidationModule
from config.config_manager import ConfigManager
from models.user_insight import UserInsight
from models.user_insight_extension import UserInsightExtension
from models.practicality import Practicality
import os
import logging

app = Flask(__name__)

# Initialize components
config_manager = ConfigManager()
user_insight_repo = UserInsightRepository()
user_insight_extension_repo = UserInsightExtensionRepo()
practicality_repo = PracticalityRepository()
validation_module = ValidationModule()

@app.route('/processTemplate', methods=['POST'])
def process_template():
    """Process a template for a user."""
    try:
        data = request.get_json()
        template_id = data['templateID']
        user_id = data['userID']
        response = user_insight_api.processTemplate(template_id, user_id)
        return jsonify(response), 200
    except Exception as e:
        user_insight_api.handleError(str(e), str(e))
        return jsonify({"error": str(e)}), 500

# ... [Other API endpoints similar to process_template]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000))) 