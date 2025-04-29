"""
Plugin SDK for IrintAI Assistant
Provides helpers and utilities for plugin development
"""
from typing import Dict, Any, Callable, List, Optional, Union
import os
import json
import importlib
import inspect


class PluginSDK:
    """SDK for IrintAI Assistant plugin development"""
    
    def __init__(self, plugin_id: str, core_system: Any):
        """
        Initialize the Plugin SDK
        
        Args:
            plugin_id: Unique plugin identifier
            core_system: Core system instance
        """
        self.plugin_id = plugin_id
        self.core_system = core_system
        self.logger = getattr(core_system, 'logger', None)
        
        # Cache for service lookups
        self._service_cache = {}
        
        # Initialize sandboxed file operations
        self.file_ops = None
        if hasattr(core_system, 'file_ops'):
            from file_operations.file_ops import PluginSandboxedFileOps
            self.file_ops = PluginSandboxedFileOps(
                core_system.file_ops, 
                plugin_id, 
                base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                logger=self.log
            )
        
    def log(self, message: str, level: str = "INFO") -> None:
        if self.logger and hasattr(self.logger, 'log'):
            self.logger.log(f"[Plugin: {self.plugin_id}] {message}", level)
        else:
            print(f"[Plugin: {self.plugin_id}] [{level}] {message}")
            
    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get a service from the core system
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance or None if not found
        """
        # Check cache first
        if service_name in self._service_cache:
            return self._service_cache[service_name]
            
        # Try to get service from plugin manager
        if hasattr(self.core_system, 'plugin_manager'):
            service = self.core_system.plugin_manager.get_service(service_name)
            if service:
                self._service_cache[service_name] = service
                return service
                
        # Try direct access from core system
        if hasattr(self.core_system, service_name):
            service = getattr(self.core_system, service_name)
            self._service_cache[service_name] = service
            return service
            
        return None
        
    def register_event_handler(self, event_name: str, handler: Callable) -> bool:
        """
        Register an event handler
        
        Args:
            event_name: Name of the event to handle
            handler: Callback function for the event
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not hasattr(self.core_system, 'plugin_manager'):
            self.log("Plugin manager not available, can't register event handler", "WARNING")
            return False
            
        return self.core_system.plugin_manager.register_event_handler(
            self.plugin_id, event_name, handler
        )
        
    def emit_event(self, event_name: str, *args, **kwargs) -> None:
        """
        Emit an event for other plugins or the core system
        
        Args:
            event_name: Name of the event to emit
            *args: Positional arguments for the event
            **kwargs: Keyword arguments for the event
        """
        if not hasattr(self.core_system, 'plugin_manager'):
            self.log("Plugin manager not available, can't emit event", "WARNING")
            return
            
        self.core_system.plugin_manager.emit_event(
            f"{self.plugin_id}.{event_name}", *args, **kwargs
        )
        
    def get_plugin_data_dir(self) -> str:
        """
        Get the plugin data directory path
        
        Returns:
            Path to the plugin data directory
        """
        # Get base plugin data directory from config
        config_manager = self.get_service('config_manager')
        if config_manager:
            base_dir = config_manager.get('plugin_data_dir', 'plugin_data')
        else:
            base_dir = 'plugin_data'
            
        # Create plugin-specific directory
        plugin_dir = os.path.join(base_dir, self.plugin_id)
        os.makedirs(plugin_dir, exist_ok=True)
        
        return plugin_dir
        
    def save_data(self, data: Dict[str, Any], filename: str = 'plugin_data.json') -> bool:
        """
        Save plugin data to a JSON file
        
        Args:
            data: Dictionary of data to save
            filename: Filename to save to
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            plugin_dir = self.get_plugin_data_dir()
            filepath = os.path.join(plugin_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            self.log(f"Failed to save plugin data: {e}", "ERROR")
            return False
            
    def load_data(self, filename: str = 'plugin_data.json', default: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load plugin data from a JSON file
        
        Args:
            filename: Filename to load from
            default: Default data to return if file doesn't exist
            
        Returns:
            Dictionary of loaded data
        """
        try:
            plugin_dir = self.get_plugin_data_dir()
            filepath = os.path.join(plugin_dir, filename)
            
            if not os.path.exists(filepath):
                return default or {}
                
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.log(f"Failed to load plugin data: {e}", "ERROR")
            return default or {}
            
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """
        Get plugin configuration
        
        Args:
            key: Specific config key to retrieve
            default: Default value to return if key doesn't exist
            
        Returns:
            Plugin configuration value
        """
        config_manager = self.get_service('config_manager')
        if not config_manager:
            return default
            
        # Get plugin-specific config
        plugin_config = config_manager.get(f"plugins.{self.plugin_id}", {})
        
        # Return specific key or full config
        if key is not None:
            return plugin_config.get(key, default)
        return plugin_config
            
    def set_config(self, key: str, value: Any) -> bool:
        """
        Set plugin configuration
        
        Args:
            key: Config key to set
            value: Config value
            
        Returns:
            True if setting was successful, False otherwise
        """
        config_manager = self.get_service('config_manager')
        if not config_manager:
            return False
            
        # Set plugin-specific config
        plugin_config_key = f"plugins.{self.plugin_id}.{key}"
        config_manager.set(plugin_config_key, value)
        
        # Save the config
        return config_manager.save_config()
        
    def register_model_hook(self, hook_type: str, callback: Callable) -> bool:
        """
        Register a hook for model processing
        
        Args:
            hook_type: Type of hook (pre_process, post_process, etc.)
            callback: Hook callback function
            
        Returns:
            True if registration was successful, False otherwise
        """
        chat_engine = self.get_service('chat_engine')
        if not chat_engine or not hasattr(chat_engine, 'register_hook'):
            self.log(f"Failed to register model hook: chat engine not available", "WARNING")
            return False
            
        try:
            chat_engine.register_hook(f"{self.plugin_id}.{hook_type}", hook_type, callback)
            return True
        except Exception as e:
            self.log(f"Failed to register model hook: {e}", "ERROR")
            return False
            
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage information
        
        Returns:
            Dictionary of resource usage metrics
        """
        system_monitor = self.get_service('system_monitor')
        if not system_monitor:
            return {}
            
        return system_monitor.get_system_stats()
        
    def get_active_plugins(self) -> List[str]:
        """
        Get list of active plugins
        
        Returns:
            List of active plugin IDs
        """
        if hasattr(self.core_system, 'plugin_manager'):
            active_plugins = self.core_system.plugin_manager.get_active_plugins()
            return list(active_plugins.keys())
        return []
        
    def call_plugin_method(self, plugin_id: str, method_name: str, *args, **kwargs) -> Optional[Any]:
        """
        Call a method on another plugin
        
        Args:
            plugin_id: ID of the plugin to call
            method_name: Name of the method to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Return value from the plugin method or None if failed
        """
        if not hasattr(self.core_system, 'plugin_manager'):
            self.log("Plugin manager not available, can't call plugin method", "WARNING")
            return None
            
        # Get the plugin instance
        plugin = self.core_system.plugin_manager.get_plugin_instance(plugin_id)
        if not plugin:
            self.log(f"Plugin {plugin_id} not found", "WARNING")
            return None
            
        # Check if method exists
        if not hasattr(plugin, method_name) or not callable(getattr(plugin, method_name)):
            self.log(f"Method {method_name} not found in plugin {plugin_id}", "WARNING")
            return None
            
        # Call the method
        try:
            method = getattr(plugin, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            self.log(f"Error calling {plugin_id}.{method_name}: {e}", "ERROR")
            return None
            
    def create_ui_component(self, parent, component_type: str, **kwargs) -> Any:
        """
        Create a UI component
        
        Args:
            parent: Parent widget
            component_type: Type of component (Frame, Label, etc.)
            **kwargs: Component options
            
        Returns:
            Created UI component
        """
        import tkinter as tk
        from tkinter import ttk
        
        # Map component types to their constructors
        component_map = {
            # Tkinter components
            'Frame': tk.Frame,
            'Label': tk.Label,
            'Button': tk.Button,
            'Entry': tk.Entry,
            'Text': tk.Text,
            'Checkbutton': tk.Checkbutton,
            'Radiobutton': tk.Radiobutton,
            'Scale': tk.Scale,
            'Listbox': tk.Listbox,
            'Scrollbar': tk.Scrollbar,
            'Menu': tk.Menu,
            'Menubutton': tk.Menubutton,
            'Canvas': tk.Canvas,
            
            # TTK components
            'TFrame': ttk.Frame,
            'TLabel': ttk.Label,
            'TButton': ttk.Button,
            'TEntry': ttk.Entry,
            'TCheckbutton': ttk.Checkbutton,
            'TRadiobutton': ttk.Radiobutton,
            'TScale': ttk.Scale,
            'Combobox': ttk.Combobox,
            'Notebook': ttk.Notebook,
            'Treeview': ttk.Treeview,
            'Scrollbar': ttk.Scrollbar,
            'Progressbar': ttk.Progressbar,
            'Separator': ttk.Separator,
            'Sizegrip': ttk.Sizegrip
        }
        
        # Get the component constructor
        constructor = component_map.get(component_type)
        if not constructor:
            self.log(f"Unknown component type: {component_type}", "WARNING")
            return None
            
        # Create and return the component
        try:
            return constructor(parent, **kwargs)
        except Exception as e:
            self.log(f"Error creating component {component_type}: {e}", "ERROR")
            return None
        
    def register_metric(self, metric_id: str, get_value_func: Callable[[], Any],
                      name: str, description: str, format_type: str = "numeric",
                      unit: str = "") -> bool:
        """
        Register a custom metric with the resource monitoring system
        
        Args:
            metric_id: Identifier for the metric
            get_value_func: Function that returns the current metric value
            name: Display name for the metric
            description: Description of the metric
            format_type: Format type (percentage, numeric, text)
            unit: Unit for numeric metrics
            
        Returns:
            True if registration was successful
        """
        system_monitor = self.get_service('system_monitor')
        if not system_monitor:
            self.log("System monitor not available", "WARNING")
            return False
            
        metadata = {
            "name": name,
            "description": description,
            "format": format_type
        }
        
        if format_type == "numeric" and unit:
            metadata["unit"] = unit
            
        return system_monitor.register_plugin_metric(
            self.plugin_id, metric_id, get_value_func, metadata
        )
        
    def unregister_metric(self, metric_id: str) -> bool:
        """
        Unregister a custom metric
        
        Args:
            metric_id: Identifier for the metric
            
        Returns:
            True if unregistration was successful
        """
        system_monitor = self.get_service('system_monitor')
        if not system_monitor:
            return False
            
        return system_monitor.unregister_plugin_metric(self.plugin_id, metric_id)
        
    def register_process(self, process_id: int, name: str = None) -> bool:
        """
        Register a process for monitoring
        
        Args:
            process_id: Process ID
            name: Optional process name
            
        Returns:
            True if registration was successful
        """
        system_monitor = self.get_service('system_monitor')
        if not system_monitor:
            self.log("System monitor not available", "WARNING")
            return False
            
        return system_monitor.register_monitored_process(self.plugin_id, process_id, name)
        
    def unregister_process(self, process_id: int) -> bool:
        """
        Unregister a monitored process
        
        Args:
            process_id: Process ID
            
        Returns:
            True if unregistration was successful
        """
        system_monitor = self.get_service('system_monitor')
        if not system_monitor:
            return False
            
        return system_monitor.unregister_monitored_process(self.plugin_id, process_id)
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics
        
        Returns:
            Dictionary of system metrics
        """
        system_monitor = self.get_service('system_monitor')
        if not system_monitor:
            return {}
            
        return system_monitor.get_system_info()


# Helper function to create plugin class template
def create_plugin_template(plugin_name: str, description: str, author: str) -> str:
    """
    Create a plugin class template
    
    Args:
        plugin_name: Name of the plugin
        description: Plugin description
        author: Plugin author
        
    Returns:
        Template string for the plugin class
    """
    plugin_id = plugin_name.lower().replace(' ', '_')
    
    template = f'''"""
{plugin_name} plugin for IrintAI Assistant

A plugin that {description.lower()}
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, List, Optional

class IrintaiPlugin:
    def __init__(self, plugin_id, core_system):
        self.plugin_id = plugin_id
        self.core_system = core_system
        self.log = core_system.logger.log if hasattr(core_system, "logger") else print
        
    def activate(self):
        """Activate the plugin"""
        self.log(f"{plugin_name} Plugin activated")
        return True
        
    def deactivate(self):
        """Deactivate the plugin"""
        self.log(f"{plugin_name} Plugin deactivated")
        return True
        
    def get_actions(self):
        """
        Get plugin actions for the UI menu
        
        Returns:
            Dictionary of action names and callbacks
        """
        return {{
            "Example Action": self.example_action
        }}
        
    def example_action(self):
        """Example plugin action"""
        self.log(f"Example action from {plugin_name}")


# Plugin metadata
plugin_info = {{
    "name": "{plugin_name}",
    "description": "{description}",
    "version": "1.0.0",
    "author": "{author}",
    "url": "https://example.com/plugins/{plugin_id}",
    "plugin_class": IrintaiPlugin,
    "compatibility": "0.5.0",
    "tags": ["example", "template"]
}}
'''
    return template

if __name__ != "__main__":
    __all__ = ["IrintaiPlugin"]  # Export the plugin class for external use
