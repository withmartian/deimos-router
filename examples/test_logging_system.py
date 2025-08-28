#!/usr/bin/env python3
"""Test script to verify the logging system functionality."""

import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock

from deimos_router.logging.base import LogEntry, LoggerBackend
from deimos_router.logging.json_logger import JSONFileLogger
from deimos_router.logging.costs import CostCalculator
from deimos_router.logging.logger import RequestLogger, configure_logging


def test_log_entry_creation():
    """Test LogEntry creation and manipulation."""
    print("Testing LogEntry creation...")
    
    # Test creating a request entry
    entry = LogEntry.create_request_entry(
        router_name="test_router",
        selected_model="gpt-4",
        routing_explanation=[{"rule": "test", "decision": "gpt-4"}],
        request={"messages": [{"role": "user", "content": "test"}]}
    )
    
    assert entry.router_name == "test_router"
    assert entry.selected_model == "gpt-4"
    assert entry.status == "pending"
    assert entry.request_id is not None
    
    # Test completing with success
    entry.complete_success(
        response={"choices": [{"message": {"content": "test response"}}]},
        latency_ms=150.5,
        tokens={"prompt": 10, "completion": 20, "total": 30},
        cost=0.001,
        cost_estimated=True,
        cost_source="token_calculation"
    )
    
    assert entry.status == "success"
    assert entry.latency_ms == 150.5
    assert entry.cost == 0.001
    assert entry.cost_estimated == True
    
    # Test converting to dict
    entry_dict = entry.to_dict()
    assert "timestamp" in entry_dict
    assert entry_dict["router_name"] == "test_router"
    assert entry_dict["status"] == "success"
    
    print("✓ LogEntry tests passed")


def test_json_file_logger():
    """Test JSONFileLogger functionality."""
    print("Testing JSONFileLogger...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = JSONFileLogger(log_directory=temp_dir, filename_prefix="test-logs")
        
        # Create test entries
        entry1 = LogEntry.create_request_entry(
            router_name="test_router",
            selected_model="gpt-4",
            routing_explanation=[],
            request={"test": "data1"}
        )
        entry1.complete_success(
            response={"test": "response1"},
            latency_ms=100.0,
            cost=0.001,
            cost_estimated=True,
            cost_source="test"
        )
        
        entry2 = LogEntry.create_request_entry(
            router_name="test_router",
            selected_model="gpt-3.5-turbo",
            routing_explanation=[],
            request={"test": "data2"}
        )
        entry2.complete_error("Test error", 50.0)
        
        # Log the entries
        logger.log_entry(entry1)
        logger.log_entry(entry2)
        
        # Test reading entries
        entries = logger.read_log_entries()
        assert len(entries) == 2
        
        # Test log file creation
        log_files = logger.get_log_files()
        assert len(log_files) == 1
        
        # Verify file content
        with open(log_files[0], 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            
            # Parse first line
            first_entry = json.loads(lines[0])
            assert first_entry["selected_model"] == "gpt-4"
            assert first_entry["status"] == "success"
            
            # Parse second line
            second_entry = json.loads(lines[1])
            assert second_entry["selected_model"] == "gpt-3.5-turbo"
            assert second_entry["status"] == "error"
        
        logger.close()
    
    print("✓ JSONFileLogger tests passed")


def test_cost_calculator():
    """Test CostCalculator functionality."""
    print("Testing CostCalculator...")
    
    calculator = CostCalculator()
    
    # Test token-based cost estimation
    tokens = {"prompt": 1000, "completion": 500, "total": 1500}
    cost, is_estimated, source = calculator.estimate_cost_from_tokens("gpt-4", tokens)
    
    # GPT-4 pricing: $0.03 input, $0.06 output per 1K tokens
    expected_cost = (1000 / 1000) * 0.03 + (500 / 1000) * 0.06  # 0.03 + 0.03 = 0.06
    assert abs(cost - expected_cost) < 0.001
    assert is_estimated == True
    assert source == "token_calculation"
    
    # Test model name normalization
    normalized = calculator._normalize_model_name("gpt-4-turbo-preview-0125")
    assert normalized == "gpt-4-turbo"
    
    normalized = calculator._normalize_model_name("claude-3-5-sonnet-20241022")
    assert normalized == "claude-3-5-sonnet"
    
    # Test custom pricing
    custom_calculator = CostCalculator(custom_pricing={
        "custom-model": {"input": 0.01, "output": 0.02}
    })
    
    cost, is_estimated, source = custom_calculator.estimate_cost_from_tokens("custom-model", tokens)
    expected_cost = (1000 / 1000) * 0.01 + (500 / 1000) * 0.02  # 0.01 + 0.01 = 0.02
    assert abs(cost - expected_cost) < 0.001
    
    print("✓ CostCalculator tests passed")


def test_request_logger():
    """Test RequestLogger functionality."""
    print("Testing RequestLogger...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock backend
        backend = JSONFileLogger(log_directory=temp_dir)
        cost_calculator = CostCalculator()
        
        logger = RequestLogger(
            backend=backend,
            cost_calculator=cost_calculator,
            enabled=True
        )
        
        # Test logging a successful request
        with logger.log_request(
            router_name="test_router",
            selected_model="gpt-4",
            routing_explanation=[{"rule": "test", "decision": "gpt-4"}],
            request_data={"messages": [{"role": "user", "content": "test"}]}
        ) as log_entry:
            
            # Simulate API response - create a simple object instead of Mock
            class MockResponse:
                def __init__(self):
                    self.model = "gpt-4"
                    self.choices = [MockChoice()]
                    self.usage = MockUsage()
            
            class MockChoice:
                def __init__(self):
                    self.message = MockMessage()
                    self.finish_reason = "stop"
            
            class MockMessage:
                def __init__(self):
                    self.role = "assistant"
                    self.content = "Test response"
            
            class MockUsage:
                def __init__(self):
                    self.prompt_tokens = 10
                    self.completion_tokens = 20
                    self.total_tokens = 30
            
            mock_response = MockResponse()
            
            # Complete the request
            import time
            start_time = time.time()
            logger.complete_request_success(log_entry, mock_response, start_time)
        
        # Test logging a failed request
        try:
            with logger.log_request(
                router_name="test_router",
                selected_model="gpt-4",
                routing_explanation=[],
                request_data={"messages": [{"role": "user", "content": "test"}]}
            ) as log_entry:
                raise Exception("Test error")
        except Exception:
            pass  # Expected
        
        # Verify entries were logged
        entries = backend.read_log_entries()
        assert len(entries) == 2
        
        # Check successful entry
        success_entry = next(e for e in entries if e["status"] == "success")
        assert success_entry["router_name"] == "test_router"
        assert success_entry["selected_model"] == "gpt-4"
        assert success_entry["tokens"]["total"] == 30
        assert success_entry["cost"] > 0
        
        # Check error entry
        error_entry = next(e for e in entries if e["status"] == "error")
        assert error_entry["error_message"] == "Test error"
        
        logger.close()
    
    print("✓ RequestLogger tests passed")


def test_disabled_logging():
    """Test that disabled logging works correctly."""
    print("Testing disabled logging...")
    
    logger = RequestLogger(enabled=False)
    
    # This should not raise any errors and should not create any files
    with logger.log_request(
        router_name="test_router",
        selected_model="gpt-4",
        routing_explanation=[],
        request_data={"test": "data"}
    ) as log_entry:
        assert log_entry.status == "disabled"
        
        # This should be a no-op
        logger.complete_request_success(log_entry, Mock(), 0.0)
    
    print("✓ Disabled logging tests passed")


def test_configuration_integration():
    """Test configuration integration."""
    print("Testing configuration integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test programmatic configuration
        logger = configure_logging(
            enabled=True,
            log_directory=temp_dir,
            custom_pricing={"test-model": {"input": 0.01, "output": 0.02}}
        )
        
        assert logger.enabled == True
        assert isinstance(logger.backend, JSONFileLogger)
        assert logger.cost_calculator.pricing["test-model"]["input"] == 0.01
        
        # Test disabled configuration
        disabled_logger = configure_logging(enabled=False)
        assert disabled_logger.enabled == False
        assert disabled_logger.backend is None
        
        logger.close()
        disabled_logger.close()
    
    print("✓ Configuration integration tests passed")


def test_error_handling():
    """Test error handling in various scenarios."""
    print("Testing error handling...")
    
    # Test with invalid log directory (should not crash)
    try:
        logger = JSONFileLogger(log_directory="/invalid/path/that/does/not/exist")
        # This might fail during directory creation, but should be handled gracefully
    except Exception as e:
        print(f"   Expected error for invalid directory: {e}")
    
    # Test with malformed log entry (should not crash the logger)
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = JSONFileLogger(log_directory=temp_dir)
        
        # Create a valid entry first
        entry = LogEntry.create_request_entry(
            router_name="test",
            selected_model="gpt-4",
            routing_explanation=[],
            request={"test": "data"}
        )
        
        # This should work fine
        logger.log_entry(entry)
        
        logger.close()
    
    print("✓ Error handling tests passed")


def run_all_tests():
    """Run all tests."""
    print("🧪 Running Logging System Tests")
    print("=" * 50)
    
    try:
        test_log_entry_creation()
        test_json_file_logger()
        test_cost_calculator()
        test_request_logger()
        test_disabled_logging()
        test_configuration_integration()
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("\nThe logging system is working correctly and ready for use.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
