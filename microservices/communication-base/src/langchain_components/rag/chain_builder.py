"""Builds RAG chains using LangChain Expression Language (LCEL)."""

from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_openai import ChatOpenAI

class RAGChainBuilder:
    """Builds specialized RAG chains for different bot types."""
    
    def __init__(self, chain_config: Dict):
        self.chain_config = chain_config
        self.llm = self._init_llm()
        
    def create_condense_question_chain(self):
        """Creates a chain for condensing questions based on chat history."""
        condense_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given the chat history and the latest question, create a standalone question."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        return condense_prompt | self.llm | self._parse_standalone_question
    
    def create_rag_chain(self, retriever, memory, session_id: str):
        """Creates a RAG chain based on configuration."""
        
        async def get_response_template(inputs: Dict) -> ChatPromptTemplate:
            template, analysis = await memory.process_message(
                message=inputs["question"],
                session_id=session_id,
                user_id=inputs["user_id"],
                bot_config=inputs["bot_config"]
            )
            return template
        
        # Build chain components based on config
        components = {
            "template": get_response_template,
            "context": self._build_context_chain(retriever),
            "question": RunnablePassthrough(),
            "chat_history": lambda x: memory.load_memory_variables({})["chat_history"]
        }
        
        # Add config-specific components
        if self.chain_config["prompt"].get("components"):
            for component in self.chain_config["prompt"]["components"]:
                components[component] = self._get_component_handler(component)
        
        chain = (
            RunnableParallel(components)
            | self._format_final_prompt()
            | self.llm
        )
        
        return chain
    
    @staticmethod
    def _parse_standalone_question(llm_response) -> str:
        """Extracts the standalone question from LLM response."""
        return llm_response.content 