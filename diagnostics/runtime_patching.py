"""
Runtime Patching Utilities

This module provides utility functions for runtime patching of objects
to prevent AttributeError crashes and improve system resilience.
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

def ensure_attribute_exists(obj: Any, attribute_name: str, default_value: Any = None) -> None:
    """
    Ensure that an object has a specified attribute, adding it with a default value if missing.
    
    Args:
        obj: Object to check
        attribute_name: Name of the attribute to ensure
        default_value: Value to set if attribute doesn't exist
    """
    if not hasattr(obj, attribute_name):
        setattr(obj, attribute_name, default_value)
        logger.warning(f"Added missing attribute '{attribute_name}' to {obj.__class__.__name__}")

def ensure_method_exists(obj: Any, method_name: str, default_impl: Optional[Callable] = None) -> None:
    """
    Ensure that an object has a specified method, adding a default implementation if missing.
    
    Args:
        obj: Object to check
        method_name: Name of the method to ensure
        default_impl: Function to use as default implementation if method doesn't exist.
                     If None, a stub function that logs the call will be used.
    """
    if not hasattr(obj, method_name):
        if default_impl is None:
            # Create a stub method that just logs the call
            def stub_method(*args, **kwargs):
                class_name = obj.__class__.__name__
                logger.warning(f"Called missing method '{method_name}' on {class_name}")
                return None
            
            default_impl = stub_method
            
        # Add the method to the object
        setattr(obj, method_name, default_impl.__get__(obj, obj.__class__))
        logger.warning(f"Added missing method '{method_name}' to {obj.__class__.__name__}")

def patch_plugin_manager(plugin_manager):
    """
    Patch the plugin manager to ensure all required methods exist.
    
    Args:
        plugin_manager: The plugin manager instance to patch
        
    Returns:
        The patched plugin manager instance
    """
    # Define required methods and their default implementations
    required_methods = [
        "set_error_handler",
        "discover_plugins",
        "load_plugin", 
        "activate_plugin", 
        "deactivate_plugin",
        "unload_plugin",
        "unload_all_plugins",
        "auto_load_plugins",
        "get_plugin_metadata",
        "get_all_plugins",
        "reload_plugin"
    ]
    
    # Ensure each required method exists
    for method in required_methods:
        ensure_method_exists(plugin_manager, method)
    
    # Ensure required attributes exist
    ensure_attribute_exists(plugin_manager, "plugins", {})
    ensure_attribute_exists(plugin_manager, "plugin_statuses", {})
    ensure_attribute_exists(plugin_manager, "plugin_dir", "plugins")
    ensure_attribute_exists(plugin_manager, "config_dir", "data/plugins")
    
    return plugin_manager
