from typing import List, Dict, Any

class WorkerBase:
    async def _find_pending_contexts(self) -> List[Dict[str, Any]]:
        """Find pending contexts for this worker's service type."""
        try:
            query = {
                "status": "pending",
                "$or": [
                    {"template.service_type": self.service_type},
                    {"tags.service": self.service_type}
                ]
            }
            # Sort by priority (lower number = higher priority), then by creation time
            cursor = self.repository.contexts.find(query).sort([
                ("priority", 1),  # Sort by priority ascending (1=highest)
                ("created_at", 1)  # Then sort by creation time
            ]).limit(self.batch_size)
            
            return await cursor.to_list(length=self.batch_size)
        except Exception as e:
            self.logger.error(f"Error finding pending contexts: {str(e)}")
            return [] 