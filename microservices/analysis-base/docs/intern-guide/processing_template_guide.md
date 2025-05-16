# Processing Template Guide

## What is a Processing Template?

A processing template is a YAML/JSON specification that defines a sequence of generic components to execute in order to perform a specific type of analysis. It's essentially a workflow definition that determines:

- Which components to use
- The sequence of execution
- Basic configuration for each component
- References to decision trees that provide specific analytical logic

## What Goes in a Processing Template?

Processing templates should ONLY include:

✅ Sequences of **generic** components  
✅ Basic configuration parameters  
✅ References to decision trees (dynamically loaded based on context)  
✅ Error handling and timeout settings  
✅ Basic flow control  

Processing templates should NEVER include:

❌ Platform-specific logic (Instagram, Etsy, etc.)  
❌ Domain-specific business rules  
❌ Complex analytical strategies  
❌ Hard-coded thresholds or classification rules  

## Template Structure

A processing template has this basic structure:

```yaml
name: "template_name"
description: "Description of what the template does"
version: "1.0"
components:
  - name: "component_1"
    type: "component_type"
    config:
      param1: value1
      param2: value2
  
  - name: "component_2"
    type: "component_type"
    config:
      param1: value1
      decision_tree: "{context.platform}_analysis_tree"
  
  # Additional components...
```

## Available Component Types

These are the primary component types you can use in your templates:

1. **collector**: Retrieves data from sources (database, API, etc.)
   ```yaml
   - name: "data_collector"
     type: "collector"
     config:
       operation: "collect_metrics"
       include_historical: true
       timeout: 30
   ```

2. **feature_extractor**: Extracts features from raw data
   ```yaml
   - name: "feature_extractor"
     type: "feature_extractor"
     config:
       extract_visual_features: true
       extract_textual_features: true
   ```

3. **analyzer**: Performs analysis operations
   ```yaml
   - name: "performance_analyzer"
     type: "analyzer"
     config:
       operation: "analyze_batch_performance"
       decision_tree: "{context.platform}_performance_analysis"
   ```

4. **transformer**: Transforms data or results
   ```yaml
   - name: "results_formatter"
     type: "transformer"
     config:
       format: "diagnostic_summary"
       include_visualizations: true
   ```

5. **storage**: Persists results
   ```yaml
   - name: "results_persister"
     type: "storage"
     config:
       destination: "database_layer"
       store_raw_data: false
   ```

## Using Dynamic References

Templates should use dynamic references wherever possible to make them reusable across domains:

```yaml
decision_tree: "{context.platform}_performance_analysis"
```

This will load different trees based on the platform in the context (e.g., "instagram_performance_analysis" for Instagram).

## Example Templates

### Example 1: Standard Descriptive Analysis Template

```yaml
name: "standard_descriptive_analysis"
description: "General-purpose descriptive analysis for any entity type"
version: "1.0"
components:
  - name: "data_collector"
    type: "collector"
    config:
      operation: "collect_metrics"
      include_historical: false
      timeout: 30
  
  - name: "feature_extractor"
    type: "feature_extractor"
    config:
      extract_visual_features: true
      extract_textual_features: true
      extract_metrics: true
  
  - name: "performance_analyzer"
    type: "analyzer"
    config:
      operation: "analyze_performance"
      decision_tree: "{context.platform}_performance_analysis"
      calculate_statistics: true
  
  - name: "results_formatter"
    type: "transformer"
    config:
      format: "descriptive_summary"
      include_visualizations: true
  
  - name: "results_persister"
    type: "storage"
    config:
      destination: "database_layer"
      store_raw_data: false
```

### Example 2: Inter-Batch Comparison Analysis Template

```yaml
name: "inter_batch_comparison_analysis"
description: "Compares performance across multiple batches"
version: "1.0"
components:
  - name: "multi_batch_collector"
    type: "collector"
    config:
      operation: "collect_batch_metrics"
      batch_count: 5  # Collect data from 5 most recent batches
      timeout: 45
  
  - name: "batch_feature_extractor"
    type: "feature_extractor"
    config:
      extract_batch_level_features: true
      normalize_metrics: true
  
  - name: "comparative_analyzer"
    type: "analyzer"
    config:
      operation: "compare_batches"
      decision_tree: "{context.platform}_batch_comparison"
      focus_metrics: ["engagement_rate", "conversion_rate"]
  
  - name: "trend_analyzer"
    type: "analyzer"
    config:
      operation: "analyze_trends"
      decision_tree: "{context.platform}_trend_analysis"
      time_window: "6_months"
  
  - name: "comparison_results_formatter"
    type: "transformer"
    config:
      format: "comparative_summary"
      include_trend_visualization: true
  
  - name: "results_persister"
    type: "storage"
    config:
      destination: "database_layer"
      store_raw_data: false
```

### Example 3: Category Analysis Template

```yaml
name: "factor_category_analysis"
description: "Analyzes factor categories as entities themselves"
version: "1.0"
components:
  - name: "factor_data_collector"
    type: "collector"
    config:
      operation: "collect_factor_data"
      include_usage_history: true
      include_performance_data: true
      timeout: 30
  
  - name: "factor_feature_extractor"
    type: "feature_extractor"
    config:
      extract_temporal_features: true
      extract_usage_patterns: true
  
  - name: "factor_analyzer"
    type: "analyzer"
    config:
      operation: "analyze_factor_performance"
      decision_tree: "{context.platform}_factor_category_analysis"
      calculate_decay_rate: true
  
  - name: "saturation_analyzer"
    type: "analyzer"
    config:
      operation: "analyze_saturation"
      decision_tree: "factor_saturation_analysis"
      time_window: "12_months"
  
  - name: "factor_results_formatter"
    type: "transformer"
    config:
      format: "factor_summary"
      include_effectiveness_timeline: true
  
  - name: "results_persister"
    type: "storage"
    config:
      destination: "database_layer"
      store_raw_data: false
```

## Best Practices

1. **Keep Templates Generic**: Templates should be reusable across different platforms and domains.

2. **Use Dynamic References**: Use context variables to dynamically reference decision trees.

3. **Provide Clear Component Sequences**: Order components in a logical flow from data collection to result storage.

4. **Limit Component Count**: Keep templates focused with 5-7 components for maintainability.

5. **Use Descriptive Names**: Name components and parameters clearly to indicate their purpose.

6. **Include Timeout Settings**: Always specify timeouts for components that interact with external systems.

7. **Document Intent**: Include clear descriptions of what the template is meant to accomplish.

## Template Validation

Before submitting your template, check that it:

- Contains no platform-specific logic
- Uses only generic components
- Has dynamic references for decision trees
- Includes all necessary components for the purpose
- Follows naming conventions
- Has appropriate timeout and error handling settings

## Next Steps

After creating your processing template, you'll need to create corresponding decision trees that provide the domain-specific logic. See the [Decision Tree Guide](./decision_tree_guide.md) for details. 