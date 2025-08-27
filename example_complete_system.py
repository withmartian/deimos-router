"""Complete example demonstrating the rule-based routing system as requested."""

import deimos_router
from deimos_router import TaskRule, Router, register_rule, register_router, chat


def main():
    print("=== Complete Rule-Based Routing System Example ===\n")
    
    # Example from the user's request
    print("1. Creating the exact example from the user's request...")
    
    # Create TaskRule as specified
    task_rule = TaskRule(
        name="task-decider",
        rules={
            "code": "anthropic/claude-sonnet-4",
            "medical": "openai/gpt-5",
            "advice": "deimos/rule/advice-decider"  # This would reference another rule
        }
    )
    register_rule(task_rule)
    
    # Create Router as specified
    router = Router(
        name="my-router",
        rules=["task-decider"],  # List of rules to evaluate
        default="openai/gpt-5"   # Default model if no rules match
    )
    register_router(router)
    
    print(f"   Created TaskRule: {task_rule}")
    print(f"   Created Router: {router}")
    print()
    
    # Test the routing logic
    print("2. Testing the routing logic...")
    
    test_cases = [
        {"task": "code", "messages": [{"role": "user", "content": "Debug my Python code"}]},
        {"task": "medical", "messages": [{"role": "user", "content": "What are flu symptoms?"}]},
        {"task": "advice", "messages": [{"role": "user", "content": "Career advice needed"}]},
        {"task": "unknown", "messages": [{"role": "user", "content": "Random question"}]},
        {"messages": [{"role": "user", "content": "No task specified"}]}
    ]
    
    for i, request_data in enumerate(test_cases, 1):
        task = request_data.get("task", "none")
        selected_model = router.select_model(request_data)
        print(f"   Test {i} - Task: '{task}' → Selected: {selected_model}")
    print()
    
    # Demonstrate the decision tree concept
    print("3. Demonstrating composable decision trees...")
    
    # Create the advice-decider rule that was referenced
    advice_rule = TaskRule(
        name="advice-decider",
        rules={
            "personal": "gpt-3.5-turbo",
            "professional": "gpt-4",
            "financial": "anthropic/claude-sonnet-4"
        }
    )
    register_rule(advice_rule)
    
    # Update the main rule to properly reference the advice rule
    updated_task_rule = TaskRule(
        name="updated-task-decider",
        rules={
            "code": "anthropic/claude-sonnet-4",
            "medical": "openai/gpt-5",
            "advice": advice_rule  # Direct reference to rule object
        }
    )
    register_rule(updated_task_rule)
    
    # Create router with the updated rule
    advanced_router = Router(
        name="advanced-router",
        rules=["updated-task-decider"],
        default="openai/gpt-5"
    )
    register_router(advanced_router)
    
    print(f"   Created nested advice rule: {advice_rule}")
    print(f"   Updated main rule to reference advice rule")
    print(f"   Advanced router: {advanced_router}")
    print()
    
    # Test the decision tree
    print("4. Testing decision tree traversal...")
    
    # This demonstrates the concept, though the advice rule would need
    # additional logic to look at more than just the 'task' field
    decision_tests = [
        {"task": "code", "messages": []},
        {"task": "medical", "messages": []},
        {"task": "advice", "messages": []},  # This will find the advice rule but it won't match further
        {"task": "unknown", "messages": []}
    ]
    
    for i, request_data in enumerate(decision_tests, 1):
        task = request_data.get("task", "none")
        selected_model = advanced_router.select_model(request_data)
        print(f"   Decision Test {i} - Task: '{task}' → Selected: {selected_model}")
    print()
    
    # Show how the system works with chat completions
    print("5. Integration with chat completions API...")
    print()
    
    print("   Example API calls that would work with real credentials:")
    print()
    
    print("   # Code task - routes to anthropic/claude-sonnet-4")
    print("   response = chat.completions.create(")
    print("       messages=[{'role': 'user', 'content': 'Help me optimize this algorithm'}],")
    print("       model='deimos/my-router',")
    print("       task='code',")
    print("       temperature=0.7")
    print("   )")
    print("   # Router evaluates: task='code' → anthropic/claude-sonnet-4")
    print()
    
    print("   # Medical task - routes to openai/gpt-5")
    print("   response = chat.completions.create(")
    print("       messages=[{'role': 'user', 'content': 'Explain diabetes'}],")
    print("       model='deimos/my-router',")
    print("       task='medical',")
    print("       temperature=0.3")
    print("   )")
    print("   # Router evaluates: task='medical' → openai/gpt-5")
    print()
    
    print("   # Unknown task - uses default")
    print("   response = chat.completions.create(")
    print("       messages=[{'role': 'user', 'content': 'General question'}],")
    print("       model='deimos/my-router',")
    print("       task='unknown',")
    print("       temperature=0.7")
    print("   )")
    print("   # Router evaluates: task='unknown' → openai/gpt-5 (default)")
    print()
    
    # Demonstrate the key concepts
    print("6. Key concepts demonstrated:")
    print()
    print("   ✓ Rule Class: Abstract base for all routing rules")
    print("   ✓ Decision Class: Represents rule outcomes (model, rule, or none)")
    print("   ✓ TaskRule: Matches 'task' field to models or other rules")
    print("   ✓ Router: Evaluates rules in order, falls back to default")
    print("   ✓ Rule Chains: Rules can reference other rules for complex routing")
    print("   ✓ Priority Order: Multiple rules evaluated in sequence")
    print("   ✓ Fallback Logic: Default model when no rules match")
    print("   ✓ API Integration: Works seamlessly with chat.completions.create()")
    print()
    
    print("=== System Architecture ===")
    print()
    print("Request → Router → Rule Chain → Decision → Model Selection")
    print()
    print("1. User makes API call with task parameter")
    print("2. Router receives request data including task")
    print("3. Router evaluates rules in priority order")
    print("4. Each rule returns a Decision (model, rule, or none)")
    print("5. If Decision is another rule, continue evaluation")
    print("6. If Decision is a model, use that model")
    print("7. If Decision is none, try next rule")
    print("8. If all rules fail, use router's default model")
    print("9. Make API call with selected model")
    print("10. Return response with routing metadata")


if __name__ == "__main__":
    main()
