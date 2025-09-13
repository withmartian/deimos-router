#!/usr/bin/env python3
"""Test script to reproduce rule chaining issue."""

from src.deimos_router.rules import CodeRule, TaskRule
from src.deimos_router.router import Router, register_router


def test_rule_chaining():
    """Test the rule chaining scenario described by the user."""
    
    print("=== Testing Rule Chaining Issue ===\n")
    
    # Create the language decision rule (second rule in chain)
    language_rule = TaskRule(
        name="language-decider",
        triggers={
            "python": "gpt-4",
            "sql": "claude-3-5-sonnet"
        }
    )
    
    # Create the code detection rule that chains to language rule
    code_or_not_rule = CodeRule(
        name="code-or-not",
        code="deimos/rules/language-decider",  # Chain to the language rule
        not_code="gpt-3.5-turbo"               # Direct model for non-code
    )
    
    # Create router using the first rule
    router = Router(
        name="chaining-test-router",
        rules=[code_or_not_rule],
        default="gpt-4o-mini"
    )
    
    print("Created rules:")
    print(f"  - {language_rule}")
    print(f"  - {code_or_not_rule}")
    print(f"  - Router: {router}")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Non-code request (should work)",
            "request_data": {
                "messages": [
                    {"role": "user", "content": "What is the weather like today? Please explain how weather patterns work."}
                ]
            },
            "expected": "gpt-3.5-turbo"
        },
        {
            "name": "Python code request (should break/chain)",
            "request_data": {
                "messages": [
                    {"role": "user", "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"}
                ],
                "task": "python"
            },
            "expected": "gpt-4"
        },
        {
            "name": "SQL code request (should break/chain)",
            "request_data": {
                "messages": [
                    {"role": "user", "content": "SELECT * FROM users WHERE created_at > '2024-01-01' ORDER BY name;"}
                ],
                "task": "sql"
            },
            "expected": "claude-3-5-sonnet"
        },
        {
            "name": "Code without task (should break)",
            "request_data": {
                "messages": [
                    {"role": "user", "content": "function processData(data) {\n    return data.map(item => item.value);\n}"}
                ]
            },
            "expected": "Should chain but task not specified"
        }
    ]
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("-" * (len(test_case['name']) + 3))
        
        try:
            # Test with regular select_model
            selected_model = router.select_model(test_case["request_data"])
            print(f"✓ Selected model: {selected_model}")
            
            # Test with explanation
            selected_model_exp, explanation = router.select_model_with_explanation(test_case["request_data"])
            print(f"✓ Selected model (with explanation): {selected_model_exp}")
            print(f"  Explanation:")
            for entry in explanation:
                print(f"    - {entry.rule_type}({entry.rule_name}): {entry.rule_trigger} → {entry.decision}")
            
            if "expected" in test_case:
                expected = test_case["expected"]
                if selected_model == expected:
                    print(f"✓ Expected: {expected} - MATCHED")
                else:
                    print(f"✗ Expected: {expected} - GOT: {selected_model}")
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print()


def test_rule_evaluation_directly():
    """Test rule evaluation directly to isolate the issue."""
    
    print("=== Testing Rule Evaluation Directly ===\n")
    
    # Create the same rules
    language_rule = TaskRule(
        name="language-decider",
        triggers={
            "python": "gpt-4", 
            "sql": "claude-3-5-sonnet"
        }
    )
    
    code_or_not_rule = CodeRule(
        name="code-or-not",
        code="deimos/rules/language-decider",
        not_code="gpt-3.5-turbo"
    )
    
    # Test the code rule directly
    python_request = {
        "messages": [
            {"role": "user", "content": "def hello():\n    print('hello world')"}
        ],
        "task": "python"
    }
    
    print("1. Testing CodeRule directly with Python code:")
    decision1 = code_or_not_rule.evaluate(python_request)
    print(f"   Decision: {decision1}")
    print(f"   Is model? {decision1.is_model()}")
    print(f"   Is rule? {decision1.is_rule()}")
    print(f"   Rule name: {decision1.get_rule_name()}")
    print()
    
    # Test the language rule directly
    print("2. Testing TaskRule directly with Python task:")
    decision2 = language_rule.evaluate(python_request)
    print(f"   Decision: {decision2}")
    print(f"   Is model? {decision2.is_model()}")
    print(f"   Is rule? {decision2.is_rule()}")
    print(f"   Model name: {decision2.get_model()}")
    print()
    
    # Test non-code request
    non_code_request = {
        "messages": [
            {"role": "user", "content": "What is machine learning?"}
        ]
    }
    
    print("3. Testing CodeRule directly with non-code:")
    decision3 = code_or_not_rule.evaluate(non_code_request)
    print(f"   Decision: {decision3}")
    print(f"   Is model? {decision3.is_model()}")
    print(f"   Is rule? {decision3.is_rule()}")
    print(f"   Model name: {decision3.get_model()}")
    print()


if __name__ == "__main__":
    test_rule_evaluation_directly()
    test_rule_chaining()
