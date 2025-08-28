#!/usr/bin/env python3
"""
Example demonstrating CodeLanguageRule functionality for detecting specific programming languages.

The CodeLanguageRule analyzes request content using regex patterns to identify specific programming
languages and route to appropriate models. It includes LLM fallback for languages not covered
by regex patterns.
"""

from deimos_router.rules import CodeLanguageRule
from deimos_router.router import Router, register_router
from deimos_router.chat import ChatCompletions

def demonstrate_language_detection():
    """Demonstrate CodeLanguageRule's language detection capabilities."""
    
    # Create a CodeLanguageRule that routes different languages to specialized models
    language_rule = CodeLanguageRule(
        name="language_detector",
        language_mappings={
            # Regex-detected languages
            "python": "claude-3-5-sonnet",
            "javascript": "gpt-4",
            "java": "gpt-4",
            "cpp": "claude-3-5-sonnet", 
            "c": "claude-3-5-sonnet",
            "csharp": "gpt-4",
            "php": "gpt-3.5-turbo",
            "ruby": "gpt-3.5-turbo",
            "go": "claude-3-5-sonnet",
            "rust": "claude-3-5-sonnet",
            "swift": "gpt-4",
            "kotlin": "gpt-4",
            "sql": "specialized-sql-model",
            "html": "web-dev-model",
            "css": "web-dev-model",
            
            # LLM fallback languages (not covered by regex)
            "scala": "gpt-4",
            "haskell": "claude-3-5-sonnet",
            "erlang": "gpt-3.5-turbo",
            "clojure": "claude-3-5-sonnet",
            "dart": "gpt-4",
        },
        default="gpt-4o-mini",
        llm_model="gpt-4o-mini",
        enable_llm_fallback=True
    )
    
    print("=== CodeLanguageRule Detection Examples ===\n")
    
    # Test cases with different programming languages
    test_cases = [
        {
            "name": "Python Code",
            "content": """
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)
            
            if __name__ == "__main__":
                for i in range(10):
                    print(f"fib({i}) = {fibonacci(i)}")
            """
        },
        {
            "name": "JavaScript Code", 
            "content": """
            const fetchUserData = async (userId) => {
                try {
                    const response = await fetch(`/api/users/${userId}`);
                    const userData = await response.json();
                    return userData;
                } catch (error) {
                    console.error('Error fetching user data:', error);
                    throw error;
                }
            };
            
            fetchUserData(123).then(user => {
                console.log('User:', user.name);
            });
            """
        },
        {
            "name": "Java Code",
            "content": """
            public class Calculator {
                public static void main(String[] args) {
                    Calculator calc = new Calculator();
                    int result = calc.add(5, 3);
                    System.out.println("Result: " + result);
                }
                
                public int add(int a, int b) {
                    return a + b;
                }
            }
            """
        },
        {
            "name": "C++ Code",
            "content": """
            #include <iostream>
            #include <vector>
            using namespace std;
            
            int main() {
                vector<int> numbers = {1, 2, 3, 4, 5};
                
                for (const auto& num : numbers) {
                    cout << num << " ";
                }
                cout << endl;
                
                return 0;
            }
            """
        },
        {
            "name": "Rust Code",
            "content": """
            fn main() {
                let numbers = vec![1, 2, 3, 4, 5];
                
                let sum: i32 = numbers.iter().sum();
                println!("Sum: {}", sum);
                
                match sum {
                    15 => println!("Perfect sum!"),
                    _ => println!("Different sum: {}", sum),
                }
            }
            """
        },
        {
            "name": "Go Code",
            "content": """
            package main
            
            import (
                "fmt"
                "net/http"
            )
            
            func handler(w http.ResponseWriter, r *http.Request) {
                fmt.Fprintf(w, "Hello, World!")
            }
            
            func main() {
                http.HandleFunc("/", handler)
                fmt.Println("Server starting on :8080")
                http.ListenAndServe(":8080", nil)
            }
            """
        },
        {
            "name": "SQL Query",
            "content": """
            SELECT 
                u.name,
                u.email,
                COUNT(o.id) as order_count,
                SUM(o.total) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.created_at >= '2024-01-01'
            GROUP BY u.id, u.name, u.email
            HAVING COUNT(o.id) > 5
            ORDER BY total_spent DESC
            LIMIT 10;
            """
        },
        {
            "name": "HTML Code",
            "content": """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>My Website</title>
            </head>
            <body>
                <div class="container">
                    <h1>Welcome to My Site</h1>
                    <p>This is a sample webpage.</p>
                    <a href="/about" class="btn">Learn More</a>
                </div>
            </body>
            </html>
            """
        },
        {
            "name": "PHP Code",
            "content": """
            <?php
            class UserManager {
                private $db;
                
                public function __construct($database) {
                    $this->db = $database;
                }
                
                public function getUser($id) {
                    $stmt = $this->db->prepare("SELECT * FROM users WHERE id = ?");
                    $stmt->execute([$id]);
                    return $stmt->fetch();
                }
            }
            
            $userManager = new UserManager($pdo);
            $user = $userManager->getUser(123);
            echo "Hello, " . $user['name'];
            ?>
            """
        },
        {
            "name": "Swift Code",
            "content": """
            import Foundation
            import UIKit
            
            class ViewController: UIViewController {
                @IBOutlet weak var nameLabel: UILabel!
                
                override func viewDidLoad() {
                    super.viewDidLoad()
                    setupUI()
                }
                
                func setupUI() {
                    nameLabel.text = "Hello, Swift!"
                    nameLabel.textColor = .systemBlue
                }
                
                @IBAction func buttonTapped(_ sender: UIButton) {
                    print("Button was tapped!")
                }
            }
            """
        },
        {
            "name": "Scala Code (LLM Fallback)",
            "content": """
            object ScalaExample extends App {
              case class Person(name: String, age: Int)
              
              val people = List(
                Person("Alice", 25),
                Person("Bob", 30),
                Person("Charlie", 35)
              )
              
              val adults = people.filter(_.age >= 18)
              val names = adults.map(_.name)
              
              println(s"Adult names: ${names.mkString(", ")}")
            }
            """
        },
        {
            "name": "Mixed Content",
            "content": """
            I'm working on a Python web scraper and need help with this code:
            
            ```python
            import requests
            from bs4 import BeautifulSoup
            
            def scrape_website(url):
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup.find_all('a')
            ```
            
            The function works but I want to add error handling and make it more robust.
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
        decision = language_rule.evaluate(request_data)
        
        print(f"Content preview: {test_case['content'][:100].strip()}...")
        if decision.value:
            print(f"Detected language: {_get_detected_language(language_rule, test_case['content'])}")
            print(f"Routed to: {decision.value}")
        else:
            print("No language detected, using default")
            print(f"Routed to: {language_rule.default}")
        print()

def _get_detected_language(rule, content):
    """Helper function to show which language was detected."""
    detected = rule._detect_language_regex(content)
    if detected:
        return detected
    
    # Check if LLM fallback would be used
    unmapped_languages = [lang for lang in rule.language_mappings.keys() 
                         if lang not in rule.language_patterns]
    if unmapped_languages and rule.enable_llm_fallback:
        return "LLM fallback (would detect from: " + ", ".join(unmapped_languages) + ")"
    
    return "None"

def demonstrate_with_router():
    """Demonstrate CodeLanguageRule integration with Router."""
    
    print("=== CodeLanguageRule with Router Integration ===\n")
    
    # Create language rule
    language_rule = CodeLanguageRule(
        name="smart_language_detector",
        language_mappings={
            "python": "claude-3-5-sonnet",
            "javascript": "gpt-4",
            "java": "gpt-4",
            "sql": "specialized-sql-model",
            "html": "web-dev-model",
            "css": "web-dev-model",
            # LLM fallback languages
            "scala": "gpt-4",
            "haskell": "claude-3-5-sonnet",
        },
        default="gpt-4o-mini"
    )
    
    # Create router with the language rule
    router = Router(
        name="language_router",
        models=["claude-3-5-sonnet", "gpt-4", "gpt-4o-mini", "specialized-sql-model", "web-dev-model"],
        rules=[language_rule]
    )
    
    # Router is automatically registered when created
    
    test_requests = [
        {
            "name": "Python Request",
            "messages": [
                {
                    "role": "user",
                    "content": "Help me optimize this Python function:\n\ndef slow_function(data):\n    result = []\n    for item in data:\n        if item > 0:\n            result.append(item * 2)\n    return result"
                }
            ]
        },
        {
            "name": "JavaScript Request",
            "messages": [
                {
                    "role": "user",
                    "content": "Review this JavaScript code:\n\nconst processData = (data) => {\n    return data.filter(x => x > 0).map(x => x * 2);\n};"
                }
            ]
        },
        {
            "name": "SQL Request",
            "messages": [
                {
                    "role": "user",
                    "content": "Optimize this SQL query:\n\nSELECT * FROM users WHERE age > 18 AND status = 'active' ORDER BY created_at DESC;"
                }
            ]
        }
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"{i}. {request['name']}")
        print("-" * (len(request['name']) + 3))
        
        # Simulate model selection
        selected_model = router.select_model(request)
        print(f"Selected model: {selected_model}")
        
        # Show which rule was triggered
        for rule in router.rules:
            decision = rule.evaluate(request)
            if decision.value:
                print(f"Rule triggered: {rule.__class__.__name__}")
                break
        else:
            print("No rules triggered, using random selection")
        
        print()

def demonstrate_rule_chaining():
    """Demonstrate CodeLanguageRule in combination with other rules."""
    
    print("\n=== CodeLanguageRule Chaining with TaskRule ===\n")
    
    from deimos_router.rules import TaskRule
    
    # Create a task rule for urgent requests
    urgent_rule = TaskRule("urgent_handler", {
        "urgent": "claude-3-5-sonnet",  # Always use best model for urgent tasks
        "debug": "claude-3-5-sonnet"
    })
    
    # Create language rule for non-urgent requests
    language_rule = CodeLanguageRule(
        name="language_detector",
        language_mappings={
            "python": "claude-3-5-sonnet",
            "javascript": "gpt-4",
            "sql": "specialized-sql-model",
            "html": "web-dev-model"
        },
        default="gpt-4o-mini"
    )
    
    # Create router with rule priority: urgent_rule first, then language_rule
    router = Router(
        name="chained_router",
        models=["claude-3-5-sonnet", "gpt-4", "gpt-4o-mini", "specialized-sql-model", "web-dev-model"],
        rules=[urgent_rule, language_rule]  # Order matters - urgent_rule has higher priority
    )
    
    test_cases = [
        {
            "name": "Urgent Python Task",
            "messages": [
                {
                    "role": "user",
                    "content": "URGENT: Fix this broken Python code:\n\ndef broken_func():\n    return x + y  # x and y are undefined"
                }
            ],
            "task": "urgent"
        },
        {
            "name": "Regular Python Task",
            "messages": [
                {
                    "role": "user",
                    "content": "Help me write a Python function to calculate factorial:\n\ndef factorial(n):\n    # TODO: implement"
                }
            ]
        },
        {
            "name": "Debug JavaScript Task",
            "messages": [
                {
                    "role": "user",
                    "content": "Debug this JavaScript:\n\nfunction buggyFunction() {\n    console.log(undefinedVariable);\n}"
                }
            ],
            "task": "debug"
        },
        {
            "name": "Regular SQL Task",
            "messages": [
                {
                    "role": "user",
                    "content": "Write a SQL query to find top customers:\n\nSELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id"
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
        
        # Show which rule was triggered
        for rule in router.rules:
            decision = rule.evaluate(request_data)
            if decision.value:
                print(f"Rule triggered: {rule.__class__.__name__} -> {decision.value}")
                break
        else:
            print("No rules triggered, using random selection")
        
        print()

def demonstrate_llm_fallback():
    """Demonstrate LLM fallback for languages not covered by regex."""
    
    print("\n=== LLM Fallback Detection Demo ===\n")
    
    # Create rule with some regex languages and some LLM-only languages
    language_rule = CodeLanguageRule(
        name="hybrid_detector",
        language_mappings={
            # Regex-covered languages
            "python": "claude-3-5-sonnet",
            "javascript": "gpt-4",
            
            # LLM-only languages (not in regex patterns)
            "scala": "gpt-4",
            "haskell": "claude-3-5-sonnet",
            "erlang": "gpt-3.5-turbo",
            "clojure": "claude-3-5-sonnet",
            "dart": "gpt-4",
        },
        default="gpt-4o-mini",
        enable_llm_fallback=True
    )
    
    print("Languages with regex patterns:", [lang for lang in language_rule.language_mappings.keys() 
                                           if lang in language_rule.language_patterns])
    print("Languages requiring LLM fallback:", [lang for lang in language_rule.language_mappings.keys() 
                                               if lang not in language_rule.language_patterns])
    print()
    
    # Test cases that would require LLM fallback
    llm_test_cases = [
        {
            "name": "Scala Code (LLM Detection)",
            "content": """
            case class User(name: String, age: Int)
            
            object UserService {
              def findAdults(users: List[User]): List[User] = {
                users.filter(_.age >= 18)
              }
              
              def main(args: Array[String]): Unit = {
                val users = List(User("Alice", 25), User("Bob", 17))
                val adults = findAdults(users)
                println(s"Adults: ${adults.map(_.name).mkString(", ")}")
              }
            }
            """
        },
        {
            "name": "Haskell Code (LLM Detection)",
            "content": """
            factorial :: Integer -> Integer
            factorial 0 = 1
            factorial n = n * factorial (n - 1)
            
            main :: IO ()
            main = do
              putStrLn "Enter a number:"
              input <- getLine
              let n = read input :: Integer
              putStrLn $ "Factorial of " ++ show n ++ " is " ++ show (factorial n)
            """
        }
    ]
    
    for i, test_case in enumerate(llm_test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("-" * (len(test_case['name']) + 3))
        
        request_data = {
            "messages": [
                {"role": "user", "content": test_case['content']}
            ]
        }
        
        print(f"Content preview: {test_case['content'][:100].strip()}...")
        
        # First try regex detection
        regex_result = language_rule._detect_language_regex(test_case['content'])
        print(f"Regex detection result: {regex_result or 'None'}")
        
        # Show that LLM fallback would be used
        unmapped_languages = [lang for lang in language_rule.language_mappings.keys() 
                             if lang not in language_rule.language_patterns]
        if not regex_result and unmapped_languages:
            print(f"Would use LLM fallback with candidates: {unmapped_languages}")
            print("Note: LLM detection requires valid API credentials")
        
        # Evaluate the rule (this would use LLM if credentials are available)
        decision = language_rule.evaluate(request_data)
        print(f"Final routing decision: {decision.value or language_rule.default}")
        print()

if __name__ == "__main__":
    demonstrate_language_detection()
    demonstrate_with_router()
    demonstrate_rule_chaining()
    demonstrate_llm_fallback()
