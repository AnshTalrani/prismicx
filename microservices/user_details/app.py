from flask import Flask
import os
import logging
from dotenv import load_dotenv

# Import controllers
from controllers import config_controller, insight_controller, tenant_controller

# Import multi-tenancy components
from multitenant.services import TenantService, TenantConfigService
from multitenant.middleware import init_tenant_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.config['CONFIG_PATH'] = os.environ.get('CONFIG_PATH', 'config/templates')
    app.config['TENANT_STORAGE_PATH'] = os.environ.get('TENANT_STORAGE_PATH', 'config/tenants')
    app.config['DEFAULT_TEMPLATES_PATH'] = os.environ.get('DEFAULT_TEMPLATES_PATH', 'config/templates')
    app.config['MULTI_TENANT_MODE'] = os.environ.get('MULTI_TENANT_MODE', 'true').lower() == 'true'
    
    # Initialize tenant service
    tenant_service = TenantService(storage_path=app.config['TENANT_STORAGE_PATH'])
    app.config['tenant_service'] = tenant_service
    
    # Initialize tenant config service
    tenant_config_service = TenantConfigService(tenant_service=tenant_service)
    app.config['tenant_config_service'] = tenant_config_service
    
    # Initialize tenant middleware
    if app.config['MULTI_TENANT_MODE']:
        init_tenant_middleware(app)
        logger.info("Multi-tenancy mode enabled")
    else:
        logger.info("Multi-tenancy mode disabled")
        
    # Initialize standard config service for backward compatibility
    app.config['config_service'] = tenant_config_service.get_config_service(None)
    
    # Register controllers
    config_controller.init_app(app)
    insight_controller.init_app(app)
    tenant_controller.init_app(app)
    
    logger.info(f"Application initialized with CONFIG_PATH={app.config['CONFIG_PATH']}")
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 