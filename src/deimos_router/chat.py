"""Chat completions API that mimics OpenAI's interface."""

from typing import Any, Dict, List, Optional, Union
import openai
from openai.types.chat import ChatCompletion

from .config import config
from .router import get_router


class ChatCompletions:
    """Chat completions API that mimics OpenAI's interface."""
    
    def __init__(self):
        """Initialize the chat completions API."""
        self._client = None
    
    def _get_client(self) -> openai.OpenAI:
        """Get or create OpenAI client with configured credentials."""
        if self._client is None:
            credentials = config.get_credentials()
            self._client = openai.OpenAI(
                api_key=credentials['api_key'],
                base_url=credentials['api_url']
            )
        return self._client
    
    def create(
        self,
        messages: List[Dict[str, str]],
        model: str,
        explain: bool = False,
        **kwargs: Any
    ) -> ChatCompletion:
        """Create a chat completion.
        
        Args:
            messages: List of message dictionaries
            model: Model name or router name (format: "deimos/router-name")
            explain: Whether to include explanation of routing decisions
            **kwargs: Additional arguments passed to OpenAI API
            
        Returns:
            ChatCompletion response with potential routing metadata and explanation
        """
        client = self._get_client()
        
        # Check if this is a router call
        if model.startswith("deimos/"):
            router_name = model[7:]  # Remove "deimos/" prefix
            router = get_router(router_name)
            
            if router is None:
                raise ValueError(f"Router '{router_name}' not found. Available routers: {list(get_router.__globals__['_router_registry'].keys())}")
            
            # Prepare request data for rule evaluation
            request_data = {
                'messages': messages,
                **kwargs  # Include all other parameters like task, temperature, etc.
            }
            
            # Select model using router with request data
            if explain:
                selected_model, explanation_entries = router.select_model_with_explanation(request_data)
            else:
                selected_model = router.select_model(request_data)
                explanation_entries = []
            
            # Filter out custom parameters that shouldn't be passed to OpenAI
            openai_kwargs = {k: v for k, v in kwargs.items() 
                           if k not in ['task', 'explain']}  # Add other custom params as needed
            
            # Make the API call with selected model
            response = client.chat.completions.create(
                messages=messages,
                model=selected_model,
                **openai_kwargs
            )
            
            # Add routing metadata to the response
            # We'll modify the response object to include routing info
            if hasattr(response, 'model'):
                # Store original model info and add routing metadata
                original_model = response.model
                response.model = selected_model
                
                # Add custom metadata (this is a bit of a hack, but works for our purposes)
                if not hasattr(response, '_deimos_metadata'):
                    response._deimos_metadata = {}
                
                response._deimos_metadata.update({
                    'router_used': router_name,
                    'selected_model': selected_model,
                    'original_model_field': original_model,
                    'available_models': router.models.copy()
                })
                
                # Add explanation if requested
                if explain and explanation_entries:
                    response._deimos_metadata['explain'] = [
                        entry.to_dict() for entry in explanation_entries
                    ]
            
            return response
        
        else:
            # Direct model call - pass through to OpenAI
            return client.chat.completions.create(
                messages=messages,
                model=model,
                **kwargs
            )


class Chat:
    """Chat API namespace that mimics OpenAI's structure."""
    
    def __init__(self):
        self.completions = ChatCompletions()


# Global chat instance
chat = Chat()
