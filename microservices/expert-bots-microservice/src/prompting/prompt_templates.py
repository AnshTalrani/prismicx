class PromptTemplates:
    PRE_TEMPLATE = """Generate strategies for: {purpose_objective}
    Guidelines: {guidelines}
    Success Metrics: {metrics}
    Input: {content}"""
    
    PRO_TEMPLATE = """Refactor this content for better {purpose_objective}:
    Current content: {content}
    Required guidelines: {guidelines}
    Optimization metrics: {metrics}"""
    
    POST_TEMPLATE = """Validate against {purpose_objective} standards:
    Content to check: {content}
    Validation checklist:
    - Guidelines: {guidelines}
    - Metrics: {metrics}"""

    @classmethod
    def get_template(cls, intent: str) -> str:
        return {
            'pre': cls.PRE_TEMPLATE,
            'pro': cls.PRO_TEMPLATE,
            'post': cls.POST_TEMPLATE
        }[intent] 