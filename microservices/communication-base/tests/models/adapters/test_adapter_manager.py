"""
Tests for the AdapterManager class.

This module contains unit tests for the AdapterManager class, which manages
adapter activation and model integration.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.models.adapters.adapter_manager import AdapterManager, AdapterActivationError
from src.models.adapters.adapter_registry import AdapterRegistry
from src.models.adapters.base_adapter import BaseAdapter


class MockAdapter(BaseAdapter):
    """Mock adapter for testing."""
    
    def __init__(self, name="mock", adapter_type="test", path=None, config=None):
        super().__init__(name=name, adapter_type=adapter_type, path=path, config=config or {})
        self._is_initialized = False
        self._is_loaded = False
        self.applied_models = set()
        
    def _initialize(self):
        self._is_initialized = True
        return True
        
    def _load(self):
        self._is_loaded = True
        return True
        
    def _unload(self):
        self._is_loaded = False
        return True
        
    def apply_to_model(self, model, config=None):
        model_id = str(id(model))
        self.applied_models.add(model_id)
        return True
        
    def remove_from_model(self, model):
        model_id = str(id(model))
        if model_id in self.applied_models:
            self.applied_models.remove(model_id)
        return True


class TestAdapterManager(unittest.TestCase):
    """Test cases for the AdapterManager class."""
    
    def setUp(self):
        """Set up test fixtures, if any."""
        # Clear the registry singleton
        registry = AdapterRegistry.get_instance()
        registry.clear()
        
        # Reset the manager singleton
        manager = AdapterManager()
        manager._active_adapters = {}
        manager._managed_models = {}
        
        # Create mock adapters
        self.sales_adapter = MockAdapter(name="sales", adapter_type="sales")
        self.support_adapter = MockAdapter(name="support", adapter_type="support")
        self.hypnosis_adapter = MockAdapter(name="hypnosis", adapter_type="persuasion")
        
        # Register adapters
        registry.register_adapter(self.sales_adapter)
        registry.register_adapter(self.support_adapter)
        registry.register_adapter(self.hypnosis_adapter)
        
        # Create a mock model
        self.model = MagicMock()
        self.model.name = "test_model"
        
    def test_get_instance(self):
        """Test that get_instance returns the same instance."""
        manager1 = AdapterManager()
        manager2 = AdapterManager.get_instance()
        
        self.assertIs(manager1, manager2, "Should return the same instance")
        
    def test_get_adapter(self):
        """Test getting an adapter by name."""
        manager = AdapterManager.get_instance()
        
        adapter = manager.get_adapter("sales")
        self.assertIs(adapter, self.sales_adapter, "Should return the correct adapter")
        
        adapter = manager.get_adapter("nonexistent")
        self.assertIsNone(adapter, "Should return None for nonexistent adapter")
        
    def test_get_adapters_for_bot(self):
        """Test getting adapters for different bot types."""
        manager = AdapterManager.get_instance()
        
        # Test sales bot
        adapters = manager.get_adapters_for_bot("sales")
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].name, "sales")
        
        # Test support bot
        adapters = manager.get_adapters_for_bot("support")
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].name, "support")
        
        # Test consultancy bot
        adapters = manager.get_adapters_for_bot("consultancy")
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].name, "hypnosis")
        
        # Test nonexistent bot type
        adapters = manager.get_adapters_for_bot("nonexistent")
        self.assertEqual(len(adapters), 0)
    
    def test_activate_adapter(self):
        """Test activating an adapter."""
        manager = AdapterManager.get_instance()
        
        # Test successful activation
        result = manager.activate_adapter(self.model, "sales")
        self.assertTrue(result, "Activation should succeed")
        self.assertTrue(manager.is_adapter_active(self.model, "sales"), 
                       "Adapter should be marked as active")
                       
        # Test activating nonexistent adapter
        with self.assertRaises(AdapterActivationError):
            manager.activate_adapter(self.model, "nonexistent")
    
    def test_deactivate_adapter(self):
        """Test deactivating an adapter."""
        manager = AdapterManager.get_instance()
        
        # Activate an adapter first
        manager.activate_adapter(self.model, "sales")
        self.assertTrue(manager.is_adapter_active(self.model, "sales"))
        
        # Test deactivation
        result = manager.deactivate_adapter(self.model, "sales")
        self.assertTrue(result, "Deactivation should succeed")
        self.assertFalse(manager.is_adapter_active(self.model, "sales"), 
                        "Adapter should be marked as inactive")
                        
        # Test deactivating nonexistent adapter
        result = manager.deactivate_adapter(self.model, "nonexistent")
        self.assertFalse(result, "Deactivation of nonexistent adapter should fail")
    
    def test_switch_adapter(self):
        """Test switching between adapters."""
        manager = AdapterManager.get_instance()
        
        # Activate first adapter
        manager.activate_adapter(self.model, "sales")
        self.assertTrue(manager.is_adapter_active(self.model, "sales"))
        
        # Switch to second adapter
        result = manager.switch_adapter(self.model, "support")
        self.assertTrue(result, "Switch should succeed")
        self.assertFalse(manager.is_adapter_active(self.model, "sales"), 
                        "First adapter should be deactivated")
        self.assertTrue(manager.is_adapter_active(self.model, "support"), 
                       "Second adapter should be activated")
    
    def test_activate_adapters_for_bot(self):
        """Test activating all adapters for a bot type."""
        manager = AdapterManager.get_instance()
        
        # Register another adapter for sales
        extra_sales = MockAdapter(name="premium_sales", adapter_type="sales")
        AdapterRegistry.get_instance().register_adapter(extra_sales)
        
        # Activate adapters for sales bot
        activated = manager.activate_adapters_for_bot(self.model, "sales")
        self.assertEqual(len(activated), 2, "Should activate two adapters")
        self.assertIn("sales", activated)
        self.assertIn("premium_sales", activated)
        
        # Verify both are active
        self.assertTrue(manager.is_adapter_active(self.model, "sales"))
        self.assertTrue(manager.is_adapter_active(self.model, "premium_sales"))
    
    def test_deactivate_all_adapters(self):
        """Test deactivating all adapters."""
        manager = AdapterManager.get_instance()
        
        # Activate multiple adapters
        manager.activate_adapter(self.model, "sales")
        manager.activate_adapter(self.model, "support")
        
        # Verify they are active
        self.assertEqual(len(manager.get_active_adapters(self.model)), 2)
        
        # Deactivate all
        result = manager.deactivate_all_adapters(self.model)
        self.assertTrue(result, "Deactivation should succeed")
        self.assertEqual(len(manager.get_active_adapters(self.model)), 0, 
                        "No adapters should be active")
    
    def test_get_active_adapters(self):
        """Test getting active adapters for a model."""
        manager = AdapterManager.get_instance()
        
        # Initially no active adapters
        adapters = manager.get_active_adapters(self.model)
        self.assertEqual(len(adapters), 0)
        
        # Activate an adapter
        manager.activate_adapter(self.model, "sales")
        
        # Check active adapters
        adapters = manager.get_active_adapters(self.model)
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0], "sales")
        
        # Activate another adapter
        manager.activate_adapter(self.model, "support")
        
        # Check active adapters again
        adapters = manager.get_active_adapters(self.model)
        self.assertEqual(len(adapters), 2)
        self.assertIn("sales", adapters)
        self.assertIn("support", adapters)


if __name__ == '__main__':
    unittest.main() 