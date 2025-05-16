# Legal Consultation Processing Flow

## User Input
```
"I need advice on drafting a contract with a software vendor to ensure we maintain IP rights for any custom development. What legal terms should I include?"
```

## Processing Flow

### 1. Initial Request Processing
- `handle_request()` function receives the prompt, session_id, and user_id
- Session data is retrieved or created via `session_manager.get_or_create_session()`
- User profile retrieved: `user_profile = profile_store.get_user_profile(user_id)`
- Conversation memory loaded: `memory = session_manager.get_session_memory(session_id)`

### 2. NLP Processing
- Text is processed through `nlp_processor.process_text(prompt)`
  - Cleaned text using `_clean_text()` method
  - spaCy processing extracts entities, keywords, and structure
  - Detected entities: ["contract", "software vendor", "IP rights", "legal terms"]
  - Entity types mapped: ["LEGAL": "contract", "terms"]
  - Sentiment analysis: neutral sentiment (0.5)
  - Domain terms extracted: ["legal": ["contract", "terms"]]

### 3. Detection Rule Matching
- `process_message_with_rules()` evaluates the text against configured rules
- "legal_question" rule matched:
  - Keywords matched: ["legal", "contract", "terms"]
  - Required entities matched: ["LEGAL"]
  - Sentiment within range: [0.3, 0.7]
  - Confidence score: 0.85 (threshold: 0.6)
  - Matched action: "use_legal_adapter"

### 4. Action Execution
- `execute_action("use_legal_adapter", context)` is called
- `handle_adapter_selection()` processes the action:
  - Adapter "legal" is selected and activated
  - `active_adapter` is set to "legal"
  - Action result logged for monitoring

### 5. Chain Creation with Specialized Adapter
- `create_specialized_chain()` creates a chain with:
  - Base LLM: consultancy_bot.llm
  - Active adapter: "legal"
  - User profile included for personalization
  - Memory context included for conversation history

### 6. Response Generation
- Chain is invoked with the prompt, chat history, and user profile
- Legal adapter focuses response on legal considerations
- Raw response generated addressing contract terms, IP rights, etc.

### 7. Post-Processing
- Generated response is analyzed with `process_message_with_rules()`
- "legal_response_quality" rule matched
- `enhance_response` action triggered with "legal_response_quality" enhancement type

### 8. Response Enhancement
- `response_enhancer.enhance_response()` applies enhancements:
  - Domain-specific terminology added: ["jurisdiction", "indemnity", "warranty"]
  - Legal citations added:
    ```
    1. Harvard Business Review: 'Legal Strategies for Business' (2023)
    2. Journal of Business Law: 'Compliance Frameworks for SMEs' (2022)
    ```
  - Checked minimum length requirement (150 words)

### 9. Final Output Preparation
- Enhanced response saved to conversation memory
- Interaction logged via mlops.log_interaction()
- Final response returned to user

## Final Response (Sample)
```
To protect your intellectual property rights in a contract with a software vendor, you should include several key legal terms:

1. Intellectual Property Ownership: Clearly define that your company will own all custom development work, including source code, documentation, and derivative works.

2. Work-for-hire Clause: Specify that all work performed is considered "work-for-hire" under copyright law, ensuring your company's ownership of the deliverables.

3. Assignment Provision: Include an explicit assignment of all IP rights from the vendor to your company.

4. Confidentiality Terms: Define what constitutes confidential information and establish protection obligations.

5. License Limitations: Clarify what rights, if any, the vendor has to use the custom work in other projects.

6. Escrow Arrangements: Consider source code escrow for critical applications in case the vendor goes out of business.

7. Warranty Against Infringement: The vendor should warrant that their work doesn't infringe on third-party IP rights.

Key legal considerations include jurisdiction, indemnity, and warranty.

References:
1. Harvard Business Review: 'Legal Strategies for Business' (2023)
2. Journal of Business Law: 'Compliance Frameworks for SMEs' (2022)
```

## Performance Metrics Collected
- Request processing time: 2.3 seconds
- NLP feature extraction time: 0.4 seconds
- Rule matching time: 0.1 seconds
- LLM response generation time: 1.5 seconds
- Enhancement time: 0.3 seconds
- Total tokens used: 720 