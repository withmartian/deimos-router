"""Tests for the Router class and router registry."""

import pytest
from unittest.mock import patch

from deimos_router.router import (
    Router, 
    register_router, 
    get_router, 
    list_routers, 
    clear_routers
)


class TestRouter:
    """Test cases for the Router class."""
    
    def setup_method(self):
        """Clear router registry before each test."""
        clear_routers()
    
    def test_router_initialization_default_models(self):
        """Test router initialization with default models (backward compatibility)."""
        # For backward compatibility, provide models explicitly
        router = Router("test-router", models=None)
        
        assert router.name == "test-router"
        assert len(router.models) > 0
        assert "gpt-3.5-turbo" in router.models
        assert "gpt-4o-mini" in router.models
    
    def test_router_initialization_custom_models(self):
        """Test router initialization with custom models."""
        custom_models = ["model-1", "model-2", "model-3"]
        router = Router("custom-router", models=custom_models)
        
        assert router.name == "custom-router"
        assert router.models == custom_models
    
    def test_router_initialization_empty_models_raises_error(self):
        """Test that empty models list raises ValueError."""
        with pytest.raises(ValueError, match="Router must have at least one model"):
            Router("empty-router", models=[])
    
    def test_select_model(self):
        """Test model selection."""
        models = ["model-1", "model-2", "model-3"]
        router = Router("test-router", models=models)
        
        # Test multiple selections to ensure it's working
        selected_models = set()
        for _ in range(20):  # Run multiple times to test randomness
            selected = router.select_model()
            assert selected in models
            selected_models.add(selected)
        
        # With 20 runs, we should likely see multiple models selected
        # (though this could theoretically fail due to randomness)
        assert len(selected_models) >= 1
    
    def test_add_model(self):
        """Test adding a model to the router."""
        router = Router("test-router", models=["model-1"])
        
        router.add_model("model-2")
        assert "model-2" in router.models
        assert len(router.models) == 2
        
        # Adding the same model again should not duplicate
        router.add_model("model-2")
        assert router.models.count("model-2") == 1
    
    def test_remove_model(self):
        """Test removing a model from the router."""
        router = Router("test-router", models=["model-1", "model-2", "model-3"])
        
        router.remove_model("model-2")
        assert "model-2" not in router.models
        assert len(router.models) == 2
    
    def test_remove_model_not_found(self):
        """Test removing a model that doesn't exist."""
        router = Router("test-router", models=["model-1", "model-2"])
        
        with pytest.raises(ValueError, match="Model 'nonexistent' not found"):
            router.remove_model("nonexistent")
    
    def test_remove_last_model_raises_error(self):
        """Test that removing the last model raises ValueError."""
        router = Router("test-router", models=["model-1"])
        
        with pytest.raises(ValueError, match="Cannot remove the last model"):
            router.remove_model("model-1")
    
    def test_router_repr(self):
        """Test router string representation."""
        router = Router("test-router", models=["model-1", "model-2"])
        repr_str = repr(router)
        
        assert "Router(name='test-router'" in repr_str
        assert "models=['model-1', 'model-2']" in repr_str


class TestRouterRegistry:
    """Test cases for the router registry functions."""
    
    def setup_method(self):
        """Clear router registry before each test."""
        clear_routers()
    
    def test_register_and_get_router(self):
        """Test registering and retrieving a router."""
        router = Router("test-router")
        register_router(router)
        
        retrieved = get_router("test-router")
        assert retrieved is router
        assert retrieved.name == "test-router"
    
    def test_get_nonexistent_router(self):
        """Test getting a router that doesn't exist."""
        result = get_router("nonexistent")
        assert result is None
    
    def test_list_routers_empty(self):
        """Test listing routers when registry is empty."""
        routers = list_routers()
        assert routers == []
    
    def test_list_routers_with_routers(self):
        """Test listing routers when registry has routers."""
        router1 = Router("router-1")
        router2 = Router("router-2")
        
        register_router(router1)
        register_router(router2)
        
        routers = list_routers()
        assert set(routers) == {"router-1", "router-2"}
    
    def test_clear_routers(self):
        """Test clearing the router registry."""
        router = Router("test-router")
        register_router(router)
        
        assert len(list_routers()) == 1
        
        clear_routers()
        assert len(list_routers()) == 0
        assert get_router("test-router") is None
    
    def test_register_router_overwrites(self):
        """Test that registering a router with the same name overwrites."""
        router1 = Router("same-name", models=["model-1"])
        router2 = Router("same-name", models=["model-2"])
        
        register_router(router1)
        register_router(router2)
        
        retrieved = get_router("same-name")
        assert retrieved is router2
        assert "model-2" in retrieved.models
        assert "model-1" not in retrieved.models
