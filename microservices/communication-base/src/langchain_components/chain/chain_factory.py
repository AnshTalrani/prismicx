"""
Factory for creating specialized conversation chains.

This module provides a centralized factory for creating different types of chains
based on bot configuration settings. It supports conversational chains, router chains,
and agent-based chains.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain.chains import ConversationalRetrievalChain, LLMChain, SequentialChain
from langchain.chains.router import MultiRouteChain, LLMRouterChain
from langchain.agents import AgentExecutor, OpenAIFunctionsAgent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.tools import BaseTool

class ChainFactory:
    """
    Factory for creating specialized conversation chains.
    
    This class handles the creation of different types of chains based on bot configuration,
    ensuring proper integration with LLM models, memory, and retrievers.
    """
    
    def __init__(self, llm_manager, config_integration, session_manager, rag_coordinator):
        """
        Initialize with required dependencies.
        
        Args:
            llm_manager: Manager for LLM models and adapters
            config_integration: Integration with the config system
            session_manager: Session management service
            rag_coordinator: RAG coordination service
        """
        self.llm_manager = llm_manager
        self.config_integration = config_integration
        self.session_manager = session_manager
        self.rag_coordinator = rag_coordinator
        self.logger = logging.getLogger(__name__)
    
    def create_chain(self, bot_type: str, session_id: str):
        """
        Create appropriate chain based on bot type and configuration.
        
        Args:
            bot_type: Type of bot ("consultancy", "sales", "support")
            session_id: Session identifier
            
        Returns:
            An appropriate LangChain chain instance
        """
        config = self.config_integration.get_config(bot_type)
        chain_type = config.get("chain_config.type", "conversational")
        
        # Get memory from session manager
        memory = self.session_manager.get_memory(session_id)
        
        # Get LLM with any adapters from Phase 1 implementation
        llm = self.llm_manager.get_model_for_session(bot_type, session_id)
        
        # Get RAG retrievers established in Phase 2.2
        retriever = self.rag_coordinator.get_retriever(bot_type, session_id)
        
        if chain_type == "conversational":
            return self._create_conversational_chain(bot_type, llm, memory, config, retriever)
        elif chain_type == "router":
            return self._create_router_chain(bot_type, llm, memory, config, retriever)
        elif chain_type == "agent":
            return self._create_agent_chain(bot_type, llm, memory, config, retriever)
        else:
            self.logger.warning(f"Unknown chain type: {chain_type}, falling back to conversational")
            return self._create_conversational_chain(bot_type, llm, memory, config, retriever)
    
    def _create_conversational_chain(self, bot_type: str, llm: Any, memory: Any, config: Dict, retriever: Any):
        """
        Create a conversational retrieval chain.
        
        Args:
            bot_type: Type of bot
            llm: Language model
            memory: Conversation memory
            config: Bot configuration
            retriever: Document retriever
            
        Returns:
            A ConversationalRetrievalChain instance
        """
        # Get the template from registry
        template = self._get_template(bot_type, config)
        
        # Configure chain parameters from config
        return ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": template},
            return_source_documents=config.get("chain_config.return_sources", True),
            verbose=config.get("chain_config.verbose", True)
        )
    
    def _create_router_chain(self, bot_type: str, llm: Any, memory: Any, config: Dict, retriever: Any):
        """
        Create a router chain for multi-purpose handling.
        
        Args:
            bot_type: Type of bot
            llm: Language model
            memory: Conversation memory
            config: Bot configuration
            retriever: Document retriever
            
        Returns:
            A MultiRouteChain instance
        """
        # Get route definitions from config
        routes = config.get("chain_config.routes", {})
        
        # Create destination chains
        destination_chains = {}
        for route_name, route_config in routes.items():
            if route_config.get("enabled", True):
                dest_chain = self._create_destination_chain(
                    bot_type, route_name, llm, memory, route_config, retriever
                )
                destination_chains[route_name] = dest_chain
        
        # Create router chain
        router_prompt = self._get_router_prompt(bot_type, config)
        router_chain = LLMRouterChain.from_llm(llm, router_prompt)
        
        # Return the complete multi-route chain
        return MultiRouteChain(
            router_chain=router_chain,
            destination_chains=destination_chains,
            default_chain=self._create_conversational_chain(bot_type, llm, memory, config, retriever),
            verbose=config.get("chain_config.verbose", True)
        )
    
    def _create_agent_chain(self, bot_type: str, llm: Any, memory: Any, config: Dict, retriever: Any):
        """
        Create an agent chain for tool usage.
        
        Args:
            bot_type: Type of bot
            llm: Language model
            memory: Conversation memory
            config: Bot configuration
            retriever: Document retriever
            
        Returns:
            An AgentExecutor instance
        """
        # Get tools from config
        tools_config = config.get("chain_config.tools", {})
        tools = self._create_tools(bot_type, tools_config)
        
        # Create agent prompt
        agent_prompt = self._get_agent_prompt(bot_type, config)
        
        # Create the agent
        agent = OpenAIFunctionsAgent.from_llm_and_tools(
            llm=llm,
            tools=tools,
            prompt=agent_prompt
        )
        
        # Return the agent executor
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=config.get("chain_config.verbose", True),
            max_iterations=config.get("chain_config.max_iterations", 5)
        )
    
    def _get_template(self, bot_type: str, config: Dict):
        """
        Get prompt template for the specified bot type.
        
        Args:
            bot_type: Type of bot
            config: Bot configuration
            
        Returns:
            A ChatPromptTemplate instance
        """
        # Get template from the template registry
        # This will be implemented when the template registry is created
        system_message = config.get("chain_config.prompt.system_message", 
                                   f"You are a helpful {bot_type} assistant.")
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
    
    def _get_router_prompt(self, bot_type: str, config: Dict):
        """
        Get router prompt for the specified bot type.
        
        Args:
            bot_type: Type of bot
            config: Bot configuration
            
        Returns:
            A ChatPromptTemplate instance
        """
        # Get route definitions for prompt
        routes = config.get("chain_config.routes", {})
        route_descriptions = "\n".join([
            f"- {name}: {route.get('description', 'No description')}"
            for name, route in routes.items()
        ])
        
        system_message = f"""You are a routing assistant for the {bot_type} bot.
Based on the user's question, route to one of the following destinations:
{route_descriptions}

If the question doesn't fit any category, respond with "DEFAULT".
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}")
        ])
    
    def _get_agent_prompt(self, bot_type: str, config: Dict):
        """
        Get agent prompt for the specified bot type.
        
        Args:
            bot_type: Type of bot
            config: Bot configuration
            
        Returns:
            A ChatPromptTemplate instance
        """
        system_message = config.get("chain_config.agent.system_message", 
                                  f"You are a helpful {bot_type} assistant with access to tools.")
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    def _create_tools(self, bot_type: str, tools_config: Dict) -> List[BaseTool]:
        """
        Create tools based on configuration.
        
        Args:
            bot_type: Type of bot
            tools_config: Tool configuration
            
        Returns:
            List of Tool instances
        """
        # This will be expanded when we implement the tool system
        # For now, return an empty list
        tools = []
        
        # Example of how tools would be created
        # if tools_config.get("calendar", {}).get("enabled", False):
        #     tools.append(CalendarTool())
        # if tools_config.get("web_search", {}).get("enabled", False):
        #     tools.append(WebSearchTool())
            
        return tools
    
    def _create_destination_chain(self, bot_type: str, route_name: str, 
                                 llm: Any, memory: Any, route_config: Dict, retriever: Any):
        """
        Create a destination chain for the router.
        
        Args:
            bot_type: Type of bot
            route_name: Name of the route
            llm: Language model
            memory: Conversation memory
            route_config: Route configuration
            retriever: Document retriever
            
        Returns:
            A Chain instance
        """
        # Get specialized retriever if defined
        specialized_retriever = retriever
        if "retrieval_domains" in route_config:
            domains = route_config.get("retrieval_domains", [])
            if domains:
                specialized_retriever = self.rag_coordinator.get_domain_retriever(
                    bot_type, domains
                )
        
        # Get specialized model if defined
        specialized_llm = llm
        if "model_name" in route_config:
            model_name = route_config.get("model_name")
            specialized_llm = self.llm_manager.get_model(model_name)
            
        # Create template for this route
        system_message = route_config.get("system_message", 
                                        f"You are a {route_name} specialist for the {bot_type} bot.")
        
        template = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        # Create chain
        return ConversationalRetrievalChain.from_llm(
            llm=specialized_llm,
            retriever=specialized_retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": template},
            return_source_documents=route_config.get("return_sources", True),
            verbose=route_config.get("verbose", True)
        ) 