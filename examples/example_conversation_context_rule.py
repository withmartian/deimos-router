"""Example usage of ConversationContextRule for conversation depth-based routing."""

from src.deimos_router.rules import ConversationContextRule
from src.deimos_router.router import Router


def main():
    """Demonstrate ConversationContextRule usage."""
    
    # Create a conversation context rule
    # - New conversations (< 3 messages): Use fast, lightweight model
    # - Developing conversations (3-10 messages): Use balanced model
    # - Deep conversations (10+ messages): Use powerful, context-aware model
    context_rule = ConversationContextRule(
        name="conversation_depth_router",
        new_threshold=3,
        deep_threshold=10,
        new_model="gpt-3.5-turbo",      # Fast for new conversations
        developing_model="gpt-4",        # Balanced for ongoing discussions
        deep_model="gpt-4-turbo"         # Powerful for complex, long conversations
    )
    
    # Create router with the context rule
    router = Router(name="conversation_router", rules=[context_rule])
    
    # Example 1: New conversation (1 message)
    print("=== Example 1: New Conversation ===")
    new_conversation = {
        "messages": [
            {"role": "user", "content": "Hello! Can you help me with something?"}
        ]
    }
    
    selected_model, explanation = router.select_model_with_explanation(new_conversation)
    print(f"Model selected: {selected_model}")
    print(f"Explanation: {explanation[0].decision}")
    print(f"Trigger: {explanation[0].rule_trigger}")
    print()
    
    # Example 2: Developing conversation (5 messages)
    print("=== Example 2: Developing Conversation ===")
    developing_conversation = {
        "messages": [
            {"role": "user", "content": "Hello! Can you help me with Python?"},
            {"role": "assistant", "content": "Of course! I'd be happy to help you with Python. What specific topic would you like to learn about?"},
            {"role": "user", "content": "I'm trying to understand list comprehensions."},
            {"role": "assistant", "content": "Great choice! List comprehensions are a powerful feature in Python. They provide a concise way to create lists."},
            {"role": "user", "content": "Can you show me some examples with filtering?"}
        ]
    }
    
    selected_model, explanation = router.select_model_with_explanation(developing_conversation)
    print(f"Model selected: {selected_model}")
    print(f"Explanation: {explanation[0].decision}")
    print(f"Trigger: {explanation[0].rule_trigger}")
    print()
    
    # Example 3: Deep conversation (12 messages)
    print("=== Example 3: Deep Conversation ===")
    deep_conversation = {
        "messages": [
            {"role": "user", "content": "I'm working on a complex machine learning project."},
            {"role": "assistant", "content": "That sounds interesting! What kind of ML project are you working on?"},
            {"role": "user", "content": "It's a recommendation system for an e-commerce platform."},
            {"role": "assistant", "content": "Recommendation systems are fascinating! Are you using collaborative filtering, content-based filtering, or a hybrid approach?"},
            {"role": "user", "content": "I'm trying to implement a hybrid approach, but I'm having issues with cold start problems."},
            {"role": "assistant", "content": "Cold start is indeed a common challenge. For new users, you might consider using demographic-based recommendations or popular items."},
            {"role": "user", "content": "That makes sense. What about handling sparse data in the user-item matrix?"},
            {"role": "assistant", "content": "For sparse matrices, you could use matrix factorization techniques like SVD or NMF, or consider deep learning approaches like autoencoders."},
            {"role": "user", "content": "I've been experimenting with SVD, but the results aren't great. Should I try neural collaborative filtering?"},
            {"role": "assistant", "content": "Neural collaborative filtering can be very effective! It can capture non-linear relationships that traditional methods might miss."},
            {"role": "user", "content": "How would you handle the evaluation metrics? I'm using RMSE but wondering about ranking metrics."},
            {"role": "assistant", "content": "For recommendation systems, ranking metrics like NDCG, MAP, or Precision@K are often more meaningful than RMSE since you care about the order of recommendations."}
        ]
    }
    
    selected_model, explanation = router.select_model_with_explanation(deep_conversation)
    print(f"Model selected: {selected_model}")
    print(f"Explanation: {explanation[0].decision}")
    print(f"Trigger: {explanation[0].rule_trigger}")
    print()
    
    # Example 4: Demonstrate threshold updates
    print("=== Example 4: Dynamic Threshold Updates ===")
    print(f"Original thresholds: {context_rule.get_thresholds()}")
    
    # Update thresholds for different conversation patterns
    context_rule.update_thresholds(new_threshold=2, deep_threshold=8)
    print(f"Updated thresholds: {context_rule.get_thresholds()}")
    
    # Test with the same developing conversation (now should be "deep")
    selected_model, explanation = router.select_model_with_explanation(developing_conversation)
    print(f"Same 5-message conversation now routes to: {selected_model}")
    print(f"Stage: {context_rule.get_conversation_stage(developing_conversation)}")
    print()
    
    # Example 5: Conversation with mixed message types
    print("=== Example 5: Mixed Message Types ===")
    mixed_conversation = {
        "messages": [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "I need help debugging this Python code."},
            {"role": "assistant", "content": "I'd be happy to help! Please share your code."},
            {"role": "user", "content": "Here's the code: def factorial(n): return n * factorial(n-1)"},
            {"role": "assistant", "content": "I see the issue - you're missing a base case for the recursion."}
        ]
    }
    
    selected_model, explanation = router.select_model_with_explanation(mixed_conversation)
    print(f"Model selected: {selected_model}")
    print(f"Message count includes system messages: {explanation[0].rule_trigger}")
    print()
    
    # Example 6: Business use case scenarios
    print("=== Example 6: Business Use Case Scenarios ===")
    
    # Customer support scenario
    customer_support_rule = ConversationContextRule(
        name="customer_support_router",
        new_threshold=2,      # Quick triage for new issues
        deep_threshold=6,     # Escalate complex issues
        new_model="gpt-3.5-turbo",     # Fast initial response
        developing_model="gpt-4",       # Standard support
        deep_model="gpt-4-turbo"        # Complex issue resolution
    )
    
    support_router = Router(name="support_router", rules=[customer_support_rule])
    
    # New customer inquiry
    new_inquiry = {
        "messages": [
            {"role": "user", "content": "Hi, I can't log into my account."}
        ]
    }
    
    selected_model, explanation = support_router.select_model_with_explanation(new_inquiry)
    print(f"New customer inquiry → {selected_model} (fast triage)")
    
    # Complex ongoing support case
    complex_case = {
        "messages": [
            {"role": "user", "content": "I'm having issues with my billing."},
            {"role": "assistant", "content": "I can help with billing issues. What specific problem are you experiencing?"},
            {"role": "user", "content": "I was charged twice for the same subscription."},
            {"role": "assistant", "content": "I apologize for the inconvenience. Let me look into this duplicate charge."},
            {"role": "user", "content": "This has happened before. I want to understand why."},
            {"role": "assistant", "content": "I understand your frustration. Let me investigate the pattern of charges on your account."},
            {"role": "user", "content": "I'm considering canceling if this keeps happening."},
            {"role": "assistant", "content": "I completely understand. Let me escalate this to ensure we resolve it properly and prevent future occurrences."}
        ]
    }
    
    selected_model, explanation = support_router.select_model_with_explanation(complex_case)
    print(f"Complex support case → {selected_model} (specialized handling)")


if __name__ == "__main__":
    main()
