"""Builder for creating specialized conversation chains."""

from typing import Optional, Dict
from langchain.memory import ConversationSummaryMemory
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.config.bot_configs import BOT_CONFIGS
from src.langchain_components.retriever import get_retriever
from src.integrations.mlops_integration import mlops
from src.session.session_manager import session_manager

def create_prompt(system_message: str, user_profile: Optional[Dict] = None) -> ChatPromptTemplate:
    """
    Creates a prompt template with optional user context.
    
    Args:
        system_message: Base system message for the bot
        user_profile: Optional user profile containing preferences and pain points
    """
    if user_profile:
        context = (f"\nUser Context - "
                  f"Preferences: {user_profile.get('preferences', {})} "
                  f"Pain Points: {user_profile.get('pain_points', [])}")
        system_message += context
    
    return ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])

def build_chain(
    bot_config: Dict,
    user_profile: Optional[Dict] = None,
    session_id: Optional[str] = None
) -> ConversationalRetrievalChain:
    """
    Builds a conversation chain using the provided configuration.
    
    Args:
        bot_config: Configuration dictionary containing bot settings
        user_profile: Optional user profile for context
        session_id: Optional session ID for memory management
    """
    # Get callbacks for monitoring
    callbacks = mlops.get_callbacks()
    
    # Core components
    llm = ChatOpenAI(
        model_name=bot_config.get("model_name", "gpt-3.5-turbo"),
        temperature=bot_config.get("temperature", 0.7),
        callbacks=callbacks
    )
    
    # Get session-specific memory if available
    memory = session_manager.get_session_memory(session_id) if session_id else None
    if not memory:
        memory = ConversationSummaryMemory(
            llm=llm,
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=bot_config.get("memory_tokens", 1000)
        )
    
    retriever = get_retriever(bot_config["sources"])
    prompt = create_prompt(bot_config["system_message"], user_profile)
    
    # Build chain
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=True,
        callbacks=callbacks
    )

def create_specialized_chain(
    llm,
    memory,
    user_profile=None,
    bot_type="consultancy",
    adapter=None
):
    """
    Creates a specialized chain for a specific bot type.
    
    Args:
        llm: The language model (HuggingFacePipeline instance)
        memory: Conversation memory
        user_profile: User profile for context
        bot_type: Type of bot ("consultancy", "sales", "support")
        adapter: Optional adapter name for specialized domain handling
    """
    config = BOT_CONFIGS[bot_type]
    
    # Create base prompt
    system_message = config["system_message"]
    
    # Add adapter context if specified
    if adapter:
        system_message += f"\nUsing specialized {adapter} adapter for domain-specific expertise."
    
    # Add user profile if available
    if user_profile:
        system_message += f"\nUser Context - Preferences: {user_profile.get('preferences', {})} Pain Points: {user_profile.get('pain_points', [])}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])
    
    # Modify retriever config based on adapter if needed
    retriever_kwargs = {}
    if adapter and "actions" in config and f"use_{adapter}_adapter" in config["actions"]:
        action_config = config["actions"][f"use_{adapter}_adapter"]
        retrieval_domains = action_config.get("retrieval_domains", [])
        if retrieval_domains:
            retriever_kwargs["domains"] = retrieval_domains
    
    # Create the chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=True
    )
    
    return chain 