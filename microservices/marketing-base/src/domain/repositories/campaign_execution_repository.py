"""
Campaign Execution Repository Interface.

This module defines the interface for repositories that handle
campaign execution data, including batches, journeys, and message deliveries.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from ..models.campaign_execution import (
    CampaignBatch,
    RecipientJourney,
    StageExecution,
    MessageDelivery,
    BatchStatus,
    JourneyStatus,
    MessageDeliveryStatus
)


class CampaignExecutionRepository(ABC):
    """
    Repository interface for campaign execution data.
    
    Defines methods for storing and retrieving data related to
    campaign execution, including batches, recipient journeys,
    stage executions, and message deliveries.
    """
    
    # Batch Operations
    @abstractmethod
    async def create_batch(self, batch: CampaignBatch) -> CampaignBatch:
        """
        Create a new campaign batch.
        
        Args:
            batch: The batch to create
            
        Returns:
            The created batch with any generated IDs
        """
        pass
    
    @abstractmethod
    async def get_batch(self, batch_id: str) -> Optional[CampaignBatch]:
        """
        Get a campaign batch by ID.
        
        Args:
            batch_id: The ID of the batch to retrieve
            
        Returns:
            The batch or None if not found
        """
        pass
    
    @abstractmethod
    async def update_batch(self, batch: CampaignBatch) -> CampaignBatch:
        """
        Update a campaign batch.
        
        Args:
            batch: The batch to update
            
        Returns:
            The updated batch
        """
        pass
    
    @abstractmethod
    async def get_batches_by_campaign(self, campaign_id: str, limit: int = 100, offset: int = 0) -> List[CampaignBatch]:
        """
        Get batches for a campaign.
        
        Args:
            campaign_id: The ID of the campaign
            limit: Maximum number of batches to return
            offset: Number of batches to skip
            
        Returns:
            List of batches for the campaign
        """
        pass
    
    @abstractmethod
    async def get_batches_by_status(self, status: Union[BatchStatus, List[BatchStatus]], limit: int = 100, offset: int = 0) -> List[CampaignBatch]:
        """
        Get batches by status.
        
        Args:
            status: The status or list of statuses to filter by
            limit: Maximum number of batches to return
            offset: Number of batches to skip
            
        Returns:
            List of batches matching the status
        """
        pass
    
    # Journey Operations
    @abstractmethod
    async def create_journey(self, journey: RecipientJourney) -> RecipientJourney:
        """
        Create a new recipient journey.
        
        Args:
            journey: The journey to create
            
        Returns:
            The created journey with any generated IDs
        """
        pass
    
    @abstractmethod
    async def get_journey(self, journey_id: str) -> Optional[RecipientJourney]:
        """
        Get a recipient journey by ID.
        
        Args:
            journey_id: The ID of the journey to retrieve
            
        Returns:
            The journey or None if not found
        """
        pass
    
    @abstractmethod
    async def update_journey(self, journey: RecipientJourney) -> RecipientJourney:
        """
        Update a recipient journey.
        
        Args:
            journey: The journey to update
            
        Returns:
            The updated journey
        """
        pass
    
    @abstractmethod
    async def get_journeys_by_batch(self, batch_id: str, limit: int = 100, offset: int = 0) -> List[RecipientJourney]:
        """
        Get journeys for a batch.
        
        Args:
            batch_id: The ID of the batch
            limit: Maximum number of journeys to return
            offset: Number of journeys to skip
            
        Returns:
            List of journeys for the batch
        """
        pass
    
    @abstractmethod
    async def get_journeys_by_recipient(self, recipient_id: str, limit: int = 100, offset: int = 0) -> List[RecipientJourney]:
        """
        Get journeys for a recipient.
        
        Args:
            recipient_id: The ID of the recipient
            limit: Maximum number of journeys to return
            offset: Number of journeys to skip
            
        Returns:
            List of journeys for the recipient
        """
        pass
    
    @abstractmethod
    async def get_journeys_by_status(self, status: Union[JourneyStatus, List[JourneyStatus]], limit: int = 100, offset: int = 0) -> List[RecipientJourney]:
        """
        Get journeys by status.
        
        Args:
            status: The status or list of statuses to filter by
            limit: Maximum number of journeys to return
            offset: Number of journeys to skip
            
        Returns:
            List of journeys matching the status
        """
        pass
    
    @abstractmethod
    async def get_journeys_for_next_stage(self, limit: int = 100) -> List[RecipientJourney]:
        """
        Get journeys that are ready for next stage execution.
        
        Finds journeys that are active and have completed their current stage
        or have waited the required time.
        
        Args:
            limit: Maximum number of journeys to return
            
        Returns:
            List of journeys ready for next stage processing
        """
        pass
    
    # Stage Execution Operations
    @abstractmethod
    async def add_stage_execution(self, journey_id: str, execution: StageExecution) -> StageExecution:
        """
        Add a stage execution to a journey.
        
        Args:
            journey_id: The ID of the journey
            execution: The stage execution to add
            
        Returns:
            The created stage execution with any generated IDs
        """
        pass
    
    @abstractmethod
    async def update_stage_execution(self, execution: StageExecution) -> StageExecution:
        """
        Update a stage execution.
        
        Args:
            execution: The stage execution to update
            
        Returns:
            The updated stage execution
        """
        pass
    
    @abstractmethod
    async def get_stage_executions_by_journey(self, journey_id: str) -> List[StageExecution]:
        """
        Get all stage executions for a journey.
        
        Args:
            journey_id: The ID of the journey
            
        Returns:
            List of stage executions for the journey
        """
        pass
    
    @abstractmethod
    async def get_pending_stage_executions(self, limit: int = 100) -> List[StageExecution]:
        """
        Get pending stage executions ready for processing.
        
        Args:
            limit: Maximum number of executions to return
            
        Returns:
            List of stage executions ready for processing
        """
        pass
    
    # Message Delivery Operations
    @abstractmethod
    async def create_message_delivery(self, delivery: MessageDelivery) -> MessageDelivery:
        """
        Create a new message delivery.
        
        Args:
            delivery: The message delivery to create
            
        Returns:
            The created message delivery with any generated IDs
        """
        pass
    
    @abstractmethod
    async def get_message_delivery(self, delivery_id: str) -> Optional[MessageDelivery]:
        """
        Get a message delivery by ID.
        
        Args:
            delivery_id: The ID of the message delivery to retrieve
            
        Returns:
            The message delivery or None if not found
        """
        pass
    
    @abstractmethod
    async def update_message_delivery(self, delivery: MessageDelivery) -> MessageDelivery:
        """
        Update a message delivery.
        
        Args:
            delivery: The message delivery to update
            
        Returns:
            The updated message delivery
        """
        pass
    
    @abstractmethod
    async def get_message_deliveries_by_journey(self, journey_id: str, limit: int = 100, offset: int = 0) -> List[MessageDelivery]:
        """
        Get message deliveries for a journey.
        
        Args:
            journey_id: The ID of the journey
            limit: Maximum number of deliveries to return
            offset: Number of deliveries to skip
            
        Returns:
            List of message deliveries for the journey
        """
        pass
    
    @abstractmethod
    async def get_message_deliveries_by_stage_execution(self, stage_execution_id: str) -> List[MessageDelivery]:
        """
        Get message deliveries for a stage execution.
        
        Args:
            stage_execution_id: The ID of the stage execution
            
        Returns:
            List of message deliveries for the stage execution
        """
        pass
    
    @abstractmethod
    async def get_message_deliveries_by_status(
        self, 
        status: Union[MessageDeliveryStatus, List[MessageDeliveryStatus]], 
        limit: int = 100, 
        offset: int = 0
    ) -> List[MessageDelivery]:
        """
        Get message deliveries by status.
        
        Args:
            status: The status or list of statuses to filter by
            limit: Maximum number of deliveries to return
            offset: Number of deliveries to skip
            
        Returns:
            List of message deliveries matching the status
        """
        pass
    
    @abstractmethod
    async def get_message_deliveries_by_tracking_id(self, tracking_id: str) -> List[MessageDelivery]:
        """
        Get message deliveries by tracking ID.
        
        Args:
            tracking_id: The tracking ID to look up
            
        Returns:
            List of message deliveries with the tracking ID
        """
        pass
    
    @abstractmethod
    async def get_pending_message_deliveries(self, limit: int = 100) -> List[MessageDelivery]:
        """
        Get pending message deliveries ready for sending.
        
        Args:
            limit: Maximum number of deliveries to return
            
        Returns:
            List of message deliveries ready for sending
        """
        pass
    
    @abstractmethod
    async def get_analytics_for_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a batch.
        
        Args:
            batch_id: The ID of the batch
            
        Returns:
            Analytics data for the batch
        """
        pass
    
    @abstractmethod
    async def get_analytics_for_campaign(self, campaign_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get analytics data for a campaign.
        
        Args:
            campaign_id: The ID of the campaign
            start_date: Optional start date for the analytics
            end_date: Optional end date for the analytics
            
        Returns:
            Analytics data for the campaign
        """
        pass
 