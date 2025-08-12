class LLMService:
    """
    Large Language Model (LLM) Service interface for modular integration.
    Implement generate_response() with your preferred LLM (e.g., OpenAI, local model).
    """
    async def generate_response(self, context: dict, prompt: str) -> str:
        """
        Generate a response using LLM. Should be implemented by subclass.
        Args:
            context: Conversation context
            prompt: User input or system prompt
        Returns:
            Generated text response
        """
        raise NotImplementedError("LLMService.generate_response must be implemented by subclass")
