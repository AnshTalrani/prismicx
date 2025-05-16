"""
Data extraction module handling data collection from various sources.
"""

from .data_fetcher import DataFetcher
from .scraper import Scraper
from .data_processor import DataProcessor
from .database_updater import DatabaseUpdater
from .data_retriever import DataRetriever
from ..common.utils import Utils

class ExtractHandler:
    """Orchestrates intelligent data extraction with prioritized search"""
    
    def __init__(self, template):
        self.template = template
        self.fetcher = DataFetcher()
        self.scraper = Scraper()
        self.processor = DataProcessor()
        self.updater = DatabaseUpdater()
        self.retriever = DataRetriever()
    
    @Utils.retry_operation
    def extract_data(self, query_context: dict):
        """
        Execute extraction pipeline with semantic search first
        
        Args:
            query_context (dict): Contains search parameters and requirements
        """
        # First try semantic search in existing database
        relevant_data = self._search_database(query_context)
        
        if not self._is_data_sufficient(relevant_data):
            # If database search insufficient, fetch from external sources
            raw_data = self._fetch_external_data(query_context)
            processed_data = self._process_raw_data(raw_data)
            
            # Update database with new information
            self._update_databases(processed_data)
            
            # Combine existing and new data
            relevant_data.update(processed_data)
        
        self.template.extracted_data = relevant_data
        return relevant_data

    def _search_database(self, query_context: dict) -> dict:
        """Semantic search in existing database"""
        search_queries = self._generate_search_queries(query_context)
        results = {}
        
        for query_type, query in search_queries.items():
            similar_records = self.retriever.retrieve_similar(
                query=query,
                top_k=5,
                threshold=0.7  # Minimum similarity threshold
            )
            results[query_type] = similar_records
        
        return results

    def _is_data_sufficient(self, data: dict) -> bool:
        """
        Check if retrieved data meets requirements
        """
        # Implementation depends on your specific criteria
        return len(data) > 0 and all(
            len(records) >= 2 for records in data.values()
        )

    def _generate_search_queries(self, context: dict) -> dict:
        """
        Generate semantic search queries from context
        """
        return {
            "trends": context.get("trend_requirements", ""),
            "keywords": context.get("keyword_requirements", ""),
            "painpoints": context.get("painpoint_requirements", "")
        }

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
            ),
            "embeddings": self.processor.compute_embeddings(
                raw_data.get('social', [])
            )
        }

    def _fetch_external_data(self, query_context: dict) -> dict:
        """Fetch data from external sources"""
        # Implementation depends on your specific data fetching logic
        return {}

    def _update_databases(self, data: dict):
        """Handle database update operations"""
        self.updater.update_database(data)
        self.updater.schedule_updates(
            self.template.context.get('schedule_params', {})
        ) 