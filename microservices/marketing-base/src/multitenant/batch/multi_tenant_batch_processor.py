"""
Multi-Tenant Batch Processor Service.

This module provides a service for processing multi-tenant campaign batches,
allowing multiple tenants to use the same campaign template efficiently.
"""

import logging
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from ...config.app_config import get_config
from .multi_tenant_batch import (
    MultiTenantCampaignBatch,
    MultiTenantBatchStatus,
    TenantExecutionResult,
    TenantExecutionStatus
)
from .multi_tenant_batch_repository import MultiTenantBatchRepository
from ..context.tenant_context import TenantContext
from ...infrastructure.database.database_factory import DatabaseFactory
from ...application.services.campaign_service import CampaignService
from ...application.services.campaign_template_converter import CampaignTemplateConverter

logger = logging.getLogger(__name__)


class MultiTenantBatchProcessor:
    """
    Service for processing multi-tenant campaign batches.
    
    This service processes campaign templates across multiple tenants,
    managing tenant context switching and tenant-specific database access.
    """
    
    def __init__(
        self,
        batch_repository: Optional[MultiTenantBatchRepository] = None,
        campaign_service: Optional[CampaignService] = None,
        template_converter: Optional[CampaignTemplateConverter] = None
    ):
        """
        Initialize the multi-tenant batch processor.
        
        Args:
            batch_repository: Repository for multi-tenant batch operations
            campaign_service: Service for campaign operations
            template_converter: Service for template conversion
        """
        self.batch_repository = batch_repository or MultiTenantBatchRepository()
        self.campaign_service = campaign_service or CampaignService()
        self.template_converter = template_converter or CampaignTemplateConverter()
        self.config = get_config()
        
    async def close(self):
        """Close resources used by the processor."""
        try:
            if self.batch_repository:
                await self.batch_repository.close()
            logger.info("Closed multi-tenant batch processor resources")
        except Exception as e:
            logger.error(f"Error closing multi-tenant batch processor resources: {str(e)}")
    
    async def process_pending_batches(self, limit: int = 5) -> Dict[str, int]:
        """
        Process pending multi-tenant campaign batches.
        
        Args:
            limit: Maximum number of batches to process
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"Processing up to {limit} pending multi-tenant campaign batches")
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
        
        # Get pending batches
        pending_batches = await self.batch_repository.get_pending_batches(limit=limit)
        stats["total"] = len(pending_batches)
        
        if not pending_batches:
            logger.info("No pending multi-tenant batches found")
            return stats
        
        # Process each batch
        for batch in pending_batches:
            try:
                if not batch.id:
                    logger.error("Encountered batch without ID, skipping")
                    continue
                    
                # Update batch status to PROCESSING
                await self.batch_repository.update_batch_status(
                    batch.id, 
                    MultiTenantBatchStatus.PROCESSING
                )
                
                # Process the batch
                success = await self.process_batch(batch)
                
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing batch {batch.id if batch else 'unknown'}: {str(e)}")
                try:
                    if batch and batch.id:
                        await self.batch_repository.update_batch_status(
                            batch.id,
                            MultiTenantBatchStatus.FAILED,
                            error_message=str(e)
                        )
                except Exception as inner_e:
                    logger.error(f"Failed to update batch status: {str(inner_e)}")
                    
                stats["failed"] += 1
        
        return stats
    
    async def process_batch(self, batch: MultiTenantCampaignBatch) -> bool:
        """
        Process a multi-tenant campaign batch.
        
        Args:
            batch: The batch to process
            
        Returns:
            True if successful, False otherwise
        """
        if not batch or not batch.id:
            logger.error("Cannot process batch: Invalid batch data")
            return False
            
        logger.info(f"Processing multi-tenant batch {batch.id} with {len(batch.tenant_ids)} tenants")
        
        try:
            # Process each tenant in the batch
            for tenant_id in batch.tenant_ids:
                tenant_result = batch.tenant_results.get(tenant_id)
                
                if not tenant_result or tenant_result.status == TenantExecutionStatus.PENDING:
                    logger.info(f"Processing tenant {tenant_id} in batch {batch.id}")
                    
                    # Create a new result with PROCESSING status
                    tenant_result = TenantExecutionResult(
                        tenant_id=tenant_id,
                        status=TenantExecutionStatus.PROCESSING,
                        started_at=datetime.utcnow()
                    )
                    
                    # Update the tenant result in the batch
                    batch.update_tenant_result(tenant_id, tenant_result)
                    await self.batch_repository.update_tenant_result(batch.id, tenant_id, tenant_result)
                    
                    # Process the tenant
                    success, stats = await self._process_tenant(batch, tenant_id)
                    
                    if success:
                        tenant_result.status = TenantExecutionStatus.COMPLETED
                    else:
                        tenant_result.status = TenantExecutionStatus.FAILED
                        
                    tenant_result.completed_at = datetime.utcnow()
                    
                    # Update statistics if available
                    if stats:
                        tenant_result.processed_count = stats.get("processed", 0)
                        tenant_result.success_count = stats.get("success", 0)
                        tenant_result.error_count = stats.get("failed", 0)
                    
                    # Update the tenant result in the batch and repository
                    batch.update_tenant_result(tenant_id, tenant_result)
                    await self.batch_repository.update_tenant_result(batch.id, tenant_id, tenant_result)
            
            # Check if all tenants have been processed
            if batch.all_tenants_processed():
                # Update batch status to COMPLETED
                batch.update_status(MultiTenantBatchStatus.COMPLETED)
                await self.batch_repository.update_batch_status(
                    batch.id,
                    MultiTenantBatchStatus.COMPLETED
                )
                logger.info(f"Completed multi-tenant batch {batch.id}")
                
            # Return success if there were no errors
            return batch.error_count == 0
            
        except Exception as e:
            logger.error(f"Error processing batch {batch.id}: {str(e)}")
            batch.update_status(MultiTenantBatchStatus.FAILED)
            batch.last_error = str(e)
            try:
                await self.batch_repository.update_batch_status(
                    batch.id,
                    MultiTenantBatchStatus.FAILED,
                    error_message=str(e)
                )
            except Exception as inner_e:
                logger.error(f"Failed to update batch status: {str(inner_e)}")
                
            return False
    
    async def _process_tenant(self, batch: MultiTenantCampaignBatch, tenant_id: str) -> Tuple[bool, Optional[Dict[str, int]]]:
        """
        Process a specific tenant within a batch.
        
        Args:
            batch: The batch being processed
            tenant_id: The tenant ID to process
            
        Returns:
            Tuple containing:
            - Boolean success indicator
            - Optional dictionary with processing statistics
        """
        if not tenant_id:
            logger.error("Cannot process tenant: Invalid tenant ID")
            return False, None
            
        logger.info(f"Processing tenant {tenant_id} for batch {batch.id}")
        
        # Set the tenant context
        TenantContext.set_tenant_id(tenant_id)
        stats = None
        
        try:
            # Get tenant-specific data
            crm_data = await self._get_tenant_crm_data(tenant_id, batch.campaign_template)
            
            if not crm_data:
                logger.error(f"Failed to get CRM data for tenant {tenant_id}")
                return False, None
            
            # Create a tenant-specific campaign from the template
            campaign = self.template_converter.convert_template_to_campaign(
                template=batch.campaign_template,
                recipients=crm_data,
                batch_id=batch.id
            )
            
            # Add tenant information to campaign
            campaign.custom_attributes["tenant_id"] = tenant_id
            campaign.custom_attributes["multi_tenant_batch_id"] = batch.id
            
            # Save the campaign
            campaign_id = await self.campaign_service.create_campaign(campaign)
            
            # Update tenant result with campaign ID
            tenant_result = batch.tenant_results.get(tenant_id)
            if tenant_result:
                tenant_result.campaign_id = campaign_id
                await self.batch_repository.update_tenant_result(batch.id, tenant_id, tenant_result)
            
            # Process the campaign
            success = await self.campaign_service.send_campaign(campaign_id)
            
            # Get statistics
            stats = await self.campaign_service.get_campaign_statistics(campaign_id)
            
            logger.info(f"Successfully processed tenant {tenant_id} for batch {batch.id} - Stats: {stats}")
            return success, stats
            
        except Exception as e:
            logger.error(f"Error processing tenant {tenant_id} for batch {batch.id}: {str(e)}")
            
            # Update tenant result with error
            tenant_result = batch.tenant_results.get(tenant_id)
            if tenant_result:
                tenant_result.status = TenantExecutionStatus.FAILED
                tenant_result.error_message = str(e)
                tenant_result.completed_at = datetime.utcnow()
                try:
                    await self.batch_repository.update_tenant_result(batch.id, tenant_id, tenant_result)
                except Exception as inner_e:
                    logger.error(f"Failed to update tenant result: {str(inner_e)}")
            
            return False, None
            
        finally:
            # Clear the tenant context
            TenantContext.clear()
    
    async def _get_tenant_crm_data(self, tenant_id: str, campaign_template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get CRM data for a specific tenant.
        
        This method accesses the tenant's CRM database to retrieve recipient data
        based on the segment criteria defined in the campaign template.
        
        Args:
            tenant_id: The tenant ID
            campaign_template: The campaign template
            
        Returns:
            List of recipient data dictionaries
        """
        if not tenant_id:
            logger.error("Cannot get CRM data: Invalid tenant ID")
            return []
            
        # Get segment criteria from template
        segment_details = campaign_template.get("segment_details", {})
        segment_criteria = segment_details.get("segment_criteria", {})
        
        # Get CRM database connection
        db_connection = None
        
        try:
            crm_db = DatabaseFactory.get_crm_db()
            
            # Execute a simple query to get recipients
            # In a real implementation, this would translate segment_criteria into a proper query
            async with crm_db.connection() as conn:
                db_connection = conn
                
                query = """
                SELECT 
                    id,
                    email,
                    first_name,
                    last_name,
                    custom_attributes
                FROM 
                    contacts
                WHERE 
                    status = 'active'
                LIMIT 
                    100
                """
                
                results = await conn.fetch(query)
                
                # Convert results to dictionaries
                recipients = []
                for row in results:
                    recipient = dict(row)
                    recipients.append(recipient)
                
                logger.info(f"Retrieved {len(recipients)} recipients for tenant {tenant_id}")
                return recipients
                
        except Exception as e:
            logger.error(f"Error getting CRM data for tenant {tenant_id}: {str(e)}")
            return []
            
        finally:
            # Ensure connection is closed
            if db_connection and hasattr(db_connection, 'close') and not db_connection.closed:
                try:
                    await db_connection.close()
                except Exception as e:
                    logger.error(f"Error closing database connection: {str(e)}")
    
    async def create_multi_tenant_batch(self, batch_data: Dict[str, Any]) -> str:
        """
        Create a new multi-tenant campaign batch.
        
        Args:
            batch_data: Dictionary with batch data
            
        Returns:
            The batch ID
        """
        if not batch_data:
            logger.error("Cannot create batch: No batch data provided")
            raise ValueError("Batch data is required")
            
        # Validate required fields
        if "campaign_template" not in batch_data:
            logger.error("Cannot create batch: Missing campaign template")
            raise ValueError("Campaign template is required")
            
        if "tenant_ids" not in batch_data or not batch_data["tenant_ids"]:
            logger.error("Cannot create batch: Missing tenant IDs")
            raise ValueError("At least one tenant ID is required")
            
        # Create batch object
        batch = MultiTenantCampaignBatch(
            name=batch_data.get("name", "Multi-tenant Campaign Batch"),
            description=batch_data.get("description"),
            campaign_template=batch_data.get("campaign_template", {}),
            tenant_ids=batch_data.get("tenant_ids", []),
            status=MultiTenantBatchStatus.CREATED,
            tags=batch_data.get("tags", []),
            custom_attributes=batch_data.get("custom_attributes", {})
        )
        
        # Set additional properties if provided
        if "max_retries" in batch_data:
            batch.max_retries = batch_data["max_retries"]
        
        # Save the batch
        batch_id = await self.batch_repository.save(batch)
        logger.info(f"Created multi-tenant batch {batch_id} with {len(batch.tenant_ids)} tenants")
        
        return batch_id
        
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get status information for a multi-tenant batch.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            Dictionary with status information
        """
        if not batch_id:
            logger.error("Cannot get batch status: Invalid batch ID")
            raise ValueError("Batch ID is required")
            
        batch = await self.batch_repository.get_by_id(batch_id)
        
        if not batch:
            logger.error(f"Batch {batch_id} not found")
            raise ValueError(f"Batch {batch_id} not found")
            
        # Get completion statistics
        stats = batch.get_completion_stats()
        
        # Create status response
        status = {
            "id": batch.id,
            "name": batch.name,
            "status": batch.status.value,
            "created_at": batch.created_at.isoformat(),
            "updated_at": batch.updated_at.isoformat(),
            "tenant_count": len(batch.tenant_ids),
            "completion_stats": stats
        }
        
        # Add timing information if available
        if batch.started_at:
            status["started_at"] = batch.started_at.isoformat()
            
        if batch.completed_at:
            status["completed_at"] = batch.completed_at.isoformat()
            
        # Add error information if available
        if batch.last_error:
            status["last_error"] = batch.last_error
            status["error_count"] = batch.error_count
            
        return status 