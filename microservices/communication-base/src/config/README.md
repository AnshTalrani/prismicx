# Configuration System

The Configuration System provides a robust, flexible way to manage configurations across the communication platform. It supports multi-level inheritance, hot-reloading, and session-specific overrides while maintaining an efficient implementation.

## Key Features

- **Multi-Level Configuration Inheritance**: Seamlessly merges base, bot-specific, and session-specific configurations
- **Hot Reloading**: Detects configuration changes on disk and automatically applies them
- **Efficient Caching**: Minimizes overhead by caching merged configurations
- **Dot Notation Access**: Easy access to nested configuration values
- **Session-Specific Overrides**: Apply temporary configuration changes for specific user sessions
- **Comprehensive Error Handling**: Graceful recovery from configuration errors

## Architecture

The system consists of five core components:

1. **ConfigLoader**: Handles loading configuration files from disk (YAML/JSON)
2. **ConfigInheritance**: Provides functionality for merging configurations with proper inheritance
3. **ConfigManager**: Central manager for configuration storage and access
4. **ConfigWatcher**: Monitors configuration files for changes and triggers reloading
5. **ConfigIntegration**: Facade that integrates the configuration system with the rest of the application

## Usage Examples

### Basic Usage

```python
from src.config.config_integration import ConfigIntegration

# Get singleton instance
config_integration = ConfigIntegration()

# Initialize with config directory
config_integration.initialize("/path/to/config/dir")

# Get full configuration for a bot type
sales_config = config_integration.get_config("sales")

# Get specific configuration value
temperature = config_integration.get_value("sales", "models.llm.temperature", default=0.7)
```

### Session-Specific Overrides

```python
# Define session-specific configuration overrides
session_overrides = {
    "models.llm.temperature": 0.5,  # Override temperature
    "session.context": {            # Add new session-specific value
        "user_expertise": "expert",
        "previous_topics": ["pricing", "features"]
    }
}

# Update session configuration
config_integration.update_session_config(
    session_id="user123-session456",
    bot_type="sales",
    updates=session_overrides
)

# Get a value with session context
temperature = config_integration.get_value(
    "sales", 
    "models.llm.temperature",
    session_id="user123-session456"
)
```

### Handling Configuration Changes

The system automatically detects changes to configuration files and reloads them. You can also manually trigger a reload:

```python
# Manually reload configurations
config_integration.reload_configs()

# Clear cached configurations for a specific session
config_integration.clear_session_cache(session_id="user123-session456")
```

## Configuration Structure

The system expects a specific directory structure:

```
config/
├── base.yaml           # Base configuration for all bots
└── bots/               # Bot-specific configurations
    ├── consultancy.yaml
    ├── sales.yaml
    └── support.yaml
```

### Configuration Files

Configuration files can be in YAML or JSON format. The system will automatically determine the format based on the file extension.

### Base Configuration

The base configuration (`base.yaml`) contains settings that apply to all bots:

```yaml
models:
  llm:
    default_model: "gpt-3.5-turbo"
    temperature: 0.7
    max_tokens: 1000
rag:
  enabled: true
  vector_store:
    similarity: "cosine"
    top_k: 5
session:
  timeout: 3600
  memory_type: "buffer"
```

### Bot-Specific Configuration

Bot-specific configurations (e.g., `bots/sales.yaml`) contain settings that apply only to a specific bot type and override base settings where applicable:

```yaml
models:
  llm:
    default_model: "gpt-4"  # Override the base setting
    temperature: 0.8        # Override the base setting
rag:
  vector_store:
    top_k: 10               # Override the base setting
    collections:            # Add new setting not in base
      - "products"
      - "campaigns"
sales_specific:             # Bot-specific settings
  campaign_stages:
    - "awareness"
    - "interest" 
    - "decision"
  follow_up_days: 3
```

## Best Practices

1. **Keep sensitive information out of config files**: Use environment variables for API keys, credentials, etc.
2. **Use descriptive names for configuration keys**: Make it clear what each setting does
3. **Provide sensible defaults**: Ensure the system can function with minimal configuration
4. **Document configuration options**: Include comments in config files to explain settings
5. **Validate configurations**: Use schemas or validation logic to catch configuration errors early

## Full Example

See `example_usage.py` for a complete working example of the configuration system. 