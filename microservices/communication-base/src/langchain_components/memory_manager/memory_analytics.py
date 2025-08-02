"""Analytics and template generation for conversation memory."""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from redis import Redis
from ..nlp_processor import NLPProcessor
import json
from config.config_manager import ConfigManager

class ConversationStage(Enum):
    START = "start"
    MIDDLE = "middle"
    END = "end"
    FOLLOW_UP = "follow_up"

class AnalysisResult(BaseModel):
    """Structured analysis results with template guidance."""
    insights: Dict
    template_data: Dict
    nlp_features: Dict  # Added NLP features
    prompt_guidance: str
    stage: ConversationStage

class MemoryAnalytics:
    """Real-time conversation analysis and template generation."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        self.redis_client = Redis.from_url("redis://localhost:6379")
        self.nlp_processor = NLPProcessor()
    
    async def analyze_message(
        self,
        message: str,
        session_id: str,
        bot_config: Dict
    ) -> AnalysisResult:
        """Analyze message using config-driven approach."""
        
        # Get required NLP features
        nlp_config = bot_config["analysis_config"]["nlp_features"]
        nlp_features = self.nlp_processor.process_message(
            message,
            required=nlp_config["required"],
            optional=nlp_config["optional"]
        )
        
        # Load and process template
        template_config = bot_config["analysis_config"]["templates"]["message"]
        template = self.config_manager.get_template(template_config["path"])
        
        # Apply analysis patterns
        analysis = await self._analyze_with_patterns(
            message=message,
            template=template,
            nlp_features=nlp_features,
            patterns=bot_config["analysis_config"]["patterns"]
        )
        
        return analysis
    
    async def _analyze_consultancy_message(
        self, 
        message: str, 
        bot_config: Dict,
        nlp_features: Dict
    ) -> AnalysisResult:
        """Analyze consultancy messages with NLP features."""
        
        # Enhance analysis template with NLP features
        analysis_template = f"""Analyze this message using the following NLP insights:

        Entities Detected:
        - Organizations: {nlp_features["entities"].organizations}
        - People: {nlp_features["entities"].people}
        - Locations: {nlp_features["entities"].locations}
        - Dates: {nlp_features["entities"].dates}

        Key Phrases: {nlp_features["key_phrases"]}
        Language: {nlp_features["language"]}
        Syntax Info: {nlp_features["syntax"]}

        Return a JSON with:
        {{
            "insights": {{
                "immediate_actions": [],
                "pain_points": [],
                "requirements": [],
                "risk_factors": [],
                "listening_patterns": {{
                    "key_concerns": [],
                    "emotional_indicators": [],
                    "unspoken_needs": []
                }},
                "entity_insights": {{
                    "mentioned_companies": [], // From organizations
                    "key_stakeholders": [], // From people
                    "geographical_focus": [], // From locations
                    "timeline_elements": [] // From dates
                }}
            }},
            "template_data": {{
                "expert_terminology": [],
                "covert_patterns": {{
                    "embedded_commands": [],
                    "pacing_statements": [],
                    "leading_phrases": []
                }},
                "strategic_focus": "",
                "delegation_needs": [],
                "anti_ai_elements": {{
                    "natural_pauses": [],
                    "thinking_indicators": [],
                    "personality_traits": []
                }}
            }},
            "nlp_features": {nlp_features},  // Include raw NLP features
            "prompt_guidance": "",
            "stage": "START/MIDDLE/END"
        }}"""
        
        return await self._get_structured_analysis(message, analysis_template)
    
    async def _analyze_sales_message(
        self, 
        message: str, 
        bot_config: Dict,
        nlp_features: Dict
    ) -> AnalysisResult:
        """Analyze sales messages with NLP features."""
        # Similar enhancement for sales analysis
        # Use entities for product mentions, pricing, etc.
        pass
    
    async def _analyze_support_message(
        self, 
        message: str, 
        bot_config: Dict,
        nlp_features: Dict
    ) -> AnalysisResult:
        """Analyze support messages with NLP features."""
        # Similar enhancement for support analysis
        # Use entities for technical terms, error messages, etc.
        pass
    
    async def _get_structured_analysis(self, message: str, template: str) -> AnalysisResult:
        """Get structured analysis using LLM."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", message)
        ])
        
        response = await (prompt | self.llm).ainvoke({"message": message})
        analysis_dict = json.loads(response.content)
        
        return AnalysisResult(**analysis_dict)
    
    async def analyze_conversation(
        self,
        messages: List[BaseMessage],
        bot_config: Dict
    ) -> Dict:
        """End-of-session comprehensive analysis."""
        insights = await self.get_session_insights(messages[0].session_id)
        
        # Get final analysis based on all insights
        final_analysis = await self._get_final_analysis(messages, insights, bot_config)
        
        return {
            "analysis": final_analysis,
            "bot_type": bot_config.get("bot_type", "unknown"),
            "real_time_insights": insights
        }
    
    async def _store_realtime_insights(self, session_id: str, insights: str):
        """Store real-time insights in Redis."""
        key = f"insights:{session_id}"
        await self.redis_client.lpush(key, insights)
        await self.redis_client.expire(key, 3600)  # 1 hour expiry
    
    async def get_session_insights(self, session_id: str) -> List[str]:
        """Get all insights for a session."""
        key = f"insights:{session_id}"
        return await self.redis_client.lrange(key, 0, -1)
    
    async def _get_final_analysis(self, messages: List[BaseMessage], insights: List[str], bot_config: Dict) -> str:
        """Get final analysis based on all insights."""
        # Customize analysis based on bot type
        if "consultancy" in bot_config["system_message"].lower():
            analysis_template = """Based on the conversation and real-time insights:
                1. Strategic decisions made
                2. Action items and timelines
                3. Business challenges identified
                4. Proposed solutions
                
                Real-time insights:
                {insights}
                
                Analyze the full conversation:
                {conversation}
                """
        elif "sales" in bot_config["system_message"].lower():
            analysis_template = """Analyze this sales conversation and extract:
                1. Product interests
                2. Price points discussed
                3. Customer objections
                4. Next steps"""
        else:  # support
            analysis_template = """Analyze this support conversation and extract:
                1. Technical issues reported
                2. Troubleshooting steps taken
                3. Resolution status
                4. Follow-up actions"""
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", analysis_template),
            MessagesPlaceholder(variable_name="chat_history")
        ])
        
        chain = analysis_prompt | self.llm
        response = await chain.ainvoke({
            "chat_history": messages,
            "insights": "\n".join(insights)
        })
        
        return response.content 