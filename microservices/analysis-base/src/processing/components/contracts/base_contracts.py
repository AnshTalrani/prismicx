"""
Base contracts for component interfaces.

This module defines the interfaces that components must implement to
fulfill specific roles in the analysis pipeline. These contracts ensure
consistent behavior across different component implementations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ComponentContract(ABC):
    """
    Base contract for all components.
    """
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the provided context.
        
        Args:
            context: The context to process
            
        Returns:
            Dict[str, Any]: The processed context
        """
        pass


class CollectorContract(ComponentContract):
    """
    Contract for data collection components.
    
    These components are responsible for retrieving data from
    external sources and preparing it for further processing.
    """
    @abstractmethod
    async def collect_data(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect data from an external source.
        
        Args:
            query: Query string to execute
            filters: Optional filters to apply
            
        Returns:
            Dict[str, Any]: The collected data
        """
        pass


class TransformerContract(ComponentContract):
    """
    Contract for data transformation components.
    
    These components are responsible for cleaning, normalizing,
    and transforming raw data into a format suitable for analysis.
    """
    @abstractmethod
    async def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform input data.
        
        Args:
            data: Raw data to transform
            
        Returns:
            Dict[str, Any]: The transformed data
        """
        pass


class FeatureExtractorContract(ComponentContract):
    """
    Contract for feature extraction components.
    
    These components are responsible for extracting meaningful
    features from preprocessed data for further analysis.
    """
    @abstractmethod
    async def extract_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from preprocessed data.
        
        Args:
            data: Preprocessed data
            
        Returns:
            Dict[str, Any]: Extracted features
        """
        pass


class AnalyzerContract(ComponentContract):
    """
    Contract for analyzer components.
    
    These components are responsible for analyzing data and
    generating insights, metrics, scores, or other outputs.
    """
    @abstractmethod
    async def analyze(self, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data and generate results.
        
        Args:
            data: Data to analyze
            params: Analysis parameters
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        pass


class PredictorContract(ComponentContract):
    """
    Contract for predictor components.
    
    These components are responsible for making predictions
    based on historical data and models.
    """
    @abstractmethod
    async def predict(self, features: Dict[str, Any], model_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make predictions based on input features.
        
        Args:
            features: Input features
            model_params: Model parameters
            
        Returns:
            Dict[str, Any]: Prediction results
        """
        pass


class RecommenderContract(ComponentContract):
    """
    Contract for recommender components.
    
    These components are responsible for generating recommendations
    based on analysis results and business rules.
    """
    @abstractmethod
    async def recommend(self, analysis_results: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations based on analysis results.
        
        Args:
            analysis_results: Results from previous analysis
            criteria: Recommendation criteria
            
        Returns:
            Dict[str, Any]: Recommendation results
        """
        pass 