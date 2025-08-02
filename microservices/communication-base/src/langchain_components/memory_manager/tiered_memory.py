"""
Tiered memory system with multiple retention policies based on importance.

This module provides a tiered memory implementation that manages information at 
different levels of retention (short-term, medium-term, and long-term) based on 
importance and relevance.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta

from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, AIMessage, HumanMessage

class TieredMemory:
    """
    Tiered memory system with different retention policies.
    
    This class manages multiple memory tiers (short-term, medium-term, long-term) with
    different retention policies, automatically promoting important information to
    longer-term memory and consolidating/pruning as needed.
    """
    
    def __init__(
        self,
        llm: Any,
        session_manager: Any,
        session_id: str,
        bot_type: str,
        short_term_window: int = 10,
        medium_term_window: int = 50,
        long_term_capacity: int = 20,
        memory_key: str = "chat_history",
        importance_threshold: float = 0.7,
        **kwargs
    ):
        """
        Initialize tiered memory system.
        
        Args:
            llm: LLM for summarization and importance assessment
            session_manager: Session management service
            session_id: Session identifier
            bot_type: Type of bot
            short_term_window: Number of recent messages in short-term memory
            medium_term_window: Number of messages in medium-term memory
            long_term_capacity: Number of summaries in long-term memory
            memory_key: Key to use for memory in chain inputs/outputs
            importance_threshold: Threshold for promoting to higher tiers
        """
        self.llm = llm
        self.session_manager = session_manager
        self.session_id = session_id
        self.bot_type = bot_type
        self.short_term_window = short_term_window
        self.medium_term_window = medium_term_window
        self.long_term_capacity = long_term_capacity
        self.memory_key = memory_key
        self.importance_threshold = importance_threshold
        self.logger = logging.getLogger(__name__)
        
        # Initialize memory tiers
        self.short_term = ConversationBufferWindowMemory(
            memory_key=memory_key,
            return_messages=True,
            k=short_term_window
        )
        
        self.medium_term = []  # List of (timestamp, message, importance) tuples
        self.long_term = []    # List of (timestamp, summary, topics) tuples
        
        # Track when we last consolidated memory
        self.last_consolidation = time.time()
        self.consolidation_interval = 3600  # 1 hour
        
        # Load existing memory if available
        self._load_from_session()
    
    def _load_from_session(self) -> None:
        """
        Load memory from session if available.
        """
        try:
            tiered_memory = self.session_manager.get_tiered_memory(self.session_id)
            if tiered_memory:
                if "short_term" in tiered_memory and tiered_memory["short_term"]:
                    # Recreate messages
                    messages = []
                    for msg in tiered_memory["short_term"]:
                        if msg["type"] == "human":
                            messages.append(HumanMessage(content=msg["content"]))
                        else:
                            messages.append(AIMessage(content=msg["content"]))
                    
                    self.short_term.chat_memory.messages = messages
                
                if "medium_term" in tiered_memory:
                    self.medium_term = tiered_memory["medium_term"]
                
                if "long_term" in tiered_memory:
                    self.long_term = tiered_memory["long_term"]
                
                self.logger.info(f"Loaded tiered memory from session {self.session_id}")
        except Exception as e:
            self.logger.warning(f"Failed to load tiered memory from session: {e}")
    
    def _save_to_session(self) -> None:
        """
        Save memory to session.
        """
        try:
            # Convert short-term messages to serializable format
            short_term_messages = []
            for msg in self.short_term.chat_memory.messages:
                short_term_messages.append({
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content
                })
            
            tiered_memory = {
                "short_term": short_term_messages,
                "medium_term": self.medium_term,
                "long_term": self.long_term
            }
            
            self.session_manager.store_tiered_memory(
                self.session_id, 
                tiered_memory
            )
            self.logger.debug(f"Saved tiered memory to session {self.session_id}")
        except Exception as e:
            self.logger.warning(f"Failed to save tiered memory to session: {e}")
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save context to memory tiers.
        
        Args:
            inputs: Input values
            outputs: Output values
        """
        # Save to short-term memory
        self.short_term.save_context(inputs, outputs)
        
        # Assess importance
        importance = self._assess_importance(inputs, outputs)
        
        # If important, also add to medium-term
        if importance >= self.importance_threshold:
            self._add_to_medium_term(inputs, outputs, importance)
        
        # Check if we should consolidate memory
        if time.time() - self.last_consolidation > self.consolidation_interval:
            self._consolidate_memory()
            self.last_consolidation = time.time()
        
        # Save all memory tiers to session
        self._save_to_session()
    
    def _assess_importance(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> float:
        """
        Assess the importance of a conversation turn.
        
        Args:
            inputs: Input values
            outputs: Output values
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        # Use LLM to assess importance
        try:
            input_text = inputs.get("question", "")
            output_text = outputs.get("answer", "")
            
            prompt = f"""
            Analyze the following conversation turn and rate its importance from 0.0 to 1.0.
            High importance (0.8-1.0) should be given to messages that:
            - Contain key decisions or commitments
            - Introduce critical new information
            - Represent significant shifts in the conversation
            - Include personal or sensitive information that should be remembered
            
            Human: {input_text}
            AI: {output_text}
            
            Provide only a single number as your response (e.g., 0.7).
            """
            
            importance_str = self.llm.predict(prompt).strip()
            
            # Try to extract a float value
            try:
                importance = float(importance_str)
                importance = max(0.0, min(1.0, importance))  # Clamp to [0, 1]
                return importance
            except ValueError:
                self.logger.warning(f"Failed to parse importance value: {importance_str}")
                return 0.5  # Default to medium importance
                
        except Exception as e:
            self.logger.warning(f"Failed to assess importance: {e}")
            return 0.5  # Default to medium importance
    
    def _add_to_medium_term(self, inputs: Dict[str, Any], outputs: Dict[str, str], importance: float) -> None:
        """
        Add important information to medium-term memory.
        
        Args:
            inputs: Input values
            outputs: Output values
            importance: Importance score
        """
        timestamp = time.time()
        input_text = inputs.get("question", "")
        output_text = outputs.get("answer", "")
        
        self.medium_term.append((timestamp, {
            "human": input_text,
            "ai": output_text
        }, importance))
        
        # Keep medium-term memory within size limit, removing oldest entries
        if len(self.medium_term) > self.medium_term_window:
            # Sort by importance and timestamp (keep recent and important)
            self.medium_term.sort(key=lambda x: (x[2], x[0]), reverse=True)
            
            # Before removing, check if any should be promoted to long-term memory
            for entry in self.medium_term[self.medium_term_window:]:
                if entry[2] >= self.importance_threshold * 1.2:  # Higher threshold for long-term
                    self._promote_to_long_term(entry)
            
            # Trim to window size
            self.medium_term = self.medium_term[:self.medium_term_window]
    
    def _promote_to_long_term(self, entry: Tuple[float, Dict[str, str], float]) -> None:
        """
        Promote important information to long-term memory.
        
        Args:
            entry: Medium-term memory entry (timestamp, messages, importance)
        """
        timestamp, messages, importance = entry
        
        # Skip if already at capacity and this is less important than existing entries
        if (len(self.long_term) >= self.long_term_capacity and 
            importance < min(e[2] for e in self.long_term)):
            return
        
        # Create a summary of the entry
        try:
            human_message = messages["human"]
            ai_message = messages["ai"]
            
            prompt = f"""
            Create a concise, information-dense summary of the following exchange:
            
            Human: {human_message}
            AI: {ai_message}
            
            This summary should capture the key points and critical information only.
            Also identify the main topics discussed as a comma-separated list.
            Format your response as:
            
            SUMMARY: [your summary]
            TOPICS: [comma-separated topics]
            """
            
            response = self.llm.predict(prompt).strip()
            
            # Parse response
            summary = ""
            topics = []
            
            for line in response.split("\n"):
                if line.startswith("SUMMARY:"):
                    summary = line[len("SUMMARY:"):].strip()
                elif line.startswith("TOPICS:"):
                    topics = [t.strip() for t in line[len("TOPICS:"):].split(",")]
            
            # Add to long-term memory
            self.long_term.append((timestamp, summary, topics, importance))
            
            # Keep long-term memory within capacity, removing least important entries
            if len(self.long_term) > self.long_term_capacity:
                self.long_term.sort(key=lambda x: x[3], reverse=True)
                self.long_term = self.long_term[:self.long_term_capacity]
                
        except Exception as e:
            self.logger.warning(f"Failed to promote to long-term memory: {e}")
    
    def _consolidate_memory(self) -> None:
        """
        Consolidate memory by summarizing older conversation chunks.
        """
        # Skip if not enough entries
        if len(self.long_term) < 3:
            return
        
        try:
            # Group related topics
            topic_groups = {}
            
            for entry in self.long_term:
                timestamp, summary, topics, importance = entry
                
                for topic in topics:
                    if topic not in topic_groups:
                        topic_groups[topic] = []
                    
                    topic_groups[topic].append((timestamp, summary, importance))
            
            # For topics with multiple entries, consolidate
            new_long_term = []
            consolidated_entries = set()
            
            for topic, entries in topic_groups.items():
                if len(entries) > 1:
                    # Sort by timestamp
                    entries.sort(key=lambda x: x[0])
                    
                    # Get summaries to consolidate
                    summaries = [entry[1] for entry in entries]
                    timestamps = [entry[0] for entry in entries]
                    importance_scores = [entry[2] for entry in entries]
                    
                    # Track entry indices for later removal
                    for i, (timestamp, _, _, _) in enumerate(self.long_term):
                        if timestamp in timestamps:
                            consolidated_entries.add(i)
                    
                    # Create consolidated summary
                    prompt = f"""
                    Consolidate these related summaries about '{topic}' into a single comprehensive summary:
                    
                    {' '.join([f'{i+1}. {summary}' for i, summary in enumerate(summaries)])}
                    
                    Your consolidated summary should:
                    1. Maintain all key information
                    2. Remove redundancy
                    3. Be chronologically ordered if appropriate
                    4. Be concise but complete
                    """
                    
                    consolidated_summary = self.llm.predict(prompt).strip()
                    avg_importance = sum(importance_scores) / len(importance_scores)
                    
                    # Add consolidated summary
                    new_long_term.append((
                        max(timestamps),  # Use latest timestamp
                        consolidated_summary,
                        [topic],
                        avg_importance
                    ))
            
            # Add non-consolidated entries
            for i, entry in enumerate(self.long_term):
                if i not in consolidated_entries:
                    new_long_term.append(entry)
            
            # Update long-term memory
            self.long_term = new_long_term
            
            # Ensure we respect capacity
            if len(self.long_term) > self.long_term_capacity:
                self.long_term.sort(key=lambda x: x[3], reverse=True)
                self.long_term = self.long_term[:self.long_term_capacity]
            
        except Exception as e:
            self.logger.warning(f"Failed to consolidate memory: {e}")
    
    def get_memory_variables(self) -> Dict[str, Any]:
        """
        Get memory variables for use in chains.
        
        Returns:
            Memory variables
        """
        # Get short-term memory (most recent messages)
        short_term_vars = self.short_term.load_memory_variables({})
        
        # Create full memory context
        memory_context = {
            self.memory_key: short_term_vars[self.memory_key],
            "long_term_memory": self._format_long_term_memory()
        }
        
        return memory_context
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables for use in chains.
        
        Args:
            inputs: Input values
            
        Returns:
            Memory variables
        """
        return self.get_memory_variables()
    
    def _format_long_term_memory(self) -> str:
        """
        Format long-term memory for inclusion in prompt.
        
        Returns:
            Formatted long-term memory
        """
        if not self.long_term:
            return ""
        
        # Sort by timestamp (oldest first)
        sorted_entries = sorted(self.long_term, key=lambda x: x[0])
        
        formatted_entries = []
        for _, summary, topics, _ in sorted_entries:
            topics_str = ", ".join(topics)
            formatted_entries.append(f"- {summary} (Topics: {topics_str})")
        
        return "Long-term memory:\n" + "\n".join(formatted_entries)
    
    def clear(self) -> None:
        """
        Clear all memory tiers.
        """
        self.short_term.clear()
        self.medium_term = []
        self.long_term = []
        self.last_consolidation = time.time()
        
        # Save cleared state
        self._save_to_session() 