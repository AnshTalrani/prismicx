"""
MLOps integration for model management.

This module provides integration with the MLOps pipeline
for model versioning, updating, and monitoring.
"""

import logging
import os
import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class ModelVersion:
    """Data class representing a model version."""
    model_id: str
    version: str
    path: str
    created_at: str
    metrics: Dict[str, float]
    is_active: bool

class MLOpsIntegration:
    """Integration with MLOps pipeline for model management."""
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(MLOpsIntegration, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, mlops_api_url=None):
        """
        Initialize MLOps integration.
        
        Args:
            mlops_api_url: URL of the MLOps API
        """
        if self._initialized:
            return
            
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mlops_api_url = mlops_api_url or os.environ.get(
            "MLOPS_API_URL", "http://mlops-pipeline:8080/api"
        )
        self._initialized = True
        self.logger.info(f"MLOps integration initialized with API URL: {self.mlops_api_url}")
    
    def get_latest_model_version(self, model_id: str) -> Optional[ModelVersion]:
        """
        Get the latest version of a model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            ModelVersion instance if available, None otherwise
        """
        try:
            response = requests.get(
                f"{self.mlops_api_url}/models/{model_id}/versions/latest",
                timeout=10
            )
            
            if response.status_code == 200:
                version_data = response.json()
                return ModelVersion(
                    model_id=version_data["model_id"],
                    version=version_data["version"],
                    path=version_data["path"],
                    created_at=version_data["created_at"],
                    metrics=version_data.get("metrics", {}),
                    is_active=version_data.get("is_active", False)
                )
            else:
                self.logger.error(f"Failed to get latest model version: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error connecting to MLOps API: {e}")
            return None
    
    def get_all_model_versions(self, model_id: str) -> List[ModelVersion]:
        """
        Get all versions of a model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            List of ModelVersion instances
        """
        try:
            response = requests.get(
                f"{self.mlops_api_url}/models/{model_id}/versions",
                timeout=10
            )
            
            if response.status_code == 200:
                versions_data = response.json()
                return [
                    ModelVersion(
                        model_id=version["model_id"],
                        version=version["version"],
                        path=version["path"],
                        created_at=version["created_at"],
                        metrics=version.get("metrics", {}),
                        is_active=version.get("is_active", False)
                    )
                    for version in versions_data
                ]
            else:
                self.logger.error(f"Failed to get model versions: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error connecting to MLOps API: {e}")
            return []
    
    def report_model_usage(self, model_id: str, version: str, usage_data: Dict[str, Any]) -> bool:
        """
        Report model usage metrics to MLOps pipeline.
        
        Args:
            model_id: ID of the model
            version: Version of the model
            usage_data: Usage data to report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.mlops_api_url}/models/{model_id}/versions/{version}/usage",
                json=usage_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully reported usage for model {model_id} version {version}")
                return True
            else:
                self.logger.error(f"Failed to report model usage: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to MLOps API: {e}")
            return False
    
    def check_for_model_updates(self) -> Dict[str, ModelVersion]:
        """
        Check for updates to all models.
        
        Returns:
            Dictionary mapping model IDs to their latest versions
        """
        try:
            response = requests.get(
                f"{self.mlops_api_url}/models/updates",
                timeout=10
            )
            
            if response.status_code == 200:
                updates_data = response.json()
                return {
                    model_id: ModelVersion(
                        model_id=model_data["model_id"],
                        version=model_data["version"],
                        path=model_data["path"],
                        created_at=model_data["created_at"],
                        metrics=model_data.get("metrics", {}),
                        is_active=model_data.get("is_active", False)
                    )
                    for model_id, model_data in updates_data.items()
                }
            else:
                self.logger.error(f"Failed to check for model updates: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error connecting to MLOps API: {e}")
            return {} 