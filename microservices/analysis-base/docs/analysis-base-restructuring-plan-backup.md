# Analysis-Base Restructuring Plan

## Current Analysis

### Key Insights from Current Implementation
Despite the issues, there are valuable aspects of the current implementation:

1. The service handles four types of analysis (descriptive, diagnostic, predictive, prescriptive)
2. Each analysis type has different processing requirements and output formats
3. The service already integrates with the database-layer microservice for category repository functionality
4. There are established patterns for retrieving insights from previous analyses
5. The analysis pipeline has multiple stages (process, analyze, store results)

## Current Implementation Details

### Data Ingestion and Pre-Processing

The data ingestion module in the analysis-base microservice follows a three-step pipeline:

#### 1. Data Collection (`data_pipeline.py`)

- The `DataIngestion` class is responsible for fetching raw data from various sources
- It accepts a `query` and optional `filters` to retrieve specific data
- The class acts as an entry point to the data processing pipeline
- This component is designed to interface with external data sources like databases and APIs
- Currently implemented as a placeholder with simulated data retrieval

```python
async def fetch_data(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetch data from the specified source.
    
    Args:
        query: Query string to execute
        filters: Optional filters to apply
        
    Returns:
        Retrieved data
    """
    # Fetch data, then forward to preprocessing pipeline
    # ...
    from .data_transformer import Preprocessing
    preprocessing = Preprocessing()
    processed_data = await preprocessing.preprocess_data(data)
    
    return processed_data
```

#### 2. Data Transformation (`data_transformer.py`)

- The `Preprocessing` class handles data cleaning and transformation 
- Its `preprocess_data()` method prepares raw data for further analysis
- It applies cleaning and normalization steps to ensure data quality
- The `transform_data()` method applies feature engineering and scaling
- Metadata is tracked at each step to maintain a processing history
- This component acts as the middle layer in the pipeline

#### 3. Feature Extraction (`feature_extraction.py`)

- The `FeatureExtraction` class extracts meaningful features from preprocessed data
- It identifies key factors through the `extract_factors()` method
- It computes feature scores with the `compute_feature_scores()` method
- The `tag_unlabeled_data()` method assigns tags based on extracted features
- It integrates with the CategoryRepository from the database layer to retrieve tagging categories
- This is the final step in the pre-processing pipeline before analysis

### Worker Processing

After data pre-processing, the analysis-base microservice has various worker modules that perform different types of analysis:

#### 1. Descriptive Analysis (`descriptive_worker.py`)

- The `DescriptiveWorker` calculates performance metrics and scores
- It processes data according to template instructions
- Analysis targets can include factors, batches, and users
- Major functions include:
  - `score_factors()`: Calculates metrics and scores for different factors
  - `score_batches()`: Analyzes performance of content batches
  - `score_users()`: Evaluates user-level metrics
  - `generate_summary()`: Creates summary statistics
  - `generate_tags()`: Assigns tags based on analysis results

#### 2. Diagnostic Analysis (`diagnostic_worker.py`)

- The `DiagnosticWorker` identifies root causes, strengths, and weaknesses
- It builds on descriptive analysis results to provide deeper insights
- Key functions include:
  - `diagnose_factors()`: Identifies why factors perform as they do (by editing their metadata?)
  - `calculate_feature_importance()`: Determines which features matter most (by giving them weights?)
  - `identify_strengths_weaknesses()`: Highlights positive and negative aspects 
  - `identify_anomalies()`: Detects unusual patterns in the data
  - `identify_root_causes()`: Determines causal relationships

#### 3. Processing Chain

- Workers are orchestrated by the processing engine
- The pipeline framework allows components to be combined flexibly
- Results from descriptive analysis feed into diagnostic analysis
- This creates a staged approach to increasingly deeper insights

### Core System Components

#### Processing Engine (`processing_engine.py`)

- Creates pipelines based on context configuration
- Manages the execution of pipelines
- Handles errors and provides meaningful error messages
- Collects and reports processing metrics

#### Pipeline and PipelineFactory (`pipeline.py`)

- Executes sequences of components in defined order
- Creates pipelines based on configuration or context type
- Manages the flow of data between components
- Collects metrics on pipeline execution

#### Worker Service (`worker_service.py`)

- Main orchestrator for processing tasks
- Polls for pending contexts, marks them as "processing"
- Handles retries and error conditions
- Updates context statuses and results after processing

### Output Generation

The analysis-base microservice generates several types of outputs:

1. **Metric Computation**
   - Each worker calculates specific metrics relevant to its analysis type
   - Descriptive workers compute performance metrics like means, medians, and standard deviations
   - Diagnostic workers generate insights about causality and importance

2. **Scoring Systems**
   - Workers assign scores to various entities (factors, batches, users)
   - Scores are normalized and stored for comparison
   - Overall scores summarize performance across multiple metrics

3. **Insight Generation**
   - Diagnostic workers identify strengths, weaknesses, and root causes
   - Feature importance scores highlight which factors matter most
   - Anomaly detection finds unusual patterns that require attention

4. **Tag Assignment**
   - Both workers generate tags based on analysis results
   - Tags provide a simplified way to categorize entities
   - They integrate with the category repository for standardization

5. **Data Storage**
   - Results are stored in repositories for future reference
   - The `store_results()` method saves complete analysis results
   - Individual entities are stored with their associated metrics and scores
   - This creates a historical record of analysis for trending and comparison

## New Structure

Based on the generative-base architecture and learnings from the current implementation, we propose the following structure:

```
microservices/analysis-base/
├── Dockerfile
├── requirements.txt
├── analysis_main.py              # Main entry point (renamed from analyse_main.py)
├── docs/                         # Documentation
├── tests/                        # Test suite
├── specs/                        # Declarative specifications directory
│   ├── models/                   # ML model specifications (for ML experts)
│   ├── decision_trees/           # Analysis decision tree configurations
│   ├── pipelines/                # Pipeline configurations
│   └── api_contracts/            # API contract definitions
└── src/
    ├── api/                      # API endpoints 
    │   ├── __init__.py
    │   ├── router.py             # FastAPI router
    │   └── schemas.py            # API schemas
    ├── common/                   # Shared utilities
    │   ├── __init__.py
    │   ├── logging.py
    │   └── utils.py
    ├── config/                   # Configuration
    │   ├── __init__.py
    │   ├── settings.py
    │   └── config_loader.py      # Enhanced configuration loader
    ├── repository/               # Data access layer
    │   ├── __init__.py
    │   ├── base_repository.py
    │   ├── context_repository.py
    │   └── results_repository.py
    ├── service/                  # Core services
    │   ├── __init__.py
    │   ├── worker_service.py     # Worker service to process analysis jobs
    │   └── health_service.py     # Health check service
    ├── processing/               # Processing infrastructure
    │   ├── __init__.py
    │   ├── pipeline.py           # Analysis pipeline management
    │   ├── pipeline_executor.py  # Pipeline execution
    │   ├── processor.py          # Core processor
    │   ├── context_poller.py     # Context polling
    │   ├── component_registry.py # Enhanced component registry
    │   ├── spec_interpreter.py   # Specification interpreter
    │   └── components/           # Base components
    │       ├── __init__.py
    │       ├── base.py           # Enhanced base component class
    │       └── contracts/        # Component contracts
    │           ├── __init__.py
    │           └── base_contracts.py  # Base contract definitions
    ├── clients/                  # Client interfaces to other services
    │   ├── __init__.py
    │   └── database_layer_client.py  # Client for database-layer interactions
    └── modules/                  # Analysis modules
        ├── __init__.py
        ├── data_ingestion/       # Data ingestion module (refactored)
        │   ├── __init__.py
        │   ├── components/       # Module-specific components
        │   │   ├── __init__.py
        │   │   ├── data_collector.py
        │   │   ├── data_transformer.py
        │   │   └── feature_extractor.py
        │   └── helpers/
        │       ├── __init__.py
        │       └── ingestion_utils.py
        ├── descriptive_module/   # Descriptive analysis module
        │   ├── __init__.py
        │   ├── components/       # Module-specific components
        │   │   ├── __init__.py
        │   │   ├── data_summarizer.py
        │   │   ├── trend_analyzer.py
        │   │   ├── factor_analyzer.py
        │   │   ├── batch_analyzer.py
        │   │   └── user_analyzer.py
        │   └── helpers/          # Module-specific helpers
        │       ├── __init__.py
        │       └── data_processor.py
        ├── diagnostic_module/    # Diagnostic analysis module
        │   ├── __init__.py
        │   ├── components/
        │   │   ├── __init__.py
        │   │   ├── root_cause_analyzer.py
        │   │   ├── correlation_detector.py
        │   │   ├── factor_analyzer.py
        │   │   ├── anomaly_detector.py
        │   │   └── strength_weakness_analyzer.py
        │   └── helpers/
        │       ├── __init__.py
        │       └── diagnosis_utils.py
        ├── predictive_module/    # Predictive analysis module
        │   ├── __init__.py
        │   ├── components/
        │   │   ├── __init__.py
        │   │   ├── forecaster.py
        │   │   ├── trend_predictor.py
        │   │   └── anomaly_detector.py
        │   └── helpers/
        │       ├── __init__.py
        │       └── prediction_utils.py
        └── prescriptive_module/  # Prescriptive analysis module
            ├── __init__.py
            ├── components/
            │   ├── __init__.py
            │   ├── recommendation_generator.py
            │   ├── strategy_optimizer.py
            │   └── impact_analyzer.py
            └── helpers/
                ├── __init__.py
                └── prescription_utils.py
```

## Key Changes from Current Structure

1. **Modular Decomposition**:
   - Break down monolithic worker files into smaller, focused components
   - Example: `descriptive_worker.py` → `factor_analyzer.py`, `batch_analyzer.py`, `user_analyzer.py`

2. **Consistent Module Structure**:
   - Each analysis type (descriptive, diagnostic, predictive, prescriptive) follows the same structure
   - Common components go in the `processing/components` directory
   - Module-specific components go in their respective module directories

3. **Data Ingestion Refactoring**:
   - Move data ingestion to a dedicated module with components
   - Preserve the pipeline structure but make it more flexible and component-based

4. **Clear Dependency Management**:
   - Explicit client for database-layer interactions
   - Dependencies injected through component constructors
   - Reduced direct imports between modules

5. **Declarative Specification Support**:
   - New `specs` directory for ML experts to define models and configurations
   - Enhanced component registry that loads from specifications
   - Specification interpreter for translating declarative models into executable code

6. **Configuration-Driven Architecture**:
   - Enhanced base component that loads and applies configuration
   - Configuration-aware pipeline for dynamic execution paths
   - Decision trees defined in configuration rather than code

7. **Contract-Based Design**:
   - Explicit API contracts for component interfaces
   - Contract verification to ensure proper implementation
   - Stable interfaces that enable independent evolution of components

## Detailed Migration Strategy

Based on the proposed architecture, we've developed a comprehensive migration strategy that provides a structured approach for incrementally implementing the new design while minimizing disruption to ongoing operations.

### Phase 1: Foundation and Infrastructure (2-3 weeks)

1. **Create Base Directory Structure**
   ```bash
   mkdir -p microservices/analysis-base/{docs,tests,specs/{models,decision_trees,pipelines,api_contracts},src/{api,common,config,repository,service,processing,clients,modules}}
   ```

2. **Set Up Docker Environment**
   - Create updated Dockerfile and docker-compose.yml
   - Ensure all dependencies are properly captured
   - Configure environment variables for development and production

3. **Establish Scope Separation Documentation**
   - Create `docs/scope_separation_guide.md` documenting the clear separation between:
     - Processing modules (generic, reusable components)
     - Processing templates (workflow definitions)
     - Decision trees (domain-specific analytical logic)
   - Create intern guide documentation explaining how to work with each component
   - Develop validation criteria for each component type
   - **Document platform-specific analysis purposes** (Instagram, Etsy, campaigns)
   - **Create guidelines for individual vs. category processing separation**

4. **Implement Core Processing Infrastructure**
   - Create enhanced BaseComponent class with configuration loading
   - Implement component registry with specification support
   - Create base contracts for component interfaces
   - **Design component interfaces that support both individual and category processing**
   - **Create analysis context model with support for inter-batch, intra-batch, and historical analysis**
   - Implement pipeline mechanism supporting template-driven execution
     - Design pipeline to accept generic processing templates
     - Ensure component sequences are defined entirely by templates
     - Create dynamic template resolution mechanism
   - Implement pipeline executor with metrics tracking and error handling

5. **Implement Configuration and Specification Management**
   - Create configuration loader with environment variable support
   - **Implement platform detection and configuration adapters for Instagram, Etsy, etc.**
   - Implement specification interpreter for processing templates
     - Create template validation and loading logic
     - Implement dynamic component sequence creation from templates
   - Implement specification interpreter for decision trees
     - Create tree validation and loading logic
     - Implement context-based condition evaluation
     - Develop outcome resolution mechanism
     - **Create validators for platform-specific decision tree patterns**
   - Define schema validation for both templates and trees

### Phase 2: Repository and Client Layer (1-2 weeks)

1. **Implement Repository Abstractions**
   - Create base repository interface with common patterns
   - Implement context repository for analysis context data
   - Implement results repository for storage and retrieval of analysis results
   - **Design repository models for both individual and category objects**
   - Set up repository factory pattern for future extensibility

2. **Enhance Database Layer Client**
   - Update client to support new category repository requirements
   - Implement connections to external data sources
   - **Create specialized repository methods for factor, secret sauce, batch, and campaign categories**
   - Add support for category history and trending
   - Create client configuration and connection pooling

3. **Create API Schemas**
   - Define input and output schemas for all analysis types
   - **Create platform-specific request and response schemas**
   - **Design dual-mode schemas that support both individual and category analysis**
   - Create API contracts for external integration
   - Implement schema validation and transformation
   - Set up versioned API support

### Phase 2.5: Template and Decision Tree Foundation (1-2 weeks)

1. **Create Processing Template Structure**
   - Design the schema for processing templates
   - Implement template parser and validator
   - Create directory structure for template storage
   - Develop template selection logic in worker service
   - **Create base templates for each platform (Instagram, Etsy, campaigns)**
   - Create base templates for each analysis type:
     - Descriptive analysis template
     - Diagnostic analysis template
     - Predictive analysis template
     - Prescriptive analysis template

2. **Create Decision Tree Structure**
   - Design the schema for decision trees
   - Implement tree parser and condition evaluator
   - Create directory structure for tree storage
   - Develop dynamic tree loading based on context
   - **Create decision trees for selecting analysis approach (inter-batch, intra-batch, historical)**
   - Create base trees for platform-specific logic:
     - Instagram analysis trees
     - Etsy analysis trees
     - Campaign analysis trees
     - Strategy analysis trees

3. **Develop Component Functionality Interface**
   - Design interfaces between components and decision trees
   - Implement outcome interpretation mechanism
   - Create component configuration extraction from templates
   - Develop context enrichment patterns
   - **Create adapter interfaces for handling both individual and category objects**

4. **Create Intern Documentation**
   - Develop comprehensive guides for interns in `docs/intern-guide/`:
     - Processing template creation guide with examples
     - Decision tree authoring guide with examples
     - README with overview of the system architecture
     - **Platform-specific analysis documentation**
     - **Individual vs. category processing guidelines**
   - Create template examples for common analysis patterns
   - Include real-world decision tree examples for different platforms

### Phase 3: Data Ingestion Module Migration (1-2 weeks)

1. **Component Migration**
   - Convert DataIngestion class to DataCollectorComponent
   - Convert Preprocessing class to DataTransformerComponent
   - Convert FeatureExtraction class to FeatureExtractorComponent
   - Implement helper utilities for data ingestion
   - **Create platform-specific numerical transformers for Instagram, Etsy, and campaign data**
   - **Implement platform type indicators as numerical flags (is_instagram: 1.0, is_etsy: 0.0)**
   - **Implement category objects as standardized numerical feature vectors**

2. **User Insight Extension Repository Integration**
   - **Implement connections to platform-specific User Insight Extension repositories**
     - Create Instagram User Insight connector
     - Create Etsy User Insight connector
     - Create adapter interfaces for additional platforms
   - **Develop standardized data access patterns for user-level metrics**
     - Ensure all user-level metrics come exclusively from User Insight Extension repositories
     - Create abstraction layer to handle platform-specific user insight data formats
   - **Map platform-specific user metrics to standardized metric framework**
     - Transform platform-specific engagement metrics to standard format
     - Normalize user interaction patterns across platforms
   - **Implement user context processors for different platforms**
     - Create user history analyzers for each platform
     - Develop user preference extractors customized per platform
     - Build cross-platform user behavior correlation tools

3. **Create Numerical Transformation Layer**
   - **Implement platform-specific normalizers that convert raw metrics to standard 0-1 range**
   - **Create algorithms to transform all platform-specific metrics to standard metrics**
   - **Develop feature vector creation from normalized platform data**
   - **Ensure all platform-specific knowledge is encapsulated in data ingestion**
   - **Create validation tests for metric normalization across platforms**
   - **Implement feature extraction that produces consistent numerical features**
   - **Create unified transformers that merge category and user insight data**
     - Develop algorithms to correlate user insights with category performance
     - Create feature vectors that incorporate both category attributes and user behaviors
     - Implement normalization strategies for combined user-category metrics

4. **Create Component Specifications**
   - Define specifications for data pipeline components
   - Create configuration templates for different data sources
   - Implement transformation rule specifications
   - Define feature extraction specifications
   - **Create platform-specific numerical transformation rules**
   - **Design specifications for numerical feature extraction**
   - **Develop User Insight Extension integration specifications**
     - Define standard interfaces for all User Insight Extension repositories
     - Create platform-specific connector configurations
     - Document required data formats and access patterns

5. **Integration Testing**
   - Verify data pipeline still functions correctly
   - Compare outputs with existing implementation
   - Ensure backward compatibility with existing systems
   - Performance test with realistic data volumes
   - **Test with platform-specific data sources**
   - **Validate numerical transformation across platforms**
   - **Verify consistent feature vector format regardless of platform**
   - **Test User Insight Extension repository integrations for all platforms**
     - Validate data retrieval from Instagram User Insight Extension
     - Verify Etsy User Insight Extension connectivity
     - Test cross-platform user insight normalization
     - Benchmark user data retrieval performance

### Phase 4: Descriptive Analysis Module Migration (2 weeks)

1. **Decompose Descriptive Worker**
   - Create factor_analyzer, batch_analyzer, user_analyzer components
   - Implement data_summarizer and trend_analyzer components
   - Add category-specific analysis components
   - Implement helper utilities for descriptive analysis
   - **Create `ObjectPerformanceAnalyzer` for category-level analysis**
   - **Implement dual-mode analyzers for both individual items and category objects**
   - **Develop specialized components for inter-batch, intra-batch, and historical analysis**

2. **Create Configuration Templates**
   - Define decision trees for descriptive analysis
   - Create pipeline configurations for different analysis contexts
   - Implement scoring parameter specifications
   - Define output format templates
   - **Create platform-specific descriptive analysis templates for Instagram, Etsy, etc.**
   - **Design templates for category object analysis (factors, secret sauces, etc.)**

3. **Integration Testing**
   - Verify descriptive analysis produces correct results
   - Compare with existing implementation
   - Test with various input types and edge cases
   - Verify integration with database layer and repositories
   - **Test with platform-specific datasets**
   - **Validate both individual and category analysis outputs**

### Phase 5: Diagnostic Analysis Module Migration (2 weeks)

1. **Decompose Diagnostic Worker**
   - Create root_cause_analyzer, correlation_detector components
   - Implement anomaly_detector and strength_weakness_analyzer components
   - Add factor_analyzer specialized for diagnostic purposes
   - Create helper utilities for diagnostic analysis
   - **Implement `FactorEffectivenessModel` for analyzing factor performance trends**
   - **Create `SecretSauceContextAnalyzer` for creative pattern analysis**
   - **Develop `CampaignDiagnosticComponent` for campaign structure analysis**

2. **Create Configuration Templates**
   - Define decision trees for diagnostic analysis
   - Create pipeline configurations for different diagnostic contexts
   - Implement causal inference specifications
   - Define anomaly detection thresholds and rules
   - **Create platform-specific diagnostic decision trees**
   - **Design category-specific diagnostic templates**
   - **Implement analysis type-specific diagnostic approaches**

3. **Integration Testing**
   - Verify diagnostic analysis produces correct results
   - Compare with existing implementation
   - Test with complex diagnostic scenarios
   - Verify integration with descriptive analysis results
   - **Test with different platforms and analysis approaches**
   - **Validate integrated individual-category analysis flows**

### Phase 6: Predictive & Prescriptive Modules (2-3 weeks)

1. **Implement Predictive Module Components**
   - Create forecaster, trend_predictor, anomaly_detector components
   - Implement time series analysis utilities
   - Add ML model integration points
   - Develop prediction evaluation metrics
   - **Create `FactorLifecyclePredictorComponent` for factor effectiveness forecasting**
   - **Implement platform-specific prediction models for Instagram, Etsy, etc.**
   - **Design forecasting components for category objects and individual items**

2. **Implement Prescriptive Module Components**
   - Create recommendation_generator, strategy_optimizer, impact_analyzer components
   - Implement optimization algorithms
   - Develop recommendation engines
   - Create impact assessment tools
   - **Implement `CreativeStrategyOptimizer` for secret sauce recommendations**
   - **Create `CampaignOptimizationComponent` for campaign strategy suggestions**
   - **Develop platform-specific recommendation generators**

3. **Create Configuration Templates**
   - Define decision trees and pipeline configurations
   - Set up ML model specifications for predictive models
   - Create recommendation strategy templates
   - Define impact assessment criteria
   - **Create platform-specific recommendation decision trees**
   - **Implement analysis approach-specific prediction templates (inter-batch, intra-batch, historical)**

### Phase 7: API and Integration (1-2 weeks)

1. **Implement API Layer**
   - Create FastAPI router and endpoints
   - Implement request validation and error handling
   - Add authentication and authorization
   - Implement health check service
   - **Create endpoints for both individual and category-level analysis**
   - **Implement platform-specific API endpoints**

2. **Worker Service Implementation**
   - Update worker service to use new component architecture
   - Implement context poller and processor
   - Add monitoring and observability
   - Implement retry and error handling strategies
   - **Create specialized workers for different analysis approaches**
   - **Implement platform detection and routing logic**

3. **Final Integration**
   - Connect all components into cohesive system
   - Set up monitoring and logging
   - Configure deployment pipeline
   - Create comprehensive documentation
   - **Integrate all analysis approaches and platform-specific components**
   - **Ensure seamless individual and category processing**

### Phase 8: Testing and Validation (2 weeks)

1. **Comprehensive Testing**
   - Create unit tests for all components
   - Implement integration tests for each module
   - Develop system tests for end-to-end functionality
   - Set up continuous integration pipeline
   - **Create platform-specific test suites**
   - **Test individual and category processing flows**
   - **Validate all analysis approaches (inter-batch, intra-batch, historical)**

2. **Performance Testing**
   - Verify performance is equal or better than previous implementation
   - Test with large datasets
   - Identify and resolve bottlenecks
   - Implement performance monitoring
   - **Benchmark platform-specific analysis performance**
   - **Test category analysis performance with large datasets**

3. **Documentation**
   - Create comprehensive documentation for ML experts
   - Document component interfaces and specifications
   - Create user guides for configuration management
   - Document deployment and operations procedures
   - **Create detailed platform-specific analysis guides**
   - **Document individual vs. category processing patterns**
   - **Create decision tree authoring guides for each platform**

## Risk Mitigation Strategy

1. **Parallel Running Period**
   - Deploy new implementation alongside existing one
   - Compare outputs to ensure consistency
   - Switch traffic gradually from old to new implementation
   - Monitor error rates and performance metrics

2. **Rollback Plan**
   - Maintain old implementation until confident in new one
   - Create scripts to revert to old implementation if issues arise
   - Implement feature flags for individual components
   - Store dual results for critical analyses during transition

3. **Feature Flags**
   - Implement feature flags to enable/disable new functionality
   - Allow for gradual rollout of new capabilities
   - Support A/B testing of new components
   - Enable quick disabling of problematic features

## Timeline and Dependencies

Total estimated timeline: 12-16 weeks

Critical dependencies:
1. Core processing infrastructure must be completed before module migrations
2. Repository layer must be implemented before components can store results
3. Data ingestion module must be migrated before analysis modules
4. Descriptive analysis must be completed before diagnostic analysis

This phased approach allows for incremental implementation and validation, ensuring that each component is thoroughly tested before moving to the next phase. As each phase is completed, the corresponding sections of this document can be updated to reflect the actual implementation details, ensuring the documentation stays in sync with the codebase.

## Code Migration Examples

### Example 1: Enhanced Factor Analysis Component

**Current Implementation (descriptive_worker.py)**:
```python
async def score_factors(self, data: Dict[str, Any], scoring_params: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score factors based on performance metrics.
    
    Args:
        data: Data containing performance metrics
        scoring_params: Parameters for scoring
        template: Original template
        
    Returns:
        Dictionary of factor scores
    """
    # Large method with multiple responsibilities
    # ...
```

**New Implementation (descriptive_module/components/factor_analyzer.py)**:
```python
from src.processing.components.base import BaseComponent
from src.processing.components.contracts import AnalyzerContract

class FactorAnalyzerComponent(BaseComponent, AnalyzerContract):
    """
    Component for analyzing factors and calculating performance metrics.
    Implements the AnalyzerContract.
    """
    
    def validate_config(self) -> None:
        """Validate component configuration."""
        # Configuration validation
        # ...
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the context by analyzing factors.
        
        Args:
            context: The context to process
            
        Returns:
            Dict[str, Any]: The processed context with factor analysis results
        """
        # Load configuration and decision tree
        config = self.load_configuration()
        decision_strategy = self.apply_decision_tree(context)
        
        # Extract data and parameters from context
        data = context.get("data", {})
        scoring_params = config.get("scoring_params", {})
        
        # Apply the appropriate analysis strategy based on decision tree
        if decision_strategy == "intra_batch":
            results = await self._analyze_intra_batch(data, scoring_params)
        elif decision_strategy == "inter_batch":
            results = await self._analyze_inter_batch(data, scoring_params)
        elif decision_strategy == "historical":
            results = await self._analyze_historical(data, scoring_params)
        else:
            results = await self._analyze_default(data, scoring_params)
        
        # Add results to context
        return self.merge_results(context, results)
```

### Example 2: Specification-Driven Data Transformation Component

**Current Implementation (data_transformer.py)**:
```python
class Preprocessing:
    """
    Handles data preprocessing and transformation.
    """
    
    async def preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Preprocessing logic
        # ...
```

**New Implementation with Configuration Support (data_ingestion/components/data_transformer.py)**:
```python
from src.processing.components.base import BaseComponent
from src.processing.components.contracts import TransformerContract

class DataTransformerComponent(BaseComponent, TransformerContract):
    """
    Component for preprocessing and transforming raw data.
    Implements the TransformerContract.
    """
    
    def validate_config(self) -> None:
        """Validate component configuration."""
        # Configuration validation
        # ...
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the context by transforming data.
        
        Args:
            context: The context to process
            
        Returns:
            Dict[str, Any]: The processed context with transformed data
        """
        # Load transformation specification
        transformation_spec = self.load_model_specification("data_transformation")
        
        # Extract data from context
        data = context.get("data", {})
        
        # Apply transformations from specification
        processed_data = {}
        for field, transforms in transformation_spec.get("transforms", {}).items():
            if field in data:
                processed_data[field] = self._apply_transforms(data[field], transforms)
        
        # Add transformed data to context
        return self.merge_results(context, {"processed_data": processed_data})
        
    def _apply_transforms(self, data, transforms):
        """Apply transformations from specification to data."""
        result = data
        for transform in transforms:
            if transform["type"] == "normalize":
                result = self._normalize(result)
            elif transform["type"] == "scale":
                result = self._scale(result, transform.get("factor", 1.0))
            # Additional transformations as defined in the specification
        return result
```

## Key Learnings to Preserve

While restructuring, we must preserve these important aspects of the current implementation:

1. **Analysis Workflows**: Maintain the distinct analysis types and their workflows
2. **Domain Knowledge**: Preserve the business logic for each analysis type
3. **Data Models**: Keep the established data models for consistency
4. **Integration Points**: Maintain integration with other services, including the database-layer
5. **Repository Pattern**: Build on the established repository pattern

## Implementation Priorities

1. First priority: Core infrastructure (base component, registry, pipeline)
2. Second priority: Descriptive and diagnostic modules
3. Third priority: Predictive and prescriptive modules
4. Fourth priority: API and integration

## Areas for Improvement

1. **Production-Ready Data Ingestion**
   - Current data ingestion implementation is mostly placeholder code
   - Need to implement real connectors to data sources
   - Add support for more sophisticated query capabilities

2. **Enhanced Feature Extraction**
   - Expand feature extraction capabilities with ML techniques
   - Add support for automatic feature detection
   - Implement dimensionality reduction for high-dimensional data

3. **Performance Optimization**
   - Optimize batch processing capabilities for large datasets
   - Implement caching for frequently accessed data
   - Add distributed processing capabilities for horizontal scaling

4. **Advanced Analytics**
   - Add predictive analytics capabilities
   - Implement more sophisticated anomaly detection
   - Enhance causal analysis with advanced statistical methods

5. **Integration Improvements**
   - Tighter integration with other microservices
   - Real-time feedback loop with generative services
   - Enhanced security for data access and processing

## Advantages of New Structure

1. **Modularity**: Clear separation of concerns between analysis types
2. **Extensibility**: Easy to add new components within each module
3. **Testability**: Components can be tested in isolation
4. **Scalability**: Different analysis types can be scaled independently
5. **Maintainability**: Smaller, focused files are easier to maintain
6. **Consistency**: Aligns with the established architecture across services 
7. **Service Integration**: Continues the pattern of consuming shared functionality from dedicated microservices

## Categories Model Integration

This section outlines the integration of the Categories Model into the restructured analysis-base service, which represents new requirements without altering the original restructuring plan.

### Core Data Entities and Category Repository Integration

The following data entities will be stored in the existing category repository that the analysis-base microservice currently integrates with. This maintains consistency with the current codebase while extending its capabilities.

#### Factors (Cognitive Marketing)

Definition: Rules, heuristics, or laws derived from psychology, marketing science, or observation (e.g., "Blue = Trust," "High Contrast = More Attention").

Machine Representation (to be stored in category repository):

```json
{
  "factor_id": "V-001",
  "category": "Visual",
  "law": "High contrast attracts attention",
  "metric_correlation": {
    "contrast_score": 0.85,
    "scroll_stop_rate": 0.77
  },
  "effectiveness": "positive",
  "purpose": "Scroll-stopping",
  "saturation_level": 0.76,
  "time_decay_rate": 0.05,
  "last_effective_timestamp": "2025-04-01T00:00:00Z"
}
```

#### Secret Sauce (SS) (Creative, Generation-Specific Ideas)

Definition: Highly creative, specific execution patterns used by the generation base (not part of the analysis base for now). These are inventive, often niche-specific ideas that can leave a memorable impression (e.g., "Start video with subtle teaser pattern reused later").

Machine Representation (to be stored in category repository):

```json
{
  "ss_id": "SS-002",
  "idea": "Repeated teaser layout",
  "impact": "Feels familiar, builds recognition",
  "used_in": ["Intro", "Main layout"],
  "creative_purpose": "Psychological imprinting",
  "saturation_level": 0.61,
  "time_decay_rate": 0.03,
  "last_effective_timestamp": "2025-03-25T00:00:00Z"
}
```

#### Batch-As-Object (BAO) and Campaign Categories

In addition to factors and secret sauces, the category repository will also store:

- **Batches**: Collections of content grouped for analysis and generation
- **Campaigns**: Higher-level objects that may contain multiple batches

These will also be represented as categories in the repository, allowing for consistent access patterns across all entity types.

### Categories Model Worker Enhancements

The Categories Model provides a more detailed framework for each worker type in the analysis-base service. The following enhancements should be integrated into the restructuring plan without changing the existing architectural decisions.

#### Descriptive Worker Enhancement

Function: To collect, extract, and summarize raw performance data of objects (factors, secret sauces, batches, campaigns) or individuals (users of the software), without interpreting why something happened or what to do next.

##### In Categories Context

Describes: Factor performance across batches or campaigns, SS performance across different use cases, overall batch-level metric outputs (e.g., CTR, save rate), campaign performance summaries, correlations between factor presence and metric trends.

Input Format:

```json
{
  "object_type": "factor",
  "object_id": "V-001",
  "metrics": ["engagement_rate", "scroll_stop_rate"],
  "time_range": "last_30_days"
}
```

Output Format:

```json
{
  "factor_id": "V-001",
  "average_engagement_rate": 0.74,
  "average_scroll_stop_rate": 0.82,
  "variance": {
    "engagement_rate": 0.05
  },
  "use_count": 128
}
```

##### In User (Individual) Context

Describes: A user's historical use of factors or campaigns, individual performance trends across content pieces, factor-level summary for a user (e.g., "Trust-related factors perform well for this user"), batch-level breakdowns the user participated in.

Input Format:

```json
{
  "user_id": "USER-903",
  "metric_targets": ["trust_score", "click_rate"],
  "factor_tracking": true,
  "time_window": "Q1_2025"
}
```

Output Format:

```json
{
  "user_id": "USER-903",
  "factor_summary": {
    "V-001": {
      "click_rate": 0.68,
      "trust_score": 0.72
    },
    "V-002": {
      "click_rate": 0.33,
      "trust_score": 0.40
    }
  },
  "best_performing_factor": "V-001",
  "average_trust_score": 0.65
}
```

ML Role: Feature extraction, aggregation and variance calculations, trend mapping, metric correlation detection (but not interpretation).

#### Diagnostic Worker Enhancement

Function: Identify why a factor or campaign or other categories worked or failed. Spots anomalies using events, feedback, or platform changes.

Input Format:

```json
{
  "object_type": "factor",
  "object_id": "V-001",
  "associated_metrics": ["scroll_stop_rate"],
  "contextual_data": {
    "platform_events": true,
    "user_feedback": true
  }
}
```

ML Role: Pattern detection, causal inference, symbolic + ML reasoning.

#### Predictive Worker Enhancement (Future: Simulated Mind Model)

Function: Simulate how a user or persona would respond to specific factor combinations or content (behavior modeling).

Input Format:

```json
{
  "user_profile": {
    "persona": "curious_genz",
    "platform": "Instagram",
    "past_engagement": ["V-002", "V-004"]
  },
  "content_factors": ["V-001", "V-006"],
  "output_desired": "trust",
  "context": "story_ad"
}
```

ML Role: User behavior modeling, embedding models, simulation via neural or RL-based frameworks.

#### Prescriptive Worker Enhancement

Function: Recommend optimal factors or SS for a batch, campaign, or user segment. Works off both diagnostic conclusions and metadata matching.

Input Format:

```json
{
  "target_object_type": "batch",
  "object_id": "BATCH-025",
  "desired_outcome": "increase_trust",
  "audience_profile": {
    "demographics": "millennial",
    "platform": "Instagram"
  }
}
```

ML Role: Optimization, recommendation engine, behavioral modeling.

### Implementation Changes for Categories Model

To integrate the Categories Model into the restructured analysis-base service, the following implementation changes are recommended:

#### 1. Enhanced Category Repository Integration

Extend the existing category repository integration to handle the new data entities:

```python
# Example of enhanced category repository integration
class CategoryRepositoryClient:
    async def get_factor(self, factor_id: str) -> Dict[str, Any]:
        """Get factor from category repository"""
        return await self.get_category("factor", factor_id)
        
    async def get_secret_sauce(self, ss_id: str) -> Dict[str, Any]:
        """Get secret sauce from category repository"""
        return await self.get_category("secret_sauce", ss_id)
        
    async def get_batch(self, batch_id: str) -> Dict[str, Any]:
        """Get batch from category repository"""
        return await self.get_category("batch", batch_id)
        
    async def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign from category repository"""
        return await self.get_category("campaign", campaign_id)
```

#### 2. Updated Data Models as Category Extensions

Rather than creating separate model files, extend the existing category models:

```
src/repository/models/
├── category.py           # Base category model
├── category_factory.py   # Factory for creating category-specific instances
└── category_types/       # Extensions for specific category types
    ├── factor.py         # Factor as a category extension
    ├── secret_sauce.py   # Secret sauce as a category extension
    ├── batch.py          # Batch as a category extension
    └── campaign.py       # Campaign as a category extension
```

#### 3. API Schemas with Category Context

Update the API schemas to work with the category context:

```
src/api/schemas/
├── category_input.py     # Base input schema for category operations
├── descriptive/
│   ├── category_input.py # Category context input schema for descriptive analysis
│   ├── user_input.py     # User context input schema
│   └── output.py         # Descriptive output schemas
├── diagnostic/
│   ├── input.py          # Diagnostic input schema
│   └── output.py         # Diagnostic output schemas
# And similar for predictive and prescriptive
```

#### 4. Module Component Enhancements with Category Repository Integration

Enhance the components to leverage the category repository:

```python
# Example of component integration with category repository
class ObjectPerformanceAnalyzer(BaseComponent):
    """Analyzes performance of category objects."""
    
    def __init__(self, category_repository: CategoryRepositoryClient):
        self.category_repository = category_repository
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Get object data from category repository
        object_type = context.get("object_type")
        object_id = context.get("object_id")
        
        if object_type == "factor":
            object_data = await self.category_repository.get_factor(object_id)
        elif object_type == "secret_sauce":
            object_data = await self.category_repository.get_secret_sauce(object_id)
        # ...and so on
        
        # Process data and return results
        # ...
```

#### 5. ML Service Integration with Category Repository

Add specialized ML components that work with the category data models:

```python
# Example of ML service integration with category repository
class FactorEffectivenessModel:
    """ML model for analyzing factor effectiveness."""
    
    def __init__(self, category_repository: CategoryRepositoryClient):
        self.category_repository = category_repository
        
    async def analyze_effectiveness(self, factor_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the effectiveness of a factor based on historical data.
        
        Args:
            factor_id: ID of the factor to analyze
            context: Analysis context
            
        Returns:
            Effectiveness analysis results
        """
        # Get factor from repository
        factor = await self.category_repository.get_factor(factor_id)
        
        # Get historical data where this factor was used
        historical_data = await self.category_repository.get_factor_usage_history(factor_id)
        
        # Apply ML model to analyze effectiveness
        # ...
        
        # Return results
        return {
            "factor_id": factor_id,
            "effectiveness": 0.85,
            "confidence": 0.92,
            "key_drivers": ["high_contrast", "visual_appeal"],
            "effectiveness_trend": "stable"
        }
```

This integration allows the ML components to work directly with the category repository, maintaining consistency across the system.

### Integration with Existing Plan

The Categories Model enhances the existing restructuring plan by leveraging the current category repository functionality while extending its capabilities:

1. **Repository Integration**: Uses the existing category repository for storing and retrieving all entity types
2. **Consistent Access Patterns**: Treats factors, secret sauces, batches, and campaigns as categories with a unified access interface
3. **Extended Entity Types**: Adds new types of categories to the existing repository
4. **Unchanged Architecture**: Maintains the core architectural patterns while adding new functionality

These enhancements align with the existing plan's emphasis on leveraging the category repository functionality and maintaining consistent patterns across the codebase.

## ML/Developer Collaboration Plan

Here's a concise plan focusing on the three key approaches to enable effective collaboration between ML experts and developers:

## 1. Declarative Model Specifications

Create a standardized YAML/JSON format that allows ML experts to specify models without coding:

- ML experts define what features to use, algorithms to apply, and hyperparameters to set
- These specifications live in a dedicated "specs" directory separate from code
- Developers build a framework that reads these specifications and creates corresponding model implementations
- When ML experts want to improve models, they update specifications rather than code

## 2. Configuration-Driven Components 

Make worker behavior configurable through external files:

- Analysis strategies, decision trees, and processing rules defined in configuration
- ML experts can modify how analysis works by changing configuration values
- Thresholds, conditions, and analysis sequences become external parameters
- Advanced logic (like when to use inter-batch vs. historical analysis) defined through configuration
- Developers focus on building a robust system that applies these configurations

### Processing Templates and Decision Trees

The configuration-driven approach is implemented through two key concepts with clearly separated responsibilities:

#### Processing Templates
Processing templates are YAML/JSON specifications that define:
- The sequence of **generic** components to execute
- Basic configuration for each component
- Reference to decision trees that provide domain-specific logic
- Error handling and timeout settings

Templates focus on "what happens in what order" (structural aspects), not "why" or "how" (domain logic). They define workflows as sequences of reusable, domain-agnostic components. For example:

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
  
  - name: "performance_analyzer"
    type: "analyzer"
    config:
      operation: "analyze_performance"
      decision_tree: "{context.platform}_performance_analysis"
```

Processing templates are completely reusable across domains because they contain no platform-specific or domain-specific logic.

#### Decision Trees
Decision trees are YAML/JSON specifications that encode:
- Domain-specific analytical logic
- Platform-specific knowledge (Instagram vs. Etsy)
- Business rules and conditions
- Factor selection criteria
- Analytical approaches for different contexts

Trees focus on "what should be analyzed and why" (domain knowledge), not "how processing happens" (structural flow). They encode expert knowledge as structured decision logic. For example:

```yaml
name: "instagram_performance_analysis"
description: "Decision tree for analyzing Instagram content performance"
version: "1.0"
root:
  condition: "context.content_type"
  branches:
    - value: "product_showcase"
      child:
        condition: "metrics.engagement_variance > 0.5"
        branches:
          - value: true
            outcome:
              analysis_approach: "visual_factor_analysis"
              primary_metrics: ["scroll_stop_rate", "engagement_rate"]
              factor_categories: ["contrast", "color_scheme", "composition"]
              reason: "High performance variance indicates visual elements are key differentiators"
```

Decision trees contain all the domain-specific intelligence and can be modified by domain experts without changing code.

#### Implementation and Execution
The system implements this separation through:

1. **Specification Interpreter**: A core module that:
   - Loads and validates templates and trees from configuration files
   - Dynamically resolves references between templates and trees
   - Evaluates decision tree conditions against the runtime context
   - Returns appropriate outcomes to guide component behavior

2. **Dynamic Resolution**: Components dynamically load the appropriate decision tree:
   ```
   decision_tree_name = f"{context.platform}_{context.analysis_type}_analysis"
   tree = spec_interpreter.load_decision_tree_spec(decision_tree_name)
   outcome = spec_interpreter.interpret_decision_tree_spec(tree, context)
   ```

3. **Intern-Friendly Documentation**: Comprehensive guides in the `docs/intern-guide/` directory:
   - Processing template creation guide
   - Decision tree authoring guide
   - Examples for different analysis types and platforms

This architecture allows interns and domain experts to:
1. Create new analysis capabilities by writing templates and trees
2. Modify analytical approaches by updating decision trees
3. Define new processing flows by creating templates
4. All without writing or modifying code

## 3. Clear API Contracts

Define stable interfaces that separate ML implementation from technical infrastructure:

- Create well-documented API contracts for how components interact
- Ensure these contracts remain stable even as implementations change
- Allow ML experts to focus on what happens "inside" these contracts
- Developers maintain the system architecture around these stable interfaces
- New ML approaches can be plugged in without disrupting the overall system

## Implementation Approach

1. First, developers build the technical framework that supports these three principles
2. ML experts then work within this framework by writing specifications and configurations
3. As ML techniques evolve, only specifications and configurations need to change
4. The underlying code remains stable, focusing on interpreting and applying these changes

This approach provides a clear separation of responsibilities where ML experts can focus on algorithms and analysis techniques while developers maintain the technical infrastructure. It creates a sustainable system that can evolve continuously as ML capabilities improve.

## Processing Infrastructure Enhancement

The existing processing infrastructure (base_Component, component_registry, pipeline, etc.) will not be replaced but rather enhanced to support the ML/Developer Collaboration Plan:

### Key Processing Module Enhancements

1. **Enhanced BaseComponent**:
   - Evolves to become a configuration interpreter
   - Gains ability to load and apply ML specifications
   - Implements configurable decision trees
   - Maintains its core role in the component architecture

2. **Enhanced Component Registry**:
   - Expands to dynamically load components based on specifications
   - Supports versioning of components and models
   - Provides lookup mechanisms for both code-based and config-based components
   - Retains its central role in component discovery and instantiation

3. **Configuration-Aware Pipeline**:
   - Adds ability to construct pipelines from processing templates
   - Supports dynamic pipeline modification based on analysis needs
   - Implements component sequences defined in templates
   - Preserves its core orchestration functionality

4. **Worker Service Integration**:
   - Workers use processing templates to determine processing sequence
   - Collect requests from repository and apply appropriate templates
   - Use decision trees to make analytical decisions
   - Upload results back to repository with appropriate metadata

5. **Specification Interpreter**:
   - New module for loading and interpreting declarative specifications
   - Handles processing templates, decision trees, and model specifications
   - Manages dynamic resolution between specifications
   - Provides validation and error reporting for specifications

This enhancement approach maintains the stable, proven foundation of the processing module while making it more flexible, configurable, and accessible to ML experts with limited coding experience.

### Phase 1: Foundation and Infrastructure (2-3 weeks)

1. **Create Base Directory Structure**
   ```bash
   mkdir -p microservices/analysis-base/{docs,tests,specs/{models,decision_trees,pipelines,api_contracts},src/{api,common,config,repository,service,processing,clients,modules}}
   ```

2. **Set Up Docker Environment**
   - Create updated Dockerfile and docker-compose.yml
   - Ensure all dependencies are properly captured
   - Configure environment variables for development and production

3. **Establish Scope Separation Documentation**
   - Create `docs/scope_separation_guide.md` documenting the clear separation between:
     - Processing modules (generic, reusable components)
     - Processing templates (workflow definitions)
     - Decision trees (domain-specific analytical logic)
   - Create intern guide documentation explaining how to work with each component
   - Develop validation criteria for each component type
   - **Document platform-specific analysis purposes** (Instagram, Etsy, campaigns)
   - **Create guidelines for individual vs. category processing separation**

4. **Implement Core Processing Infrastructure**
   - Create enhanced BaseComponent class with configuration loading
   - Implement component registry with specification support
   - Create base contracts for component interfaces
   - **Design component interfaces that support both individual and category processing**
   - **Create analysis context model with support for inter-batch, intra-batch, and historical analysis**
   - Implement pipeline mechanism supporting template-driven execution
     - Design pipeline to accept generic processing templates
     - Ensure component sequences are defined entirely by templates
     - Create dynamic template resolution mechanism
   - Implement pipeline executor with metrics tracking and error handling

5. **Implement Configuration and Specification Management**
   - Create configuration loader with environment variable support
   - **Implement platform detection and configuration adapters for Instagram, Etsy, etc.**
   - Implement specification interpreter for processing templates
     - Create template validation and loading logic
     - Implement dynamic component sequence creation from templates
   - Implement specification interpreter for decision trees
     - Create tree validation and loading logic
     - Implement context-based condition evaluation
     - Develop outcome resolution mechanism
     - **Create validators for platform-specific decision tree patterns**
   - Define schema validation for both templates and trees

### Phase 2: Repository and Client Layer (1-2 weeks)

1. **Implement Repository Abstractions**
   - Create base repository interface with common patterns
   - Implement context repository for analysis context data
   - Implement results repository for storage and retrieval of analysis results
   - **Design repository models for both individual and category objects**
   - Set up repository factory pattern for future extensibility

2. **Enhance Database Layer Client**
   - Update client to support new category repository requirements
   - Implement connections to external data sources
   - **Create specialized repository methods for factor, secret sauce, batch, and campaign categories**
   - Add support for category history and trending
   - Create client configuration and connection pooling

3. **Create API Schemas**
   - Define input and output schemas for all analysis types
   - **Create platform-specific request and response schemas**
   - **Design dual-mode schemas that support both individual and category analysis**
   - Create API contracts for external integration
   - Implement schema validation and transformation
   - Set up versioned API support

### Phase 2.5: Template and Decision Tree Foundation (1-2 weeks)

1. **Create Processing Template Structure**
   - Design the schema for processing templates
   - Implement template parser and validator
   - Create directory structure for template storage
   - Develop template selection logic in worker service
   - **Create base templates for each platform (Instagram, Etsy, campaigns)**
   - Create base templates for each analysis type:
     - Descriptive analysis template
     - Diagnostic analysis template
     - Predictive analysis template
     - Prescriptive analysis template

2. **Create Decision Tree Structure**
   - Design the schema for decision trees
   - Implement tree parser and condition evaluator
   - Create directory structure for tree storage
   - Develop dynamic tree loading based on context
   - **Create decision trees for selecting analysis approach (inter-batch, intra-batch, historical)**
   - Create base trees for platform-specific logic:
     - Instagram analysis trees
     - Etsy analysis trees
     - Campaign analysis trees
     - Strategy analysis trees

3. **Develop Component Functionality Interface**
   - Design interfaces between components and decision trees
   - Implement outcome interpretation mechanism
   - Create component configuration extraction from templates
   - Develop context enrichment patterns
   - **Create adapter interfaces for handling both individual and category objects**

4. **Create Intern Documentation**
   - Develop comprehensive guides for interns in `docs/intern-guide/`:
     - Processing template creation guide with examples
     - Decision tree authoring guide with examples
     - README with overview of the system architecture
     - **Platform-specific analysis documentation**
     - **Individual vs. category processing guidelines**
   - Create template examples for common analysis patterns
   - Include real-world decision tree examples for different platforms

### Phase 3: Data Ingestion Module Migration (1-2 weeks)

1. **Component Migration**
   - Convert DataIngestion class to DataCollectorComponent
   - Convert Preprocessing class to DataTransformerComponent
   - Convert FeatureExtraction class to FeatureExtractorComponent
   - Implement helper utilities for data ingestion
   - **Create platform-specific numerical transformers for Instagram, Etsy, and campaign data**
   - **Implement platform type indicators as numerical flags (is_instagram: 1.0, is_etsy: 0.0)**
   - **Implement category objects as standardized numerical feature vectors**

2. **User Insight Extension Repository Integration**
   - **Implement connections to platform-specific User Insight Extension repositories**
     - Create Instagram User Insight connector
     - Create Etsy User Insight connector
     - Create adapter interfaces for additional platforms
   - **Develop standardized data access patterns for user-level metrics**
     - Ensure all user-level metrics come exclusively from User Insight Extension repositories
     - Create abstraction layer to handle platform-specific user insight data formats
   - **Map platform-specific user metrics to standardized metric framework**
     - Transform platform-specific engagement metrics to standard format
     - Normalize user interaction patterns across platforms
   - **Implement user context processors for different platforms**
     - Create user history analyzers for each platform
     - Develop user preference extractors customized per platform
     - Build cross-platform user behavior correlation tools

3. **Create Numerical Transformation Layer**
   - **Implement platform-specific normalizers that convert raw metrics to standard 0-1 range**
   - **Create algorithms to transform all platform-specific metrics to standard metrics**
   - **Develop feature vector creation from normalized platform data**
   - **Ensure all platform-specific knowledge is encapsulated in data ingestion**
   - **Create validation tests for metric normalization across platforms**
   - **Implement feature extraction that produces consistent numerical features**
   - **Create unified transformers that merge category and user insight data**
     - Develop algorithms to correlate user insights with category performance
     - Create feature vectors that incorporate both category attributes and user behaviors
     - Implement normalization strategies for combined user-category metrics

4. **Create Component Specifications**
   - Define specifications for data pipeline components
   - Create configuration templates for different data sources
   - Implement transformation rule specifications
   - Define feature extraction specifications
   - **Create platform-specific numerical transformation rules**
   - **Design specifications for numerical feature extraction**
   - **Develop User Insight Extension integration specifications**
     - Define standard interfaces for all User Insight Extension repositories
     - Create platform-specific connector configurations
     - Document required data formats and access patterns

5. **Integration Testing**
   - Verify data pipeline still functions correctly
   - Compare outputs with existing implementation
   - Ensure backward compatibility with existing systems
   - Performance test with realistic data volumes
   - **Test with platform-specific data sources**
   - **Validate numerical transformation across platforms**
   - **Verify consistent feature vector format regardless of platform**
   - **Test User Insight Extension repository integrations for all platforms**
     - Validate data retrieval from Instagram User Insight Extension
     - Verify Etsy User Insight Extension connectivity
     - Test cross-platform user insight normalization
     - Benchmark user data retrieval performance

### Phase 4: Descriptive Analysis Module Migration (2 weeks)

1. **Decompose Descriptive Worker**
   - Create factor_analyzer, batch_analyzer, user_analyzer components
   - Implement data_summarizer and trend_analyzer components
   - Add category-specific analysis components
   - Implement helper utilities for descriptive analysis
   - **Create `ObjectPerformanceAnalyzer` for category-level analysis**
   - **Implement dual-mode analyzers for both individual items and category objects**
   - **Develop specialized components for inter-batch, intra-batch, and historical analysis**

2. **Create Configuration Templates**
   - Define decision trees for descriptive analysis
   - Create pipeline configurations for different analysis contexts
   - Implement scoring parameter specifications
   - Define output format templates
   - **Create platform-specific descriptive analysis templates for Instagram, Etsy, etc.**
   - **Design templates for category object analysis (factors, secret sauces, etc.)**

3. **Integration Testing**
   - Verify descriptive analysis produces correct results
   - Compare with existing implementation
   - Test with various input types and edge cases
   - Verify integration with database layer and repositories
   - **Test with platform-specific datasets**
   - **Validate both individual and category analysis outputs**

### Phase 5: Diagnostic Analysis Module Migration (2 weeks)

1. **Decompose Diagnostic Worker**
   - Create root_cause_analyzer, correlation_detector components
   - Implement anomaly_detector and strength_weakness_analyzer components
   - Add factor_analyzer specialized for diagnostic purposes
   - Create helper utilities for diagnostic analysis
   - **Implement `FactorEffectivenessModel` for analyzing factor performance trends**
   - **Create `SecretSauceContextAnalyzer` for creative pattern analysis**
   - **Develop `CampaignDiagnosticComponent` for campaign structure analysis**

2. **Create Configuration Templates**
   - Define decision trees for diagnostic analysis
   - Create pipeline configurations for different diagnostic contexts
   - Implement causal inference specifications
   - Define anomaly detection thresholds and rules
   - **Create platform-specific diagnostic decision trees**
   - **Design category-specific diagnostic templates**
   - **Implement analysis type-specific diagnostic approaches**

3. **Integration Testing**
   - Verify diagnostic analysis produces correct results
   - Compare with existing implementation
   - Test with complex diagnostic scenarios
   - Verify integration with descriptive analysis results
   - **Test with different platforms and analysis approaches**
   - **Validate integrated individual-category analysis flows**

### Phase 6: Predictive & Prescriptive Modules (2-3 weeks)

1. **Implement Predictive Module Components**
   - Create forecaster, trend_predictor, anomaly_detector components
   - Implement time series analysis utilities
   - Add ML model integration points
   - Develop prediction evaluation metrics
   - **Create `FactorLifecyclePredictorComponent` for factor effectiveness forecasting**
   - **Implement platform-specific prediction models for Instagram, Etsy, etc.**
   - **Design forecasting components for category objects and individual items**

2. **Implement Prescriptive Module Components**
   - Create recommendation_generator, strategy_optimizer, impact_analyzer components
   - Implement optimization algorithms
   - Develop recommendation engines
   - Create impact assessment tools
   - **Implement `CreativeStrategyOptimizer` for secret sauce recommendations**
   - **Create `CampaignOptimizationComponent` for campaign strategy suggestions**
   - **Develop platform-specific recommendation generators**

3. **Create Configuration Templates**
   - Define decision trees and pipeline configurations
   - Set up ML model specifications for predictive models
   - Create recommendation strategy templates
   - Define impact assessment criteria
   - **Create platform-specific recommendation decision trees**
   - **Implement analysis approach-specific prediction templates (inter-batch, intra-batch, historical)**

### Phase 7: API and Integration (1-2 weeks)

1. **Implement API Layer**
   - Create FastAPI router and endpoints
   - Implement request validation and error handling
   - Add authentication and authorization
   - Implement health check service
   - **Create endpoints for both individual and category-level analysis**
   - **Implement platform-specific API endpoints**

2. **Worker Service Implementation**
   - Update worker service to use new component architecture
   - Implement context poller and processor
   - Add monitoring and observability
   - Implement retry and error handling strategies
   - **Create specialized workers for different analysis approaches**
   - **Implement platform detection and routing logic**

3. **Final Integration**
   - Connect all components into cohesive system
   - Set up monitoring and logging
   - Configure deployment pipeline
   - Create comprehensive documentation
   - **Integrate all analysis approaches and platform-specific components**
   - **Ensure seamless individual and category processing**

### Phase 8: Testing and Validation (2 weeks)

1. **Comprehensive Testing**
   - Create unit tests for all components
   - Implement integration tests for each module
   - Develop system tests for end-to-end functionality
   - Set up continuous integration pipeline
   - **Create platform-specific test suites**
   - **Test individual and category processing flows**
   - **Validate all analysis approaches (inter-batch, intra-batch, historical)**

2. **Performance Testing**
   - Verify performance is equal or better than previous implementation
   - Test with large datasets
   - Identify and resolve bottlenecks
   - Implement performance monitoring
   - **Benchmark platform-specific analysis performance**
   - **Test category analysis performance with large datasets**

3. **Documentation**
   - Create comprehensive documentation for ML experts
   - Document component interfaces and specifications
   - Create user guides for configuration management
   - Document deployment and operations procedures
   - **Create detailed platform-specific analysis guides**
   - **Document individual vs. category processing patterns**
   - **Create decision tree authoring guides for each platform**

## Risk Mitigation Strategy

1. **Parallel Running Period**
   - Deploy new implementation alongside existing one
   - Compare outputs to ensure consistency
   - Switch traffic gradually from old to new implementation
   - Monitor error rates and performance metrics

2. **Rollback Plan**
   - Maintain old implementation until confident in new one
   - Create scripts to revert to old implementation if issues arise
   - Implement feature flags for individual components
   - Store dual results for critical analyses during transition

3. **Feature Flags**
   - Implement feature flags to enable/disable new functionality
   - Allow for gradual rollout of new capabilities
   - Support A/B testing of new components
   - Enable quick disabling of problematic features

## Timeline and Dependencies

Total estimated timeline: 12-16 weeks

Critical dependencies:
1. Core processing infrastructure must be completed before module migrations
2. Repository layer must be implemented before components can store results
3. Data ingestion module must be migrated before analysis modules
4. Descriptive analysis must be completed before diagnostic analysis

This phased approach allows for incremental implementation and validation, ensuring that each component is thoroughly tested before moving to the next phase. As each phase is completed, the corresponding sections of this document can be updated to reflect the actual implementation details, ensuring the documentation stays in sync with the codebase.

## Component Responsibility Matrix

| Responsibility | Processing Module | Processing Template | Decision Tree |
|----------------|----------|---------------|-----------------|
| Component sequence | ❌ | ✅ | ❌ |
| Data flow between components | ❌ | ✅ | ❌ |
| Error handling and retries | ✅ | ✅ | ❌ |
| Domain-specific logic | ❌ | ❌ | ✅ |
| Platform-specific knowledge | ❌ | ❌ | ✅ |
| Business rules | ❌ | ❌ | ✅ |
| Component implementation | ✅ | ❌ | ❌ |
| Analysis methodology | ❌ | ❌ | ✅ |
| Processing strategies | ❌ | ✅ | ✅ |
| Factor selection criteria | ❌ | ❌ | ✅ |

This matrix clearly defines which aspects of the system are the responsibility of each component type, helping to maintain proper separation of concerns during implementation.

> **Note:** For detailed information about analysis purposes for different platforms (Instagram, Etsy, campaigns) and the scope separation between pipelines and decision trees, see [Analysis Purposes and Processing Strategy](docs/analysis_purposes_and_strategy.md). This document explains how the system handles both individual and category-level processing across inter-batch, intra-batch, and historical analysis approaches.

## Risk Mitigation Strategy