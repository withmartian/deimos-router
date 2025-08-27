#!/usr/bin/env python3
"""Example usage of AutoTaskRule for automatic task detection and routing."""

import asyncio
from deimos_router import Router
from deimos_router.rules import AutoTaskRule


def create_auto_task_router():
    """Create a router that automatically detects tasks from message content."""
    
    # Define task mappings for common LLM use cases
    task_mappings = {
        'writing': 'gpt-4o',           # Creative writing, blog posts, articles
        'coding': 'claude-3-sonnet',   # Programming, debugging, code review
        'analysis': 'gpt-4o-mini',     # Data analysis, research, insights
        'summarization': 'gpt-4o-mini', # Summarizing documents, articles
        'translation': 'claude-3-haiku', # Language translation
        'explanation': 'gpt-4o',       # Explaining concepts, teaching
        'brainstorming': 'gpt-4o',     # Idea generation, creative thinking
    }
    
    # Create the auto task rule
    auto_task_rule = AutoTaskRule(
        name='auto_task_router',
        task_mappings=task_mappings,
        default='gpt-4o-mini',  # Default for undetected/unmapped tasks
        llm_model='gpt-4o-mini'  # Use smallest model for task detection
    )
    
    # Create and configure the router
    router = Router()
    router.add_rule(auto_task_rule)
    
    return router


async def test_auto_task_routing():
    """Test the auto task router with various common LLM tasks."""
    
    router = create_auto_task_router()
    
    # Test cases with different common tasks
    test_cases = [
        {
            'name': 'Creative Writing',
            'messages': [
                {'role': 'user', 'content': 'Write a short story about a robot who discovers emotions for the first time. Make it touching and thought-provoking.'}
            ],
            'expected_task': 'writing',
            'expected_model': 'gpt-4o'
        },
        {
            'name': 'Programming Help',
            'messages': [
                {'role': 'user', 'content': 'Help me debug this Python function. It\'s supposed to calculate fibonacci numbers but it\'s running too slowly:\n\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)'}
            ],
            'expected_task': 'coding',
            'expected_model': 'claude-3-sonnet'
        },
        {
            'name': 'Data Analysis',
            'messages': [
                {'role': 'user', 'content': 'Analyze this sales data and identify trends. What insights can you provide about customer behavior patterns over the last quarter?'}
            ],
            'expected_task': 'analysis',
            'expected_model': 'gpt-4o-mini'
        },
        {
            'name': 'Document Summarization',
            'messages': [
                {'role': 'user', 'content': 'Please summarize this 50-page research paper on climate change impacts. I need the key findings and conclusions in bullet points.'}
            ],
            'expected_task': 'summarization',
            'expected_model': 'gpt-4o-mini'
        },
        {
            'name': 'Language Translation',
            'messages': [
                {'role': 'user', 'content': 'Translate this business email from English to Spanish, maintaining a professional tone: "Dear Mr. Rodriguez, I hope this email finds you well..."'}
            ],
            'expected_task': 'translation',
            'expected_model': 'claude-3-haiku'
        },
        {
            'name': 'Concept Explanation',
            'messages': [
                {'role': 'user', 'content': 'Explain quantum computing to me like I\'m a high school student. What are the key concepts I need to understand?'}
            ],
            'expected_task': 'explanation',
            'expected_model': 'gpt-4o'
        },
        {
            'name': 'Brainstorming Session',
            'messages': [
                {'role': 'user', 'content': 'I need creative ideas for a new mobile app that helps people reduce food waste. Can you brainstorm some innovative features and approaches?'}
            ],
            'expected_task': 'brainstorming',
            'expected_model': 'gpt-4o'
        },
        {
            'name': 'Mixed/Unclear Task',
            'messages': [
                {'role': 'user', 'content': 'Hello, how are you today? What\'s the weather like?'}
            ],
            'expected_task': 'none',
            'expected_model': 'gpt-4o-mini'  # Should fall back to default
        }
    ]
    
    print("🤖 Testing Auto Task Detection Router")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n📝 Testing {test_case['name']}:")
        print(f"   Input: {test_case['messages'][0]['content'][:80]}...")
        
        try:
            # Route the request
            result = await router.route({
                'messages': test_case['messages'],
                'metadata': {'test_case': test_case['name']}
            })
            
            selected_model = result.get('model', 'unknown')
            print(f"   🎯 Selected Model: {selected_model}")
            print(f"   ✅ Expected Model: {test_case['expected_model']}")
            
            if selected_model == test_case['expected_model']:
                print(f"   ✅ PASS - Correct model selected!")
            else:
                print(f"   ❌ FAIL - Expected {test_case['expected_model']}, got {selected_model}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Auto Task Detection Test Complete!")


def demonstrate_rule_configuration():
    """Demonstrate different ways to configure the AutoTaskRule."""
    
    print("\n🔧 Auto Task Rule Configuration Examples")
    print("=" * 50)
    
    # Example 1: Basic configuration with common tasks
    print("\n1️⃣ Basic Configuration (Common Tasks):")
    basic_rule = AutoTaskRule(
        name='basic_auto_task_router',
        task_mappings={
            'writing': 'gpt-4o',
            'coding': 'claude-3-sonnet',
            'analysis': 'gpt-4o-mini'
        },
        default='gpt-4o-mini'
    )
    print(f"   Rule: {basic_rule}")
    
    # Example 2: Extended configuration with more tasks
    print("\n2️⃣ Extended Configuration (More Tasks):")
    extended_rule = AutoTaskRule(
        name='extended_auto_task_router',
        task_mappings={
            'writing': 'gpt-4o',
            'coding': 'claude-3-sonnet',
            'analysis': 'gpt-4o-mini',
            'summarization': 'gpt-4o-mini',
            'translation': 'claude-3-haiku',
            'explanation': 'gpt-4o',
            'brainstorming': 'gpt-4o',
            'research': 'claude-3-sonnet',
            'editing': 'gpt-4o-mini'
        },
        default='gpt-4o-mini',
        llm_model='gpt-4o'  # Use more powerful model for detection
    )
    print(f"   Rule: {extended_rule}")
    print(f"   Detection Model: {extended_rule.llm_model}")
    
    # Example 3: Specialized configuration for specific domains
    print("\n3️⃣ Domain-Specific Configuration:")
    domain_rule = AutoTaskRule(
        name='business_auto_task_router',
        task_mappings={
            'writing': 'gpt-4o',        # Business writing, proposals
            'analysis': 'claude-3-sonnet', # Business analysis, reports
            'summarization': 'gpt-4o-mini', # Meeting summaries, reports
            'translation': 'claude-3-haiku', # International business
        },
        default='gpt-4o-mini'
    )
    print(f"   Rule: {domain_rule}")
    
    # Example 4: Dynamic task management
    print("\n4️⃣ Dynamic Task Management:")
    dynamic_rule = AutoTaskRule(
        name='dynamic_auto_task_router',
        task_mappings={'writing': 'gpt-4o'},
        default='gpt-4o-mini'
    )
    
    # Add tasks dynamically
    dynamic_rule.add_task_mapping('coding', 'claude-3-sonnet')
    dynamic_rule.add_task_mapping('analysis', 'gpt-4o-mini')
    
    print(f"   Initial Rule: AutoTaskRule(name='dynamic_auto_task_router', tasks=['writing'])")
    print(f"   After adding tasks: {dynamic_rule}")
    
    # Remove a task
    dynamic_rule.remove_task_mapping('analysis')
    print(f"   After removing 'analysis': {dynamic_rule}")


def demonstrate_common_task_examples():
    """Show examples of messages for each common task type."""
    
    print("\n📋 Common Task Examples")
    print("=" * 50)
    
    task_examples = {
        'writing': [
            "Write a blog post about the benefits of remote work",
            "Create a compelling product description for our new smartphone",
            "Draft a professional email to decline a meeting invitation",
            "Write a short story about time travel"
        ],
        'coding': [
            "Help me optimize this SQL query for better performance",
            "Debug this JavaScript function that's not working properly",
            "Write a Python script to process CSV files",
            "Review this code and suggest improvements"
        ],
        'analysis': [
            "Analyze these survey results and identify key trends",
            "What insights can you draw from this financial data?",
            "Compare the pros and cons of these three marketing strategies",
            "Evaluate the performance metrics from our last campaign"
        ],
        'summarization': [
            "Summarize this 20-page research paper in 3 paragraphs",
            "Give me the key points from this meeting transcript",
            "Condense this article into bullet points",
            "Create an executive summary of this quarterly report"
        ],
        'translation': [
            "Translate this contract from English to French",
            "Convert this marketing copy to Spanish",
            "Translate these technical specifications to German",
            "Help me translate this customer feedback from Japanese"
        ],
        'explanation': [
            "Explain machine learning concepts to a beginner",
            "How does blockchain technology work?",
            "What is the difference between REST and GraphQL APIs?",
            "Explain quantum physics in simple terms"
        ],
        'brainstorming': [
            "Generate ideas for our next product launch campaign",
            "What are some creative solutions to reduce office energy consumption?",
            "Brainstorm features for a new fitness app",
            "Come up with innovative team building activities"
        ]
    }
    
    for task, examples in task_examples.items():
        print(f"\n🎯 {task.upper()} Examples:")
        for i, example in enumerate(examples, 1):
            print(f"   {i}. \"{example}\"")


if __name__ == '__main__':
    print("🚀 Auto Task Rule Example")
    print("This example demonstrates automatic task detection and routing.")
    print("\nNote: Make sure you have configured your API credentials in secrets.json")
    print("or environment variables before running this example.\n")
    
    # Demonstrate configuration options
    demonstrate_rule_configuration()
    
    # Show common task examples
    demonstrate_common_task_examples()
    
    # Test the routing (commented out by default since it requires API credentials)
    print("\n" + "=" * 60)
    print("To test actual routing, uncomment the following line and ensure")
    print("your API credentials are configured:")
    print("# asyncio.run(test_auto_task_routing())")
    
    # Uncomment the next line to run actual tests (requires API credentials)
    # asyncio.run(test_auto_task_routing())
