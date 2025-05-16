# Urgent Request with Sentiment Analysis Flow

## User Input
```
"We urgently need to respond to a serious competitor threat. They just launched a pricing campaign that's targeting our top customers with 30% discounts. We need a response strategy ASAP!"
```

## Processing Flow

### 1. Initial Request Processing
- `handle_request()` function receives the prompt, session_id, and user_id
- Session data retrieved: `session = session_manager.get_or_create_session()`
- User profile retrieved: `user_profile = profile_store.get_user_profile(user_id)`
- Memory loaded: `memory = session_manager.get_session_memory(session_id)`

### 2. NLP Processing with Urgency and Sentiment Focus
- Text is processed through `nlp_processor.process_text(prompt)`
  - Cleaned text using `_clean_text()` method
  - Entities extracted: ["competitor threat", "pricing campaign", "top customers", "30% discounts", "response strategy"]
  - Entity types mapped: ["BUSINESS": "competitor", "customers", "strategy"]
  - Sentiment analysis performed:
    ```python
    sentiment = {
        "polarity": -0.3,  # Negative sentiment
        "positive_count": 1,
        "negative_count": 3,
        "negation_count": 0,
        "assessment": "negative"
    }
    ```
  - Urgency analysis performed:
    ```python
    urgency_terms = {
        "high": ["urgently", "ASAP", "serious"],
        "medium": ["need", "respond"],
        "low": []
    }
    urgency_score = 0.85  # High urgency detected
    ```
  - Domain terms extracted: ["strategy": ["strategy", "competitor"]]
  - Request type: "instruction" (action-oriented)

### 3. Detection Rule Matching with Urgency Prioritization
- `process_message_with_rules()` evaluates the text against configured rules
- "strategy_question" rule matched:
  - Keywords matched: ["strategy", "competitor"]
  - Required entities matched: ["BUSINESS"]
  - Confidence score: 0.75 (threshold: 0.6)
  - Matched action: "use_strategy_adapter"
  - Urgency flag set to "high" based on NLP urgency score

### 4. Prioritized Action Execution
- `execute_action("use_strategy_adapter", context)` is called with urgency context
- `handle_adapter_selection()` processes the action with high priority:
  - Adapter "strategy" is selected and activated
  - `active_adapter` is set to "strategy"
  - Priority flag passed to the LLM pipeline
  - Action result stored with urgency metadata

### 5. Expedited Chain Creation
- `create_specialized_chain()` creates a chain with:
  - Base LLM: consultancy_bot.llm
  - Active adapter: "strategy"
  - Priority processing flag set to "high"
  - Reduced token optimization for faster response
  - Temperature lowered to 0.5 for more focused output

### 6. Response Generation with Prioritization
- Chain is invoked with the prompt, chat history, and urgency context
- Strategy adapter focuses on competitive response strategies
- Raw response generated with emphasis on immediate actions
- Processing prioritized in queue based on urgency flag

### 7. Sentiment-Aware Post-Processing
- Generated response analyzed for tone matching through `process_message_with_rules()`
- Sentiment-appropriate language enforced
- "strategy_response_quality" rule matched with urgency modifier
- `enhance_response` action triggered with context: `{"urgency": "high", "sentiment": "negative"}`

### 8. Urgency-Oriented Response Enhancement
- `response_enhancer.enhance_response()` applies targeted enhancements:
  - Concise, action-oriented phrasing prioritized
  - Critical strategy terminology added for clarity
  - Framework section added but kept brief
  - Citations limited to most relevant references
  - Format optimized for readability and quick implementation

### 9. Expedited Output Preparation
- Enhanced response saved to conversation memory
- Urgent interaction logged via mlops.log_interaction() with urgency flag
- Priority notification sent to monitoring dashboard via special event
- Final response returned to user with minimal latency

## Sequence Diagram with Urgency Pathway
```
User → Prioritized Processing → Urgency Analysis → Sentiment Analysis →
Expedited Rule Matching → Fast-Path Adapter Selection → Priority Chain Creation →
Urgent Response Generation → Concise Enhancement → Expedited Delivery → User
```

## Final Response (Sample)
```
# IMMEDIATE COMPETITIVE RESPONSE STRATEGY

## SITUATION ANALYSIS
You're facing a direct competitive threat with 30% discounts targeting your key customers. This requires immediate action to prevent customer loss and revenue impact.

## RECOMMENDED IMMEDIATE ACTIONS (24-48 HOURS)

1. **Customer Outreach** - HIGHEST PRIORITY
   - Contact all targeted top customers immediately
   - Emphasize your value proposition beyond price
   - Consider offering existing customers loyalty incentives (not necessarily matching full discount)

2. **Targeted Counter-Offer** - HIGH PRIORITY
   - Develop a targeted counter-offer for at-risk customers
   - Focus on total value (service, support, quality) not just price
   - Consider strategic discounts for most vulnerable accounts (15-20%)
   
3. **Sales Team Mobilization**
   - Equip sales team with competitive talking points
   - Authorize limited negotiation flexibility
   - Redirect sales resources to focus on defending key accounts

## SHORT-TERM STRATEGY (1-2 WEEKS)

4. **Value Enhancement**
   - Identify and communicate additional value you can offer quickly
   - Bundle additional services at minimal cost to improve value perception
   - Emphasize competitor weaknesses (reliability, support, quality)

5. **Strategic Price Evaluation**
   - Conduct rapid analysis of sustainable price adjustments
   - Consider segment-specific pricing strategy adjustments
   - Evaluate targeted counter-promotions

## LONGER-TERM RESPONSE (2-4 WEEKS)

6. **Competitive Intelligence**
   - Determine if this is a short-term promotion or permanent change
   - Assess competitor financial sustainability at 30% discount
   - Analyze competitor's strategic intent and potential next moves

7. **Value Proposition Refinement**
   - Strengthen non-price differentiation
   - Develop communication strategy emphasizing total cost of ownership

This competitive market positioning requires immediate action to protect your customer base and maintain your market position against this aggressive price competition.

References:
1. Harvard Business Review: 'Responding to Competitive Price Cuts' (2022)
```

## Performance Metrics Collected
- Request prioritization time: 0.05 seconds
- Urgency detection time: 0.2 seconds
- NLP feature extraction time: 0.4 seconds
- Rule matching time: 0.1 seconds
- LLM response generation time: 1.2 seconds (expedited)
- Enhancement time: 0.2 seconds (optimized)
- Total tokens used: 680
- End-to-end latency: 2.15 seconds (vs. 2.8s average) 