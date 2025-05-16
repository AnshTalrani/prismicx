#!/usr/bin/env python
"""
Adapter Usage Example

This script demonstrates how to use the different domain-specific adapters
(hypnosis, sales, support) with various language models. It shows:
- Initializing adapters with different configurations
- Applying adapters to models
- Configuring adapter behavior for specific use cases
- Switching between adapters for different conversation contexts
- Basic error handling and cleanup

Run this script with:
    python adapter_usage_example.py

Note: This example assumes you have the required language models and adapter weights
installed in the expected locations.
"""

import os
import logging
import sys
from typing import Dict, Any, List, Optional
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

# Import the required modules
from src.models.adapters.hypnosis_adapter import HypnosisAdapter
from src.models.adapters.sales_adapter import SalesAdapter
from src.models.adapters.support_adapter import SupportAdapter

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_dummy_model(model_name: str) -> Any:
    """
    Load a dummy model for demonstration purposes.
    
    In a real application, this would load an actual language model
    using libraries like transformers, torch, etc.
    
    Args:
        model_name: Name of the model to load
    
    Returns:
        A mock model object for demonstration
    """
    logger.info(f"Loading model: {model_name}")
    
    # This is just a dummy model for demonstration
    class DummyModel:
        def __init__(self, name):
            self.name = name
            self.generation_config = type('obj', (object,), {
                'logits_processor': []
            })
            self._original_methods = {}
            
        def generate(self, prompt, **kwargs):
            """Mock generate method"""
            return f"Response from {self.name}: {prompt}"
            
        def __str__(self):
            return f"Model({self.name})"
    
    # Simulate loading time
    time.sleep(1)
    return DummyModel(model_name)


def demo_hypnosis_adapter():
    """Demonstrate the usage of HypnosisAdapter."""
    logger.info("\n--- Demonstrating Hypnosis Adapter ---")
    
    # Load a model
    model = load_dummy_model("mistral-7b")
    
    try:
        # Initialize the hypnosis adapter with custom config
        hypnosis_config = {
            "intensity": 0.7,
            "techniques": {
                "covert_commands": {"enabled": True, "strength": 0.8},
                "pacing_leading": {"enabled": True, "strength": 0.7},
                "vocabulary_mirroring": {"enabled": False}
            },
            "persona": "trusted_advisor"
        }
        
        adapter = HypnosisAdapter(
            name="subtle_influence",
            path="/path/to/hypnosis/adapter",  # Would be an actual path in production
            config=hypnosis_config
        )
        
        # Initialize and apply to model
        logger.info("Initializing hypnosis adapter")
        adapter.initialize()
        
        logger.info("Applying hypnosis adapter to model")
        adapter.apply_to_model(model)
        
        # Demonstrate generating text with the adapter
        prompt = "Tell me about the benefits of using AI in healthcare"
        logger.info(f"Generating response with prompt: '{prompt}'")
        response = model.generate(prompt)
        
        # In a real application, the adapter would modify the response
        # to include hypnosis techniques
        logger.info(f"Generated response: '{response}'")
        
        # Remove the adapter when done
        logger.info("Removing hypnosis adapter from model")
        adapter.remove_from_model(model)
        
    except Exception as e:
        logger.error(f"Error in hypnosis adapter demo: {e}")
        
    finally:
        # Cleanup
        logger.info("Hypnosis adapter demo completed")


def demo_sales_adapter():
    """Demonstrate the usage of SalesAdapter."""
    logger.info("\n--- Demonstrating Sales Adapter ---")
    
    # Load a model
    model = load_dummy_model("llama-7b")
    
    try:
        # Initialize the sales adapter with custom config
        sales_config = {
            "intensity": 0.6,
            "techniques": {
                "aida": {"enabled": True, "strength": 0.8},
                "fab": {"enabled": True, "strength": 0.7},
                "objection_handling": {"enabled": True, "strength": 0.9}
            },
            "tone": "consultative",
            "target_audience": "finance"
        }
        
        adapter = SalesAdapter(
            name="finance_sales",
            path="/path/to/sales/adapter",  # Would be an actual path in production
            config=sales_config
        )
        
        # Initialize and apply to model
        logger.info("Initializing sales adapter")
        adapter.initialize()
        
        logger.info("Applying sales adapter to model")
        adapter.apply_to_model(model)
        
        # Demonstrate industry-specific targeting
        logger.info("Available industries: ['finance', 'healthcare', 'technology']")
        logger.info("Setting target audience to finance industry")
        adapter.set_target_audience("finance")
        
        # Demonstrate generating text with the adapter
        prompt = "Tell me about your investment advisory services"
        logger.info(f"Generating response with prompt: '{prompt}'")
        response = model.generate(prompt)
        
        # In a real application, the adapter would modify the response
        # to include sales techniques specific to finance
        logger.info(f"Generated response: '{response}'")
        
        # Remove the adapter when done
        logger.info("Removing sales adapter from model")
        adapter.remove_from_model(model)
        
    except Exception as e:
        logger.error(f"Error in sales adapter demo: {e}")
        
    finally:
        # Cleanup
        logger.info("Sales adapter demo completed")


def demo_support_adapter():
    """Demonstrate the usage of SupportAdapter."""
    logger.info("\n--- Demonstrating Support Adapter ---")
    
    # Load a model
    model = load_dummy_model("gpt-j")
    
    try:
        # Initialize the support adapter with custom config
        support_config = {
            "empathy_level": 0.8,
            "techniques": {
                "active_listening": {"enabled": True, "strength": 0.9},
                "emotional_intelligence": {"enabled": True, "strength": 0.8},
                "follow_up_questions": {"enabled": True, "strength": 0.7}
            },
            "tone": "supportive",
            "knowledge_base": "software"
        }
        
        adapter = SupportAdapter(
            name="tech_support",
            path="/path/to/support/adapter",  # Would be an actual path in production
            config=support_config
        )
        
        # Initialize and apply to model
        logger.info("Initializing support adapter")
        adapter.initialize()
        
        logger.info("Applying support adapter to model")
        adapter.apply_to_model(model)
        
        # Demonstrate conversation state tracking
        logger.info("Starting new customer support conversation")
        adapter.clear_conversation_state()
        
        # Process user queries
        queries = [
            "I'm really frustrated that your app keeps crashing when I try to export my data",
            "Yes, I'm using the latest version on Windows 10",
            "I've tried restarting but it still doesn't work!"
        ]
        
        for query in queries:
            logger.info(f"\nUser query: '{query}'")
            
            # Analyze the query for emotions and issues
            analysis = adapter.analyze_user_query(query)
            logger.info(f"Query analysis: {analysis}")
            
            # Generate a response
            response = model.generate(query)
            logger.info(f"Generated response: '{response}'")
        
        # Show the conversation state
        logger.info("\nConversation summary:")
        logger.info(f"Detected emotions: {adapter.get_detected_emotions()}")
        logger.info(f"Identified issues: {len(adapter.get_identified_issues())}")
        
        # Remove the adapter when done
        logger.info("Removing support adapter from model")
        adapter.remove_from_model(model)
        
    except Exception as e:
        logger.error(f"Error in support adapter demo: {e}")
        
    finally:
        # Cleanup
        logger.info("Support adapter demo completed")


def demo_adapter_switching():
    """Demonstrate switching between different adapters for the same model."""
    logger.info("\n--- Demonstrating Adapter Switching ---")
    
    # Load a model
    model = load_dummy_model("falcon-7b")
    
    adapters = {}
    
    try:
        # Initialize all adapters
        logger.info("Initializing adapters")
        
        adapters["sales"] = SalesAdapter(name="sales")
        adapters["sales"].initialize()
        
        adapters["support"] = SupportAdapter(name="support")
        adapters["support"].initialize()
        
        adapters["hypnosis"] = HypnosisAdapter(name="hypnosis")
        adapters["hypnosis"].initialize()
        
        # Demonstrate switching between adapters
        conversations = [
            {"type": "sales", "query": "Tell me about your premium plans"},
            {"type": "support", "query": "I'm having trouble logging in"},
            {"type": "hypnosis", "query": "I'm not sure if your product is right for me"},
            {"type": "sales", "query": "What makes your service better than competitors?"}
        ]
        
        active_adapter = None
        
        for conversation in conversations:
            adapter_type = conversation["type"]
            query = conversation["query"]
            
            logger.info(f"\nSwitching to {adapter_type} context")
            logger.info(f"User query: '{query}'")
            
            # If a different adapter is active, remove it
            if active_adapter and active_adapter != adapter_type:
                logger.info(f"Removing {active_adapter} adapter")
                adapters[active_adapter].remove_from_model(model)
            
            # Apply the new adapter if needed
            if active_adapter != adapter_type:
                logger.info(f"Applying {adapter_type} adapter")
                adapters[adapter_type].apply_to_model(model)
                active_adapter = adapter_type
            
            # Generate response
            response = model.generate(query)
            logger.info(f"Generated response ({adapter_type}): '{response}'")
        
        # Clean up
        if active_adapter:
            logger.info(f"Removing {active_adapter} adapter")
            adapters[active_adapter].remove_from_model(model)
        
    except Exception as e:
        logger.error(f"Error in adapter switching demo: {e}")
        
    finally:
        # Cleanup
        logger.info("Adapter switching demo completed")


def main():
    """Run all adapter demonstrations."""
    logger.info("Starting adapter usage examples")
    
    try:
        # Run the individual demos
        demo_hypnosis_adapter()
        demo_sales_adapter()
        demo_support_adapter()
        demo_adapter_switching()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        
    finally:
        logger.info("Adapter usage examples completed")


if __name__ == "__main__":
    main() 