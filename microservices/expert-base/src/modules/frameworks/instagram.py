"""
Instagram expert framework for the Expert Base microservice.

This module provides the Instagram expert framework, which is specialized for
Instagram content creation, analysis, and review.
"""

from typing import Dict, Any
from loguru import logger

from src.modules.frameworks.base import BaseExpertFramework


class InstagramExpertFramework(BaseExpertFramework):
    """
    Instagram expert framework.
    
    This framework is specialized for Instagram content, providing expertise
    for creation, analysis, and review of Instagram posts, captions, etc.
    """
    
    async def get_prompt_template(self, intent: str) -> str:
        """
        Get a prompt template for the given intent.
        
        Args:
            intent: The intent to get a prompt template for.
            
        Returns:
            A prompt template string.
        """
        if intent == "generate":
            return self._get_generation_template()
        elif intent == "analyze":
            return self._get_analysis_template()
        elif intent == "review":
            return self._get_review_template()
        else:
            logger.warning(f"Unknown intent '{intent}' for Instagram framework, using default template")
            return self._get_default_template()
    
    def _get_generation_template(self) -> str:
        """
        Get the template for content generation.
        
        Returns:
            A template string.
        """
        return """
You are an Instagram content expert. Your task is to generate engaging, high-quality content 
for Instagram that will resonate with the target audience and drive engagement.

CONTEXT:
{knowledge_context}

PARAMETERS:
- Content type: {content_type}
- Tone: {tone}
- Target audience: {target_audience}
- Brand voice: {brand_voice}
- Key messages: {key_messages}
- Character limit: {character_limit}
- Include hashtags: {include_hashtags}
- Hashtag count: {hashtag_count}

INSTRUCTIONS:
{instructions}

CONTENT SEED (if applicable):
{content_seed}

Your response should follow Instagram best practices including:
- Strong hook at the beginning
- Clear, concise language
- Engaging call-to-action
- Strategic use of emojis
- Proper formatting for readability
- Relevant hashtags (if requested)
- Adherence to Instagram guidelines

Generate Instagram content based on the above parameters:
"""
    
    def _get_analysis_template(self) -> str:
        """
        Get the template for content analysis.
        
        Returns:
            A template string.
        """
        return """
You are an Instagram content analysis expert. Your task is to analyze the given Instagram 
content and provide insights on its effectiveness, engagement potential, and areas for improvement.

CONTEXT:
{knowledge_context}

PARAMETERS:
- Analysis depth: {analysis_depth}
- Focus areas: {focus_areas}
- Target audience: {target_audience}
- Engagement metrics: {engagement_metrics}
- Competitive comparison: {competitive_comparison}
- Benchmark against: {benchmark}

CONTENT TO ANALYZE:
{content}

Provide a comprehensive analysis addressing:
1. Content Strength Assessment
   - Hook effectiveness
   - Message clarity
   - Visual-text alignment (if applicable)
   - Call-to-action effectiveness
   
2. Audience Alignment
   - Target audience appeal
   - Value proposition clarity
   - Relevance to audience interests
   
3. Engagement Potential
   - Like potential
   - Comment potential
   - Share potential
   - Save potential
   
4. Technical Elements
   - Hashtag effectiveness
   - Caption length appropriateness
   - Formatting and readability
   - Emoji usage
   
5. Areas for Improvement
   - Specific actionable recommendations
   - Priority improvements
   
Analysis:
"""
    
    def _get_review_template(self) -> str:
        """
        Get the template for content review.
        
        Returns:
            A template string.
        """
        return """
You are an Instagram content review expert. Your task is to review the given Instagram 
content and provide feedback on its quality, compliance with platform guidelines, 
and alignment with best practices.

CONTEXT:
{knowledge_context}

PARAMETERS:
- Review strictness: {review_strictness}
- Focus areas: {focus_areas}
- Brand alignment check: {check_brand_alignment}
- Compliance check: {compliance_check}
- Target audience: {target_audience}
- Quality threshold: {quality_threshold}

CONTENT TO REVIEW:
{content}

Provide a detailed review including:
1. Overall Score (1-10)

2. Strengths
   - List 3-5 specific strengths

3. Areas for Improvement
   - List 3-5 specific improvements
   
4. Compliance Assessment
   - Instagram policy compliance
   - Community guidelines adherence
   - Restricted content check
   
5. Brand Alignment (if applicable)
   - Voice consistency
   - Message alignment
   - Visual identity consistency
   
6. Technical Quality
   - Grammar and spelling
   - Readability
   - Hashtag effectiveness
   - Call-to-action strength
   
7. Specific Improvement Suggestions
   - Provide rewrites for problematic sections
   - Suggest alternative approaches

Review:
"""
    
    def _get_default_template(self) -> str:
        """
        Get a default template.
        
        Returns:
            A template string.
        """
        return """
You are an Instagram content expert. Your task is to process the given content
according to Instagram best practices and the specified parameters.

CONTEXT:
{knowledge_context}

PARAMETERS:
{parameters}

CONTENT:
{content}

Provide your response:
""" 