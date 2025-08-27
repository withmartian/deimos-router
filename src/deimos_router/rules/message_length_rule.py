"""Message length-based rule implementation."""

from typing import Any, Dict, Optional, Union
from .base import Rule, Decision


class MessageLengthRule(Rule):
    """Rule that makes decisions based on the total length of user messages."""
    
    def __init__(self, name: str, 
                 short_threshold: int,
                 long_threshold: int,
                 short_model: Union[str, Rule],
                 medium_model: Union[str, Rule],
                 long_model: Union[str, Rule]):
        """Initialize a MessageLengthRule.
        
        Args:
            name: The name of this rule
            short_threshold: Character count threshold for short messages
            long_threshold: Character count threshold for long messages
            short_model: Model or rule to use for short messages (< short_threshold)
            medium_model: Model or rule to use for medium messages (short_threshold <= length < long_threshold)
            long_model: Model or rule to use for long messages (>= long_threshold)
        """
        super().__init__(name)
        
        # Validate thresholds
        if short_threshold >= long_threshold:
            raise ValueError("short_threshold must be less than long_threshold")
        if short_threshold < 0 or long_threshold < 0:
            raise ValueError("thresholds must be non-negative")
        
        self.short_threshold = short_threshold
        self.long_threshold = long_threshold
        self.short_model = short_model
        self.medium_model = medium_model
        self.long_model = long_model
    
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate based on the total length of user messages.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Decision based on message length
        """
        # Extract text content from messages
        text_content = self._extract_text_content(request_data)
        
        # Calculate total character count
        total_length = len(text_content)
        
        # Determine which model to use based on length
        if total_length < self.short_threshold:
            return Decision(self.short_model, trigger=f"short_message_{total_length}_chars")
        elif total_length < self.long_threshold:
            return Decision(self.medium_model, trigger=f"medium_message_{total_length}_chars")
        else:
            return Decision(self.long_model, trigger=f"long_message_{total_length}_chars")
    
    def _extract_text_content(self, request_data: Dict[str, Any]) -> str:
        """Extract text content from request messages.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Combined text content from all user messages
        """
        messages = request_data.get('messages', [])
        text_parts = []
        
        for message in messages:
            if isinstance(message, dict) and 'content' in message:
                # Only count user messages, not system/assistant messages
                role = message.get('role', 'user')
                if role == 'user':
                    content = message['content']
                    if isinstance(content, str):
                        text_parts.append(content)
        
        return '\n'.join(text_parts)
    
    def get_thresholds(self) -> Dict[str, int]:
        """Get the current thresholds.
        
        Returns:
            Dictionary with short_threshold and long_threshold
        """
        return {
            'short_threshold': self.short_threshold,
            'long_threshold': self.long_threshold
        }
    
    def update_thresholds(self, short_threshold: Optional[int] = None, 
                         long_threshold: Optional[int] = None) -> None:
        """Update the length thresholds.
        
        Args:
            short_threshold: New short threshold (optional)
            long_threshold: New long threshold (optional)
            
        Raises:
            ValueError: If the new thresholds are invalid
        """
        new_short = short_threshold if short_threshold is not None else self.short_threshold
        new_long = long_threshold if long_threshold is not None else self.long_threshold
        
        # Validate new thresholds
        if new_short >= new_long:
            raise ValueError("short_threshold must be less than long_threshold")
        if new_short < 0 or new_long < 0:
            raise ValueError("thresholds must be non-negative")
        
        self.short_threshold = new_short
        self.long_threshold = new_long
    
    def __repr__(self) -> str:
        return (f"MessageLengthRule(name='{self.name}', "
                f"short_threshold={self.short_threshold}, "
                f"long_threshold={self.long_threshold})")
