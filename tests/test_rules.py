"""Tests for the rule-based model selection system."""

import pytest
from unittest.mock import Mock

from deimos_router.rules import (
    Rule, Decision, TaskRule, CodeRule, CodeLanguageRule,
    register_rule, get_rule, list_rules, clear_rules
)
from deimos_router.router import Router, register_router, clear_routers
from deimos_router import chat


class TestDecision:
    """Test cases for the Decision class."""
    
    def test_model_decision(self):
        """Test decision with a model."""
        decision = Decision("gpt-3.5-turbo")
        
        assert decision.is_model()
        assert not decision.is_rule()
        assert not decision.is_none()
        assert decision.get_model() == "gpt-3.5-turbo"
        assert decision.get_rule() is None
        assert str(decision) == "Decision(model='gpt-3.5-turbo', trigger='None')"
    
    def test_rule_decision(self):
        """Test decision with another rule."""
        rule = TaskRule("test-rule", {})
        decision = Decision(rule)
        
        assert not decision.is_model()
        assert decision.is_rule()
        assert not decision.is_none()
        assert decision.get_model() is None
        assert decision.get_rule() is rule
        assert str(decision) == "Decision(rule=test-rule, trigger='None')"
    
    def test_none_decision(self):
        """Test decision with None."""
        decision = Decision(None)
        
        assert not decision.is_model()
        assert not decision.is_rule()
        assert decision.is_none()
        assert decision.get_model() is None
        assert decision.get_rule() is None
        assert str(decision) == "Decision(None, trigger='None')"


class TestTaskRule:
    """Test cases for the TaskRule class."""
    
    def setup_method(self):
        """Setup for each test."""
        clear_rules()
    
    def test_task_rule_initialization(self):
        """Test TaskRule initialization."""
        triggers = {
            "code": "anthropic/claude-sonnet-4",
            "medical": "openai/gpt-5"
        }
        task_rule = TaskRule("task-decider", triggers)
        
        assert task_rule.name == "task-decider"
        assert task_rule.triggers == triggers
        assert str(task_rule) == "TaskRule(name='task-decider', triggers=['code', 'medical'])"
    
    def test_task_rule_evaluate_with_matching_task(self):
        """Test TaskRule evaluation with matching task."""
        triggers = {
            "code": "anthropic/claude-sonnet-4",
            "medical": "openai/gpt-5"
        }
        task_rule = TaskRule("task-decider", triggers)
        
        request_data = {
            "messages": [{"role": "user", "content": "Help me code"}],
            "task": "code"
        }
        
        decision = task_rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == "anthropic/claude-sonnet-4"
    
    def test_task_rule_evaluate_with_no_task(self):
        """Test TaskRule evaluation when no task is provided."""
        triggers = {"code": "anthropic/claude-sonnet-4"}
        task_rule = TaskRule("task-decider", triggers)
        
        request_data = {
            "messages": [{"role": "user", "content": "Help me"}]
            # No task field
        }
        
        decision = task_rule.evaluate(request_data)
        assert decision.is_none()
    
    def test_task_rule_evaluate_with_unknown_task(self):
        """Test TaskRule evaluation with unknown task."""
        triggers = {"code": "anthropic/claude-sonnet-4"}
        task_rule = TaskRule("task-decider", triggers)
        
        request_data = {
            "messages": [{"role": "user", "content": "Help me"}],
            "task": "unknown-task"
        }
        
        decision = task_rule.evaluate(request_data)
        assert decision.is_none()
    
    def test_task_rule_with_rule_reference(self):
        """Test TaskRule that references another rule."""
        # Create a nested rule
        nested_rule = TaskRule("advice-decider", {
            "personal": "openai/gpt-3.5-turbo",
            "professional": "anthropic/claude-sonnet-4"
        })
        
        # Create main rule that references the nested rule
        main_rule = TaskRule("task-decider", {
            "code": "anthropic/claude-sonnet-4",
            "advice": nested_rule
        })
        
        request_data = {
            "messages": [{"role": "user", "content": "Give me advice"}],
            "task": "advice"
        }
        
        decision = main_rule.evaluate(request_data)
        assert decision.is_rule()
        assert decision.get_rule() is nested_rule
    
    def test_add_and_remove_task_rules(self):
        """Test adding and removing task rules."""
        task_rule = TaskRule("test-rule", {"initial": "gpt-3.5-turbo"})
        
        # Add a new rule
        task_rule.add_task_rule("new-task", "gpt-4")
        assert "new-task" in task_rule.triggers
        assert task_rule.triggers["new-task"] == "gpt-4"
        
        # Remove a rule
        task_rule.remove_task_rule("initial")
        assert "initial" not in task_rule.triggers
        
        # Remove non-existent rule (should not raise error)
        task_rule.remove_task_rule("non-existent")


class TestCodeRule:
    """Test cases for the CodeRule class."""
    
    def setup_method(self):
        """Setup for each test."""
        clear_rules()
    
    def test_code_rule_initialization(self):
        """Test CodeRule initialization."""
        code_rule = CodeRule(
            name="code-detector",
            code="anthropic/claude-sonnet-4",
            not_code="gpt-3.5-turbo"
        )
        
        assert code_rule.name == "code-detector"
        assert code_rule.code == "anthropic/claude-sonnet-4"
        assert code_rule.not_code == "gpt-3.5-turbo"
        assert str(code_rule) == "CodeRule(name='code-detector', code=anthropic/claude-sonnet-4, not_code=gpt-3.5-turbo)"
    
    def test_code_rule_detects_python_code(self):
        """Test CodeRule detection of Python code."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        python_code_examples = [
            {
                "messages": [{"role": "user", "content": "def hello_world():\n    print('Hello, World!')"}]
            },
            {
                "messages": [{"role": "user", "content": "for i in range(10):\n    if i % 2 == 0:\n        print(i)"}]
            },
            {
                "messages": [{"role": "user", "content": "import numpy as np\nfrom sklearn import datasets"}]
            },
            {
                "messages": [{"role": "user", "content": "class MyClass:\n    def __init__(self):\n        self.value = 42"}]
            },
            {
                "messages": [{"role": "user", "content": "try:\n    result = divide(10, 0)\nexcept ZeroDivisionError:\n    print('Cannot divide by zero')"}]
            }
        ]
        
        for request_data in python_code_examples:
            decision = code_rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "code-model"
    
    def test_code_rule_detects_javascript_code(self):
        """Test CodeRule detection of JavaScript code."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        javascript_examples = [
            {
                "messages": [{"role": "user", "content": "function greet(name) {\n    console.log('Hello, ' + name);\n}"}]
            },
            {
                "messages": [{"role": "user", "content": "const arr = [1, 2, 3, 4, 5];\nconst doubled = arr.map(x => x * 2);"}]
            },
            {
                "messages": [{"role": "user", "content": "if (condition) {\n    doSomething();\n} else {\n    doSomethingElse();\n}"}]
            },
            {
                "messages": [{"role": "user", "content": "async function fetchData() {\n    const response = await fetch('/api/data');\n    return response.json();\n}"}]
            }
        ]
        
        for request_data in javascript_examples:
            decision = code_rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "code-model"
    
    def test_code_rule_detects_sql_code(self):
        """Test CodeRule detection of SQL code."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        sql_examples = [
            {
                "messages": [{"role": "user", "content": "SELECT * FROM users WHERE age > 18 ORDER BY name"}]
            },
            {
                "messages": [{"role": "user", "content": "INSERT INTO products (name, price) VALUES ('Widget', 19.99)"}]
            },
            {
                "messages": [{"role": "user", "content": "UPDATE customers SET email = 'new@email.com' WHERE id = 123"}]
            },
            {
                "messages": [{"role": "user", "content": "CREATE TABLE orders (\n    id INT PRIMARY KEY,\n    customer_id INT,\n    total DECIMAL(10,2)\n)"}]
            }
        ]
        
        for request_data in sql_examples:
            decision = code_rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "code-model"
    
    def test_code_rule_detects_html_code(self):
        """Test CodeRule detection of HTML code."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        html_examples = [
            {
                "messages": [{"role": "user", "content": "<div class='container'>\n    <h1>Welcome</h1>\n    <p>Hello world!</p>\n</div>"}]
            },
            {
                "messages": [{"role": "user", "content": "<form action='/submit' method='post'>\n    <input type='text' name='username' />\n    <button type='submit'>Submit</button>\n</form>"}]
            },
            {
                "messages": [{"role": "user", "content": "<img src='image.jpg' alt='Description' />"}]
            }
        ]
        
        for request_data in html_examples:
            decision = code_rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "code-model"
    
    def test_code_rule_detects_shell_commands(self):
        """Test CodeRule detection of shell commands."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        shell_examples = [
            {
                "messages": [{"role": "user", "content": "$ ls -la /home/user\n$ cd /var/log\n$ grep 'error' *.log"}]
            },
            {
                "messages": [{"role": "user", "content": "git clone https://github.com/user/repo.git\ngit checkout -b feature-branch"}]
            },
            {
                "messages": [{"role": "user", "content": "npm install express\nnpm start"}]
            },
            {
                "messages": [{"role": "user", "content": "docker build -t myapp .\ndocker run -p 3000:3000 myapp"}]
            }
        ]
        
        for request_data in shell_examples:
            decision = code_rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "code-model"
    
    def test_code_rule_detects_error_messages(self):
        """Test CodeRule detection of error messages and stack traces."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        error_examples = [
            {
                "messages": [{"role": "user", "content": "Traceback (most recent call last):\n  File 'main.py', line 10, in <module>\n    result = divide(10, 0)\nZeroDivisionError: division by zero"}]
            },
            {
                "messages": [{"role": "user", "content": "Error: Cannot read property 'length' of undefined\n    at Object.getLength (utils.js:15:20)\n    at main.js:42:15"}]
            },
            {
                "messages": [{"role": "user", "content": "java.lang.NullPointerException\n\tat com.example.MyClass.method(MyClass.java:25)"}]
            }
        ]
        
        for request_data in error_examples:
            decision = code_rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "code-model"
    
    def test_code_rule_rejects_natural_language(self):
        """Test CodeRule correctly identifies natural language as not code."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        natural_language_examples = [
            {
                "messages": [{"role": "user", "content": "Hello, how are you today? I hope you're doing well."}]
            },
            {
                "messages": [{"role": "user", "content": "Can you please explain the concept of machine learning to me?"}]
            },
            {
                "messages": [{"role": "user", "content": "What is the weather like in New York? I'm planning a trip there next week."}]
            },
            {
                "messages": [{"role": "user", "content": "I need help with my homework. The assignment is about World War II history."}]
            },
            {
                "messages": [{"role": "user", "content": "Thank you for your assistance. This has been very helpful and informative."}]
            },
            {
                "messages": [{"role": "user", "content": "Could you recommend some good books about philosophy? I'm particularly interested in ethics."}]
            }
        ]
        
        for request_data in natural_language_examples:
            decision = code_rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "text-model"
    
    def test_code_rule_handles_mixed_content(self):
        """Test CodeRule with mixed code and natural language content."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        # Content with significant code should be detected as code
        mixed_code_heavy = {
            "messages": [{"role": "user", "content": "I'm having trouble with this Python function:\n\ndef calculate_average(numbers):\n    if len(numbers) == 0:\n        return 0\n    return sum(numbers) / len(numbers)\n\nCan you help me optimize it?"}]
        }
        
        decision = code_rule.evaluate(mixed_code_heavy)
        assert decision.is_model()
        assert decision.get_model() == "code-model"
        
        # Content with minimal code mentions should be detected as natural language
        mixed_text_heavy = {
            "messages": [{"role": "user", "content": "I'm learning about programming and I heard that Python is a good language to start with. What do you think about that? Should I also learn JavaScript or focus on Python first?"}]
        }
        
        decision = code_rule.evaluate(mixed_text_heavy)
        assert decision.is_model()
        assert decision.get_model() == "text-model"
    
    def test_code_rule_handles_empty_content(self):
        """Test CodeRule with empty or missing content."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        empty_examples = [
            {"messages": []},
            {"messages": [{"role": "user", "content": ""}]},
            {"messages": [{"role": "user"}]},  # Missing content
            {}  # No messages
        ]
        
        for request_data in empty_examples:
            decision = code_rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "text-model"
    
    def test_code_rule_with_multiple_messages(self):
        """Test CodeRule with multiple messages in conversation."""
        code_rule = CodeRule("code-detector", "code-model", "text-model")
        
        # Multiple messages with code
        code_conversation = {
            "messages": [
                {"role": "user", "content": "I need help with this function"},
                {"role": "assistant", "content": "Sure, I can help. What's the issue?"},
                {"role": "user", "content": "def broken_function(x):\n    return x / 0\n\nThis keeps throwing an error"}
            ]
        }
        
        decision = code_rule.evaluate(code_conversation)
        assert decision.is_model()
        assert decision.get_model() == "code-model"
        
        # Multiple messages without code
        text_conversation = {
            "messages": [
                {"role": "user", "content": "Hello, I have a question about cooking"},
                {"role": "assistant", "content": "I'd be happy to help with cooking questions!"},
                {"role": "user", "content": "What's the best way to make pasta? I'm a beginner cook."}
            ]
        }
        
        decision = code_rule.evaluate(text_conversation)
        assert decision.is_model()
        assert decision.get_model() == "text-model"
    
    def test_code_rule_with_rule_references(self):
        """Test CodeRule that references other rules."""
        # Create nested rules
        python_rule = TaskRule("python-specialist", {"optimization": "gpt-4", "debugging": "anthropic/claude-sonnet-4"})
        general_rule = TaskRule("general-code", {"review": "gpt-3.5-turbo", "explanation": "gpt-3.5-turbo"})
        
        code_rule = CodeRule(
            name="smart-code-detector",
            code=python_rule,  # Reference to another rule
            not_code="gpt-3.5-turbo"
        )
        
        request_data = {
            "messages": [{"role": "user", "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"}]
        }
        
        decision = code_rule.evaluate(request_data)
        assert decision.is_rule()
        assert decision.get_rule() is python_rule


class TestRuleRegistry:
    """Test cases for the rule registry functions."""
    
    def setup_method(self):
        """Setup for each test."""
        clear_rules()
    
    def test_register_and_get_rule(self):
        """Test registering and retrieving a rule."""
        rule = TaskRule("test-rule", {"code": "gpt-4"})
        register_rule(rule)
        
        retrieved = get_rule("test-rule")
        assert retrieved is rule
        assert retrieved.name == "test-rule"
    
    def test_get_nonexistent_rule(self):
        """Test getting a rule that doesn't exist."""
        result = get_rule("nonexistent")
        assert result is None
    
    def test_list_rules_empty(self):
        """Test listing rules when registry is empty."""
        rules = list_rules()
        assert rules == []
    
    def test_list_rules_with_rules(self):
        """Test listing rules when registry has rules."""
        rule1 = TaskRule("rule-1", {"task1": "model1"})
        rule2 = TaskRule("rule-2", {"task2": "model2"})
        
        register_rule(rule1)
        register_rule(rule2)
        
        rules = list_rules()
        assert set(rules) == {"rule-1", "rule-2"}
    
    def test_clear_rules(self):
        """Test clearing the rule registry."""
        rule = TaskRule("test-rule", {"task": "model"})
        register_rule(rule)
        
        assert len(list_rules()) == 1
        
        clear_rules()
        assert len(list_rules()) == 0
        assert get_rule("test-rule") is None


class TestRouterWithRules:
    """Test cases for Router using the rule system."""
    
    def setup_method(self):
        """Setup for each test."""
        clear_rules()
        clear_routers()
    
    def test_router_with_task_rule(self):
        """Test router using a TaskRule."""
        # Create and register a task rule
        task_rule = TaskRule("task-decider", {
            "code": "anthropic/claude-sonnet-4",
            "medical": "openai/gpt-5",
            "general": "gpt-3.5-turbo"
        })
        register_rule(task_rule)
        
        # Create router that uses the rule
        router = Router(
            name="my-router",
            rules=["task-decider"],
            default="gpt-4o-mini"
        )
        
        # Test code task
        request_data = {"task": "code", "messages": []}
        selected = router.select_model(request_data)
        assert selected == "anthropic/claude-sonnet-4"
        
        # Test medical task
        request_data = {"task": "medical", "messages": []}
        selected = router.select_model(request_data)
        assert selected == "openai/gpt-5"
        
        # Test unknown task (should use default)
        request_data = {"task": "unknown", "messages": []}
        selected = router.select_model(request_data)
        assert selected == "gpt-4o-mini"
        
        # Test no task (should use default)
        request_data = {"messages": []}
        selected = router.select_model(request_data)
        assert selected == "gpt-4o-mini"
    
    def test_router_with_multiple_rules(self):
        """Test router with multiple rules in priority order."""
        # Create first rule (higher priority)
        rule1 = TaskRule("priority-rule", {"urgent": "gpt-4"})
        register_rule(rule1)
        
        # Create second rule (lower priority)
        rule2 = TaskRule("general-rule", {"code": "gpt-3.5-turbo"})
        register_rule(rule2)
        
        router = Router(
            name="multi-rule-router",
            rules=["priority-rule", "general-rule"],
            default="gpt-4o-mini"
        )
        
        # Test urgent task (matches first rule)
        request_data = {"task": "urgent", "messages": []}
        selected = router.select_model(request_data)
        assert selected == "gpt-4"
        
        # Test code task (matches second rule)
        request_data = {"task": "code", "messages": []}
        selected = router.select_model(request_data)
        assert selected == "gpt-3.5-turbo"
        
        # Test unknown task (uses default)
        request_data = {"task": "unknown", "messages": []}
        selected = router.select_model(request_data)
        assert selected == "gpt-4o-mini"
    
    def test_router_with_rule_chain(self):
        """Test router with chained rules."""
        # Create nested rule
        advice_rule = TaskRule("advice-decider", {
            "personal": "gpt-3.5-turbo",
            "professional": "gpt-4"
        })
        register_rule(advice_rule)
        
        # Create main rule that references nested rule
        main_rule = TaskRule("task-decider", {
            "code": "anthropic/claude-sonnet-4",
            "advice": advice_rule
        })
        register_rule(main_rule)
        
        router = Router(
            name="chain-router",
            rules=["task-decider"],
            default="gpt-4o-mini"
        )
        
        # Test chained rule resolution
        request_data = {
            "task": "advice",
            "advice_type": "personal",  # This would need to be handled by advice_rule
            "messages": []
        }
        
        # For this test, we need to modify the advice rule to look for advice_type
        advice_rule.triggers["personal"] = "gpt-3.5-turbo"  # Direct model for testing
        
        # The chain should resolve: task-decider -> advice-decider -> model
        # But since advice-decider doesn't know about advice_type, it will return None
        # and the router will use default
        selected = router.select_model(request_data)
        assert selected == "gpt-4o-mini"  # Falls back to default
    
    def test_router_backward_compatibility(self):
        """Test that router still works with old models parameter."""
        router = Router(
            name="legacy-router",
            models=["gpt-3.5-turbo", "gpt-4"]
        )
        
        # Should still work with random selection
        selected = router.select_model()
        assert selected in ["gpt-3.5-turbo", "gpt-4"]
    
    def test_router_with_direct_rule_objects(self):
        """Test router with direct rule objects instead of rule names."""
        task_rule = TaskRule("direct-rule", {
            "test": "gpt-4"
        })
        
        router = Router(
            name="direct-router",
            rules=[task_rule],  # Direct rule object, not registered
            default="gpt-3.5-turbo"
        )
        
        request_data = {"task": "test", "messages": []}
        selected = router.select_model(request_data)
        assert selected == "gpt-4"


class TestIntegrationWithChat:
    """Integration tests with the chat completions API."""
    
    def setup_method(self):
        """Setup for each test."""
        clear_rules()
        clear_routers()
        chat.completions._client = None
    
    def test_chat_with_task_routing(self):
        """Test chat completions with task-based routing."""
        # Create and register task rule
        task_rule = TaskRule("task-router", {
            "code": "gpt-4",
            "writing": "gpt-3.5-turbo"
        })
        register_rule(task_rule)
        
        # Create and register router
        router = Router(
            name="test-router",
            rules=["task-router"],
            default="gpt-4o-mini"
        )
        register_router(router)
        
        # Mock the OpenAI client to avoid actual API calls
        from unittest.mock import patch, Mock
        
        with patch('deimos_router.chat.config') as mock_config:
            with patch('deimos_router.chat.openai.OpenAI') as mock_openai:
                mock_config.get_credentials.return_value = {
                    'api_key': 'test-key',
                    'api_url': 'https://test-api.com'
                }
                
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                mock_response = Mock()
                mock_response.model = 'gpt-4'
                mock_response._deimos_metadata = {}
                # Ensure cost attribute is None to avoid float conversion issues
                mock_response.cost = None
                # Mock usage for cost calculation
                mock_usage = Mock()
                mock_usage.prompt_tokens = 10
                mock_usage.completion_tokens = 5
                mock_usage.total_tokens = 15
                mock_response.usage = mock_usage
                # Make choices iterable for logging system
                mock_choice = Mock()
                mock_choice.message = Mock()
                mock_choice.message.content = "Test response"
                mock_choice.message.role = "assistant"
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                
                # Make a request with task parameter
                messages = [{"role": "user", "content": "Help me write code"}]
                
                response = chat.completions.create(
                    messages=messages,
                    model="deimos/test-router",
                    task="code",  # This should route to gpt-4
                    temperature=0.7
                )
                
                # Verify the correct model was called
                mock_client.chat.completions.create.assert_called_once_with(
                    messages=messages,
                    model="gpt-4",  # Should have selected gpt-4 based on task
                    temperature=0.7
                )
                
                # Verify routing metadata
                assert hasattr(response, '_deimos_metadata')
                metadata = response._deimos_metadata
                assert metadata['router_used'] == 'test-router'
                assert metadata['selected_model'] == 'gpt-4'


class TestCodeLanguageRule:
    """Test cases for the CodeLanguageRule class."""
    
    def setup_method(self):
        """Setup for each test."""
        clear_rules()
    
    def test_code_language_rule_initialization(self):
        """Test CodeLanguageRule initialization."""
        language_mappings = {
            "python": "claude-3-5-sonnet",
            "javascript": "gpt-4",
            "sql": "specialized-sql-model"
        }
        
        rule = CodeLanguageRule(
            name="language-detector",
            language_mappings=language_mappings,
            default="gpt-4o-mini",
            llm_model="gpt-4o-mini",
            enable_llm_fallback=True
        )
        
        assert rule.name == "language-detector"
        assert rule.language_mappings == language_mappings
        assert rule.default == "gpt-4o-mini"
        assert rule.llm_model == "gpt-4o-mini"
        assert rule.enable_llm_fallback is True
        assert str(rule) == "CodeLanguageRule(name='language-detector', languages=['python', 'javascript', 'sql'])"
    
    def test_python_detection(self):
        """Test Python language detection."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model", "javascript": "js-model"},
            default="default-model"
        )
        
        python_examples = [
            "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "import numpy as np\nfrom sklearn import datasets\n\nif __name__ == '__main__':\n    print('Hello')",
            "class MyClass:\n    def __init__(self):\n        self.value = 42\n    \n    def method(self):\n        return self.value",
            "for i in range(10):\n    if i % 2 == 0:\n        print(f'Even: {i}')\n    elif i % 3 == 0:\n        print(f'Divisible by 3: {i}')"
        ]
        
        for code in python_examples:
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "python-model"
    
    def test_javascript_detection(self):
        """Test JavaScript language detection."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model", "javascript": "js-model"},
            default="default-model"
        )
        
        javascript_examples = [
            "function greet(name) {\n    console.log('Hello, ' + name);\n}",
            "const fetchData = async () => {\n    const response = await fetch('/api/data');\n    return response.json();\n};",
            "let numbers = [1, 2, 3, 4, 5];\nconst doubled = numbers.map(x => x * 2);",
            "import React from 'react';\n\nconst Component = () => {\n    return <div>Hello World</div>;\n};"
        ]
        
        for code in javascript_examples:
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "js-model"
    
    def test_java_detection(self):
        """Test Java language detection."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"java": "java-model", "python": "python-model"},
            default="default-model"
        )
        
        java_examples = [
            "public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println('Hello, World!');\n    }\n}",
            "public int calculateSum(int a, int b) {\n    return a + b;\n}",
            "import java.util.List;\nimport java.util.ArrayList;\n\npublic class Example {\n    private List<String> items = new ArrayList<>();\n}"
        ]
        
        for code in java_examples:
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "java-model"
    
    def test_cpp_detection(self):
        """Test C++ language detection."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"cpp": "cpp-model", "c": "c-model"},
            default="default-model"
        )
        
        cpp_examples = [
            "#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n    cout << 'Hello World' << endl;\n    return 0;\n}",
            "class MyClass {\npublic:\n    void method() {\n        std::cout << 'Hello' << std::endl;\n    }\n};",
            "#include <string>\n\nstd::string getName() {\n    return std::string('John');\n}"
        ]
        
        for code in cpp_examples:
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "cpp-model"
    
    def test_sql_detection(self):
        """Test SQL language detection."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"sql": "sql-model", "python": "python-model"},
            default="default-model"
        )
        
        sql_examples = [
            "SELECT * FROM users WHERE age > 18 ORDER BY name",
            "INSERT INTO products (name, price) VALUES ('Widget', 19.99)",
            "UPDATE customers SET email = 'new@email.com' WHERE id = 123",
            "CREATE TABLE orders (\n    id INT PRIMARY KEY,\n    customer_id INT,\n    total DECIMAL(10,2)\n)",
            "SELECT u.name, COUNT(o.id) as order_count\nFROM users u\nLEFT JOIN orders o ON u.id = o.user_id\nGROUP BY u.id\nHAVING COUNT(o.id) > 5"
        ]
        
        for code in sql_examples:
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "sql-model"
    
    def test_html_detection(self):
        """Test HTML language detection."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"html": "html-model", "css": "css-model"},
            default="default-model"
        )
        
        html_examples = [
            "<!DOCTYPE html>\n<html>\n<head><title>Test</title></head>\n<body><h1>Hello</h1></body>\n</html>",
            "<div class='container'>\n    <p>Hello world!</p>\n    <a href='/about'>Learn More</a>\n</div>",
            "<form action='/submit' method='post'>\n    <input type='text' name='username' />\n    <button type='submit'>Submit</button>\n</form>"
        ]
        
        for code in html_examples:
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "html-model"
    
    def test_rust_detection(self):
        """Test Rust language detection."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"rust": "rust-model", "go": "go-model"},
            default="default-model"
        )
        
        rust_examples = [
            "fn main() {\n    println!('Hello, world!');\n}",
            "fn fibonacci(n: u32) -> u32 {\n    match n {\n        0 => 0,\n        1 => 1,\n        _ => fibonacci(n-1) + fibonacci(n-2),\n    }\n}",
            "use std::collections::HashMap;\n\nlet mut map = HashMap::new();\nmap.insert('key', 'value');"
        ]
        
        for code in rust_examples:
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "rust-model"
    
    def test_go_detection(self):
        """Test Go language detection."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"go": "go-model", "rust": "rust-model"},
            default="default-model"
        )
        
        go_examples = [
            "package main\n\nimport 'fmt'\n\nfunc main() {\n    fmt.Println('Hello, World!')\n}",
            "func add(a, b int) int {\n    return a + b\n}",
            "import (\n    'net/http'\n    'fmt'\n)\n\nfunc handler(w http.ResponseWriter, r *http.Request) {\n    fmt.Fprintf(w, 'Hello!')\n}"
        ]
        
        for code in go_examples:
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "go-model"
    
    def test_multiple_languages_chooses_highest_score(self):
        """Test that when multiple languages match, the highest scoring one is chosen."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model", "javascript": "js-model"},
            default="default-model"
        )
        
        # Code that has both Python and JavaScript patterns, but Python should score higher
        mixed_code = """
        # This looks like Python
        def process_data(data):
            result = []
            for item in data:
                if item > 0:
                    result.append(item * 2)
            return result
        
        // But also has some JavaScript-like comments
        const someVar = 'hello';
        """
        
        request_data = {"messages": [{"role": "user", "content": mixed_code}]}
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == "python-model"  # Python should win due to higher score
    
    def test_minimum_score_threshold(self):
        """Test that weak matches below threshold are rejected."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model"},
            default="default-model"
        )
        
        # Text that mentions Python but isn't actually Python code
        weak_match = "I'm learning about Python programming. It's a great language for beginners."
        
        request_data = {"messages": [{"role": "user", "content": weak_match}]}
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == "default-model"  # Should fall back to default
    
    def test_empty_content_uses_default(self):
        """Test that empty content uses default model."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model"},
            default="default-model"
        )
        
        empty_examples = [
            {"messages": []},
            {"messages": [{"role": "user", "content": ""}]},
            {"messages": [{"role": "user"}]},  # Missing content
            {}  # No messages
        ]
        
        for request_data in empty_examples:
            decision = rule.evaluate(request_data)
            assert decision.is_model()
            assert decision.get_model() == "default-model"
    
    def test_unmapped_language_uses_default(self):
        """Test that detected but unmapped languages use default."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model"},  # Only Python mapped
            default="default-model",
            enable_llm_fallback=False  # Disable LLM fallback for this test
        )
        
        # JavaScript code, but JavaScript not in mappings
        js_code = "function test() {\n    console.log('Hello');\n}"
        request_data = {"messages": [{"role": "user", "content": js_code}]}
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == "default-model"
    
    def test_llm_fallback_disabled(self):
        """Test behavior when LLM fallback is disabled."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={
                "python": "python-model",
                "scala": "scala-model"  # Scala not in regex patterns
            },
            default="default-model",
            enable_llm_fallback=False
        )
        
        # Scala code that would require LLM detection
        scala_code = "case class User(name: String, age: Int)\n\nobject Main extends App {\n  println('Hello Scala')\n}"
        request_data = {"messages": [{"role": "user", "content": scala_code}]}
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == "default-model"  # Should use default since LLM is disabled
    
    def test_mixed_content_with_code_blocks(self):
        """Test detection in mixed content with code blocks."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model"},
            default="default-model"
        )
        
        mixed_content = """
        I'm having trouble with this Python function:
        
        ```python
        def calculate_factorial(n):
            if n <= 1:
                return 1
            return n * calculate_factorial(n - 1)
        ```
        
        Can you help me optimize it for better performance?
        """
        
        request_data = {"messages": [{"role": "user", "content": mixed_content}]}
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == "python-model"
    
    def test_multiple_messages_language_detection(self):
        """Test language detection across multiple messages."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model", "javascript": "js-model"},
            default="default-model"
        )
        
        # Multiple messages with Python code
        python_conversation = {
            "messages": [
                {"role": "user", "content": "I need help with a Python function"},
                {"role": "assistant", "content": "Sure! What do you need help with?"},
                {"role": "user", "content": "def broken_func(data):\n    for item in data:\n        print(item)\n    return len(data)"}
            ]
        }
        
        decision = rule.evaluate(python_conversation)
        assert decision.is_model()
        assert decision.get_model() == "python-model"
    
    def test_language_detection_with_rule_references(self):
        """Test CodeLanguageRule that references other rules."""
        # Create a nested rule for Python-specific routing
        python_task_rule = TaskRule("python-tasks", {
            "optimization": "python-optimizer-model",
            "debugging": "python-debugger-model"
        })
        
        rule = CodeLanguageRule(
            name="smart-language-rule",
            language_mappings={
                "python": python_task_rule,  # Reference to another rule
                "javascript": "js-model"
            },
            default="default-model"
        )
        
        python_code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        request_data = {"messages": [{"role": "user", "content": python_code}]}
        
        decision = rule.evaluate(request_data)
        assert decision.is_rule()
        assert decision.get_rule() is python_task_rule
    
    def test_regex_detection_method(self):
        """Test the _detect_language_regex method directly."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model", "javascript": "js-model"},
            default="default-model"
        )
        
        # Test Python detection
        python_code = "def hello():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello()"
        detected = rule._detect_language_regex(python_code)
        assert detected == "python"
        
        # Test JavaScript detection
        js_code = "function greet(name) {\n    console.log(`Hello, ${name}!`);\n}\n\ngreet('World');"
        detected = rule._detect_language_regex(js_code)
        assert detected == "javascript"
        
        # Test no detection
        natural_text = "This is just regular text without any code patterns."
        detected = rule._detect_language_regex(natural_text)
        assert detected is None
    
    def test_extract_text_content_method(self):
        """Test the _extract_text_content method."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"python": "python-model"},
            default="default-model"
        )
        
        # Test with multiple messages
        request_data = {
            "messages": [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Second message"},
                {"role": "user", "content": "Third message"}
            ]
        }
        
        text = rule._extract_text_content(request_data)
        assert text == "First message\nSecond message\nThird message"
        
        # Test with empty messages
        empty_request = {"messages": []}
        text = rule._extract_text_content(empty_request)
        assert text == ""
        
        # Test with missing content
        missing_content = {"messages": [{"role": "user"}]}
        text = rule._extract_text_content(missing_content)
        assert text == ""
    
    def test_llm_detection_method_without_credentials(self):
        """Test LLM detection method when credentials are not available."""
        rule = CodeLanguageRule(
            name="test-rule",
            language_mappings={"scala": "scala-model"},
            default="default-model",
            enable_llm_fallback=True
        )
        
        # Mock get_credentials to return None
        from unittest.mock import patch
        
        with patch('deimos_router.rules.code_language_rule.config.is_configured', return_value=False):
            result = rule._detect_language_llm("some code", ["scala"])
            assert result is None
    
    def test_comprehensive_language_coverage(self):
        """Test that all major languages in the patterns are properly detected."""
        rule = CodeLanguageRule(
            name="comprehensive-rule",
            language_mappings={
                "python": "python-model",
                "javascript": "js-model", 
                "java": "java-model",
                "cpp": "cpp-model",
                "c": "c-model",
                "csharp": "csharp-model",
                "php": "php-model",
                "ruby": "ruby-model",
                "go": "go-model",
                "rust": "rust-model",
                "swift": "swift-model",
                "kotlin": "kotlin-model",
                "sql": "sql-model",
                "html": "html-model",
                "css": "css-model"
            },
            default="default-model"
        )
        
        # Test samples for each language
        language_samples = {
            "python": "def test():\n    import os\n    print('Hello')",
            "javascript": "const test = () => {\n    console.log('Hello');\n};",
            "java": "public class Test {\n    public static void main(String[] args) {\n        System.out.println('Hello');\n    }\n}",
            "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    cout << 'Hello' << endl;\n    return 0;\n}",
            "c": "#include <stdio.h>\nint main() {\n    printf('Hello');\n    return 0;\n}",
            "csharp": "using System;\nnamespace Test {\n    public class Program {\n        public static void Main() {\n            Console.WriteLine('Hello');\n        }\n    }\n}",
            "php": "<?php\nfunction test() {\n    echo 'Hello';\n}\n?>",
            "ruby": "def test\n    puts 'Hello'\nend\n\ntest",
            "go": "package main\nimport 'fmt'\nfunc main() {\n    fmt.Println('Hello')\n}",
            "rust": "fn main() {\n    println!('Hello');\n}",
            "swift": "import Foundation\nfunc test() {\n    print('Hello')\n}",
            "kotlin": "fun main() {\n    println('Hello')\n}",
            "sql": "SELECT * FROM users WHERE name = 'test'",
            "html": "<html><body><h1>Hello</h1></body></html>",
            "css": "body { color: red; }\n.container { margin: 0 auto; }"
        }
        
        # Expected model mappings (some have different names than the language key)
        expected_models = {
            "python": "python-model",
            "javascript": "js-model",  # Note: uses "js-model" not "javascript-model"
            "java": "java-model",
            "cpp": "cpp-model",
            "c": "c-model",
            "csharp": "csharp-model",
            "php": "php-model",
            "ruby": "ruby-model",
            "go": "go-model",
            "rust": "rust-model",
            "swift": "swift-model",
            "kotlin": "kotlin-model",
            "sql": "sql-model",
            "html": "html-model",
            "css": "css-model"
        }
        
        for expected_lang, code in language_samples.items():
            request_data = {"messages": [{"role": "user", "content": code}]}
            decision = rule.evaluate(request_data)
            assert decision.is_model(), f"Failed to detect {expected_lang}"
            expected_model = expected_models[expected_lang]
            assert decision.get_model() == expected_model, f"Wrong model for {expected_lang}: got {decision.get_model()}, expected {expected_model}"
