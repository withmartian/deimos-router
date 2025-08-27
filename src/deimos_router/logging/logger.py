"""Main request logger orchestrator."""

import time
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from .base import LogEntry, LoggerBackend
from .json_logger import JSONFileLogger
from .costs import CostCalculator
from ..config import config


class RequestLogger:
    """Main logging orchestrator that coordinates logging operations."""
    
    def __init__(
        self, 
        backend: Optional[LoggerBackend] = None,
        cost_calculator: Optional[CostCalculator] = None,
        enabled: bool = True
    ):
        """Initialize the request logger.
        
        Args:
            backend: The logging backend to use (defaults to JSONFileLogger)
            cost_calculator: Cost calculator instance (defaults to new CostCalculator)
            enabled: Whether logging is enabled
        """
        self.enabled = enabled
        if enabled and backend is None:
            self.backend = JSONFileLogger()
        else:
            self.backend = backend
        self.cost_calculator = cost_calculator or CostCalculator()
    
    @contextmanager
    def log_request(
        self,
        router_name: Optional[str],
        selected_model: str,
        routing_explanation: List[Dict[str, Any]],
        request_data: Dict[str, Any],
        request_id: Optional[str] = None
    ):
        """Context manager for logging a complete request/response cycle.
        
        Args:
            router_name: Name of the router used (None for direct model calls)
            selected_model: The model that was selected
            routing_explanation: List of routing decision explanations
            request_data: The complete request data
            request_id: Optional request ID (will generate if not provided)
            
        Yields:
            LogEntry object that can be updated during the request
        """
        if not self.enabled:
            # Create a dummy entry that does nothing
            yield _DummyLogEntry()
            return
        
        # Create initial log entry
        entry = LogEntry.create_request_entry(
            router_name=router_name,
            selected_model=selected_model,
            routing_explanation=routing_explanation,
            request=request_data,
            request_id=request_id
        )
        
        start_time = time.time()
        
        try:
            yield entry
        except Exception as e:
            # Log the error
            latency_ms = (time.time() - start_time) * 1000
            entry.complete_error(str(e), latency_ms)
            self._log_entry(entry)
            raise
        else:
            # If no exception occurred but entry wasn't completed, mark as success
            if entry.status == "pending":
                latency_ms = (time.time() - start_time) * 1000
                entry.complete_success(
                    response={"status": "completed_without_response"},
                    latency_ms=latency_ms
                )
            
            self._log_entry(entry)
    
    def complete_request_success(
        self,
        entry: LogEntry,
        response: Any,
        start_time: float
    ) -> None:
        """Complete a request with successful response data.
        
        Args:
            entry: The log entry to complete
            response: The API response object
            start_time: The start time of the request
        """
        if not self.enabled or isinstance(entry, _DummyLogEntry):
            return
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract tokens from response
        tokens = self.cost_calculator.extract_tokens_from_response(response)
        
        # Calculate cost
        cost, cost_estimated, cost_source = self.cost_calculator.calculate_cost(
            entry.selected_model, response
        )
        
        # Convert response to dictionary for logging
        response_dict = self._response_to_dict(response)
        
        # Complete the entry
        entry.complete_success(
            response=response_dict,
            latency_ms=latency_ms,
            tokens=tokens,
            cost=cost,
            cost_estimated=cost_estimated,
            cost_source=cost_source
        )
    
    def _response_to_dict(self, response: Any) -> Dict[str, Any]:
        """Convert API response to dictionary for logging.
        
        Args:
            response: The API response object
            
        Returns:
            Dictionary representation of the response
        """
        response_dict = {}
        
        # Handle OpenAI ChatCompletion response
        if hasattr(response, 'model'):
            response_dict['model'] = response.model
        
        if hasattr(response, 'choices') and response.choices:
            response_dict['choices'] = []
            for choice in response.choices:
                choice_dict = {}
                if hasattr(choice, 'message'):
                    choice_dict['message'] = {
                        'role': getattr(choice.message, 'role', None),
                        'content': getattr(choice.message, 'content', None)
                    }
                if hasattr(choice, 'finish_reason'):
                    choice_dict['finish_reason'] = choice.finish_reason
                response_dict['choices'].append(choice_dict)
        
        if hasattr(response, 'usage'):
            usage = response.usage
            response_dict['usage'] = {
                'prompt_tokens': getattr(usage, 'prompt_tokens', None),
                'completion_tokens': getattr(usage, 'completion_tokens', None),
                'total_tokens': getattr(usage, 'total_tokens', None)
            }
        
        # Include deimos metadata if present
        if hasattr(response, '_deimos_metadata'):
            response_dict['_deimos_metadata'] = response._deimos_metadata
        
        # If we couldn't extract standard fields, try to convert the whole object
        if not response_dict:
            try:
                # Try to convert to dict if it has a dict method
                if hasattr(response, 'dict'):
                    response_dict = response.dict()
                elif hasattr(response, '__dict__'):
                    response_dict = response.__dict__.copy()
                else:
                    response_dict = {'raw_response': str(response)}
            except Exception:
                response_dict = {'raw_response': str(response)}
        
        return response_dict
    
    def _log_entry(self, entry: LogEntry) -> None:
        """Write the log entry to the backend.
        
        Args:
            entry: The log entry to write
        """
        try:
            self.backend.log_entry(entry)
        except Exception as e:
            # Don't let logging errors crash the main application
            print(f"Error logging entry: {e}", file=__import__('sys').stderr)
    
    def close(self) -> None:
        """Close the logger and clean up resources."""
        if self.backend:
            self.backend.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class _DummyLogEntry:
    """Dummy log entry for when logging is disabled."""
    
    def __init__(self):
        self.status = "disabled"
    
    def complete_success(self, *args, **kwargs):
        """No-op for disabled logging."""
        pass
    
    def complete_error(self, *args, **kwargs):
        """No-op for disabled logging."""
        pass


# Global logger instance
_global_logger: Optional[RequestLogger] = None


def get_logger() -> RequestLogger:
    """Get the global logger instance.
    
    Returns:
        The global RequestLogger instance
    """
    global _global_logger
    if _global_logger is None:
        # Initialize with configuration settings
        backend = None
        if config.logging_enabled:
            backend = JSONFileLogger(log_directory=config.log_directory)
        
        cost_calculator = CostCalculator(custom_pricing=config.custom_pricing)
        
        _global_logger = RequestLogger(
            backend=backend,
            cost_calculator=cost_calculator,
            enabled=config.logging_enabled
        )
    return _global_logger


def set_logger(logger: RequestLogger) -> None:
    """Set the global logger instance.
    
    Args:
        logger: The RequestLogger instance to use globally
    """
    global _global_logger
    _global_logger = logger


def configure_logging(
    enabled: bool = True,
    log_directory: str = "./logs",
    custom_pricing: Optional[Dict[str, Dict[str, float]]] = None
) -> RequestLogger:
    """Configure the global logger with common settings.
    
    Args:
        enabled: Whether logging is enabled
        log_directory: Directory for log files
        custom_pricing: Custom model pricing data
        
    Returns:
        The configured RequestLogger instance
    """
    backend = JSONFileLogger(log_directory=log_directory) if enabled else None
    cost_calculator = CostCalculator(custom_pricing=custom_pricing)
    
    logger = RequestLogger(
        backend=backend,
        cost_calculator=cost_calculator,
        enabled=enabled
    )
    
    set_logger(logger)
    return logger
