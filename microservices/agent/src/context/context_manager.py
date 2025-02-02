from typing import Optional
from models.request import Request
from models.context_delta import ContextDelta  # Assuming ContextDelta is defined
from redis_cluster import RedisCluster  # Assuming RedisCluster implementation
from version_control import DVCAdapter  # Assuming DVCAdapter implementation
from uuid import uuid4
from redis_connection import RedisConnection
from models.execution_template import ExecutionTemplate

class ContextManager:
    redis: RedisCluster = RedisCluster(...)  # Initialize with appropriate parameters
    versioning_system: DVCAdapter = DVCAdapter(...)  # Initialize with appropriate parameters

    def __init__(self):
        self.redis = RedisConnection()

    def save_checkpoint(self, request: Request) -> str:
        """
        Saves a checkpoint for the given request.
        """
        # Implementation for saving a checkpoint
        checkpoint_id = self.redis.save(request.to_dict())
        self.versioning_system.track_checkpoint(checkpoint_id)
        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> Request:
        """
        Loads a checkpoint by its ID.
        """
        # Implementation for loading a checkpoint
        data = self.redis.load(checkpoint_id)
        return Request(**data)

    def diff_contexts(self, old: dict, new: dict) -> ContextDelta:
        """
        Computes the difference between two contexts.
        """
        # Implementation for diffing contexts
        delta = {}
        for key in new:
            if old.get(key) != new.get(key):
                delta[key] = {'old': old.get(key), 'new': new.get(key)}
        return ContextDelta(delta)

    def create_batch_context(self, template: ExecutionTemplate) -> str:
        batch_id = f"batch_{uuid4()}"
        self.redis.hset(batch_id, "template", template.json())
        return batch_id

    def update_template_progress(self, batch_id: str, step_index: int):
        self.redis.hset(batch_id, "current_step", step_index) 