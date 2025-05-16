"""
Tests for output generation components
"""

import unittest
from unittest.mock import patch, MagicMock
from src.high_quality_output_generation_module.handler import OutputGenerator
from src.template import Template

class TestOutputGenerator(unittest.TestCase):
    
    @patch('src.high_quality_output_generation_module.handler.ContentGenerator')
    @patch('src.high_quality_output_generation_module.handler.VariableExtractor')
    def test_generation_success(self, mock_extractor, mock_generator):
        template = Template("test_purpose")
        template.selected_info = {
            "generation_prompt": "Test prompt",
            "generation_params": {"length": 100}
        }
        
        mock_gen = mock_generator.return_value
        mock_gen.generate_content.return_value = {"text": "Test content"}
        
        mock_ext = mock_extractor.return_value
        mock_ext.extract_hashtags.return_value = ["test"]
        mock_ext.extract_cta.return_value = "Click here"
        mock_ext.extract_product_mentions.return_value = ["Product"]
        
        generator = OutputGenerator(template)
        generator.generate_output()
        
        self.assertIn("content", template.generated_output) 