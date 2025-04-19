"""
Runtime Attribute Patching - Dynamically add missing attributes to objects
This module helps prevent AttributeError crashes by ensuring required methods exist
"""

import logging
import inspect
from typing import Any, Dict, Callable, Optional

logger = logging.getLogger(__name__)


def ensure_attribute_exists(obj: Any, attr_name: str, default_value: Any = None) -> bool:
    """
    Ensure an attribute exists on an object by adding it if it doesn't.
    
    Args:
        obj: The object to check
        attr_name: Name of the attribute to ensure exists
        default_value: Value to set if attribute doesn't exist
        
    Returns:
        True if attribute was added, False if it already existed
    """
    if not hasattr(obj, attr_name):
        setattr(obj, attr_name, default_value)
        return True
    return False


def ensure_method_exists(obj: Any, method_name: str, 
                         default_implementation: Optional[Callable] = None) -> bool:
    """
    Ensure a method exists on an object by adding it if it doesn't.
    
    Args:
        obj: The object to check
        method_name: Name of the method to ensure exists
        default_implementation: Function to use as the method implementation
        
    Returns:
        True if method was added, False if it already existed
    """
    if not hasattr(obj, method_name):
        if default_implementation is None:
            # Create a no-op function with the same name
            def noop_method(*args, **kwargs):
                method_obj = args[0].__class__.__name__
                logger.warning(f"Called missing method '{method_name}' on {method_obj}")
                return None
                
            default_implementation = noop_method
            
        setattr(obj, method_name, default_implementation.__get__(obj, obj.__class__))
        return True
    return False


def patch_plugin_manager(plugin_manager):
    """
    Add commonly missing attributes to the PluginManager class
    
    Args:
        plugin_manager: The plugin manager instance to patch
    """
    # Ensure error_handler attribute exists
    ensure_attribute_exists(plugin_manager, 'error_handler', None)
    
    # Add set_error_handler method if missing
    def set_error_handler_impl(self, handler_func):
        """Set a function to handle plugin errors"""
        self.error_handler = handler_func
        
    ensure_method_exists(plugin_manager, 'set_error_handler', set_error_handler_impl)
    
    # Add commonly used methods if they're missing
    critical_methods = {
        'discover_plugins': lambda self: [],
        'load_plugin': lambda self, plugin_name: False,
        'activate_plugin': lambda self, plugin_name: False,
        'deactivate_plugin': lambda self, plugin_name: False,
        'unload_plugin': lambda self, plugin_name: False,
        'unload_all_plugins': lambda self: None,
        'auto_load_plugins': lambda self: None,
    }
    
    for method_name, default_impl in critical_methods.items():
        ensure_method_exists(plugin_manager, method_name, default_impl)
    
    return plugin_manager
