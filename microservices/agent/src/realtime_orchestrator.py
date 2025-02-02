class RealtimeOrchestrator:
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    async def execute(self, template: ExecutionTemplate, data: dict):
        """Execute template steps in sequence for real-time requests"""
        context = data.copy()
        
        for step in template.steps:
            result = await self._execute_step(step, context)
            context.update(result)
            
        return context

    async def _execute_step(self, step, context):
        """Execute a single template step"""
        try:
            # Execution logic
        except Exception as e:
            action = self.error_handler.handle_error(e, step)
            self._handle_error_action(action, step, context)

    async def execute_step(self, step: ProcessingStep, context: dict):
        try:
            # Execution logic
        except Exception as e:
            action = self.error_handler.handle_error(e, step)
            self._handle_error_action(action, step, context) 