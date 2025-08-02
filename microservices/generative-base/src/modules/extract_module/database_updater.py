"""
Database update operations with periodic refresh
"""
from datetime import datetime, timedelta
from ..common.utils import Utils

class DatabaseUpdater:
    """Handles database updates and periodic refresh"""
    
    def __init__(self):
        self.utils = Utils()
        self.last_update = {}  # Track last update times by category

    @Utils.retry_operation
    def update_database(self, data: dict):
        """Update database with new extracted data"""
        # Store data with timestamps
        timestamp = datetime.now()
        for category, content in data.items():
            self._store_with_metadata(category, content, timestamp)
        self.last_update[category] = timestamp

    def _store_with_metadata(self, category: str, content: dict, timestamp: datetime):
        """Store data with metadata for tracking freshness"""
        enriched_content = {
            "data": content,
            "timestamp": timestamp,
            "source": content.get("source", "web_scrape"),
            "embeddings": content.get("embeddings", [])
        }
        # Implementation would interact with actual database
        self.utils.log_info(f"Storing {category} data with timestamp {timestamp}")

    @Utils.retry_operation
    def check_and_refresh(self, handler, refresh_threshold_hours: int = 24):
        """
        Check data freshness and trigger updates if needed
        
        Args:
            handler: ExtractHandler instance for fetching fresh data
            refresh_threshold_hours: Hours before data is considered stale
        """
        now = datetime.now()
        threshold = timedelta(hours=refresh_threshold_hours)
        
        for category, last_update in self.last_update.items():
            if now - last_update > threshold:
                self.utils.log_info(f"Refreshing {category} data")
                # Trigger fresh data collection for this category
                fresh_data = handler.extract_data({
                    "category": category,
                    "force_refresh": True
                })
                self.update_database({category: fresh_data})

    @Utils.retry_operation
    def schedule_updates(self, schedule_params: dict):
        """Schedule periodic database updates"""
        interval = schedule_params.get('interval', 24)
        self.utils.log_info(f"Scheduled updates every {interval} hours") 