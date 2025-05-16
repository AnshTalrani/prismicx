# Custom Processing Examples

This document provides real-world examples of creating and configuring custom processing components for the Generative Base service.

## Creating a Custom Processing Component

### Example 1: Creating a Content Classification Component

In this example, we'll create a component that classifies content into categories.

#### 1. Create the YAML configuration file

Create a file named `content_classification.yaml` in the `docs/modules/` directory:

```yaml
# content_classification.yaml
id: "content_classification"
name: "Content Classification Component"
description: "Classifies content into predefined categories"
version: "1.0.0"
  
behavior:
  input_types:
    - "processed_text"
    - "raw_text"
  
  output_type: "classified_content"
  
  ai_models:
    primary:
      type: "openai"
      model: "gpt-4"
      temperature: 0.3
      max_tokens: 1000
  
  config:
    categories:
      - "technology"
      - "business"
      - "health"
      - "science"
      - "entertainment"
    confidence_threshold: 0.7
    multi_label: false
    include_reasoning: true
  
  prompts:
    classification: |
      Analyze the following content and classify it into one of these categories:
      {{#each categories}}
      - {{this}}
      {{/each}}
      
      CONTENT:
      {{content}}
      
      For each category, provide a confidence score between 0 and 1.
      If requested, explain your reasoning for the top category.
      
      Output should be in JSON format:
      {
        "primary_category": "category_name",
        "confidence_scores": {
          "category1": 0.X,
          "category2": 0.Y,
          ...
        },
        "reasoning": "Your explanation here if include_reasoning is true"
      }
```

#### 2. Add to `framework_definition.yaml`

Add the component to the modules list in `framework_definition.yaml`:

```yaml
modules:
  # ... existing modules ...
  - id: "content_classification"
    path: "modules/content_classification.yaml"
    enabled: true
    description: "Classifies content into predefined categories"
```

#### 3. Create a Processing Flow

Add a flow that uses the new component:

```yaml
flows:
  # ... existing flows ...
  - id: "classification_flow"
    name: "Content Classification"
    description: "Process and classify content"
    modules:
      - id: "input_preprocessing"
        config_override: {}
      - id: "content_classification"
        config_override: {
          "multi_label": true,
          "confidence_threshold": 0.5
        }
```

### Example 2: Enhancing Content with Citations

This example creates a component that enhances content with relevant citations.

#### 1. Create the YAML configuration file

Create a file named `citation_enhancement.yaml` in the `docs/modules/` directory:

```yaml
# citation_enhancement.yaml
id: "citation_enhancement"
name: "Citation Enhancement"
description: "Enhances content with relevant citations and references"
version: "1.0.0"
  
behavior:
  input_types:
    - "processed_text"
  
  output_type: "cited_content"
  
  ai_models:
    primary:
      type: "openai"
      model: "gpt-4"
      temperature: 0.4
      max_tokens: 2000
  
  config:
    citation_style: "APA"  # Options: APA, MLA, Chicago
    citation_placement: "inline"  # Options: inline, footnote, endnote
    min_citations: 3
    max_citations: 10
    verify_sources: true
    add_bibliography: true
  
  prompts:
    enhance_with_citations: |
      Enhance the following content by adding appropriate citations in {{citation_style}} style
      using {{citation_placement}} placement.
      
      CONTENT:
      {{content}}
      
      Add between {{min_citations}} and {{max_citations}} citations to strengthen the arguments 
      and claims in the text. If verify_sources is true, only use reputable academic or 
      authoritative sources.
      
      If add_bibliography is true, include a properly formatted bibliography at the end.
```

#### 2. Add to Processing Flow

Add the component to an existing flow or create a new flow:

```yaml
flows:
  - id: "academic_content_flow"
    name: "Academic Content Generation"
    description: "Generate academic content with proper citations"
    modules:
      - id: "input_preprocessing"
        config_override: {}
      - id: "high_quality_output"
        config_override: {
          "tone": "academic",
          "style": "analytical"
        }
      - id: "citation_enhancement"
        config_override: {
          "citation_style": "APA",
          "min_citations": 5
        }
      - id: "quality_assurance"
        config_override: {}
```

## Implementing Custom Processing Logic

For components that need custom processing logic beyond what can be configured in YAML, you'll need to create a Python class:

### Example: Custom Fact-Checking Component

```python
# src/processing/components/custom/fact_checking_component.py
from typing import Dict, Any
import aiohttp
from ...base_component import BaseComponent

class FactCheckingComponent(BaseComponent):
    """
    Component for fact-checking generated content against trusted sources.
    """
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the context by fact-checking claims."""
        self.logger.info("Starting fact-checking process")
        
        # Get content to fact-check from context
        content = context.get("data", {}).get("content", "")
        if not content:
            self.logger.warning("No content to fact-check")
            return context
        
        # Extract claims using prompt template
        claims_prompt = self.get_prompt_template("extract_claims")
        if not claims_prompt:
            self.logger.error("Missing extract_claims prompt template")
            if self.continue_on_error:
                return context
            raise ValueError("Missing required prompt template")
        
        # Render the prompt with the content
        rendered_prompt = self.render_prompt("extract_claims", {"data": {"content": content}})
        
        # Extract claims using LLM call (simplified example)
        claims = await self._extract_claims_with_llm(rendered_prompt)
        
        # Verify each claim against trusted sources
        verification_results = []
        for claim in claims:
            result = await self._verify_claim(claim)
            verification_results.append(result)
        
        # Enhance context with verification results
        updated_context = self.merge_results(context, {
            "fact_check_results": verification_results,
            "verified_claims_count": len(verification_results),
            "accurate_claims_count": sum(1 for r in verification_results if r["accurate"]),
            "inaccurate_claims_count": sum(1 for r in verification_results if not r["accurate"]),
        })
        
        self.logger.info(f"Completed fact-checking with {len(verification_results)} claims verified")
        return updated_context
    
    async def _extract_claims_with_llm(self, prompt: str) -> list:
        """Extract factual claims from content using LLM."""
        # Implementation would use LLM API to extract claims
        # Simplified example returns mock data
        return [
            {"claim": "The Earth orbits the Sun", "confidence": 0.95},
            {"claim": "Water boils at 100 degrees Celsius at sea level", "confidence": 0.92}
        ]
    
    async def _verify_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a claim against trusted sources."""
        # Implementation would check external knowledge bases or APIs
        # Simplified example returns mock verification
        claim_text = claim["claim"]
        
        # In a real implementation, this would query factual databases
        async with aiohttp.ClientSession() as session:
            # Example API call (would be replaced with actual fact-checking service)
            # async with session.get(f"https://factcheck-api.example.com/verify?claim={claim_text}") as response:
            #     verification = await response.json()
            
            # Mock verification result
            verification = {
                "claim": claim_text,
                "accurate": True,
                "confidence": 0.9,
                "sources": ["Encyclopedia Britannica", "NASA"]
            }
            
        return verification
    
    def validate_config(self) -> None:
        """Validate the component configuration."""
        required_config = ["verification_threshold", "trusted_sources"]
        for config_key in required_config:
            if config_key not in self.config:
                raise ValueError(f"Missing required configuration key: {config_key}")
        
        # Verify configuration values
        threshold = self.config["verification_threshold"]
        if not (0 <= threshold <= 1):
            raise ValueError(f"verification_threshold must be between 0 and 1, got {threshold}")
```

## Advanced Configuration Examples

### Conditional Processing Flow

Configure a flow that uses different components based on content type:

```yaml
flows:
  - id: "adaptive_content_flow"
    name: "Adaptive Content Processing"
    description: "Adapts processing based on content type"
    modules:
      - id: "input_preprocessing"
        config_override: {}
      - id: "content_classification"
        config_override: {}
      - id: "conditional_router"
        config_override: {
          "routes": {
            "technical": ["technical_enhancement", "code_verification"],
            "business": ["business_enhancement", "fact_verification"],
            "creative": ["creative_enhancement", "tone_adjustment"]
          },
          "default_route": ["general_enhancement"]
        }
      - id: "quality_assurance"
        config_override: {}
```

### Parallel Processing Flow

Configure a flow that processes different aspects of content in parallel:

```yaml
flows:
  - id: "parallel_processing_flow"
    name: "Parallel Content Processing"
    description: "Processes content aspects in parallel for efficiency"
    modules:
      - id: "input_preprocessing"
        config_override: {}
      - id: "content_splitter"
        config_override: {
          "split_method": "semantic_sections"
        }
      - id: "parallel_processor"
        config_override: {
          "parallel_modules": [
            "grammar_check", 
            "tone_analysis", 
            "fact_verification"
          ],
          "max_parallel": 3
        }
      - id: "content_merger"
        config_override: {
          "merge_strategy": "incorporate_all_feedback"
        }
      - id: "final_polish"
        config_override: {}
```

## Best Practices

1. **Start with YAML Configuration**: Try to implement your component using just YAML configuration first
2. **Use Custom Code When Necessary**: Only implement custom Python code when needed for complex logic
3. **Reuse Existing Components**: Combine existing components in new ways before creating new ones
4. **Document Your Components**: Add detailed descriptions and example configurations
5. **Test in Isolation**: Test each new component individually before adding it to production flows
6. **Monitor Performance**: Keep track of component performance metrics and adjust as needed

## Troubleshooting

Common issues and solutions when creating custom processing components:

1. **Component Not Found**: Ensure the component is properly registered in the component registry
2. **Configuration Errors**: Validate all required configuration parameters are provided
3. **Flow Execution Failures**: Check that components are listed in the correct order
4. **Prompt Template Issues**: Verify that all referenced variables exist in the context
5. **Performance Problems**: Monitor component execution time and optimize slow components 