import importlib
import requests
import asyncio
from microservices.generative-base.src.template import ValidatedTemplate

class DataProcessor:
    def __init__(self):
        self.steps = []
    
    def add_step(self, processor_class: str, method: str, params: dict):
        processor = globals()[processor_class]()
        self.steps.append(
            (processor, method, params)
        )
    
    def execute(self, context: dict):
        for processor, method, params in self.steps:
            func = getattr(processor, method)
            context = func(context, **params)
        return context 

class BatchPipeline:
    def __init__(self, template: ExecutionTemplate, registry: ServiceRegistry):
        self.steps = self._parse_template(template)
        self.registry = registry
    
    def _parse_template(self, template):
        return [
            ProcessingStep(**step.dict())
            for step in template.steps
        ]
    
    def process_item(self, item: dict) -> dict:
        context = item.copy()
        for step in self.steps:
            try:
                result = self._execute_step(step, context)
                context.update(result)
            except Exception as e:
                context["error"] = str(e)
                break
        return context

    def _execute_step(self, step, context):
        service_url = self.registry.get_service_endpoint(step.service)
        inputs = {param: context[ctx_key] for param, ctx_key in step.input_map.items()}
        
        response = requests.post(
            f"{service_url}/execute",
            json={
                "operation": step.operation,
                "inputs": inputs
            },
            timeout=10
        )
        
        return {ctx_key: response.json()[output_key] 
                for output_key, ctx_key in step.output_map.items()} 

async def process_chunk(template: ValidatedTemplate, chunk: list):
    # Initialize pipeline WITH POOL OF 10 WORKERS
    pipeline = BatchPipeline(template, max_workers=10)
    
    # Process all 50 users CONCURRENTLY
    futures = [pipeline.process_item(user) for user in chunk]
    
    # Process steps SEQUENTIALLY per user, but USERS IN PARALLEL
    return await asyncio.gather(*fruits) 