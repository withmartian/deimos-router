"""Example demonstrating rule-based model selection in deimos-router."""

import deimos_router
from deimos_router import TaskRule, Router, register_rule, register_router, chat


def main():
    print("=== Rule-Based Routing Example ===\n")
    
    # Example 1: Simple TaskRule
    print("1. Creating a TaskRule for different types of tasks...")
    
    task_rule = TaskRule(
        name="task-decider",
        rules={
            "code": "anthropic/claude-sonnet-4",
            "medical": "openai/gpt-5", 
            "advice": "gpt-3.5-turbo",
            "writing": "gpt-4"
        }
    )
    register_rule(task_rule)
    print(f"   Created rule: {task_rule}")
    print()
    
    # Example 2: Router using the TaskRule
    print("2. Creating a Router that uses the TaskRule...")
    
    router = Router(
        name="my-router",
        rules=["task-decider"],  # Reference to registered rule
        default="gpt-4o-mini"    # Fallback if no rules match
    )
    print(f"   Created router: {router}")
    print()
    
    # Example 3: Testing rule-based selection
    print("3. Testing rule-based model selection...")
    
    test_cases = [
        {"task": "code", "messages": [{"role": "user", "content": "Help me debug this Python code"}]},
        {"task": "medical", "messages": [{"role": "user", "content": "What are the symptoms of flu?"}]},
        {"task": "advice", "messages": [{"role": "user", "content": "Should I change careers?"}]},
        {"task": "unknown", "messages": [{"role": "user", "content": "Random question"}]},
        {"messages": [{"role": "user", "content": "No task specified"}]}  # No task field
    ]
    
    for i, request_data in enumerate(test_cases, 1):
        task = request_data.get("task", "none")
        selected_model = router.select_model(request_data)
        print(f"   Test {i} - Task: '{task}' → Selected: {selected_model}")
    print()
    
    # Example 4: Nested Rules (Rule Chains)
    print("4. Creating nested rules for more complex routing...")
    
    # Create a specialized advice rule
    advice_rule = TaskRule(
        name="advice-decider", 
        rules={
            "personal": "gpt-3.5-turbo",
            "professional": "gpt-4",
            "financial": "anthropic/claude-sonnet-4"
        }
    )
    register_rule(advice_rule)
    
    # Update the main rule to reference the advice rule
    main_rule = TaskRule(
        name="main-decider",
        rules={
            "code": "anthropic/claude-sonnet-4",
            "medical": "openai/gpt-5",
            "advice": advice_rule,  # Points to another rule
            "writing": "gpt-4"
        }
    )
    register_rule(main_rule)
    
    # Create router with the main rule
    advanced_router = Router(
        name="advanced-router",
        rules=["main-decider"],
        default="gpt-4o-mini"
    )
    
    print(f"   Created nested rules: main-decider → advice-decider")
    print(f"   Advanced router: {advanced_router}")
    print()
    
    # Example 5: Multiple Rules in Priority Order
    print("5. Creating router with multiple rules in priority order...")
    
    # High priority rule for urgent tasks
    urgent_rule = TaskRule(
        name="urgent-decider",
        rules={
            "emergency": "gpt-4",
            "critical": "gpt-4"
        }
    )
    register_rule(urgent_rule)
    
    # General rule for common tasks
    general_rule = TaskRule(
        name="general-decider", 
        rules={
            "code": "gpt-3.5-turbo",
            "writing": "gpt-3.5-turbo",
            "research": "gpt-4o-mini"
        }
    )
    register_rule(general_rule)
    
    # Router that checks urgent first, then general
    priority_router = Router(
        name="priority-router",
        rules=["urgent-decider", "general-decider"],  # Order matters!
        default="gpt-4o-mini"
    )
    
    print(f"   Priority router checks: urgent-decider → general-decider → default")
    
    priority_tests = [
        {"task": "emergency", "messages": []},  # Matches urgent rule
        {"task": "code", "messages": []},       # Matches general rule
        {"task": "unknown", "messages": []}     # Uses default
    ]
    
    for i, request_data in enumerate(priority_tests, 1):
        task = request_data.get("task", "none")
        selected_model = priority_router.select_model(request_data)
        print(f"   Priority Test {i} - Task: '{task}' → Selected: {selected_model}")
    print()
    
    # Example 6: API Call Examples (would work with real credentials)
    print("6. Example API calls using rule-based routing:")
    print()
    
    print("   # Code assistance request")
    print("   response = chat.completions.create(")
    print("       messages=[{'role': 'user', 'content': 'Help me optimize this algorithm'}],")
    print("       model='deimos/my-router',")
    print("       task='code',  # This triggers the rule-based selection")
    print("       temperature=0.7")
    print("   )")
    print("   # Would select: anthropic/claude-sonnet-4")
    print()
    
    print("   # Medical question")
    print("   response = chat.completions.create(")
    print("       messages=[{'role': 'user', 'content': 'Explain diabetes symptoms'}],")
    print("       model='deimos/my-router',")
    print("       task='medical',")
    print("       temperature=0.3")
    print("   )")
    print("   # Would select: openai/gpt-5")
    print()
    
    print("   # No task specified - uses default")
    print("   response = chat.completions.create(")
    print("       messages=[{'role': 'user', 'content': 'General question'}],")
    print("       model='deimos/my-router',")
    print("       temperature=0.7")
    print("   )")
    print("   # Would select: gpt-4o-mini (default)")
    print()
    
    print("=== Rule-Based Routing Features Demonstrated ===")
    print("✓ TaskRule creation with task-to-model mappings")
    print("✓ Router creation with rule references and defaults")
    print("✓ Rule-based model selection based on request data")
    print("✓ Nested rules (rule chains) for complex routing")
    print("✓ Multiple rules with priority ordering")
    print("✓ Fallback to default when no rules match")
    print("✓ Integration with chat completions API")


if __name__ == "__main__":
    main()
