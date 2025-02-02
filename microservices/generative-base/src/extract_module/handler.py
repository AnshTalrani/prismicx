"""
Data extraction module handling data collection from various sources.
"""

from .data_fetcher import DataFetcher
from .scraper import Scraper
from .data_processor import DataProcessor
from .database_updater import DatabaseUpdater
from ..common.utils import Utils

class ExtractHandler:
    """Orchestrates data extraction from multiple sources"""
    
    def __init__(self, template):
        self.template = template
        self.fetcher = DataFetcher()
        self.scraper = Scraper()
        self.processor = DataProcessor()
        self.updater = DatabaseUpdater()
    
    @Utils.retry_operation
    def extract_data(self):
        """Execute full extraction pipeline"""
        raw_data = {
            "database": self.fetcher.fetch_from_database(
                self.template.context.get('query_params')
            ),
            "web": self.fetcher.fetch_from_web(
                self.template.context.get('sources')
            ),
            "social": self.scraper.scrape_social_media(
                self.template.context.get('social_params')
            )
        }
        
        processed_data = self._process_raw_data(raw_data)
        self.template.extracted_data = processed_data
        self._update_databases(processed_data)

    def _process_raw_data(self, raw_data: dict) -> dict:
        """Process and analyze raw data"""
        return {
            "sentiment": self.processor.perform_sentiment_analysis(
                raw_data.get('social', [])
            ),
            "keywords": self.processor.extract_keywords(
                raw_data.get('web', [])
            ),
            "trends": self.processor.analyze_trends(
                raw_data.get('database', [])
            )
        }

    def _update_databases(self, data: dict):
        """Handle database update operations"""
        self.updater.update_database(data)
        self.updater.schedule_updates(
            self.template.context.get('schedule_params', {})
        ) 