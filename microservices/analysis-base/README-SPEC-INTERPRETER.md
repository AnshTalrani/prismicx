# Specification Interpreter for Analysis-Base Microservice

## Overview

The Specification Interpreter is a core component of the analysis-base microservice that enables declarative model and pipeline specifications. It serves as a bridge between high-level, declarative specifications written by data scientists or domain experts and the executable code needed to implement those specifications.

This document provides an overview of the specification interpreter architecture, the specification format, and examples of how to use it.

## Architecture

The specification interpreter consists of several key components:

1. **SpecInterpreter Class**: The main class that loads, validates, and interprets specifications.
2. **Model Specifications**: YAML/JSON declarations that define ML models and their parameters.
3. **Decision Tree Specifications**: YAML/JSON declarations that define decision trees for determining actions or strategies.
4. **Pipeline Specifications**: YAML/JSON declarations that define processing pipelines composed of multiple components.

## Specification Formats

### Model Specifications

Model specifications are located in the `specs/models/` directory and define how models should be configured and used. They support multiple model types, including:

- Scikit-learn models
- Text processors
- Feature extractors
- Custom model types

Example model specification:
```yaml
id: "model_id_001"
name: "Example Model"
type: "sklearn"
version: "1.0.0"
algorithm: "RandomForestClassifier"
hyperparameters:
  n_estimators: 100
  max_depth: 10
```

See `specs/examples/model_template.yaml` for a comprehensive example.

### Decision Tree Specifications

Decision tree specifications are located in the `specs/decision_trees/` directory and define decision logic for determining actions, strategies, or recommendations based on contextual data.

Example decision tree specification:
```yaml
id: "decision_tree_001"
name: "Example Decision Tree"
version: "1.0.0"
root:
  type: "condition"
  condition: "data.score > 0.7"
  then:
    result: "HIGH_PRIORITY"
  else:
    result: "STANDARD_PRIORITY"
```

See `specs/examples/decision_tree_template.yaml` for a comprehensive example.

### Pipeline Specifications

Pipeline specifications are located in the `specs/pipelines/` directory and define processing pipelines composed of multiple components. These specifications can reference model and decision tree specifications.

Example pipeline specification:
```yaml
id: "pipeline_001"
name: "Example Pipeline"
version: "1.0.0"
type: "descriptive"
components:
  - type: "transformer"
    name: "data_cleaner"
    model: "data_cleaning_model"
  - type: "analyzer"
    name: "pattern_analyzer"
    model: "pattern_detection_model"
```

See `specs/examples/pipeline_template.yaml` for a comprehensive example.

## Usage

### Loading and Interpreting Specifications

```python
from src.processing.spec_interpreter import get_interpreter

# Get the singleton instance of the spec interpreter
spec_interpreter = get_interpreter()

# Load a model specification
model_spec = spec_interpreter.load_model_spec("model_name")

# Interpret the model specification
interpreted_model = spec_interpreter.interpret_model_spec(model_spec)

# Load a pipeline specification
pipeline_spec = spec_interpreter.load_pipeline_spec("pipeline_name")

# Interpret the pipeline specification
interpreted_pipeline = spec_interpreter.interpret_pipeline_spec(pipeline_spec)

# Evaluate a decision tree against a context
decision_tree_spec = spec_interpreter.load_decision_tree_spec("decision_tree_name")
context = {"data": {"user_segment": "premium", "churn_risk": 0.8}}
result = spec_interpreter.interpret_decision_tree_spec(decision_tree_spec, context)
```

### Creating Components from Specifications

Components can be created using the Component Registry together with specifications:

```python
from src.processing.components.transformers.text_processor import TextProcessor
from src.processing.component_registry import get_registry

# Create a component directly with a model specification name
text_processor = TextProcessor(
    component_id="text_processor_001",
    name="Text Processor",
    model_name="text_cleaning_basic"
)

# Alternatively, use the component registry
registry = get_registry()
component_spec = {
    "type": "transformer",
    "name": "text_cleaner",
    "model": "text_cleaning_basic"
}
component = registry.create_component_from_spec(component_spec)
```

## Adding New Specification Types

To add support for a new model type:

1. Add validation logic to `_validate_model_spec()` in `spec_interpreter.py`
2. Add interpretation logic by creating a new `_interpret_xyz_model()` method
3. Update the `interpret_model_spec()` method to call your new interpreter based on model type

## Testing

A test script is provided at `tests/test_spec_interpreter.py` that demonstrates how to use the specification interpreter with various types of specifications.

To run the tests:

```bash
python tests/test_spec_interpreter.py
```

## Best Practices

1. **Version Your Specifications**: Always include a version number in your specifications to track changes.
2. **Document Your Specifications**: Include descriptions for specifications and their components.
3. **Validate Specifications**: Always validate user-provided specifications before interpreting them.
4. **Cache Interpreted Results**: For performance-critical applications, consider caching interpreted results.
5. **Handle Missing Specifications**: Gracefully handle missing specifications with clear error messages.

## Troubleshooting

Common issues:

- **File Not Found**: Ensure the specification file exists in the correct directory.
- **Invalid Specification**: Check that the specification follows the required format for its type.
- **Missing Required Fields**: Ensure all required fields are present in the specification.
- **Interpretation Errors**: Check that referenced models and components exist and are compatible.

## Further Resources

- See the template specifications in the `specs/examples/` directory.
- Read the docstrings in the `spec_interpreter.py` file for detailed API documentation. 