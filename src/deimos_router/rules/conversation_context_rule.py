"""Conversation context-based rule implementation."""

from typing import Any, Dict, Optional, Union
from .base import Rule, Decision


class ConversationContextRule(Rule):
    """Rule that makes decisions based on conversation history depth and context."""
    
    def __init__(self, name: str,
                 new_threshold: int,
                 deep_threshold: int,
                 new_model: Union[str, Rule],
                 developing_model: Union[str, Rule],
                 deep_model: Union[str, Rule]):
        """Initialize a ConversationContextRule.
        
        Args:
            name: The name of this rule
            new_threshold: Message count threshold for new conversations
            deep_threshold: Message count threshold for deep conversations
            new_model: Model or rule to use for new conversations (< new_threshold messages)
            developing_model: Model or rule to use for developing conversations (new_threshold <= messages < deep_threshold)
            deep_model: Model or rule to use for deep conversations (>= deep_threshold messages)
        """
        super().__init__(name)
        
        # Validate thresholds
        if new_threshold >= deep_threshold:
            raise ValueError("new_threshold must be less than deep_threshold")
        if new_threshold < 1 or deep_threshold < 1:
            raise ValueError("thresholds must be positive integers")
        
        self.new_threshold = new_threshold
        self.deep_threshold = deep_threshold
        self.new_model = new_model
        self.developing_model = developing_model
        self.deep_model = deep_model
    
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate based on conversation context depth.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Decision based on conversation context
        """
        # Analyze conversation context
        context_info = self._analyze_conversation_context(request_data)
        
        message_count = context_info['message_count']
        total_chars = context_info['total_chars']
        
        # Determine which model to use based on conversation depth
        if message_count < self.new_threshold:
            stage = "new"
            model = self.new_model
        elif message_count < self.deep_threshold:
            stage = "developing"
            model = self.developing_model
        else:
            stage = "deep"
            model = self.deep_model
        
        trigger = f"{stage}_conversation_{message_count}_messages_{total_chars}_chars"
        return Decision(model, trigger=trigger)
    
    def _analyze_conversation_context(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the conversation context from request messages.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Dictionary with conversation analysis results
        """
        messages = request_data.get('messages', [])
        
        # Count messages and calculate total character count
        message_count = 0
        total_chars = 0
        user_messages = 0
        assistant_messages = 0
        
        for message in messages:
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                role = message.get('role', 'user')
                
                if isinstance(content, str):
                    message_count += 1
                    total_chars += len(content)
                    
                    # Track message types for additional context
                    if role == 'user':
                        user_messages += 1
                    elif role == 'assistant':
                        assistant_messages += 1
        
        return {
            'message_count': message_count,
            'total_chars': total_chars,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'avg_message_length': total_chars / message_count if message_count > 0 else 0
        }
    
    def get_thresholds(self) -> Dict[str, int]:
        """Get the current thresholds.
        
        Returns:
            Dictionary with new_threshold and deep_threshold
        """
        return {
            'new_threshold': self.new_threshold,
            'deep_threshold': self.deep_threshold
        }
    
    def update_thresholds(self, new_threshold: Optional[int] = None,
                         deep_threshold: Optional[int] = None) -> None:
        """Update the conversation depth thresholds.
        
        Args:
            new_threshold: New threshold for new conversations (optional)
            deep_threshold: New threshold for deep conversations (optional)
            
        Raises:
            ValueError: If the new thresholds are invalid
        """
        new_new = new_threshold if new_threshold is not None else self.new_threshold
        new_deep = deep_threshold if deep_threshold is not None else self.deep_threshold
        
        # Validate new thresholds
        if new_new >= new_deep:
            raise ValueError("new_threshold must be less than deep_threshold")
        if new_new < 1 or new_deep < 1:
            raise ValueError("thresholds must be positive integers")
        
        self.new_threshold = new_new
        self.deep_threshold = new_deep
    
    def get_conversation_stage(self, request_data: Dict[str, Any]) -> str:
        """Get the conversation stage for the given request.
        
        Args:
            request_data: The complete request data
            
        Returns:
            The conversation stage: 'new', 'developing', or 'deep'
        """
        context_info = self._analyze_conversation_context(request_data)
        message_count = context_info['message_count']
        
        if message_count < self.new_threshold:
            return "new"
        elif message_count < self.deep_threshold:
            return "developing"
        else:
            return "deep"
    
    def __repr__(self) -> str:
        return (f"ConversationContextRule(name='{self.name}', "
                f"new_threshold={self.new_threshold}, "
                f"deep_threshold={self.deep_threshold})")
