"""
Analytics API endpoints.

This module provides comprehensive analytics and reporting endpoints
for the outreach system, including campaign metrics, conversation insights,
and performance analytics.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ...models.schemas import CampaignResponse, ConversationResponse
from ...services.analytics_service import AnalyticsService
from ...config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_analytics_service() -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService()


@router.get("/campaigns")
async def get_campaign_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    campaign_id: Optional[UUID] = Query(None, description="Specific campaign ID"),
    group_by: Optional[str] = Query("day", description="Grouping (day, week, month)"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive campaign analytics."""
    try:
        logger.info("Getting campaign analytics")
        analytics = await service.get_campaign_analytics(
            start_date=start_date,
            end_date=end_date,
            campaign_id=campaign_id,
            group_by=group_by
        )
        return analytics
    except Exception as e:
        logger.error(f"Failed to get campaign analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign analytics: {str(e)}"
        )


@router.get("/conversations")
async def get_conversation_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    conversation_id: Optional[UUID] = Query(None, description="Specific conversation ID"),
    group_by: Optional[str] = Query("day", description="Grouping (day, week, month)"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive conversation analytics."""
    try:
        logger.info("Getting conversation analytics")
        analytics = await service.get_conversation_analytics(
            start_date=start_date,
            end_date=end_date,
            conversation_id=conversation_id,
            group_by=group_by
        )
        return analytics
    except Exception as e:
        logger.error(f"Failed to get conversation analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation analytics: {str(e)}"
        )


@router.get("/performance")
async def get_performance_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get system performance analytics."""
    try:
        logger.info("Getting performance analytics")
        analytics = await service.get_performance_analytics(
            start_date=start_date,
            end_date=end_date
        )
        return analytics
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance analytics: {str(e)}"
        )


@router.get("/models")
async def get_model_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    model_type: Optional[str] = Query(None, description="Specific model type"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get AI model performance analytics."""
    try:
        logger.info("Getting model analytics")
        analytics = await service.get_model_analytics(
            start_date=start_date,
            end_date=end_date,
            model_type=model_type
        )
        return analytics
    except Exception as e:
        logger.error(f"Failed to get model analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model analytics: {str(e)}"
        )


@router.get("/emotions")
async def get_emotion_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    emotion_category: Optional[str] = Query(None, description="Specific emotion category"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get emotion detection analytics."""
    try:
        logger.info("Getting emotion analytics")
        analytics = await service.get_emotion_analytics(
            start_date=start_date,
            end_date=end_date,
            emotion_category=emotion_category
        )
        return analytics
    except Exception as e:
        logger.error(f"Failed to get emotion analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emotion analytics: {str(e)}"
        )


@router.get("/realtime")
async def get_realtime_metrics(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get real-time system metrics."""
    try:
        logger.info("Getting real-time metrics")
        metrics = await service.get_realtime_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get real-time metrics: {str(e)}"
        )


@router.get("/dashboard")
async def get_dashboard_data(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive dashboard data."""
    try:
        logger.info("Getting dashboard data")
        dashboard_data = await service.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/reports/campaign/{campaign_id}")
async def get_campaign_report(
    campaign_id: UUID,
    report_type: str = Query("summary", description="Report type (summary, detailed, performance)"),
    format: str = Query("json", description="Report format (json, csv, pdf)"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Generate campaign report."""
    try:
        logger.info(f"Generating campaign report for {campaign_id}")
        report = await service.generate_campaign_report(
            campaign_id=campaign_id,
            report_type=report_type,
            format=format
        )
        return report
    except Exception as e:
        logger.error(f"Failed to generate campaign report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate campaign report: {str(e)}"
        )


@router.get("/reports/conversation/{conversation_id}")
async def get_conversation_report(
    conversation_id: UUID,
    report_type: str = Query("summary", description="Report type (summary, detailed, transcript)"),
    format: str = Query("json", description="Report format (json, csv, pdf)"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Generate conversation report."""
    try:
        logger.info(f"Generating conversation report for {conversation_id}")
        report = await service.generate_conversation_report(
            conversation_id=conversation_id,
            report_type=report_type,
            format=format
        )
        return report
    except Exception as e:
        logger.error(f"Failed to generate conversation report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate conversation report: {str(e)}"
        )


@router.get("/insights")
async def get_insights(
    insight_type: str = Query("general", description="Type of insights (general, campaign, conversation)"),
    limit: int = Query(10, ge=1, le=100, description="Number of insights to return"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get AI-powered insights and recommendations."""
    try:
        logger.info(f"Getting insights of type: {insight_type}")
        insights = await service.get_insights(
            insight_type=insight_type,
            limit=limit
        )
        return insights
    except Exception as e:
        logger.error(f"Failed to get insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights: {str(e)}"
        )


@router.get("/trends")
async def get_trends(
    trend_type: str = Query("engagement", description="Type of trends (engagement, performance, emotions)"),
    period: str = Query("7d", description="Time period (1d, 7d, 30d, 90d)"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get trend analysis."""
    try:
        logger.info(f"Getting trends of type: {trend_type}")
        trends = await service.get_trends(
            trend_type=trend_type,
            period=period
        )
        return trends
    except Exception as e:
        logger.error(f"Failed to get trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trends: {str(e)}"
        )


@router.get("/predictions")
async def get_predictions(
    prediction_type: str = Query("conversion", description="Type of predictions (conversion, engagement, churn)"),
    horizon: str = Query("7d", description="Prediction horizon (1d, 7d, 30d)"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get predictive analytics."""
    try:
        logger.info(f"Getting predictions of type: {prediction_type}")
        predictions = await service.get_predictions(
            prediction_type=prediction_type,
            horizon=horizon
        )
        return predictions
    except Exception as e:
        logger.error(f"Failed to get predictions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get predictions: {str(e)}"
        )


@router.post("/export")
async def export_analytics(
    export_config: Dict[str, Any],
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Export analytics data."""
    try:
        logger.info("Exporting analytics data")
        export_result = await service.export_analytics(export_config)
        return export_result
    except Exception as e:
        logger.error(f"Failed to export analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics: {str(e)}"
        ) 