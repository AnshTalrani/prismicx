"""
Feature Extraction Module

This module is responsible for extracting features from preprocessed data
and computing feature scores.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureExtraction:
    """
    Handles feature extraction and scoring.
    """
    
    def __init__(self):
        """Initialize the feature extraction component"""
        logger.info("Feature extraction component initialized")
    
    async def extract_factors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract factors from preprocessed data.
        
        Args:
            data: Preprocessed data
            
        Returns:
            Data with extracted factors
        """
        try:
            logger.info("Extracting factors from data")
            
            # This is a placeholder for actual factor extraction logic
            # In a real implementation, this would identify and extract key factors
            
            # Example implementation:
            data["factors"] = []
            
            if "results" in data:
                # Extract some example factors
                data["factors"] = [
                    {"name": "factor1", "value": 0.75, "confidence": 0.9},
                    {"name": "factor2", "value": 0.42, "confidence": 0.8},
                    {"name": "factor3", "value": 0.91, "confidence": 0.95}
                ]
            
            # Compute feature scores
            data = await self.compute_feature_scores(data)
            
            # Tag unlabeled data
            data = await self.tag_unlabeled_data(data)
            
            return data
            
        except Exception as e:
            logger.error(f"Factor extraction failed: {str(e)}")
            raise
    
    async def compute_feature_scores(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute scores for extracted features.
        
        Args:
            data: Data with extracted factors
            
        Returns:
            Data with feature scores
        """
        try:
            logger.info("Computing feature scores")
            
            # This is a placeholder for actual score computation logic
            # In a real implementation, this would calculate scores based on factors
            
            # Example implementation:
            if "factors" in data:
                data["scores"] = {}
                
                # Calculate an overall score based on factors
                factor_values = [factor["value"] * factor["confidence"] for factor in data["factors"]]
                if factor_values:
                    data["scores"]["overall"] = sum(factor_values) / len(factor_values)
                
                # Calculate individual scores
                for factor in data["factors"]:
                    data["scores"][factor["name"]] = factor["value"]
            
            return data
            
        except Exception as e:
            logger.error(f"Feature score computation failed: {str(e)}")
            raise
    
    async def tag_unlabeled_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tag unlabeled data based on extracted features.
        
        Args:
            data: Data with extracted factors and scores
            
        Returns:
            Tagged data
        """
        try:
            logger.info("Tagging unlabeled data")
            
            # This is a placeholder for actual tagging logic
            # In a real implementation, this would assign tags based on features
            
            # Example implementation:
            if "factors" in data:
                data["tags"] = []
                
                # Fetch categories from repository
                # Updated import to use the database-layer category repository service
                from database_layer.category_repository_service.src.repository.category_repository import CategoryRepository
                
                # Create a repository instance
                mongodb_uri = "mongodb://mongodb:27017"  # Use environment variables in production
                category_repository = CategoryRepository(mongodb_uri=mongodb_uri)
                await category_repository.connect()
                
                # Get categories
                categories = []
                categories_data = await category_repository.get_categories_by_type("tag")
                if categories_data:
                    categories = categories_data
                
                # Tag based on factors and categories
                for factor in data["factors"]:
                    if factor["value"] > 0.8:
                        data["tags"].append("high_" + factor["name"])
                    elif factor["value"] < 0.3:
                        data["tags"].append("low_" + factor["name"])
                
                # Add category tags
                for category in categories:
                    if category.get("threshold", 0) < data.get("scores", {}).get("overall", 0):
                        data["tags"].append(category.get("name", ""))
            
            return data
            
        except Exception as e:
            logger.error(f"Data tagging failed: {str(e)}")
            raise
