# Model Adapters System

This directory contains the adapter system for enhancing language models with domain-specific capabilities. The adapter system allows language models to be fine-tuned for specialized tasks without requiring full model retraining.

## Overview

The adapter system provides a framework for:

1. **Domain-specific adaptation** - Enhance models with specialized capabilities for sales, support, and persuasion
2. **Dynamic adapter switching** - Change model behavior at runtime based on conversation context
3. **Configurable behavior** - Fine-tune adapter parameters for specific use cases
4. **Framework-agnostic design** - Works with different model architectures and frameworks

## Architecture

The adapter system follows a layered architecture:

```
BaseAdapter (abstract base class)
    ├── HypnosisAdapter (persuasion techniques)
    ├── SalesAdapter (sales methodologies)
    └── SupportAdapter (customer support capabilities)
```

### Components

- **BaseAdapter** (`base_adapter.py`) - Abstract base class defining the adapter interface
- **HypnosisAdapter** (`hypnosis_adapter.py`) - Enhances models with persuasion and influence techniques
- **SalesAdapter** (`sales_adapter.py`) - Adds sales methodologies and persuasion strategies
- **SupportAdapter** (`support_adapter.py`) - Improves empathy and problem-solving for customer support
- **AdapterRegistry** (to be implemented) - Central registry for managing adapters
- **AdapterManager** (to be implemented) - Handles adapter activation and model integration

## Key Features

### Common Adapter Features

All adapters share these core features:

- **Initialization and loading** - Prepare resources and validate configuration
- **Model application** - Apply the adapter to a language model
- **Configuration** - Customizable parameters for adapter behavior
- **Multi-framework support** - Compatible with different model frameworks

### Specialized Capabilities

Each adapter provides unique capabilities:

#### Hypnosis Adapter

- **Covert command embedding** - Subtle embedded directives
- **Pacing and leading** - Matching then guiding language patterns
- **User vocabulary mirroring** - Adapts to user's speech patterns
- **Configurable personas** - Different persuasion styles

#### Sales Adapter

- **AIDA framework** - Attention, Interest, Desire, Action
- **FAB technique** - Features, Advantages, Benefits
- **Objection handling** - Address common customer concerns
- **Industry-specific targeting** - Customized for different business domains

#### Support Adapter

- **Emotion detection** - Recognizes user emotions in text
- **Problem classification** - Categorizes customer issues
- **Empathy enhancement** - Improves emotional responses
- **Knowledge base integration** - Domain-specific solutions

## Usage

### Basic Usage

```python
# Import the adapter
from src.models.adapters.sales_adapter import SalesAdapter

# Initialize the adapter with custom configuration
adapter = SalesAdapter(
    name="finance_sales",
    path="/path/to/adapter/weights",
    config={
        "intensity": 0.7,
        "techniques": {
            "aida": {"enabled": True, "strength": 0.8}
        }
    }
)

# Initialize the adapter
adapter.initialize()

# Apply to a model
adapter.apply_to_model(model)

# Generate text with the adapted model
response = model.generate("Tell me about your services")

# Remove the adapter when done
adapter.remove_from_model(model)
```

### Adapter Switching

```python
# Initialize adapters
sales_adapter = SalesAdapter(name="sales")
sales_adapter.initialize()

support_adapter = SupportAdapter(name="support")
support_adapter.initialize()

# Apply sales adapter for product discussions
sales_adapter.apply_to_model(model)
response = model.generate("Tell me about your pricing plans")

# Switch to support adapter for technical issues
sales_adapter.remove_from_model(model)
support_adapter.apply_to_model(model)
response = model.generate("I'm having trouble with installation")
```

### Specialized Features

#### Sales Adapter Industry Targeting

```python
sales_adapter = SalesAdapter(name="sales")
sales_adapter.initialize()
sales_adapter.apply_to_model(model)

# Set industry targeting
sales_adapter.set_target_audience("healthcare")

# Generate industry-specific responses
response = model.generate("How can your solution help our hospital?")
```

#### Support Adapter Emotion Analysis

```python
support_adapter = SupportAdapter(name="support")
support_adapter.initialize()
support_adapter.apply_to_model(model)

# Analyze customer query for emotions and issues
analysis = support_adapter.analyze_user_query(
    "I'm really frustrated that your app keeps crashing!"
)

# Access detected emotions
emotions = support_adapter.get_detected_emotions()
```

## Adapter Files and Resources

Each adapter expects certain resources in its specified path:

### Hypnosis Adapter

- `patterns.json` - Persuasion and influence language patterns
- `weights/` - PEFT/LoRA weights for the adapter

### Sales Adapter

- `sales_patterns.json` - Sales techniques and templates
- `industries/` - Industry-specific terminology and value propositions
- `weights/` - PEFT/LoRA weights for the adapter

### Support Adapter

- `support_patterns.json` - Support phrases and emotion indicators
- `knowledge_bases/` - Domain-specific problem solutions
- `weights/` - PEFT/LoRA weights for the adapter

## Examples

See the `examples` directory for complete usage examples:

- `adapter_usage_example.py` - Demonstrates basic adapter usage
- `conversation_switching.py` (to be implemented) - Shows dynamic adapter switching
- `custom_adapter_example.py` (to be implemented) - Guide for creating custom adapters

## Extending the System

To create a custom adapter:

1. Subclass `BaseAdapter` from `base_adapter.py`
2. Implement required methods: `_initialize()`, `_load()`, `apply_to_model()`, `remove_from_model()`
3. Define adapter-specific configuration and methods
4. Register with `AdapterRegistry` (when implemented)

## Technical Details

### Model Compatibility

The adapter system supports multiple integration methods:

1. **PEFT/LoRA integration** - For models with PEFT support
2. **Generation hooks** - For models with generation pipeline hooks
3. **Custom adapter methods** - For models with adapter-specific APIs
4. **Method monkey-patching** - Fallback for other model types

### Configuration Options

Common configuration parameters across adapters:

- `intensity` - Overall strength of adapter effects (0.0-1.0)
- `techniques` - Enable/disable specific techniques and their strengths
- `tone` - The communication style to use (varies by adapter)

## Future Roadmap

- **AdapterRegistry** - Central registry for adapter discovery and management
- **AdapterManager** - Automated adapter selection and switching
- **Adapter composition** - Combine multiple adapters with priority control
- **Domain expansion** - Additional specialized adapters for new domains
- **Performance optimization** - Reduced memory footprint for adapter switching 