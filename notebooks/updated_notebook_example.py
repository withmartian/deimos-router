# Updated version of your notebook with routing metadata access

import deimos_router
from deimos_router import Router, register_router, chat
from deimos_router.rules import TaskRule, AutoTaskRule

# Your original router
router = Router(
    name="my-first-router",
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

# Register the router
register_router(router)

# Use the router for chat completions WITH EXPLANATION
response = chat.completions.create(
    model="deimos/my-first-router",
    messages=[
        {"role": "user", "content": "Write a python function that finds the nth fibonacci number"}
    ],
    task="coding",
    explain=True  # Add this to get detailed routing info
)

print("Response content:")
print(response.choices[0].message.content)

# ACCESS ROUTING METADATA
print("\n" + "="*50)
print("ROUTING METADATA:")
print("="*50)

if hasattr(response, '_deimos_metadata'):
    metadata = response._deimos_metadata
    print(f"Router used: {metadata.get('router_used')}")
    print(f"Selected model: {metadata.get('selected_model')}")
    print(f"Available models: {metadata.get('available_models')}")
    
    # Detailed explanation of routing decisions
    if 'explain' in metadata:
        print(f"\nDetailed Routing Explanation:")
        for i, entry in enumerate(metadata['explain'], 1):
            print(f"  Step {i}:")
            print(f"    Rule Type: {entry['rule_type']}")
            print(f"    Rule Name: {entry['rule_name']}")
            print(f"    Trigger: {entry['rule_trigger']}")
            print(f"    Decision: {entry['decision']}")
else:
    print("No routing metadata found")

print("\n" + "="*50 + "\n")

# Your auto task router
auto_task = AutoTaskRule(
    name="auto-task-rule",
    triggers={
        "creative writing": "openai/gpt-4o",
        "code": "openai/gpt-4o",  # Fixed model name
        "informational": "openai/gpt-4o-mini",  # Fixed model name
        "haiku composition": "openai/gpt-4o-mini"  # Fixed model name
    },
)

auto_router = Router(
    name="auto-router",
    rules=[auto_task],
    default="openai/gpt-4o-mini"
)

register_router(auto_router)

# Use the auto router WITH EXPLANATION
response1 = chat.completions.create(
    model="deimos/auto-router",
    messages=[
        {"role": "user", "content": "Write a python function that finds the nth fibonacci number"}
    ],
    explain=True  # Get routing explanation
)

print("Auto Router Response:")
print(response1.choices[0].message.content[:200] + "...")

# ACCESS AUTO ROUTER METADATA
print("\n" + "="*50)
print("AUTO ROUTER METADATA:")
print("="*50)

def print_routing_info(response, title=""):
    """Helper function to print routing information"""
    if title:
        print(f"\n{title}:")
    
    if hasattr(response, '_deimos_metadata'):
        metadata = response._deimos_metadata
        print(f"  Router used: {metadata.get('router_used')}")
        print(f"  Selected model: {metadata.get('selected_model')}")
        
        if 'explain' in metadata:
            print(f"  Routing explanation:")
            for entry in metadata['explain']:
                print(f"    - Rule: {entry['rule_name']} ({entry['rule_type']})")
                print(f"      Trigger: {entry['rule_trigger']}")
                print(f"      Decision: {entry['decision']}")
    else:
        print("  No routing metadata found")

print_routing_info(response1, "Coding Task")

# Test haiku with explanation
haiku = chat.completions.create(
    model="deimos/auto-router",
    messages=[
        {"role": "user", "content": "Write a short japanese poem about mars, and follow the syllable count 5, 7, 5"}
    ],
    explain=True
)

print(f"\nHaiku Response:")
print(haiku.choices[0].message.content)

print_routing_info(haiku, "Haiku Task")

# QUICK ACCESS FUNCTION
def get_routing_summary(response):
    """Quick function to get key routing info"""
    if not hasattr(response, '_deimos_metadata'):
        return "No routing info available"
    
    metadata = response._deimos_metadata
    router = metadata.get('router_used', 'Unknown')
    model = metadata.get('selected_model', 'Unknown')
    
    # Get the trigger from explanation if available
    trigger = "Unknown"
    if 'explain' in metadata and metadata['explain']:
        # Get the final decision's trigger
        final_decision = metadata['explain'][-1]
        trigger = final_decision.get('rule_trigger', 'Unknown')
    
    return f"Router: {router} | Model: {model} | Trigger: {trigger}"

print("\n" + "="*50)
print("QUICK ROUTING SUMMARIES:")
print("="*50)
print(f"Coding task: {get_routing_summary(response1)}")
print(f"Haiku task: {get_routing_summary(haiku)}")
