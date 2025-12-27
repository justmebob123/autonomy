"""
Conversation Thread Management

Manages conversation threads for multiple models, enabling model-to-model
communication with arbiter oversight.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json

from ..logging_setup import get_logger


class ConversationThread:
    """
    Manages a conversation thread for a single model.
    
    Each model has its own thread that can include:
    - Messages from the user
    - Messages from other models
    - System messages
    - Tool results
    """
    
    def __init__(self, model: str, role: str, max_context_tokens: int = 8192):
        """
        Initialize a conversation thread.
        
        Args:
            model: Model name
            role: Role of this model
            max_context_tokens: Maximum tokens to keep in context
        """
        self.model = model
        self.role = role
        self.max_context_tokens = max_context_tokens
        self.messages: List[Dict] = []
        self.metadata: Dict[str, Any] = {
            "created": datetime.now().isoformat(),
            "message_count": 0,
            "total_tokens": 0
        }
        self.logger = get_logger()
    
    def add_message(self, role: str, content: str, 
                   from_model: Optional[str] = None,
                   metadata: Optional[Dict] = None):
        """
        Add a message to this thread.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            from_model: Source model if message is from another model
            metadata: Additional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        if from_model:
            message["from_model"] = from_model
        
        if metadata:
            message["metadata"] = metadata
        
        self.messages.append(message)
        self.metadata["message_count"] += 1
        
        # Estimate tokens (rough approximation)
        tokens = len(content.split()) * 1.3
        self.metadata["total_tokens"] += tokens
        
        self.logger.debug(f"Added message to {self.model} thread: {role} ({len(content)} chars)")
    
    def get_context(self, max_tokens: Optional[int] = None) -> List[Dict]:
        """
        Get conversation context within token limit.
        
        Args:
            max_tokens: Maximum tokens (uses thread default if None)
        
        Returns:
            List of message dicts
        """
        if max_tokens is None:
            max_tokens = self.max_context_tokens
        
        # Start from most recent and work backwards
        context = []
        total_tokens = 0
        
        for msg in reversed(self.messages):
            # Estimate tokens
            msg_tokens = len(msg["content"].split()) * 1.3
            
            if total_tokens + msg_tokens > max_tokens:
                break
            
            context.insert(0, {
                "role": msg["role"],
                "content": msg["content"]
            })
            total_tokens += msg_tokens
        
        return context
    
    def get_full_history(self) -> List[Dict]:
        """
        Get full conversation history.
        
        Returns:
            List of all messages
        """
        return self.messages.copy()
    
    def clear(self):
        """Clear the conversation thread."""
        self.messages = []
        self.metadata["message_count"] = 0
        self.metadata["total_tokens"] = 0
        self.logger.debug(f"Cleared {self.model} thread")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get thread statistics.
        
        Returns:
            Dict with stats
        """
        return {
            "model": self.model,
            "role": self.role,
            "message_count": self.metadata["message_count"],
            "total_tokens": self.metadata["total_tokens"],
            "created": self.metadata["created"]
        }


class MultiModelConversationManager:
    """
    Manages conversations across multiple models.
    
    This enables:
    - Model-to-model communication
    - Arbiter oversight and intervention
    - Context filtering and routing
    - Shared context management
    """
    
    def __init__(self, arbiter_model: Optional[str] = None):
        """
        Initialize the conversation manager.
        
        Args:
            arbiter_model: Name of the arbiter model (if any)
        """
        self.threads: Dict[str, ConversationThread] = {}
        self.shared_context: List[Dict] = []
        self.arbiter_model = arbiter_model
        self.logger = get_logger()
        
        # Track routing decisions
        self.routing_history: List[Dict] = []
    
    def create_thread(self, model: str, role: str, 
                     max_context_tokens: int = 8192) -> ConversationThread:
        """
        Create a new conversation thread for a model.
        
        Args:
            model: Model name
            role: Role of this model
            max_context_tokens: Maximum context tokens
        
        Returns:
            ConversationThread instance
        """
        thread = ConversationThread(model, role, max_context_tokens)
        self.threads[model] = thread
        
        self.logger.info(f"Created conversation thread for {model} ({role})")
        
        return thread
    
    def get_thread(self, model: str) -> Optional[ConversationThread]:
        """
        Get a conversation thread by model name.
        
        Args:
            model: Model name
        
        Returns:
            ConversationThread or None
        """
        return self.threads.get(model)
    
    def route_message(self, 
                     from_model: str, 
                     to_model: str, 
                     message: str,
                     filter_context: bool = True,
                     arbiter_review: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Route a message from one model to another.
        
        The arbiter can filter/modify the message before routing.
        
        Args:
            from_model: Source model
            to_model: Destination model
            message: Message content
            filter_context: Whether to filter context
            arbiter_review: Arbiter's review decision (if any)
        
        Returns:
            Dict with routing result
        """
        # Apply arbiter modifications if provided
        if arbiter_review:
            if arbiter_review.get("should_modify"):
                message = arbiter_review["modified_message"]
                self.logger.info(f"  Arbiter modified message from {from_model} to {to_model}")
            
            if arbiter_review.get("should_redirect"):
                original_to = to_model
                to_model = arbiter_review["redirect_to"]
                self.logger.info(f"  Arbiter redirected from {original_to} to {to_model}")
        
        # Get or create destination thread
        thread = self.threads.get(to_model)
        if not thread:
            self.logger.warning(f"No thread for {to_model}, creating one")
            thread = self.create_thread(to_model, "unknown")
        
        # Add message to thread
        thread.add_message(
            role="user",
            content=message,
            from_model=from_model
        )
        
        # Add to shared context
        self.shared_context.append({
            "from": from_model,
            "to": to_model,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Track routing
        self.routing_history.append({
            "from": from_model,
            "to": to_model,
            "modified": arbiter_review.get("should_modify", False) if arbiter_review else False,
            "redirected": arbiter_review.get("should_redirect", False) if arbiter_review else False,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "routed_to": to_model,
            "message": message,
            "modified": arbiter_review.get("should_modify", False) if arbiter_review else False
        }
    
    def broadcast_message(self, 
                         from_model: str, 
                         message: str, 
                         to_models: List[str]):
        """
        Broadcast a message to multiple models.
        
        Args:
            from_model: Source model
            message: Message content
            to_models: List of destination models
        """
        self.logger.info(f"Broadcasting from {from_model} to {len(to_models)} models")
        
        for to_model in to_models:
            self.route_message(from_model, to_model, message)
    
    def get_shared_context(self, max_messages: int = 10) -> List[Dict]:
        """
        Get recent shared context.
        
        Args:
            max_messages: Maximum messages to return
        
        Returns:
            List of recent context messages
        """
        return self.shared_context[-max_messages:]
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics.
        
        Returns:
            Dict with routing stats
        """
        total_routes = len(self.routing_history)
        modified_count = sum(1 for r in self.routing_history if r["modified"])
        redirected_count = sum(1 for r in self.routing_history if r["redirected"])
        
        # Count routes by model
        routes_by_model = {}
        for route in self.routing_history:
            from_model = route["from"]
            to_model = route["to"]
            
            if from_model not in routes_by_model:
                routes_by_model[from_model] = {"sent": 0, "received": 0}
            if to_model not in routes_by_model:
                routes_by_model[to_model] = {"sent": 0, "received": 0}
            
            routes_by_model[from_model]["sent"] += 1
            routes_by_model[to_model]["received"] += 1
        
        return {
            "total_routes": total_routes,
            "modified_count": modified_count,
            "redirected_count": redirected_count,
            "modification_rate": modified_count / total_routes if total_routes > 0 else 0,
            "redirection_rate": redirected_count / total_routes if total_routes > 0 else 0,
            "routes_by_model": routes_by_model
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics.
        
        Returns:
            Dict with all stats
        """
        return {
            "threads": {
                model: thread.get_stats()
                for model, thread in self.threads.items()
            },
            "routing": self.get_routing_stats(),
            "shared_context_size": len(self.shared_context)
        }
    
    def clear_all(self):
        """Clear all conversation threads and shared context."""
        for thread in self.threads.values():
            thread.clear()
        
        self.shared_context = []
        self.routing_history = []
        
        self.logger.info("Cleared all conversation threads")
    
    def save_conversation(self, filepath: Path):
        """
        Save conversation history to file.
        
        Args:
            filepath: Path to save to
        """
        data = {
            "threads": {
                model: thread.get_full_history()
                for model, thread in self.threads.items()
            },
            "shared_context": self.shared_context,
            "routing_history": self.routing_history,
            "stats": self.get_all_stats(),
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved conversation to {filepath}")
    
    def load_conversation(self, filepath: Path):
        """
        Load conversation history from file.
        
        Args:
            filepath: Path to load from
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Recreate threads
        for model, messages in data["threads"].items():
            thread = self.create_thread(model, "loaded")
            for msg in messages:
                thread.add_message(
                    role=msg["role"],
                    content=msg["content"],
                    from_model=msg.get("from_model")
                )
        
        self.shared_context = data["shared_context"]
        self.routing_history = data["routing_history"]
        
        self.logger.info(f"Loaded conversation from {filepath}")