"""Base classes for the logging system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class LogEntry:
    """Represents a complete log entry for a request/response cycle."""
    
    # Request identification
    timestamp: datetime
    request_id: str
    
    # Routing information
    router_name: Optional[str]
    selected_model: str
    routing_explanation: List[Dict[str, Any]]
    
    # Request/Response data
    request: Dict[str, Any]
    response: Optional[Dict[str, Any]]
    
    # Performance metrics
    latency_ms: Optional[float]
    
    # Token usage
    tokens: Optional[Dict[str, int]]  # {"prompt": 100, "completion": 50, "total": 150}
    
    # Cost information
    cost: Optional[float]
    cost_estimated: bool
    cost_source: str  # "api_response", "token_calculation", "unknown"
    
    # Status
    status: str  # "success", "error", "timeout", etc.
    error_message: Optional[str] = None
    
    @classmethod
    def create_request_entry(
        cls,
        router_name: Optional[str],
        selected_model: str,
        routing_explanation: List[Dict[str, Any]],
        request: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> 'LogEntry':
        """Create a log entry for the start of a request."""
        return cls(
            timestamp=datetime.utcnow(),
            request_id=request_id or str(uuid.uuid4()),
            router_name=router_name,
            selected_model=selected_model,
            routing_explanation=routing_explanation,
            request=request,
            response=None,
            latency_ms=None,
            tokens=None,
            cost=None,
            cost_estimated=True,
            cost_source="unknown",
            status="pending"
        )
    
    def complete_success(
        self,
        response: Dict[str, Any],
        latency_ms: float,
        tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
        cost_estimated: bool = True,
        cost_source: str = "unknown"
    ) -> None:
        """Complete the log entry with successful response data."""
        self.response = response
        self.latency_ms = latency_ms
        self.tokens = tokens
        self.cost = cost
        self.cost_estimated = cost_estimated
        self.cost_source = cost_source
        self.status = "success"
    
    def complete_error(
        self,
        error_message: str,
        latency_ms: Optional[float] = None
    ) -> None:
        """Complete the log entry with error information."""
        self.error_message = error_message
        self.latency_ms = latency_ms
        self.status = "error"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the log entry to a dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat() + "Z",
            "request_id": self.request_id,
            "router_name": self.router_name,
            "selected_model": self.selected_model,
            "routing_explanation": self.routing_explanation,
            "request": self.request,
            "response": self.response,
            "latency_ms": self.latency_ms,
            "tokens": self.tokens,
            "cost": self.cost,
            "cost_estimated": self.cost_estimated,
            "cost_source": self.cost_source,
            "status": self.status,
            "error_message": self.error_message
        }


class LoggerBackend(ABC):
    """Abstract base class for logging backends."""
    
    @abstractmethod
    def log_entry(self, entry: LogEntry) -> None:
        """Log a complete entry.
        
        Args:
            entry: The log entry to write
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the logger and clean up resources."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
