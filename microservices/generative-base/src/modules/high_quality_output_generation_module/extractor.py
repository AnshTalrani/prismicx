"""
Variable extraction components for output generation
"""

import re
from ..common.utils import Utils

class VariableExtractor:
    """Extracts structured elements from generated content"""
    
    def __init__(self):
        self.utils = Utils()

    @Utils.retry_operation
    def extract_hashtags(self, text: str) -> list:
        """Extract hashtags from text content"""
        return re.findall(r"#(\w+)", text)

    @Utils.retry_operation
    def extract_cta(self, text: str) -> str:
        """Identify primary call-to-action phrase"""
        cta_patterns = [
            r"(\b(?:Shop now|Learn more|Sign up|Subscribe|Buy today)\b)",
            r"([A-Z][^.!?]*\!)"
        ]
        for pattern in cta_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return ""

    @Utils.retry_operation
    def extract_product_mentions(self, text: str) -> list:
        """Extract product names from text"""
        return re.findall(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b", text) 