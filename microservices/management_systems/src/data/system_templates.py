"""
Predefined templates for business management systems.

These templates define the structure and fields for common business systems like
CRM, Sales Automation, Social Media, etc. They can be used to quickly create
new system instances for tenants.
"""

from datetime import datetime
from typing import Dict, Any, List

# CRM System Template
CRM_CONTACTS = {
    "system_id": "crm-contacts",
    "name": "Customer Contacts",
    "type": "crm",
    "description": "Manage your customer and lead contact information",
    "version": "1.0.0",
    "tenant_collection": "crm_contacts",
    "data_fields": [
        {
            "name": "full_name",
            "display_name": "Full Name",
            "field_type": "string",
            "required": True,
            "description": "Customer's full name"
        },
        {
            "name": "email",
            "display_name": "Email Address",
            "field_type": "string",
            "required": True,
            "validation": "email",
            "description": "Primary email address"
        },
        {
            "name": "phone",
            "display_name": "Phone Number",
            "field_type": "string",
            "required": False,
            "description": "Primary phone number"
        },
        {
            "name": "company",
            "display_name": "Company",
            "field_type": "string",
            "required": False,
            "description": "Company or organization name"
        },
        {
            "name": "job_title",
            "display_name": "Job Title",
            "field_type": "string",
            "required": False,
            "description": "Position within company"
        },
        {
            "name": "status",
            "display_name": "Status",
            "field_type": "string",
            "required": True,
            "default": "lead",
            "options": ["lead", "prospect", "customer", "inactive"],
            "description": "Contact status"
        },
        {
            "name": "source",
            "display_name": "Lead Source",
            "field_type": "string",
            "required": False,
            "options": ["website", "referral", "advertisement", "social_media", "event", "other"],
            "description": "How the contact was acquired"
        },
        {
            "name": "notes",
            "display_name": "Notes",
            "field_type": "text",
            "required": False,
            "description": "Additional notes about the contact"
        },
        {
            "name": "last_contact",
            "display_name": "Last Contact Date",
            "field_type": "date",
            "required": False,
            "description": "Date of last communication"
        }
    ],
    "data_views": [
        {
            "view_id": "all-contacts",
            "name": "All Contacts",
            "description": "View all contacts",
            "fields": ["full_name", "email", "phone", "company", "status"],
            "sort_by": "full_name"
        },
        {
            "view_id": "leads",
            "name": "Leads",
            "description": "View all leads",
            "fields": ["full_name", "email", "phone", "source", "last_contact"],
            "filters": {"status": "lead"},
            "sort_by": "last_contact",
            "sort_order": "desc"
        },
        {
            "view_id": "customers",
            "name": "Customers",
            "description": "View all current customers",
            "fields": ["full_name", "email", "phone", "company", "last_contact"],
            "filters": {"status": "customer"},
            "sort_by": "last_contact",
            "sort_order": "desc"
        }
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Sales Automation Template
SALES_OPPORTUNITIES = {
    "system_id": "sales-opportunities",
    "name": "Sales Opportunities",
    "type": "sales_automation",
    "description": "Track and manage your sales pipeline and opportunities",
    "version": "1.0.0",
    "tenant_collection": "sales_opportunities",
    "data_fields": [
        {
            "name": "name",
            "display_name": "Opportunity Name",
            "field_type": "string",
            "required": True,
            "description": "Name of the sales opportunity"
        },
        {
            "name": "contact_id",
            "display_name": "Contact",
            "field_type": "reference",
            "required": True,
            "description": "Associated contact",
            "reference": {
                "collection": "crm_contacts",
                "display_field": "full_name"
            }
        },
        {
            "name": "value",
            "display_name": "Value",
            "field_type": "number",
            "required": True,
            "description": "Estimated value of the opportunity"
        },
        {
            "name": "currency",
            "display_name": "Currency",
            "field_type": "string",
            "required": True,
            "default": "USD",
            "options": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
            "description": "Currency of the opportunity value"
        },
        {
            "name": "stage",
            "display_name": "Stage",
            "field_type": "string",
            "required": True,
            "default": "prospecting",
            "options": ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"],
            "description": "Current stage in sales pipeline"
        },
        {
            "name": "probability",
            "display_name": "Probability (%)",
            "field_type": "number",
            "required": True,
            "default": 10,
            "validation": "range:0-100",
            "description": "Estimated probability of closing"
        },
        {
            "name": "expected_close_date",
            "display_name": "Expected Close Date",
            "field_type": "date",
            "required": True,
            "description": "Expected date to close the deal"
        },
        {
            "name": "description",
            "display_name": "Description",
            "field_type": "text",
            "required": False,
            "description": "Details about the opportunity"
        },
        {
            "name": "next_steps",
            "display_name": "Next Steps",
            "field_type": "text",
            "required": False,
            "description": "Next actions to move forward"
        }
    ],
    "data_views": [
        {
            "view_id": "all-opportunities",
            "name": "All Opportunities",
            "description": "View all sales opportunities",
            "fields": ["name", "contact_id", "value", "currency", "stage", "probability", "expected_close_date"],
            "sort_by": "expected_close_date"
        },
        {
            "view_id": "pipeline",
            "name": "Sales Pipeline",
            "description": "Active opportunities by stage",
            "fields": ["name", "contact_id", "value", "currency", "probability", "expected_close_date"],
            "filters": {"stage": {"$nin": ["closed_won", "closed_lost"]}},
            "sort_by": "expected_close_date"
        },
        {
            "view_id": "won-deals",
            "name": "Won Deals",
            "description": "Successfully closed opportunities",
            "fields": ["name", "contact_id", "value", "currency", "expected_close_date"],
            "filters": {"stage": "closed_won"},
            "sort_by": "expected_close_date",
            "sort_order": "desc"
        }
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Social Media Post Management
SOCIAL_MEDIA_POSTS = {
    "system_id": "social-posts",
    "name": "Social Media Posts",
    "type": "social_media",
    "description": "Manage and schedule posts across social media platforms",
    "version": "1.0.0",
    "tenant_collection": "social_posts",
    "data_fields": [
        {
            "name": "title",
            "display_name": "Post Title",
            "field_type": "string",
            "required": True,
            "description": "Internal title for the post"
        },
        {
            "name": "content",
            "display_name": "Content",
            "field_type": "text",
            "required": True,
            "description": "Post content/caption"
        },
        {
            "name": "platform",
            "display_name": "Platform",
            "field_type": "string",
            "required": True,
            "options": ["instagram", "facebook", "twitter", "linkedin", "tiktok", "pinterest"],
            "description": "Social media platform"
        },
        {
            "name": "media_urls",
            "display_name": "Media URLs",
            "field_type": "array",
            "required": False,
            "description": "URLs to images or videos"
        },
        {
            "name": "scheduled_date",
            "display_name": "Scheduled Date",
            "field_type": "datetime",
            "required": False,
            "description": "When to publish the post"
        },
        {
            "name": "status",
            "display_name": "Status",
            "field_type": "string",
            "required": True,
            "default": "draft",
            "options": ["draft", "scheduled", "published", "failed"],
            "description": "Current status of the post"
        },
        {
            "name": "tags",
            "display_name": "Tags/Hashtags",
            "field_type": "array",
            "required": False,
            "description": "Post tags or hashtags"
        },
        {
            "name": "engagement",
            "display_name": "Engagement Metrics",
            "field_type": "object",
            "required": False,
            "description": "Post performance metrics",
            "properties": {
                "likes": {"type": "number", "description": "Number of likes"},
                "comments": {"type": "number", "description": "Number of comments"},
                "shares": {"type": "number", "description": "Number of shares"},
                "clicks": {"type": "number", "description": "Number of link clicks"}
            }
        }
    ],
    "data_views": [
        {
            "view_id": "all-posts",
            "name": "All Posts",
            "description": "View all social media posts",
            "fields": ["title", "platform", "scheduled_date", "status"],
            "sort_by": "scheduled_date",
            "sort_order": "desc"
        },
        {
            "view_id": "drafts",
            "name": "Draft Posts",
            "description": "Posts in draft status",
            "fields": ["title", "platform", "scheduled_date"],
            "filters": {"status": "draft"},
            "sort_by": "scheduled_date"
        },
        {
            "view_id": "scheduled",
            "name": "Scheduled Posts",
            "description": "Posts scheduled for publication",
            "fields": ["title", "platform", "scheduled_date"],
            "filters": {"status": "scheduled"},
            "sort_by": "scheduled_date"
        },
        {
            "view_id": "published",
            "name": "Published Posts",
            "description": "Posts that have been published",
            "fields": ["title", "platform", "scheduled_date", "engagement.likes", "engagement.comments"],
            "filters": {"status": "published"},
            "sort_by": "scheduled_date",
            "sort_order": "desc"
        }
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# E-commerce Product Management
ECOMMERCE_PRODUCTS = {
    "system_id": "ecommerce-products",
    "name": "E-commerce Products",
    "type": "ecommerce",
    "description": "Manage your product catalog for e-commerce platforms",
    "version": "1.0.0",
    "tenant_collection": "ecommerce_products",
    "data_fields": [
        {
            "name": "name",
            "display_name": "Product Name",
            "field_type": "string",
            "required": True,
            "description": "Name of the product"
        },
        {
            "name": "sku",
            "display_name": "SKU",
            "field_type": "string",
            "required": True,
            "description": "Stock keeping unit"
        },
        {
            "name": "description",
            "display_name": "Description",
            "field_type": "text",
            "required": True,
            "description": "Product description"
        },
        {
            "name": "price",
            "display_name": "Price",
            "field_type": "number",
            "required": True,
            "description": "Product price"
        },
        {
            "name": "currency",
            "display_name": "Currency",
            "field_type": "string",
            "required": True,
            "default": "USD",
            "options": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
            "description": "Currency of the price"
        },
        {
            "name": "inventory",
            "display_name": "Inventory Count",
            "field_type": "number",
            "required": True,
            "default": 0,
            "description": "Current inventory level"
        },
        {
            "name": "category",
            "display_name": "Category",
            "field_type": "string",
            "required": True,
            "description": "Product category"
        },
        {
            "name": "image_urls",
            "display_name": "Images",
            "field_type": "array",
            "required": False,
            "description": "Product image URLs"
        },
        {
            "name": "status",
            "display_name": "Status",
            "field_type": "string",
            "required": True,
            "default": "draft",
            "options": ["draft", "active", "inactive", "out_of_stock"],
            "description": "Product status"
        },
        {
            "name": "variants",
            "display_name": "Variants",
            "field_type": "array",
            "required": False,
            "description": "Product variants (size, color, etc.)"
        },
        {
            "name": "weight",
            "display_name": "Weight (g)",
            "field_type": "number",
            "required": False,
            "description": "Product weight in grams"
        },
        {
            "name": "dimensions",
            "display_name": "Dimensions (cm)",
            "field_type": "object",
            "required": False,
            "description": "Product dimensions",
            "properties": {
                "length": {"type": "number", "description": "Length in cm"},
                "width": {"type": "number", "description": "Width in cm"},
                "height": {"type": "number", "description": "Height in cm"}
            }
        }
    ],
    "data_views": [
        {
            "view_id": "all-products",
            "name": "All Products",
            "description": "View all products",
            "fields": ["name", "sku", "price", "currency", "inventory", "status"],
            "sort_by": "name"
        },
        {
            "view_id": "active-products",
            "name": "Active Products",
            "description": "Products currently for sale",
            "fields": ["name", "sku", "price", "currency", "inventory", "category"],
            "filters": {"status": "active"},
            "sort_by": "category"
        },
        {
            "view_id": "low-inventory",
            "name": "Low Inventory",
            "description": "Products with low inventory",
            "fields": ["name", "sku", "price", "inventory", "status"],
            "filters": {"inventory": {"$lt": 10}, "status": "active"},
            "sort_by": "inventory"
        }
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Financial Transactions
FINANCE_TRANSACTIONS = {
    "system_id": "finance-transactions",
    "name": "Financial Transactions",
    "type": "finance_automation",
    "description": "Track income, expenses and financial transactions",
    "version": "1.0.0",
    "tenant_collection": "finance_transactions",
    "data_fields": [
        {
            "name": "date",
            "display_name": "Transaction Date",
            "field_type": "date",
            "required": True,
            "description": "Date of the transaction"
        },
        {
            "name": "description",
            "display_name": "Description",
            "field_type": "string",
            "required": True,
            "description": "Description of the transaction"
        },
        {
            "name": "amount",
            "display_name": "Amount",
            "field_type": "number",
            "required": True,
            "description": "Transaction amount"
        },
        {
            "name": "currency",
            "display_name": "Currency",
            "field_type": "string",
            "required": True,
            "default": "USD",
            "options": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
            "description": "Currency of the transaction"
        },
        {
            "name": "type",
            "display_name": "Type",
            "field_type": "string",
            "required": True,
            "options": ["income", "expense", "transfer"],
            "description": "Type of transaction"
        },
        {
            "name": "category",
            "display_name": "Category",
            "field_type": "string",
            "required": True,
            "description": "Transaction category"
        },
        {
            "name": "account",
            "display_name": "Account",
            "field_type": "string",
            "required": True,
            "description": "Associated account"
        },
        {
            "name": "reference",
            "display_name": "Reference",
            "field_type": "string",
            "required": False,
            "description": "Reference number or ID"
        },
        {
            "name": "notes",
            "display_name": "Notes",
            "field_type": "text",
            "required": False,
            "description": "Additional notes"
        },
        {
            "name": "status",
            "display_name": "Status",
            "field_type": "string",
            "required": True,
            "default": "pending",
            "options": ["pending", "completed", "reconciled", "voided"],
            "description": "Status of the transaction"
        }
    ],
    "data_views": [
        {
            "view_id": "all-transactions",
            "name": "All Transactions",
            "description": "View all financial transactions",
            "fields": ["date", "description", "amount", "currency", "type", "category", "status"],
            "sort_by": "date",
            "sort_order": "desc"
        },
        {
            "view_id": "income",
            "name": "Income",
            "description": "View all income transactions",
            "fields": ["date", "description", "amount", "currency", "category", "status"],
            "filters": {"type": "income"},
            "sort_by": "date",
            "sort_order": "desc"
        },
        {
            "view_id": "expenses",
            "name": "Expenses",
            "description": "View all expense transactions",
            "fields": ["date", "description", "amount", "currency", "category", "status"],
            "filters": {"type": "expense"},
            "sort_by": "date",
            "sort_order": "desc"
        },
        {
            "view_id": "pending",
            "name": "Pending Transactions",
            "description": "View pending transactions",
            "fields": ["date", "description", "amount", "currency", "type", "status"],
            "filters": {"status": "pending"},
            "sort_by": "date"
        }
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# All system templates
SYSTEM_TEMPLATES = {
    "crm-contacts": CRM_CONTACTS,
    "sales-opportunities": SALES_OPPORTUNITIES,
    "social-posts": SOCIAL_MEDIA_POSTS,
    "ecommerce-products": ECOMMERCE_PRODUCTS,
    "finance-transactions": FINANCE_TRANSACTIONS
}

def get_system_template(template_id: str) -> Dict[str, Any]:
    """Get a system template by ID."""
    return SYSTEM_TEMPLATES.get(template_id, {})

def get_all_system_templates() -> List[Dict[str, Any]]:
    """Get all available system templates."""
    return list(SYSTEM_TEMPLATES.values()) 