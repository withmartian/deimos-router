#!/usr/bin/env python3
"""
Test that routing metadata is now available by default (explain=True by default).
"""

import sys
sys.path.insert(0, '../src')

from deimos_router import Router, register_router, chat
from deimos_router.rules import TaskRule

# Create a simple router
router = Router(
    name="test-default-explain",
    rules=[
        TaskRule(
            name="simple-task-rule",
            triggers={
                'coding': 'openai/gpt-4o',
                'simple': 'openai/gpt-4o-mini'
            }
        )
    ],
    default="openai/gpt-4o-mini"
)

register_router(router)

print("Testing default explain behavior...")
print("="*50)

# Test 1: Default behavior (should now include explanation)
response = chat.completions.create(
    model="deimos/test-default-explain",
    messages=[
        {"role": "user", "content": "Write a simple hello world function"}
    ],
    task="coding"
)

print("Test 1: Default behavior (no explicit explain parameter)")
if hasattr(response, '_deimos_metadata'):
    metadata = response._deimos_metadata
    print(f"✓ Router used: {metadata.get('router_used')}")
    print(f"✓ Selected model: {metadata.get('selected_model')}")
    
    if 'explain' in metadata:
        print("✓ Explanation available by default!")
        for entry in metadata['explain']:
            print(f"  - Rule: {entry['rule_name']}")
            print(f"    Trigger: {entry['rule_trigger']}")
            print(f"    Decision: {entry['decision']}")
    else:
        print("✗ No explanation found")
else:
    print("✗ No metadata found")

print("\n" + "="*50)

# Test 2: Explicitly setting explain=False
response2 = chat.completions.create(
    model="deimos/test-default-explain",
    messages=[
        {"role": "user", "content": "What's 2+2?"}
    ],
    task="simple",
    explain=False  # Explicitly disable explanation
)

print("Test 2: Explicitly setting explain=False")
if hasattr(response2, '_deimos_metadata'):
    metadata2 = response2._deimos_metadata
    print(f"✓ Router used: {metadata2.get('router_used')}")
    print(f"✓ Selected model: {metadata2.get('selected_model')}")
    
    if 'explain' in metadata2:
        print("✗ Explanation still present (should be disabled)")
    else:
        print("✓ Explanation correctly disabled")
else:
    print("✗ No metadata found")

print("\n" + "="*50)
print("Summary: Routing metadata should now be available by default!")
print("You no longer need to add explain=True to get routing information.")
