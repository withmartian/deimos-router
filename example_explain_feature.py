"""Example demonstrating the explain feature for routing decisions."""

from src.deimos_router.router import Router, register_router
from src.deimos_router.rules.task_rule import TaskRule
from src.deimos_router.rules.code_rule import CodeRule
from src.deimos_router.chat import chat
from src.deimos_router.rules import register_rule
import json


def setup_example_router():
    """Set up a router with multiple rules to demonstrate explanation."""
    
    # Create a TaskRule that routes based on task type
    task_rule = TaskRule("my-task-rule", {
        "creative writing": "gpt-4",
        "code review": "gpt-4o",
        "debugging": "claude-3-sonnet"
    })
    register_rule(task_rule)
    
    # Create a CodeRule that detects code and routes accordingly
    code_rule = CodeRule("my-code-rule", 
                        code="gpt-4o",  # Use GPT-4o for code
                        not_code="gpt-3.5-turbo")  # Use cheaper model for non-code
    register_rule(code_rule)
    
    # Create a router that uses both rules in sequence
    router = Router(
        name="explain-demo-router",
        rules=[task_rule, code_rule],  # Try task rule first, then code rule
        default="gpt-3.5-turbo"
    )
    register_router(router)
    
    return router


def test_explain_feature():
    """Test the explain feature with various scenarios."""
    
    print("Setting up router with multiple rules...")
    router = setup_example_router()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Creative Writing Task",
            "messages": [{"role": "user", "content": "Write a short story about a dragon"}],
            "task": "creative writing",
            "expected_trigger": "creative writing"
        },
        {
            "name": "Code Review Task", 
            "messages": [{"role": "user", "content": "Review this Python function"}],
            "task": "code review",
            "expected_trigger": "code review"
        },
        {
            "name": "Code Detection (no task)",
            "messages": [{"role": "user", "content": "def hello_world():\n    print('Hello, World!')"}],
            "expected_trigger": "code_detected"
        },
        {
            "name": "Natural Language (no task)",
            "messages": [{"role": "user", "content": "What is the weather like today?"}],
            "expected_trigger": "no_code_detected"
        },
        {
            "name": "Unknown Task (falls to code rule)",
            "messages": [{"role": "user", "content": "Help me with machine learning"}],
            "task": "unknown_task",
            "expected_trigger": "no_code_detected"
        },
        {
            "name": "Default Fallback",
            "messages": [{"role": "user", "content": ""}],
            "expected_trigger": "None"
        }
    ]
    
    print("\n" + "="*80)
    print("TESTING EXPLAIN FEATURE")
    print("="*80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 50)
        
        # Prepare request data
        request_data = {
            'messages': test_case['messages']
        }
        if 'task' in test_case:
            request_data['task'] = test_case['task']
        
        # Get model selection with explanation
        selected_model, explanation = router.select_model_with_explanation(request_data)
        
        print(f"Selected Model: {selected_model}")
        print(f"Explanation ({len(explanation)} entries):")
        
        for j, entry in enumerate(explanation, 1):
            print(f"  {j}. Rule Type: {entry.rule_type}")
            print(f"     Rule Name: {entry.rule_name}")
            print(f"     Trigger: {entry.rule_trigger}")
            print(f"     Decision: {entry.decision}")
            if j < len(explanation):
                print()
        
        # Show JSON format
        print(f"\nJSON Format:")
        explanation_json = [entry.to_dict() for entry in explanation]
        print(json.dumps(explanation_json, indent=2))


def test_chat_api_explain():
    """Test the explain feature through the chat API."""
    
    print("\n" + "="*80)
    print("TESTING CHAT API WITH EXPLAIN")
    print("="*80)
    
    # Note: This would normally make actual API calls, but for demo purposes
    # we'll show how it would work
    
    test_requests = [
        {
            "messages": [{"role": "user", "content": "Write a poem about coding"}],
            "model": "deimos/explain-demo-router",
            "task": "creative writing",
            "explain": True
        },
        {
            "messages": [{"role": "user", "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"}],
            "model": "deimos/explain-demo-router", 
            "explain": True
        }
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. Chat API Request:")
        print(f"   Messages: {request['messages'][0]['content'][:50]}...")
        print(f"   Model: {request['model']}")
        print(f"   Task: {request.get('task', 'None')}")
        print(f"   Explain: {request['explain']}")
        
        # This is what the response would look like
        print(f"\n   Expected Response Structure:")
        print(f"   - response.model: [selected model]")
        print(f"   - response._deimos_metadata['explain']: [explanation array]")
        print(f"   - Each explanation entry has: rule_type, rule_name, rule_trigger, decision")


if __name__ == "__main__":
    # Run the tests
    test_explain_feature()
    test_chat_api_explain()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("The explain feature provides detailed information about how routing decisions are made:")
    print("1. Each rule evaluation is tracked with its type, name, trigger, and decision")
    print("2. The explanation accumulates as rules are evaluated in sequence")
    print("3. The final explanation shows the complete decision path")
    print("4. This is compatible with OpenAI's response format via metadata")
    print("5. Callers expecting standard OpenAI responses won't be affected")
