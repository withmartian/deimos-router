User Guide
==========

This comprehensive guide covers all aspects of using Deimos Router effectively.

Core Concepts
-------------

Routers
~~~~~~~

A **Router** is the main component that manages routing decisions. It contains:

- A unique name for identification
- A list of rules that define routing logic
- A default model to use when no rules match

.. code-block:: python

   from deimos_router import Router

   router = Router(
       name="my-router",
       rules=[rule1, rule2, rule3],
       default_model="openai/gpt-4o-mini"
   )

Rules
~~~~~

**Rules** define the logic for routing decisions. Each rule:

- Has a name and type
- Evaluates request data (messages, task, etc.)
- Returns either a model name or another rule to evaluate
- Can be chained together for complex routing logic

Rule Chaining
~~~~~~~~~~~~~

Rules can point to other rules, creating chains:

.. code-block:: python

   # Rule A points to Rule B, which points to a model
   rule_a = TaskRule(name="task-router", rules={'coding': rule_b})
   rule_b = CodeRule(name="code-detector", code="openai/gpt-4", not_code="openai/gpt-4o-mini")

Chat Completions
----------------

Making API Calls
~~~~~~~~~~~~~~~~~

Use the ``chat.completions.create()`` method for all API calls:

.. code-block:: python

   from deimos_router import chat

   # Router-based call
   response = chat.completions.create(
       model="deimos/router-name",
       messages=[{"role": "user", "content": "Hello"}],
       # Additional parameters for routing
       task="coding",
       explain=True
   )

   # Direct model call
   response = chat.completions.create(
       model="openai/gpt-4o-mini",
       messages=[{"role": "user", "content": "Hello"}]
   )

Custom Parameters
~~~~~~~~~~~~~~~~~

Deimos Router supports custom parameters that are used for routing but not passed to the underlying LLM API:

- ``task``: Specify the task type for TaskRule routing
- ``explain``: Get detailed routing explanations
- Any other custom parameters your rules might use

Standard OpenAI parameters (``temperature``, ``max_tokens``, etc.) are passed through to the LLM API.

Router Registration
-------------------

Global Registration
~~~~~~~~~~~~~~~~~~~

Register routers globally to use them in API calls:

.. code-block:: python

   from deimos_router import register_router, clear_routers

   # Register a router
   register_router(my_router)

   # Clear all registered routers
   clear_routers()

   # Check registered routers
   from deimos_router.router import get_router
   router = get_router("my-router")

Creating Rules
--------------

Rule Instances
~~~~~~~~~~~~~~

Create rule instances by importing the rule class and providing configuration:

.. code-block:: python

   from deimos_router.rules import TaskRule, CodeRule, MessageLengthRule

   # Task-based routing
   task_rule = TaskRule(
       name="task-router",
       rules={
           'coding': 'openai/gpt-4',
           'creative': 'openai/gpt-4',
           'simple': 'openai/gpt-4o-mini'
       }
   )

   # Code detection
   code_rule = CodeRule(
       name="code-detector",
       code="openai/gpt-4",
       not_code="openai/gpt-4o-mini"
   )

   # Message length routing
   length_rule = MessageLengthRule(
       name="length-router",
       short_threshold=100,
       long_threshold=500,
       short_model="openai/gpt-4o-mini",
       medium_model="openai/gpt-4o-mini",
       long_model="openai/gpt-4"
   )

Rule Composition
~~~~~~~~~~~~~~~~

Combine rules for sophisticated routing logic:

.. code-block:: python

   from deimos_router import Router
   from deimos_router.rules import CodeRule, TaskRule, MessageLengthRule

   # Create individual rules
   task_rule = TaskRule(
       name="task-router",
       rules={
           'coding': 'openai/gpt-4',
           'analysis': 'openai/gpt-4',
           'simple': 'openai/gpt-4o-mini'
       }
   )

   code_rule = CodeRule(
       name="code-detector",
       code=task_rule,  # If code detected, use task rule
       not_code='openai/gpt-4o-mini'  # If no code, use simple model
   )

   length_rule = MessageLengthRule(
       name="length-fallback",
       short_threshold=50,
       long_threshold=500,
       short_model="openai/gpt-4o-mini",
       medium_model="openai/gpt-4o-mini",
       long_model="openai/gpt-4"
   )

   # Compose rules in a router
   router = Router(
       name="complex-router",
       rules=[code_rule, length_rule],  # Try code detection first, then length
       default_model="openai/gpt-4o-mini"
   )

Creating Routers
----------------

Basic Router
~~~~~~~~~~~~

.. code-block:: python

   from deimos_router import Router
   from deimos_router.rules import TaskRule

   router = Router(
       name="basic-router",
       rules=[
           TaskRule(
               name="task-rule",
               rules={'coding': 'openai/gpt-4o', 'simple': 'openai/gpt-4o-mini'}
           )
       ],
       default_model="openai/gpt-4o-mini"
   )

Multi-Rule Router
~~~~~~~~~~~~~~~~~

.. code-block:: python

   router = Router(
       name="multi-rule-router",
       rules=[
           # Rules are evaluated in order
           CodeRule(name="code-check", code="openai/gpt-4o", not_code=None),
           TaskRule(name="task-check", rules={'creative': 'openai/gpt-4o'}),
           MessageLengthRule(
               name="length-check",
               short_threshold=100,
               long_threshold=500,
               short_model="openai/gpt-4o-mini",
               medium_model="openai/gpt-4o-mini",
               long_model="openai/gpt-4o"
           )
       ],
       default_model="openai/gpt-4o-mini"
   )

Router Evaluation
~~~~~~~~~~~~~~~~~

Routers evaluate rules in the order they're defined:

1. Each rule is evaluated with the request data
2. If a rule returns a model, that model is used
3. If a rule returns another rule, that rule is evaluated
4. If no rules match, the default model is used
5. Rule chains are followed until a model is found

Debugging and Explanation
-------------------------

Understanding Routing Decisions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``explain=True`` parameter to get detailed information about routing decisions:

.. code-block:: python

   response = chat.completions.create(
       model="deimos/my-router",
       messages=[{"role": "user", "content": "Write code"}],
       task="coding",
       explain=True
   )

   # Access routing metadata
   metadata = response._deimos_metadata
   print(f"Router used: {metadata['router_used']}")
   print(f"Selected model: {metadata['selected_model']}")

   # Detailed explanation
   for entry in metadata['explain']:
       print(f"Rule: {entry['rule_name']} ({entry['rule_type']})")
       print(f"Decision: {entry['decision']}")
       print(f"Trigger: {entry['trigger']}")

Error Handling
--------------

Router Not Found
~~~~~~~~~~~~~~~~~

.. code-block:: python

   try:
       response = chat.completions.create(
           model="deimos/nonexistent-router",
           messages=[{"role": "user", "content": "Hello"}]
       )
   except ValueError as e:
       print(f"Router error: {e}")

API Errors
~~~~~~~~~~

Standard OpenAI API errors are passed through:

.. code-block:: python

   try:
       response = chat.completions.create(
           model="openai/invalid-model",
           messages=[{"role": "user", "content": "Hello"}]
       )
   except Exception as e:
       print(f"API error: {e}")

Best Practices
--------------

1. **Use Descriptive Names**: Give your routers and rules clear, descriptive names
2. **Order Rules Carefully**: Rules are evaluated in order, so put more specific rules first
3. **Provide Fallbacks**: Always specify a default model for your routers
4. **Test Your Rules**: Use the ``explain`` parameter to verify routing behavior
5. **Keep Rules Simple**: Complex logic should be split across multiple rules
6. **Document Your Routing**: Comment your rule configurations for maintainability

Performance Considerations
--------------------------

- Rules that require LLM calls (like AutoTaskRule, NaturalLanguageRule) add latency
- Simple rules (TaskRule, MessageLengthRule, CodeRule) are very fast
- Rule chains are evaluated sequentially, so shorter chains are faster
- Consider caching strategies for expensive rule evaluations
