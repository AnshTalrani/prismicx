"""
Multi-Tenant Campaign Batch Model.

This module defines the MultiTenantCampaignBatch class which represents a batch of tenants
using the same campaign template, allowing for efficient processing of the same campaign
across multiple tenants while maintaining tenant isolation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Set
import uuid


class MultiTenantBatchStatus(str, Enum):
    """Status of a multi-tenant campaign batch."""
    CREATED = "created"
    VALIDATING = "validating"
    QUEUED = "queued"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TenantExecutionStatus(str, Enum):
    """Status of tenant-specific execution within a multi-tenant batch."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TenantExecutionResult:
    """
    Represents the result of campaign execution for a specific tenant.
    """
    tenant_id: str
    status: TenantExecutionStatus = TenantExecutionStatus.PENDING
    processed_count: int = 0
    success_count: int = 0
    error_count: int = 0
    campaign_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TenantExecutionResult':
        """Create a TenantExecutionResult from dictionary data."""
        instance = cls(
            tenant_id=data["tenant_id"],
            status=TenantExecutionStatus(data.get("status", "pending")),
            processed_count=data.get("processed_count", 0),
            success_count=data.get("success_count", 0),
            error_count=data.get("error_count", 0),
            campaign_id=data.get("campaign_id"),
            error_message=data.get("error_message"),
            custom_attributes=data.get("custom_attributes", {})
        )
        
        # Parse timestamps
        if "started_at" in data and data["started_at"]:
            instance.started_at = datetime.fromisoformat(data["started_at"])
        
        if "completed_at" in data and data["completed_at"]:
            instance.completed_at = datetime.fromisoformat(data["completed_at"])
            
        return instance


@dataclass
class MultiTenantCampaignBatch:
    """
    Represents a batch of tenants sharing the same campaign template.
    
    This model allows for efficient processing of the same campaign across
    multiple tenants, while maintaining proper tenant isolation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    campaign_template: Dict[str, Any] = field(default_factory=dict)
    
    # Batch metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: MultiTenantBatchStatus = MultiTenantBatchStatus.CREATED
    
    # Tenant processing
    tenant_ids: List[str] = field(default_factory=list)
    tenant_results: Dict[str, TenantExecutionResult] = field(default_factory=dict)
    current_tenant_index: int = 0
    
    # Timing information
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    
    # Processing settings
    max_retries: int = 3
    retry_count: int = 0
    
    # Additional data
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize derived values after object creation."""
        # Initialize tenant_results for each tenant_id if not already present
        for tenant_id in self.tenant_ids:
            if tenant_id not in self.tenant_results:
                self.tenant_results[tenant_id] = TenantExecutionResult(tenant_id=tenant_id)
    
    def update_status(self, new_status: MultiTenantBatchStatus) -> None:
        """
        Update the status of the batch.
        
        Args:
            new_status: The new status to set
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Update timing information based on status
        now = datetime.utcnow()
        
        if new_status == MultiTenantBatchStatus.PROCESSING and not self.started_at:
            self.started_at = now
            
        if new_status in (
            MultiTenantBatchStatus.COMPLETED, 
            MultiTenantBatchStatus.FAILED, 
            MultiTenantBatchStatus.CANCELLED
        ):
            self.completed_at = now
    
    def update_tenant_result(self, tenant_id: str, result: TenantExecutionResult) -> None:
        """
        Update the execution result for a specific tenant.
        
        Args:
            tenant_id: The tenant ID
            result: The execution result
        """
        self.tenant_results[tenant_id] = result
        self.updated_at = datetime.utcnow()
        
        # Update error count
        if result.status == TenantExecutionStatus.FAILED:
            self.error_count += 1
            self.last_error = result.error_message
    
    def get_next_pending_tenant(self) -> Optional[str]:
        """
        Get the next tenant ID that is pending processing.
        
        Returns:
            The next tenant ID or None if all tenants have been processed
        """
        for tenant_id in self.tenant_ids:
            result = self.tenant_results.get(tenant_id)
            if result and result.status == TenantExecutionStatus.PENDING:
                return tenant_id
        return None
    
    def all_tenants_processed(self) -> bool:
        """
        Check if all tenants have been processed.
        
        Returns:
            True if all tenants have been processed, False otherwise
        """
        for tenant_id in self.tenant_ids:
            result = self.tenant_results.get(tenant_id)
            if not result or result.status in (TenantExecutionStatus.PENDING, TenantExecutionStatus.PROCESSING):
                return False
        return True
    
    def get_completion_stats(self) -> Dict[str, int]:
        """
        Get statistics about the processing completion.
        
        Returns:
            Dictionary with completion statistics
        """
        total = len(self.tenant_ids)
        completed = 0
        failed = 0
        pending = 0
        
        for tenant_id in self.tenant_ids:
            result = self.tenant_results.get(tenant_id)
            if not result or result.status == TenantExecutionStatus.PENDING:
                pending += 1
            elif result.status == TenantExecutionStatus.COMPLETED:
                completed += 1
            elif result.status == TenantExecutionStatus.FAILED:
                failed += 1
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "processing": total - (completed + failed + pending)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiTenantCampaignBatch':
        """Create a MultiTenantCampaignBatch from dictionary data."""
        instance = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description"),
            campaign_template=data.get("campaign_template", {}),
            tenant_ids=data.get("tenant_ids", []),
            current_tenant_index=data.get("current_tenant_index", 0),
            status=MultiTenantBatchStatus(data.get("status", "created")),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error"),
            max_retries=data.get("max_retries", 3),
            retry_count=data.get("retry_count", 0),
            tags=data.get("tags", []),
            custom_attributes=data.get("custom_attributes", {})
        )
        
        # Parse timestamps
        if "created_at" in data:
            instance.created_at = datetime.fromisoformat(data["created_at"])
            
        if "updated_at" in data:
            instance.updated_at = datetime.fromisoformat(data["updated_at"])
            
        if "started_at" in data and data["started_at"]:
            instance.started_at = datetime.fromisoformat(data["started_at"])
            
        if "completed_at" in data and data["completed_at"]:
            instance.completed_at = datetime.fromisoformat(data["completed_at"])
        
        # Parse tenant results
        if "tenant_results" in data:
            for tenant_id, result_data in data["tenant_results"].items():
                if isinstance(result_data, dict):
                    # Ensure tenant_id is in the result data
                    result_data["tenant_id"] = tenant_id
                    instance.tenant_results[tenant_id] = TenantExecutionResult.from_dict(result_data)
                
        return instance 