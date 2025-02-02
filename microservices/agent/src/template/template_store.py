from redis import Redis
from models.template import ExecutionTemplate

class TemplateStore:
    def __init__(self):
        self.redis = Redis(host='redis', port=6379, db=0)
    
    def get(self, purpose_id: str) -> ExecutionTemplate:
        """Retrieve template from storage"""
        template_data = self.redis.get(f"template:{purpose_id}")
        return ExecutionTemplate.parse_raw(template_data) if template_data else None
    
    def save(self, template: ExecutionTemplate):
        """Persist template to storage"""
        self.redis.set(f"template:{template.id}", template.json()) 