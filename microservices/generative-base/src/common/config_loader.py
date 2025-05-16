"""
Configuration Loader Module

This module provides functionality to load, parse, and validate YAML configuration
files for the document-driven framework.
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "docs"
FRAMEWORK_DEF_FILE = "framework_definition.yaml"
MODULES_COMBINED_FILE = "modules_combined.yaml"

class ConfigurationLoader:
    """
    Handles loading, parsing, and validation of YAML configuration files.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Base path for configuration files, defaults to 'docs' in the current directory
        """
        self.config_path = config_path or os.environ.get("GENERATIVE_CONFIG_PATH", DEFAULT_CONFIG_PATH)
        self.framework_config = {}
        self.module_configs = {}
        self.template_flow_mapping = {}
        
        logger.info(f"Configuration loader initialized with path: {self.config_path}")
    
    def load_all_configurations(self) -> bool:
        """
        Load all configuration files - framework definition and module configs.
        
        Returns:
            True if loading was successful, False otherwise
        """
        try:
            # Load framework definition
            success = self.load_framework_definition()
            if not success:
                return False
                
            # Load individual module configurations from the modules directory
            modules_dir = os.path.join(self.config_path, "modules")
            if os.path.exists(modules_dir):
                for filename in os.listdir(modules_dir):
                    if filename.endswith(".yaml") or filename.endswith(".yml"):
                        module_id = filename.split(".")[0]
                        module_path = os.path.join(modules_dir, filename)
                        self.load_module_config(module_id, module_path)
            
            # If combined modules file exists, use it for any missing modules
            self.load_combined_modules()
            
            # Build the template-to-flow mapping
            self._build_template_flow_mapping()
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")
            return False
    
    def load_framework_definition(self) -> bool:
        """
        Load the framework definition YAML file.
        
        Returns:
            True if loading was successful, False otherwise
        """
        framework_path = os.path.join(self.config_path, FRAMEWORK_DEF_FILE)
        
        if not os.path.exists(framework_path):
            logger.error(f"Framework definition file not found: {framework_path}")
            return False
        
        try:
            with open(framework_path, 'r') as file:
                self.framework_config = yaml.safe_load(file)
            
            # Basic validation
            if not self.framework_config or 'framework' not in self.framework_config:
                logger.error("Invalid framework definition: missing 'framework' section")
                return False
                
            logger.info(f"Successfully loaded framework definition from {framework_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading framework definition: {str(e)}")
            return False
    
    def load_module_config(self, module_id: str, file_path: str) -> bool:
        """
        Load a single module configuration file.
        
        Args:
            module_id: Identifier for the module
            file_path: Path to the module configuration file
            
        Returns:
            True if loading was successful, False otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"Module configuration file not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r') as file:
                module_config = yaml.safe_load(file)
            
            # Store the module configuration
            self.module_configs[module_id] = module_config
            logger.info(f"Successfully loaded module config for {module_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading module config for {module_id}: {str(e)}")
            return False
    
    def load_combined_modules(self) -> bool:
        """
        Load the combined modules YAML file for any modules not individually defined.
        
        Returns:
            True if loading was successful or file doesn't exist, False on error
        """
        combined_path = os.path.join(self.config_path, MODULES_COMBINED_FILE)
        
        if not os.path.exists(combined_path):
            logger.warning(f"Combined modules file not found: {combined_path}")
            return True  # Not an error, just means we're using individual files
        
        try:
            with open(combined_path, 'r') as file:
                combined_modules = yaml.safe_load(file)
            
            # Extract each module from the combined file
            for module_id, module_config in combined_modules.items():
                # Only use if not already loaded from individual file
                if module_id not in self.module_configs:
                    self.module_configs[module_id] = module_config
                    logger.info(f"Loaded module {module_id} from combined file")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading combined modules: {str(e)}")
            return False
    
    def _build_template_flow_mapping(self) -> None:
        """
        Build a mapping from template IDs to flow definitions.
        """
        # Check if there's an explicit mapping in the framework config
        if ('framework' in self.framework_config and 
            'template_flow_mapping' in self.framework_config['framework']):
            self.template_flow_mapping = self.framework_config['framework']['template_flow_mapping']
        else:
            # Build a default mapping based on flow IDs
            # Assuming each flow can process templates with the same ID
            flows = self.get_flows()
            for flow_id, flow_config in flows.items():
                self.template_flow_mapping[flow_id] = flow_id
        
        logger.info(f"Built template-to-flow mapping with {len(self.template_flow_mapping)} entries")
    
    def get_module_config(self, module_id: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific module.
        
        Args:
            module_id: Identifier for the module
            
        Returns:
            Module configuration or empty dict if not found
        """
        return self.module_configs.get(module_id, {})
    
    def get_flow_for_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the flow configuration for a given template ID.
        
        Args:
            template_id: Identifier for the template
            
        Returns:
            Flow configuration or None if not found
        """
        flow_id = self.template_flow_mapping.get(template_id)
        if not flow_id:
            # Try pattern matching
            for pattern, mapped_flow in self.template_flow_mapping.items():
                if pattern.endswith('*') and template_id.startswith(pattern[:-1]):
                    flow_id = mapped_flow
                    break
        
        if not flow_id:
            logger.warning(f"No flow mapping found for template: {template_id}")
            return None
        
        # Get the flow configuration
        return self.get_flow(flow_id)
    
    def get_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific flow configuration by ID.
        
        Args:
            flow_id: Identifier for the flow
            
        Returns:
            Flow configuration or None if not found
        """
        flows = self.get_flows()
        for flow in flows:
            if flow.get('id') == flow_id:
                return flow
        return None
    
    def get_flows(self) -> List[Dict[str, Any]]:
        """
        Get all defined flow configurations.
        
        Returns:
            List of flow configurations
        """
        if ('framework' in self.framework_config and 
            'flows' in self.framework_config['framework']):
            return self.framework_config['framework']['flows']
        return []
    
    def get_enabled_modules(self) -> List[Dict[str, Any]]:
        """
        Get all enabled module configurations from the framework definition.
        
        Returns:
            List of enabled module configurations
        """
        if ('framework' in self.framework_config and 
            'modules' in self.framework_config['framework']):
            return [m for m in self.framework_config['framework']['modules'] if m.get('enabled', True)]
        return []
    
    def get_system_config(self) -> Dict[str, Any]:
        """
        Get the system-wide configuration.
        
        Returns:
            System configuration or empty dict if not found
        """
        if ('framework' in self.framework_config and 
            'system' in self.framework_config['framework']):
            return self.framework_config['framework']['system']
        return {} 