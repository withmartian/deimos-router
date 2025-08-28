"""Default model configurations for deimos-router.

This module contains the built-in default models for various tasks.
Users can override these defaults through environment variables or configuration files.
"""

from typing import Dict

# Default models for various tasks
DEFAULT_MODELS: Dict[str, str] = {
    'code_language_detection': 'openai/gpt-4o-mini',
    'natural_language_detection': 'openai/gpt-4o-mini', 
    'general_chat': 'openai/gpt-4o-mini',
    'code_analysis': 'openai/gpt-4o-mini',
    'task_classification': 'openai/gpt-5-nano',
}

# Default cheap models for router fallback
DEFAULT_ROUTER_MODELS = [
    "openai/gpt-3.5-turbo",
    "openai/gpt-3.5-turbo-0125", 
    "openai/gpt-4o-mini",
    "openai/gpt-4o-mini-2024-07-18",
]

def get_default_model(task: str) -> str:
    """Get the default model for a specific task.
    
    Args:
        task: The task name (e.g., 'code_language_detection', 'general_chat')
        
    Returns:
        The default model name for the task, or 'gpt-4o-mini' if task not found
    """
    return DEFAULT_MODELS.get(task, 'openai/gpt-4o-mini')

def get_all_default_models() -> Dict[str, str]:
    """Get all default models as a dictionary.
    
    Returns:
        A copy of the default models dictionary
    """
    return DEFAULT_MODELS.copy()

def get_default_router_models() -> list[str]:
    """Get the default models for router fallback.
    
    Returns:
        A copy of the default router models list
    """
    return DEFAULT_ROUTER_MODELS.copy()
