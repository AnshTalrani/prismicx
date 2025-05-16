"""Enhanced memory management with bot-specific configurations."""

from typing import Dict, List, Optional
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from .memory_store import RedisMemoryStore, MemoryConfig
from storage.conversation_store import ConversationStore
from storage.user_profile_store import UserProfileStore
from datetime import datetime
from langchain_components.template_engine import DynamicTemplateEngine, TemplateConfig, TemplateType

class EnhancedMemoryManager:
    """Advanced memory management with summarization and analytics."""
    
    def __init__(self):
        self.store = RedisMemoryStore()
        self.conversation_store = ConversationStore()
        self.user_profile_store = UserProfileStore()
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        self.analytics = MemoryAnalytics()
        self.template_engine = DynamicTemplateEngine()
    
    def _get_summary_chain(self, bot_config: Dict):
        """Create a summary chain with bot-specific prompt."""
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", bot_config["memory"]["summarization_prompt"]),
            MessagesPlaceholder(variable_name="chat_history")
        ])
        return summary_prompt | self.llm
    
    async def get_memory_for_session(
        self, 
        session_id: str, 
        bot_config: Dict
    ) -> List[BaseMessage]:
        """Get memory with bot-specific summarization."""
        history = self.store.get_history(session_id, bot_config)
        messages = history.messages
        
        memory_config = bot_config["memory"]
        if len(messages) > memory_config["window_size"]:
            summary_chain = self._get_summary_chain(bot_config)
            summary = await self.summarize_conversation(
                messages[:-memory_config["window_size"]], 
                summary_chain
            )
            messages = [AIMessage(content=summary)] + messages[-memory_config["window_size"]:]
            
        return messages
    
    async def summarize_conversation(self, messages: List[BaseMessage], summary_chain: RunnablePassthrough) -> str:
        """Create a summary of the conversation."""
        response = await summary_chain.ainvoke({"chat_history": messages})
        return response.content
    
    async def get_standalone_question(
        self, 
        question: str, 
        chat_history: List[BaseMessage]
    ) -> str:
        """Convert a follow-up question into a standalone question."""
        response = await self.condense_chain.ainvoke({
            "chat_history": chat_history,
            "question": question
        })
        return response.content
    
    async def end_session(
        self,
        session_id: str,
        user_id: str,
        bot_config: Dict
    ):
        """End a session and save summary to long-term storage."""
        # Get current session messages
        history = self.store.get_history(session_id, bot_config)
        messages = history.messages
        
        if not messages:
            return
            
        # Generate summary
        summary_chain = self._get_summary_chain(bot_config)
        summary = await self.summarize_conversation(messages, summary_chain)
        
        # Get conversation analysis
        analysis = await self.analytics.analyze_conversation(messages, bot_config)
        
        # Save to long-term storage
        await self.conversation_store.save_summary(
            session_id=session_id,
            user_id=user_id,
            bot_type=bot_config.get("bot_type", "unknown"),
            summary=summary,
            analysis=analysis
        )
        
        # Update user profile with insights
        await self.user_profile_store.update_user_insights(
            user_id=user_id,
            bot_type=bot_config.get("bot_type", "unknown"),
            insights=analysis
        )
    
    async def get_historical_context(
        self,
        user_id: str,
        bot_config: Dict
    ) -> str:
        """Get relevant historical context for a new session."""
        return await self.conversation_store.get_context_for_session(
            user_id=user_id,
            bot_type=bot_config.get("bot_type", "unknown")
        )
    
    async def process_message(self, message: str, session_id: str, user_id: str, bot_config: Dict):
        """Process each message with both real-time and periodic analysis."""
        # Get real-time analysis
        analysis = await self.analytics.analyze_message(
            message, session_id, bot_config
        )
        
        # Get user profile and history
        user_profile = await self.user_profile_store.get_user_profile(user_id)
        conversation_history = await self.get_memory_for_session(session_id, bot_config)
        
        # Determine conversation stage
        stage = self._determine_stage(conversation_history)
        
        # Generate appropriate template
        template_config = TemplateConfig(
            bot_type=bot_config["bot_type"],
            conversation_stage=stage,
            template_type=TemplateType.RESPONSE,
            style_preferences=user_profile["preferences"],
            required_components=self._get_required_components(analysis)
        )
        
        template = await self.template_engine.generate_template(
            analysis_results=analysis,
            user_profile=user_profile,
            template_config=template_config,
            campaign_data=bot_config.get("campaign_data")
        )
        
        return template, analysis

    async def _create_periodic_summary(self, session_id: str, user_id: str, bot_config: Dict):
        """Create periodic summaries for long-term context."""
        messages = await self.get_memory_for_session(session_id, bot_config)
        summary = await self.summarize_conversation(messages, self._get_summary_chain(bot_config))
        
        # Save periodic summary
        await self.conversation_store.save_summary(
            session_id=session_id,
            user_id=user_id,
            bot_type=bot_config.get("bot_type", "unknown"),
            summary=summary,
            summary_type="periodic",
            timestamp=datetime.utcnow()
        ) 