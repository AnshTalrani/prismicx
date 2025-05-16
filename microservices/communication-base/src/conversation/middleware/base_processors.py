"""
Base Middleware Processors

This module provides base implementations for common middleware processors
used in the conversation pipeline.
"""

import logging
from typing import Dict, Any, Tuple, Optional, List
import re
import json
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


async def intent_detection_processor(
    message: str, 
    context: Dict[str, Any],
    bot_type: str
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Detects intent from user message and adds to context.
    
    Args:
        message: The user message
        context: The current conversation context
        bot_type: The type of bot
        
    Returns:
        Tuple of (unchanged message, context updates)
    """
    logger.info(f"Processing intent detection for bot type {bot_type}")
    
    # This is a simplified mock implementation
    # In a real system, this would use NLU service or ML model
    
    context_updates = {}
    
    # Example simple keyword-based intent detection
    intents = {
        # General intents
        "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
        "goodbye": ["bye", "goodbye", "see you", "farewell", "exit", "quit", "end conversation"],
        "thank_you": ["thanks", "thank you", "appreciate it", "grateful", "thank"],
        "help": ["help", "assist", "support", "guide", "how do i", "how to"],
        
        # Sales specific intents
        "pricing_inquiry": ["price", "cost", "how much", "pricing", "discount", "offer"],
        "product_inquiry": ["product", "feature", "specification", "compare", "difference"],
        "purchase_intent": ["buy", "purchase", "order", "get one", "acquire", "add to cart"],
        
        # Consultancy specific intents
        "business_advice": ["advice", "strategy", "plan", "improve", "recommendation"],
        "market_analysis": ["market", "industry", "analysis", "trend", "competitor"],
        "process_optimization": ["optimize", "improve process", "efficiency", "streamline"],
        
        # Support specific intents
        "technical_issue": ["issue", "problem", "error", "bug", "doesn't work", "not working"],
        "account_management": ["account", "password", "login", "profile", "settings"],
        "refund_request": ["refund", "money back", "cancel order", "return"]
    }
    
    # Detect intent based on keywords
    message_lower = message.lower()
    detected_intent = None
    max_confidence = 0.0
    
    for intent, keywords in intents.items():
        # Skip non-relevant intents for the bot type
        if (
            (bot_type == "sales" and intent.startswith(("consultancy_", "support_"))) or
            (bot_type == "consultancy" and intent.startswith(("sales_", "support_"))) or
            (bot_type == "support" and intent.startswith(("sales_", "consultancy_")))
        ):
            continue
            
        for keyword in keywords:
            if keyword in message_lower:
                # Simple confidence calculation
                # In a real system, this would use more sophisticated methods
                confidence = 0.7 + (len(keyword) / 50)  # Longer matches = higher confidence
                if confidence > max_confidence:
                    max_confidence = confidence
                    detected_intent = {
                        "name": intent,
                        "confidence": min(confidence, 0.95),  # Cap at 0.95
                        "parameters": {}
                    }
    
    # If no intent matched, use fallback
    if not detected_intent:
        detected_intent = {
            "name": "unknown",
            "confidence": 0.3,
            "parameters": {}
        }
    
    context_updates["detected_intent"] = detected_intent
    logger.info(f"Detected intent: {detected_intent['name']} with confidence {detected_intent['confidence']}")
    
    return message, context_updates


async def entity_extraction_processor(
    message: str, 
    context: Dict[str, Any],
    bot_type: str
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Extracts entities from user message and adds to context.
    
    Args:
        message: The user message
        context: The current conversation context
        bot_type: The type of bot
        
    Returns:
        Tuple of (unchanged message, context updates)
    """
    logger.info(f"Processing entity extraction for bot type {bot_type}")
    
    # This is a simplified mock implementation
    # In a real system, this would use NER models or services
    
    context_updates = {"entities": {}}
    
    # Example simple regex-based entity extraction
    entity_patterns = {
        # Contact information
        "email": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "contact_info"),
        "phone": (r'\b(?:\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b', "contact_info"),
        
        # Numeric entities
        "amount": (r'\$\s?\d+(?:\.\d{2})?|\d+\s?(?:dollars|USD)', "numeric"),
        "percentage": (r'\d+(?:\.\d+)?\s?%', "numeric"),
        "date": (r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', "datetime"),
        
        # Product entities
        "product_name": (r'(?:product|item|model)\s([A-Z][A-Za-z0-9-]+)', "product"),
        "product_category": (r'(?:category|type|section)\s([A-Za-z0-9-]+)', "product"),
    }
    
    # Extract entities using regex patterns
    for entity_name, (pattern, category) in entity_patterns.items():
        matches = re.findall(pattern, message)
        if matches:
            # Only store the first match for simplicity
            match_value = matches[0]
            context_updates["entities"][entity_name] = {
                "value": match_value,
                "confidence": 0.8,  # Simple confidence score
                "source": "user",
                "category": category,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"Extracted entity {entity_name}: {match_value}")
    
    return message, context_updates


async def message_summarization_processor(
    message: str, 
    context: Dict[str, Any],
    bot_type: str
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Summarizes conversation if it gets too long.
    
    Args:
        message: The user message
        context: The current conversation context
        bot_type: The type of bot
        
    Returns:
        Tuple of (unchanged message, context updates)
    """
    logger.info(f"Processing message summarization for bot type {bot_type}")
    
    # This is a simplified mock implementation
    # In a real system, this would use summarization models
    
    context_updates = {}
    messages = context.get("messages", [])
    
    # Check if we need to summarize (if many messages)
    if len(messages) > 20:  # Threshold for summarization
        # In a real implementation, this would use an LLM to create the summary
        # For this mock, we'll just create a simple placeholder
        
        # Count messages by role
        user_msg_count = sum(1 for m in messages if m.get("role") == "user")
        assistant_msg_count = sum(1 for m in messages if m.get("role") == "assistant")
        
        # Create simple summary
        summary = (
            f"Conversation summary: {user_msg_count} user messages and "
            f"{assistant_msg_count} assistant messages. "
            f"Current state: {context.get('current_state', 'unknown')}. "
            f"Main topics: {', '.join(context.get('detected_topics', ['general discussion']))}"
        )
        
        context_updates["conversation_summary"] = summary
        
        # Keep only recent messages
        # In a real implementation, we might keep the summary as a system message
        # and remove older messages
        if len(messages) > 30:  # If very long conversation
            recent_messages = messages[-10:]  # Keep only last 10 messages
            context_updates["messages"] = recent_messages
            logger.info(f"Summarized conversation and kept only last 10 messages")
    
    return message, context_updates


async def sentiment_analysis_processor(
    message: str, 
    context: Dict[str, Any],
    bot_type: str
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Analyzes sentiment of user message.
    
    Args:
        message: The user message
        context: The current conversation context
        bot_type: The type of bot
        
    Returns:
        Tuple of (unchanged message, context updates)
    """
    logger.info(f"Processing sentiment analysis for bot type {bot_type}")
    
    # This is a simplified mock implementation
    # In a real system, this would use sentiment analysis models
    
    context_updates = {}
    
    # Simple keyword-based sentiment analysis
    positive_words = ["happy", "good", "great", "excellent", "awesome", "thanks", 
                     "thank", "appreciate", "like", "love", "helpful", "wonderful"]
    negative_words = ["bad", "terrible", "awful", "horrible", "disappointing", 
                     "useless", "hate", "dislike", "angry", "upset", "frustrated"]
    
    message_lower = message.lower()
    positive_count = sum(1 for word in positive_words if word in message_lower)
    negative_count = sum(1 for word in negative_words if word in message_lower)
    
    # Calculate sentiment score (-1.0 to 1.0)
    total_count = positive_count + negative_count
    if total_count > 0:
        sentiment_score = (positive_count - negative_count) / total_count
    else:
        sentiment_score = 0.0  # Neutral if no sentiment words
    
    # Determine sentiment label
    if sentiment_score > 0.3:
        sentiment = "positive"
    elif sentiment_score < -0.3:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    # Add sentiment to context
    context_updates["sentiment"] = {
        "score": sentiment_score,
        "label": sentiment,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Detected sentiment: {sentiment} (score: {sentiment_score:.2f})")
    
    # Track sentiment history
    sentiment_history = context.get("sentiment_history", [])
    sentiment_history.append({
        "score": sentiment_score,
        "label": sentiment,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Keep only recent history
    if len(sentiment_history) > 10:
        sentiment_history = sentiment_history[-10:]
    
    context_updates["sentiment_history"] = sentiment_history
    
    return message, context_updates


# Post-processing middlewares

async def response_formatting_processor(
    response: str,
    original_message: str,
    context: Dict[str, Any],
    bot_type: str
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Formats the response based on bot type and conversation context.
    
    Args:
        response: The generated response
        original_message: The original user message
        context: The conversation context
        bot_type: The type of bot
        
    Returns:
        Tuple of (formatted response, context updates)
    """
    logger.info(f"Formatting response for bot type {bot_type}")
    
    context_updates = {}
    formatted_response = response
    
    # Add typing-like delays for human-like response
    # This would be handled at the client level
    # We just add metadata to indicate delay characteristics
    
    # Calculate typing delay based on response length
    words = len(response.split())
    typing_delay = min(1.5, 0.5 + (words * 0.03))  # 0.5s base + 0.03s per word, max 1.5s
    
    # Add metadata for typing simulation
    context_updates["response_metadata"] = {
        "typing_delay": typing_delay,
        "response_length": len(response),
        "word_count": words
    }
    
    # Personalization based on bot type
    if bot_type == "sales" and context.get("user_info", {}).get("profile", {}).get("name"):
        user_name = context.get("user_info", {}).get("profile", {}).get("name")
        # If it's a greeting state, personalize with name
        if context.get("current_state") in ["greeting", "welcome", "introduction"]:
            formatted_response = f"Hi {user_name}, {formatted_response}"
    
    # Add contextual awareness if available (e.g., continue a previous point)
    if context.get("conversation_flags", {}).get("continue_point"):
        continue_point = context.get("conversation_flags", {}).get("continue_point")
        if "As I was saying" not in formatted_response and "mentioned earlier" not in formatted_response:
            formatted_response = f"As I was saying about {continue_point}, {formatted_response}"
        # Clear the continue flag
        context_updates["conversation_flags"] = context.get("conversation_flags", {})
        context_updates["conversation_flags"]["continue_point"] = None
    
    logger.info(f"Response formatted with typing delay: {typing_delay}s")
    return formatted_response, context_updates


async def response_enhancement_processor(
    response: str,
    original_message: str,
    context: Dict[str, Any],
    bot_type: str
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Enhances the response with additional information or formatting.
    
    Args:
        response: The generated response
        original_message: The original user message
        context: The conversation context
        bot_type: The type of bot
        
    Returns:
        Tuple of (enhanced response, context updates)
    """
    logger.info(f"Enhancing response for bot type {bot_type}")
    
    context_updates = {}
    enhanced_response = response
    
    # Add sentiment-based enhancement
    sentiment = context.get("sentiment", {}).get("label")
    if sentiment == "negative":
        # For negative sentiment, add empathy
        if bot_type in ["support", "consultancy"] and "I understand" not in enhanced_response.lower():
            enhanced_response = f"I understand your concern. {enhanced_response}"
    
    # Add bot-specific enhancements
    if bot_type == "sales":
        # Check if we should add product info
        if any(keyword in enhanced_response.lower() for keyword in ["product", "offer", "feature"]):
            # Add call to action
            if "Would you like" not in enhanced_response and "?" in enhanced_response:
                enhanced_response += " Would you like to learn more about our special offers?"
    
    elif bot_type == "support":
        # Check if it's a solution response
        if any(keyword in enhanced_response.lower() for keyword in ["solve", "fix", "solution"]):
            # Add follow-up question
            if "resolve your issue" not in enhanced_response and "?" in enhanced_response:
                enhanced_response += " Did this help resolve your issue?"
    
    # Track response characteristics for analytics
    context_updates["response_analytics"] = {
        "response_type": "enhanced" if enhanced_response != response else "standard",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Response enhanced based on context")
    return enhanced_response, context_updates 