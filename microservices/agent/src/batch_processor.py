import aiohttp
import asyncio
from microservices.agent.src.models.template import ServiceSequenceTemplate, ExecutionTemplate
from context_manager import ContextManager
from typing import List
from error_handler import ErrorHandler

class BatchProcessor:
    def __init__(self):
        self.context_mgr = ContextManager()
        self.error_handler = ErrorHandler()
    
    async def execute(self, template: ExecutionTemplate, batch_data: List[dict]):
        """Orchestrates batch processing flow"""
        batch_id = self.context_mgr.create_batch_context(template)
        
        # Split into chunks based on template config
        chunks = self._chunk_data(batch_data, template.batch_config["chunk_size"])
        
        # Process chunks through generative-base
        results = await self._process_chunks(template, chunks)
        
        # Handle retries for failed items
        retry_queue = self.error_handler.handle_batch_errors(results)
        if retry_queue:
            retry_results = await self._process_retries(template, chunks, retry_queue)
            results.extend(retry_results)
        
        return self._aggregate_results(batch_id, results)

    async def _process_chunks(self, template, chunks):
        """Process chunks through generative-base"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for chunk in chunks:
                task = self._process_chunk(session, template, chunk)
                tasks.append(task)
            return await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_chunk(self, session, template, chunk):
        """Send chunk to generative-base batch endpoint"""
        return await session.post(
            "http://generative-base/process-batch-chain",
            json={
                "template": template.dict(),
                "batch_items": chunk
            }
        )

    async def execute_sequence(self, template: ServiceSequenceTemplate, batch_data: list):
        chunk_size = template.batch_defaults["chunk_size"]
        
        # Group items by sequence requirements
        grouped_batches = self._organize_by_sequence(batch_data, template)
        
        # Process each sequence group
        for service, items in grouped_batches.items():
            service_template = template.get_service_subtemplate(service)
            chunks = [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]
            
            await self._process_service_chunks(
                service, 
                service_template,
                chunks
            )

    async def _process_service_chunks(self, service, template, chunks):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for chunk in chunks:
                task = session.post(
                    f"http://{service}/process-sequence",
                    json={
                        "template": template.dict(),
                        "batch_items": chunk
                    }
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks) 