"""Example usage of MessageLengthRule for routing based on message length."""

from src.deimos_router.rules import MessageLengthRule
from src.deimos_router.router import Router


def main():
    """Demonstrate MessageLengthRule usage."""
    
    # Create a message length rule
    # Short messages (< 200 chars) -> fast model
    # Medium messages (200-1500 chars) -> balanced model  
    # Long messages (>= 1500 chars) -> powerful model
    length_rule = MessageLengthRule(
        name="length_router",
        short_threshold=200,
        long_threshold=1500,
        short_model="gpt-3.5-turbo",
        medium_model="gpt-4",
        long_model="gpt-4-turbo"
    )
    
    # Create router with the length rule
    router = Router(name="length_demo", rules=[length_rule])
    
    # Test cases
    test_cases = [
        {
            "name": "Short message",
            "messages": [
                {"role": "user", "content": "What is 2+2?"}
            ]
        },
        {
            "name": "Medium message", 
            "messages": [
                {"role": "user", "content": "Can you explain the differences between React hooks and class components? I'm trying to understand when to use each approach and what the performance implications might be. Also, are there any best practices I should follow when migrating from class components to hooks?"}
            ]
        },
        {
            "name": "Long message",
            "messages": [
                {"role": "user", "content": """I'm working on a complex web application that needs to handle real-time data updates, user authentication, file uploads, and integration with multiple third-party APIs. The frontend is built with React and TypeScript, and the backend uses Node.js with Express. 

I'm facing several challenges:

1. Performance issues when handling large datasets - the UI becomes sluggish when displaying tables with thousands of rows
2. Memory leaks that seem to occur during file upload operations, especially with large files
3. Authentication token refresh logic that sometimes fails and logs users out unexpectedly
4. Race conditions in API calls that cause inconsistent state updates
5. Difficulty in testing components that rely heavily on external API responses

Could you provide a comprehensive analysis of these issues and suggest architectural improvements? I'm particularly interested in:
- Best practices for optimizing React performance with large datasets
- Proper memory management during file operations
- Robust authentication flow implementation
- State management patterns that prevent race conditions
- Testing strategies for API-dependent components

Please include code examples where relevant and explain the trade-offs of different approaches. I'd also like to understand how to implement proper error boundaries, optimize bundle sizes, handle offline scenarios, implement proper caching strategies, and ensure accessibility compliance. Additionally, what are the best practices for state management in large applications, how to structure component hierarchies for maintainability, and what testing frameworks work best for different types of components and integration scenarios?"""}
            ]
        }
    ]
    
    print("MessageLengthRule Example")
    print("=" * 50)
    print(f"Rule configuration:")
    print(f"  Short threshold: {length_rule.short_threshold} chars -> {length_rule.short_model}")
    print(f"  Long threshold: {length_rule.long_threshold} chars -> {length_rule.long_model}")
    print(f"  Medium messages: {length_rule.medium_model}")
    print()
    
    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        
        # Calculate message length
        user_content = ""
        for msg in test_case['messages']:
            if msg.get('role') == 'user':
                user_content += msg.get('content', '')
        
        message_length = len(user_content)
        print(f"  Message length: {message_length} characters")
        
        # Get routing decision
        selected_model, explanation = router.select_model_with_explanation(test_case)
        print(f"  Selected model: {selected_model}")
        print(f"  Trigger: {explanation[0].rule_trigger}")
        print()


if __name__ == "__main__":
    main()
