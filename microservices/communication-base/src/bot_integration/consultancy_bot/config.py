"""Configuration for the consultancy bot."""

CONSULTANCY_BOT_CONFIG = {
    "bot_type": "consultancy",
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.7,
    "memory_tokens": 1000,
    "system_message": """You are an expert business consultant with deep knowledge in 
    strategy, operations, and digital transformation. Help clients analyze their business 
    challenges and provide actionable recommendations.""",
    "sources": ["business_cases", "industry_reports", "best_practices"],
    "doc_paths": {
        "legal_docs": "data/legal/",
        "company_data": "data/company/",
        "expert_insights": "data/insights/"
    },
    "lora_adapter_path": "path/to/consultancy/adapter",
    "analysis": {
        "focus_areas": ["strategy", "operations", "finance", "marketing"],
        "expertise_domains": ["legal", "marketing", "social_media"],
        "covert_patterns": True,
        "delegation_enabled": True
    },
    
    # Conversation states for the consultancy bot
    "conversation": {
        "initial_state": "greeting",
        "states": {
            "greeting": {
                "description": "Initial greeting and setting the tone",
                "default_response": "Hello! I'm here to help with your business challenges. What brings you here today?",
                "adapters": ["consultant"],
                "use_rag": False,
                "on_entry": {
                    "message": "Welcome to our business consultancy. I'm here to help analyze your challenges and provide strategic recommendations.",
                    "context_updates": {"greeted": True}
                },
                "transitions": [
                    {
                        "target": "problem_identification",
                        "conditions": [
                            {"type": "message_count", "threshold": 1}
                        ]
                    }
                ]
            },
            "problem_identification": {
                "description": "Identify the core problems",
                "default_response": "Can you tell me more about the challenges you're facing?",
                "adapters": ["consultant", "active_listening"],
                "use_rag": True,
                "on_entry": {
                    "context_updates": {"problem_identification_started": True}
                },
                "transitions": [
                    {
                        "target": "analysis",
                        "conditions": [
                            {"type": "entity_present", "entity_name": "business_problem"},
                            {"type": "message_count", "threshold": 2}
                        ]
                    }
                ]
            },
            "analysis": {
                "description": "Analyze the situation",
                "default_response": "Based on what you've shared, let me analyze this situation further.",
                "adapters": ["consultant", "hypnosis"],
                "use_rag": True,
                "on_entry": {
                    "context_updates": {"analysis_started": True}
                },
                "transitions": [
                    {
                        "target": "recommendation",
                        "conditions": [
                            {"type": "message_count", "threshold": 3},
                            {"type": "keyword_match", "keywords": ["solution", "recommend", "what should", "next steps", "how to"]}
                        ]
                    },
                    {
                        "target": "problem_identification",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["another issue", "different problem", "also facing"]}
                        ]
                    }
                ]
            },
            "recommendation": {
                "description": "Provide recommendations",
                "default_response": "Here are my recommendations based on your situation.",
                "adapters": ["consultant", "persuasion"],
                "use_rag": True,
                "on_entry": {
                    "context_updates": {"recommendation_started": True}
                },
                "transitions": [
                    {
                        "target": "implementation_planning",
                        "conditions": [
                            {"type": "sentiment", "range": [0.6, 1.0]},
                            {"type": "keyword_match", "keywords": ["implement", "execute", "how to", "next steps", "timeline"]}
                        ]
                    },
                    {
                        "target": "analysis",
                        "conditions": [
                            {"type": "sentiment", "range": [0.0, 0.4]},
                            {"type": "keyword_match", "keywords": ["not sure", "different", "alternative", "other options"]}
                        ]
                    }
                ]
            },
            "implementation_planning": {
                "description": "Plan implementation steps",
                "default_response": "Let's discuss how to implement these recommendations.",
                "adapters": ["consultant"],
                "use_rag": True,
                "on_entry": {
                    "context_updates": {"implementation_planning_started": True}
                },
                "transitions": [
                    {
                        "target": "follow_up",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["follow up", "check in", "next meeting", "progress"]}
                        ]
                    },
                    {
                        "target": "closing",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["thank", "goodbye", "finished", "complete", "done"]}
                        ]
                    }
                ]
            },
            "follow_up": {
                "description": "Follow up on implementation",
                "default_response": "How has the implementation been going? Any new challenges?",
                "adapters": ["consultant"],
                "use_rag": False,
                "on_entry": {
                    "context_updates": {"follow_up_scheduled": True}
                },
                "transitions": [
                    {
                        "target": "problem_identification",
                        "conditions": [
                            {"type": "sentiment", "range": [0.0, 0.4]},
                            {"type": "keyword_match", "keywords": ["issue", "problem", "challenge", "difficulty", "not working"]}
                        ]
                    },
                    {
                        "target": "closing",
                        "conditions": [
                            {"type": "sentiment", "range": [0.6, 1.0]},
                            {"type": "keyword_match", "keywords": ["successful", "going well", "complete", "finished"]}
                        ]
                    }
                ]
            },
            "closing": {
                "description": "Close the conversation",
                "default_response": "Thank you for consulting with me. Is there anything else you'd like to discuss?",
                "adapters": ["consultant"],
                "use_rag": False,
                "on_entry": {
                    "context_updates": {"conversation_closing": True}
                },
                "transitions": [
                    {
                        "target": "problem_identification",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["yes", "actually", "one more thing", "another question"]}
                        ]
                    }
                ]
            }
        }
    },
    
    "memory": {
        "window_size": 20,
        "summary_interval": 10,
        "max_tokens": 2000,
        "timeout": 3600,  # 1 hour
        "summarization_prompt": """As a business consultant, summarize the key strategic points, 
        decisions, and action items from this conversation."""
    },
    "response": {
        "style_matching": True,
        "anti_ai_patterns": True,
        "source_citation": True,
        "expert_terminology": True
    },
    "session": {
        "timeout": 3600,  # 1 hour
        "extend_on_activity": True,
        "max_duration": 7200  # 2 hours
    },
    "chain_config": {
        "retrieval": {
            "type": "hybrid",
            "k": 4,
            "score_threshold": 0.7,
            "reranking": True
        },
        "prompt": {
            "style": "expert_consultant",
            "components": ["context", "analysis", "history"],
            "anti_ai": True
        },
        "memory": {
            "type": "enhanced",
            "window_size": 20,
            "summary_interval": 10
        }
    },
    "analysis_config": {
        "nlp_features": {
            "required": ["entities", "key_phrases", "sentiment"],
            "optional": ["syntax", "complexity"]
        },
        "templates": {
            "message": {
                "path": "templates/consultancy/message_analysis.json",
                "components": ["insights", "covert_patterns", "actions"]
            },
            "conversation": {
                "path": "templates/consultancy/conversation_analysis.json",
                "components": ["summary", "decisions", "next_steps"]
            }
        },
        "patterns": {
            "covert": ["pacing", "leading", "embedded"],
            "expert": ["terminology", "frameworks", "methodologies"]
        }
    },
    # Integrated detection rules
    "detection_rules": {
        "sample_request": {
            "enabled": True,
            "description": "Detects when a user is asking for a sample or example",
            "keywords": [
                "sample", "example", "demo", "showcase", "illustration",
                "can you show me", "give me an example", "could i see a sample",
                "provide a sample", "send me a sample", "share an example",
                "prototype", "demonstration", "what would it look like",
                "specimen", "model", "template", "case study"
            ],
            "required_entities": ["DOCUMENT_TYPE"],
            "confidence_threshold": 0.7,
            "action": "delegate_to_agent"
        },
        "legal_question": {
            "enabled": True,
            "description": "Detects legal-related questions",
            "keywords": [
                "legal", "law", "regulation", "compliance", "contract",
                "agreement", "terms", "liability", "lawsuit", "sue",
                "attorney", "lawyer", "legal department", "legal team"
            ],
            "required_entities": ["LEGAL"],
            "sentiment_range": [0.3, 0.7],  # Neutral-to-concerned sentiment
            "confidence_threshold": 0.6,
            "action": "use_legal_adapter"
        },
        "financial_question": {
            "enabled": True,
            "description": "Detects finance-related questions",
            "keywords": [
                "finance", "budget", "cost", "pricing", "investment",
                "revenue", "profit", "expense", "cash flow", "financial",
                "balance sheet", "income statement", "roi", "return on investment"
            ],
            "required_entities": ["FINANCIAL"],
            "sentiment_range": [0.4, 0.9],  # Neutral-to-positive sentiment
            "confidence_threshold": 0.6,
            "action": "use_finance_adapter"
        },
        "strategy_question": {
            "enabled": True,
            "description": "Detects strategy-related questions",
            "keywords": [
                "strategy", "strategic", "planning", "long-term", "vision",
                "mission", "goal", "objective", "competitive advantage", 
                "market position", "growth", "expansion", "roadmap"
            ],
            "required_entities": ["BUSINESS"],
            "confidence_threshold": 0.6,
            "action": "use_strategy_adapter"
        },
        "legal_response_quality": {
            "enabled": True,
            "description": "Detects when a legal response needs enhancement",
            "keywords": ["legal", "law", "regulation", "compliance"],
            "confidence_threshold": 0.6,
            "action": "enhance_response",
            "enhancement_type": "legal_response_quality"
        },
        "finance_response_quality": {
            "enabled": True,
            "description": "Detects when a financial response needs enhancement",
            "keywords": ["finance", "budget", "cost", "investment"],
            "confidence_threshold": 0.6,
            "action": "enhance_response",
            "enhancement_type": "finance_response_quality"
        }
    },
    # Action definitions
    "actions": {
        "delegate_to_agent": {
            "enabled": True,
            "description": "Delegates requests to the agent microservice",
            "endpoint": "/bot/request",
            "urgency": "high",
            "timeout": 30,
            "retry_count": 2,
            "fallback_action": "use_strategy_adapter",
            "success_criteria": {
                "status": "success",
                "content_present": True
            }
        },
        "use_legal_adapter": {
            "enabled": True,
            "description": "Uses the legal adapter for processing",
            "adapter": "legal",
            "retrieval_domains": ["legal"],
            "required_citations": True
        },
        "use_finance_adapter": {
            "enabled": True,
            "description": "Uses the finance adapter for processing",
            "adapter": "finance",
            "retrieval_domains": ["finance"],
            "numerical_analysis": True
        },
        "use_strategy_adapter": {
            "enabled": True,
            "description": "Uses the strategy adapter for processing",
            "adapter": "strategy",
            "retrieval_domains": ["strategy", "business"],
            "framework_analysis": True
        },
        "enhance_response": {
            "enabled": True,
            "description": "Enhances responses with additional quality elements",
            "domains": ["legal", "finance", "strategy"],
            "quality_target": "professional"
        }
    },
    # Response enhancement configurations
    "response_enhancements": {
        "legal_response_quality": {
            "description": "Enhances legal responses with appropriate terminology and citations",
            "add_citations": True,
            "domain_terminology": "legal",
            "min_length": 150
        },
        "finance_response_quality": {
            "description": "Enhances financial responses with appropriate terminology and data",
            "add_citations": True,
            "domain_terminology": "finance",
            "min_length": 200
        },
        "strategy_response_quality": {
            "description": "Enhances strategy responses with frameworks and terminology",
            "add_citations": True,
            "domain_terminology": "strategy",
            "min_length": 250,
            "add_frameworks": True
        }
    },
    # Domain-specific terminology
    "domain_terminology": {
        "legal": ["jurisdiction", "compliance", "liability", "contract", "terms", "regulation", 
                 "statutory", "tort", "litigation", "arbitration", "indemnity", "warranty"],
        "finance": ["ROI", "cash flow", "P&L", "balance sheet", "EBITDA", "depreciation", 
                   "assets", "liabilities", "equity", "valuation", "NPV", "IRR", "margin"],
        "strategy": ["competitive advantage", "market positioning", "value proposition", "SWOT",
                    "Porter's Five Forces", "blue ocean", "disruption", "innovation", "market penetration"]
    },
    # Business frameworks by domain
    "business_frameworks": {
        "strategy": [
            {"name": "SWOT Analysis", "components": ["Strengths", "Weaknesses", "Opportunities", "Threats"]},
            {"name": "Porter's Five Forces", "components": ["Supplier Power", "Buyer Power", "Competitive Rivalry", 
                                                          "Threat of Substitution", "Threat of New Entry"]},
            {"name": "Value Chain", "components": ["Inbound Logistics", "Operations", "Outbound Logistics", 
                                                 "Marketing & Sales", "Service"]}
        ],
        "finance": [
            {"name": "Financial Ratio Analysis", "components": ["Liquidity Ratios", "Profitability Ratios", 
                                                              "Leverage Ratios", "Efficiency Ratios"]},
            {"name": "Break-even Analysis", "components": ["Fixed Costs", "Variable Costs", "Contribution Margin", 
                                                         "Break-even Point"]}
        ],
        "legal": [
            {"name": "Risk Assessment Matrix", "components": ["Probability", "Impact", "Risk Level", "Mitigation Strategy"]},
            {"name": "Compliance Framework", "components": ["Regulatory Requirements", "Internal Controls", 
                                                          "Monitoring", "Reporting"]}
        ]
    },
    # NLP entity mappings
    "entity_types": {
        "DOCUMENT_TYPE": ["plan", "report", "analysis", "strategy", "proposal", "contract", "agreement", "template"],
        "LEGAL": ["contract", "agreement", "terms", "compliance", "regulation", "law", "statute", "legal"],
        "FINANCIAL": ["budget", "cost", "revenue", "profit", "expense", "investment", "ROI", "pricing"],
        "BUSINESS": ["strategy", "market", "competition", "customer", "product", "service", "growth", "KPI"]
    }
} 