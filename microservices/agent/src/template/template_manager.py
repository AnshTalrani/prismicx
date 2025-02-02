class TemplateManager:
    def __init__(self):
        self.store = TemplateStore()
        self.cache = {}  # In-memory cache
    
    def get_template(self, purpose_id: str, version: str = "latest") -> ExecutionTemplate:
        """Get template with version support"""
        cache_key = f"{purpose_id}:{version}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        template = self.store.get(cache_key) or self._default_template(purpose_id)
        self.cache[cache_key] = template
        return template
    
    def _default_template(self, purpose_id: str) -> ExecutionTemplate:
        return ExecutionTemplate(
            id=f"default_{purpose_id}",
            description=f"Default template for {purpose_id}",
            steps=[]
        ) 