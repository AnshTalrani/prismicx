import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
from collections import defaultdict

# Updated import to use the database-layer category repository
from database_layer.category_repository_service.src.repository.category_repository import CategoryRepository

logger = logging.getLogger(__name__)

class DiagnosticWorker:
    """
    Worker for diagnostic analysis of various entity types.
    
    This worker analyzes data to identify root causes, strengths, weaknesses,
    and feature importance for factors, batches, users, and other entities.
    """
    
    def __init__(self, category_repository: CategoryRepository):
        """
        Initialize the diagnostic worker.
        
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
            "root_causes": {},
            "strengths": {},
            "weaknesses": {},
            "feature_importance": {},
            "anomalies": {}
        }
        
        # Get descriptive analysis results if available
        descriptive_results = await self.get_descriptive_results(template_id)
        
        # Process each entity type according to template
        if "factors" in target_entities:
            factor_results = await self.diagnose_factors(
                data, 
                processing_params.get("factor_diagnostics", {}),
                template,
                descriptive_results
            )
            results["root_causes"]["factors"] = factor_results.get("root_causes", {})
            results["strengths"]["factors"] = factor_results.get("strengths", {})
            results["weaknesses"]["factors"] = factor_results.get("weaknesses", {})
            results["feature_importance"]["factors"] = factor_results.get("feature_importance", {})
            results["anomalies"]["factors"] = factor_results.get("anomalies", {})
            
        if "batches" in target_entities:
            batch_results = await self.diagnose_batches(
                data,
                processing_params.get("batch_diagnostics", {}),
                template,
                descriptive_results
            )
            results["root_causes"]["batches"] = batch_results.get("root_causes", {})
            results["strengths"]["batches"] = batch_results.get("strengths", {})
            results["weaknesses"]["batches"] = batch_results.get("weaknesses", {})
            results["feature_importance"]["batches"] = batch_results.get("feature_importance", {})
            results["anomalies"]["batches"] = batch_results.get("anomalies", {})
            
        if "users" in target_entities:
            user_results = await self.diagnose_users(
                data,
                processing_params.get("user_diagnostics", {}),
                template,
                descriptive_results
            )
            results["root_causes"]["users"] = user_results.get("root_causes", {})
            results["strengths"]["users"] = user_results.get("strengths", {})
            results["weaknesses"]["users"] = user_results.get("weaknesses", {})
            results["feature_importance"]["users"] = user_results.get("feature_importance", {})
            results["anomalies"]["users"] = user_results.get("anomalies", {})
            
        # Store results in repository
        await self.store_results(results, template_id)
        
        return results
        
    async def get_descriptive_results(self, template_id: str) -> Dict[str, Any]:
        """
        Get descriptive analysis results for the same template.
        
        Args:
            template_id: Template ID
            
        Returns:
            Descriptive analysis results
        """
        descriptive_results = await self.category_repository.get_analysis_results("descriptive", template_id)
        
        if descriptive_results and len(descriptive_results) > 0:
            return descriptive_results[0].get("results", {})
            
        return {}
        
    async def diagnose_factors(
        self, 
        data: Dict[str, Any], 
        diagnostics_params: Dict[str, Any], 
        template: Dict[str, Any],
        descriptive_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Diagnose factors to identify root causes, strengths, and weaknesses.
        
        Args:
            data: Data containing performance metrics
            diagnostics_params: Parameters for diagnostics
            template: Original template
            descriptive_results: Results from descriptive analysis
            
        Returns:
            Diagnostic results for factors
        """
        # Initialize results
        results = {
            "root_causes": {},
            "strengths": {},
            "weaknesses": {},
            "feature_importance": {},
            "anomalies": {}
        }
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for factor diagnostics")
            return results
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Get factor scores from descriptive results if available
        factor_scores = {}
        if descriptive_results and "scores" in descriptive_results:
            factor_scores = descriptive_results.get("scores", {}).get("factors", {})
            
        # Get factor categories to diagnose
        factor_categories = diagnostics_params.get("categories", [])
        
        # If no specific categories provided, try to infer from data
        if not factor_categories:
            # Try to infer factor categories from column names
            potential_factors = [col for col in df.columns if col not in ["timestamp", "date", "id", "user_id", "batch_id"]]
            factor_categories = potential_factors
            
        # Identify target metrics for diagnostics
        target_metrics = diagnostics_params.get("target_metrics", ["engagement", "conversion"])
        available_metrics = [col for col in df.columns if col in target_metrics]
        
        if not available_metrics:
            # If specified metrics not available, use any numeric columns as targets
            available_metrics = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) and 
                                col not in ["id", "user_id", "batch_id"]]
            
        if not available_metrics:
            logger.warning("No target metrics available for factor diagnostics")
            return results
            
        # Diagnose each factor category
        for category in factor_categories:
            # Skip if category not in data
            if category not in df.columns:
                continue
                
            # Get unique factor values in this category
            unique_factors = df[category].unique()
            
            # Calculate feature importance for this category
            feature_importance = await self.calculate_feature_importance(df, category, available_metrics)
            results["feature_importance"][category] = feature_importance
            
            # Identify strengths and weaknesses
            strengths, weaknesses = await self.identify_strengths_weaknesses(
                df, 
                category, 
                unique_factors, 
                available_metrics,
                factor_scores
            )
            
            results["strengths"][category] = strengths
            results["weaknesses"][category] = weaknesses
            
            # Identify anomalies
            anomalies = await self.identify_anomalies(df, category, unique_factors, available_metrics)
            results["anomalies"][category] = anomalies
            
            # Identify root causes
            root_causes = await self.identify_root_causes(
                df, 
                category, 
                unique_factors, 
                available_metrics,
                feature_importance
            )
            
            results["root_causes"][category] = root_causes
            
            # Update factor metadata in repository
            await self.update_factor_metadata(category, unique_factors, results, template.get("template_id", ""))
            
        return results
        
    async def calculate_feature_importance(
        self, 
        df: pd.DataFrame, 
        category: str, 
        target_metrics: List[str]
    ) -> Dict[str, float]:
        """
        Calculate feature importance for a category.
        
        Args:
            df: DataFrame with data
            category: Category to analyze
            target_metrics: Target metrics for importance calculation
            
        Returns:
            Dictionary of feature importance scores
        """
        # Simple feature importance calculation based on correlation
        importance_scores = {}
        
        for metric in target_metrics:
            # Skip if metric not in data
            if metric not in df.columns:
                continue
                
            # Create dummy variables for categorical features
            if pd.api.types.is_object_dtype(df[category]):
                dummies = pd.get_dummies(df[category], prefix=category)
                
                # Calculate correlation with target metric
                for col in dummies.columns:
                    corr = dummies[col].corr(df[metric])
                    if not pd.isna(corr):
                        # Extract value from dummy column name
                        value = col.replace(f"{category}_", "")
                        importance_scores[f"{value}_{metric}"] = abs(corr)
            else:
                # For numeric categories, calculate direct correlation
                corr = df[category].corr(df[metric])
                if not pd.isna(corr):
                    importance_scores[f"{category}_{metric}"] = abs(corr)
                    
        return importance_scores
        
    async def identify_strengths_weaknesses(
        self, 
        df: pd.DataFrame, 
        category: str, 
        unique_values: np.ndarray, 
        target_metrics: List[str],
        factor_scores: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Identify strengths and weaknesses for factor values.
        
        Args:
            df: DataFrame with data
            category: Category to analyze
            unique_values: Unique values in the category
            target_metrics: Target metrics for analysis
            factor_scores: Scores from descriptive analysis
            
        Returns:
            Tuple of strengths and weaknesses dictionaries
        """
        strengths = {}
        weaknesses = {}
        
        for metric in target_metrics:
            # Skip if metric not in data
            if metric not in df.columns:
                continue
                
            # Calculate overall metric average
            overall_avg = df[metric].mean()
            
            for value in unique_values:
                # Skip null values
                if pd.isna(value):
                    continue
                    
                # Filter data for this factor value
                factor_data = df[df[category] == value]
                
                if len(factor_data) == 0:
                    continue
                    
                # Calculate average for this factor value
                factor_avg = factor_data[metric].mean()
                
                # Calculate percent difference from overall average
                if overall_avg != 0:
                    percent_diff = ((factor_avg - overall_avg) / overall_avg) * 100
                else:
                    percent_diff = 0
                    
                # Determine if strength or weakness
                factor_id = f"{category}:{value}"
                
                if percent_diff >= 10:  # 10% better than average
                    strengths[f"{factor_id}_{metric}"] = {
                        "category": category,
                        "value": value,
                        "metric": metric,
                        "factor_avg": float(factor_avg),
                        "overall_avg": float(overall_avg),
                        "percent_diff": float(percent_diff),
                        "sample_size": int(len(factor_data))
                    }
                elif percent_diff <= -10:  # 10% worse than average
                    weaknesses[f"{factor_id}_{metric}"] = {
                        "category": category,
                        "value": value,
                        "metric": metric,
                        "factor_avg": float(factor_avg),
                        "overall_avg": float(overall_avg),
                        "percent_diff": float(percent_diff),
                        "sample_size": int(len(factor_data))
                    }
                    
        return strengths, weaknesses
        
    async def identify_anomalies(
        self, 
        df: pd.DataFrame, 
        category: str, 
        unique_values: np.ndarray, 
        target_metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Identify anomalies in factor values.
        
        Args:
            df: DataFrame with data
            category: Category to analyze
            unique_values: Unique values in the category
            target_metrics: Target metrics for analysis
            
        Returns:
            Dictionary of anomalies
        """
        anomalies = {}
        
        for metric in target_metrics:
            # Skip if metric not in data
            if metric not in df.columns:
                continue
                
            # Calculate overall metric statistics
            overall_mean = df[metric].mean()
            overall_std = df[metric].std()
            
            # Set threshold for anomaly detection (2 standard deviations)
            threshold = 2.0
            
            for value in unique_values:
                # Skip null values
                if pd.isna(value):
                    continue
                    
                # Filter data for this factor value
                factor_data = df[df[category] == value]
                
                if len(factor_data) < 5:  # Require minimum sample size
                    continue
                    
                # Calculate z-score for this factor value
                factor_mean = factor_data[metric].mean()
                if overall_std != 0:
                    z_score = abs((factor_mean - overall_mean) / overall_std)
                else:
                    z_score = 0
                    
                # Check if anomaly
                if z_score > threshold:
                    factor_id = f"{category}:{value}"
                    anomalies[f"{factor_id}_{metric}"] = {
                        "category": category,
                        "value": value,
                        "metric": metric,
                        "factor_mean": float(factor_mean),
                        "overall_mean": float(overall_mean),
                        "z_score": float(z_score),
                        "direction": "above" if factor_mean > overall_mean else "below",
                        "sample_size": int(len(factor_data))
                    }
                    
        return anomalies
        
    async def identify_root_causes(
        self, 
        df: pd.DataFrame, 
        category: str, 
        unique_values: np.ndarray, 
        target_metrics: List[str],
        feature_importance: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Identify root causes for performance variations.
        
        Args:
            df: DataFrame with data
            category: Category to analyze
            unique_values: Unique values in the category
            target_metrics: Target metrics for analysis
            feature_importance: Feature importance scores
            
        Returns:
            Dictionary of root causes
        """
        root_causes = {}
        
        # Sort feature importance to find most important features
        sorted_importance = sorted(
            [(k, v) for k, v in feature_importance.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get top 3 important features
        top_features = sorted_importance[:3]
        
        for feature_key, importance in top_features:
            # Parse feature key to get value and metric
            parts = feature_key.split('_')
            if len(parts) < 2:
                continue
                
            value = parts[0]
            metric = parts[-1]
            
            # Skip if metric not in target metrics
            if metric not in target_metrics:
                continue
                
            # Filter data for this factor value
            factor_data = df[df[category] == value]
            
            if len(factor_data) == 0:
                continue
                
            # Calculate average for this factor value
            factor_avg = factor_data[metric].mean()
            overall_avg = df[metric].mean()
            
            # Calculate percent difference from overall average
            if overall_avg != 0:
                percent_diff = ((factor_avg - overall_avg) / overall_avg) * 100
            else:
                percent_diff = 0
                
            # Add as root cause if significant difference
            if abs(percent_diff) >= 10:
                factor_id = f"{category}:{value}"
                root_causes[f"{factor_id}_{metric}"] = {
                    "category": category,
                    "value": value,
                    "metric": metric,
                    "factor_avg": float(factor_avg),
                    "overall_avg": float(overall_avg),
                    "percent_diff": float(percent_diff),
                    "importance": float(importance),
                    "impact": "positive" if percent_diff > 0 else "negative",
                    "sample_size": int(len(factor_data))
                }
                
        return root_causes
        
    async def update_factor_metadata(
        self, 
        category: str, 
        unique_values: np.ndarray, 
        results: Dict[str, Any],
        template_id: str
    ) -> None:
        """
        Update factor metadata in the repository.
        
        Args:
            category: Category to update
            unique_values: Unique values in the category
            results: Diagnostic results
            template_id: Template ID
        """
        for value in unique_values:
            # Skip null values
            if pd.isna(value):
                continue
                
            factor_id = f"factor_{category}_{value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if factor exists
            existing_factor = await self.category_repository.get_factor(factor_id)
            
            if not existing_factor:
                # Create new factor if not exists
                factor_data = {
                    "factor_name": f"{category}:{value}",
                    "category_id": category,
                    "value": value,
                    "template_id": template_id,
                    "factor_type": "diagnostic"
                }
                await self.category_repository.store_factor(factor_id, factor_data)
                
            # Collect metadata from results
            metadata = {
                "diagnostic": {
                    "strengths": {},
                    "weaknesses": {},
                    "feature_importance": {},
                    "anomalies": {},
                    "root_causes": {}
                }
            }
            
            # Add strengths
            if category in results["strengths"]:
                for key, strength in results["strengths"][category].items():
                    if strength["value"] == value:
                        metadata["diagnostic"]["strengths"][key] = strength
                        
            # Add weaknesses
            if category in results["weaknesses"]:
                for key, weakness in results["weaknesses"][category].items():
                    if weakness["value"] == value:
                        metadata["diagnostic"]["weaknesses"][key] = weakness
                        
            # Add feature importance
            if category in results["feature_importance"]:
                for key, importance in results["feature_importance"][category].items():
                    if key.startswith(f"{value}_"):
                        metadata["diagnostic"]["feature_importance"][key] = importance
                        
            # Add anomalies
            if category in results["anomalies"]:
                for key, anomaly in results["anomalies"][category].items():
                    if anomaly["value"] == value:
                        metadata["diagnostic"]["anomalies"][key] = anomaly
                        
            # Add root causes
            if category in results["root_causes"]:
                for key, root_cause in results["root_causes"][category].items():
                    if root_cause["value"] == value:
                        metadata["diagnostic"]["root_causes"][key] = root_cause
                        
            # Update factor metadata
            await self.category_repository.update_factor_metadata(factor_id, metadata)
            
    async def store_results(self, results: Dict[str, Any], template_id: str) -> None:
        """
        Store analysis results in the repository.
        
        Args:
            results: Analysis results
            template_id: Template ID
        """
        # Store as analysis result
        await self.category_repository.store_analysis_result(
            "diagnostic",
            template_id,
            results
        )
        
        # For backward compatibility, also store as a factor
        factor_id = f"diagnostic_{template_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        factor_data = {
            "template_id": template_id,
            "factor_type": "diagnostic",
            "root_causes": results.get("root_causes", {}),
            "strengths": results.get("strengths", {}),
            "weaknesses": results.get("weaknesses", {}),
            "feature_importance": results.get("feature_importance", {}),
            "anomalies": results.get("anomalies", {})
        }
        
        await self.category_repository.store_factor(factor_id, factor_data)
        
    async def diagnose_batches(
        self, 
        data: Dict[str, Any], 
        diagnostics_params: Dict[str, Any], 
        template: Dict[str, Any],
        descriptive_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Diagnose batches to identify root causes, strengths, and weaknesses.
        
        Args:
            data: Data containing performance metrics
            diagnostics_params: Parameters for diagnostics
            template: Original template
            descriptive_results: Results from descriptive analysis
            
        Returns:
            Diagnostic results for batches
        """
        # Initialize results
        results = {
            "root_causes": {},
            "strengths": {},
            "weaknesses": {},
            "feature_importance": {},
            "anomalies": {}
        }
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for batch diagnostics")
            return results
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Check if batch_id column exists
        if "batch_id" not in df.columns:
            logger.warning("No batch_id column found for batch diagnostics")
            return results
            
        # Get batch scores from descriptive results if available
        batch_scores = {}
        if descriptive_results and "scores" in descriptive_results:
            batch_scores = descriptive_results.get("scores", {}).get("batches", {})
            
        # Get unique batch IDs
        unique_batches = df["batch_id"].unique()
        
        # Identify target metrics for diagnostics
        target_metrics = diagnostics_params.get("target_metrics", ["engagement", "conversion"])
        available_metrics = [col for col in df.columns if col in target_metrics]
        
        if not available_metrics:
            # If specified metrics not available, use any numeric columns as targets
            available_metrics = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) and 
                                col not in ["id", "user_id", "batch_id"]]
            
        if not available_metrics:
            logger.warning("No target metrics available for batch diagnostics")
            return results
            
        # Identify factor categories that might influence batch performance
        factor_categories = [col for col in df.columns if col not in ["id", "user_id", "batch_id", "timestamp", "date"] + available_metrics]
        
        # Calculate overall batch statistics
        batch_stats = {}
        for batch_id in unique_batches:
            # Skip null values
            if pd.isna(batch_id):
                continue
                
            # Filter data for this batch
            batch_data = df[df["batch_id"] == batch_id]
            
            if len(batch_data) == 0:
                continue
                
            # Calculate statistics for each metric
            batch_stats[str(batch_id)] = {}
            
            for metric in available_metrics:
                batch_stats[str(batch_id)][metric] = {
                    "mean": float(batch_data[metric].mean()),
                    "median": float(batch_data[metric].median()),
                    "std": float(batch_data[metric].std()) if len(batch_data) > 1 else 0.0,
                    "min": float(batch_data[metric].min()),
                    "max": float(batch_data[metric].max()),
                    "count": int(len(batch_data))
                }
                
        # Calculate overall statistics across all batches
        overall_stats = {}
        for metric in available_metrics:
            overall_stats[metric] = {
                "mean": float(df[metric].mean()),
                "median": float(df[metric].median()),
                "std": float(df[metric].std()) if len(df) > 1 else 0.0,
                "min": float(df[metric].min()),
                "max": float(df[metric].max()),
                "count": int(len(df))
            }
            
        # Identify strengths and weaknesses for each batch
        for batch_id in unique_batches:
            # Skip null values
            if pd.isna(batch_id):
                continue
                
            batch_id_str = str(batch_id)
            
            if batch_id_str not in batch_stats:
                continue
                
            # Analyze each metric
            for metric in available_metrics:
                # Calculate percent difference from overall average
                batch_mean = batch_stats[batch_id_str][metric]["mean"]
                overall_mean = overall_stats[metric]["mean"]
                
                if overall_mean != 0:
                    percent_diff = ((batch_mean - overall_mean) / overall_mean) * 100
                else:
                    percent_diff = 0
                    
                # Determine if strength or weakness
                if percent_diff >= 10:  # 10% better than average
                    if batch_id_str not in results["strengths"]:
                        results["strengths"][batch_id_str] = {}
                        
                    results["strengths"][batch_id_str][metric] = {
                        "batch_id": batch_id_str,
                        "metric": metric,
                        "batch_mean": batch_mean,
                        "overall_mean": overall_mean,
                        "percent_diff": float(percent_diff),
                        "sample_size": batch_stats[batch_id_str][metric]["count"]
                    }
                elif percent_diff <= -10:  # 10% worse than average
                    if batch_id_str not in results["weaknesses"]:
                        results["weaknesses"][batch_id_str] = {}
                        
                    results["weaknesses"][batch_id_str][metric] = {
                        "batch_id": batch_id_str,
                        "metric": metric,
                        "batch_mean": batch_mean,
                        "overall_mean": overall_mean,
                        "percent_diff": float(percent_diff),
                        "sample_size": batch_stats[batch_id_str][metric]["count"]
                    }
                    
            # Identify anomalies
            for metric in available_metrics:
                batch_mean = batch_stats[batch_id_str][metric]["mean"]
                overall_mean = overall_stats[metric]["mean"]
                overall_std = overall_stats[metric]["std"]
                
                # Set threshold for anomaly detection (2 standard deviations)
                threshold = 2.0
                
                # Calculate z-score
                if overall_std != 0:
                    z_score = abs((batch_mean - overall_mean) / overall_std)
                else:
                    z_score = 0
                    
                # Check if anomaly
                if z_score > threshold:
                    if batch_id_str not in results["anomalies"]:
                        results["anomalies"][batch_id_str] = {}
                        
                    results["anomalies"][batch_id_str][metric] = {
                        "batch_id": batch_id_str,
                        "metric": metric,
                        "batch_mean": batch_mean,
                        "overall_mean": overall_mean,
                        "z_score": float(z_score),
                        "direction": "above" if batch_mean > overall_mean else "below",
                        "sample_size": batch_stats[batch_id_str][metric]["count"]
                    }
                    
        # Identify root causes for batch performance
        for batch_id in unique_batches:
            # Skip null values
            if pd.isna(batch_id):
                continue
                
            batch_id_str = str(batch_id)
            
            # Filter data for this batch
            batch_data = df[df["batch_id"] == batch_id]
            
            if len(batch_data) < 5:  # Require minimum sample size
                continue
                
            # Analyze factor distribution within batch
            for category in factor_categories:
                # Skip if not categorical
                if not pd.api.types.is_object_dtype(df[category]):
                    continue
                    
                # Get value counts for this category in the batch
                value_counts = batch_data[category].value_counts(normalize=True)
                
                # Get overall value counts for comparison
                overall_counts = df[category].value_counts(normalize=True)
                
                # Find overrepresented values in the batch
                for value, batch_pct in value_counts.items():
                    if value in overall_counts:
                        overall_pct = overall_counts[value]
                        
                        # Calculate percent difference
                        if overall_pct != 0:
                            pct_diff = ((batch_pct - overall_pct) / overall_pct) * 100
                        else:
                            pct_diff = 0
                            
                        # If value is significantly overrepresented and batch has a strength or weakness
                        if abs(pct_diff) >= 20:  # 20% difference in representation
                            # Check if this batch has strengths or weaknesses
                            has_strength = batch_id_str in results["strengths"]
                            has_weakness = batch_id_str in results["weaknesses"]
                            
                            if has_strength or has_weakness:
                                if batch_id_str not in results["root_causes"]:
                                    results["root_causes"][batch_id_str] = {}
                                    
                                factor_key = f"{category}:{value}"
                                results["root_causes"][batch_id_str][factor_key] = {
                                    "batch_id": batch_id_str,
                                    "category": category,
                                    "value": value,
                                    "batch_percentage": float(batch_pct),
                                    "overall_percentage": float(overall_pct),
                                    "percent_diff": float(pct_diff),
                                    "impact": "positive" if has_strength else "negative",
                                    "related_to": list(results["strengths"].get(batch_id_str, {}).keys()) if has_strength else list(results["weaknesses"].get(batch_id_str, {}).keys())
                                }
                                
        # Calculate feature importance for batches
        for metric in available_metrics:
            # Create a new DataFrame with batch statistics
            batch_stats_df = pd.DataFrame([
                {
                    "batch_id": batch_id,
                    f"{metric}_mean": stats[metric]["mean"],
                    f"{metric}_std": stats[metric]["std"],
                    f"{metric}_count": stats[metric]["count"]
                }
                for batch_id, stats in batch_stats.items()
            ])
            
            if len(batch_stats_df) < 3:  # Need at least a few batches for meaningful analysis
                continue
                
            # For each factor category, calculate how well it explains batch performance
            for category in factor_categories:
                # Skip if not categorical
                if not pd.api.types.is_object_dtype(df[category]):
                    continue
                    
                # Calculate the most common value for each batch
                batch_dominant_values = {}
                for batch_id in unique_batches:
                    if pd.isna(batch_id):
                        continue
                        
                    batch_data = df[df["batch_id"] == batch_id]
                    if len(batch_data) == 0:
                        continue
                        
                    value_counts = batch_data[category].value_counts()
                    if len(value_counts) == 0:
                        continue
                        
                    batch_dominant_values[str(batch_id)] = value_counts.index[0]
                    
                # Skip if not enough batches have dominant values
                if len(batch_dominant_values) < 3:
                    continue
                    
                # Add dominant value to batch stats DataFrame
                batch_stats_df["dominant_value"] = batch_stats_df["batch_id"].map(batch_dominant_values)
                batch_stats_df = batch_stats_df.dropna(subset=["dominant_value"])
                
                if len(batch_stats_df) < 3:
                    continue
                    
                # Calculate variance explained by dominant value
                # (Simple approach: calculate ratio of between-group variance to total variance)
                group_means = batch_stats_df.groupby("dominant_value")[f"{metric}_mean"].mean()
                overall_mean = batch_stats_df[f"{metric}_mean"].mean()
                
                # Between-group sum of squares
                between_ss = sum([(group_mean - overall_mean) ** 2 * len(batch_stats_df[batch_stats_df["dominant_value"] == value]) 
                                for value, group_mean in group_means.items()])
                
                # Total sum of squares
                total_ss = sum((batch_stats_df[f"{metric}_mean"] - overall_mean) ** 2)
                
                # Calculate variance explained (R-squared)
                if total_ss != 0:
                    variance_explained = between_ss / total_ss
                else:
                    variance_explained = 0
                    
                # Store feature importance
                if category not in results["feature_importance"]:
                    results["feature_importance"][category] = {}
                    
                results["feature_importance"][category][metric] = float(variance_explained)
                
        # Update Secret Sauce for batches
        for batch_id in unique_batches:
            if pd.isna(batch_id):
                continue
                
            batch_id_str = str(batch_id)
            
            # Skip if no diagnostics for this batch
            if (batch_id_str not in results["strengths"] and 
                batch_id_str not in results["weaknesses"] and 
                batch_id_str not in results["anomalies"]):
                continue
                
            # Get existing Secret Sauce
            secret_sauces = await self.category_repository.get_secret_sauce_by_entity("batch", batch_id_str)
            
            if secret_sauces and len(secret_sauces) > 0:
                secret_sauce = secret_sauces[0]
                secret_sauce_id = secret_sauce.get("secret_sauce_id")
                
                # Update with diagnostic information
                diagnostic_data = {
                    "diagnostic": {
                        "strengths": results["strengths"].get(batch_id_str, {}),
                        "weaknesses": results["weaknesses"].get(batch_id_str, {}),
                        "anomalies": results["anomalies"].get(batch_id_str, {}),
                        "root_causes": results["root_causes"].get(batch_id_str, {})
                    }
                }
                
                await self.category_repository.update_secret_sauce(secret_sauce_id, diagnostic_data)
                
        return results
        
    async def diagnose_users(
        self, 
        data: Dict[str, Any], 
        diagnostics_params: Dict[str, Any], 
        template: Dict[str, Any],
        descriptive_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Diagnose users to identify root causes, strengths, and weaknesses.
        
        Args:
            data: Data containing performance metrics
            diagnostics_params: Parameters for diagnostics
            template: Original template
            descriptive_results: Results from descriptive analysis
            
        Returns:
            Diagnostic results for users
        """
        # Initialize results
        results = {
            "root_causes": {},
            "strengths": {},
            "weaknesses": {},
            "feature_importance": {},
            "anomalies": {}
        }
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for user diagnostics")
            return results
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Check if user_id column exists
        if "user_id" not in df.columns:
            logger.warning("No user_id column found for user diagnostics")
            return results
            
        # Get user scores from descriptive results if available
        user_scores = {}
        if descriptive_results and "scores" in descriptive_results:
            user_scores = descriptive_results.get("scores", {}).get("users", {})
            
        # Get unique user IDs
        unique_users = df["user_id"].unique()
        
        # Identify target metrics for diagnostics
        target_metrics = diagnostics_params.get("target_metrics", ["engagement", "conversion"])
        available_metrics = [col for col in df.columns if col in target_metrics]
        
        if not available_metrics:
            # If specified metrics not available, use any numeric columns as targets
            available_metrics = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) and 
                                col not in ["id", "user_id", "batch_id"]]
            
        if not available_metrics:
            logger.warning("No target metrics available for user diagnostics")
            return results
            
        # Identify factor categories that might influence user performance
        factor_categories = [col for col in df.columns if col not in ["id", "user_id", "batch_id", "timestamp", "date"] + available_metrics]
        
        # Calculate overall user statistics
        user_stats = {}
        for user_id in unique_users:
            # Skip null values
            if pd.isna(user_id):
                continue
                
            # Filter data for this user
            user_data = df[df["user_id"] == user_id]
            
            if len(user_data) == 0:
                continue
                
            # Calculate statistics for each metric
            user_stats[str(user_id)] = {}
            
            for metric in available_metrics:
                user_stats[str(user_id)][metric] = {
                    "mean": float(user_data[metric].mean()),
                    "median": float(user_data[metric].median()),
                    "std": float(user_data[metric].std()) if len(user_data) > 1 else 0.0,
                    "min": float(user_data[metric].min()),
                    "max": float(user_data[metric].max()),
                    "count": int(len(user_data))
                }
                
        # Calculate overall statistics across all users
        overall_stats = {}
        for metric in available_metrics:
            overall_stats[metric] = {
                "mean": float(df[metric].mean()),
                "median": float(df[metric].median()),
                "std": float(df[metric].std()) if len(df) > 1 else 0.0,
                "min": float(df[metric].min()),
                "max": float(df[metric].max()),
                "count": int(len(df))
            }
            
        # Identify strengths and weaknesses for each user
        for user_id in unique_users:
            # Skip null values
            if pd.isna(user_id):
                continue
                
            user_id_str = str(user_id)
            
            if user_id_str not in user_stats:
                continue
                
            # Analyze each metric
            for metric in available_metrics:
                # Calculate percent difference from overall average
                user_mean = user_stats[user_id_str][metric]["mean"]
                overall_mean = overall_stats[metric]["mean"]
                
                if overall_mean != 0:
                    percent_diff = ((user_mean - overall_mean) / overall_mean) * 100
                else:
                    percent_diff = 0
                    
                # Determine if strength or weakness
                if percent_diff >= 15:  # 15% better than average
                    if user_id_str not in results["strengths"]:
                        results["strengths"][user_id_str] = {}
                        
                    results["strengths"][user_id_str][metric] = {
                        "user_id": user_id_str,
                        "metric": metric,
                        "user_mean": user_mean,
                        "overall_mean": overall_mean,
                        "percent_diff": float(percent_diff),
                        "sample_size": user_stats[user_id_str][metric]["count"]
                    }
                elif percent_diff <= -15:  # 15% worse than average
                    if user_id_str not in results["weaknesses"]:
                        results["weaknesses"][user_id_str] = {}
                        
                    results["weaknesses"][user_id_str][metric] = {
                        "user_id": user_id_str,
                        "metric": metric,
                        "user_mean": user_mean,
                        "overall_mean": overall_mean,
                        "percent_diff": float(percent_diff),
                        "sample_size": user_stats[user_id_str][metric]["count"]
                    }
                    
            # Identify anomalies
            for metric in available_metrics:
                user_mean = user_stats[user_id_str][metric]["mean"]
                overall_mean = overall_stats[metric]["mean"]
                overall_std = overall_stats[metric]["std"]
                
                # Set threshold for anomaly detection (2.5 standard deviations)
                threshold = 2.5
                
                # Calculate z-score
                if overall_std != 0:
                    z_score = abs((user_mean - overall_mean) / overall_std)
                else:
                    z_score = 0
                    
                # Check if anomaly
                if z_score > threshold:
                    if user_id_str not in results["anomalies"]:
                        results["anomalies"][user_id_str] = {}
                        
                    results["anomalies"][user_id_str][metric] = {
                        "user_id": user_id_str,
                        "metric": metric,
                        "user_mean": user_mean,
                        "overall_mean": overall_mean,
                        "z_score": float(z_score),
                        "direction": "above" if user_mean > overall_mean else "below",
                        "sample_size": user_stats[user_id_str][metric]["count"]
                    }
                    
        # Identify root causes for user performance
        for user_id in unique_users:
            # Skip null values
            if pd.isna(user_id):
                continue
                
            user_id_str = str(user_id)
            
            # Filter data for this user
            user_data = df[df["user_id"] == user_id]
            
            if len(user_data) < 5:  # Require minimum sample size
                continue
                
            # Get factors associated with this user
            user_factors = await self.category_repository.get_factors_by_entity("user", user_id_str)
            
            # If no factors found, try to identify from data
            if not user_factors:
                # Analyze factor distribution for this user
                for category in factor_categories:
                    # Skip if not categorical
                    if not pd.api.types.is_object_dtype(df[category]):
                        continue
                        
                    # Get most common value for this user
                    value_counts = user_data[category].value_counts()
                    if len(value_counts) == 0:
                        continue
                        
                    most_common_value = value_counts.index[0]
                    
                    # Check if this factor is associated with strengths or weaknesses
                    if (user_id_str in results["strengths"] or user_id_str in results["weaknesses"]):
                        if user_id_str not in results["root_causes"]:
                            results["root_causes"][user_id_str] = {}
                            
                        factor_key = f"{category}:{most_common_value}"
                        results["root_causes"][user_id_str][factor_key] = {
                            "user_id": user_id_str,
                            "category": category,
                            "value": most_common_value,
                            "frequency": float(value_counts[most_common_value] / len(user_data)),
                            "impact": "positive" if user_id_str in results["strengths"] else "negative",
                            "related_to": list(results["strengths"].get(user_id_str, {}).keys()) if user_id_str in results["strengths"] else list(results["weaknesses"].get(user_id_str, {}).keys())
                        }
            else:
                # Use existing factors
                for factor in user_factors:
                    category = factor.get("category_id")
                    value = factor.get("value")
                    
                    if not category or not value:
                        continue
                        
                    # Check if this factor is associated with strengths or weaknesses
                    if (user_id_str in results["strengths"] or user_id_str in results["weaknesses"]):
                        if user_id_str not in results["root_causes"]:
                            results["root_causes"][user_id_str] = {}
                            
                        factor_key = f"{category}:{value}"
                        results["root_causes"][user_id_str][factor_key] = {
                            "user_id": user_id_str,
                            "category": category,
                            "value": value,
                            "factor_id": factor.get("factor_id", ""),
                            "impact": "positive" if user_id_str in results["strengths"] else "negative",
                            "related_to": list(results["strengths"].get(user_id_str, {}).keys()) if user_id_str in results["strengths"] else list(results["weaknesses"].get(user_id_str, {}).keys())
                        }
                        
        # Link users to factors based on diagnostic results
        for user_id in unique_users:
            if pd.isna(user_id):
                continue
                
            user_id_str = str(user_id)
            
            # Skip if no root causes identified
            if user_id_str not in results["root_causes"]:
                continue
                
            # Link user to factors identified as root causes
            for factor_key, root_cause in results["root_causes"][user_id_str].items():
                category = root_cause.get("category")
                value = root_cause.get("value")
                
                if not category or not value:
                    continue
                    
                # Create or get factor
                factor_id = root_cause.get("factor_id")
                
                if not factor_id:
                    factor_id = f"factor_{category}_{value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # Check if factor exists
                    existing_factor = await self.category_repository.get_factor(factor_id)
                    
                    if not existing_factor:
                        # Create new factor
                        factor_data = {
                            "factor_name": f"{category}:{value}",
                            "category_id": category,
                            "value": value,
                            "template_id": template.get("template_id", ""),
                            "factor_type": "diagnostic"
                        }
                        await self.category_repository.store_factor(factor_id, factor_data)
                        
                # Link factor to user
                await self.category_repository.link_factor_to_entity(factor_id, "user", user_id_str)
                
        return results

async def create_worker(category_repository: CategoryRepository = None) -> DiagnosticWorker:
    """
    Create and initialize a diagnostic worker.
    
    Args:
        category_repository: Optional category repository
        
    Returns:
        Initialized DiagnosticWorker
    """
    if category_repository is None:
        # Initialize a new category repository
        mongodb_uri = "mongodb://mongodb:27017"  # Use environment variables in production
        category_repository = CategoryRepository(mongodb_uri=mongodb_uri)
        await category_repository.connect()
        
    return DiagnosticWorker(category_repository) 