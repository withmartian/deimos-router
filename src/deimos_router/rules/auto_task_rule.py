"""Automatic task detection rule implementation."""

from typing import Any, Dict, Optional
import openai
from ..config import config
from .base import Rule, Decision


class AutoTaskRule(Rule):
    """Rule that automatically detects tasks from message content using an LLM."""
    
    def __init__(self, name: str, triggers: Dict[str, str], 
                 default: Optional[str] = None,
                 llm_model: Optional[str] = None):
        """Initialize an AutoTaskRule.
        
        Args:
            name: The name of this rule
            triggers: Dictionary mapping task names to model names or rule names (deimos/rules/rule-name)
            default: Default model name or rule name (deimos/rules/rule-name) when no task is detected or mapped
            llm_model: Model to use for task detection. If None, uses the default model from config.
        """
        super().__init__(name)
        self.triggers = triggers
        self.default = default
        self.llm_model = llm_model or config.get_default_model('task_classification')
    
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate based on the task detected from message content.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Decision based on detected task
        """
        # Extract text content from messages
        text_content = self._extract_text_content(request_data)
        
        if not text_content:
            return Decision(self.default)
        
        # Use LLM to detect the task
        detected_task = self._detect_task_llm(text_content)
        
        if detected_task and detected_task in self.triggers:
            return Decision(self.triggers[detected_task], trigger=detected_task)
        
        # Fall back to default
        return Decision(self.default)
    
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
    
    def _detect_task_llm(self, text: str) -> Optional[str]:
        """Detect task type using LLM.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected task name or None
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
            
            # Create prompt for task detection
            available_tasks = list(self.triggers.keys())
            tasks_list = ', '.join(available_tasks)
            
            prompt = f"""Analyze the following user message and determine what type of task they are requesting.

You must respond with ONLY ONE of these exact task names: {tasks_list}

If the message doesn't clearly match any of these tasks, respond with "none".

IMPORTANT: Your response must be EXACTLY one of the task names listed above, or "none". Do not include any other text, explanations, or formatting.

User message:
{text[:2000]}"""  # Limit text to avoid token limits

            # Make the API call
            # Note: Some models (like gpt-5-nano) don't support custom temperature or max_tokens
            api_params = {
                "model": self.llm_model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Only add temperature and max_tokens for models that support them
            if not self.llm_model.endswith('-nano'):
                api_params["temperature"] = 0.1
                api_params["max_tokens"] = 50
            
            response = client.chat.completions.create(**api_params)
            
            # Extract the response
            raw_response = response.choices[0].message.content
            if raw_response is None:
                return None
                
            raw_response = raw_response.strip()
            detected = raw_response.lower()
            
            # Validate the response
            if detected == "none":
                return None
            
            # Check if the detected task is in our available tasks (case-insensitive)
            for task in available_tasks:
                if task.lower() == detected:
                    return task
            
            # If we get here, the LLM returned something unexpected
            return None
            
        except Exception:
            # If LLM detection fails, return None
            return None
    
    def add_task_mapping(self, task: str, decision: str) -> None:
        """Add a new task mapping.
        
        Args:
            task: The task name
            decision: The model name or rule name (deimos/rules/rule-name) to use for this task
        """
        self.triggers[task] = decision
    
    def remove_task_mapping(self, task: str) -> None:
        """Remove a task mapping.
        
        Args:
            task: The task name to remove
        """
        if task in self.triggers:
            del self.triggers[task]
    
    def __repr__(self) -> str:
        return f"AutoTaskRule(name='{self.name}', tasks={list(self.triggers.keys())})"
