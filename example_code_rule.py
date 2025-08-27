#!/usr/bin/env python3
"""
Example demonstrating CodeRule functionality for detecting code in requests.

The CodeRule analyzes request content using regex patterns to determine if it contains
code with high accuracy. It can detect Python, JavaScript, SQL, HTML, shell commands,
error messages, and more.
"""

from deimos_router.rules import CodeRule
from deimos_router.chat import ChatCompletions

def demonstrate_code_detection():
    """Demonstrate CodeRule's code detection capabilities."""
    
    # Create a CodeRule that routes code requests to 'claude-3-5-sonnet' 
    # and non-code requests to 'gpt-4'
    code_rule = CodeRule(
        name="code_detector",
        code="claude-3-5-sonnet",
        not_code="gpt-4"
    )
    
    print("=== CodeRule Detection Examples ===\n")
    
    # Test cases with different types of content
    test_cases = [
        {
            "name": "Python Code",
            "content": """
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)
            
            print(fibonacci(10))
            """
        },
        {
            "name": "JavaScript Code", 
            "content": """
            const users = await fetch('/api/users')
                .then(response => response.json())
                .catch(error => console.error('Error:', error));
            
            users.forEach(user => {
                document.getElementById('user-list').innerHTML += `<li>${user.name}</li>`;
            });
            """
        },
        {
            "name": "SQL Query",
            "content": """
            SELECT u.name, u.email, COUNT(o.id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.created_at >= '2024-01-01'
            GROUP BY u.id, u.name, u.email
            HAVING COUNT(o.id) > 5
            ORDER BY order_count DESC;
            """
        },
        {
            "name": "HTML/CSS Code",
            "content": """
            <div class="container">
                <h1>Welcome to My Site</h1>
                <style>
                    .container { max-width: 800px; margin: 0 auto; }
                    h1 { color: #333; font-family: Arial, sans-serif; }
                </style>
            </div>
            """
        },
        {
            "name": "Shell Commands",
            "content": """
            # Install dependencies
            pip install -r requirements.txt
            
            # Run the application
            python app.py --port 8000 --debug
            
            # Check logs
            tail -f /var/log/app.log | grep ERROR
            """
        },
        {
            "name": "Error Message",
            "content": """
            Traceback (most recent call last):
              File "app.py", line 42, in process_data
                result = data['key']
            KeyError: 'key'
            
            The above exception was the direct cause of the following exception:
            ValueError: Required key 'key' not found in data
            """
        },
        {
            "name": "Natural Language",
            "content": """
            I'm having trouble understanding how to implement a binary search algorithm.
            Could you explain the concept and walk me through the steps? I know it's
            more efficient than linear search, but I'm not sure about the implementation
            details. What are the key things to remember?
            """
        },
        {
            "name": "Mixed Content",
            "content": """
            Here's how you can implement a simple web scraper in Python:
            
            ```python
            import requests
            from bs4 import BeautifulSoup
            
            def scrape_website(url):
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup.find_all('a')
            ```
            
            This function fetches a webpage and extracts all the links. Make sure
            to install the required packages first using pip install requests beautifulsoup4.
            """
        }
    ]
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("-" * (len(test_case['name']) + 3))
        
        # Create a mock request data structure
        request_data = {
            "messages": [
                {"role": "user", "content": test_case['content']}
            ]
        }
        
        # Evaluate the rule
        decision = code_rule.evaluate(request_data)
        
        print(f"Content preview: {test_case['content'][:100].strip()}...")
        print(f"Detected as: {'CODE' if decision.value == 'claude-3-5-sonnet' else 'NOT CODE'}")
        print(f"Routed to: {decision.value}")
        print()

def demonstrate_with_chat_completions():
    """Demonstrate CodeRule integration with ChatCompletions."""
    
    print("=== CodeRule with ChatCompletions Integration ===\n")
    
    # Create a router with CodeRule and register it
    from deimos_router.router import Router, register_router
    
    router = Router(
        name="code_router",
        models=["gpt-4", "claude-3-5-sonnet"],
        rules=[
            CodeRule(name="code_detector", code="claude-3-5-sonnet", not_code="gpt-4")
        ]
    )
    
    # Register the router so ChatCompletions can find it
    register_router(router)
    
    # Create ChatCompletions instance
    chat = ChatCompletions()
    
    # Test with code request
    print("1. Code Request (should route to claude-3-5-sonnet)")
    print("-" * 50)
    
    try:
        response = chat.create(
            messages=[
                {
                    "role": "user", 
                    "content": "Fix this Python function:\n\ndef broken_func(lst):\n    for i in range(len(lst)):\n        if lst[i] = 5:\n            return i"
                }
            ],
            model="deimos/code_router",  # Use the router via deimos/ prefix
            max_tokens=100
        )
        print(f"Routed to: {getattr(response, '_deimos_metadata', {}).get('selected_model', 'Unknown')}")
        print(f"Router used: {getattr(response, '_deimos_metadata', {}).get('router_used', 'None')}")
    except Exception as e:
        print(f"Note: {e} (This is expected without actual API credentials)")
    
    print()
    
    # Test with natural language request
    print("2. Natural Language Request (should route to gpt-4)")
    print("-" * 50)
    
    try:
        response = chat.create(
            messages=[
                {
                    "role": "user",
                    "content": "What are the benefits of using renewable energy sources? Please explain in simple terms."
                }
            ],
            model="deimos/code_router",  # Use the router via deimos/ prefix
            max_tokens=100
        )
        print(f"Routed to: {getattr(response, '_deimos_metadata', {}).get('selected_model', 'Unknown')}")
        print(f"Router used: {getattr(response, '_deimos_metadata', {}).get('router_used', 'None')}")
    except Exception as e:
        print(f"Note: {e} (This is expected without actual API credentials)")

def demonstrate_rule_chaining():
    """Demonstrate CodeRule in combination with other rules."""
    
    print("\n=== CodeRule Chaining with TaskRule ===\n")
    
    from deimos_router.rules import TaskRule
    from deimos_router.router import Router
    
    # Create a complex rule chain:
    # 1. If task is "debug", use claude-3-5-sonnet regardless of content
    # 2. Otherwise, use CodeRule to decide between models
    
    debug_rule = TaskRule(name="debug_task", triggers={"debug": "claude-3-5-sonnet"})
    code_rule = CodeRule(name="code_detector", code="claude-3-5-sonnet", not_code="gpt-4")
    
    router = Router(
        name="chained_router",
        models=["gpt-4", "claude-3-5-sonnet"],
        rules=[debug_rule, code_rule]  # debug_rule has higher priority
    )
    
    test_cases = [
        {
            "name": "Debug Task with Code",
            "messages": [
                {
                    "role": "system",
                    "content": "You are helping debug code issues."
                },
                {
                    "role": "user", 
                    "content": "This function isn't working:\n\ndef add(a, b):\n    return a + b"
                }
            ],
            "task": "debug"
        },
        {
            "name": "Code without Debug Task",
            "messages": [
                {
                    "role": "user",
                    "content": "Write a function to calculate factorial:\n\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)"
                }
            ]
        },
        {
            "name": "Natural Language without Debug Task", 
            "messages": [
                {
                    "role": "user",
                    "content": "Explain the concept of recursion in programming."
                }
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("-" * (len(test_case['name']) + 3))
        
        request_data = {
            "messages": test_case["messages"],
            "max_tokens": 100
        }
        
        if "task" in test_case:
            request_data["task"] = test_case["task"]
        
        # Simulate routing decision
        selected_model = router.select_model(request_data)
        print(f"Selected model: {selected_model}")
        
        # Show which rule would have been triggered
        for rule in router.rules:
            decision = rule.evaluate(request_data)
            if decision.value:
                print(f"Rule triggered: {rule.__class__.__name__} -> {decision.value}")
                break
        else:
            print("No rules triggered, using random selection")
        
        print()

if __name__ == "__main__":
    demonstrate_code_detection()
    demonstrate_with_chat_completions()
    demonstrate_rule_chaining()
