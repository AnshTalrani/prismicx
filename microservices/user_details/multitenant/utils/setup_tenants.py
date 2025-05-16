#!/usr/bin/env python3
"""
Setup script for initializing the multi-tenant environment.

This script:
1. Creates necessary directories
2. Creates default tenant configurations
3. Initializes sample tenants if requested

Usage:
    python setup_tenants.py [--create-sample-tenants]
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to the path so we can import from multitenant
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from microservices.user_details.multitenant.services import TenantService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_directories():
    """Create necessary directories for multi-tenancy."""
    # Base directories
    os.makedirs('config/tenants', exist_ok=True)
    os.makedirs('config/templates', exist_ok=True)
    os.makedirs('config/templates/extension_types', exist_ok=True)
    
    logger.info("Created base directories")


def setup_sample_tenants(tenant_service):
    """Create sample tenants for testing."""
    # Sample tenant 1
    tenant_id = 'tenant1'
    if not tenant_service.repository.tenant_exists(tenant_id):
        success, message = tenant_service.create_tenant(
            tenant_id=tenant_id,
            name='Development Tenant',
            config={
                'environment': 'development',
                'features': {
                    'advanced_analytics': True,
                    'custom_extensions': True
                }
            }
        )
        if success:
            logger.info(f"Created sample tenant: {tenant_id}")
        else:
            logger.error(f"Failed to create tenant {tenant_id}: {message}")
    else:
        logger.info(f"Sample tenant {tenant_id} already exists")
    
    # Sample tenant 2
    tenant_id = 'tenant2'
    if not tenant_service.repository.tenant_exists(tenant_id):
        success, message = tenant_service.create_tenant(
            tenant_id=tenant_id,
            name='Production Tenant',
            config={
                'environment': 'production',
                'features': {
                    'advanced_analytics': False,
                    'custom_extensions': False
                }
            }
        )
        if success:
            logger.info(f"Created sample tenant: {tenant_id}")
        else:
            logger.error(f"Failed to create tenant {tenant_id}: {message}")
    else:
        logger.info(f"Sample tenant {tenant_id} already exists")


def main():
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(description='Setup multi-tenant environment')
    parser.add_argument(
        '--create-sample-tenants',
        action='store_true',
        help='Create sample tenants for testing'
    )
    
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    # Initialize tenant service
    tenant_service = TenantService()
    
    # Create sample tenants if requested
    if args.create_sample_tenants:
        setup_sample_tenants(tenant_service)
    
    logger.info("Multi-tenant environment setup complete")


if __name__ == '__main__':
    main() 