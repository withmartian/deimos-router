"""Task-based rule implementation."""

from typing import Any, Dict
from .base import Rule, Decision


class TaskRule(Rule):
    """Rule that makes decisions based on task metadata in the request."""
    
    def __init__(self, name: str, triggers: Dict[str, str]):
        """Initialize a TaskRule.
        
        Args:
            name: The name of this rule
            triggers: Dictionary mapping task names to model names or rule names (deimos/rules/rule-name)
        """
        super().__init__(name)
        self.triggers = triggers
    
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
        
        # Look up the task in our triggers
        if task in self.triggers:
            decision_value = self.triggers[task]
            return Decision(decision_value, trigger=task)
        
        # No matching rule for this task
        return Decision(None, trigger=task)
    
    def add_task_rule(self, task: str, decision: str) -> None:
        """Add a new task rule.
        
        Args:
            task: The task name
            decision: The model name or rule name (deimos/rules/rule-name) to use for this task
        """
        self.triggers[task] = decision
    
    def remove_task_rule(self, task: str) -> None:
        """Remove a task rule.
        
        Args:
            task: The task name to remove
        """
        if task in self.triggers:
            del self.triggers[task]
    
    def __repr__(self) -> str:
        return f"TaskRule(name='{self.name}', triggers={list(self.triggers.keys())})"
