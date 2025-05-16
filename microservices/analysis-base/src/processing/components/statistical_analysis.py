"""
Statistical Analysis Component for Analysis Base

This module provides a component for performing basic statistical analysis
on numerical data in the context.
"""

import time
import numpy as np
from typing import Dict, Any, List, Optional
import structlog

from src.processing.base_component import BaseComponent
from src.common.exceptions import ProcessingError, ValidationError


class StatisticalAnalysisComponent(BaseComponent):
    """
    Component for performing statistical analysis on numerical data.
    
    This component calculates basic statistics (mean, median, mode, standard deviation,
    min, max, quartiles) for numerical fields in the data.
    """
    
    def validate_config(self) -> None:
        """
        Validate the component configuration.
        
        Config parameters:
        - target_fields: Optional list of field names to analyze. If not provided, all numerical fields are analyzed.
        - include_percentiles: Optional boolean to include percentile calculations (default: True)
        - percentiles: Optional list of percentiles to calculate (default: [25, 50, 75, 90, 95, 99])
        - detect_outliers: Optional boolean to detect outliers (default: False)
        - outlier_method: Optional string indicating the outlier detection method ('iqr', 'z_score', 'percentile')
        - outlier_threshold: Optional threshold value for the outlier detection method
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Optional parameters with defaults
        if "include_percentiles" in self.config and not isinstance(self.config["include_percentiles"], bool):
            raise ValueError("include_percentiles must be a boolean")
            
        if "percentiles" in self.config:
            if not isinstance(self.config["percentiles"], list):
                raise ValueError("percentiles must be a list")
                
            for p in self.config["percentiles"]:
                if not isinstance(p, (int, float)) or p < 0 or p > 100:
                    raise ValueError("percentiles must be numbers between 0 and 100")
                    
        if "detect_outliers" in self.config and not isinstance(self.config["detect_outliers"], bool):
            raise ValueError("detect_outliers must be a boolean")
            
        if "outlier_method" in self.config:
            valid_methods = ["iqr", "z_score", "percentile"]
            if self.config["outlier_method"] not in valid_methods:
                raise ValueError(f"outlier_method must be one of: {', '.join(valid_methods)}")
                
        if "target_fields" in self.config and not isinstance(self.config["target_fields"], list):
            raise ValueError("target_fields must be a list of field names")
            
        # Log successful validation
        self.logger.debug("Configuration validated successfully")
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the context by performing statistical analysis.
        
        Args:
            context: The context to process
            
        Returns:
            Dict[str, Any]: The processed context with statistical analysis results
            
        Raises:
            ProcessingError: If processing fails
        """
        self.validate_input(context)
        
        try:
            start_time = time.time()
            
            # Get the data to analyze
            data = context["data"]
            
            # Determine which fields to analyze
            target_fields = self.config.get("target_fields")
            if target_fields:
                fields_to_analyze = {field: self._get_numeric_values(data, field) for field in target_fields if self._field_exists(data, field)}
            else:
                # Find all numeric fields
                fields_to_analyze = self._find_numeric_fields(data)
                
            # Check if we have any fields to analyze
            if not fields_to_analyze:
                self.logger.warning("No numeric fields found for statistical analysis")
                # Return stats showing no fields were analyzed
                results = {
                    "fields_analyzed": 0,
                    "message": "No numeric fields found for analysis"
                }
                return self.merge_results(context, results)
            
            # Calculate statistics for each field
            field_stats = {}
            for field_name, values in fields_to_analyze.items():
                if not values:
                    field_stats[field_name] = {"error": "No numeric values found"}
                    continue
                    
                # Calculate basic statistics
                field_stats[field_name] = self._calculate_statistics(values)
                
                # Detect outliers if configured
                if self.config.get("detect_outliers", False):
                    field_stats[field_name]["outliers"] = self._detect_outliers(values)
            
            # Prepare results
            results = {
                "fields_analyzed": len(fields_to_analyze),
                "statistics": field_stats,
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
            
            # Extract tags if there are any notable statistics
            tags = self._extract_statistical_tags(field_stats)
            if tags:
                results["tags"] = tags
            
            # Add results to the context
            processed_context = self.merge_results(context, results)
            
            self.log_timing("Statistical analysis", start_time)
            return processed_context
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise e
                
            self.logger.error("Statistical analysis failed", error=str(e))
            raise ProcessingError(
                message=f"Statistical analysis failed: {str(e)}",
                component=self.name,
                retry_recommended=False,
                original_error=e
            )
    
    def validate_input(self, context: Dict[str, Any]) -> None:
        """
        Validate that the context has required fields.
        
        Args:
            context: The context to validate
            
        Raises:
            ValidationError: If the input is invalid
        """
        super().validate_input(context)
        
        # Check if there is a data field to analyze
        if not context["data"]:
            raise ValidationError(
                message="Data field is empty",
                field="data"
            )
            
        # If specific fields are targeted, ensure at least one exists
        target_fields = self.config.get("target_fields")
        if target_fields:
            found = False
            for field in target_fields:
                if self._field_exists(context["data"], field):
                    found = True
                    break
                    
            if not found:
                raise ValidationError(
                    message="None of the specified target fields found in data",
                    field="target_fields",
                    value=target_fields
                )
    
    def _field_exists(self, data: Dict[str, Any], field: str) -> bool:
        """
        Check if a field exists in the data.
        
        Args:
            data: The data to check
            field: The field name to look for
            
        Returns:
            bool: True if the field exists
        """
        # Handle dotted notation for nested fields
        if "." in field:
            parts = field.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False
            return True
        
        return field in data
    
    def _get_numeric_values(self, data: Dict[str, Any], field: str) -> List[float]:
        """
        Extract numeric values from a field.
        
        Args:
            data: The data to extract from
            field: The field name to extract
            
        Returns:
            List[float]: List of numeric values
        """
        values = []
        
        # Handle dotted notation for nested fields
        if "." in field:
            parts = field.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return []
            
            field_value = current
        else:
            field_value = data.get(field)
        
        # Handle different types of field values
        if isinstance(field_value, (int, float)):
            values = [float(field_value)]
        elif isinstance(field_value, list):
            values = [float(v) for v in field_value if isinstance(v, (int, float))]
        
        return values
    
    def _find_numeric_fields(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, List[float]]:
        """
        Find all numeric fields in the data.
        
        Args:
            data: The data to search
            prefix: Current field prefix for nested fields
            
        Returns:
            Dict[str, List[float]]: Dictionary mapping field names to numeric values
        """
        numeric_fields = {}
        
        if not isinstance(data, dict):
            return numeric_fields
            
        for key, value in data.items():
            field_name = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, (int, float)):
                numeric_fields[field_name] = [float(value)]
            elif isinstance(value, list) and all(isinstance(v, (int, float)) for v in value):
                numeric_fields[field_name] = [float(v) for v in value]
            elif isinstance(value, dict):
                # Recursively search nested dictionaries
                nested_fields = self._find_numeric_fields(value, field_name)
                numeric_fields.update(nested_fields)
                
        return numeric_fields
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, Any]:
        """
        Calculate statistics for a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Dict[str, Any]: Dictionary of statistics
        """
        # Convert to numpy array
        values_array = np.array(values)
        
        # Calculate basic statistics
        stats = {
            "count": len(values),
            "mean": float(np.mean(values_array)),
            "median": float(np.median(values_array)),
            "std": float(np.std(values_array)),
            "min": float(np.min(values_array)),
            "max": float(np.max(values_array)),
            "sum": float(np.sum(values_array))
        }
        
        # Calculate percentiles if configured
        if self.config.get("include_percentiles", True):
            percentiles = self.config.get("percentiles", [25, 50, 75, 90, 95, 99])
            stats["percentiles"] = {
                str(p): float(np.percentile(values_array, p)) for p in percentiles
            }
        
        return stats
    
    def _detect_outliers(self, values: List[float]) -> List[float]:
        """
        Detect outliers in a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            List[float]: List of outlier values
        """
        method = self.config.get("outlier_method", "iqr")
        values_array = np.array(values)
        
        if method == "iqr":
            # Use IQR method
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1
            threshold = self.config.get("outlier_threshold", 1.5)
            
            lower_bound = q1 - (threshold * iqr)
            upper_bound = q3 + (threshold * iqr)
            
            outliers = [v for v in values if v < lower_bound or v > upper_bound]
            
        elif method == "z_score":
            # Use Z-score method
            mean = np.mean(values_array)
            std = np.std(values_array)
            threshold = self.config.get("outlier_threshold", 3.0)
            
            outliers = [v for v in values if abs((v - mean) / std) > threshold]
            
        elif method == "percentile":
            # Use percentile method
            lower_percentile = self.config.get("lower_percentile", 1)
            upper_percentile = self.config.get("upper_percentile", 99)
            
            lower_bound = np.percentile(values_array, lower_percentile)
            upper_bound = np.percentile(values_array, upper_percentile)
            
            outliers = [v for v in values if v < lower_bound or v > upper_bound]
            
        else:
            outliers = []
            
        return outliers
    
    def _extract_statistical_tags(self, field_stats: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Extract tags based on statistical properties.
        
        Args:
            field_stats: Statistics for each field
            
        Returns:
            List[str]: List of extracted tags
        """
        tags = []
        
        for field, stats in field_stats.items():
            if "error" in stats:
                continue
                
            # Check for high variance
            if stats.get("std", 0) > stats.get("mean", 0) * 0.5:
                tags.append(f"high_variance_{field}")
                
            # Check for outliers
            if "outliers" in stats and len(stats["outliers"]) > 0:
                tags.append(f"has_outliers_{field}")
                
            # Check for extreme values
            if stats.get("max", 0) > stats.get("mean", 0) * 10:
                tags.append(f"extreme_high_values_{field}")
                
            if stats.get("min", 0) < stats.get("mean", 0) * 0.1 and stats.get("min", 0) < 0:
                tags.append(f"extreme_low_values_{field}")
                
        return tags 