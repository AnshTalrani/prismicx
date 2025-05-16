import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import uuid
from collections import defaultdict

# Updated import to use the database-layer category repository
from database_layer.category_repository_service.src.repository.category_repository import CategoryRepository

logger = logging.getLogger(__name__)

class PrescriptiveWorker:
    """
    Worker for prescriptive analysis of various entity types.
    
    This worker generates recommendations, optimizes strategies, and prioritizes
    actions for factors, batches, users, and other entities based on insights
    from descriptive, diagnostic, and predictive analyses.
    """
    
    def __init__(self, category_repository: CategoryRepository):
        """
        Initialize the prescriptive worker.
        
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
            "recommendations": [],
            "strategy_adjustments": {},
            "expected_impacts": {},
            "prioritized_actions": [],
            "metadata": {}
        }
        
        # Retrieve insights from previous analyses
        insights = await self.retrieve_analysis_insights(template_id)
        
        # Process each entity type according to template
        if "factors" in target_entities:
            factor_results = await self.prescribe_factors(
                data, 
                processing_params,
                template,
                insights
            )
            results["recommendations"].extend(factor_results.get("recommendations", []))
            results["strategy_adjustments"].update(factor_results.get("strategy_adjustments", {}))
            results["expected_impacts"].update(factor_results.get("expected_impacts", {}))
            
        if "batches" in target_entities:
            batch_results = await self.prescribe_batches(
                data,
                processing_params,
                template,
                insights
            )
            results["recommendations"].extend(batch_results.get("recommendations", []))
            results["strategy_adjustments"].update(batch_results.get("strategy_adjustments", {}))
            results["expected_impacts"].update(batch_results.get("expected_impacts", {}))
            
        if "users" in target_entities:
            user_results = await self.prescribe_users(
                data,
                processing_params,
                template,
                insights
            )
            results["recommendations"].extend(user_results.get("recommendations", []))
            results["strategy_adjustments"].update(user_results.get("strategy_adjustments", {}))
            results["expected_impacts"].update(user_results.get("expected_impacts", {}))
            
        # Store results in repository
        await self.store_results(results, template_id)
        
        # Prioritize actions across all entity types
        results["prioritized_actions"] = self.prioritize_actions(results["recommendations"])
        
        return results
        
    async def retrieve_analysis_insights(self, template_id: str) -> Dict[str, Any]:
        """
        Retrieve insights from previous analyses.
        
        Args:
            template_id: Template ID
            
        Returns:
            Dictionary of insights from different analysis types
        """
        insights = {
            "descriptive": {},
            "diagnostic": {},
            "predictive": {}
        }
        
        # Get descriptive analysis results
        descriptive_results = await self.category_repository.get_analysis_results("descriptive", template_id)
        if descriptive_results and len(descriptive_results) > 0:
            insights["descriptive"] = descriptive_results[0].get("results", {})
            
        # Get diagnostic analysis results
        diagnostic_results = await self.category_repository.get_analysis_results("diagnostic", template_id)
        if diagnostic_results and len(diagnostic_results) > 0:
            insights["diagnostic"] = diagnostic_results[0].get("results", {})
            
        # Get predictive analysis results
        predictive_results = await self.category_repository.get_analysis_results("predictive", template_id)
        if predictive_results and len(predictive_results) > 0:
            insights["predictive"] = predictive_results[0].get("results", {})
            
        # Get factors from previous analyses
        descriptive_factors = await self.category_repository.get_factors_by_template(template_id, "descriptive")
        diagnostic_factors = await self.category_repository.get_factors_by_template(template_id, "diagnostic")
        predictive_factors = await self.category_repository.get_factors_by_template(template_id, "predictive")
        
        insights["factors"] = {
            "descriptive": descriptive_factors,
            "diagnostic": diagnostic_factors,
            "predictive": predictive_factors
        }
        
        return insights
        
    async def prescribe_factors(
        self, 
        data: Dict[str, Any], 
        processing_params: Dict[str, Any], 
        template: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate prescriptions for factors.
        
        Args:
            data: Data containing performance metrics
            processing_params: Parameters for processing
            template: Original template
            insights: Insights from previous analyses
            
        Returns:
            Prescription results for factors
        """
        # Initialize results
        results = {
            "recommendations": [],
            "strategy_adjustments": {},
            "expected_impacts": {}
        }
        
        # Get recommendation types to generate
        recommendation_types = processing_params.get("recommendation_types", ["content", "strategy", "timing"])
        
        # Get optimization method
        optimization_method = processing_params.get("optimization_method", "rule_based")
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for factor prescriptions")
            return results
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Generate content recommendations
        if "content" in recommendation_types:
            content_recommendations = await self.generate_content_recommendations(df, insights, processing_params)
            results["recommendations"].extend(content_recommendations)
            
        # Generate strategy recommendations
        if "strategy" in recommendation_types:
            strategy_recommendations, strategy_adjustments = await self.generate_strategy_recommendations(
                df, insights, processing_params
            )
            results["recommendations"].extend(strategy_recommendations)
            results["strategy_adjustments"].update(strategy_adjustments)
            
        # Generate timing recommendations
        if "timing" in recommendation_types:
            timing_recommendations = await self.generate_timing_recommendations(df, insights, processing_params)
            results["recommendations"].extend(timing_recommendations)
            
        # Calculate expected impacts
        results["expected_impacts"] = await self.calculate_expected_impacts(
            results["recommendations"], 
            insights
        )
        
        # Optimize recommendations if needed
        if optimization_method != "rule_based" and len(results["recommendations"]) > 0:
            results["recommendations"] = await self.optimize_recommendations(
                results["recommendations"],
                results["expected_impacts"],
                optimization_method,
                processing_params
            )
            
        # Assign factors to recommendations
        await self.assign_factors_to_recommendations(results["recommendations"], template_id)
        
        return results
        
    async def generate_content_recommendations(
        self, 
        df: pd.DataFrame, 
        insights: Dict[str, Any],
        processing_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate content-related recommendations.
        
        Args:
            df: DataFrame with data
            insights: Insights from previous analyses
            processing_params: Parameters for processing
            
        Returns:
            List of content recommendations
        """
        recommendations = []
        
        # Extract diagnostic insights
        diagnostic_insights = insights.get("diagnostic", {})
        strengths = diagnostic_insights.get("strengths", {}).get("factors", {})
        weaknesses = diagnostic_insights.get("weaknesses", {}).get("factors", {})
        
        # Extract predictive insights
        predictive_insights = insights.get("predictive", {})
        risk_scores = predictive_insights.get("risk_scores", {}).get("factors", {})
        
        # Identify content categories
        content_categories = ["caption_type", "media_type", "hashtag_strategy", "image_style"]
        available_categories = [cat for cat in content_categories if cat in df.columns]
        
        for category in available_categories:
            # Get unique values
            unique_values = df[category].unique()
            
            # Analyze each value
            for value in unique_values:
                if pd.isna(value):
                    continue
                    
                factor_id = f"{category}:{value}"
                
                # Check if this factor is a strength
                is_strength = False
                strength_metrics = []
                
                if category in strengths:
                    for key, strength in strengths[category].items():
                        if key.startswith(f"{factor_id}_"):
                            is_strength = True
                            metric = strength.get("metric")
                            if metric:
                                strength_metrics.append(metric)
                                
                # Check if this factor is a weakness
                is_weakness = False
                weakness_metrics = []
                
                if category in weaknesses:
                    for key, weakness in weaknesses[category].items():
                        if key.startswith(f"{factor_id}_"):
                            is_weakness = True
                            metric = weakness.get("metric")
                            if metric:
                                weakness_metrics.append(metric)
                                
                # Check if this factor has high risk
                is_high_risk = False
                risk_metrics = []
                
                if category in risk_scores:
                    if factor_id in risk_scores[category]:
                        for metric, risk in risk_scores[category][factor_id].items():
                            if risk.get("score", 0) > 0.6:  # High risk threshold
                                is_high_risk = True
                                risk_metrics.append(metric)
                                
                # Generate recommendations based on insights
                if is_strength:
                    # Recommend using more of this factor
                    recommendations.append({
                        "type": "content",
                        "category": category,
                        "action": "increase",
                        "value": value,
                        "reason": f"This {category} has shown strong performance in {', '.join(strength_metrics)}",
                        "confidence": 0.8,
                        "metrics_affected": strength_metrics
                    })
                    
                if is_weakness:
                    # Recommend using less of this factor
                    recommendations.append({
                        "type": "content",
                        "category": category,
                        "action": "decrease",
                        "value": value,
                        "reason": f"This {category} has shown weak performance in {', '.join(weakness_metrics)}",
                        "confidence": 0.7,
                        "metrics_affected": weakness_metrics
                    })
                    
                if is_high_risk:
                    # Recommend caution with this factor
                    recommendations.append({
                        "type": "content",
                        "category": category,
                        "action": "monitor",
                        "value": value,
                        "reason": f"This {category} shows high risk for {', '.join(risk_metrics)}",
                        "confidence": 0.6,
                        "metrics_affected": risk_metrics
                    })
                    
        return recommendations
        
    async def generate_strategy_recommendations(
        self, 
        df: pd.DataFrame, 
        insights: Dict[str, Any],
        processing_params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate strategy-related recommendations.
        
        Args:
            df: DataFrame with data
            insights: Insights from previous analyses
            processing_params: Parameters for processing
            
        Returns:
            Tuple of strategy recommendations and strategy adjustments
        """
        recommendations = []
        strategy_adjustments = {}
        
        # Extract diagnostic insights
        diagnostic_insights = insights.get("diagnostic", {})
        root_causes = diagnostic_insights.get("root_causes", {}).get("factors", {})
        feature_importance = diagnostic_insights.get("feature_importance", {}).get("factors", {})
        
        # Extract predictive insights
        predictive_insights = insights.get("predictive", {})
        forecasts = predictive_insights.get("ensemble_forecast", {}).get("factors", {})
        
        # Identify strategy categories
        strategy_categories = ["target_audience", "campaign_objective", "budget_allocation"]
        available_categories = [cat for cat in strategy_categories if cat in df.columns]
        
        # Generate overall strategy adjustments
        strategy_adjustments = {
            "focus_areas": [],
            "resource_allocation": {},
            "risk_mitigation": []
        }
        
        # Identify top performing factors across all categories
        top_factors = []
        
        for category in available_categories:
            if category in feature_importance:
                # Sort factors by importance
                sorted_importance = []
                
                for metric, importance in feature_importance[category].items():
                    if isinstance(importance, dict):
                        for factor, score in importance.items():
                            sorted_importance.append((factor, score))
                    else:
                        # Handle case where importance is directly mapped to metric
                        sorted_importance.append((metric, importance))
                        
                sorted_importance.sort(key=lambda x: x[1], reverse=True)
                
                # Add top factors to focus areas
                for factor, score in sorted_importance[:2]:  # Top 2 factors
                    if score > 0.3:  # Minimum importance threshold
                        factor_name = f"{category}:{factor.split('_')[0]}" if '_' in factor else f"{category}:{factor}"
                        top_factors.append((factor_name, score))
                        
                        strategy_adjustments["focus_areas"].append({
                            "factor": factor_name,
                            "importance": score,
                            "reason": f"High impact on performance metrics"
                        })
                        
        # Sort top factors by importance
        top_factors.sort(key=lambda x: x[1], reverse=True)
        
        # Allocate resources based on factor importance
        total_importance = sum(score for _, score in top_factors)
        
        if total_importance > 0:
            for factor, score in top_factors:
                allocation = (score / total_importance) * 100
                strategy_adjustments["resource_allocation"][factor] = round(allocation, 1)
                
        # Generate specific strategy recommendations
        for category in available_categories:
            # Get unique values
            unique_values = df[category].unique()
            
            # Analyze each value
            for value in unique_values:
                if pd.isna(value):
                    continue
                    
                factor_id = f"{category}:{value}"
                
                # Check if this factor is a root cause
                is_root_cause = False
                root_cause_metrics = []
                impact = "positive"
                
                if category in root_causes:
                    for key, root_cause in root_causes[category].items():
                        if key.startswith(f"{factor_id}_"):
                            is_root_cause = True
                            metric = root_cause.get("metric")
                            if metric:
                                root_cause_metrics.append(metric)
                            if root_cause.get("impact") == "negative":
                                impact = "negative"
                                
                # Check forecast trends
                has_forecast = False
                forecast_trend = "stable"
                forecast_metrics = []
                
                if category in forecasts:
                    if factor_id in forecasts[category]:
                        has_forecast = True
                        for metric, forecast in forecasts[category][factor_id].items():
                            if len(forecast) > 1:
                                first_half = np.mean(forecast[:len(forecast)//2])
                                second_half = np.mean(forecast[len(forecast)//2:])
                                
                                if second_half > first_half * 1.1:
                                    forecast_trend = "increasing"
                                    forecast_metrics.append(metric)
                                elif second_half < first_half * 0.9:
                                    forecast_trend = "decreasing"
                                    forecast_metrics.append(metric)
                                    
                # Generate recommendations based on insights
                if is_root_cause:
                    action = "increase" if impact == "positive" else "decrease"
                    
                    recommendations.append({
                        "type": "strategy",
                        "category": category,
                        "action": action,
                        "value": value,
                        "reason": f"This {category} is a root cause of {'positive' if impact == 'positive' else 'negative'} performance in {', '.join(root_cause_metrics)}",
                        "confidence": 0.85,
                        "metrics_affected": root_cause_metrics
                    })
                    
                if has_forecast and forecast_trend != "stable":
                    action = "increase" if forecast_trend == "increasing" else "decrease"
                    
                    recommendations.append({
                        "type": "strategy",
                        "category": category,
                        "action": action,
                        "value": value,
                        "reason": f"This {category} shows a {forecast_trend} trend in {', '.join(forecast_metrics)}",
                        "confidence": 0.7,
                        "metrics_affected": forecast_metrics
                    })
                    
        return recommendations, strategy_adjustments
        
    async def generate_timing_recommendations(
        self, 
        df: pd.DataFrame, 
        insights: Dict[str, Any],
        processing_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate timing-related recommendations.
        
        Args:
            df: DataFrame with data
            insights: Insights from previous analyses
            processing_params: Parameters for processing
            
        Returns:
            List of timing recommendations
        """
        recommendations = []
        
        # Extract diagnostic insights
        diagnostic_insights = insights.get("diagnostic", {})
        strengths = diagnostic_insights.get("strengths", {}).get("factors", {})
        
        # Identify timing categories
        timing_categories = ["posting_time", "day_of_week", "season"]
        available_categories = [cat for cat in timing_categories if cat in df.columns]
        
        for category in available_categories:
            # Get unique values
            unique_values = df[category].unique()
            
            # Analyze each value
            for value in unique_values:
                if pd.isna(value):
                    continue
                    
                factor_id = f"{category}:{value}"
                
                # Check if this timing is a strength
                is_strength = False
                strength_metrics = []
                
                if category in strengths:
                    for key, strength in strengths[category].items():
                        if key.startswith(f"{factor_id}_"):
                            is_strength = True
                            metric = strength.get("metric")
                            if metric:
                                strength_metrics.append(metric)
                                
                # Generate recommendations based on insights
                if is_strength:
                    # Recommend optimal timing
                    recommendations.append({
                        "type": "timing",
                        "category": category,
                        "action": "optimize",
                        "value": value,
                        "reason": f"This {category} has shown strong performance in {', '.join(strength_metrics)}",
                        "confidence": 0.8,
                        "metrics_affected": strength_metrics
                    })
                    
        # Add seasonal recommendations if available
        if "season" in available_categories:
            current_month = datetime.now().month
            upcoming_season = ""
            
            if 3 <= current_month <= 5:
                upcoming_season = "summer"
            elif 6 <= current_month <= 8:
                upcoming_season = "fall"
            elif 9 <= current_month <= 11:
                upcoming_season = "winter"
            else:
                upcoming_season = "spring"
                
            # Check if we have data for the upcoming season
            if upcoming_season in df["season"].unique():
                recommendations.append({
                    "type": "timing",
                    "category": "season",
                    "action": "prepare",
                    "value": upcoming_season,
                    "reason": f"Prepare content for upcoming {upcoming_season} season",
                    "confidence": 0.75,
                    "metrics_affected": ["engagement", "conversion"]
                })
                
        return recommendations
        
    async def calculate_expected_impacts(
        self, 
        recommendations: List[Dict[str, Any]], 
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate expected impacts of recommendations.
        
        Args:
            recommendations: List of recommendations
            insights: Insights from previous analyses
            
        Returns:
            Dictionary of expected impacts
        """
        expected_impacts = {}
        
        # Extract diagnostic insights
        diagnostic_insights = insights.get("diagnostic", {})
        strengths = diagnostic_insights.get("strengths", {}).get("factors", {})
        weaknesses = diagnostic_insights.get("weaknesses", {}).get("factors", {})
        
        # Calculate impact for each recommendation
        for i, recommendation in enumerate(recommendations):
            recommendation_id = f"rec_{i}"
            category = recommendation.get("category")
            value = recommendation.get("value")
            action = recommendation.get("action")
            metrics_affected = recommendation.get("metrics_affected", [])
            
            factor_id = f"{category}:{value}"
            
            # Initialize impact
            impact = {
                "metrics": {},
                "overall_score": 0.0,
                "confidence": recommendation.get("confidence", 0.5)
            }
            
            # Calculate impact for each affected metric
            for metric in metrics_affected:
                # Default impact values
                percent_change = 0.0
                confidence = 0.5
                
                # Check if we have strength data for this factor and metric
                if category in strengths:
                    key = f"{factor_id}_{metric}"
                    if key in strengths[category]:
                        strength = strengths[category][key]
                        percent_diff = strength.get("percent_diff", 0)
                        
                        if action == "increase":
                            # Increasing a strength
                            percent_change = min(percent_diff * 0.5, 30.0)  # Cap at 30%
                            confidence = 0.7
                        elif action == "decrease":
                            # Decreasing a strength
                            percent_change = -min(percent_diff * 0.3, 20.0)  # Cap at -20%
                            confidence = 0.6
                            
                # Check if we have weakness data for this factor and metric
                if category in weaknesses:
                    key = f"{factor_id}_{metric}"
                    if key in weaknesses[category]:
                        weakness = weaknesses[category][key]
                        percent_diff = weakness.get("percent_diff", 0)
                        
                        if action == "decrease":
                            # Decreasing a weakness
                            percent_change = -min(percent_diff * 0.5, 30.0)  # Cap at 30%
                            confidence = 0.7
                        elif action == "increase":
                            # Increasing a weakness
                            percent_change = min(percent_diff * 0.3, 20.0)  # Cap at 20%
                            confidence = 0.5
                            
                # Store impact for this metric
                impact["metrics"][metric] = {
                    "percent_change": float(percent_change),
                    "confidence": float(confidence)
                }
                
            # Calculate overall impact score
            if impact["metrics"]:
                avg_percent_change = np.mean([m["percent_change"] for m in impact["metrics"].values()])
                avg_confidence = np.mean([m["confidence"] for m in impact["metrics"].values()])
                
                impact["overall_score"] = avg_percent_change * avg_confidence
                impact["confidence"] = avg_confidence
                
            expected_impacts[recommendation_id] = impact
            
        return expected_impacts
        
    async def optimize_recommendations(
        self, 
        recommendations: List[Dict[str, Any]],
        expected_impacts: Dict[str, Any],
        optimization_method: str,
        processing_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Optimize recommendations based on expected impacts.
        
        Args:
            recommendations: List of recommendations
            expected_impacts: Dictionary of expected impacts
            optimization_method: Method for optimization
            processing_params: Parameters for processing
            
        Returns:
            Optimized list of recommendations
        """
        # If no recommendations or impacts, return as is
        if not recommendations or not expected_impacts:
            return recommendations
            
        # Add impact scores to recommendations
        for i, recommendation in enumerate(recommendations):
            recommendation_id = f"rec_{i}"
            if recommendation_id in expected_impacts:
                recommendation["impact_score"] = expected_impacts[recommendation_id].get("overall_score", 0)
                recommendation["impact_confidence"] = expected_impacts[recommendation_id].get("confidence", 0.5)
                
        # Simple optimization: sort by impact score
        if optimization_method == "impact_score":
            return sorted(recommendations, key=lambda x: abs(x.get("impact_score", 0)), reverse=True)
            
        # Confidence-weighted optimization
        if optimization_method == "confidence_weighted":
            return sorted(recommendations, key=lambda x: abs(x.get("impact_score", 0)) * x.get("impact_confidence", 0.5), reverse=True)
            
        # Balanced optimization: consider both impact and diversity of recommendation types
        if optimization_method == "balanced":
            # Group recommendations by type
            grouped = defaultdict(list)
            for rec in recommendations:
                grouped[rec.get("type", "other")].append(rec)
                
            # Sort each group by impact score
            for group in grouped.values():
                group.sort(key=lambda x: abs(x.get("impact_score", 0)), reverse=True)
                
            # Interleave recommendations from different groups
            optimized = []
            max_per_group = max(len(group) for group in grouped.values())
            
            for i in range(max_per_group):
                for group_type in ["content", "strategy", "timing", "other"]:
                    group = grouped.get(group_type, [])
                    if i < len(group):
                        optimized.append(group[i])
                        
            return optimized
            
        # Default: return original recommendations
        return recommendations
        
    def prioritize_actions(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize actions based on recommendations.
        
        Args:
            recommendations: List of recommendations
            
        Returns:
            Prioritized list of actions
        """
        # If no recommendations, return empty list
        if not recommendations:
            return []
            
        # Convert recommendations to actions
        actions = []
        
        for i, recommendation in enumerate(recommendations):
            category = recommendation.get("category", "")
            value = recommendation.get("value", "")
            action_type = recommendation.get("action", "")
            reason = recommendation.get("reason", "")
            confidence = recommendation.get("confidence", 0.5)
            impact_score = recommendation.get("impact_score", 0)
            
            # Create action
            action = {
                "id": f"action_{i}",
                "description": f"{action_type.capitalize()} {category} '{value}'",
                "details": reason,
                "priority_score": abs(impact_score) * confidence,
                "confidence": confidence,
                "impact": impact_score,
                "recommendation_type": recommendation.get("type", "other"),
                "metrics_affected": recommendation.get("metrics_affected", [])
            }
            
            actions.append(action)
            
        # Sort actions by priority score
        actions.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Add priority level
        for i, action in enumerate(actions):
            if i < len(actions) // 3:
                action["priority_level"] = "high"
            elif i < 2 * len(actions) // 3:
                action["priority_level"] = "medium"
            else:
                action["priority_level"] = "low"
                
        return actions
        
    async def assign_factors_to_recommendations(
        self, 
        recommendations: List[Dict[str, Any]], 
        template_id: str
    ) -> None:
        """
        Assign factors to recommendations.
        
        Args:
            recommendations: List of recommendations
            template_id: Template ID
        """
        for recommendation in recommendations:
            category = recommendation.get("category")
            value = recommendation.get("value")
            
            if not category or not value:
                continue
                
            # Create factor ID
            factor_id = f"factor_{category}_{value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if factor exists
            existing_factor = await self.category_repository.get_factor(factor_id)
            
            if not existing_factor:
                # Create new factor
                factor_data = {
                    "factor_name": f"{category}:{value}",
                    "category_id": category,
                    "value": value,
                    "template_id": template_id,
                    "factor_type": "prescriptive",
                    "recommendation": {
                        "action": recommendation.get("action"),
                        "reason": recommendation.get("reason"),
                        "confidence": recommendation.get("confidence"),
                        "metrics_affected": recommendation.get("metrics_affected", [])
                    }
                }
                await self.category_repository.store_factor(factor_id, factor_data)
                
            # Link factor to entities if applicable
            if "entity_type" in recommendation and "entity_id" in recommendation:
                entity_type = recommendation["entity_type"]
                entity_id = recommendation["entity_id"]
                
                await self.category_repository.link_factor_to_entity(factor_id, entity_type, entity_id)
                
    async def store_results(self, results: Dict[str, Any], template_id: str) -> None:
        """
        Store analysis results in the repository.
        
        Args:
            results: Analysis results
            template_id: Template ID
        """
        # Store as analysis result
        await self.category_repository.store_analysis_result(
            "prescriptive",
            template_id,
            results
        )
        
        # For backward compatibility, also store as a factor
        factor_id = f"prescriptive_{template_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        factor_data = {
            "template_id": template_id,
            "factor_type": "prescriptive",
            "recommendations": results.get("recommendations", []),
            "strategy_adjustments": results.get("strategy_adjustments", {}),
            "expected_impacts": results.get("expected_impacts", {}),
            "prioritized_actions": results.get("prioritized_actions", [])
        }
        
        await self.category_repository.store_factor(factor_id, factor_data)
        
    async def prescribe_batches(
        self, 
        data: Dict[str, Any], 
        processing_params: Dict[str, Any], 
        template: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate prescriptions for batches.
        
        Args:
            data: Data containing performance metrics
            processing_params: Parameters for processing
            template: Original template
            insights: Insights from previous analyses
            
        Returns:
            Prescription results for batches
        """
        # Initialize results
        results = {
            "recommendations": [],
            "strategy_adjustments": {},
            "expected_impacts": {}
        }
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for batch prescriptions")
            return results
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Check if batch_id column exists
        if "batch_id" not in df.columns:
            logger.warning("No batch_id column found for batch prescriptions")
            return results
            
        # Get unique batch IDs
        unique_batches = df["batch_id"].unique()
        
        # Get optimization method
        optimization_method = processing_params.get("optimization_method", "rule_based")
        
        # Get recommendation types to generate
        recommendation_types = processing_params.get("recommendation_types", ["content_mix", "scheduling", "targeting"])
        
        # Generate batch recommendations
        batch_recommendations = await self.generate_batch_recommendations(
            df, 
            unique_batches, 
            insights, 
            recommendation_types, 
            processing_params
        )
        
        results["recommendations"].extend(batch_recommendations)
        
        # Generate batch strategy adjustments
        batch_strategy_adjustments = await self.generate_batch_strategy_adjustments(
            df, 
            unique_batches, 
            insights, 
            processing_params
        )
        
        results["strategy_adjustments"].update(batch_strategy_adjustments)
        
        # Calculate expected impacts
        results["expected_impacts"] = await self.calculate_expected_impacts(
            results["recommendations"], 
            insights
        )
        
        # Optimize recommendations if needed
        if optimization_method != "rule_based" and len(results["recommendations"]) > 0:
            results["recommendations"] = await self.optimize_recommendations(
                results["recommendations"],
                results["expected_impacts"],
                optimization_method,
                processing_params
            )
            
        # Assign batches to recommendations
        for recommendation in results["recommendations"]:
            if "entity_id" in recommendation and "entity_type" in recommendation and recommendation["entity_type"] == "batch":
                # Update Secret Sauce with recommendations
                await self.update_batch_secret_sauce(recommendation["entity_id"], recommendation, template.get("template_id", ""))
                
        return results
        
    async def prescribe_users(
        self, 
        data: Dict[str, Any], 
        processing_params: Dict[str, Any], 
        template: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate prescriptions for users.
        
        Args:
            data: Data containing performance metrics
            processing_params: Parameters for processing
            template: Original template
            insights: Insights from previous analyses
            
        Returns:
            Prescription results for users
        """
        # Initialize results
        results = {
            "recommendations": [],
            "strategy_adjustments": {},
            "expected_impacts": {}
        }
        
        # Extract data points
        data_points = data.get("data", [])
        if not data_points:
            logger.warning("No data points found for user prescriptions")
            return results
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Check if user_id column exists
        if "user_id" not in df.columns:
            logger.warning("No user_id column found for user prescriptions")
            return results
            
        # Get unique user IDs
        unique_users = df["user_id"].unique()
        
        # Get optimization method
        optimization_method = processing_params.get("optimization_method", "rule_based")
        
        # Get recommendation types to generate
        recommendation_types = processing_params.get("recommendation_types", ["personalization", "engagement", "content_preference"])
        
        # Generate user recommendations
        user_recommendations = await self.generate_user_recommendations(
            df, 
            unique_users, 
            insights, 
            recommendation_types, 
            processing_params
        )
        
        results["recommendations"].extend(user_recommendations)
        
        # Calculate expected impacts
        results["expected_impacts"] = await self.calculate_expected_impacts(
            results["recommendations"], 
            insights
        )
        
        # Optimize recommendations if needed
        if optimization_method != "rule_based" and len(results["recommendations"]) > 0:
            results["recommendations"] = await self.optimize_recommendations(
                results["recommendations"],
                results["expected_impacts"],
                optimization_method,
                processing_params
            )
            
        # Assign factors to users based on recommendations
        for recommendation in results["recommendations"]:
            if "entity_id" in recommendation and "entity_type" in recommendation and recommendation["entity_type"] == "user":
                await self.assign_recommendation_to_user(recommendation, template.get("template_id", ""))
                
        return results
        
    async def generate_batch_recommendations(
        self, 
        df: pd.DataFrame, 
        batch_ids: np.ndarray, 
        insights: Dict[str, Any],
        recommendation_types: List[str],
        processing_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for batches.
        
        Args:
            df: DataFrame with data
            batch_ids: Array of batch IDs
            insights: Insights from previous analyses
            recommendation_types: Types of recommendations to generate
            processing_params: Parameters for processing
            
        Returns:
            List of batch recommendations
        """
        recommendations = []
        
        # Extract diagnostic insights
        diagnostic_insights = insights.get("diagnostic", {})
        batch_strengths = diagnostic_insights.get("strengths", {}).get("batches", {})
        batch_weaknesses = diagnostic_insights.get("weaknesses", {}).get("batches", {})
        batch_root_causes = diagnostic_insights.get("root_causes", {}).get("batches", {})
        
        # Extract predictive insights
        predictive_insights = insights.get("predictive", {})
        batch_forecasts = predictive_insights.get("ensemble_forecast", {}).get("batches", {})
        batch_risk_scores = predictive_insights.get("risk_scores", {}).get("batches", {})
        
        # Process each batch
        for batch_id in batch_ids:
            if pd.isna(batch_id):
                continue
                
            batch_id_str = str(batch_id)
            
            # Filter data for this batch
            batch_data = df[df["batch_id"] == batch_id]
            
            if len(batch_data) == 0:
                continue
                
            # Generate content mix recommendations
            if "content_mix" in recommendation_types:
                # Find best performing content types in this batch
                content_categories = ["caption_type", "media_type", "hashtag_strategy", "image_style"]
                available_categories = [cat for cat in content_categories if cat in df.columns]
                
                for category in available_categories:
                    # Calculate performance by category value
                    if "engagement" in df.columns:
                        top_performers = batch_data.groupby(category)["engagement"].mean().sort_values(ascending=False)
                        
                        if len(top_performers) > 0:
                            top_value = top_performers.index[0]
                            
                            recommendations.append({
                                "type": "content_mix",
                                "entity_type": "batch",
                                "entity_id": batch_id_str,
                                "category": category,
                                "action": "optimize",
                                "value": top_value,
                                "reason": f"This {category} performs best in batch {batch_id_str}",
                                "confidence": 0.75,
                                "metrics_affected": ["engagement"]
                            })
                            
            # Generate scheduling recommendations
            if "scheduling" in recommendation_types:
                # Check if we have timing columns
                timing_categories = ["posting_time", "day_of_week"]
                available_timing = [cat for cat in timing_categories if cat in df.columns]
                
                for category in available_timing:
                    if "engagement" in df.columns:
                        timing_performance = batch_data.groupby(category)["engagement"].mean().sort_values(ascending=False)
                        
                        if len(timing_performance) > 0:
                            best_timing = timing_performance.index[0]
                            
                            recommendations.append({
                                "type": "scheduling",
                                "entity_type": "batch",
                                "entity_id": batch_id_str,
                                "category": category,
                                "action": "optimize",
                                "value": best_timing,
                                "reason": f"This {category} shows higher engagement in batch {batch_id_str}",
                                "confidence": 0.8,
                                "metrics_affected": ["engagement"]
                            })
                            
            # Generate targeting recommendations
            if "targeting" in recommendation_types:
                # Check if we have audience columns
                audience_categories = ["target_audience", "demographic"]
                available_audience = [cat for cat in audience_categories if cat in df.columns]
                
                for category in available_audience:
                    if "conversion" in df.columns:
                        audience_performance = batch_data.groupby(category)["conversion"].mean().sort_values(ascending=False)
                        
                        if len(audience_performance) > 0:
                            best_audience = audience_performance.index[0]
                            
                            recommendations.append({
                                "type": "targeting",
                                "entity_type": "batch",
                                "entity_id": batch_id_str,
                                "category": category,
                                "action": "focus",
                                "value": best_audience,
                                "reason": f"This {category} shows higher conversion in batch {batch_id_str}",
                                "confidence": 0.7,
                                "metrics_affected": ["conversion"]
                            })
                            
            # Check batch strengths and weaknesses
            if batch_id_str in batch_strengths:
                # Recommend leveraging strengths
                for metric, strength in batch_strengths[batch_id_str].items():
                    recommendations.append({
                        "type": "strategy",
                        "entity_type": "batch",
                        "entity_id": batch_id_str,
                        "category": "performance",
                        "action": "leverage",
                        "value": metric,
                        "reason": f"Batch {batch_id_str} shows strength in {metric}",
                        "confidence": 0.85,
                        "metrics_affected": [metric]
                    })
                    
            if batch_id_str in batch_weaknesses:
                # Recommend addressing weaknesses
                for metric, weakness in batch_weaknesses[batch_id_str].items():
                    recommendations.append({
                        "type": "strategy",
                        "entity_type": "batch",
                        "entity_id": batch_id_str,
                        "category": "performance",
                        "action": "improve",
                        "value": metric,
                        "reason": f"Batch {batch_id_str} shows weakness in {metric}",
                        "confidence": 0.75,
                        "metrics_affected": [metric]
                    })
                    
            # Check root causes
            if batch_id_str in batch_root_causes:
                # Recommend addressing root causes
                for factor_key, root_cause in batch_root_causes[batch_id_str].items():
                    category, value = factor_key.split(":")
                    impact = root_cause.get("impact", "positive")
                    action = "increase" if impact == "positive" else "decrease"
                    
                    recommendations.append({
                        "type": "root_cause",
                        "entity_type": "batch",
                        "entity_id": batch_id_str,
                        "category": category,
                        "action": action,
                        "value": value,
                        "reason": f"This is a {impact} root cause for batch {batch_id_str}",
                        "confidence": 0.85,
                        "metrics_affected": root_cause.get("related_to", [])
                    })
                    
            # Check risk scores
            if "batch_id" in batch_risk_scores and batch_id_str in batch_risk_scores["batch_id"]:
                for metric, risk in batch_risk_scores["batch_id"][batch_id_str].items():
                    if risk.get("score", 0) > 0.6:  # High risk threshold
                        recommendations.append({
                            "type": "risk_mitigation",
                            "entity_type": "batch",
                            "entity_id": batch_id_str,
                            "category": "risk",
                            "action": "mitigate",
                            "value": metric,
                            "reason": f"Batch {batch_id_str} shows high risk in {metric}",
                            "confidence": 0.7,
                            "metrics_affected": [metric]
                        })
                        
        return recommendations
        
    async def generate_batch_strategy_adjustments(
        self, 
        df: pd.DataFrame, 
        batch_ids: np.ndarray, 
        insights: Dict[str, Any],
        processing_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate strategy adjustments for batches.
        
        Args:
            df: DataFrame with data
            batch_ids: Array of batch IDs
            insights: Insights from previous analyses
            processing_params: Parameters for processing
            
        Returns:
            Dictionary of batch strategy adjustments
        """
        strategy_adjustments = {
            "batch_focus": [],
            "resource_allocation": {},
            "risk_mitigation": []
        }
        
        # Extract predictive insights
        predictive_insights = insights.get("predictive", {})
        batch_forecasts = predictive_insights.get("ensemble_forecast", {}).get("batches", {})
        batch_risk_scores = predictive_insights.get("risk_scores", {}).get("batches", {})
        
        # Calculate batch performance scores
        batch_scores = {}
        
        if "engagement" in df.columns:
            for batch_id in batch_ids:
                if pd.isna(batch_id):
                    continue
                    
                batch_id_str = str(batch_id)
                batch_data = df[df["batch_id"] == batch_id]
                
                if len(batch_data) > 0:
                    # Calculate performance score
                    engagement_score = batch_data["engagement"].mean()
                    
                    # Add forecast trend if available
                    trend_bonus = 0.0
                    if "batch_id" in batch_forecasts and batch_id_str in batch_forecasts["batch_id"]:
                        for metric, forecast in batch_forecasts["batch_id"][batch_id_str].items():
                            if metric == "engagement" and len(forecast) > 1:
                                first_half = np.mean(forecast[:len(forecast)//2])
                                second_half = np.mean(forecast[len(forecast)//2:])
                                
                                if second_half > first_half * 1.1:
                                    trend_bonus = 0.2  # 20% bonus for increasing trend
                                elif second_half < first_half * 0.9:
                                    trend_bonus = -0.1  # 10% penalty for decreasing trend
                                    
                    # Calculate risk penalty
                    risk_penalty = 0.0
                    if "batch_id" in batch_risk_scores and batch_id_str in batch_risk_scores["batch_id"]:
                        for metric, risk in batch_risk_scores["batch_id"][batch_id_str].items():
                            if metric == "engagement":
                                risk_penalty = min(0.3, risk.get("score", 0) * 0.5)  # Up to 30% penalty
                                
                    # Final batch score
                    batch_scores[batch_id_str] = engagement_score * (1 + trend_bonus - risk_penalty)
                    
        # Identify top performing batches
        if batch_scores:
            sorted_batches = sorted(batch_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Add top batches to focus
            for batch_id, score in sorted_batches[:3]:  # Top 3 batches
                strategy_adjustments["batch_focus"].append({
                    "batch_id": batch_id,
                    "score": float(score),
                    "reason": "High performance and growth potential"
                })
                
            # Allocate resources based on batch scores
            total_score = sum(score for _, score in sorted_batches)
            
            if total_score > 0:
                for batch_id, score in sorted_batches:
                    allocation = (score / total_score) * 100
                    strategy_adjustments["resource_allocation"][batch_id] = round(allocation, 1)
                    
            # Identify high risk batches
            high_risk_batches = []
            
            if "batch_id" in batch_risk_scores:
                for batch_id_str in batch_risk_scores["batch_id"]:
                    batch_risks = batch_risk_scores["batch_id"][batch_id_str]
                    avg_risk = np.mean([risk.get("score", 0) for risk in batch_risks.values()])
                    
                    if avg_risk > 0.6:  # High risk threshold
                        high_risk_batches.append({
                            "batch_id": batch_id_str,
                            "risk_score": float(avg_risk),
                            "metrics_at_risk": list(batch_risks.keys())
                        })
                        
            strategy_adjustments["risk_mitigation"] = high_risk_batches
            
        return strategy_adjustments
        
    async def generate_user_recommendations(
        self, 
        df: pd.DataFrame, 
        user_ids: np.ndarray, 
        insights: Dict[str, Any],
        recommendation_types: List[str],
        processing_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for users.
        
        Args:
            df: DataFrame with data
            user_ids: Array of user IDs
            insights: Insights from previous analyses
            recommendation_types: Types of recommendations to generate
            processing_params: Parameters for processing
            
        Returns:
            List of user recommendations
        """
        recommendations = []
        
        # Extract diagnostic insights
        diagnostic_insights = insights.get("diagnostic", {})
        user_strengths = diagnostic_insights.get("strengths", {}).get("users", {})
        user_weaknesses = diagnostic_insights.get("weaknesses", {}).get("users", {})
        
        # Extract predictive insights
        predictive_insights = insights.get("predictive", {})
        user_forecasts = predictive_insights.get("ensemble_forecast", {}).get("users", {})
        user_risk_scores = predictive_insights.get("risk_scores", {}).get("users", {})
        
        # Process each user
        for user_id in user_ids:
            if pd.isna(user_id):
                continue
                
            user_id_str = str(user_id)
            
            # Filter data for this user
            user_data = df[df["user_id"] == user_id]
            
            if len(user_data) == 0:
                continue
                
            # Generate personalization recommendations
            if "personalization" in recommendation_types:
                # Find content preferences
                content_categories = ["caption_type", "media_type", "hashtag_strategy", "image_style"]
                available_categories = [cat for cat in content_categories if cat in df.columns]
                
                for category in available_categories:
                    if len(user_data[category].dropna()) > 0:
                        # Get most common value for this user
                        preferred_value = user_data[category].value_counts().index[0]
                        
                        recommendations.append({
                            "type": "personalization",
                            "entity_type": "user",
                            "entity_id": user_id_str,
                            "category": category,
                            "action": "personalize",
                            "value": preferred_value,
                            "reason": f"User {user_id_str} appears to prefer this {category}",
                            "confidence": 0.7,
                            "metrics_affected": ["engagement"]
                        })
                        
            # Generate engagement recommendations
            if "engagement" in recommendation_types:
                # Check past engagement
                if "engagement" in df.columns:
                    user_engagement = user_data["engagement"].mean()
                    overall_engagement = df["engagement"].mean()
                    
                    if user_engagement < overall_engagement * 0.8:  # Low engagement
                        recommendations.append({
                            "type": "engagement",
                            "entity_type": "user",
                            "entity_id": user_id_str,
                            "category": "engagement",
                            "action": "boost",
                            "value": "low_engagement",
                            "reason": f"User {user_id_str} shows lower than average engagement",
                            "confidence": 0.75,
                            "metrics_affected": ["engagement"]
                        })
                        
            # Generate content preference recommendations
            if "content_preference" in recommendation_types:
                # Find highest engagement content types
                if "engagement" in df.columns:
                    content_categories = ["caption_type", "media_type", "hashtag_strategy", "image_style"]
                    available_categories = [cat for cat in content_categories if cat in df.columns]
                    
                    for category in available_categories:
                        if len(user_data) >= 5:  # Need minimum data points
                            engagement_by_type = user_data.groupby(category)["engagement"].mean()
                            
                            if len(engagement_by_type) > 1:
                                best_type = engagement_by_type.idxmax()
                                
                                recommendations.append({
                                    "type": "content_preference",
                                    "entity_type": "user",
                                    "entity_id": user_id_str,
                                    "category": category,
                                    "action": "target",
                                    "value": best_type,
                                    "reason": f"User {user_id_str} engages most with this {category}",
                                    "confidence": 0.8,
                                    "metrics_affected": ["engagement"]
                                })
                                
            # Check user strengths and weaknesses
            if user_id_str in user_strengths:
                # Recommend leveraging strengths
                for metric, strength in user_strengths[user_id_str].items():
                    recommendations.append({
                        "type": "strategy",
                        "entity_type": "user",
                        "entity_id": user_id_str,
                        "category": "performance",
                        "action": "leverage",
                        "value": metric,
                        "reason": f"User {user_id_str} shows strength in {metric}",
                        "confidence": 0.8,
                        "metrics_affected": [metric]
                    })
                    
            # Check risk scores
            if "user_id" in user_risk_scores and user_id_str in user_risk_scores["user_id"]:
                for metric, risk in user_risk_scores["user_id"][user_id_str].items():
                    if risk.get("score", 0) > 0.7:  # High risk threshold
                        recommendations.append({
                            "type": "risk_mitigation",
                            "entity_type": "user",
                            "entity_id": user_id_str,
                            "category": "risk",
                            "action": "mitigate",
                            "value": metric,
                            "reason": f"User {user_id_str} shows high risk in {metric}",
                            "confidence": 0.7,
                            "metrics_affected": [metric]
                        })
                        
        return recommendations
        
    async def update_batch_secret_sauce(
        self, 
        batch_id: str, 
        recommendation: Dict[str, Any],
        template_id: str
    ) -> None:
        """
        Update Secret Sauce for a batch with recommendation.
        
        Args:
            batch_id: Batch ID
            recommendation: Recommendation data
            template_id: Template ID
        """
        # Get existing Secret Sauce
        secret_sauces = await self.category_repository.get_secret_sauce_by_entity("batch", batch_id)
        
        if secret_sauces and len(secret_sauces) > 0:
            # Update existing Secret Sauce
            secret_sauce = secret_sauces[0]
            secret_sauce_id = secret_sauce.get("secret_sauce_id")
            
            # Initialize prescriptive section if not exists
            if "prescriptive" not in secret_sauce:
                secret_sauce["prescriptive"] = {
                    "recommendations": [],
                    "template_id": template_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Add recommendation to list
            secret_sauce["prescriptive"]["recommendations"].append(recommendation)
            
            # Update timestamp
            secret_sauce["prescriptive"]["timestamp"] = datetime.now().isoformat()
            
            # Update Secret Sauce
            await self.category_repository.update_secret_sauce(secret_sauce_id, secret_sauce)
        else:
            # Create new Secret Sauce
            secret_sauce_data = {
                "batch_id": batch_id,
                "template_id": template_id,
                "prescriptive": {
                    "recommendations": [recommendation],
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await self.category_repository.store_secret_sauce(secret_sauce_data)
            
    async def assign_recommendation_to_user(
        self, 
        recommendation: Dict[str, Any],
        template_id: str
    ) -> None:
        """
        Assign recommendation to a user by creating and linking a factor.
        
        Args:
            recommendation: Recommendation data
            template_id: Template ID
        """
        user_id = recommendation.get("entity_id")
        category = recommendation.get("category")
        value = recommendation.get("value")
        
        if not user_id or not category or not value:
            return
            
        # Create factor ID
        factor_id = f"factor_{category}_{value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Check if factor exists
        existing_factor = await self.category_repository.get_factor(factor_id)
        
        if not existing_factor:
            # Create new factor
            factor_data = {
                "factor_name": f"{category}:{value}",
                "category_id": category,
                "value": value,
                "template_id": template_id,
                "factor_type": "prescriptive",
                "recommendation": {
                    "action": recommendation.get("action"),
                    "reason": recommendation.get("reason"),
                    "confidence": recommendation.get("confidence"),
                    "metrics_affected": recommendation.get("metrics_affected", [])
                }
            }
            await self.category_repository.store_factor(factor_id, factor_data)
            
        # Link factor to user
        await self.category_repository.link_factor_to_entity(factor_id, "user", user_id)

async def create_worker(category_repository: CategoryRepository = None) -> PrescriptiveWorker:
    """
    Create and initialize a prescriptive worker.
    
    Args:
        category_repository: Optional category repository
        
    Returns:
        Initialized PrescriptiveWorker
    """
    if category_repository is None:
        # Initialize a new category repository
        mongodb_uri = "mongodb://mongodb:27017"  # Use environment variables in production
        category_repository = CategoryRepository(mongodb_uri=mongodb_uri)
        await category_repository.connect()
        
    return PrescriptiveWorker(category_repository) 