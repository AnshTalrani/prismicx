def handle_batch_errors(self, results):
    return [
        idx for idx, result in enumerate(results)
        if "error" in result and 
        result["error"]["type"] in self.retriable_errors
    ] 

class BatchErrorHandler:
    def handle_service_errors(self, result: dict) -> bool:
        error_type = result.get("error", {}).get("type")
        return error_type in self.retriable_errors
    
    def create_compensation_plan(self, failed_step: ProcessingStep):
        return {
            "action": "rollback",
            "steps": self._get_rollback_steps(failed_step),
            "notification": "batch_compensation_required"
        } 