"""
Output generation handler combining content and variable extraction
"""

from .generator import ContentGenerator
from .extractor import VariableExtractor
from ..common.utils import Utils

class OutputGenerator:
    """Orchestrates high-quality output generation"""
    
    def __init__(self, template):
        self.template = template
        self.content_gen = ContentGenerator()
        self.var_extractor = VariableExtractor()
        self.utils = Utils()

    @Utils.retry_operation
    def generate_output(self):
        """Execute full output generation pipeline"""
        try:
            # Get generation parameters from template
            prompt = self.template.selected_info.get('generation_prompt', '')
            params = self.template.selected_info.get('generation_params', {})
            
            # Generate base content
            raw_content = self.content_gen.generate_content(prompt, params)
            
            # Extract structured elements
            self.template.generated_output = {
                "content": raw_content.get('text', ''),
                "metadata": {
                    "hashtags": self.var_extractor.extract_hashtags(raw_content.get('text', '')),
                    "cta": self.var_extractor.extract_cta(raw_content.get('text', '')),
                    "product_mentions": self.var_extractor.extract_product_mentions(raw_content.get('text', ''))
                },
                "raw_response": raw_content
            }
        except Exception as e:
            self.utils.log_error(f"Output generation failed: {e}")
            raise 