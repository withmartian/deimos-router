Getting Started
===============

This guide will help you get up and running with Deimos Router quickly.

Installation
------------

Install Deimos Router using pip:

.. code-block:: bash

   pip install deimos-router

Configuration
-------------

Before using Deimos Router, you need to configure your API credentials. Deimos Router supports multiple configuration methods:

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Set the following environment variables:

.. code-block:: bash

   export DEIMOS_API_URL="https://your-api-endpoint.com/v1"
   export DEIMOS_API_KEY="your-api-key"

Configuration File
~~~~~~~~~~~~~~~~~~

Create a ``secrets.json`` file in your project directory:

.. code-block:: json

   {
     "api_url": "https://your-api-endpoint.com/v1",
     "api_key": "your-api-key"
   }

Basic Usage
-----------

Here's a simple example to get you started:

.. code-block:: python

   from deimos_router import Router, register_router, chat
   from deimos_router.rules import TaskRule

   # Create a simple router
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
       default_model="openai/gpt-4o-mini"
   )

   # Register the router
   register_router(router)

   # Use the router for chat completions
   response = chat.completions.create(
       model="deimos/my-first-router",
       messages=[
           {"role": "user", "content": "Help me write a Python function"}
       ],
       task="coding"
   )

   print(response.choices[0].message.content)

Understanding the Example
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Router Creation**: We create a ``Router`` with a name and a list of rules
2. **Rule Definition**: The ``TaskRule`` routes requests based on the ``task`` parameter
3. **Registration**: We register the router so it can be used in API calls
4. **API Call**: We use ``chat.completions.create()`` with the router name prefixed by ``deimos/``
5. **Task Parameter**: The ``task="coding"`` parameter tells the router which rule to apply

Direct Model Calls
-------------------

You can also make direct calls to specific models without routing:

.. code-block:: python

   from deimos_router import chat

   # Direct model call
   response = chat.completions.create(
       model="openai/gpt-4o-mini",
       messages=[
           {"role": "user", "content": "Hello, world!"}
       ]
   )

Router with Explanation
-----------------------

To understand how routing decisions are made, use the ``explain`` parameter:

.. code-block:: python

   response = chat.completions.create(
       model="deimos/my-first-router",
       messages=[
           {"role": "user", "content": "Write a poem"}
       ],
       task="creative",
       explain=True
   )

   # Check the routing explanation
   print("Router used:", response._deimos_metadata['router_used'])
   print("Selected model:", response._deimos_metadata['selected_model'])
   
   # Detailed explanation of routing decisions
   for entry in response._deimos_metadata['explain']:
       print(f"Rule: {entry['rule_name']} ({entry['rule_type']})")
       print(f"Decision: {entry['decision']}")
       print(f"Trigger: {entry['trigger']}")

Next Steps
----------

Now that you have the basics working, you can:

1. Learn about different :doc:`rule-types` available
2. Explore more complex :doc:`examples`
3. Read the complete :doc:`user-guide`
4. Check the :doc:`api-reference` for detailed documentation
