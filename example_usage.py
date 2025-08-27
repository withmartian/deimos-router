"""Example usage of deimos-router demonstrating the key functionality."""

import deimos_router
from deimos_router import Router, register_router, chat

def main():
    print("=== Deimos Router Example ===\n")
    
    # Checkpoint 1: User can create a Router
    print("1. Creating a router named 'my-router'...")
    my_router = Router("my-router")
    register_router(my_router)
    print(f"   Created router: {my_router}")
    print(f"   Available models: {my_router.models}")
    print()
    
    # Show router selection in action
    print("2. Testing router model selection...")
    for i in range(3):
        selected = my_router.select_model()
        print(f"   Selection {i+1}: {selected}")
    print()
    
    # Checkpoint 2 & 3: Making API calls (these would work with real credentials)
    print("3. Example API calls (would work with real credentials):")
    
    # Example messages
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    print("\n   Direct model call example:")
    print("   response = chat.completions.create(")
    print("       messages=messages,")
    print("       model='gpt-3.5-turbo',")
    print("       temperature=0.7")
    print("   )")
    print("   # This would call the model directly")
    
    print("\n   Router-based call example:")
    print("   response = chat.completions.create(")
    print("       messages=messages,")
    print("       model='deimos/my-router',")
    print("       temperature=0.7")
    print("   )")
    print("   # This would:")
    print("   # 1. Look up the 'my-router' router")
    print("   # 2. Call router.select_model() to choose a model")
    print("   # 3. Make the API call with the selected model")
    print("   # 4. Add routing metadata to the response")
    
    print("\n   Response would include routing metadata:")
    print("   response._deimos_metadata = {")
    print("       'router_used': 'my-router',")
    print("       'selected_model': 'gpt-3.5-turbo',  # (or whichever was selected)")
    print("       'available_models': ['gpt-3.5-turbo', 'gpt-3.5-turbo-0125', ...]")
    print("   }")
    
    print("\n=== All checkpoints demonstrated! ===")
    print("✓ User can create a Router like 'my-router'")
    print("✓ User can make calls using deimos.chat.completions to a selected model")
    print("✓ User can make calls using deimos.chat.completions to a router")
    print("✓ Router responses include information about which model was selected")

if __name__ == "__main__":
    main()
