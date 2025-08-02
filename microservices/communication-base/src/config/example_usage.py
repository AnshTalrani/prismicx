"""
Example Config System Usage

This script demonstrates how to use the config system in practice.
It shows initialization, access, and hot-reloading functionality.

Run this file as a standalone script for a demonstration:
    python -m src.config.example_usage
"""

import os
import time
import logging
import json
from typing import Dict, Any

from src.config.config_integration import ConfigIntegration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Demo config files
DEMO_BASE_CONFIG = {
    "models": {
        "llm": {
            "default_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    },
    "rag": {
        "enabled": True,
        "vector_store": {
            "similarity": "cosine",
            "top_k": 5
        }
    },
    "session": {
        "timeout": 3600,
        "memory_type": "buffer"
    }
}

DEMO_SALES_CONFIG = {
    "models": {
        "llm": {
            "default_model": "gpt-4",
            "temperature": 0.8
        }
    },
    "rag": {
        "vector_store": {
            "top_k": 10,
            "collections": ["products", "campaigns"]
        }
    },
    "sales_specific": {
        "campaign_stages": ["awareness", "interest", "decision"],
        "follow_up_days": 3
    }
}

DEMO_CONSULTANCY_CONFIG = {
    "models": {
        "llm": {
            "default_model": "gpt-4",
            "temperature": 0.6
        }
    },
    "rag": {
        "vector_store": {
            "collections": ["business", "finance", "legal"]
        }
    },
    "consultancy_specific": {
        "frameworks": ["porter", "swot", "pestel"],
        "domains": ["strategy", "finance", "operations"]
    }
}

def create_demo_configs(config_dir: str) -> None:
    """
    Create demo configuration files for demonstration purposes.
    
    Args:
        config_dir: Directory where config files should be created
    """
    # Create directories
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(os.path.join(config_dir, "bots"), exist_ok=True)
    
    # Create base config
    with open(os.path.join(config_dir, "base.json"), "w") as f:
        json.dump(DEMO_BASE_CONFIG, f, indent=4)
        
    # Create bot-specific configs
    with open(os.path.join(config_dir, "bots", "sales.json"), "w") as f:
        json.dump(DEMO_SALES_CONFIG, f, indent=4)
        
    with open(os.path.join(config_dir, "bots", "consultancy.json"), "w") as f:
        json.dump(DEMO_CONSULTANCY_CONFIG, f, indent=4)
        
    print(f"Created demo configs in {config_dir}")

def modify_config_for_hot_reload_demo(config_dir: str) -> None:
    """
    Modify a config file to demonstrate hot reloading.
    
    Args:
        config_dir: Directory containing config files
    """
    sales_config_path = os.path.join(config_dir, "bots", "sales.json")
    
    # Load existing config
    with open(sales_config_path, "r") as f:
        config = json.load(f)
    
    # Modify a value
    config["models"]["llm"]["temperature"] = 0.9
    
    # Add a new key
    config["hot_reload_test"] = {
        "timestamp": time.time(),
        "message": "This value was updated during hot reload!"
    }
    
    # Save modified config
    with open(sales_config_path, "w") as f:
        json.dump(config, f, indent=4)
        
    print(f"Modified sales config for hot reload demonstration")

def demo_config_system() -> None:
    """Run a demonstration of the config system functionality."""
    # Create a temporary config directory
    temp_config_dir = "temp_configs"
    
    try:
        # Create demo configs
        create_demo_configs(temp_config_dir)
        
        # Initialize config integration
        config_integration = ConfigIntegration()
        success = config_integration.initialize(
            config_dir=temp_config_dir,
            base_config_name="base.json",
            enable_hot_reload=True,
            hot_reload_interval=2.0
        )
        
        if not success:
            print("Failed to initialize config system!")
            return
            
        # Basic usage - Get full configs
        print("\n=== Full Configurations ===")
        
        base_config = config_integration.get_base_config()
        print(f"Base Config (subset): {json.dumps(base_config['models'], indent=2)}")
        
        sales_config = config_integration.get_config("sales")
        print(f"Sales Config (subset): {json.dumps(sales_config['models'], indent=2)}")
        
        consultancy_config = config_integration.get_config("consultancy")
        print(f"Consultancy Config (subset): {json.dumps(consultancy_config['models'], indent=2)}")
        
        # Accessing specific values
        print("\n=== Accessing Specific Values ===")
        
        sales_model = config_integration.get_value("sales", "models.llm.default_model")
        sales_temp = config_integration.get_value("sales", "models.llm.temperature")
        sales_campaign_stages = config_integration.get_value("sales", "sales_specific.campaign_stages")
        
        print(f"Sales Model: {sales_model}")
        print(f"Sales Temperature: {sales_temp}")
        print(f"Sales Campaign Stages: {sales_campaign_stages}")
        
        consultancy_model = config_integration.get_value("consultancy", "models.llm.default_model")
        consultancy_temp = config_integration.get_value("consultancy", "models.llm.temperature")
        consultancy_frameworks = config_integration.get_value("consultancy", "consultancy_specific.frameworks")
        
        print(f"Consultancy Model: {consultancy_model}")
        print(f"Consultancy Temperature: {consultancy_temp}")
        print(f"Consultancy Frameworks: {consultancy_frameworks}")
        
        # Session-specific overrides
        print("\n=== Session-Specific Config ===")
        
        session_id = "user123-session456"
        session_overrides = {
            "models.llm.temperature": 0.5,  # Override temperature
            "session.context": {             # Add new session-specific value
                "user_expertise": "expert",
                "previous_topics": ["pricing", "features"]
            }
        }
        
        # Update session config
        session_config = config_integration.update_session_config(
            session_id=session_id,
            bot_type="sales",
            updates=session_overrides
        )
        
        # Access session-specific values
        session_temp = config_integration.get_value(
            "sales", 
            "models.llm.temperature",
            session_id=session_id,
            session_overrides=session_overrides
        )
        
        session_context = config_integration.get_value(
            "sales", 
            "session.context",
            session_id=session_id,
            session_overrides=session_overrides
        )
        
        print(f"Session Temperature: {session_temp}")
        print(f"Session Context: {session_context}")
        
        # Hot reload demonstration
        print("\n=== Hot Reload Demonstration ===")
        print("Watching for config changes (will modify sales config in 2 seconds)...")
        time.sleep(2)
        
        # Modify a config file
        modify_config_for_hot_reload_demo(temp_config_dir)
        
        # Wait for hot reload to detect change
        print("Waiting for hot reload to detect changes (5 seconds)...")
        time.sleep(5)
        
        # Check if values were updated
        new_sales_temp = config_integration.get_value("sales", "models.llm.temperature")
        new_sales_message = config_integration.get_value("sales", "hot_reload_test.message", default="Not found")
        
        print(f"Updated Sales Temperature: {new_sales_temp}")
        print(f"New Config Value: {new_sales_message}")
        
        # Clean shutdown
        print("\n=== Shutting Down ===")
        config_integration.shutdown()
        print("Config system shut down")
        
    finally:
        # Clean up temporary files (uncomment for actual removal)
        # import shutil
        # shutil.rmtree(temp_config_dir, ignore_errors=True)
        print(f"\nNote: Temporary config files remain in '{temp_config_dir}' for inspection")

if __name__ == "__main__":
    demo_config_system() 