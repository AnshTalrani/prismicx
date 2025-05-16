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

4. **Implement Core Processing Infrastructure**
   - Create enhanced BaseComponent class with configuration loading
   - Implement component registry with specification support
   - Create base contracts for component interfaces
   - Implement pipeline mechanism supporting template-driven execution
     - Design pipeline to accept generic processing templates
     - Ensure component sequences are defined entirely by templates
     - Create dynamic template resolution mechanism
   - Implement pipeline executor with metrics tracking and error handling

5. **Implement Configuration and Specification Management**
   - Create configuration loader with environment variable support
   - Implement specification interpreter for processing templates
     - Create template validation and loading logic
     - Implement dynamic component sequence creation from templates
   - Implement specification interpreter for decision trees
     - Create tree validation and loading logic
     - Implement context-based condition evaluation
     - Develop outcome resolution mechanism
   - Define schema validation for both templates and trees

### Phase 2: Repository and Client Layer (1-2 weeks)

1. **Implement Repository Abstractions**
   - Create base repository interface with common patterns
   - Implement context repository for analysis context data
   - Implement results repository for storage and retrieval of analysis results
   - Set up repository factory pattern for future extensibility

2. **Enhance Database Layer Client**
   - Update client to support new category repository requirements
   - Implement connections to external data sources
   - Add support for category history and trending
   - Create client configuration and connection pooling

3. **Create API Schemas**
   - Define input and output schemas for all analysis types
   - Create API contracts for external integration
   - Implement schema validation and transformation
   - Set up versioned API support

### Phase 2.5: Platform-Specific Analysis Implementation (1-2 weeks)

Based on the defined Analysis Purposes and Processing Strategy section, we need to implement the foundation for platform-specific analysis and dual-mode processing (individual and category):

1. **Analysis Context Model**
   - Create `AnalysisContext` class with platform detection (Instagram, Etsy, Campaign, Strategy)
   - Implement analysis type tracking (inter-batch, intra-batch, historical)
   - Add entity type detection (individual content item vs. category object)
   - Develop context enrichment utilities for adding platform-specific metadata

2. **Platform-Specific Decision Trees**
   - Create base decision tree templates for each platform:
     - Instagram analysis decision trees
     - Etsy analysis decision trees
     - Campaign analysis decision trees
     - Strategy analysis decision trees
   - Implement platform-specific condition evaluators
   - Define default analysis rules based on entity characteristics

3. **Individual and Category Processing Components**
   - Create dual-mode base components that can process both individuals and categories
   - Implement `ObjectPerformanceAnalyzer` for category-level analysis
   - Develop mode detection and processing strategy selection
   - Create adapter patterns for uniform component interfaces

4. **Analysis Strategy Selection Framework**
   - Implement decision trees for selecting between analysis approaches
   - Create template selection logic based on context properties
   - Develop dynamic component configuration based on analysis approach
   - Build context validation for each analysis type

### Phase 3: Data Ingestion Module Migration (1-2 weeks)

1. **Component Migration**
   - Convert DataIngestion class to DataCollectorComponent
   - Convert Preprocessing class to DataTransformerComponent
   - Convert FeatureExtraction class to FeatureExtractorComponent
   - Implement helper utilities for data ingestion

2. **Create Component Specifications**
   - Define specifications for data pipeline components
   - Create configuration templates for different data sources
   - Implement transformation rule specifications
   - Define feature extraction specifications
   - Create platform-specific data collection specifications for Instagram, Etsy, and Campaign data
   - Implement category object collection specifications for factors, secret sauces, and batches

3. **Integration Testing**
   - Verify data pipeline still functions correctly
   - Compare outputs with existing implementation
   - Ensure backward compatibility with existing systems
   - Performance test with realistic data volumes

### Phase 4: Descriptive Analysis Module Migration (2 weeks)

1. **Decompose Descriptive Worker**
   - Create factor_analyzer, batch_analyzer, user_analyzer components
   - Implement data_summarizer and trend_analyzer components
   - Add category-specific analysis components
   - Implement helper utilities for descriptive analysis
   - Create specialized analyzers for Instagram, Etsy, and Campaign content
   - Implement dual-mode factor analyzers for both individual content and factor categories

2. **Create Configuration Templates**
   - Define decision trees for descriptive analysis
   - Create pipeline configurations for different analysis contexts
   - Implement scoring parameter specifications
   - Define output format templates
   - Create platform-specific decision trees for descriptive analysis
   - Implement analysis selection trees for inter-batch, intra-batch, and historical analysis

3. **Integration Testing**
   - Verify descriptive analysis produces correct results
   - Compare with existing implementation
   - Test with various input types and edge cases
   - Verify integration with database layer and repositories

### Phase 5: Diagnostic Analysis Module Migration (2 weeks)

1. **Decompose Diagnostic Worker**
   - Create root_cause_analyzer, correlation_detector components
   - Implement anomaly_detector and strength_weakness_analyzer components
   - Add factor_analyzer specialized for diagnostic purposes
   - Create helper utilities for diagnostic analysis
   - Implement `FactorEffectivenessModel` for factor performance diagnosis
   - Create `SecretSauceContextAnalyzer` for creative pattern analysis
   - Develop `CampaignDiagnosticComponent` for campaign structure analysis

2. **Create Configuration Templates**
   - Define decision trees for diagnostic analysis
   - Create pipeline configurations for different diagnostic contexts
   - Implement causal inference specifications
   - Define anomaly detection thresholds and rules
   - Create platform-specific diagnostic decision trees for Instagram, Etsy, and Campaign analysis
   - Implement analysis type selection trees for diagnostic processes

3. **Integration Testing**
   - Verify diagnostic analysis produces correct results
   - Compare with existing implementation
   - Test with complex diagnostic scenarios
   - Verify integration with descriptive analysis results

### Phase 6: Predictive & Prescriptive Modules (2-3 weeks)

1. **Implement Predictive Module Components**
   - Create forecaster, trend_predictor, anomaly_detector components
   - Implement time series analysis utilities
   - Add ML model integration points
   - Develop prediction evaluation metrics
   - Implement `FactorLifecyclePredictorComponent` for factor effectiveness forecasting
   - Create platform-specific prediction models for Instagram, Etsy, and Campaign analysis

2. **Implement Prescriptive Module Components**
   - Create recommendation_generator, strategy_optimizer, impact_analyzer components
   - Implement optimization algorithms
   - Develop recommendation engines
   - Create impact assessment tools
   - Implement `CreativeStrategyOptimizer` for secret sauce recommendations
   - Create `CampaignOptimizationComponent` for campaign strategy recommendations

3. **Create Configuration Templates**
   - Define decision trees and pipeline configurations
   - Set up ML model specifications for predictive models
   - Create recommendation strategy templates
   - Define impact assessment criteria
   - Implement platform-specific recommendation trees for Instagram, Etsy, and Campaign contexts
   - Create dual-mode templates for both individual and category-level recommendations

### Phase 7: API and Integration (1-2 weeks)

1. **Implement API Layer**
   - Create FastAPI router and endpoints
   - Implement request validation and error handling
   - Add authentication and authorization
   - Implement health check service

2. **Worker Service Implementation**
   - Update worker service to use new component architecture
   - Implement context poller and processor
   - Add monitoring and observability
   - Implement retry and error handling strategies

3. **Final Integration**
   - Connect all components into cohesive system
   - Set up monitoring and logging
   - Configure deployment pipeline
   - Create comprehensive documentation

### Phase 8: Testing and Validation (2 weeks)

1. **Comprehensive Testing**
   - Create unit tests for all components
   - Implement integration tests for each module
   - Develop system tests for end-to-end functionality
   - Set up continuous integration pipeline

2. **Performance Testing**
   - Verify performance is equal or better than previous implementation
   - Test with large datasets
   - Identify and resolve bottlenecks
   - Implement performance monitoring

3. **Documentation**
   - Create comprehensive documentation for ML experts
   - Document component interfaces and specifications
   - Create user guides for configuration management
   - Document deployment and operations procedures

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
