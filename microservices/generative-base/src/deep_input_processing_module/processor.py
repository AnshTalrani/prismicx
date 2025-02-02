"""
Deep input processing handler
"""

from .strategist import AIStrategist
from ..common.utils import Utils

class DeepInputProcessor:
    """Orchestrates deep input processing workflow"""
    
    def __init__(self, template):
        self.template = template
        self.strategist = AIStrategist()
        self.utils = Utils()

    @Utils.retry_operation
    def process_input(self):
        """Execute deep input processing pipeline"""
        try:
            # Resolve conflicts and generate prompt
            strategy = self.strategist.resolve_conflicts(
                self.template.extracted_data.get('trends', []),
                self.template.user_details.get('brand_alignment', 0.5)
            )
            
            prompt, params = self.strategist.generate_fine_tuned_prompt(
                self.template.purpose_id,
                self.template.extracted_data,
                self.template.user_details
            )
            
            # Update template with processed information
            self.template.selected_info.update({
                "strategy": strategy,
                "generation_prompt": prompt,
                "generation_params": params
            })
            
        except Exception as e:
            self.utils.log_error(f"Deep input processing failed: {e}")
            raise 