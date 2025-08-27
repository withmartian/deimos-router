#!/usr/bin/env python3
"""Example usage of NaturalLanguageRule for routing based on natural language detection."""

import asyncio
from deimos_router import Router
from deimos_router.rules import NaturalLanguageRule


def create_natural_language_router():
    """Create a router that routes based on detected natural language."""
    
    # Define language mappings - map 2-letter ISO codes to models
    language_mappings = {
        'en': 'gpt-4o',           # English -> GPT-4o (best for English)
        'es': 'claude-3-sonnet',  # Spanish -> Claude Sonnet (good multilingual)
        'fr': 'gpt-4o-mini',      # French -> GPT-4o Mini (cost-effective)
        'de': 'claude-3-haiku',   # German -> Claude Haiku (fast multilingual)
        'it': 'gpt-4o-mini',      # Italian -> GPT-4o Mini
        'pt': 'claude-3-sonnet',  # Portuguese -> Claude Sonnet
    }
    
    # Create the natural language rule
    natural_language_rule = NaturalLanguageRule(
        name='natural_language_router',
        language_mappings=language_mappings,
        default='gpt-4o-mini',  # Default for undetected/unmapped languages
        llm_model='gpt-4o-mini'  # Use smallest model for language detection
    )
    
    # Create and configure the router
    router = Router()
    router.add_rule(natural_language_rule)
    
    return router


async def test_natural_language_routing():
    """Test the natural language router with various languages."""
    
    router = create_natural_language_router()
    
    # Test cases with different languages
    test_cases = [
        {
            'name': 'English',
            'messages': [
                {'role': 'user', 'content': 'Hello! Can you help me write a Python function to calculate the factorial of a number?'}
            ],
            'expected_model': 'gpt-4o'
        },
        {
            'name': 'Spanish',
            'messages': [
                {'role': 'user', 'content': '¡Hola! ¿Puedes ayudarme a escribir una función en Python para calcular el factorial de un número?'}
            ],
            'expected_model': 'claude-3-sonnet'
        },
        {
            'name': 'French',
            'messages': [
                {'role': 'user', 'content': 'Bonjour! Pouvez-vous m\'aider à écrire une fonction Python pour calculer la factorielle d\'un nombre?'}
            ],
            'expected_model': 'gpt-4o-mini'
        },
        {
            'name': 'German',
            'messages': [
                {'role': 'user', 'content': 'Hallo! Können Sie mir helfen, eine Python-Funktion zu schreiben, um die Fakultät einer Zahl zu berechnen?'}
            ],
            'expected_model': 'claude-3-haiku'
        },
        {
            'name': 'Italian',
            'messages': [
                {'role': 'user', 'content': 'Ciao! Puoi aiutarmi a scrivere una funzione Python per calcolare il fattoriale di un numero?'}
            ],
            'expected_model': 'gpt-4o-mini'
        },
        {
            'name': 'Portuguese',
            'messages': [
                {'role': 'user', 'content': 'Olá! Você pode me ajudar a escrever uma função Python para calcular o fatorial de um número?'}
            ],
            'expected_model': 'claude-3-sonnet'
        },
        {
            'name': 'Mixed/Unclear',
            'messages': [
                {'role': 'user', 'content': 'xyz abc 123 !@# random text'}
            ],
            'expected_model': 'gpt-4o-mini'  # Should fall back to default
        }
    ]
    
    print("🌍 Testing Natural Language Router")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n📝 Testing {test_case['name']}:")
        print(f"   Input: {test_case['messages'][0]['content'][:60]}...")
        
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
    print("🏁 Natural Language Routing Test Complete!")


def demonstrate_rule_configuration():
    """Demonstrate different ways to configure the NaturalLanguageRule."""
    
    print("\n🔧 Natural Language Rule Configuration Examples")
    print("=" * 50)
    
    # Example 1: Basic configuration
    print("\n1️⃣ Basic Configuration:")
    basic_rule = NaturalLanguageRule(
        name='basic_language_router',
        language_mappings={
            'en': 'gpt-4o',
            'es': 'claude-3-sonnet'
        },
        default='gpt-4o-mini'
    )
    print(f"   Rule: {basic_rule}")
    
    # Example 2: With custom detection model
    print("\n2️⃣ Custom Detection Model:")
    custom_rule = NaturalLanguageRule(
        name='custom_language_router',
        language_mappings={
            'en': 'gpt-4o',
            'fr': 'claude-3-sonnet',
            'de': 'gpt-4o-mini'
        },
        default='gpt-4o-mini',
        llm_model='gpt-4o'  # Use more powerful model for detection
    )
    print(f"   Rule: {custom_rule}")
    print(f"   Detection Model: {custom_rule.llm_model}")
    
    # Example 3: Nested rules (language -> specialized rules)
    print("\n3️⃣ Nested Rules (Language -> Specialized Rules):")
    
    # Create specialized rules for different languages
    english_code_rule = NaturalLanguageRule(
        name='english_code_router',
        language_mappings={'en': 'gpt-4o'},  # Specialized for English coding
        default='gpt-4o'
    )
    
    spanish_general_rule = NaturalLanguageRule(
        name='spanish_general_router', 
        language_mappings={'es': 'claude-3-sonnet'},  # Good for Spanish
        default='claude-3-sonnet'
    )
    
    nested_rule = NaturalLanguageRule(
        name='nested_language_router',
        language_mappings={
            'en': english_code_rule,      # Route English to specialized rule
            'es': spanish_general_rule,   # Route Spanish to specialized rule
            'fr': 'gpt-4o-mini'          # Direct model for French
        },
        default='gpt-4o-mini'
    )
    print(f"   Main Rule: {nested_rule}")
    print(f"   English Sub-rule: {english_code_rule}")
    print(f"   Spanish Sub-rule: {spanish_general_rule}")


if __name__ == '__main__':
    print("🚀 Natural Language Rule Example")
    print("This example demonstrates routing based on natural language detection.")
    print("\nNote: Make sure you have configured your API credentials in secrets.json")
    print("or environment variables before running this example.\n")
    
    # Demonstrate configuration options
    demonstrate_rule_configuration()
    
    # Test the routing (commented out by default since it requires API credentials)
    print("\n" + "=" * 60)
    print("To test actual routing, uncomment the following line and ensure")
    print("your API credentials are configured:")
    print("# asyncio.run(test_natural_language_routing())")
    
    # Uncomment the next line to run actual tests (requires API credentials)
    # asyncio.run(test_natural_language_routing())
