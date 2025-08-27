"""Base classes for the rule system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class Decision:
    """Represents a decision made by a rule."""
    
    def __init__(self, value: Union[str, 'Rule', None], trigger: Optional[str] = None):
        """Initialize a decision.
        
        Args:
            value: Either a model name (str), another Rule, or None for no decision
            trigger: The trigger that caused this decision (e.g., task name, code language)
        """
        self.value = value
        self.trigger = trigger
    
    def is_model(self) -> bool:
        """Check if this decision is a model selection."""
        return isinstance(self.value, str)
    
    def is_rule(self) -> bool:
        """Check if this decision points to another rule."""
        return isinstance(self.value, Rule)
    
    def is_none(self) -> bool:
        """Check if this decision is None (no decision made)."""
        return self.value is None
    
    def get_model(self) -> Optional[str]:
        """Get the model name if this is a model decision."""
        return self.value if self.is_model() else None
    
    def get_rule(self) -> Optional['Rule']:
        """Get the rule if this decision points to another rule."""
        return self.value if self.is_rule() else None
    
    def __repr__(self) -> str:
        if self.is_model():
            return f"Decision(model='{self.value}', trigger='{self.trigger}')"
        elif self.is_rule():
            return f"Decision(rule={self.value.name}, trigger='{self.trigger}')"
        else:
            return f"Decision(None, trigger='{self.trigger}')"


class ExplanationEntry:
    """Represents an entry in the explanation of how a model was selected."""
    
    def __init__(self, rule_type: str, rule_name: str, rule_trigger: Optional[str], decision: str):
        """Initialize an explanation entry.
        
        Args:
            rule_type: The type of rule (e.g., "TaskRule", "CodeRule")
            rule_name: The name of the rule
            rule_trigger: What triggered this rule (e.g., "creative writing", "python")
            decision: The decision made (model name or "continue")
        """
        self.rule_type = rule_type
        self.rule_name = rule_name
        self.rule_trigger = rule_trigger or "None"
        self.decision = decision
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for API response."""
        return {
            "rule_type": self.rule_type,
            "rule_name": self.rule_name,
            "rule_trigger": self.rule_trigger,
            "decision": self.decision
        }


class Rule(ABC):
    """Abstract base class for all rules."""
    
    def __init__(self, name: str):
        """Initialize a rule with a name.
        
        Args:
            name: The name of this rule
        """
        self.name = name
    
    @abstractmethod
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate the rule against request data.
        
        Args:
            request_data: The complete request data including messages and metadata
            
        Returns:
            A Decision object containing either a model, another rule, or None
        """
        pass
    
    def get_rule_type(self) -> str:
        """Get the type name of this rule."""
        return self.__class__.__name__
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
