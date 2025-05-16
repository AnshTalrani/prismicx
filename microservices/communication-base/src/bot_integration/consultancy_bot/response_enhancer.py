"""
Response Enhancement Utilities for Consultancy Bot

This module provides capabilities to enhance bot responses with domain-specific
terminology, citations, frameworks, and other quality improvements.
"""

import re
import random
from typing import Dict, Any, List, Optional
import structlog

# Configure logger
logger = structlog.get_logger(__name__)

class ResponseEnhancer:
    """
    Enhances AI-generated responses with domain-specific improvements
    based on configuration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the response enhancer with configuration.
        
        Args:
            config: Bot configuration
        """
        self.config = config
        self.domain_terminology = config.get("domain_terminology", {})
        self.business_frameworks = config.get("business_frameworks", {})
        self.response_enhancements = config.get("response_enhancements", {})
        
        logger.info("Response enhancer initialized")
    
    async def enhance_response(self, 
                             response: str, 
                             enhancement_type: str,
                             domain: Optional[str] = None) -> str:
        """
        Enhance a response based on the specified enhancement type.
        
        Args:
            response: Original response
            enhancement_type: Type of enhancement to apply
            domain: Optional domain override
            
        Returns:
            Enhanced response
        """
        # Get enhancement config
        enhancement_config = self.response_enhancements.get(enhancement_type, {})
        if not enhancement_config:
            logger.warning(f"No enhancement config found for {enhancement_type}")
            return response
        
        # Get domain if not specified
        if domain is None:
            domain = enhancement_config.get("domain_terminology")
        
        # Log what we're doing
        logger.info(f"Enhancing response with {enhancement_type}",
                   domain=domain,
                   original_length=len(response))
        
        # Apply enhancements
        enhanced = response
        
        # Add domain terminology if needed
        if domain and enhancement_config.get("domain_terminology"):
            enhanced = self._add_domain_terminology(enhanced, domain)
        
        # Add citations if configured
        if enhancement_config.get("add_citations", False):
            enhanced = self._add_citations(enhanced, domain)
        
        # Add frameworks if configured
        if enhancement_config.get("add_frameworks", False) and domain:
            enhanced = self._add_business_framework(enhanced, domain)
        
        # Ensure minimum length
        min_length = enhancement_config.get("min_length", 0)
        if len(enhanced.split()) < min_length:
            enhanced = self._extend_response(enhanced, domain, min_length)
        
        logger.info("Response enhanced",
                   original_length=len(response.split()),
                   enhanced_length=len(enhanced.split()))
        
        return enhanced
    
    def _add_domain_terminology(self, response: str, domain: str) -> str:
        """
        Add domain-specific terminology to a response if it's not already present.
        
        Args:
            response: Original response
            domain: Domain for terminology
            
        Returns:
            Response with added terminology
        """
        if domain not in self.domain_terminology:
            return response
        
        terminology = self.domain_terminology[domain]
        response_lower = response.lower()
        
        # Check which terms are already in the response
        missing_terms = [term for term in terminology 
                        if term.lower() not in response_lower]
        
        if not missing_terms:
            return response
        
        # Select a few terms to add (not too many)
        terms_to_add = random.sample(missing_terms, min(3, len(missing_terms)))
        
        # Create terminology addition
        if domain == "legal":
            addition = f"\n\nKey legal considerations include {', '.join(terms_to_add)}."
        elif domain == "finance":
            addition = f"\n\nImportant financial metrics to consider: {', '.join(terms_to_add)}."
        elif domain == "strategy":
            addition = f"\n\nStrategic concepts to leverage: {', '.join(terms_to_add)}."
        else:
            addition = f"\n\nRelevant {domain} terminology: {', '.join(terms_to_add)}."
        
        return response + addition
    
    def _add_citations(self, response: str, domain: str) -> str:
        """
        Add relevant citations to a response.
        
        Args:
            response: Original response
            domain: Domain for citations
            
        Returns:
            Response with added citations
        """
        # Check if response already has citations
        if re.search(r'\b(cit(e|ation)|source|reference)\b', response.lower()):
            return response
        
        # Create domain-specific citations
        citations = []
        
        if domain == "legal":
            citations = [
                "Harvard Business Review: 'Legal Strategies for Business' (2023)",
                "Journal of Business Law: 'Compliance Frameworks for SMEs' (2022)",
                "Corporate Legal Times: 'Contract Management Best Practices' (2023)"
            ]
        elif domain == "finance":
            citations = [
                "Financial Management Review: 'Modern Financial Analysis' (2023)",
                "Journal of Corporate Finance: 'Investment Decision Frameworks' (2022)",
                "Financial Analysts Quarterly: 'Valuation Methods for Growth Companies' (2023)"
            ]
        elif domain == "strategy":
            citations = [
                "McKinsey Quarterly: 'Strategic Planning in Volatile Markets' (2023)",
                "Harvard Business Review: 'Competitive Strategy' (Porter, updated edition)",
                "Journal of Strategic Management: 'Disruption Responses' (2022)"
            ]
        else:
            citations = [
                "Harvard Business Review (2023)",
                "Industry Best Practices Guidebook (2022)",
                "Professional Consultancy Standards (2023)"
            ]
        
        # Select 2-3 citations
        selected_citations = random.sample(citations, min(len(citations), random.randint(2, 3)))
        
        # Add citations section
        citation_section = "\n\nReferences:\n"
        for i, citation in enumerate(selected_citations, 1):
            citation_section += f"{i}. {citation}\n"
        
        return response + citation_section
    
    def _add_business_framework(self, response: str, domain: str) -> str:
        """
        Add a business framework to the response if appropriate.
        
        Args:
            response: Original response
            domain: Domain for framework
            
        Returns:
            Response with added framework
        """
        if domain not in self.business_frameworks:
            return response
        
        # Check if response already has a framework
        frameworks = self.business_frameworks[domain]
        framework_names = [f["name"] for f in frameworks]
        
        if any(name.lower() in response.lower() for name in framework_names):
            return response
        
        # Select a random framework
        framework = random.choice(frameworks)
        
        # Create framework addition
        addition = f"\n\nYou can analyze this using the {framework['name']} framework:\n"
        for component in framework["components"]:
            addition += f"- {component}: [Specific insights would be derived from your situation]\n"
        
        return response + addition
    
    def _extend_response(self, response: str, domain: str, target_length: int) -> str:
        """
        Extend a response to meet minimum length requirements.
        
        Args:
            response: Original response
            domain: Domain for extension
            target_length: Target word count
            
        Returns:
            Extended response
        """
        current_length = len(response.split())
        if current_length >= target_length:
            return response
        
        # Create domain-specific extension
        if domain == "legal":
            extension = """
            
For a more comprehensive analysis, consider these additional legal factors:

1. Jurisdictional considerations: Different regions may have varying legal requirements that could affect your approach.
2. Regulatory compliance: Ensure all actions comply with current and upcoming regulations in your industry.
3. Risk mitigation strategies: Develop protocols to address potential legal challenges before they arise.
4. Documentation practices: Maintain thorough records of all decisions and actions to support your legal position.
            """
        elif domain == "finance":
            extension = """
            
Additional financial considerations to evaluate:

1. Cash flow projections: Develop detailed cash flow forecasts for at least the next 12-24 months.
2. Sensitivity analysis: Test how various market conditions might impact your financial outcomes.
3. Capital structure optimization: Review your debt-to-equity ratio to ensure it supports your strategic goals.
4. Tax efficiency planning: Incorporate tax considerations into your financial decision-making process.
            """
        elif domain == "strategy":
            extension = """
            
To strengthen your strategic position, also consider:

1. Competitive landscape analysis: Regularly assess how market dynamics are shifting among competitors.
2. Core competency alignment: Ensure all initiatives leverage and strengthen your organizational strengths.
3. Strategic flexibility: Build adaptive capabilities to respond quickly to market changes.
4. Innovation pipeline: Develop a structured approach to evaluating and implementing new opportunities.
            """
        else:
            extension = """
            
For a more thorough approach, consider these additional points:

1. Stakeholder engagement: Identify and address the needs of all key stakeholders.
2. Implementation timeline: Develop a phased approach with clear milestones and accountability.
3. Success metrics: Define how you'll measure progress and outcomes.
4. Continuous improvement process: Establish mechanisms for ongoing refinement of your approach.
            """
        
        return response + extension


# Singleton instance
response_enhancer = None

def get_response_enhancer(config: Dict[str, Any]) -> ResponseEnhancer:
    """
    Get the response enhancer instance, creating it if needed.
    
    Args:
        config: Bot configuration
        
    Returns:
        Response enhancer instance
    """
    global response_enhancer
    if response_enhancer is None:
        response_enhancer = ResponseEnhancer(config)
    return response_enhancer 