"""Configuration for the support bot."""

SUPPORT_BOT_CONFIG = {
    "bot_type": "support",
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.5,  # Lower temperature for more deterministic/factual responses
    "memory_tokens": 800,
    "system_message": """You are a technical support specialist who helps users resolve issues 
    efficiently. Provide clear, step-by-step solutions while maintaining a helpful and patient 
    approach. Prioritize accuracy, clarity, and thoroughness in your responses.""",
    "sources": ["knowledge_base", "troubleshooting_guides", "faqs"],
    "doc_paths": {
        "knowledge_base": "data/support/knowledge_base/",
        "troubleshooting": "data/support/troubleshooting/",
        "issue_templates": "data/support/templates/"
    },
    "lora_adapter_path": "path/to/support/adapter",
    
    # Product types for support
    "product_types": ["app", "service", "hardware"],
    
    # Conversation states for the support bot
    "conversation": {
        "initial_state": "greeting",
        "states": {
            "greeting": {
                "description": "Initial greeting and gathering basic info",
                "default_response": "Hello! I'm here to help. What issue are you experiencing today?",
                "adapters": ["support"],
                "use_rag": False,
                "on_entry": {
                    "message": "Welcome to customer support. I'm here to help solve your technical issues.",
                    "context_updates": {"greeted": True}
                },
                "transitions": [
                    {
                        "target": "issue_identification",
                        "conditions": [
                            {"type": "message_count", "threshold": 1}
                        ]
                    }
                ]
            },
            "issue_identification": {
                "description": "Identify the specific issue",
                "default_response": "Could you please describe the issue in more detail?",
                "adapters": ["support"],
                "use_rag": True,
                "on_entry": {
                    "context_updates": {"issue_identification_started": True}
                },
                "transitions": [
                    {
                        "target": "troubleshooting",
                        "conditions": [
                            {"type": "entity_present", "entity_name": "issue_type"},
                            {"type": "message_count", "threshold": 2}
                        ]
                    },
                    {
                        "target": "escalation",
                        "conditions": [
                            {"type": "sentiment", "range": [0.0, 0.3]},
                            {"type": "keyword_match", "keywords": ["urgent", "critical", "emergency", "not working at all"]}
                        ]
                    }
                ]
            },
            "troubleshooting": {
                "description": "Guide through troubleshooting steps",
                "default_response": "Let's try some troubleshooting steps to resolve this issue.",
                "adapters": ["support", "technical"],
                "use_rag": True,
                "on_entry": {
                    "context_updates": {"troubleshooting_started": True}
                },
                "transitions": [
                    {
                        "target": "resolution",
                        "conditions": [
                            {"type": "sentiment", "range": [0.6, 1.0]},
                            {"type": "keyword_match", "keywords": ["fixed", "solved", "working", "resolved", "better"]}
                        ]
                    },
                    {
                        "target": "escalation",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["not working", "tried that", "doesn't help", "speak to human"]}
                        ]
                    }
                ]
            },
            "resolution": {
                "description": "Resolve the issue",
                "default_response": "Based on the steps we've taken, is the issue resolved now?",
                "adapters": ["support"],
                "use_rag": False,
                "on_entry": {
                    "context_updates": {"resolution_proposed": True}
                },
                "transitions": [
                    {
                        "target": "confirmation",
                        "conditions": [
                            {"type": "sentiment", "range": [0.6, 1.0]},
                            {"type": "keyword_match", "keywords": ["yes", "working", "fixed", "resolved", "thank"]}
                        ]
                    },
                    {
                        "target": "troubleshooting",
                        "conditions": [
                            {"type": "sentiment", "range": [0.0, 0.4]},
                            {"type": "keyword_match", "keywords": ["no", "still", "not fixed", "same issue", "problem"]}
                        ]
                    }
                ]
            },
            "confirmation": {
                "description": "Confirm resolution and satisfaction",
                "default_response": "I'm glad we could resolve your issue. Is there anything else you need help with?",
                "adapters": ["support"],
                "use_rag": False,
                "on_entry": {
                    "message": "Great! I'm glad we were able to solve your issue.",
                    "context_updates": {"resolution_confirmed": True}
                },
                "transitions": [
                    {
                        "target": "issue_identification",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["yes", "another", "one more", "also", "new issue"]}
                        ]
                    },
                    {
                        "target": "closing",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["no", "that's all", "nothing else", "goodbye", "thanks"]}
                        ]
                    }
                ]
            },
            "escalation": {
                "description": "Escalate to human support if needed",
                "default_response": "This issue requires additional support. I'll escalate this to our specialist team.",
                "adapters": ["support"],
                "use_rag": False,
                "on_entry": {
                    "message": "I understand this is a complex issue that needs specialized attention.",
                    "context_updates": {"escalation_initiated": True}
                },
                "transitions": [
                    {
                        "target": "closing",
                        "conditions": [
                            {"type": "message_count", "threshold": 2}
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "escalate_ticket",
                        "params": {
                            "priority": "high"
                        }
                    }
                ]
            },
            "closing": {
                "description": "Close the conversation",
                "default_response": "Thank you for contacting our support team. Have a great day!",
                "adapters": ["support"],
                "use_rag": False,
                "on_entry": {
                    "context_updates": {"conversation_closing": True}
                },
                "transitions": [
                    {
                        "target": "issue_identification",
                        "conditions": [
                            {"type": "keyword_match", "keywords": ["wait", "one more thing", "actually", "before you go"]}
                        ]
                    }
                ]
            }
        }
    },
    
    # Issue types with tiers
    "issue_types": {
        "technical": {
            "description": "Technical issues requiring troubleshooting",
            "tier": 1,
            "timeout": 1200,  # 20 minutes
            "escalation_threshold": 3,  # Number of exchanges before escalation
            "response_time_goal": 300  # 5 minutes
        },
        "billing": {
            "description": "Billing and payment-related issues",
            "tier": 2,
            "timeout": 1800,  # 30 minutes
            "escalation_threshold": 2,
            "response_time_goal": 600  # 10 minutes
        },
        "access": {
            "description": "Account access and permissions issues",
            "tier": 1,
            "timeout": 1200,  # 20 minutes
            "escalation_threshold": 2,
            "response_time_goal": 300  # 5 minutes
        },
        "feature": {
            "description": "Questions about product features",
            "tier": 3,
            "timeout": 2400,  # 40 minutes
            "escalation_threshold": 4,
            "response_time_goal": 900  # 15 minutes
        },
        "bug": {
            "description": "Potential bugs and errors",
            "tier": 1,
            "timeout": 1200,  # 20 minutes
            "escalation_threshold": 2,
            "response_time_goal": 300  # 5 minutes
        }
    },
    
    # Memory settings
    "memory": {
        "window_size": 10,
        "summary_interval": 5,
        "max_tokens": 1000,
        "timeout": 1200,  # 20 minutes
        "summarization_prompt": """As a technical support specialist, summarize the key issues, 
        troubleshooting steps attempted, and the current status of resolution."""
    },
    
    # Response settings
    "response": {
        "step_by_step": True,
        "anti_ai_patterns": True,
        "clear_formatting": True,
        "technical_accuracy": True
    },
    
    # Session settings
    "session": {
        "timeout": 1800,  # 30 minutes
        "extend_on_activity": True,
        "max_duration": 7200  # 2 hours
    },
    
    # Model parameters - optimized for support
    "model_params": {
        "temperature": 0.5,
        "max_length": 384,
        "top_p": 0.85,
        "top_k": 40,
        "use_4bit": True,  # Use 4-bit quantization for faster responses
        "use_8bit": False
    },
    
    # Chain configuration
    "chain_config": {
        "retrieval": {
            "type": "hybrid",
            "k": 5,  # More results for comprehensive troubleshooting
            "score_threshold": 0.7,
            "reranking": True
        },
        "prompt": {
            "style": "technical_support",
            "components": ["issue_details", "troubleshooting_history", "system_info"],
            "anti_ai": True
        },
        "memory": {
            "type": "enhanced",
            "window_size": 10,
            "summary_interval": 5
        }
    },
    
    # NLP features configuration
    "analysis_config": {
        "nlp_features": {
            "required": ["entities", "sentiment", "issue_type"],
            "optional": ["urgency", "technical_complexity"]
        },
        "templates": {
            "message": {
                "path": "templates/support/message_analysis.json",
                "components": ["issue_classification", "urgency", "next_steps"]
            },
            "conversation": {
                "path": "templates/support/conversation_analysis.json",
                "components": ["issue_summary", "steps_taken", "resolution_status"]
            }
        },
        "patterns": {
            "error_messages": ["error", "failed", "doesn't work", "broken"],
            "urgency_signals": ["urgent", "asap", "immediately", "critical"]
        }
    },
    
    # Detection rules
    "detection_rules": {
        "error_report": {
            "enabled": True,
            "description": "Detects when a user reports an error",
            "keywords": [
                "error", "problem", "issue", "doesn't work", "not working", 
                "broken", "failed", "crash", "bug", "glitch", "malfunction",
                "won't load", "stuck", "frozen", "can't access"
            ],
            "required_entities": ["ERROR_TYPE"],
            "confidence_threshold": 0.6,
            "action": "troubleshoot_error"
        },
        "account_issue": {
            "enabled": True,
            "description": "Detects account-related issues",
            "keywords": [
                "login", "account", "password", "can't log in", "access", 
                "credentials", "authentication", "locked out", "reset", 
                "username", "forgot", "sign in", "permissions"
            ],
            "confidence_threshold": 0.65,
            "action": "handle_account_issue"
        },
        "billing_inquiry": {
            "enabled": True,
            "description": "Detects billing inquiries",
            "keywords": [
                "bill", "charge", "payment", "invoice", "subscription", 
                "credit card", "refund", "transaction", "receipt", 
                "charged", "paid", "billing"
            ],
            "confidence_threshold": 0.7,
            "action": "handle_billing_inquiry"
        },
        "high_urgency": {
            "enabled": True,
            "description": "Detects high urgency issues",
            "keywords": [
                "urgent", "immediately", "asap", "emergency", "critical", 
                "right now", "deadline", "important", "priority", "desperate",
                "stuck", "can't continue", "blocking"
            ],
            "sentiment_range": [0.1, 0.4],  # Negative sentiment indicating frustration
            "confidence_threshold": 0.6,
            "action": "prioritize_issue"
        },
        "escalation_needed": {
            "enabled": True,
            "description": "Detects when escalation is needed",
            "keywords": [
                "speak to manager", "supervisor", "escalate", "human", 
                "real person", "agent", "not helping", "want someone else",
                "higher up", "tier 2", "senior support", "specialist"
            ],
            "confidence_threshold": 0.65,
            "action": "escalate_to_human"
        }
    },
    
    # Action definitions
    "actions": {
        "troubleshoot_error": {
            "enabled": True,
            "description": "Provides troubleshooting steps for errors",
            "retrieval_domains": ["troubleshooting_guides"],
            "step_by_step": True,
            "confirmation_checks": True
        },
        "handle_account_issue": {
            "enabled": True,
            "description": "Addresses account-related issues",
            "verification_steps": True,
            "security_protocols": True,
            "self_service_options": True
        },
        "handle_billing_inquiry": {
            "enabled": True,
            "description": "Addresses billing-related inquiries",
            "retrieval_domains": ["billing_faq"],
            "transaction_lookup": True,
            "refund_policy": True
        },
        "prioritize_issue": {
            "enabled": True,
            "description": "Escalates high urgency issues",
            "response_time": 120,  # 2 minutes
            "notification_channels": ["slack", "email"],
            "template": "urgent_issue"
        },
        "escalate_to_human": {
            "enabled": True,
            "description": "Escalates to human support agent",
            "generate_ticket": True,
            "channels": ["chat", "email", "phone"],
            "handoff_summary": True
        },
        "generate_ticket": {
            "enabled": True,
            "description": "Generates a support ticket",
            "ticket_format": "standard",
            "include_transcript": True,
            "priority_assignment": True
        }
    },
    
    # Response enhancement configurations
    "response_enhancements": {
        "technical_solution": {
            "description": "Enhances technical solution responses",
            "numbered_steps": True,
            "code_formatting": True,
            "verification_steps": True,
            "min_length": 200
        },
        "account_security": {
            "description": "Enhances account security responses",
            "security_warnings": True,
            "verification_instructions": True,
            "privacy_guidelines": True,
            "min_length": 150
        },
        "general_guidance": {
            "description": "Enhances general guidance responses",
            "clear_instructions": True,
            "additional_resources": True,
            "follow_up_options": True,
            "min_length": 100
        }
    },
    
    # Technical terminology by domain
    "technical_terminology": {
        "app": ["login", "interface", "dashboard", "update", "version", "cache", "data", 
               "sync", "notification", "settings", "profile", "upload", "download"],
        "service": ["account", "subscription", "plan", "tier", "quota", "usage", "limit", 
                  "authorization", "permission", "role", "access", "integration", "API"],
        "hardware": ["device", "connection", "power", "reset", "battery", "cable", "port", 
                   "screen", "button", "adapter", "memory", "storage", "driver"]
    },
    
    # Troubleshooting decision trees
    "troubleshooting_trees": {
        "login_issues": [
            {"step": "Check username/password", "next_if_success": "end", "next_if_failure": "password_reset"},
            {"step": "password_reset", "next_if_success": "end", "next_if_failure": "account_lockout"},
            {"step": "account_lockout", "next_if_success": "end", "next_if_failure": "contact_support"}
        ],
        "connectivity": [
            {"step": "Check internet connection", "next_if_success": "check_app_status", "next_if_failure": "network_troubleshooting"},
            {"step": "check_app_status", "next_if_success": "end", "next_if_failure": "clear_cache"},
            {"step": "clear_cache", "next_if_success": "end", "next_if_failure": "reinstall_app"},
            {"step": "reinstall_app", "next_if_success": "end", "next_if_failure": "contact_support"},
            {"step": "network_troubleshooting", "next_if_success": "end", "next_if_failure": "contact_support"}
        ],
        "payment_issues": [
            {"step": "Check payment method", "next_if_success": "verify_transaction", "next_if_failure": "update_payment"},
            {"step": "update_payment", "next_if_success": "end", "next_if_failure": "contact_billing"},
            {"step": "verify_transaction", "next_if_success": "end", "next_if_failure": "contact_billing"}
        ]
    },
    
    # Entity types for NLP
    "entity_types": {
        "ERROR_TYPE": ["login", "payment", "connection", "performance", "data", "sync", "crash"],
        "PLATFORM": ["web", "mobile", "desktop", "android", "ios", "windows", "mac", "linux"],
        "ACTION": ["reset", "update", "install", "remove", "configure", "enable", "disable"],
        "COMPONENT": ["account", "profile", "dashboard", "settings", "payment", "subscription"],
        "SEVERITY": ["critical", "high", "medium", "low", "minor"],
        "TIME_FRAME": ["immediately", "today", "yesterday", "last week", "recently"]
    },
    
    # Ticket templates
    "ticket_templates": {
        "standard": {
            "fields": ["issue_type", "description", "steps_taken", "urgency"],
            "auto_categorize": True,
            "id_format": "SUP-{date}-{sequential}"
        },
        "bug_report": {
            "fields": ["issue_type", "description", "steps_to_reproduce", "platform", "version"],
            "auto_categorize": True,
            "id_format": "BUG-{date}-{sequential}"
        },
        "feature_request": {
            "fields": ["description", "use_case", "priority", "requested_by"],
            "auto_categorize": True,
            "id_format": "FEAT-{date}-{sequential}"
        }
    }
} 