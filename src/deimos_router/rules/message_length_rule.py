"""Message length-based rule implementation."""

from typing import Any, Dict, Optional
import tiktoken
from .base import Rule, Decision


class MessageLengthRule(Rule):
    """Rule that makes decisions based on the total token length of user messages."""
    
    def __init__(self, name: str, 
                 short_threshold: int,
                 long_threshold: int,
                 short_model: str,
                 medium_model: str,
                 long_model: str,
                 encoding_name: str = "cl100k_base"):
        """Initialize a MessageLengthRule.
        
        Args:
            name: The name of this rule
            short_threshold: Token count threshold for short messages
            long_threshold: Token count threshold for long messages
            short_model: Model name or rule name (deimos/rules/rule-name) to use for short messages (< short_threshold)
            medium_model: Model name or rule name (deimos/rules/rule-name) to use for medium messages (short_threshold <= length < long_threshold)
            long_model: Model name or rule name (deimos/rules/rule-name) to use for long messages (>= long_threshold)
            encoding_name: The tiktoken encoding to use (default: "cl100k_base" for GPT-4/3.5-turbo)
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
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except KeyError:
            raise ValueError(f"Unknown encoding: {encoding_name}")
        self.encoding_name = encoding_name
    
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate based on the total token length of user messages.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Decision based on message token length
        """
        # Extract text content from messages
        text_content = self._extract_text_content(request_data)
        
        # Calculate total token count
        total_tokens = self._count_tokens(text_content)
        
        # Determine which model to use based on token count
        if total_tokens < self.short_threshold:
            return Decision(self.short_model, trigger=f"short_message_{total_tokens}_tokens")
        elif total_tokens < self.long_threshold:
            return Decision(self.medium_model, trigger=f"medium_message_{total_tokens}_tokens")
        else:
            return Decision(self.long_model, trigger=f"long_message_{total_tokens}_tokens")
    
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
    
    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.
        
        Args:
            text: The text to tokenize
            
        Returns:
            Number of tokens in the text
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
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
        """Update the token count thresholds.
        
        Args:
            short_threshold: New short token threshold (optional)
            long_threshold: New long token threshold (optional)
            
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
        return (f"MessageLengthRule('{self.name}', "
                f"{self.short_threshold}, "
                f"{self.long_threshold}, "
                f"'{self.short_model}', "
                f"'{self.medium_model}', "
                f"'{self.long_model}', "
                f"encoding_name={self.encoding_name!r})")
