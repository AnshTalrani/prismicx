#!/usr/bin/env python3
"""
Test script for the specification interpreter and text processor component.

This script demonstrates how to use the specification interpreter to load
model specifications and create components based on those specifications.
"""
import asyncio
import logging
import os
import sys
from typing import Any, Dict

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing.spec_interpreter import get_interpreter, SpecInterpreter
from src.processing.components.transformers.text_processor import TextProcessor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_spec_interpreter")


async def test_text_processor():
    """
    Test the TextProcessor component with a specification.
    """
    # Create a TextProcessor component with a model specification
    text_processor = TextProcessor(
        component_id="test_text_processor_001",
        name="Test Text Processor",
        description="A test text processor component",
        model_name="text_cleaning_basic"
    )
    
    # Example text to process
    text = """
    Hello World! This is an example of text that needs cleaning.
    It contains punctuation, stopwords, and other elements that
    may need to be removed or normalized. For example, there are
    multiple   spaces   and   extra   punctuation!!!
    """
    
    # Process the text
    logger.info("Original text:")
    logger.info(text)
    
    processed_text = await text_processor.transform(text)
    
    logger.info("\nProcessed text:")
    logger.info(processed_text)
    
    # Process a list of texts
    texts = [
        "Hello World! This is text #1",
        "Hello World! This is text #2",
        "Hello World! This is text #3"
    ]
    
    logger.info("\nOriginal list of texts:")
    for i, t in enumerate(texts):
        logger.info(f"[{i}] {t}")
    
    processed_texts = await text_processor.transform(texts)
    
    logger.info("\nProcessed list of texts:")
    for i, t in enumerate(processed_texts):
        logger.info(f"[{i}] {t}")
    
    # Process a dictionary with a text field
    text_dict = {
        "id": "doc_001",
        "text": "Hello World! This is a document with metadata.",
        "metadata": {
            "source": "test",
            "timestamp": "2023-07-20T12:00:00"
        }
    }
    
    logger.info("\nOriginal dictionary:")
    logger.info(text_dict)
    
    processed_dict = await text_processor.transform(text_dict)
    
    logger.info("\nProcessed dictionary:")
    logger.info(processed_dict)


async def test_direct_spec_interpreter():
    """
    Test the SpecInterpreter directly to load and interpret specifications.
    """
    # Get the specification interpreter
    spec_interpreter = get_interpreter()
    
    # Load a model specification
    try:
        model_spec = spec_interpreter.load_model_spec("text_cleaning_basic")
        logger.info("Loaded model specification:")
        logger.info(f"ID: {model_spec.get('id')}")
        logger.info(f"Name: {model_spec.get('name')}")
        logger.info(f"Type: {model_spec.get('type')}")
        logger.info(f"Version: {model_spec.get('version')}")
        
        # Interpret the model specification
        interpreted_spec = spec_interpreter.interpret_model_spec(model_spec)
        logger.info("\nInterpreted model specification:")
        logger.info(f"Implementation: {interpreted_spec.get('implementation')}")
        logger.info(f"Language: {interpreted_spec.get('language')}")
        logger.info(f"Number of processors: {len(interpreted_spec.get('processors', []))}")
    except Exception as e:
        logger.error(f"Error loading model specification: {str(e)}")


async def test_pipeline_spec():
    """
    Test loading and interpreting a pipeline specification.
    """
    # Get the specification interpreter
    spec_interpreter = get_interpreter()
    
    # Define a simple pipeline specification inline (normally this would be loaded from a file)
    pipeline_spec = {
        "id": "test_pipeline_001",
        "name": "Test Pipeline",
        "version": "1.0.0",
        "type": "descriptive",
        "description": "A test pipeline specification",
        "components": [
            {
                "type": "transformer",
                "name": "text_cleaner",
                "description": "Cleans and normalizes text data",
                "model": "text_cleaning_basic"
            },
            {
                "type": "analyzer",
                "name": "word_frequency_analyzer",
                "description": "Analyzes word frequencies in the text",
                "config": {
                    "min_word_length": 3,
                    "max_words": 100
                }
            }
        ]
    }
    
    try:
        # Interpret the pipeline specification
        interpreted_pipeline = spec_interpreter.interpret_pipeline_spec(pipeline_spec)
        
        logger.info("Interpreted pipeline specification:")
        logger.info(f"ID: {interpreted_pipeline.get('id')}")
        logger.info(f"Name: {interpreted_pipeline.get('name')}")
        logger.info(f"Number of components: {len(interpreted_pipeline.get('components', []))}")
        
        # Check if the model configuration was loaded for the text_cleaner component
        components = interpreted_pipeline.get("components", [])
        if components and "model_config" in components[0]:
            logger.info("\nFirst component model configuration loaded successfully")
            model_config = components[0]["model_config"]
            logger.info(f"Implementation: {model_config.get('implementation')}")
            logger.info(f"Number of processors: {len(model_config.get('processors', []))}")
    except Exception as e:
        logger.error(f"Error interpreting pipeline specification: {str(e)}")


async def main():
    """
    Run the test functions.
    """
    logger.info("Testing TextProcessor component...")
    await test_text_processor()
    
    logger.info("\n" + "="*80 + "\n")
    
    logger.info("Testing SpecInterpreter directly...")
    await test_direct_spec_interpreter()
    
    logger.info("\n" + "="*80 + "\n")
    
    logger.info("Testing pipeline specification interpretation...")
    await test_pipeline_spec()


if __name__ == "__main__":
    asyncio.run(main()) 