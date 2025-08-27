#!/usr/bin/env python3
"""Example demonstrating the logging functionality in deimos-router."""

import json
import time
from datetime import datetime
from pathlib import Path

from deimos_router.router import Router, register_router
from deimos_router.rules import CodeRule, TaskRule
from deimos_router.chat import ChatCompletions
from deimos_router.logging.logger import configure_logging, get_logger
from deimos_router.logging.json_logger import JSONFileLogger


def setup_example_router():
    """Set up an example router with rules for demonstration."""
    # Create a router with code detection and task-based routing
    router = Router(
        name="example_router",
        rules=[
            CodeRule(name="code_detector", code="claude-3-5-sonnet", not_code="gpt-4"),
            TaskRule(name="task_router", rules={
                "debug": "claude-3-5-sonnet",
                "creative": "gpt-4",
                "analysis": "gpt-4"
            })
        ],
        default="gpt-3.5-turbo"
    )
    
    # Register the router
    register_router(router)
    return router


def demonstrate_logging_configuration():
    """Demonstrate different logging configuration options."""
    print("=== Logging Configuration Demo ===")
    
    # Option 1: Use default configuration (enabled by default)
    print("1. Default logging configuration:")
    logger = get_logger()
    print(f"   - Enabled: {logger.enabled}")
    print(f"   - Backend: {type(logger.backend).__name__}")
    print(f"   - Cost Calculator: {type(logger.cost_calculator).__name__}")
    
    # Option 2: Configure logging programmatically
    print("\n2. Custom logging configuration:")
    custom_logger = configure_logging(
        enabled=True,
        log_directory="./custom_logs",
        custom_pricing={
            "gpt-4": {"input": 0.03, "output": 0.06},
            "claude-3-5-sonnet": {"input": 0.003, "output": 0.015}
        }
    )
    print(f"   - Custom directory: ./custom_logs")
    print(f"   - Custom pricing configured")
    
    # Option 3: Disable logging
    print("\n3. Disabled logging:")
    disabled_logger = configure_logging(enabled=False)
    print(f"   - Enabled: {disabled_logger.enabled}")


def demonstrate_router_logging():
    """Demonstrate logging with router-based requests."""
    print("\n=== Router Logging Demo ===")
    
    # Set up router
    router = setup_example_router()
    chat = ChatCompletions()
    
    # Example requests that will trigger different routing decisions
    test_requests = [
        {
            "messages": [{"role": "user", "content": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"}],
            "description": "Code request (should route to claude-3-5-sonnet)"
        },
        {
            "messages": [{"role": "user", "content": "Write a creative story about a time traveler"}],
            "task": "creative",
            "description": "Creative task (should route to gpt-4)"
        },
        {
            "messages": [{"role": "user", "content": "Help me debug this function"}],
            "task": "debug",
            "description": "Debug task (should route to claude-3-5-sonnet)"
        },
        {
            "messages": [{"role": "user", "content": "What's the weather like?"}],
            "description": "General request (should use default)"
        }
    ]
    
    print("Making example requests (these will be logged):")
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. {request['description']}")
        
        try:
            # Note: This will fail without proper API credentials, but logging will still work
            response = chat.create(
                messages=request["messages"],
                model="deimos/example_router",
                task=request.get("task"),
                explain=True  # Get routing explanations
            )
            print(f"   ✓ Request completed successfully")
            
        except Exception as e:
            print(f"   ⚠ Request failed (expected without API credentials): {str(e)[:100]}...")
            # The request will still be logged even if it fails


def demonstrate_direct_model_logging():
    """Demonstrate logging with direct model requests."""
    print("\n=== Direct Model Logging Demo ===")
    
    chat = ChatCompletions()
    
    try:
        # Direct model call (no router)
        response = chat.create(
            messages=[{"role": "user", "content": "Hello, how are you?"}],
            model="gpt-3.5-turbo"
        )
        print("✓ Direct model request completed successfully")
        
    except Exception as e:
        print(f"⚠ Direct model request failed (expected without API credentials): {str(e)[:100]}...")


def examine_log_files():
    """Examine the generated log files."""
    print("\n=== Log File Examination ===")
    
    # Get the logger to access the backend
    logger = get_logger()
    
    if isinstance(logger.backend, JSONFileLogger):
        log_files = logger.backend.get_log_files()
        
        if log_files:
            print(f"Found {len(log_files)} log file(s):")
            
            for log_file in log_files:
                print(f"\n📁 {log_file}")
                
                # Read and display some entries
                try:
                    entries = logger.backend.read_log_entries()
                    print(f"   Contains {len(entries)} log entries")
                    
                    if entries:
                        # Show the structure of the first entry
                        first_entry = entries[0]
                        print("   Sample log entry structure:")
                        for key in first_entry.keys():
                            value = first_entry[key]
                            if isinstance(value, str) and len(value) > 50:
                                value = value[:50] + "..."
                            print(f"     - {key}: {value}")
                
                except Exception as e:
                    print(f"   Error reading log file: {e}")
        else:
            print("No log files found yet.")
    else:
        print("No JSON file logger backend configured.")


def demonstrate_log_analysis():
    """Demonstrate basic log analysis capabilities."""
    print("\n=== Log Analysis Demo ===")
    
    logger = get_logger()
    
    if isinstance(logger.backend, JSONFileLogger):
        try:
            entries = logger.backend.read_log_entries()
            
            if not entries:
                print("No log entries found for analysis.")
                return
            
            print(f"Analyzing {len(entries)} log entries:")
            
            # Basic statistics
            successful_requests = [e for e in entries if e.get('status') == 'success']
            failed_requests = [e for e in entries if e.get('status') == 'error']
            
            print(f"  - Successful requests: {len(successful_requests)}")
            print(f"  - Failed requests: {len(failed_requests)}")
            
            # Model usage statistics
            model_usage = {}
            for entry in entries:
                model = entry.get('selected_model', 'unknown')
                model_usage[model] = model_usage.get(model, 0) + 1
            
            print("  - Model usage:")
            for model, count in model_usage.items():
                print(f"    * {model}: {count} requests")
            
            # Router usage statistics
            router_usage = {}
            for entry in entries:
                router = entry.get('router_name') or 'direct'
                router_usage[router] = router_usage.get(router, 0) + 1
            
            print("  - Router usage:")
            for router, count in router_usage.items():
                print(f"    * {router}: {count} requests")
            
            # Average latency (for successful requests)
            if successful_requests:
                latencies = [e.get('latency_ms', 0) for e in successful_requests if e.get('latency_ms')]
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                    print(f"  - Average latency: {avg_latency:.2f}ms")
            
            # Total estimated costs
            total_cost = 0
            estimated_costs = 0
            for entry in entries:
                cost = entry.get('cost')
                if cost:
                    total_cost += cost
                    if entry.get('cost_estimated', True):
                        estimated_costs += 1
            
            if total_cost > 0:
                print(f"  - Total estimated cost: ${total_cost:.6f}")
                print(f"  - Estimated costs: {estimated_costs}/{len(entries)} entries")
        
        except Exception as e:
            print(f"Error during log analysis: {e}")
    else:
        print("No JSON file logger backend available for analysis.")


def main():
    """Run the logging demonstration."""
    print("🚀 Deimos Router Logging System Demo")
    print("=" * 50)
    
    # Configure logging for the demo
    configure_logging(
        enabled=True,
        log_directory="./demo_logs",
        custom_pricing={
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-3-5-sonnet": {"input": 0.003, "output": 0.015}
        }
    )
    
    try:
        # Run demonstrations
        demonstrate_logging_configuration()
        demonstrate_router_logging()
        demonstrate_direct_model_logging()
        
        # Give a moment for any async operations
        time.sleep(0.1)
        
        examine_log_files()
        demonstrate_log_analysis()
        
        print("\n" + "=" * 50)
        print("✅ Demo completed!")
        print("\nCheck the './demo_logs' directory for generated log files.")
        print("Each log entry contains:")
        print("  - Request/response data")
        print("  - Routing decisions and explanations")
        print("  - Timing and performance metrics")
        print("  - Cost estimates")
        print("  - Error information (if applicable)")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        logger = get_logger()
        logger.close()


if __name__ == "__main__":
    main()
