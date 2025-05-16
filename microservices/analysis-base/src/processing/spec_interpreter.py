"""
Specification interpreter for the analysis-base microservice.

This module provides the SpecInterpreter class for loading and interpreting
declarative specifications for ML models and analysis pipelines. It serves
as a bridge between ML expert-defined specifications and executable code.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from src.config.config_loader import get_value


class SpecInterpreter:
    """
    Interpreter for declarative specifications.
    
    This class loads, validates, and interprets declarative specifications
    for ML models, decision trees, and pipelines. It provides methods to
    convert specifications into executable configurations for components.
    
    Attributes:
        logger (logging.Logger): Logger for the interpreter
        models_dir (str): Directory containing model specifications
        decision_trees_dir (str): Directory containing decision tree specifications
        pipelines_dir (str): Directory containing pipeline specifications
        loaded_specs (Dict[str, Dict[str, Any]]): Cached loaded specifications
    """
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        decision_trees_dir: Optional[str] = None,
        pipelines_dir: Optional[str] = None
    ):
        """
        Initialize the specification interpreter.
        
        Args:
            models_dir: Directory containing model specifications
            decision_trees_dir: Directory containing decision tree specifications
            pipelines_dir: Directory containing pipeline specifications
        """
        self.logger = logging.getLogger("spec_interpreter")
        
        # Set directories, using settings as defaults
        self.models_dir = models_dir or get_value("model.specs_dir", "specs/models")
        self.decision_trees_dir = decision_trees_dir or get_value(
            "model.decision_tree_specs_dir", "specs/decision_trees"
        )
        self.pipelines_dir = pipelines_dir or get_value("pipeline.specs_dir", "specs/pipelines")
        
        # Initialize cache for loaded specifications
        self.loaded_specs: Dict[str, Dict[str, Any]] = {
            "models": {},
            "decision_trees": {},
            "pipelines": {}
        }
    
    def load_model_spec(self, model_name: str) -> Dict[str, Any]:
        """
        Load a model specification.
        
        Args:
            model_name: Name of the model specification
            
        Returns:
            Dict[str, Any]: Loaded model specification
            
        Raises:
            FileNotFoundError: If the specification does not exist
            ValueError: If the specification is invalid
        """
        # Check cache first
        if model_name in self.loaded_specs["models"]:
            return self.loaded_specs["models"][model_name]
        
        # Construct path
        model_path = self._get_spec_path(self.models_dir, model_name)
        
        # Load the specification
        spec = self._load_spec_file(model_path)
        
        # Validate model specification
        self._validate_model_spec(spec)
        
        # Cache the specification
        self.loaded_specs["models"][model_name] = spec
        
        return spec
    
    def load_decision_tree_spec(self, tree_name: str) -> Dict[str, Any]:
        """
        Load a decision tree specification.
        
        Args:
            tree_name: Name of the decision tree specification
            
        Returns:
            Dict[str, Any]: Loaded decision tree specification
            
        Raises:
            FileNotFoundError: If the specification does not exist
            ValueError: If the specification is invalid
        """
        # Check cache first
        if tree_name in self.loaded_specs["decision_trees"]:
            return self.loaded_specs["decision_trees"][tree_name]
        
        # Construct path
        tree_path = self._get_spec_path(self.decision_trees_dir, tree_name)
        
        # Load the specification
        spec = self._load_spec_file(tree_path)
        
        # Validate decision tree specification
        self._validate_decision_tree_spec(spec)
        
        # Cache the specification
        self.loaded_specs["decision_trees"][tree_name] = spec
        
        return spec
    
    def load_pipeline_spec(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Load a pipeline specification.
        
        Args:
            pipeline_name: Name of the pipeline specification
            
        Returns:
            Dict[str, Any]: Loaded pipeline specification
            
        Raises:
            FileNotFoundError: If the specification does not exist
            ValueError: If the specification is invalid
        """
        # Check cache first
        if pipeline_name in self.loaded_specs["pipelines"]:
            return self.loaded_specs["pipelines"][pipeline_name]
        
        # Construct path
        pipeline_path = self._get_spec_path(self.pipelines_dir, pipeline_name)
        
        # Load the specification
        spec = self._load_spec_file(pipeline_path)
        
        # Validate pipeline specification
        self._validate_pipeline_spec(spec)
        
        # Cache the specification
        self.loaded_specs["pipelines"][pipeline_name] = spec
        
        return spec
    
    def interpret_model_spec(self, model_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a model specification.
        
        This method converts a declarative model specification into a
        configuration that can be used by components.
        
        Args:
            model_spec: Model specification to interpret
            
        Returns:
            Dict[str, Any]: Interpreted model configuration
        """
        # This is a placeholder implementation. In a real implementation,
        # this would interpret the model specification based on its type.
        
        model_type = model_spec.get("type")
        
        if model_type == "sklearn":
            return self._interpret_sklearn_model(model_spec)
        elif model_type == "text_processor":
            return self._interpret_text_processor(model_spec)
        elif model_type == "feature_extractor":
            return self._interpret_feature_extractor(model_spec)
        else:
            # Default interpretation: pass through the model specification
            return model_spec
    
    def interpret_decision_tree_spec(
        self, 
        tree_spec: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """
        Interpret a decision tree specification for a given context.
        
        This method evaluates a decision tree specification against a context
        to determine the appropriate strategy or action.
        
        Args:
            tree_spec: Decision tree specification to interpret
            context: Context to evaluate against
            
        Returns:
            str: The selected strategy or action
        """
        # Verify that the tree has a root node
        if "root" not in tree_spec:
            raise ValueError("Invalid decision tree: missing root node")
        
        # Start from the root node
        current_node = tree_spec["root"]
        
        # Traverse the tree
        while True:
            # If the node has a type, it's an evaluation node
            if "type" in current_node:
                node_type = current_node["type"]
                
                if node_type == "condition":
                    # Evaluate the condition
                    condition_result = self._evaluate_condition(current_node, context)
                    
                    # Follow the appropriate branch
                    if condition_result:
                        current_node = current_node.get("then", {})
                    else:
                        current_node = current_node.get("else", {})
                        
                elif node_type == "switch":
                    # Evaluate the expression
                    expression_result = self._evaluate_expression(current_node.get("expression", ""), context)
                    
                    # Follow the matching case or default
                    cases = current_node.get("cases", {})
                    if expression_result in cases:
                        current_node = cases[expression_result]
                    else:
                        current_node = current_node.get("default", {})
                        
                else:
                    # Unknown node type
                    raise ValueError(f"Unknown decision tree node type: {node_type}")
                    
            # If the node has a result, we've reached a leaf node
            elif "result" in current_node:
                return current_node["result"]
                
            # Neither a type nor a result, invalid node
            else:
                raise ValueError("Invalid decision tree node: missing type or result")
    
    def interpret_pipeline_spec(self, pipeline_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a pipeline specification.
        
        This method converts a declarative pipeline specification into a
        configuration that can be used to create a pipeline.
        
        Args:
            pipeline_spec: Pipeline specification to interpret
            
        Returns:
            Dict[str, Any]: Interpreted pipeline configuration
        """
        # This is a placeholder implementation. In a real implementation,
        # this would resolve component references, load external models, etc.
        
        # Copy the pipeline specification
        interpreted_spec = pipeline_spec.copy()
        
        # Process components
        if "components" in interpreted_spec:
            interpreted_components = []
            
            for component in interpreted_spec["components"]:
                # Interpret the component based on its type
                interpreted_component = self._interpret_component(component)
                interpreted_components.append(interpreted_component)
                
            interpreted_spec["components"] = interpreted_components
        
        return interpreted_spec
    
    def _get_spec_path(self, base_dir: str, spec_name: str) -> Path:
        """
        Get the path to a specification file.
        
        Args:
            base_dir: Base directory for specifications
            spec_name: Name of the specification
            
        Returns:
            Path: Path to the specification file
            
        Raises:
            FileNotFoundError: If the specification does not exist
        """
        # Check if the name includes a file extension
        if not spec_name.endswith((".yaml", ".yml", ".json")):
            # Try YAML first, then JSON
            yaml_path = Path(base_dir) / f"{spec_name}.yaml"
            yml_path = Path(base_dir) / f"{spec_name}.yml"
            json_path = Path(base_dir) / f"{spec_name}.json"
            
            if yaml_path.exists():
                return yaml_path
            elif yml_path.exists():
                return yml_path
            elif json_path.exists():
                return json_path
            else:
                raise FileNotFoundError(
                    f"Specification not found: {spec_name} (tried {yaml_path}, {yml_path}, {json_path})"
                )
        else:
            # Use the provided file extension
            path = Path(base_dir) / spec_name
            
            if not path.exists():
                raise FileNotFoundError(f"Specification not found: {path}")
                
            return path
    
    def _load_spec_file(self, path: Path) -> Dict[str, Any]:
        """
        Load a specification file.
        
        Args:
            path: Path to the specification file
            
        Returns:
            Dict[str, Any]: Loaded specification
            
        Raises:
            ValueError: If the file is not valid YAML or JSON
        """
        try:
            with open(path, "r") as f:
                if path.suffix in (".yaml", ".yml"):
                    spec = yaml.safe_load(f)
                elif path.suffix == ".json":
                    spec = json.load(f)
                else:
                    raise ValueError(f"Unsupported file extension: {path.suffix}")
                    
            if not isinstance(spec, dict):
                raise ValueError(f"Invalid specification: {path} (not a dictionary)")
                
            return spec
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Error parsing specification {path}: {str(e)}")
    
    def _validate_model_spec(self, spec: Dict[str, Any]) -> None:
        """
        Validate a model specification.
        
        Args:
            spec: Model specification to validate
            
        Raises:
            ValueError: If the specification is invalid
        """
        # Verify that the specification has a type
        if "type" not in spec:
            raise ValueError("Invalid model specification: missing type")
        
        # Different validation based on model type
        model_type = spec["type"]
        
        if model_type == "sklearn":
            if "algorithm" not in spec:
                raise ValueError("Invalid sklearn model specification: missing algorithm")
                
        elif model_type == "text_processor":
            if "processors" not in spec:
                raise ValueError("Invalid text processor specification: missing processors")
                
        elif model_type == "feature_extractor":
            if "features" not in spec:
                raise ValueError("Invalid feature extractor specification: missing features")
                
        # Add more model type validations as needed
    
    def _validate_decision_tree_spec(self, spec: Dict[str, Any]) -> None:
        """
        Validate a decision tree specification.
        
        Args:
            spec: Decision tree specification to validate
            
        Raises:
            ValueError: If the specification is invalid
        """
        # Verify that the specification has a root node
        if "root" not in spec:
            raise ValueError("Invalid decision tree specification: missing root node")
        
        # Validate the root node
        self._validate_decision_tree_node(spec["root"])
    
    def _validate_decision_tree_node(self, node: Dict[str, Any]) -> None:
        """
        Validate a decision tree node.
        
        Args:
            node: Decision tree node to validate
            
        Raises:
            ValueError: If the node is invalid
        """
        # A node must have either a type or a result
        if "type" not in node and "result" not in node:
            raise ValueError("Invalid decision tree node: missing type or result")
        
        # If the node has a type, validate based on the type
        if "type" in node:
            node_type = node["type"]
            
            if node_type == "condition":
                if "condition" not in node:
                    raise ValueError("Invalid condition node: missing condition")
                    
                if "then" not in node:
                    raise ValueError("Invalid condition node: missing then branch")
                    
                if "else" not in node:
                    raise ValueError("Invalid condition node: missing else branch")
                    
                # Recursively validate child nodes
                self._validate_decision_tree_node(node["then"])
                self._validate_decision_tree_node(node["else"])
                
            elif node_type == "switch":
                if "expression" not in node:
                    raise ValueError("Invalid switch node: missing expression")
                    
                if "cases" not in node or not isinstance(node["cases"], dict):
                    raise ValueError("Invalid switch node: missing or invalid cases")
                    
                # Recursively validate case nodes
                for case, case_node in node["cases"].items():
                    self._validate_decision_tree_node(case_node)
                    
                # Validate default case if present
                if "default" in node:
                    self._validate_decision_tree_node(node["default"])
            
            else:
                raise ValueError(f"Unknown decision tree node type: {node_type}")
    
    def _validate_pipeline_spec(self, spec: Dict[str, Any]) -> None:
        """
        Validate a pipeline specification.
        
        Args:
            spec: Pipeline specification to validate
            
        Raises:
            ValueError: If the specification is invalid
        """
        # Verify that the specification has an ID and name
        if "id" not in spec:
            raise ValueError("Invalid pipeline specification: missing id")
            
        if "name" not in spec:
            raise ValueError("Invalid pipeline specification: missing name")
            
        # Verify that the specification has components
        if "components" not in spec or not isinstance(spec["components"], list):
            raise ValueError("Invalid pipeline specification: missing or invalid components")
            
        # Validate each component
        for i, component in enumerate(spec["components"]):
            if "type" not in component:
                raise ValueError(f"Invalid pipeline component {i}: missing type")
                
            if "name" not in component:
                raise ValueError(f"Invalid pipeline component {i}: missing name")
    
    def _interpret_sklearn_model(self, model_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a scikit-learn model specification.
        
        Args:
            model_spec: Model specification to interpret
            
        Returns:
            Dict[str, Any]: Interpreted model configuration
        """
        # Extract model parameters
        algorithm = model_spec.get("algorithm")
        hyperparameters = model_spec.get("hyperparameters", {})
        
        # Build model configuration
        config = {
            "algorithm": algorithm,
            "hyperparameters": hyperparameters,
            "implementation": "sklearn"
        }
        
        # Add feature scaling if specified
        if "scaling" in model_spec:
            config["scaling"] = model_spec["scaling"]
        
        return config
    
    def _interpret_text_processor(self, model_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a text processor specification.
        
        Args:
            model_spec: Model specification to interpret
            
        Returns:
            Dict[str, Any]: Interpreted model configuration
        """
        # Extract processors
        processors = model_spec.get("processors", [])
        
        # Build processor configurations
        processor_configs = []
        for processor in processors:
            processor_type = processor.get("type")
            processor_config = processor.get("config", {})
            
            processor_configs.append({
                "type": processor_type,
                "config": processor_config
            })
        
        return {
            "processors": processor_configs,
            "language": model_spec.get("language", "en"),
            "implementation": "text_processor"
        }
    
    def _interpret_feature_extractor(self, model_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a feature extractor specification.
        
        Args:
            model_spec: Model specification to interpret
            
        Returns:
            Dict[str, Any]: Interpreted model configuration
        """
        # Extract features
        features = model_spec.get("features", [])
        
        # Build feature configurations
        feature_configs = []
        for feature in features:
            feature_type = feature.get("type")
            feature_source = feature.get("source")
            feature_name = feature.get("name")
            feature_config = feature.get("config", {})
            
            feature_configs.append({
                "type": feature_type,
                "source": feature_source,
                "name": feature_name,
                "config": feature_config
            })
        
        return {
            "features": feature_configs,
            "implementation": "feature_extractor"
        }
    
    def _interpret_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a pipeline component.
        
        Args:
            component: Component specification to interpret
            
        Returns:
            Dict[str, Any]: Interpreted component configuration
        """
        # Copy the component specification
        interpreted_component = component.copy()
        
        # If the component references a model, load and interpret it
        if "model" in component:
            model_name = component["model"]
            try:
                model_spec = self.load_model_spec(model_name)
                interpreted_model = self.interpret_model_spec(model_spec)
                interpreted_component["model_config"] = interpreted_model
            except (FileNotFoundError, ValueError) as e:
                self.logger.warning(f"Error loading model {model_name}: {str(e)}")
        
        # If the component references a decision tree, load it
        if "decision_tree" in component:
            tree_name = component["decision_tree"]
            try:
                tree_spec = self.load_decision_tree_spec(tree_name)
                interpreted_component["decision_tree_spec"] = tree_spec
            except (FileNotFoundError, ValueError) as e:
                self.logger.warning(f"Error loading decision tree {tree_name}: {str(e)}")
        
        return interpreted_component
    
    def _evaluate_condition(self, node: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition node against a context.
        
        Args:
            node: Condition node to evaluate
            context: Context to evaluate against
            
        Returns:
            bool: Result of the condition
        """
        # Simple placeholder implementation for condition evaluation
        condition = node.get("condition", "")
        
        # In a real implementation, this would interpret complex conditions
        # For now, just handle a few simple cases
        
        # Check for field existence
        if condition.startswith("exists:"):
            field = condition[7:].strip()
            return self._get_value_from_context(field, context) is not None
            
        # Check for field emptiness
        if condition.startswith("empty:"):
            field = condition[6:].strip()
            value = self._get_value_from_context(field, context)
            
            if value is None:
                return True
                
            if isinstance(value, (list, dict, str)):
                return len(value) == 0
                
            return False
            
        # Check for equal comparison
        if "==" in condition:
            field, value_str = condition.split("==", 1)
            field = field.strip()
            value_str = value_str.strip()
            
            actual_value = self._get_value_from_context(field, context)
            expected_value = self._parse_value(value_str)
            
            return actual_value == expected_value
        
        # Unknown condition
        self.logger.warning(f"Unknown condition: {condition}")
        return False
    
    def _evaluate_expression(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        Evaluate an expression against a context.
        
        Args:
            expression: Expression to evaluate
            context: Context to evaluate against
            
        Returns:
            Any: Result of the expression
        """
        # Simple placeholder implementation for expression evaluation
        # In a real implementation, this would interpret complex expressions
        
        # Check if the expression is a context field reference
        if expression.startswith("context."):
            field = expression[8:].strip()
            return self._get_value_from_context(field, context)
        
        # Check if the expression is a literal value
        try:
            return self._parse_value(expression)
        except ValueError:
            pass
        
        # Unknown expression
        self.logger.warning(f"Unknown expression: {expression}")
        return None
    
    def _get_value_from_context(self, field: str, context: Dict[str, Any]) -> Any:
        """
        Get a value from a context by field path.
        
        Args:
            field: Field path (dot notation)
            context: Context to get value from
            
        Returns:
            Any: The field value, or None if not found
        """
        parts = field.split(".")
        current = context
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _parse_value(self, value_str: str) -> Any:
        """
        Parse a value string to the appropriate type.
        
        Args:
            value_str: Value string to parse
            
        Returns:
            Any: The parsed value
            
        Raises:
            ValueError: If the value cannot be parsed
        """
        # Check for boolean values
        if value_str.lower() in ["true", "yes", "y"]:
            return True
            
        if value_str.lower() in ["false", "no", "n"]:
            return False
        
        # Check for null value
        if value_str.lower() in ["null", "none"]:
            return None
        
        # Check for integer values
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Check for float values
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Check for string literals
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            return value_str[1:-1]
        
        # Unquoted string
        return value_str


# Create a singleton instance
spec_interpreter = SpecInterpreter()

def get_interpreter() -> SpecInterpreter:
    """
    Get the specification interpreter instance.
    
    Returns:
        SpecInterpreter: The specification interpreter instance
    """
    return spec_interpreter 