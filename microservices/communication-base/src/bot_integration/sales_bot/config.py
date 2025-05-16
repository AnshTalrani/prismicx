"""Configuration for the sales bot."""

SALES_BOT_CONFIG = {
    "bot_type": "sales",
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.7,
    "memory_tokens": 1000,
    "system_message": """You are an expert sales consultant who helps customers find the perfect 
    products. Use your knowledge of our offerings to match customer needs with ideal solutions, 
    highlighting key benefits and addressing potential concerns.""",
    "sources": ["product_catalog", "customer_reviews", "competitive_analysis"],
    "doc_paths": {
        "product_docs": "data/products/",
        "campaign_data": "data/campaigns/",
        "competitor_data": "data/competitors/"
    },
    "lora_adapter_path": "path/to/sales/adapter",
    
    # Product domains
    "product_domains": ["clothing", "jewelry", "accessories"],
    
    # Campaign stages
    "campaign_stages": {
        "awareness": {
            "description": "Initial stage where customer learns about products",
            "focus": "Information and education",
            "model_params": {
                "temperature": 0.6,
                "top_p": 0.85
            }
        },
        "interest": {
            "description": "Customer shows interest in specific products",
            "focus": "Benefits and features",
            "model_params": {
                "temperature": 0.7,
                "max_length": 640
            }
        },
        "decision": {
            "description": "Customer is ready to make a purchase decision",
            "focus": "Conversion and commitment",
            "model_params": {
                "temperature": 0.8,
                "top_p": 0.95
            }
        }
    },
    
    # Conversation states for the sales bot
    "conversation": {
        "initial_state": "greeting",
        "states": {
            "greeting": {
                "description": "Initial greeting and building rapport",
                "default_response": "Hello! How can I help you today?",
                "adapters": ["sales"],
                "use_rag": False,
                "on_entry": {
                    "message": "Welcome to our sales assistance! I'm here to help you find the perfect product.",
                    "context_updates": {"greeted": True}
                },
                "on_exit": {
                    "context_updates": {"completed_greeting": True}
                },
                "transitions": [
                    {
                        "target": "discovery",
                        "conditions": [
                            {"type": "message_count", "threshold": 1}
                        ]
                    }
                ]
            },
            "discovery": {
                "description": "Discover customer needs and pain points",
                "default_response": "What challenges are you facing that our solution might help with?",
                "adapters": ["sales"],
                "use_rag": True,
                "on_entry": {
                    "message": "To help you better, I'd like to understand your specific needs.",
                    "context_updates": {"discovery_started": True}
                },
                "transitions": [
                    {
                        "target": "qualification",
                        "conditions": [
                            {"type": "entity_present", "entity_name": "pain_point"},
                            {"type": "message_count", "threshold": 2}
                        ]
                    }
                ]
            },
            "qualification": {
                "description": "Qualify the prospect",
                "default_response": "Can you tell me a bit about your timeline and budget for this project?",
                "adapters": ["sales"],
                "use_rag": False,
                "on_entry": {
                    "context_updates": {"qualification_started": True}
                },
                "transitions": [
                    {
                        "target": "presentation",
                        "conditions": [
                            {"type": "entity_present", "entity_name": "budget"},
                            {"type": "entity_present", "entity_name": "timeline"}
                        ]
                    },
                    {
                        "target": "objection_handling",
                        "conditions": [
                            {"type": "sentiment", "range": [0.0, 0.4]}
                        ]
                    }
                ]
            },
            "presentation": {
                "description": "Present solution",
                "default_response": "Based on what you've told me, our solution offers several benefits that address your needs.",
                "adapters": ["sales"],
                "use_rag": True,
                "on_entry": {
                    "context_updates": {"presentation_started": True}
                },
                "transitions": [
                    {
                        "target": "objection_handling",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["expensive", "price", "costly", "budget", "too much"]}
                        ]
                    },
                    {
                        "target": "closing_deal",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["interested", "sounds good", "like that", "want to"]}
                        ]
                    }
                ]
            },
            "objection_handling": {
                "description": "Handle objections",
                "default_response": "I understand your concern. Let me address that.",
                "adapters": ["sales", "persuasion"],
                "use_rag": True,
                "on_entry": {
                    "context_updates": {"objection_handling_started": True}
                },
                "transitions": [
                    {
                        "target": "closing_deal",
                        "conditions": [
                            {"type": "sentiment", "range": [0.6, 1.0]}
                        ]
                    },
                    {
                        "target": "presentation",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["tell me more", "more information", "details"]}
                        ]
                    }
                ]
            },
            "closing_deal": {
                "description": "Close the deal",
                "default_response": "Would you like to move forward with a demonstration of our solution?",
                "adapters": ["sales", "persuasion"],
                "use_rag": False,
                "on_entry": {
                    "context_updates": {"closing_started": True}
                },
                "transitions": [
                    {
                        "target": "follow_up",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["think about it", "get back", "later", "not now"]}
                        ]
                    },
                    {
                        "target": "closing",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["yes", "sure", "proceed", "book", "schedule"]}
                        ]
                    }
                ]
            },
            "follow_up": {
                "description": "Follow up after conversation",
                "default_response": "I'm following up on our conversation. Have you had a chance to consider our solution?",
                "adapters": ["sales"],
                "use_rag": False,
                "on_entry": {
                    "context_updates": {"follow_up_scheduled": True}
                },
                "transitions": [
                    {
                        "target": "closing",
                        "conditions": [
                            {"type": "message_count", "threshold": 2}
                        ]
                    }
                ]
            },
            "closing": {
                "description": "Close the conversation",
                "default_response": "Thank you for your time today. Is there anything else I can help you with?",
                "adapters": ["sales"],
                "use_rag": False,
                "on_entry": {
                    "context_updates": {"conversation_closing": True}
                },
                "transitions": []
            }
        }
    },
    
    # Memory settings
    "memory": {
        "window_size": 15,
        "summary_interval": 8,
        "max_tokens": 1500,
        "timeout": 1800,  # 30 minutes
        "summarization_prompt": """As a sales consultant, summarize the key points, 
        customer interests, and potential objections from this conversation."""
    },
    
    # Response settings
    "response": {
        "style_matching": True,
        "anti_ai_patterns": True,
        "persuasive_elements": True,
        "benefits_focused": True
    },
    
    # Session settings
    "session": {
        "timeout": 1800,  # 30 minutes
        "extend_on_activity": True,
        "max_duration": 3600  # 1 hour
    },
    
    # Chain configuration
    "chain_config": {
        "retrieval": {
            "type": "hybrid",
            "k": 3,
            "score_threshold": 0.65,
            "reranking": True
        },
        "prompt": {
            "style": "sales_consultant",
            "components": ["product_info", "customer_profile", "history"],
            "anti_ai": True
        },
        "memory": {
            "type": "enhanced",
            "window_size": 15,
            "summary_interval": 8
        }
    },
    
    # NLP features configuration
    "analysis_config": {
        "nlp_features": {
            "required": ["entities", "sentiment", "intentions"],
            "optional": ["urgency", "price_sensitivity"]
        },
        "templates": {
            "message": {
                "path": "templates/sales/message_analysis.json",
                "components": ["buying_signals", "objections", "interests"]
            },
            "conversation": {
                "path": "templates/sales/conversation_analysis.json",
                "components": ["profile", "preferences", "objections"]
            }
        },
        "patterns": {
            "buying_signals": ["interested in", "how much", "when can I"],
            "objections": ["too expensive", "not sure", "need to think"]
        }
    },
    
    # Detection rules
    "detection_rules": {
        "product_interest": {
            "enabled": True,
            "description": "Detects when a user expresses interest in a product",
            "keywords": [
                "interested in", "looking for", "do you have", "searching for", 
                "want to buy", "considering", "thinking about purchasing",
                "tell me about", "show me", "how much is", "price of", "cost"
            ],
            "required_entities": ["PRODUCT_TYPE"],
            "confidence_threshold": 0.6,
            "action": "product_recommendation"
        },
        "price_objection": {
            "enabled": True,
            "description": "Detects price objections",
            "keywords": [
                "expensive", "costs too much", "high price", "overpriced",
                "can't afford", "budget", "cheaper", "discount", "sale",
                "more affordable", "price is high", "too much money"
            ],
            "sentiment_range": [0.1, 0.4],  # Negative sentiment
            "confidence_threshold": 0.65,
            "action": "handle_price_objection"
        },
        "ready_to_purchase": {
            "enabled": True,
            "description": "Detects readiness to purchase",
            "keywords": [
                "buy now", "purchase", "add to cart", "checkout", "order",
                "payment", "get it now", "sign up", "subscribe", "where can I buy",
                "how do I buy", "ready to buy", "take it"
            ],
            "sentiment_range": [0.6, 1.0],  # Positive sentiment
            "confidence_threshold": 0.7,
            "action": "facilitate_purchase" 
        },
        "competitor_mention": {
            "enabled": True,
            "description": "Detects when a competitor is mentioned",
            "keywords": [
                "competitor names to be filled in",
                "other brand", "different company", "instead of you",
                "compare with", "better than your", "also looking at"
            ],
            "confidence_threshold": 0.65,
            "action": "handle_competition_comparison"
        },
        "follow_up_needed": {
            "enabled": True,
            "description": "Detects when follow-up is needed",
            "keywords": [
                "think about it", "get back to you", "contact later",
                "not ready", "need time", "consider it", "sleep on it",
                "email me", "call me", "later", "tomorrow", "next week"
            ],
            "confidence_threshold": 0.6,
            "action": "schedule_follow_up"
        }
    },
    
    # Action definitions
    "actions": {
        "product_recommendation": {
            "enabled": True,
            "description": "Recommends products based on detected interests",
            "retrieval_domains": ["product_catalog"],
            "personalized": True,
            "compare_options": True
        },
        "handle_price_objection": {
            "enabled": True,
            "description": "Addresses price concerns with value-focused messaging",
            "value_emphasis": True,
            "alternative_options": True,
            "financing_info": True
        },
        "facilitate_purchase": {
            "enabled": True,
            "description": "Guides customer through purchase process",
            "steps": ["confirm_selection", "provide_checkout_link", "suggest_addons"],
            "urgency": "medium"
        },
        "handle_competition_comparison": {
            "enabled": True,
            "description": "Addresses comparisons with competitors",
            "retrieval_domains": ["competitive_analysis"],
            "highlight_advantages": True,
            "acknowledge_alternatives": True
        },
        "schedule_follow_up": {
            "enabled": True,
            "description": "Sets up follow-up contact",
            "channels": ["email", "notification"],
            "timings": {
                "default": 86400,  # 24 hours
                "high_interest": 3600,  # 1 hour
                "low_interest": 259200  # 3 days
            }
        }
    },
    
    # Response enhancement configurations
    "response_enhancements": {
        "product_focus": {
            "description": "Enhances product-focused responses",
            "add_features": True,
            "add_benefits": True,
            "add_social_proof": True,
            "min_length": 150
        },
        "objection_handling": {
            "description": "Enhances objection-handling responses",
            "acknowledge_concern": True,
            "reframe_positively": True,
            "provide_alternatives": True,
            "min_length": 200
        },
        "closing_focus": {
            "description": "Enhances responses focused on closing sales",
            "clear_cta": True,
            "urgency_elements": True,
            "reassurance": True,
            "min_length": 150
        }
    },
    
    # Product terminology by category
    "product_terminology": {
        "clothing": ["fabric", "size", "cut", "fit", "style", "collection", "season", 
                    "material", "care", "wash", "wear", "pattern", "design"],
        "jewelry": ["metal", "stone", "carat", "clarity", "cut", "setting", "band", 
                   "chain", "clasp", "finish", "polish", "certification", "appraisal"],
        "accessories": ["material", "design", "size", "style", "function", "feature", 
                       "compatibility", "care", "use", "utility", "portability"]
    },
    
    # Sales techniques by stage
    "sales_techniques": {
        "awareness": [
            {"name": "Problem-Solution", "pattern": "Identify a problem, then present product as solution"},
            {"name": "Education-Based", "pattern": "Provide valuable information before selling"},
            {"name": "Storytelling", "pattern": "Share relatable stories about product benefits"}
        ],
        "interest": [
            {"name": "Feature-Benefit", "pattern": "Connect each feature to a specific benefit"},
            {"name": "Social Proof", "pattern": "Share testimonials and reviews from satisfied customers"},
            {"name": "Comparison", "pattern": "Favorably compare products to alternatives"}
        ],
        "decision": [
            {"name": "Assumptive Close", "pattern": "Assume the sale will happen in your language"},
            {"name": "Urgency Creation", "pattern": "Create time-limited reasons to buy now"},
            {"name": "Choice Close", "pattern": "Offer choices between products rather than yes/no"}
        ]
    },
    
    # Entity types for NLP
    "entity_types": {
        "PRODUCT_TYPE": ["shirt", "dress", "pants", "shoes", "ring", "necklace", "bracelet", "bag", "wallet", "watch"],
        "PRICE_POINT": ["cheap", "expensive", "affordable", "luxury", "budget", "high-end", "premium", "discount"],
        "SIZE": ["small", "medium", "large", "S", "M", "L", "XL", "size"],
        "COLOR": ["red", "blue", "green", "black", "white", "yellow", "purple", "pink", "brown", "gray"],
        "MATERIAL": ["cotton", "silk", "leather", "gold", "silver", "platinum", "diamond", "metal", "fabric"],
        "OCCASION": ["casual", "formal", "business", "wedding", "party", "everyday", "special", "gift"],
        "BUYING_STAGE": ["researching", "comparing", "deciding", "purchasing", "browsing", "shopping"]
    },
    
    # Model parameters
    "model_params": {
        "temperature": 0.7,
        "max_length": 512,
        "top_p": 0.9,
        "top_k": 50
    }
} 