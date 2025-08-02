# Strategy Development with Agent Delegation Flow

## User Input
```
"Could you provide a sample strategic plan for entering the European market with our SaaS product? We're a US-based company with 50 employees and $5M annual revenue."
```

## Processing Flow

### 1. Initial Request Processing
- `handle_request()` function receives the prompt, session_id, and user_id
- Session and user data retrieved:
  - `session = session_manager.get_or_create_session()`
  - `user_profile = profile_store.get_user_profile(user_id)`
  - `memory = session_manager.get_session_memory(session_id)`

### 2. NLP Processing
- Text is processed through `nlp_processor.process_text(prompt)`
  - Cleaned text using `_clean_text()` method
  - Entities extracted: ["sample", "strategic plan", "European market", "SaaS product", "US-based company", "50 employees", "$5M annual revenue"]
  - Entity types mapped: 
    - ["DOCUMENT_TYPE": "plan", "strategy"]
    - ["BUSINESS": "market", "product", "company"]
  - Domain terms extracted: 
    - ["strategy": ["strategic", "market"]]
    - ["finance": ["revenue"]]
  - Request type: "question"
  - Urgency: low (0.2)

### 3. Detection Rule Matching
- `process_message_with_rules()` evaluates the text against configured rules
- Two rules matched:
  1. "sample_request" rule (primary match):
     - Keywords matched: ["sample", "provide a sample", "strategic plan"]
     - Required entities matched: ["DOCUMENT_TYPE": "plan", "strategy"]
     - Confidence score: 0.85 (threshold: 0.7)
     - Matched action: "delegate_to_agent"
  
  2. "strategy_question" rule (secondary match):
     - Keywords matched: ["strategic", "market"]
     - Required entities matched: ["BUSINESS"]
     - Confidence score: 0.75 (threshold: 0.6)
     - Matched action: "use_strategy_adapter" (not executed immediately)

### 4. Primary Action Execution: Agent Delegation
- `execute_action("delegate_to_agent", context)` is called
- `handle_agent_delegation()` processes the action:
  - Creates AgentClient instance
  - Urgency set to "high" from config
  - Sends request to specialized agent service:
    ```python
    agent_response = await agent_client.send_request(
        text=prompt,
        user_id=user_id,
        session_id=session_id,
        urgency="high"
    )
    ```
  - Checks success criteria:
    - Status == "success"
    - Content is present
  - In this case, agent service returns an error status

### 5. Fallback Action Execution
- Delegation failure detected, fallback action triggered
- Retrieves fallback action from config: "use_strategy_adapter"
- Executes fallback action:
  ```python
  fallback_result = await consultancy_bot.execute_action(
      action_name="use_strategy_adapter",
      context={
          "rule_name": "sample_request",
          "action": "use_strategy_adapter",
          "prompt": prompt,
          "user_id": user_id,
          "session_id": session_id,
          "memory": memory
      }
  )
  ```
- Strategy adapter is activated: `active_adapter = "strategy"`

### 6. Chain Creation with Strategy Adapter
- `create_specialized_chain()` creates a chain with:
  - Base LLM: consultancy_bot.llm
  - Active adapter: "strategy"
  - User profile included for personalization
  - Memory context included for conversation history
  - Strategy-specific retrieval domains activated

### 7. Response Generation
- Chain is invoked with the prompt, chat history, and user profile
- Strategy adapter focuses response on strategic planning
- Raw response generated providing a sample strategic plan

### 8. Post-Processing
- Generated response is analyzed with `process_message_with_rules()`
- "strategy_response_quality" rule matched
- `enhance_response` action triggered with "strategy_response_quality" enhancement type

### 9. Response Enhancement
- `response_enhancer.enhance_response()` applies enhancements:
  - Domain-specific terminology added: ["market positioning", "value proposition", "competitive advantage"]
  - Strategic framework added: "Porter's Five Forces"
  - Strategy citations added:
    ```
    1. Harvard Business Review: 'Competitive Strategy' (Porter, updated edition)
    2. McKinsey Quarterly: 'Strategic Planning in Volatile Markets' (2023)
    ```
  - Checked minimum length requirement (250 words)

### 10. Final Output Preparation
- Enhanced response saved to conversation memory
- Interaction logged via mlops.log_interaction() with action history
- Final response returned to user

## Sequence Diagram
```
User → handle_request → NLPProcessor → RuleMatching → AgentDelegation (fails) 
  → FallbackAction → StrategyAdapter → ResponseGeneration → ResponseEnhancement → User
```

## Final Response (Sample)
```
# Strategic Plan for European Market Entry - SaaS Product

## Executive Summary
This strategic plan outlines the approach for a US-based SaaS company ($5M revenue, 50 employees) to enter the European market. The plan provides a structured approach to establishing market presence, building customer relationships, and scaling operations in the EU region.

## 1. Market Analysis

### Target Markets
- Primary: UK, Germany, Netherlands (English proficiency, tech adoption)
- Secondary: France, Spain, Italy (phased approach after initial success)

### Competitive Landscape
- Identify local and global competitors already operating in Europe
- Map competitive positioning and unique selling propositions
- Analyze pricing strategies in European markets

## 2. Go-to-Market Strategy

### Entry Model
- Initial: Digital-first approach with localized marketing and remote sales
- Phase 2: Strategic partnerships with local technology providers
- Phase 3: Establish small office presence in primary markets

### Distribution Channels
- Direct sales team with remote capabilities
- Partner network development
- Digital marketing and self-service purchase options

### Localization Requirements
- Product features and interface translation
- Documentation and support materials
- Pricing structure (currency, VAT considerations)

## 3. Legal and Compliance

### GDPR Compliance
- Data protection impact assessment
- Privacy policy updates
- User consent mechanisms implementation

### Business Structure
- Determine optimal legal entity structure
- Tax implications and reporting requirements
- Employment law considerations

## 4. Financial Projections

### Investment Required
- Initial entry: $250,000-350,000
- Break-even timeline: 18-24 months
- 3-year ROI projection: 2.5x investment

### Revenue Targets
- Year 1: $500,000
- Year 2: $1.2M
- Year 3: $2.5M

## 5. Implementation Roadmap

### Phase 1: Preparation (Months 1-3)
- Market research finalization
- Legal and compliance setup
- Initial localization

### Phase 2: Soft Launch (Months 4-6)
- Early adopter program
- Partnership development
- Marketing campaign initiation

### Phase 3: Full Market Entry (Months 7-12)
- Sales team expansion
- Marketing intensification
- Customer success team development

You can analyze this using the Porter's Five Forces framework:
- Supplier Power: [Specific insights would be derived from your situation]
- Buyer Power: [Specific insights would be derived from your situation]
- Competitive Rivalry: [Specific insights would be derived from your situation]
- Threat of Substitution: [Specific insights would be derived from your situation]
- Threat of New Entry: [Specific insights would be derived from your situation]

This strategic market positioning will help establish your value proposition and create sustainable competitive advantage in the European market.

References:
1. Harvard Business Review: 'Competitive Strategy' (Porter, updated edition)
2. McKinsey Quarterly: 'Strategic Planning in Volatile Markets' (2023)
```

## Performance Metrics Collected
- Request processing time: 3.2 seconds
- NLP feature extraction time: 0.5 seconds
- Rule matching time: 0.15 seconds
- Agent delegation attempt: 0.7 seconds
- Fallback processing time: 0.2 seconds
- LLM response generation time: 1.3 seconds
- Enhancement time: 0.35 seconds
- Total tokens used: 1150 