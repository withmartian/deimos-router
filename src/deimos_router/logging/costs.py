"""Cost calculation utilities for logging."""

from typing import Any, Dict, Optional, Tuple
import re


# Default pricing per 1K tokens (input/output) for common models
# These are approximate prices and should be updated regularly
DEFAULT_MODEL_PRICING = {
    # OpenAI models
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
    
    # Anthropic models
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    
    # Generic fallback
    "default": {"input": 0.002, "output": 0.004}
}


class CostCalculator:
    """Calculates costs for API requests based on token usage and model pricing."""
    
    def __init__(self, custom_pricing: Optional[Dict[str, Dict[str, float]]] = None):
        """Initialize the cost calculator.
        
        Args:
            custom_pricing: Custom pricing data to override defaults
        """
        self.pricing = DEFAULT_MODEL_PRICING.copy()
        if custom_pricing:
            self.pricing.update(custom_pricing)
    
    def extract_cost_from_response(self, response: Any) -> Tuple[Optional[float], bool, str]:
        """Extract cost information from API response.
        
        Args:
            response: The API response object
            
        Returns:
            Tuple of (cost, is_estimated, source)
        """
        # Try to extract actual cost from response
        # This varies by provider and may be in headers, metadata, or response body
        
        # Check for cost in response metadata (some providers include this)
        if hasattr(response, '_deimos_metadata') and 'cost' in response._deimos_metadata:
            return response._deimos_metadata['cost'], False, "api_response"
        
        # Check for cost in response headers (if available)
        if hasattr(response, 'headers'):
            cost_header = response.headers.get('x-cost') or response.headers.get('cost')
            if cost_header:
                try:
                    return float(cost_header), False, "api_response"
                except (ValueError, TypeError):
                    pass
        
        # Check for cost in response body (some APIs include this)
        if hasattr(response, 'cost') and response.cost is not None:
            return float(response.cost), False, "api_response"
        
        # No actual cost found
        return None, True, "unknown"
    
    def extract_tokens_from_response(self, response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage from API response.
        
        Args:
            response: The API response object
            
        Returns:
            Dictionary with token counts or None
        """
        tokens = {}
        
        # OpenAI format
        if hasattr(response, 'usage'):
            usage = response.usage
            if hasattr(usage, 'prompt_tokens'):
                tokens['prompt'] = usage.prompt_tokens
            if hasattr(usage, 'completion_tokens'):
                tokens['completion'] = usage.completion_tokens
            if hasattr(usage, 'total_tokens'):
                tokens['total'] = usage.total_tokens
            elif 'prompt' in tokens and 'completion' in tokens:
                tokens['total'] = tokens['prompt'] + tokens['completion']
        
        # Anthropic format (if different)
        elif hasattr(response, 'token_usage'):
            usage = response.token_usage
            if hasattr(usage, 'input_tokens'):
                tokens['prompt'] = usage.input_tokens
            if hasattr(usage, 'output_tokens'):
                tokens['completion'] = usage.output_tokens
            if 'prompt' in tokens and 'completion' in tokens:
                tokens['total'] = tokens['prompt'] + tokens['completion']
        
        return tokens if tokens else None
    
    def estimate_cost_from_tokens(
        self, 
        model: str, 
        tokens: Dict[str, int]
    ) -> Tuple[float, bool, str]:
        """Estimate cost based on token usage and model pricing.
        
        Args:
            model: The model name
            tokens: Token usage dictionary
            
        Returns:
            Tuple of (cost, is_estimated, source)
        """
        # Normalize model name for pricing lookup
        normalized_model = self._normalize_model_name(model)
        
        # Get pricing for this model
        model_pricing = self.pricing.get(normalized_model, self.pricing["default"])
        
        # Calculate cost
        cost = 0.0
        
        # Input tokens cost
        if 'prompt' in tokens:
            cost += (tokens['prompt'] / 1000) * model_pricing['input']
        
        # Output tokens cost
        if 'completion' in tokens:
            cost += (tokens['completion'] / 1000) * model_pricing['output']
        
        return cost, True, "token_calculation"
    
    def calculate_cost(
        self, 
        model: str, 
        response: Any
    ) -> Tuple[Optional[float], bool, str]:
        """Calculate cost for a request/response.
        
        Args:
            model: The model name
            response: The API response object
            
        Returns:
            Tuple of (cost, is_estimated, source)
        """
        # First try to extract actual cost from response
        cost, is_estimated, source = self.extract_cost_from_response(response)
        if cost is not None:
            return cost, is_estimated, source
        
        # Fall back to token-based estimation
        tokens = self.extract_tokens_from_response(response)
        if tokens:
            return self.estimate_cost_from_tokens(model, tokens)
        
        # No cost or token information available
        return None, True, "unknown"
    
    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for pricing lookup.
        
        Args:
            model: The original model name
            
        Returns:
            Normalized model name
        """
        # Remove version suffixes and normalize common variations
        model = model.lower()
        
        # Handle OpenAI model variations
        if model.startswith('gpt-4-turbo'):
            return 'gpt-4-turbo'
        elif model.startswith('gpt-4'):
            return 'gpt-4'
        elif model.startswith('gpt-3.5-turbo-16k'):
            return 'gpt-3.5-turbo-16k'
        elif model.startswith('gpt-3.5-turbo'):
            return 'gpt-3.5-turbo'
        
        # Handle Anthropic model variations
        elif 'claude-3-5-sonnet' in model:
            return 'claude-3-5-sonnet'
        elif 'claude-3-opus' in model:
            return 'claude-3-opus'
        elif 'claude-3-sonnet' in model:
            return 'claude-3-sonnet'
        elif 'claude-3-haiku' in model:
            return 'claude-3-haiku'
        
        # Return original if no match found
        return model
    
    def update_pricing(self, model: str, input_price: float, output_price: float) -> None:
        """Update pricing for a specific model.
        
        Args:
            model: The model name
            input_price: Price per 1K input tokens
            output_price: Price per 1K output tokens
        """
        self.pricing[model] = {"input": input_price, "output": output_price}
    
    def get_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing information for a model.
        
        Args:
            model: The model name
            
        Returns:
            Dictionary with input and output pricing
        """
        normalized_model = self._normalize_model_name(model)
        return self.pricing.get(normalized_model, self.pricing["default"])
