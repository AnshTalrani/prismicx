# Decision Tree Guide

## What is a Decision Tree?

In our analysis-base microservice, a decision tree is a YAML/JSON specification that encodes domain-specific analytical logic, business rules, and decision-making strategies. Unlike processing templates which define the "how" of analysis (component sequence), decision trees define the "what" and "why" of analysis (specific analytical approaches and interpretations).

Decision trees allow domain experts to encode their knowledge without modifying code, making the system flexible and adaptable to different platforms and contexts.

## What Goes in a Decision Tree?

Decision trees should ONLY include:

✅ Domain-specific analytical logic  
✅ Platform-specific knowledge (Instagram vs. Etsy)  
✅ Business rules and conditions  
✅ Threshold values for classifications  
✅ Factor selection criteria  
✅ Analysis strategy selection  
✅ Interpretive frameworks  

Decision trees should NEVER include:

❌ Component sequencing logic  
❌ Technical implementation details  
❌ General processing flow  
❌ Resource allocation parameters  

## Tree Structure

A decision tree has this basic structure:

```yaml
name: "tree_name"
description: "Description of the tree's purpose"
version: "1.0"
root:
  condition: "expression_to_evaluate"
  branches:
    - value: "match_value"
      child:
        # Nested condition
        condition: "another_expression"
        branches:
          - value: "another_match"
            outcome:
              # Final outcome/result
              param1: value1
              param2: value2
          
    - value: "different_match"
      outcome:
        # Directly to outcome
        param1: value1
        param2: value2
    
    - default:
      # Default branch if no match
      outcome:
        param1: default_value1
        param2: default_value2
```

## Condition Expressions

Decision trees use condition expressions to evaluate context and determine which branch to follow:

1. **Simple property access**:
   ```yaml
   condition: "context.platform"
   ```

2. **Nested property access**:
   ```yaml
   condition: "metrics.engagement_rate"
   ```

3. **Comparison operations**:
   ```yaml
   condition: "metrics.engagement_rate > 0.05"
   ```

4. **Contains check**:
   ```yaml
   condition: "features.visual_elements contains 'high_contrast'"
   ```

5. **Multiple conditions** (in advanced trees):
   ```yaml
   condition: "metrics.engagement_rate > 0.05 AND context.content_type == 'product_showcase'"
   ```

## Outcome Structure

The outcome is what the decision tree produces after evaluating conditions. These outcomes are used by components to adjust their behavior:

```yaml
outcome:
  analysis_approach: "visual_factor_analysis"
  primary_metrics: ["scroll_stop_rate", "engagement_rate"]
  factor_categories: ["attention_capture", "visual_appeal"]
  reason: "High contrast elements indicate visual appeal is primary driver"
  confidence: 0.85
```

Different components may expect different fields in the outcome, but common ones include:
- `analysis_approach` - Which analytical method to use
- `primary_metrics` - Which metrics to focus on
- `factor_categories` - Which categories of factors to analyze
- `reason` - Explanation for the decision (helps with transparency)
- `confidence` - How confident we are in this determination

## Example Decision Trees

### Example 1: Instagram Performance Analysis Tree

```yaml
name: "instagram_performance_analysis"
description: "Decision tree for analyzing Instagram content performance"
version: "1.0"

root:
  condition: "context.content_type"
  branches:
    # Branch for product showcase content
    - value: "product_showcase"
      child:
        condition: "metrics.engagement_variance > 0.5"
        branches:
          # High variance in engagement metrics
          - value: true
            outcome:
              analysis_approach: "visual_factor_analysis"
              primary_metrics: ["scroll_stop_rate", "engagement_rate"]
              factor_categories: ["contrast", "color_scheme", "composition"]
              reason: "High performance variance indicates visual elements are key differentiators"
          
          # Low variance in engagement metrics
          - value: false
            outcome:
              analysis_approach: "timing_and_caption_analysis"
              primary_metrics: ["posting_time_performance", "caption_engagement"]
              factor_categories: ["time_of_day", "caption_sentiment", "hashtag_strategy"]
              reason: "Low visual variance suggests timing and text content are primary drivers"
    
    # Branch for lifestyle content
    - value: "lifestyle"
      child:
        condition: "metrics.audience_demographic"
        branches:
          - value: "gen_z_dominant"
            outcome:
              analysis_approach: "trend_alignment_analysis"
              primary_metrics: ["trending_topic_alignment", "authenticity_score"]
              factor_categories: ["authenticity", "trend_relevance"]
              reason: "Gen Z audience responds strongly to authenticity and trend alignment"
          
          - value: "millennial_dominant"
            outcome:
              analysis_approach: "value_proposition_analysis"
              primary_metrics: ["value_proposition_clarity", "aspiration_alignment"]
              factor_categories: ["aspiration", "lifestyle_alignment"]
              reason: "Millennial audience responds to clear value proposition and aspirational content"
          
          - default:
            outcome:
              analysis_approach: "standard_engagement_analysis"
              primary_metrics: ["engagement_rate", "save_rate"]
              factor_categories: ["general_appeal", "content_quality"]
              reason: "Default approach for mixed demographics"
    
    # Default branch for other content types
    - default:
      outcome:
        analysis_approach: "standard_content_analysis"
        primary_metrics: ["engagement_rate", "reach", "shares"]
        factor_categories: ["general_visual", "audience_match"]
        reason: "Standard analysis for unspecified content type"
```

### Example 2: Factor Effectiveness Analysis Tree

```yaml
name: "factor_effectiveness_analysis"
description: "Analyzes the effectiveness of cognitive marketing factors"
version: "2.0"

root:
  condition: "context.platform"
  branches:
    - value: "instagram"
      child:
        condition: "metrics.effectiveness_trend"
        branches:
          - value: "declining"
            outcome:
              analysis_approach: "saturation_analysis"
              primary_metrics: ["usage_frequency", "audience_familiarity"]
              factor_categories: ["attention", "novelty"]
              saturation_threshold: 0.75
              reason: "Declining effectiveness often indicates factor saturation"
          
          - value: "stable"
            outcome:
              analysis_approach: "implementation_quality_analysis"
              primary_metrics: ["quality_score", "consistency_score"]
              factor_categories: ["execution", "quality"]
              reason: "Stable effectiveness suggests focus on implementation quality"
          
          - value: "increasing"
            outcome:
              analysis_approach: "amplification_analysis"
              primary_metrics: ["growth_rate", "audience_expansion"]
              factor_categories: ["reach", "amplification"]
              reason: "Increasing effectiveness indicates potential for strategic amplification"
    
    - value: "etsy"
      child:
        # Etsy-specific logic here
        condition: "metrics.conversion_impact"
        branches:
          - value: "> 0.1"
            outcome:
              analysis_approach: "high_converting_factor_analysis"
              primary_metrics: ["conversion_rate", "add_to_cart_rate"]
              factor_categories: ["trust", "urgency"]
              reason: "High conversion impact factors should be analyzed for product optimization"
          
          - default:
            outcome:
              analysis_approach: "standard_marketplace_analysis"
              primary_metrics: ["click_through_rate", "listing_quality_score"]
              factor_categories: ["visibility", "listing_quality"]
              reason: "Standard analysis for marketplace factors"
    
    - default:
      outcome:
        analysis_approach: "general_factor_analysis"
        primary_metrics: ["performance_score", "consistency_score"]
        factor_categories: ["general_effectiveness"]
        reason: "Generic approach for unspecified platforms"
```

### Example 3: Diagnostic Root Cause Tree

```yaml
name: "instagram_causal_factors"
description: "Determines causal relationships for Instagram performance"
version: "2.0"

root:
  condition: "context.diagnostic_approach" 
  branches:
    - value: "visual_factor_analysis"
      child:
        condition: "features.dominant_elements"
        branches:
          - value: "contains:high_contrast"
            outcome:
              causal_hypothesis: "visual_attention_driver"
              evidence_pattern: "contrast_engagement_correlation"
              confidence: 0.85
              explanation: "High contrast is driving increased attention and scroll-stop rate"
              recommended_metrics: ["contrast_score", "scroll_stop_rate"]
          
          - value: "contains:blue_dominant"
            outcome:
              causal_hypothesis: "trust_signal"
              evidence_pattern: "color_trust_correlation"
              confidence: 0.65
              explanation: "Blue-dominant imagery correlates with higher trust metrics"
              recommended_metrics: ["trust_score", "brand_sentiment"]
          
          - value: "contains:faces"
            outcome:
              causal_hypothesis: "human_connection"
              evidence_pattern: "face_engagement_correlation"
              confidence: 0.78
              explanation: "Human faces create emotional connection driving engagement"
              recommended_metrics: ["emotional_response", "comment_sentiment"]
    
    - value: "timing_and_caption_analysis"
      child:
        condition: "metrics.posting_time_segment"
        branches:
          - value: "evening"
            outcome:
              causal_hypothesis: "leisure_browsing_alignment"
              evidence_pattern: "evening_engagement_pattern"
              confidence: 0.72
              explanation: "Evening posts align with leisure browsing behavior"
              recommended_metrics: ["time_on_post", "save_rate"]
          
          - value: "morning"
            outcome:
              causal_hypothesis: "commute_browsing_pattern"
              evidence_pattern: "morning_engagement_spikes"
              confidence: 0.68
              explanation: "Morning posts catch commute browsing audience"
              recommended_metrics: ["scroll_stop_rate", "brief_engagement_metrics"]
    
    - default:
      outcome:
        causal_hypothesis: "general_quality_factors"
        evidence_pattern: "quality_engagement_correlation"
        confidence: 0.50
        explanation: "General content quality appears to be primary factor"
        recommended_metrics: ["quality_score", "engagement_rate"]
```

## Best Practices

1. **Start Simple**: Begin with a few key conditions before adding complexity.

2. **Use Clear Conditions**: Make condition expressions readable and unambiguous.

3. **Provide Meaningful Outcomes**: Include explanations and reasons in outcomes.

4. **Balance Depth**: Keep trees reasonably deep (3-4 levels maximum).

5. **Consider Default Cases**: Always include default branches for unexpected inputs.

6. **Document Domain Knowledge**: Use descriptions and comments to explain the logic.

7. **Version Your Trees**: Increment version numbers when making significant changes.

8. **Validate With Experts**: Have domain experts review your trees for accuracy.

9. **Test with Different Inputs**: Ensure your tree handles various input scenarios.

## Tree Validation

Before submitting your decision tree, check that it:

- Contains domain-specific knowledge, not technical implementation details
- Has clear, unambiguous conditions
- Includes appropriate default branches
- Provides complete outcomes with necessary parameters
- Has explanations/reasons for key decisions
- Follows naming conventions
- Is validated with domain experts

## Next Steps

After creating your decision tree, ensure it works correctly with the corresponding processing template. See the [Processing Template Guide](./processing_template_guide.md) if you haven't already created a template.

Remember that the power of our system comes from the separation of concerns between generic processing templates and domain-specific decision trees. This allows domain experts to focus on their specialized knowledge while maintaining a consistent technical infrastructure. 