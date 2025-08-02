"""
Field Mapping Examples

This module provides example field mapping configurations for the batch campaign processor.
These examples can be used as references when setting up field mappings for different client systems.
"""

from typing import Dict, Any

# Example field mapping for an e-commerce client
ECOMMERCE_FIELD_MAPPING: Dict[str, Any] = {
    # Customer data mapping (from client CRM to our system)
    "customer_mapping": {
        # Basic mapping of fields with direct correspondence
        "field_mappings": {
            # client_field: our_field
            "userId": "user_id",
            "firstName": "first_name",
            "lastName": "last_name",
            "emailAddress": "email",
            "phoneNum": "phone",
            "customerSince": "registration_date",
            "userPrefs.marketingConsent": "marketing_consent",
            "userPrefs.emailFrequency": "email_frequency",
            "segmentTags": "tags",
        },
        
        # Value transformations for fields that need processing
        "value_transformations": {
            # Transform customer status to our standardized values
            "status": {
                "mapping": {
                    "ACTIVE": "active",
                    "INACTIVE": "inactive",
                    "SUSPENDED": "blocked",
                    "NEW": "new",
                    "VIP": "premium"
                },
                "default": "active"
            },
            
            # Boolean transformations
            "isSubscribed": {
                "mapping": {
                    True: True,
                    False: False,
                    "yes": True,
                    "no": False,
                    1: True,
                    0: False
                },
                "default": False
            }
        },
        
        # Combine fields in client system to create our fields
        "field_combinations": {
            "full_name": {
                "source_fields": ["firstName", "lastName"],
                "separator": " "
            },
            "full_address": {
                "source_fields": ["address.street", "address.city", "address.state", "address.zip"],
                "separator": ", "
            }
        }
    },
    
    # Product data mapping
    "product_mapping": {
        "field_mappings": {
            "productId": "product_id",
            "prodName": "name",
            "prodDescription": "description",
            "price": "price",
            "salePrice": "sale_price",
            "imageUrls": "images",
            "prodCategory": "category",
            "inStock": "in_stock_quantity",
            "brand.name": "brand",
            "createdAt": "created_at",
            "updatedAt": "updated_at"
        },
        
        # Value transformations for product fields
        "value_transformations": {
            "availabilityStatus": {
                "mapping": {
                    "IN_STOCK": "in_stock",
                    "OUT_OF_STOCK": "out_of_stock",
                    "BACKORDER": "backorder",
                    "DISCONTINUED": "discontinued"
                },
                "default": "out_of_stock"
            }
        },
        
        # Computed fields based on client data
        "computed_fields": {
            "is_on_sale": {
                "condition": "salePrice < price and salePrice > 0",
                "value_true": True,
                "value_false": False
            },
            "discount_percentage": {
                "expression": "round(((price - salePrice) / price) * 100) if price > 0 and salePrice < price else 0"
            }
        }
    },
    
    # Segment criteria mapping (how our segment criteria map to client DB fields)
    "segment_criteria_mapping": {
        "age": "userProfile.age",
        "gender": "userProfile.gender",
        "location.country": "address.country",
        "location.city": "address.city",
        "purchase_count": "stats.totalPurchases",
        "last_purchase_date": "lastOrderDate",
        "average_order_value": "stats.avgOrderValue",
        "product_category_preference": "preferences.favoriteCategories",
        "email_engagement_score": "metrics.emailEngagement",
        "loyalty_tier": "loyaltyInfo.tier"
    }
}

# Example field mapping for a B2B SaaS client
B2B_SAAS_FIELD_MAPPING: Dict[str, Any] = {
    # Customer mapping for B2B clients (companies rather than individuals)
    "customer_mapping": {
        "field_mappings": {
            "companyId": "company_id",
            "companyName": "company_name",
            "industry": "industry",
            "mainContactEmail": "primary_email",
            "mainContactName": "primary_contact",
            "mainContactPhone": "primary_phone",
            "companySize": "company_size",
            "subscriptionTier": "subscription_tier",
            "subscriptionStartDate": "subscription_start_date",
            "subscriptionEndDate": "subscription_renewal_date",
            "billingAddress": "billing_address",
            "accountManager": "account_manager"
        },
        
        "value_transformations": {
            "accountStatus": {
                "mapping": {
                    "active": "active",
                    "churned": "churned",
                    "trial": "trial",
                    "past_due": "at_risk"
                },
                "default": "unknown"
            },
            "companySize": {
                "mapping": {
                    "1-10": "micro",
                    "11-50": "small",
                    "51-200": "medium",
                    "201-1000": "large",
                    "1001+": "enterprise"
                },
                "default": "unknown"
            }
        }
    },
    
    # Product mapping for B2B SaaS products
    "product_mapping": {
        "field_mappings": {
            "planId": "product_id",
            "planName": "name", 
            "planDescription": "description",
            "monthlyPrice": "monthly_price",
            "annualPrice": "annual_price",
            "features": "features",
            "maxUsers": "max_users",
            "maxStorage": "max_storage_gb",
            "supportLevel": "support_level"
        },
        
        "computed_fields": {
            "annual_discount_percentage": {
                "expression": "round(((monthlyPrice * 12 - annualPrice) / (monthlyPrice * 12)) * 100) if monthlyPrice > 0 and annualPrice > 0 else 0"
            },
            "is_enterprise": {
                "condition": "'enterprise' in planName.lower() or maxUsers > 100",
                "value_true": True,
                "value_false": False
            }
        }
    },
    
    # Segment criteria mapping for B2B customers
    "segment_criteria_mapping": {
        "company_size": "companySize",
        "industry": "industry",
        "subscription_tier": "subscriptionTier",
        "days_to_renewal": "daysToRenewal",
        "monthly_active_users": "usage.monthlyActiveUsers",
        "feature_usage.api_calls": "usage.apiCalls",
        "customer_health_score": "metrics.healthScore",
        "renewal_risk": "metrics.renewalRisk",
        "expansion_opportunity": "metrics.expansionScore"
    }
}

# Example field mapping for a financial services client
FINANCIAL_SERVICES_FIELD_MAPPING: Dict[str, Any] = {
    # Customer mapping for financial services
    "customer_mapping": {
        "field_mappings": {
            "customerId": "user_id",
            "name.first": "first_name",
            "name.last": "last_name",
            "emailAddress": "email",
            "phoneNumber": "phone",
            "dateOfBirth": "birth_date",
            "kycStatus": "verification_status",
            "riskProfile": "risk_profile",
            "accountCreationDate": "registration_date",
            "address.line1": "address_line1",
            "address.line2": "address_line2",
            "address.city": "city",
            "address.state": "state",
            "address.postalCode": "postal_code",
            "address.country": "country"
        },
        
        "value_transformations": {
            "customerStatus": {
                "mapping": {
                    "ACTIVE": "active",
                    "INACTIVE": "inactive",
                    "SUSPENDED": "suspended",
                    "PENDING_VERIFICATION": "pending_verification"
                },
                "default": "pending_verification"
            },
            
            "kycStatus": {
                "mapping": {
                    "VERIFIED": "verified",
                    "UNVERIFIED": "unverified",
                    "IN_PROGRESS": "in_progress",
                    "REJECTED": "rejected",
                    "REQUIRES_ADDITIONAL_INFO": "additional_info_required"
                },
                "default": "unverified"
            },
            
            "riskProfile": {
                "mapping": {
                    "LOW": "low_risk",
                    "MEDIUM": "medium_risk",
                    "HIGH": "high_risk"
                },
                "default": "medium_risk"
            }
        },
        
        "field_combinations": {
            "full_name": {
                "source_fields": ["name.first", "name.last"],
                "separator": " "
            }
        }
    },
    
    # Product mapping for financial products
    "product_mapping": {
        "field_mappings": {
            "productId": "product_id",
            "productName": "name",
            "productType": "type",
            "interestRate": "interest_rate",
            "annualFee": "annual_fee",
            "minimumDeposit": "minimum_deposit",
            "term": "term_months",
            "riskLevel": "risk_level",
            "eligible": "eligibility_criteria",
            "benefits": "benefits",
            "productCreatedDate": "created_at"
        },
        
        "value_transformations": {
            "productType": {
                "mapping": {
                    "SAVINGS": "savings_account",
                    "CHECKING": "checking_account",
                    "CREDIT_CARD": "credit_card",
                    "LOAN": "loan",
                    "MORTGAGE": "mortgage",
                    "INVESTMENT": "investment"
                },
                "default": "other"
            }
        },
        
        "computed_fields": {
            "is_credit_product": {
                "condition": "productType in ['CREDIT_CARD', 'LOAN', 'MORTGAGE']",
                "value_true": True,
                "value_false": False
            }
        }
    },
    
    # Segment criteria mapping for financial clients
    "segment_criteria_mapping": {
        "age": "age",
        "income": "financials.annualIncome",
        "credit_score": "creditScore",
        "account_balance": "account.currentBalance",
        "account_type": "account.type",
        "has_mortgage": "products.hasMortgage",
        "investment_balance": "investments.totalBalance",
        "risk_profile": "riskProfile",
        "last_transaction_date": "account.lastTransactionDate",
        "product_count": "products.count"
    }
}

# Dictionary of example mappings for easy access
EXAMPLE_MAPPINGS = {
    "ecommerce": ECOMMERCE_FIELD_MAPPING,
    "b2b_saas": B2B_SAAS_FIELD_MAPPING,
    "financial_services": FINANCIAL_SERVICES_FIELD_MAPPING
}


def get_example_mapping(client_type: str) -> Dict[str, Any]:
    """
    Get an example field mapping configuration based on client type.
    
    Args:
        client_type: Type of client (ecommerce, b2b_saas, financial_services)
        
    Returns:
        Example field mapping configuration
    """
    return EXAMPLE_MAPPINGS.get(client_type.lower(), ECOMMERCE_FIELD_MAPPING) 