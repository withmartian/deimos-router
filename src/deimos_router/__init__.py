"""Deimos Router - A Python routing library."""

__version__ = "0.1.0"

# Import main components
from .router import Router, register_router, get_router, list_routers, clear_routers
from .chat import chat
from .config import config
from .rules import Rule, Decision, TaskRule, CodeRule, CodeLanguageRule, NaturalLanguageRule, AutoTaskRule, register_rule, get_rule, list_rules, clear_rules

def hello() -> str:
    return "Hello from deimos-router!"


__all__ = [
    "hello", 
    "__version__",
    "Router",
    "register_router", 
    "get_router", 
    "list_routers", 
    "clear_routers",
    "chat",
    "config",
    "Rule",
    "Decision",
    "TaskRule",
    "CodeRule",
    "CodeLanguageRule",
    "NaturalLanguageRule",
    "AutoTaskRule",
    "register_rule",
    "get_rule",
    "list_rules",
    "clear_rules"
]
