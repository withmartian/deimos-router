"""Natural language detection rule implementation."""

from typing import Any, Dict, Optional, Union
import openai
from ..config import config
from .base import Rule, Decision


class NaturalLanguageRule(Rule):
    """Rule that makes decisions based on the natural language detected in the message."""
    
    def __init__(self, name: str, language_mappings: Dict[str, Union[str, Rule]], 
                 default: Optional[Union[str, Rule]] = None,
                 llm_model: Optional[str] = None):
        """Initialize a NaturalLanguageRule.
        
        Args:
            name: The name of this rule
            language_mappings: Dictionary mapping 2-letter ISO language codes to models or rules
            default: Default model/rule when no language is detected or mapped
            llm_model: Model to use for language detection. If None, uses the default model from config.
        """
        super().__init__(name)
        self.language_mappings = language_mappings
        self.default = default
        self.llm_model = llm_model or config.get_default_model('natural_language_detection')
    
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate based on the natural language detected in the message.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Decision based on detected language
        """
        # Extract text content from messages
        text_content = self._extract_text_content(request_data)
        
        if not text_content:
            return Decision(self.default, trigger="no_content")
        
        # Use LLM to detect the language
        detected_language = self._detect_language_llm(text_content)
        
        if detected_language and detected_language in self.language_mappings:
            return Decision(self.language_mappings[detected_language], trigger=detected_language)
        
        # Fall back to default
        return Decision(self.default, trigger="no_language_detected")
    
    def _extract_text_content(self, request_data: Dict[str, Any]) -> str:
        """Extract text content from request messages."""
        messages = request_data.get('messages', [])
        text_parts = []
        
        for message in messages:
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                if isinstance(content, str):
                    text_parts.append(content)
        
        return '\n'.join(text_parts)
    
    def _detect_language_llm(self, text: str) -> Optional[str]:
        """Detect natural language using LLM.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected 2-letter ISO language code or None
        """
        try:
            # Get credentials for the LLM
            if not config.is_configured():
                return None
            
            credentials = config.get_credentials()
            
            # Create OpenAI client
            client = openai.OpenAI(
                api_key=credentials['api_key'],
                base_url=credentials.get('api_url')
            )
            
            # Create prompt for language detection
            available_languages = list(self.language_mappings.keys())
            languages_list = ', '.join(available_languages)
            
            prompt = f"""Analyze the following text and determine what natural language it is predominantly written in.

You must respond with ONLY a 2-letter ISO language code from this list: {languages_list}

If the text doesn't clearly match any of these languages, or if you cannot determine the language, respond with "None".

Respond with ONLY the 2-letter language code (or "None"), nothing else.

Text to analyze:
{text[:2000]}"""  # Limit text to avoid token limits

            # Make the API call
            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            # Extract the response
            detected = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            if detected == "none":
                return None
            
            # Check if the detected language is in our available languages
            for lang in available_languages:
                if lang.lower() == detected:
                    return lang
            
            return None
            
        except Exception:
            # If LLM detection fails, return None
            return None
    
    def __repr__(self) -> str:
        return f"NaturalLanguageRule(name='{self.name}', languages={list(self.language_mappings.keys())})"
