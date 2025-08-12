from src.services.llm_service import LLMService
from typing import Dict

try:
    import transformers
except ImportError:
    transformers = None

class GPT20BLLMService(LLMService):
    """
    TinyLlama 1.1B-based LLM Service implementation.
    """
    def __init__(self, model_name: str = "facebook/opt-125m"):
        if transformers is None:
            raise ImportError("transformers package is required for GPT20BLLMService")
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
        self.model = transformers.AutoModelForCausalLM.from_pretrained(model_name)

    async def generate_response(self, context: Dict, prompt: str) -> str:
        input_text = prompt
        if context:
            input_text = context.get("history", "") + "\n" + prompt
        inputs = self.tokenizer(input_text, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=16)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(input_text):].strip()
