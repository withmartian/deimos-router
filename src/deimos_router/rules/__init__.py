"""Rule-based model selection system."""

from typing import List, Optional
from .base import Decision, Rule
from .task_rule import TaskRule
from .code_rule import CodeRule
from .code_language_rule import CodeLanguageRule
from .natural_language_rule import NaturalLanguageRule
from .auto_task_rule import AutoTaskRule

# Global registry for rules (similar to router registry)
_rule_registry = {}


def register_rule(rule: Rule) -> None:
    """Register a rule globally by name.
    
    Args:
        rule: The rule instance to register
    """
    _rule_registry[rule.name] = rule


def get_rule(name: str) -> Optional[Rule]:
    """Get a registered rule by name.
    
    Args:
        name: The rule name
        
    Returns:
        The rule instance if found, None otherwise
    """
    return _rule_registry.get(name)


def list_rules() -> List[str]:
    """List all registered rule names.
    
    Returns:
        List of rule names
    """
    return list(_rule_registry.keys())


def clear_rules() -> None:
    """Clear all registered rules. Mainly for testing."""
    _rule_registry.clear()


# Export all the classes and functions
__all__ = [
    'Decision',
    'Rule',
    'TaskRule',
    'CodeRule',
    'CodeLanguageRule',
    'NaturalLanguageRule',
    'AutoTaskRule',
    'register_rule',
    'get_rule',
    'list_rules',
    'clear_rules'
]
