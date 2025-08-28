#!/usr/bin/env python3
"""
Example showing how to access routing metadata from deimos responses.
"""

import sys
sys.path.insert(0, '../src')

from deimos_router import Router, register_router, chat
from deimos_router.rules import TaskRule

# Create and register a router
router = Router(
    name="metadata-example-router",
    rules=[
        TaskRule(
            name="task-based-routing",
            triggers={
                'coding': 'openai/gpt-4o',
                'creative': 'openai/gpt-4o',
                'simple': 'openai/gpt-4o-mini'
            }
        )
    ],
    default="openai/gpt-4o-mini"
)

register_router(router)

# Example 1: Basic usage - metadata is automatically added
print("=== Example 1: Basic Usage ===")
response = chat.completions.create(
    model="deimos/metadata-example-router",
    messages=[
        {"role": "user", "content": "Write a python function that finds the nth fibonacci number"}
    ],
    task="coding"
)

print(f"Response model: {response.model}")
print(f"Response content: {response.choices[0].message.content[:100]}...")

# Access routing metadata
if hasattr(response, '_deimos_metadata'):
    metadata = response._deimos_metadata
    print(f"\nRouting Metadata:")
    print(f"  Router used: {metadata.get('router_used')}")
    print(f"  Selected model: {metadata.get('selected_model')}")
    print(f"  Available models: {metadata.get('available_models')}")
else:
    print("No routing metadata found")

print("\n" + "="*50 + "\n")

# Example 2: With explanation - get detailed routing decision info
print("=== Example 2: With Explanation ===")
response_with_explanation = chat.completions.create(
    model="deimos/metadata-example-router",
    messages=[
        {"role": "user", "content": "Write a creative story about a robot"}
    ],
    task="creative",
    explain=True  # This enables detailed explanation
)

print(f"Response model: {response_with_explanation.model}")
print(f"Response content: {response_with_explanation.choices[0].message.content[:100]}...")

# Access detailed routing explanation
if hasattr(response_with_explanation, '_deimos_metadata'):
    metadata = response_with_explanation._deimos_metadata
    print(f"\nRouting Metadata:")
    print(f"  Router used: {metadata.get('router_used')}")
    print(f"  Selected model: {metadata.get('selected_model')}")
    
    # Detailed explanation of routing decisions
    if 'explain' in metadata:
        print(f"\nDetailed Routing Explanation:")
        for i, entry in enumerate(metadata['explain'], 1):
            print(f"  Step {i}:")
            print(f"    Rule Type: {entry['rule_type']}")
            print(f"    Rule Name: {entry['rule_name']}")
            print(f"    Trigger: {entry['rule_trigger']}")
            print(f"    Decision: {entry['decision']}")

print("\n" + "="*50 + "\n")

# Example 3: Helper function to extract routing info
def get_routing_info(response):
    """Helper function to extract routing information from a response."""
    if not hasattr(response, '_deimos_metadata'):
        return None
    
    metadata = response._deimos_metadata
    routing_info = {
        'router_used': metadata.get('router_used'),
        'selected_model': metadata.get('selected_model'),
        'available_models': metadata.get('available_models', []),
        'explanation': metadata.get('explain', [])
    }
    
    # Extract the final trigger and rule that made the decision
    if routing_info['explanation']:
        final_decision = routing_info['explanation'][-1]
        routing_info['final_rule'] = final_decision['rule_name']
        routing_info['final_trigger'] = final_decision['rule_trigger']
        routing_info['final_rule_type'] = final_decision['rule_type']
    
    return routing_info

print("=== Example 3: Using Helper Function ===")
response3 = chat.completions.create(
    model="deimos/metadata-example-router",
    messages=[
        {"role": "user", "content": "What's 2+2?"}
    ],
    task="simple",
    explain=True
)

routing_info = get_routing_info(response3)
if routing_info:
    print(f"Router: {routing_info['router_used']}")
    print(f"Selected Model: {routing_info['selected_model']}")
    print(f"Final Rule: {routing_info.get('final_rule', 'N/A')}")
    print(f"Final Trigger: {routing_info.get('final_trigger', 'N/A')}")
    print(f"Rule Type: {routing_info.get('final_rule_type', 'N/A')}")
else:
    print("No routing information available")
