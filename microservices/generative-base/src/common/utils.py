"""
Common utilities for logging and operational functions.
"""

import time
import logging

class Utils:
    """Provides common utility methods for the microservice"""
    
    @staticmethod
    def log_info(message: str):
        """Structured info logging"""
        logging.info(f"[GenerativeBase] {message}")
    
    @staticmethod
    def log_error(message: str):
        """Structured error logging"""
        logging.error(f"[GenerativeBase] {message}")
    
    @staticmethod
    def retry_operation(operation, max_retries=3, backoff_factor=1):
        """
        Retry decorator with exponential backoff
        
        Args:
            operation: Function to retry
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for backoff timing
        """
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                sleep_time = backoff_factor * (2 ** attempt)
                time.sleep(sleep_time) 