"""Task-based rule implementation."""

from typing import Any, Dict, Union
from .base import Rule, Decision


class TaskRule(Rule):
    """Rule that makes decisions based on task metadata in the request."""
    
    def __init__(self, name: str, rules: Dict[str, Union[str, Rule]]):
        """Initialize a TaskRule.
        
        Args:
            name: The name of this rule
            rules: Dictionary mapping task names to models or other rules
        """
        super().__init__(name)
        self.rules = rules
    
    def evaluate(self, request_data: Dict[str, Any]) -> Decision:
        """Evaluate based on the 'task' field in request data.
        
        Args:
            request_data: The complete request data
            
        Returns:
            Decision based on the task, or None if no task or no matching rule
        """
        # Look for task in the request data
        task = request_data.get('task')
        
        if task is None:
            return Decision(None, trigger=None)
        
        # Look up the task in our rules
        if task in self.rules:
            decision_value = self.rules[task]
            return Decision(decision_value, trigger=task)
        
        # No matching rule for this task
        return Decision(None, trigger=task)
    
    def add_task_rule(self, task: str, decision: Union[str, Rule]) -> None:
        """Add a new task rule.
        
        Args:
            task: The task name
            decision: The model name or Rule to use for this task
        """
        self.rules[task] = decision
    
    def remove_task_rule(self, task: str) -> None:
        """Remove a task rule.
        
        Args:
            task: The task name to remove
        """
        if task in self.rules:
            del self.rules[task]
    
    def __repr__(self) -> str:
        return f"TaskRule(name='{self.name}', rules={list(self.rules.keys())})"
