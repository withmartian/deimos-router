"""Router class for model selection."""

import random
from typing import Any, Dict, List, Optional, Union

from .rules import Rule, Decision, get_rule
from .rules.base import ExplanationEntry
from .default_models import get_default_router_models


class Router:
    """Router for selecting models based on routing logic."""
    
    # Default cheap models for fallback
    DEFAULT_CHEAP_MODELS = get_default_router_models()
    
    def __init__(
        self, 
        name: str, 
        rules: Optional[List[Union[str, Rule]]] = None,
        default: Optional[str] = None,
        models: Optional[List[str]] = None  # Keep for backward compatibility
    ):
        """Initialize router with a name and routing rules.
        
        Args:
            name: The name of the router
            rules: List of rule names (strings) or Rule objects to evaluate in order
            default: Default model to use if no rules match
            models: Legacy parameter for backward compatibility (will be ignored if rules provided)
        """
        self.name = name
        self.rules = rules or []
        self.default = default or "gpt-3.5-turbo"
        
        # Backward compatibility: if no rules provided but models are specified, use random selection
        if not self.rules:
            if models is None:
                self.models = self.DEFAULT_CHEAP_MODELS.copy()
            else:
                self.models = models
            
            if not self.models:
                raise ValueError("Router must have at least one model to select from")
        else:
            # For rule-based routers, models is not used
            self.models = models or []
    
    def select_model(self, request_data: Optional[Dict[str, Any]] = None) -> str:
        """Select a model based on rules or fallback to random/default selection.
        
        Args:
            request_data: The complete request data for rule evaluation
            
        Returns:
            The selected model name
        """
        # If we have rules, use rule-based selection
        if self.rules:
            return self._select_model_by_rules(request_data or {})
        
        # Backward compatibility: random selection from models list
        if self.models:
            return random.choice(self.models)
        
        # Final fallback
        return self.default
    
    def select_model_with_explanation(self, request_data: Optional[Dict[str, Any]] = None) -> tuple[str, List[ExplanationEntry]]:
        """Select a model and return explanation of the decision process.
        
        Args:
            request_data: The complete request data for rule evaluation
            
        Returns:
            Tuple of (selected_model, explanation_entries)
        """
        explanation = []
        
        # If we have rules, use rule-based selection with explanation
        if self.rules:
            model, explanation = self._select_model_by_rules_with_explanation(request_data or {})
            if model:
                return model, explanation
        
        # Backward compatibility: random selection from models list
        if self.models:
            selected = random.choice(self.models)
            explanation.append(ExplanationEntry("default", "default", "None", selected))
            return selected, explanation
        
        # Final fallback
        explanation.append(ExplanationEntry("default", "default", "None", self.default))
        return self.default, explanation
    
    def _select_model_by_rules(self, request_data: Dict[str, Any]) -> str:
        """Select model using the rule-based system.
        
        Args:
            request_data: The complete request data
            
        Returns:
            The selected model name
        """
        for rule_ref in self.rules:
            # Get the rule (either by name or direct reference)
            if isinstance(rule_ref, str):
                rule = get_rule(rule_ref)
                if rule is None:
                    continue  # Skip unknown rules
            else:
                rule = rule_ref
            
            # Evaluate the rule chain
            selected_model = self._evaluate_rule_chain(rule, request_data)
            if selected_model:
                return selected_model
        
        # No rules matched, use default
        return self.default
    
    def _select_model_by_rules_with_explanation(self, request_data: Dict[str, Any]) -> tuple[Optional[str], List[ExplanationEntry]]:
        """Select model using the rule-based system with explanation tracking.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Tuple of (selected_model, explanation_entries)
        """
        explanation = []
        
        for rule_ref in self.rules:
            # Get the rule (either by name or direct reference)
            if isinstance(rule_ref, str):
                rule = get_rule(rule_ref)
                if rule is None:
                    continue  # Skip unknown rules
            else:
                rule = rule_ref
            
            # Evaluate the rule chain with explanation
            selected_model, rule_explanation = self._evaluate_rule_chain_with_explanation(rule, request_data)
            explanation.extend(rule_explanation)
            
            if selected_model:
                return selected_model, explanation
        
        # No rules matched, add default explanation
        explanation.append(ExplanationEntry("default", "default", "None", self.default))
        return self.default, explanation
    
    def _evaluate_rule_chain(self, rule: Rule, request_data: Dict[str, Any], max_depth: int = 10) -> Optional[str]:
        """Evaluate a chain of rules until we get a model or exhaust the chain.
        
        Args:
            rule: The starting rule
            request_data: The request data
            max_depth: Maximum depth to prevent infinite loops
            
        Returns:
            The selected model name, or None if no decision reached
        """
        current_rule = rule
        depth = 0
        
        while current_rule and depth < max_depth:
            decision = current_rule.evaluate(request_data)
            
            if decision.is_model():
                return decision.get_model()
            elif decision.is_rule():
                current_rule = decision.get_rule()
                depth += 1
            else:
                # Decision is None, rule chain ends without a model
                return None
        
        # Max depth reached or no valid decision
        return None
    
    def _evaluate_rule_chain_with_explanation(self, rule: Rule, request_data: Dict[str, Any], max_depth: int = 10) -> tuple[Optional[str], List[ExplanationEntry]]:
        """Evaluate a chain of rules with explanation tracking.
        
        Args:
            rule: The starting rule
            request_data: The request data
            max_depth: Maximum depth to prevent infinite loops
            
        Returns:
            Tuple of (selected_model, explanation_entries)
        """
        explanation = []
        current_rule = rule
        depth = 0
        
        while current_rule and depth < max_depth:
            decision = current_rule.evaluate(request_data)
            
            if decision.is_model():
                # Final decision - model selected
                explanation.append(ExplanationEntry(
                    rule_type=current_rule.get_rule_type(),
                    rule_name=current_rule.name,
                    rule_trigger=decision.trigger,
                    decision=decision.get_model()
                ))
                return decision.get_model(), explanation
            elif decision.is_rule():
                # Continue to next rule
                explanation.append(ExplanationEntry(
                    rule_type=current_rule.get_rule_type(),
                    rule_name=current_rule.name,
                    rule_trigger=decision.trigger,
                    decision="continue"
                ))
                current_rule = decision.get_rule()
                depth += 1
            else:
                # Decision is None, rule chain ends without a model
                explanation.append(ExplanationEntry(
                    rule_type=current_rule.get_rule_type(),
                    rule_name=current_rule.name,
                    rule_trigger=decision.trigger,
                    decision="no_match"
                ))
                return None, explanation
        
        # Max depth reached
        if current_rule:
            explanation.append(ExplanationEntry(
                rule_type=current_rule.get_rule_type(),
                rule_name=current_rule.name,
                rule_trigger="max_depth_reached",
                decision="no_match"
            ))
        
        return None, explanation
    
    def add_model(self, model: str) -> None:
        """Add a model to the router's selection pool.
        
        Args:
            model: The model name to add
        """
        if model not in self.models:
            self.models.append(model)
    
    def remove_model(self, model: str) -> None:
        """Remove a model from the router's selection pool.
        
        Args:
            model: The model name to remove
            
        Raises:
            ValueError: If trying to remove the last model or if model not found
        """
        if len(self.models) <= 1:
            raise ValueError("Cannot remove the last model from router")
        
        if model not in self.models:
            raise ValueError(f"Model '{model}' not found in router")
        
        self.models.remove(model)
    
    def __repr__(self) -> str:
        return f"Router(name='{self.name}', models={self.models})"


# Global registry for routers
_router_registry = {}


def register_router(router: Router) -> None:
    """Register a router globally by name.
    
    Args:
        router: The router instance to register
    """
    _router_registry[router.name] = router


def get_router(name: str) -> Optional[Router]:
    """Get a registered router by name.
    
    Args:
        name: The router name
        
    Returns:
        The router instance if found, None otherwise
    """
    return _router_registry.get(name)


def list_routers() -> List[str]:
    """List all registered router names.
    
    Returns:
        List of router names
    """
    return list(_router_registry.keys())


def clear_routers() -> None:
    """Clear all registered routers. Mainly for testing."""
    _router_registry.clear()
