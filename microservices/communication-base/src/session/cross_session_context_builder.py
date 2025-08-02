"""
Cross-session context builder for maintaining context across user sessions.

This module provides functionality to track and analyze entity data across
multiple sessions, enabling seamless conversation continuity and improved
personalization.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from src.config.config_inheritance import ConfigInheritance
from src.clients.system_users_conversation_repository_client import SystemUsersRepositoryClient
from src.clients.campaign_users_repository_client import CampaignUsersRepositoryClient
from src.langchain_components.nlp.hybrid_processor import hybrid_processor
from src.storage.entity_history_tracker import EntityHistoryTracker
from src.analytics.entity_trend_analyzer import EntityTrendAnalyzer

class CrossSessionContextBuilder:
    """
    Cross-session context builder for maintaining context across user sessions.
    
    This class provides functionality to:
    1. Track entity data across multiple sessions
    2. Analyze trends in user interactions
    3. Build contextual background for new sessions
    """
    
    def __init__(self):
        """Initialize the cross-session context builder."""
        self.logger = logging.getLogger(__name__)
        self.config_inheritance = ConfigInheritance()
        self.system_repo_client = SystemUsersRepositoryClient()
        self.campaign_repo_client = CampaignUsersRepositoryClient()
        self.entity_history_tracker = EntityHistoryTracker()
        self.entity_trend_analyzer = EntityTrendAnalyzer()
    
    async def build_cross_session_context(
        self, 
        user_id: str, 
        bot_type: str,
        campaign_id: Optional[str] = None,
        context_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build context from previous sessions for a user.
        
        Args:
            user_id: User identifier
            bot_type: Type of bot
            campaign_id: Optional campaign identifier
            context_depth: How far back to look for context (sessions/days)
            
        Returns:
            Cross-session context dictionary
        """
        try:
            # Get config for this bot type
            config = self.config_inheritance.get_config(bot_type)
            session_config = config.get("session", {})
            
            # Use provided context depth or get from config
            if context_depth is None:
                context_depth = session_config.get("context_depth", 3)  # Default to 3 sessions
            
            # Determine which repository to use
            if campaign_id:
                historical_data = await self.campaign_repo_client.get_user_history(
                    user_id=user_id,
                    campaign_id=campaign_id,
                    limit=context_depth
                )
            else:
                historical_data = await self.system_repo_client.get_user_history(
                    user_id=user_id,
                    limit=context_depth
                )
            
            # Process historical data
            context = await self._process_historical_data(historical_data, bot_type)
            
            # Add entity trends analysis
            entity_trends = await self._analyze_entity_trends(user_id, bot_type, campaign_id)
            if entity_trends:
                context["entity_trends"] = entity_trends
            
            # Add user profile data
            profile_data = await self._get_user_profile(user_id, bot_type, campaign_id)
            if profile_data:
                context["user_profile"] = profile_data
            
            # Add last conversation summary if available
            last_conversation = await self._get_last_conversation_summary(user_id, bot_type, campaign_id)
            if last_conversation:
                context["last_conversation"] = last_conversation
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error building cross-session context: {e}")
            return {}
    
    async def _process_historical_data(
        self, 
        historical_data: List[Dict[str, Any]],
        bot_type: str
    ) -> Dict[str, Any]:
        """
        Process historical session data into a usable context.
        
        Args:
            historical_data: List of historical session data
            bot_type: Type of bot
            
        Returns:
            Processed context dictionary
        """
        if not historical_data:
            return {}
        
        try:
            # Initialize context
            context = {
                "entity_history": {},
                "conversation_topics": [],
                "question_topics": [],
                "frequent_concerns": []
            }
            
            all_entities = []
            all_topics = []
            all_questions = []
            
            # Process each historical session
            for session_data in historical_data:
                # Process entities from this session
                session_entities = session_data.get("entities", [])
                if session_entities:
                    all_entities.extend(session_entities)
                
                # Process topics from this session
                session_topics = session_data.get("topics", [])
                if session_topics:
                    all_topics.extend(session_topics)
                
                # Process questions from this session
                session_questions = session_data.get("questions", [])
                if session_questions:
                    all_questions.extend(session_questions)
            
            # Group entities by type
            entity_by_type = {}
            for entity in all_entities:
                entity_type = entity.get("type")
                if entity_type:
                    if entity_type not in entity_by_type:
                        entity_by_type[entity_type] = []
                    entity_by_type[entity_type].append(entity)
            
            # Store entity history
            context["entity_history"] = entity_by_type
            
            # Extract conversation topics (top 5)
            topic_counts = {}
            for topic in all_topics:
                topic_name = topic.get("name")
                if topic_name:
                    topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
            
            # Sort topics by frequency
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            context["conversation_topics"] = [topic for topic, count in sorted_topics[:5]]
            
            # Extract question topics
            question_topics = {}
            for question in all_questions:
                question_topic = question.get("topic")
                if question_topic:
                    question_topics[question_topic] = question_topics.get(question_topic, 0) + 1
            
            # Sort question topics by frequency
            sorted_question_topics = sorted(question_topics.items(), key=lambda x: x[1], reverse=True)
            context["question_topics"] = [topic for topic, count in sorted_question_topics[:5]]
            
            # Extract frequent concerns
            concerns = []
            for entity in all_entities:
                if entity.get("type") == "PAIN_POINT" or entity.get("type") == "CONCERN":
                    concerns.append(entity.get("value"))
            
            # Count concern frequencies
            concern_counts = {}
            for concern in concerns:
                if concern:
                    concern_counts[concern] = concern_counts.get(concern, 0) + 1
            
            # Sort concerns by frequency
            sorted_concerns = sorted(concern_counts.items(), key=lambda x: x[1], reverse=True)
            context["frequent_concerns"] = [concern for concern, count in sorted_concerns[:3]]
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error processing historical data: {e}")
            return {}
    
    async def _analyze_entity_trends(
        self, 
        user_id: str, 
        bot_type: str,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze trends in entity data for a user.
        
        Args:
            user_id: User identifier
            bot_type: Type of bot
            campaign_id: Optional campaign identifier
            
        Returns:
            Entity trends dictionary
        """
        try:
            # Get entity history from the tracker
            entity_history = await self.entity_history_tracker.get_entity_history(
                user_id=user_id,
                bot_type=bot_type,
                campaign_id=campaign_id
            )
            
            if not entity_history:
                return {}
            
            # Analyze trends
            trends = await self.entity_trend_analyzer.analyze_trends(entity_history)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing entity trends: {e}")
            return {}
    
    async def _get_user_profile(
        self, 
        user_id: str, 
        bot_type: str,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user profile data from repository.
        
        Args:
            user_id: User identifier
            bot_type: Type of bot
            campaign_id: Optional campaign identifier
            
        Returns:
            User profile dictionary
        """
        try:
            # Determine which repository to use
            if campaign_id:
                profile = await self.campaign_repo_client.get_user_profile(
                    user_id=user_id,
                    campaign_id=campaign_id
                )
            else:
                profile = await self.system_repo_client.get_user_profile(
                    user_id=user_id
                )
            
            return profile or {}
            
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            return {}
    
    async def _get_last_conversation_summary(
        self, 
        user_id: str, 
        bot_type: str,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary of the last conversation with the user.
        
        Args:
            user_id: User identifier
            bot_type: Type of bot
            campaign_id: Optional campaign identifier
            
        Returns:
            Last conversation summary dictionary
        """
        try:
            # Determine which repository to use
            if campaign_id:
                last_session = await self.campaign_repo_client.get_last_session(
                    user_id=user_id,
                    campaign_id=campaign_id
                )
            else:
                last_session = await self.system_repo_client.get_last_session(
                    user_id=user_id
                )
            
            if not last_session:
                return {}
            
            # Extract summary
            summary = last_session.get("summary", "")
            
            # Extract key entities
            entities = last_session.get("entities", [])
            key_entities = [e for e in entities if e.get("importance", 0) > 0.7]
            
            # Get timestamp
            timestamp = last_session.get("timestamp", 0)
            time_ago = self._format_time_ago(timestamp)
            
            return {
                "summary": summary,
                "key_entities": key_entities,
                "time_ago": time_ago
            }
            
        except Exception as e:
            self.logger.error(f"Error getting last conversation summary: {e}")
            return {}
    
    def _format_time_ago(self, timestamp: float) -> str:
        """
        Format timestamp as a human-readable time ago string.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            Human-readable time ago string
        """
        if not timestamp:
            return "unknown time ago"
        
        now = time.time()
        seconds_ago = now - timestamp
        
        if seconds_ago < 60:
            return "just now"
        elif seconds_ago < 3600:
            minutes = int(seconds_ago / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds_ago < 86400:
            hours = int(seconds_ago / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds_ago < 604800:
            days = int(seconds_ago / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds_ago < 2592000:
            weeks = int(seconds_ago / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            # Format as date
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%B %d, %Y")
    
    async def update_session_context(
        self, 
        session_id: str,
        user_id: str,
        bot_type: str,
        entities: List[Dict[str, Any]],
        campaign_id: Optional[str] = None
    ) -> None:
        """
        Update cross-session context with new entity data.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            bot_type: Type of bot
            entities: List of extracted entities
            campaign_id: Optional campaign identifier
        """
        try:
            # Update entity history tracker
            await self.entity_history_tracker.add_entities(
                user_id=user_id,
                session_id=session_id,
                bot_type=bot_type,
                entities=entities,
                campaign_id=campaign_id
            )
            
            # No need to return anything
            
        except Exception as e:
            self.logger.error(f"Error updating session context: {e}")
    
    async def generate_context_bridge(
        self, 
        user_id: str,
        bot_type: str,
        current_session_id: str,
        campaign_id: Optional[str] = None
    ) -> str:
        """
        Generate a natural language bridge to previous conversation context.
        
        This provides a human-friendly way to reference previous interactions.
        
        Args:
            user_id: User identifier
            bot_type: Type of bot
            current_session_id: Current session identifier
            campaign_id: Optional campaign identifier
            
        Returns:
            Natural language context bridge
        """
        try:
            # Get last conversation summary
            last_conversation = await self._get_last_conversation_summary(
                user_id=user_id,
                bot_type=bot_type,
                campaign_id=campaign_id
            )
            
            if not last_conversation:
                return ""
            
            # Create natural language bridge
            time_ago = last_conversation.get("time_ago", "previously")
            summary = last_conversation.get("summary", "")
            
            # Generate different bridge formats based on bot type
            if bot_type == "consultancy":
                bridge = f"When we spoke {time_ago}, we discussed {summary}"
            elif bot_type == "sales":
                bridge = f"Based on our conversation {time_ago}, you were interested in {summary}"
            elif bot_type == "support":
                bridge = f"In our previous interaction {time_ago}, we worked on {summary}"
            else:
                bridge = f"In our conversation {time_ago}, we talked about {summary}"
            
            return bridge
            
        except Exception as e:
            self.logger.error(f"Error generating context bridge: {e}")
            return ""


# Create singleton instance
cross_session_context_builder = CrossSessionContextBuilder() 