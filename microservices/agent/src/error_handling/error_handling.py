"""
Unified error handler for both real-time and batch processing
"""
from models.template import ExecutionTemplate
from collections import defaultdict
from utils.logger import setup_logger

class ErrorHandler:
    def __init__(self):
        self.logger = setup_logger()
        self.error_stats = defaultdict(int)
        self.retry_policies = {}

    def handle_error(self, error: Exception, context: dict) -> str:
        """Template-driven error resolution"""
        error_type = type(error).__name__
        self.logger.error(f"{error_type}: {str(error)}")
        self.error_stats[error_type] += 1
        
        if self._should_retry(error_type, context):
            return "retry"
        return "compensate"

    def _should_retry(self, error_type: str, policy: dict) -> bool:
        return (self.retry_count < policy["max_attempts"] and 
                error_type in policy["retriable_errors"])

    def handle(self, error, context):
        """Template-driven error handling"""
        error_type = type(error).__name__
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1
        
        if context.get('retry_count', 0) < context.get('max_retries', 3):
            return "retry"
        return "abort"

    def handle_batch_errors(self, results, template):
        error_policy = template.error_policy
        retry_queue = []
        
        for idx, result in enumerate(results):
            if "error" in result:
                if self._should_retry(result, error_policy):
                    retry_queue.append(idx)
                else:
                    self._compensate_action(result)
        
        return retry_queue

    def _compensate_action(self, error):
        # Implement compensation logic
        pass 

    def _send_to_elk(self, error):
        # Implement elk communication logic
        pass 