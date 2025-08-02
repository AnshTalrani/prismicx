# Document-Driven Framework Configuration

This directory contains YAML configuration files that control the behavior of the Generative Base framework. These configuration files allow AI specialists to modify the system's behavior without needing to understand or modify the underlying code.

## Overview

The Generative Base framework is designed to be controlled entirely through documentation rather than code modifications. This approach enables AI specialists to focus on their areas of expertise (prompts, AI models, parameters) while minimizing the need to understand the underlying code implementation.

## Key Files

### 1. `framework_definition.yaml`

This is the master configuration file that defines the overall structure of the generative framework:

- **System configuration**: Global settings for the framework
- **Module registry**: List of all available processing modules
- **Processing flows**: Predefined sequences of modules for different tasks
- **Parameter templates**: Reusable parameter sets for common generation tasks
- **Error handling**: Strategies for handling processing errors

AI specialists can modify this file to:
- Enable or disable specific modules
- Create new processing flows
- Adjust global system parameters
- Define new parameter templates

### 2. `modules_combined.yaml`

This comprehensive file defines all the AI processing modules available in the system:

- **Module behavior**: Input/output types, AI models, and configuration options
- **Prompt templates**: The actual prompts used by each module
- **AI model configuration**: Model selection, parameters, and fallback options
- **Processing logic**: Behavior rules and processing options

AI specialists can modify this file to:
- Change prompt templates
- Adjust AI model parameters (temperature, max tokens, etc.)
- Add or modify processing options
- Configure module-specific behavior

### 3. `processing.md`

This documentation file explains the processing architecture of the Generative Base service:

- **Key components**: Pipeline, Pipeline Builder, Context Poller, Component Registry, etc.
- **Processing flows**: How components are sequenced to process contexts
- **Template processing**: How templates are mapped to appropriate flows
- **Batch processing**: Efficient handling of multiple related contexts
- **Error handling**: Strategies for handling processing errors
- **Metrics and monitoring**: How processing performance is measured

AI specialists should refer to this file to understand how the processing system works and how to configure it.

### 4. `custom_processing_examples.md`

This documentation file provides practical examples of creating and configuring custom processing components:

- **Creating a custom component**: Step-by-step examples with YAML configurations
- **Implementing custom processing logic**: Examples of Python code for complex components
- **Advanced configuration examples**: Examples of conditional and parallel processing flows
- **Best practices**: Guidelines for creating effective and maintainable components
- **Troubleshooting**: Common issues and solutions when creating custom components

AI specialists should refer to this file for practical guidance on extending the processing system.

## How to Use

1. **Make changes to YAML files only** - Don't modify the code
2. **Restart the service** after changing configuration files
3. **Check logs** to verify your changes were applied correctly

## Example: Modifying a Module

To change the behavior of the "high_quality_output" module:

1. Open `modules_combined.yaml`
2. Find the "HIGH QUALITY OUTPUT MODULE" section
3. Modify the prompt templates, AI model parameters, or configuration options
4. Save the file and restart the service

## Example: Creating a New Flow

To create a new processing flow:

1. Open `framework_definition.yaml`
2. Under the "flows" section, add a new flow definition:
   ```yaml
   - id: "my_custom_flow"
     name: "My Custom Flow"
     description: "A custom flow for specific content generation"
     modules:
       - id: "input_preprocessing"
         config_override: {}
       - id: "high_quality_output"
         config_override: {
           "temperature": 0.8,
           "style": "narrative"
         }
   ```
3. Save the file and restart the service

## Guidelines for AI Specialists

1. **Document all changes** you make to the configuration files
2. **Test thoroughly** after making changes
3. **Start with small modifications** before making larger changes
4. **Keep backups** of working configurations

For questions or support, please contact the development team. 