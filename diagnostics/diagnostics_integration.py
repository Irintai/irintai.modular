"""
Enhanced Diagnostics Integration Module

This module integrates the enhanced diagnostics functionality with the rest of the system,
particularly with the settings manager.
"""

import os
import sys
import importlib
import logging

# Setup logging
logger = logging.getLogger(__name__)

def integrate_with_settings_manager(settings_manager):
    """
    Integrate enhanced diagnostics with the settings manager
    
    Args:
        settings_manager: The settings manager instance
        
    Returns:
        bool: True if integration was successful, False otherwise
    """
    logger.info("Integrating enhanced diagnostics with settings manager...")
    
    try:
        # Register diagnostic settings
        settings_manager.update_setting("diagnostics.enabled", True)
        settings_manager.update_setting("diagnostics.log_level", "INFO")
        settings_manager.update_setting("diagnostics.auto_fix", False)
        settings_manager.update_setting("diagnostics.track_memory", True)
        
        # Setup diagnostic observers
        def on_log_level_change(value):
            logging.getLogger("diagnostics").setLevel(value)
            logger.info(f"Diagnostic log level changed to {value}")
        
        # Register the observer for log level changes
        settings_manager.register_observer("diagnostics.log_level", on_log_level_change)
        
        # Initialize with current setting
        current_level = settings_manager.get_setting("diagnostics.log_level", "INFO")
        log_level = getattr(logging, current_level, logging.INFO)
        logging.getLogger("diagnostics").setLevel(log_level)
        
        logger.info("Enhanced diagnostics successfully integrated with settings manager")
        return True
    except Exception as e:
        logger.error(f"Failed to integrate enhanced diagnostics with settings manager: {e}")
        return False

def setup_runtime_patching():
    """
    Set up runtime patching utilities if they don't exist
    
    Returns:
        tuple: (patch_plugin_manager, ensure_method_exists) functions or None if not available
    """
    try:
        # First try to import from utils
        from runtime_patching import patch_plugin_manager, ensure_method_exists
        logger.info("Using runtime patching utilities from utils.runtime_patching")
        return (patch_plugin_manager, ensure_method_exists)
    except ImportError:
        logger.warning("utils.runtime_patching not available, creating local implementation")
        
        # Create local implementation if import fails
        def ensure_attribute_exists(obj, attribute_name, default_value=None):
            """Ensure attribute exists on object"""
            if not hasattr(obj, attribute_name):
                setattr(obj, attribute_name, default_value)
                logger.warning(f"Added missing attribute '{attribute_name}' to {obj.__class__.__name__}")
        
        def ensure_method_exists(obj, method_name, default_impl=None):
            """Ensure method exists on object"""
            if not hasattr(obj, method_name):
                if default_impl is None:
                    def stub_method(*args, **kwargs):
                        class_name = obj.__class__.__name__
                        logger.warning(f"Called missing method '{method_name}' on {class_name}")
                        return None
                    
                    default_impl = stub_method
                
                setattr(obj, method_name, default_impl.__get__(obj, obj.__class__))
                logger.warning(f"Added missing method '{method_name}' to {obj.__class__.__name__}")
        
        def patch_plugin_manager(plugin_manager):
            """Patch plugin manager with required methods"""
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
            
            for method in required_methods:
                ensure_method_exists(plugin_manager, method)
            
            ensure_attribute_exists(plugin_manager, "plugins", {})
            ensure_attribute_exists(plugin_manager, "plugin_statuses", {})
            ensure_attribute_exists(plugin_manager, "plugin_dir", "plugins")
            ensure_attribute_exists(plugin_manager, "config_dir", "data/plugins")
            
            return plugin_manager
            
        return (patch_plugin_manager, ensure_method_exists)
