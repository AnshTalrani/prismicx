"""
Unified batch scheduler service for scheduling batch executions.

This module combines the original BatchScheduler with the DynamicBatchScheduler
to provide preference-based job scheduling capabilities.
It supports the 2x2 matrix model for batch processing, handling both processing
methods (INDIVIDUAL vs BATCH) and data source types (USERS vs CATEGORIES).
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import signal

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    logging.error("APScheduler package not found. Install with 'pip install apscheduler'")
    AsyncIOScheduler = None
    CronTrigger = None

# Import Config Database client
from src.infrastructure.clients.config_database_client import ConfigDatabaseClient
# Import batch type value objects
from src.domain.value_objects.batch_type import ProcessingMethod, DataSourceType, BatchType

logger = logging.getLogger(__name__)

class BatchScheduler:
    """
    Service for scheduling batch executions.
    Uses APScheduler to schedule batch executions based on configuration.
    
    Key features:
    - Supports various scheduling frequencies (daily, weekly, monthly)
    - Handles job priorities and dependencies
    - Provides monitoring and control of scheduled jobs
    """
    
    def __init__(self, batch_processor, config_db_client=None):
        """
        Initialize the batch scheduler.
        
        Args:
            batch_processor: Service for processing batches
            config_db_client: Optional client for config database
        """
        self.batch_processor = batch_processor
        self.scheduler = AsyncIOScheduler() if AsyncIOScheduler else None
        self.running = False
        self.config_db_client = config_db_client
        
        # Track dynamic schedules (used by DynamicBatchScheduler)
        self.dynamic_schedules = {}
        
        # Change monitor task and poll interval
        self.config_change_monitor = None
        self.change_poll_interval = 60
        
        logger.info("Initialized BatchScheduler")
    
    async def initialize(self):
        """
        Initialize scheduler with batch configurations.
        
        Returns:
            Dictionary with initialization status
        """
        if not self.scheduler:
            error_msg = "APScheduler not available. Scheduler initialization failed."
            logger.error(error_msg)
            return {"status": "failed", "error": error_msg}
        
        # Load batch configs
        await self.batch_processor.load_batch_configs()
        
        # Schedule each job
        scheduled_jobs = []
        for job in self.batch_processor.batch_configs.get("batch_processing_jobs", []):
            job_id = await self.schedule_job(job)
            if job_id:
                scheduled_jobs.append({"job_id": job["job_id"], "scheduler_job_id": job_id})
        
        logger.info(f"Scheduler initialized with {len(scheduled_jobs)} jobs")
        return {
            "status": "success",
            "scheduled_jobs": scheduled_jobs,
            "initialized_at": datetime.utcnow().isoformat()
        }
    
    async def schedule_job(self, job: Dict[str, Any]) -> Optional[str]:
        """
        Schedule a job based on configuration.
        
        Args:
            job: Job configuration
            
        Returns:
            Job ID if scheduled successfully, None otherwise
        """
        if not self.scheduler:
            logger.error("Scheduler not available")
            return None
            
        schedule = job.get("schedule", {})
        frequency = schedule.get("frequency")
        
        if not frequency:
            logger.error(f"No schedule frequency defined for job {job['job_id']}")
            return None
        
        # Extract batch type information if present in the configuration
        batch_type_info = job.get("batch_type", {})
        processing_method = batch_type_info.get("processing_method", "INDIVIDUAL")
        data_source_type = batch_type_info.get("data_source_type", "USERS")
        
        try:
            # Validate batch type values
            try:
                proc_method = ProcessingMethod.from_string(processing_method)
                data_source = DataSourceType.from_string(data_source_type)
                # Create BatchType object
                batch_type = BatchType(proc_method, data_source)
                logger.info(f"Using batch type {batch_type} for job {job['job_id']}")
            except ValueError as e:
                logger.warning(f"Invalid batch type for job {job['job_id']}: {str(e)}. Using default.")
                # Use default batch type (INDIVIDUAL_USERS)
                batch_type = BatchType(ProcessingMethod.INDIVIDUAL, DataSourceType.USERS)
    
            scheduler_job_id = f"job_{job['job_id']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            if frequency == "daily":
                # Parse time
                time_str = schedule.get("time", "00:00")
                time_parts = time_str.split(":")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                
                # Schedule job
                self.scheduler.add_job(
                    self.batch_processor.execute_job,
                    CronTrigger(hour=hour, minute=minute),
                    id=scheduler_job_id,
                    args=[job["job_id"], {"batch_type": batch_type.to_dict()}],
                    name=f"Daily job: {job['job_id']}"
                )
                logger.info(f"Scheduled daily job {job['job_id']} at {hour:02d}:{minute:02d}")
                
            elif frequency == "weekly":
                # Parse time
                time_str = schedule.get("time", "00:00")
                time_parts = time_str.split(":")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                day_of_week = schedule.get("day", "mon").lower()
                
                # Schedule job
                self.scheduler.add_job(
                    self.batch_processor.execute_job,
                    CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
                    id=scheduler_job_id,
                    args=[job["job_id"], {"batch_type": batch_type.to_dict()}],
                    name=f"Weekly job: {job['job_id']}"
                )
                logger.info(f"Scheduled weekly job {job['job_id']} on {day_of_week} at {hour:02d}:{minute:02d}")
                
            elif frequency == "monthly":
                # Parse time
                time_str = schedule.get("time", "00:00")
                time_parts = time_str.split(":")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                day = schedule.get("day", "1")
                
                # Schedule job
                self.scheduler.add_job(
                    self.batch_processor.execute_job,
                    CronTrigger(day=day, hour=hour, minute=minute),
                    id=scheduler_job_id,
                    args=[job["job_id"], {"batch_type": batch_type.to_dict()}],
                    name=f"Monthly job: {job['job_id']}"
                )
                logger.info(f"Scheduled monthly job {job['job_id']} on day {day} at {hour:02d}:{minute:02d}")
                
            elif frequency == "biweekly":
                # Parse time
                time_str = schedule.get("time", "00:00")
                time_parts = time_str.split(":")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                
                # Schedule job (run on 1st and 15th of each month)
                self.scheduler.add_job(
                    self.batch_processor.execute_job,
                    CronTrigger(day="1,15", hour=hour, minute=minute),
                    id=scheduler_job_id,
                    args=[job["job_id"]],
                    name=f"Biweekly job: {job['job_id']}"
                )
                logger.info(f"Scheduled biweekly job {job['job_id']} on days 1,15 at {hour:02d}:{minute:02d}")
                
            elif frequency == "hourly":
                # Schedule job to run every hour
                self.scheduler.add_job(
                    self.batch_processor.execute_job,
                    CronTrigger(minute=0),
                    id=scheduler_job_id,
                    args=[job["job_id"]],
                    name=f"Hourly job: {job['job_id']}"
                )
                logger.info(f"Scheduled hourly job {job['job_id']}")
                
            else:
                logger.error(f"Unsupported frequency {frequency} for job {job['job_id']}")
                return None
                
            return scheduler_job_id
            
        except Exception as e:
            logger.error(f"Failed to schedule job {job['job_id']}: {str(e)}")
            return None
    
    def start(self):
        """
        Start the scheduler.
        
        Returns:
            Start status
        """
        if not self.scheduler:
            logger.error("Scheduler not available")
            return {"status": "failed", "error": "Scheduler not available"}
        
        if self.running:
            logger.warning("Scheduler already running")
            return {"status": "warning", "message": "Scheduler already running"}
        
        try:
            # Register signal handlers for graceful shutdown
            self._register_signal_handlers()
            
            # Start scheduler
            self.scheduler.start()
            self.running = True
            
            logger.info("Scheduler started")
            return {"status": "success", "started_at": datetime.utcnow().isoformat()}
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def stop(self):
        """
        Stop the scheduler.
        
        Returns:
            Stop status
        """
        if not self.scheduler:
            logger.error("Scheduler not available")
            return {"status": "failed", "error": "Scheduler not available"}
        
        if not self.running:
            logger.warning("Scheduler not running")
            return {"status": "warning", "message": "Scheduler not running"}
        
        try:
            # Stop config change monitor if it exists
            if self.config_change_monitor:
                self.config_change_monitor.cancel()
                self.config_change_monitor = None
                logger.info("Stopped config change monitor")
            
            # Shutdown scheduler
            self.scheduler.shutdown()
            self.running = False
            
            logger.info("Scheduler stopped")
            return {"status": "success", "stopped_at": datetime.utcnow().isoformat()}
            
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all scheduled jobs.
        
        Returns:
            List of scheduled jobs
        """
        if not self.scheduler:
            logger.error("Scheduler not available")
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "job_id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "args": job.args
            })
        
        return jobs
    
    async def run_job_now(self, job_id: str) -> Dict[str, Any]:
        """
        Run a job immediately, regardless of schedule.
        
        Args:
            job_id: Job ID to run
            
        Returns:
            Execution result
        """
        try:
            # Check if job exists
            job = await self.batch_processor.get_job_config(job_id)
            if not job:
                error_msg = f"Job {job_id} not found"
                logger.error(error_msg)
                return {"status": "failed", "error": error_msg}
                
            # Execute job
            logger.info(f"Manually executing job {job_id}")
            result = await self.batch_processor.execute_job(job_id)
            
            return {
                "status": "success",
                "job_id": job_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a job.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Job status
        """
        try:
            status = await self.batch_processor.get_job_status(job_id)
            return {
                "job_id": job_id,
                "status": status
            }
        except Exception as e:
            logger.error(f"Failed to check job status {job_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        try:
            # Register for SIGINT (Ctrl+C) and SIGTERM
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, self._handle_shutdown_signal)
            logger.info("Registered signal handlers for graceful shutdown")
        except Exception as e:
            logger.warning(f"Failed to register signal handlers: {str(e)}")
    
    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signal by stopping scheduler."""
        logger.info(f"Received signal {signum}, shutting down scheduler")
        self.stop()
        
        # Exit after a delay to allow for cleanup
        def delayed_exit():
            logger.info("Exiting application")
            asyncio.get_event_loop().stop()
            
        asyncio.get_event_loop().call_later(2, delayed_exit)
    
    # Dynamic batch scheduler methods
    
    async def initialize_dynamic_schedules(self):
        """
        Initialize dynamic schedules based on user preferences.
        
        Returns:
            Dictionary with dynamic scheduling results
        """
        if not self.config_db_client:
            logger.warning("Config database client not available, skipping dynamic schedules")
            return {"dynamic_schedules": []}
            
        dynamic_schedules = []
        
        try:
            # Get feature types requiring scheduling
            feature_types = await self.config_db_client.get_feature_types()
            logger.info(f"Retrieved {len(feature_types)} feature types for scheduling")
            
            for feature_type in feature_types:
                # Get frequency groups for this feature
                frequency_groups = await self.config_db_client.get_frequency_groups(feature_type)
                logger.info(f"Feature {feature_type}: {len(frequency_groups)} frequency groups")
                
                for group_key, users in frequency_groups.items():
                    # Parse group key (frequency:time_key)
                    parts = group_key.split(":", 1)
                    if len(parts) != 2:
                        logger.warning(f"Invalid group key format: {group_key}")
                        continue
                        
                    frequency, time_key = parts
                    
                    # Create schedule for this group
                    schedule_id = await self.schedule_preference_group(
                        feature_type, frequency, time_key, len(users))
                        
                    if schedule_id:
                        dynamic_schedules.append({
                            "schedule_id": schedule_id,
                            "feature_type": feature_type,
                            "frequency": frequency,
                            "time_key": time_key,
                            "user_count": len(users)
                        })
                        logger.info(f"Created schedule {schedule_id} for {len(users)} users")
            
            self.dynamic_schedules = {
                schedule["schedule_id"]: schedule for schedule in dynamic_schedules
            }
            
            logger.info(f"Initialized {len(dynamic_schedules)} dynamic schedules")
            return {"dynamic_schedules": dynamic_schedules}
            
        except Exception as e:
            logger.error(f"Error initializing dynamic schedules: {str(e)}")
            return {"dynamic_schedules": [], "error": str(e)}
        
    async def schedule_preference_group(self, feature_type, frequency, time_key, user_count):
        """
        Schedule a batch job for a preference group.
        
        Args:
            feature_type: Type of feature (instagram_posts, etsy_analysis)
            frequency: Frequency (daily, weekly, monthly)
            time_key: Time key for scheduling
            user_count: Number of users in this group
            
        Returns:
            Schedule ID if successful, None otherwise
        """
        if not self.scheduler:
            logger.error("Scheduler not available")
            return None
            
        try:
            # Create unique schedule ID
            schedule_id = f"{feature_type}_{frequency}_{time_key.replace(':', '_')}"
            
            # Parse scheduling parameters based on frequency and time_key
            if frequency == "daily":
                # For daily, time_key is just the time
                time_parts = time_key.split(":")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                
                trigger = self._create_cron_trigger(hour=hour, minute=minute)
                name = f"Daily {feature_type} at {hour:02d}:{minute:02d}"
                
            elif frequency == "weekly":
                # For weekly, time_key is day:time
                day_time = time_key.split(":")
                day_of_week = day_time[0].lower()
                time_parts = day_time[1].split(":")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                
                trigger = self._create_cron_trigger(day_of_week=day_of_week, hour=hour, minute=minute)
                name = f"Weekly {feature_type} on {day_of_week} at {hour:02d}:{minute:02d}"
                
            elif frequency == "monthly":
                # For monthly, time_key is day:time
                day_time = time_key.split(":")
                day = day_time[0]
                time_parts = day_time[1].split(":")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                
                trigger = self._create_cron_trigger(day=day, hour=hour, minute=minute)
                name = f"Monthly {feature_type} on day {day} at {hour:02d}:{minute:02d}"
                
            else:
                logger.error(f"Unsupported frequency: {frequency}")
                return None
                
            # Add job to scheduler
            self.scheduler.add_job(
                self.process_preference_group,
                trigger,
                id=schedule_id,
                args=[feature_type, frequency, time_key],
                name=name,
                replace_existing=True  # Replace if exists
            )
            
            logger.info(f"Scheduled preference group: {name} for {user_count} users")
            return schedule_id
            
        except Exception as e:
            logger.error(f"Failed to schedule preference group: {str(e)}")
            return None
    
    def _create_cron_trigger(self, **kwargs):
        """Create a cron trigger with the given parameters."""
        try:
            from apscheduler.triggers.cron import CronTrigger
            return CronTrigger(**kwargs)
        except ImportError:
            logger.error("APScheduler package not found")
            return None
            
    async def process_preference_group(self, feature_type, frequency, time_key):
        """
        Process a preference group.
        Called by the scheduler when the schedule triggers.
        
        Args:
            feature_type: Feature type
            frequency: Frequency
            time_key: Time key
            
        Returns:
            Processing result dictionary
        """
        try:
            # Check if batch processor supports preference-based batches
            if hasattr(self.batch_processor, "process_user_preference_batch"):
                # Process with enhanced processor
                batch_id = await self.batch_processor.process_user_preference_batch(
                    feature_type, frequency, time_key)
                
                logger.info(f"Triggered preference batch {batch_id} for {feature_type}")
                return {"status": "success", "batch_id": batch_id}
            else:
                # Fallback to standard processing
                logger.warning("BatchProcessor does not support preference-based batches. Using fallback.")
                
                # Get users for this preference group
                users = await self.config_db_client.get_frequency_group_users(
                    feature_type, frequency, time_key)
                
                # Get appropriate template for this feature type
                template_id = self._get_template_for_feature(feature_type)
                
                # Process as standard batch with user IDs
                user_ids = [user["user_id"] for user in users]
                job_config = {
                    "job_id": f"{feature_type}_{frequency}_{time_key.replace(':', '_')}",
                    "batch_type": {
                        "processing_method": ProcessingMethod.INDIVIDUAL.value,
                        "data_source_type": DataSourceType.USERS.value
                    },
                    "purpose_id": template_id,
                    "filters": {
                        "specific_users": user_ids
                    },
                    "metadata": {
                        "feature_type": feature_type,
                        "frequency": frequency,
                        "time_key": time_key
                    }
                }
                
                # Execute as a standard job
                batch_id = await self.batch_processor.process_job(
                    job_config["job_id"], 
                    parameters=job_config
                )
                
                logger.info(f"Triggered fallback batch {batch_id} for {feature_type}")
                return {"status": "success", "batch_id": batch_id, "mode": "fallback"}
                
        except Exception as e:
            logger.error(f"Error processing preference group: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def start_config_change_monitor(self):
        """Start monitoring for configuration changes."""
        if self.config_change_monitor:
            # Already running
            return
            
        self.config_change_monitor = asyncio.create_task(self._monitor_config_changes())
        logger.info("Started configuration change monitor")
    
    async def _monitor_config_changes(self):
        """Periodically check for config changes and update schedules."""
        try:
            while True:
                # Wait for poll interval
                await asyncio.sleep(self.change_poll_interval)
                
                # Check for changes using the new all-tenants endpoint
                logger.debug("Checking for preference changes")
                
                try:
                    # Get feature configuration changes across all tenants
                    changed_features = set()
                    
                    # Check all features in a more efficient way using the all-tenants endpoint
                    feature_types = await self.config_db_client.get_feature_types()
                    
                    for feature_type in feature_types:
                        # Check if this feature's configuration has changed by comparing timestamps
                        config_key = f"features/{feature_type}/last_updated"
                        all_tenant_updates = await self.config_db_client.get_config_for_all_tenants(config_key)
                        
                        # If we have updates for any tenant, mark this feature for refresh
                        if all_tenant_updates:
                            changed_features.add(feature_type)
                    
                    if changed_features:
                        logger.info(f"Detected changes in {len(changed_features)} features")
                        
                        # Refresh schedules for changed features
                        for feature_type in changed_features:
                            await self.refresh_feature_schedules(feature_type)
                            
                except Exception as e:
                    logger.error(f"Error checking for feature changes: {str(e)}")
                        
        except asyncio.CancelledError:
            logger.info("Config change monitor cancelled")
        except Exception as e:
            logger.error(f"Error in config change monitor: {str(e)}")
    
    async def refresh_feature_schedules(self, feature_type):
        """
        Refresh schedules for a specific feature.
        
        Args:
            feature_type: Feature type to refresh
        """
        try:
            logger.info(f"Refreshing schedules for feature {feature_type}")
            
            # Get current schedules for this feature
            current_schedules = {
                schedule_id: schedule
                for schedule_id, schedule in self.dynamic_schedules.items()
                if schedule["feature_type"] == feature_type
            }
            
            # Get current frequency groups using the all-tenants optimized method
            frequency_groups = await self.config_db_client.get_frequency_groups(feature_type)
            
            # Create new schedules that don't exist
            created_count = 0
            updated_count = 0
            
            for group_key, users in frequency_groups.items():
                # Parse group key
                parts = group_key.split(":", 1)
                if len(parts) != 2:
                    continue
                    
                frequency, time_key = parts
                
                # Create schedule ID
                schedule_id = f"{feature_type}_{frequency}_{time_key.replace(':', '_')}"
                
                if schedule_id in current_schedules:
                    # Schedule exists, just update user count
                    if current_schedules[schedule_id]["user_count"] != len(users):
                        self.dynamic_schedules[schedule_id]["user_count"] = len(users)
                        updated_count += 1
                        
                    # Remove from current_schedules to track what's left
                    current_schedules.pop(schedule_id, None)
                else:
                    # New schedule needed
                    new_id = await self.schedule_preference_group(
                        feature_type, frequency, time_key, len(users))
                        
                    if new_id:
                        self.dynamic_schedules[new_id] = {
                            "schedule_id": new_id,
                            "feature_type": feature_type,
                            "frequency": frequency,
                            "time_key": time_key,
                            "user_count": len(users)
                        }
                        created_count += 1
            
            # Remove schedules that no longer exist
            removed_count = 0
            for schedule_id, schedule in current_schedules.items():
                # Remove from scheduler
                try:
                    self.scheduler.remove_job(schedule_id)
                    # Remove from tracking
                    self.dynamic_schedules.pop(schedule_id, None)
                    removed_count += 1
                except Exception:
                    logger.warning(f"Failed to remove schedule {schedule_id}")
            
            logger.info(
                f"Refreshed {feature_type} schedules: "
                f"{created_count} created, {updated_count} updated, {removed_count} removed"
            )
            
        except Exception as e:
            logger.error(f"Error refreshing schedules for {feature_type}: {str(e)}")
    
    def _get_template_for_feature(self, feature_type):
        """Get template ID for a feature type."""
        # This is a fallback that should be delegated to the batch processor
        if hasattr(self.batch_processor, "_get_template_for_feature"):
            return self.batch_processor._get_template_for_feature(feature_type)
            
        # Simple fallback mapping
        templates = {
            "instagram_posts": "instagram_post_generator",
            "etsy_analysis": "etsy_product_analyzer"
        }
        return templates.get(feature_type, "generic_template") 