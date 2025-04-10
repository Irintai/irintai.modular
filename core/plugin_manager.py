"""
Plugin Manager - Handles discovery, loading, and lifecycle of plugins
"""
import os
import sys
import json
import importlib
import importlib.util
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Type

class PluginError(Exception):
    """Base exception for plugin-related errors"""
    pass

class PluginLoadError(PluginError):
    """Exception raised when a plugin fails to load"""
    pass

class PluginActivationError(PluginError):
    """Exception raised when a plugin fails to activate"""
    pass

class PluginConfigurationError(PluginError):
    """Exception raised when plugin configuration fails"""
    pass

class PluginManager:
    """Manages the discovery, loading, and lifecycle of plugins"""
    
    # Plugin status constants
    PLUGIN_STATUS = {
        "NOT_LOADED": "Not Loaded",
        "LOADING": "Loading...",
        "LOADED": "Loaded",
        "ACTIVE": "Active",
        "INACTIVE": "Inactive",
        "ERROR": "Error"
    }
    
    def __init__(
        self, 
        plugin_dir: str = "plugins",
        config_dir: str = "data/plugins",
        logger: Optional[Callable] = None,
        core_system: Any = None
    ):
        """
        Initialize the plugin manager
        
        Args:
            plugin_dir: Directory containing plugins
            config_dir: Directory for plugin configurations
            logger: Optional logging function
            core_system: Reference to the main application system
        """
        self.plugin_dir = plugin_dir
        self.config_dir = config_dir
        self.log = logger or print
        self.core_system = core_system
        
        # Plugin storage
        self.plugins: Dict[str, Any] = {}
        self.plugin_statuses: Dict[str, str] = {}
        self.plugin_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Ensure directories exist
        os.makedirs(self.plugin_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Add plugin directory to path if not already there
        if os.path.abspath(self.plugin_dir) not in sys.path:
            sys.path.append(os.path.abspath(self.plugin_dir))
            
        self.log(f"[Plugin Manager] Initialized with plugin directory: {self.plugin_dir}")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugin directory
        
        Returns:
            List of plugin names
        """
        discovered = []
        
        try:
            # Look for directories containing __init__.py
            for item in os.listdir(self.plugin_dir):
                item_path = os.path.join(self.plugin_dir, item)
                init_path = os.path.join(item_path, "__init__.py")
                
                if os.path.isdir(item_path) and os.path.exists(init_path):
                    discovered.append(item)
                    self.plugin_statuses[item] = self.PLUGIN_STATUS["NOT_LOADED"]
                    self.log(f"[Plugin Discovery] Found plugin: {item}")
        except Exception as e:
            self.log(f"[Plugin Error] Discovery failed: {e}")
            
        return discovered
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a specific plugin
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            True if plugin loaded successfully, False otherwise
        """
        with self._lock:
            # Check if plugin exists
            plugin_path = os.path.join(self.plugin_dir, plugin_name)
            init_path = os.path.join(plugin_path, "__init__.py")
            
            if not os.path.exists(init_path):
                self.log(f"[Plugin Error] Plugin not found: {plugin_name}")
                self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["ERROR"]
                return False
                
            # Update status
            self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["LOADING"]
            
            try:
                # Import the plugin module
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{plugin_name}", 
                    init_path
                )
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load spec for {plugin_name}")
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check for required plugin class
                if not hasattr(module, "IrintaiPlugin"):
                    raise PluginLoadError(f"Missing IrintaiPlugin class in {plugin_name}")
                
                # Get plugin class
                plugin_class = getattr(module, "IrintaiPlugin")
                
                # Extract and validate metadata
                if not hasattr(plugin_class, "METADATA"):
                    raise PluginLoadError(f"Missing METADATA in {plugin_name}")
                    
                metadata = getattr(plugin_class, "METADATA")
                self.plugin_metadata[plugin_name] = metadata
                
                # Create config path for this plugin
                plugin_config_dir = os.path.join(self.config_dir, plugin_name)
                os.makedirs(plugin_config_dir, exist_ok=True)
                config_path = os.path.join(plugin_config_dir, "config.json")
                
                # Initialize plugin instance
                plugin_instance = plugin_class(
                    core_system=self.core_system,
                    config_path=config_path,
                    logger=self.log
                )
                
                # Store the plugin instance
                self.plugins[plugin_name] = plugin_instance
                
                # Update status
                self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["LOADED"]
                self.log(f"[Plugin] Loaded: {plugin_name}")
                
                return True
                
            except Exception as e:
                self.log(f"[Plugin Error] Failed to load {plugin_name}: {e}")
                self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["ERROR"]
                return False
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """
        Discover and load all available plugins
        
        Returns:
            Dictionary mapping plugin names to load success status
        """
        plugins = self.discover_plugins()
        results = {}
        
        for plugin in plugins:
            results[plugin] = self.load_plugin(plugin)
            
        return results
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Activate a loaded plugin
        
        Args:
            plugin_name: Name of the plugin to activate
            
        Returns:
            True if plugin activated successfully, False otherwise
        """
        with self._lock:
            # Check if plugin is loaded
            if plugin_name not in self.plugins:
                self.log(f"[Plugin Error] Cannot activate unloaded plugin: {plugin_name}")
                return False
                
            # Get the plugin instance
            plugin = self.plugins[plugin_name]
            
            try:
                # Call plugin's activate method
                if hasattr(plugin, "activate") and callable(plugin.activate):
                    result = plugin.activate()
                    
                    if result:
                        self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["ACTIVE"]
                        self.log(f"[Plugin] Activated: {plugin_name}")
                    else:
                        self.log(f"[Plugin Warning] Activation returned False: {plugin_name}")
                        return False
                else:
                    # No explicit activation method, just mark as active
                    self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["ACTIVE"]
                    self.log(f"[Plugin] Set active: {plugin_name}")
                
                return True
                
            except Exception as e:
                self.log(f"[Plugin Error] Activation failed for {plugin_name}: {e}")
                self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["ERROR"]
                return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Deactivate an active plugin
        
        Args:
            plugin_name: Name of the plugin to deactivate
            
        Returns:
            True if plugin deactivated successfully, False otherwise
        """
        with self._lock:
            # Check if plugin is loaded
            if plugin_name not in self.plugins:
                self.log(f"[Plugin Error] Cannot deactivate unloaded plugin: {plugin_name}")
                return False
                
            # Get the plugin instance
            plugin = self.plugins[plugin_name]
            
            try:
                # Call plugin's deactivate method
                if hasattr(plugin, "deactivate") and callable(plugin.deactivate):
                    result = plugin.deactivate()
                    
                    if result:
                        self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["INACTIVE"]
                        self.log(f"[Plugin] Deactivated: {plugin_name}")
                    else:
                        self.log(f"[Plugin Warning] Deactivation returned False: {plugin_name}")
                        return False
                else:
                    # No explicit deactivation method, just mark as inactive
                    self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["INACTIVE"]
                    self.log(f"[Plugin] Set inactive: {plugin_name}")
                
                return True
                
            except Exception as e:
                self.log(f"[Plugin Error] Deactivation failed for {plugin_name}: {e}")
                self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["ERROR"]
                return False
    
    def get_plugin_status(self, plugin_name: str) -> str:
        """
        Get the current status of a plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Current plugin status
        """
        return self.plugin_statuses.get(plugin_name, self.PLUGIN_STATUS["NOT_LOADED"])
    
    def get_plugin_metadata(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin metadata dictionary
        """
        return self.plugin_metadata.get(plugin_name, {})
    
    def get_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all plugins
        
        Returns:
            Dictionary mapping plugin names to info dictionaries
        """
        result = {}
        
        for plugin_name in self.plugin_statuses:
            metadata = self.get_plugin_metadata(plugin_name)
            status = self.get_plugin_status(plugin_name)
            
            result[plugin_name] = {
                "name": plugin_name,
                "status": status,
                "version": metadata.get("version", "Unknown"),
                "description": metadata.get("description", "No description"),
                "author": metadata.get("author", "Unknown")
            }
            
        return result
    
    def update_plugin_configuration(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """
        Update configuration for a specific plugin
        
        Args:
            plugin_name: Name of the plugin
            config: Configuration dictionary
            
        Returns:
            True if configuration updated successfully, False otherwise
        """
        with self._lock:
            # Check if plugin is loaded
            if plugin_name not in self.plugins:
                self.log(f"[Plugin Error] Cannot configure unloaded plugin: {plugin_name}")
                return False
                
            # Get the plugin instance
            plugin = self.plugins[plugin_name]
            
            try:
                # Call plugin's update_configuration method
                if hasattr(plugin, "update_configuration") and callable(plugin.update_configuration):
                    result = plugin.update_configuration(**config)
                    
                    if result:
                        self.log(f"[Plugin] Configuration updated: {plugin_name}")
                        return True
                    else:
                        self.log(f"[Plugin Warning] Configuration update failed: {plugin_name}")
                        return False
                else:
                    self.log(f"[Plugin Warning] No configuration update method: {plugin_name}")
                    return False
                    
            except Exception as e:
                self.log(f"[Plugin Error] Configuration update failed for {plugin_name}: {e}")
                return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin (deactivate, unload, load, activate)
        
        Args:
            plugin_name: Name of the plugin to reload
            
        Returns:
            True if plugin reloaded successfully, False otherwise
        """
        with self._lock:
            # Check if plugin was active
            was_active = self.plugin_statuses.get(plugin_name) == self.PLUGIN_STATUS["ACTIVE"]
            
            # Deactivate if active
            if was_active:
                if not self.deactivate_plugin(plugin_name):
                    return False
                    
            # Remove from loaded plugins
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
                
            # Mark as not loaded
            self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["NOT_LOADED"]
            
            # Reload
            if not self.load_plugin(plugin_name):
                return False
                
            # Reactivate if it was active
            if was_active:
                return self.activate_plugin(plugin_name)
                
            return True
    
    def call_plugin_method(self, plugin_name: str, method_name: str, *args, **kwargs) -> Any:
        """
        Call a method on a loaded plugin
        
        Args:
            plugin_name: Name of the plugin
            method_name: Name of the method to call
            *args: Positional arguments to pass
            **kwargs: Keyword arguments to pass
            
        Returns:
            Result of the method call
        
        Raises:
            PluginError: If the plugin or method doesn't exist
        """
        with self._lock:
            # Check if plugin is loaded
            if plugin_name not in self.plugins:
                raise PluginError(f"Plugin not loaded: {plugin_name}")
                
            # Get the plugin instance
            plugin = self.plugins[plugin_name]
            
            # Check if method exists
            if not hasattr(plugin, method_name) or not callable(getattr(plugin, method_name)):
                raise PluginError(f"Method {method_name} not found in plugin {plugin_name}")
                
            # Call the method
            try:
                method = getattr(plugin, method_name)
                return method(*args, **kwargs)
            except Exception as e:
                self.log(f"[Plugin Error] Method call failed: {plugin_name}.{method_name}: {e}")
                raise