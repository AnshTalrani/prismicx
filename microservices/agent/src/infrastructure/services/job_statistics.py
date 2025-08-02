"""
Job Statistics Service for tracking batch job execution metrics.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class JobStatistics:
    """
    Class for tracking comprehensive job statistics across executions.
    
    Maintains detailed metrics for each job:
    - Overall success and failure rates
    - Purpose-specific statistics
    - Historical execution data
    - Performance trends
    """
    
    def __init__(self, job_id: str, storage_dir: str = "data/batch/statistics"):
        """
        Initialize job statistics tracker.
        
        Args:
            job_id: ID of the job
            storage_dir: Directory for storing statistics
        """
        self.job_id = job_id
        self.storage_dir = storage_dir
        self.stats_file = os.path.join(storage_dir, f"{job_id}_stats.json")
        self.stats = {
            "job_id": job_id,
            "total_executions": 0,
            "total_processed": 0,
            "total_succeeded": 0,
            "total_failed": 0,
            "purpose_stats": {},
            "last_execution": None,
            "executions": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Ensure directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing stats if available
        self._load_stats()
    
    def _load_stats(self) -> None:
        """Load statistics from file if it exists."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
                    logger.info(f"Loaded statistics for job {self.job_id}")
            except Exception as e:
                logger.error(f"Error loading statistics for job {self.job_id}: {str(e)}")
    
    def _save_stats(self) -> None:
        """Save statistics to file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
                logger.info(f"Saved statistics for job {self.job_id}")
        except Exception as e:
            logger.error(f"Error saving statistics for job {self.job_id}: {str(e)}")
    
    def record_execution_start(self, execution_id: str, batch_type: str, 
                              purpose_id: str, expected_count: int) -> None:
        """
        Record the start of a job execution.
        
        Args:
            execution_id: ID of this execution
            batch_type: Type of batch processing
            purpose_id: Purpose ID being processed
            expected_count: Expected number of items
        """
        execution = {
            "execution_id": execution_id,
            "batch_type": batch_type,
            "purpose_id": purpose_id,
            "expected_count": expected_count,
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "status": "in_progress",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "duration_seconds": None
        }
        
        # Initialize purpose stats if not exists
        if purpose_id not in self.stats["purpose_stats"]:
            self.stats["purpose_stats"][purpose_id] = {
                "total_processed": 0,
                "total_succeeded": 0, 
                "total_failed": 0,
                "last_execution": None
            }
        
        # Update stats
        self.stats["total_executions"] += 1
        self.stats["last_execution"] = datetime.utcnow().isoformat()
        self.stats["executions"].insert(0, execution)
        self.stats["updated_at"] = datetime.utcnow().isoformat()
        
        # Trim executions list if too long
        if len(self.stats["executions"]) > 100:
            self.stats["executions"] = self.stats["executions"][:100]
            
        # Save stats
        self._save_stats()
    
    def update_execution_progress(self, execution_id: str, processed: int = 0, 
                                succeeded: int = 0, failed: int = 0) -> None:
        """
        Update the progress of an execution.
        
        Args:
            execution_id: ID of the execution
            processed: Number of processed items
            succeeded: Number of successful items
            failed: Number of failed items
        """
        # Find execution
        for execution in self.stats["executions"]:
            if execution["execution_id"] == execution_id:
                # Update execution stats
                execution["processed"] += processed
                execution["succeeded"] += succeeded
                execution["failed"] += failed
                
                # Update purpose stats
                purpose_id = execution["purpose_id"]
                self.stats["purpose_stats"][purpose_id]["total_processed"] += processed
                self.stats["purpose_stats"][purpose_id]["total_succeeded"] += succeeded
                self.stats["purpose_stats"][purpose_id]["total_failed"] += failed
                self.stats["purpose_stats"][purpose_id]["last_execution"] = datetime.utcnow().isoformat()
                
                # Update overall stats
                self.stats["total_processed"] += processed
                self.stats["total_succeeded"] += succeeded
                self.stats["total_failed"] += failed
                self.stats["updated_at"] = datetime.utcnow().isoformat()
                
                # Save stats
                self._save_stats()
                return
    
    def record_execution_complete(self, execution_id: str, status: str) -> None:
        """
        Record the completion of an execution.
        
        Args:
            execution_id: ID of the execution
            status: Final status (completed, failed, partial)
        """
        for execution in self.stats["executions"]:
            if execution["execution_id"] == execution_id:
                # Update status
                execution["status"] = status
                execution["end_time"] = datetime.utcnow().isoformat()
                
                # Calculate duration
                start_time = datetime.fromisoformat(execution["start_time"])
                end_time = datetime.fromisoformat(execution["end_time"])
                execution["duration_seconds"] = (end_time - start_time).total_seconds()
                
                # Update purpose stats
                purpose_id = execution["purpose_id"]
                self.stats["purpose_stats"][purpose_id]["last_execution"] = datetime.utcnow().isoformat()
                
                # Save stats
                self.stats["updated_at"] = datetime.utcnow().isoformat()
                self._save_stats()
                return
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """
        Get complete job statistics.
        
        Returns:
            Complete statistics object
        """
        return self.stats
    
    def get_purpose_statistics(self, purpose_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific purpose.
        
        Args:
            purpose_id: Purpose ID
            
        Returns:
            Purpose-specific statistics
        """
        if purpose_id in self.stats["purpose_stats"]:
            # Get executions for this purpose
            purpose_executions = [
                execution for execution in self.stats["executions"]
                if execution["purpose_id"] == purpose_id
            ]
            
            return {
                "purpose_id": purpose_id,
                "stats": self.stats["purpose_stats"][purpose_id],
                "executions": purpose_executions[:10]  # Return only the last 10
            }
        
        return {"purpose_id": purpose_id, "stats": None, "executions": []} 