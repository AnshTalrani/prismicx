import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Updated import to use the database-layer category repository
from database_layer.category_repository_service.src.repository.category_repository import CategoryRepository

logger = logging.getLogger(__name__)

class DescriptiveWorker:
    """
    Worker for descriptive analysis of various entity types.
    
    This worker analyzes raw data to extract performance metrics and assign scores
    to factors, batches, users, and other entities based on template instructions.
    """
    
    def __init__(self, category_repository: CategoryRepository):
        """
        Initialize the descriptive worker.
        
        Args:
            category_repository: Repository for storing and retrieving categories and factors
        """
        self.category_repository = category_repository
        
    async def process(self, template: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data according to template instructions.
        
        Args:
            template: Template with processing instructions
            data: Data to process
            
        Returns:
            Processing results
        """
        template_id = template.get("template_id", str(uuid.uuid4()))
        processing_params = template.get("processing", {})
        target_entities = processing_params.get("target_entities", ["factors"])
        
        # Initialize results
        results = {
            "template_id": template_id,
            "timestamp": datetime.now().isoformat(),
            "scores": {},
            "summary": {},
            "tags": []
        }
        
        # Process each entity type according to template
        if "factors" in target_entities:
            results["scores"]["factors"] = await self.score_factors(
                data, 
                processing_params.get("factor_scoring", {}),
                template
            )
            
        if "batches" in target_entities:
            results["scores"]["batches"] = await self.score_batches(
                data,
                processing_params.get("batch_scoring", {}),
                template
            )
            
        if "users" in target_entities:
            results["scores"]["users"] = await self.score_users(
                data,
                processing_params.get("user_scoring", {}),
                template
            )
            
        # Generate summary statistics
        results["summary"] = await self.generate_summary(data, results["scores"], template)
        
        # Generate tags
        results["tags"] = await self.generate_tags(data, results["scores"], template)
        
        # Store results in repository
        await self.store_results(results, template_id)
        
        return results
        
    async def score_factors(self, data: Dict[str, Any], scoring_params: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score factors based on performance metrics.
        
        Args:
            data: Data containing performance metrics
            scoring_params: Parameters for scoring
            template: Original template
            
        Returns:
            Dictionary of factor scores
        """
        factor_scores = {}
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for factor scoring")
            return factor_scores
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Get factor categories to score
        factor_categories = scoring_params.get("categories", [])
        
        # If no specific categories provided, try to infer from data
        if not factor_categories:
            # Try to infer factor categories from column names
            potential_factors = [col for col in df.columns if col not in ["timestamp", "date", "id", "user_id"]]
            factor_categories = potential_factors
        
        # Score each factor category
        for category in factor_categories:
            # Skip if category not in data
            if category not in df.columns:
                continue
                
            # Get unique factor values in this category
            unique_factors = df[category].unique()
            
            for factor_value in unique_factors:
                # Skip null values
                if pd.isna(factor_value):
                    continue
                    
                # Filter data for this factor
                factor_data = df[df[category] == factor_value]
                
                # Calculate performance metrics
                metrics = {}
                
                # Calculate engagement metrics if available
                if "engagement" in df.columns:
                    metrics["engagement"] = {
                        "mean": float(factor_data["engagement"].mean()),
                        "median": float(factor_data["engagement"].median()),
                        "std": float(factor_data["engagement"].std()) if len(factor_data) > 1 else 0.0,
                        "min": float(factor_data["engagement"].min()),
                        "max": float(factor_data["engagement"].max()),
                        "count": int(len(factor_data))
                    }
                    
                # Calculate conversion metrics if available
                if "conversion" in df.columns:
                    metrics["conversion"] = {
                        "mean": float(factor_data["conversion"].mean()),
                        "median": float(factor_data["conversion"].median()),
                        "std": float(factor_data["conversion"].std()) if len(factor_data) > 1 else 0.0,
                        "min": float(factor_data["conversion"].min()),
                        "max": float(factor_data["conversion"].max()),
                        "count": int(len(factor_data))
                    }
                
                # Calculate other available metrics
                for metric_col in df.columns:
                    if metric_col in ["engagement", "conversion", "timestamp", "date", "id", "user_id", category]:
                        continue
                        
                    if pd.api.types.is_numeric_dtype(df[metric_col]):
                        metrics[metric_col] = {
                            "mean": float(factor_data[metric_col].mean()),
                            "median": float(factor_data[metric_col].median()),
                            "std": float(factor_data[metric_col].std()) if len(factor_data) > 1 else 0.0,
                            "min": float(factor_data[metric_col].min()),
                            "max": float(factor_data[metric_col].max()),
                            "count": int(len(factor_data))
                        }
                
                # Calculate overall score (simple average of available metrics)
                overall_score = 0.0
                metric_count = 0
                
                for metric_name, metric_values in metrics.items():
                    if "mean" in metric_values:
                        overall_score += metric_values["mean"]
                        metric_count += 1
                        
                if metric_count > 0:
                    overall_score /= metric_count
                
                # Store factor score
                factor_id = f"{category}:{factor_value}"
                factor_scores[factor_id] = {
                    "category": category,
                    "value": factor_value,
                    "metrics": metrics,
                    "overall_score": overall_score,
                    "sample_size": len(factor_data)
                }
                
                # Store factor in repository
                await self.store_factor(
                    category, 
                    factor_value, 
                    metrics, 
                    overall_score, 
                    template.get("template_id", "")
                )
        
        return factor_scores
        
    async def score_batches(self, data: Dict[str, Any], scoring_params: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score batches based on performance metrics.
        
        Args:
            data: Data containing performance metrics
            scoring_params: Parameters for scoring
            template: Original template
            
        Returns:
            Dictionary of batch scores
        """
        batch_scores = {}
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for batch scoring")
            return batch_scores
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Check if batch_id column exists
        if "batch_id" not in df.columns:
            logger.warning("No batch_id column found for batch scoring")
            return batch_scores
            
        # Get unique batch IDs
        unique_batches = df["batch_id"].unique()
        
        # Score each batch
        for batch_id in unique_batches:
            # Skip null values
            if pd.isna(batch_id):
                continue
                
            # Filter data for this batch
            batch_data = df[df["batch_id"] == batch_id]
            
            # Calculate performance metrics
            metrics = {}
            
            # Calculate metrics for all numeric columns
            for col in batch_data.columns:
                if col in ["batch_id", "timestamp", "date", "id", "user_id"]:
                    continue
                    
                if pd.api.types.is_numeric_dtype(batch_data[col]):
                    metrics[col] = {
                        "mean": float(batch_data[col].mean()),
                        "median": float(batch_data[col].median()),
                        "std": float(batch_data[col].std()) if len(batch_data) > 1 else 0.0,
                        "min": float(batch_data[col].min()),
                        "max": float(batch_data[col].max()),
                        "count": int(len(batch_data))
                    }
            
            # Calculate overall score (simple average of available metrics)
            overall_score = 0.0
            metric_count = 0
            
            for metric_name, metric_values in metrics.items():
                if "mean" in metric_values:
                    overall_score += metric_values["mean"]
                    metric_count += 1
                    
            if metric_count > 0:
                overall_score /= metric_count
            
            # Store batch score
            batch_scores[str(batch_id)] = {
                "batch_id": str(batch_id),
                "metrics": metrics,
                "overall_score": overall_score,
                "sample_size": len(batch_data)
            }
            
            # Create Secret Sauce for batch
            await self.create_secret_sauce(
                "batch", 
                str(batch_id), 
                metrics, 
                overall_score, 
                template.get("template_id", "")
            )
        
        return batch_scores
        
    async def score_users(self, data: Dict[str, Any], scoring_params: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score users based on performance metrics.
        
        Args:
            data: Data containing performance metrics
            scoring_params: Parameters for scoring
            template: Original template
            
        Returns:
            Dictionary of user scores
        """
        user_scores = {}
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for user scoring")
            return user_scores
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Check if user_id column exists
        if "user_id" not in df.columns:
            logger.warning("No user_id column found for user scoring")
            return user_scores
            
        # Get unique user IDs
        unique_users = df["user_id"].unique()
        
        # Score each user
        for user_id in unique_users:
            # Skip null values
            if pd.isna(user_id):
                continue
                
            # Filter data for this user
            user_data = df[df["user_id"] == user_id]
            
            # Calculate performance metrics
            metrics = {}
            
            # Calculate metrics for all numeric columns
            for col in user_data.columns:
                if col in ["user_id", "timestamp", "date", "id", "batch_id"]:
                    continue
                    
                if pd.api.types.is_numeric_dtype(user_data[col]):
                    metrics[col] = {
                        "mean": float(user_data[col].mean()),
                        "median": float(user_data[col].median()),
                        "std": float(user_data[col].std()) if len(user_data) > 1 else 0.0,
                        "min": float(user_data[col].min()),
                        "max": float(user_data[col].max()),
                        "count": int(len(user_data))
                    }
            
            # Calculate overall score (simple average of available metrics)
            overall_score = 0.0
            metric_count = 0
            
            for metric_name, metric_values in metrics.items():
                if "mean" in metric_values:
                    overall_score += metric_values["mean"]
                    metric_count += 1
                    
            if metric_count > 0:
                overall_score /= metric_count
            
            # Store user score
            user_scores[str(user_id)] = {
                "user_id": str(user_id),
                "metrics": metrics,
                "overall_score": overall_score,
                "sample_size": len(user_data)
            }
            
            # Link user to appropriate factors
            await self.link_user_to_factors(str(user_id), user_data, template.get("template_id", ""))
        
        return user_scores
        
    async def generate_summary(self, data: Dict[str, Any], scores: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary statistics from scores.
        
        Args:
            data: Original data
            scores: Calculated scores
            template: Original template
            
        Returns:
            Summary statistics
        """
        summary = {
            "total_records": len(data.get("data", [])),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Add factor summary if available
        if "factors" in scores:
            factor_summary = {
                "total_factors": len(scores["factors"]),
                "average_score": np.mean([f["overall_score"] for f in scores["factors"].values()]) if scores["factors"] else 0,
                "top_factors": sorted(
                    [(k, v["overall_score"]) for k, v in scores["factors"].items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5] if scores["factors"] else []
            }
            summary["factors"] = factor_summary
            
        # Add batch summary if available
        if "batches" in scores:
            batch_summary = {
                "total_batches": len(scores["batches"]),
                "average_score": np.mean([b["overall_score"] for b in scores["batches"].values()]) if scores["batches"] else 0,
                "top_batches": sorted(
                    [(k, v["overall_score"]) for k, v in scores["batches"].items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5] if scores["batches"] else []
            }
            summary["batches"] = batch_summary
            
        # Add user summary if available
        if "users" in scores:
            user_summary = {
                "total_users": len(scores["users"]),
                "average_score": np.mean([u["overall_score"] for u in scores["users"].values()]) if scores["users"] else 0,
                "top_users": sorted(
                    [(k, v["overall_score"]) for k, v in scores["users"].items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5] if scores["users"] else []
            }
            summary["users"] = user_summary
            
        return summary
        
    async def generate_tags(self, data: Dict[str, Any], scores: Dict[str, Any], template: Dict[str, Any]) -> List[str]:
        """
        Generate tags based on scores.
        
        Args:
            data: Original data
            scores: Calculated scores
            template: Original template
            
        Returns:
            List of tags
        """
        tags = []
        
        # Add tags based on factor scores
        if "factors" in scores and scores["factors"]:
            # Add tags for top factors
            top_factors = sorted(
                [(k, v["overall_score"]) for k, v in scores["factors"].items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for factor_id, score in top_factors:
                factor = scores["factors"][factor_id]
                tags.append(f"top_factor:{factor['category']}:{factor['value']}")
                
        # Add tags based on batch scores
        if "batches" in scores and scores["batches"]:
            # Add tags for top batches
            top_batches = sorted(
                [(k, v["overall_score"]) for k, v in scores["batches"].items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for batch_id, score in top_batches:
                tags.append(f"top_batch:{batch_id}")
                
        # Add general analysis tags
        tags.append(f"analysis_type:descriptive")
        tags.append(f"template:{template.get('template_id', '')}")
        
        return tags
        
    async def store_results(self, results: Dict[str, Any], template_id: str) -> None:
        """
        Store analysis results in the repository.
        
        Args:
            results: Analysis results
            template_id: Template ID
        """
        # Store as analysis result
        await self.category_repository.store_analysis_result(
            "descriptive",
            template_id,
            results
        )
        
        # For backward compatibility, also store as a factor
        factor_id = f"descriptive_{template_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        factor_data = {
            "template_id": template_id,
            "factor_type": "descriptive",
            "scores": results.get("scores", {}),
            "summary": results.get("summary", {}),
            "tags": results.get("tags", [])
        }
        
        await self.category_repository.store_factor(factor_id, factor_data)
        
    async def store_factor(self, category: str, value: Any, metrics: Dict[str, Any], score: float, template_id: str) -> str:
        """
        Store a factor in the repository.
        
        Args:
            category: Factor category
            value: Factor value
            metrics: Performance metrics
            score: Overall score
            template_id: Template ID
            
        Returns:
            Factor ID
        """
        factor_id = f"factor_{category}_{value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        factor_data = {
            "factor_name": f"{category}:{value}",
            "category_id": category,
            "value": value,
            "metrics": metrics,
            "overall_score": score,
            "template_id": template_id,
            "factor_type": "descriptive"
        }
        
        await self.category_repository.store_factor(factor_id, factor_data)
        
        return factor_id
        
    async def create_secret_sauce(self, entity_type: str, entity_id: str, metrics: Dict[str, Any], score: float, template_id: str) -> str:
        """
        Create a Secret Sauce record for an entity.
        
        Args:
            entity_type: Type of entity (batch, campaign)
            entity_id: ID of the entity
            metrics: Performance metrics
            score: Overall score
            template_id: Template ID
            
        Returns:
            Secret Sauce ID
        """
        secret_sauce_data = {
            f"{entity_type}_id": entity_id,
            "aggregated_score": score,
            "aggregated_metrics": metrics,
            "template_id": template_id,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        secret_sauce_id = await self.category_repository.store_secret_sauce(secret_sauce_data)
        
        return secret_sauce_id
        
    async def link_user_to_factors(self, user_id: str, user_data: pd.DataFrame, template_id: str) -> None:
        """
        Link a user to relevant factors based on their data.
        
        Args:
            user_id: User ID
            user_data: User data
            template_id: Template ID
        """
        # Get factor categories from columns
        factor_categories = [col for col in user_data.columns if col not in ["timestamp", "date", "id", "user_id", "batch_id"]]
        
        for category in factor_categories:
            # Skip if not categorical
            if not pd.api.types.is_object_dtype(user_data[category]):
                continue
                
            # Get most common value for this user
            value_counts = user_data[category].value_counts()
            if len(value_counts) == 0:
                continue
                
            most_common_value = value_counts.index[0]
            
            # Get or create factor
            factor_id = f"factor_{category}_{most_common_value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Link factor to user
            await self.category_repository.link_factor_to_entity(factor_id, "user", user_id)

async def create_worker(category_repository: CategoryRepository = None) -> DescriptiveWorker:
    """
    Create and initialize a descriptive worker.
    
    Args:
        category_repository: Optional category repository
        
    Returns:
        Initialized DescriptiveWorker
    """
    if category_repository is None:
        # Initialize a new category repository
        mongodb_uri = "mongodb://mongodb:27017"  # Use environment variables in production
        category_repository = CategoryRepository(mongodb_uri=mongodb_uri)
        await category_repository.connect()
        
    return DescriptiveWorker(category_repository) 