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
from utils.version import VERSION

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
        self.error_handler = None
        
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
    
    def set_error_handler(self, handler_func):
        """
        Set a callback function to handle plugin errors
        
        Args:
            handler_func: Function that takes (plugin_name, error_message) parameters
        """
        self.error_handler = handler_func
    
    def unload_plugin(self, plugin_name):
        """
        Unload a specific plugin from memory

        Args:
            plugin_name (str): Name of the plugin to unload
            
        Returns:
            bool: True if plugin was unloaded successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            self.log(f"[Plugin] Cannot unload '{plugin_name}': plugin not found")
            return False
            
        # Deactivate first if active
        if self.plugin_statuses.get(plugin_name) == self.PLUGIN_STATUS["ACTIVE"]:
            self.deactivate_plugin(plugin_name)
        
        # Remove from plugins dict
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            
        # Update status
        self.plugin_statuses[plugin_name] = self.PLUGIN_STATUS["NOT_LOADED"]
        
        self.log(f"[Plugin] Unloaded plugin: {plugin_name}")
        return True
    
    def unload_all_plugins(self):
        """
        Unload all plugins from memory
        
        Returns:
            int: Number of plugins unloaded
        """
        plugin_names = list(self.plugins.keys())
        count = 0
        
        for plugin_name in plugin_names:
            if self.unload_plugin(plugin_name):
                count += 1
                
        self.log(f"[Plugin] Unloaded {count} plugins")
        return count
    
    def auto_load_plugins(self):
        """
        Automatically load and activate plugins marked for auto-loading
        
        Returns:
            int: Number of plugins auto-loaded
        """
        # Check if we have access to config_manager
        if not hasattr(self, 'core_system') or not self.core_system or 'config_manager' not in self.core_system:
            self.log("[Plugin] Cannot auto-load plugins: no access to config manager")
            return 0
            
        config_manager = self.core_system['config_manager']
        autoload_plugins = config_manager.get("autoload_plugins", [])
        
        if not autoload_plugins:
            self.log("[Plugin] No plugins marked for auto-loading")
            return 0
            
        self.log(f"[Plugin] Auto-loading {len(autoload_plugins)} plugins: {', '.join(autoload_plugins)}")
        
        # First discover plugins if not already done
        if not self.plugins:
            self.discover_plugins()
            
        # Load and activate each plugin
        count = 0
        for plugin_name in autoload_plugins:
            if plugin_name not in self.plugin_statuses or self.plugin_statuses[plugin_name] == self.PLUGIN_STATUS["NOT_LOADED"]:
                # Load the plugin
                if self.load_plugin(plugin_name):
                    # Attempt to activate
                    if self.activate_plugin(plugin_name):
                        count += 1
                        self.log(f"[Plugin] Auto-loaded and activated: {plugin_name}")
                    else:
                        self.log(f"[Plugin Warning] Auto-loaded but failed to activate: {plugin_name}")
                    
        return count
        
    def register_service(self, service_name, service_obj):
        """
        Register a service that plugins can access
        
        Args:
            service_name (str): Name of the service
            service_obj (object): Service object to register
            
        Returns:
            bool: True if service was registered successfully
        """
        if not hasattr(self, 'services'):
            self.services = {}
            
        self.services[service_name] = service_obj
        self.log(f"[Plugin] Registered service: {service_name}")
        return True
        
    def get_active_plugins(self):
        """
        Get a list of currently active plugins
        
        Returns:
            list: List of active plugin names
        """
        active_plugins = []
        for plugin_name, status in self.plugin_statuses.items():
            if status == self.PLUGIN_STATUS["ACTIVE"]:
                active_plugins.append(plugin_name)
        return active_plugins
    
    def get_plugin_info(self, plugin_id):
        """
        Get information about a specific plugin
        
        Args:
            plugin_id (str): The ID/name of the plugin
            
        Returns:
            dict: Dictionary containing plugin metadata, or empty dict if plugin not found
        """
        if plugin_id in self.plugin_metadata:
            return self.plugin_metadata[plugin_id]
        else:
            self.log(f"[Plugin Warning] Requested info for unknown plugin: {plugin_id}")
            return {}
    
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
                    plugin_id=plugin_name,  # Pass plugin name as the plugin_id
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
    
    def get_plugin_instance(self, plugin_id: str) -> Any:
        """
        Get the instance of a loaded plugin
        
        Args:
            plugin_id: Name/ID of the plugin
            
        Returns:
            The plugin instance or None if not found or not loaded
        """
        return self.plugins.get(plugin_id)
    
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

    def register_plugin_ui(self, plugin_name: str, ui_container: Any) -> bool:
        """
        Register a plugin's UI components with the main application
        
        Args:
            plugin_name: Name of the plugin
            ui_container: UI container to register into
            
        Returns:
            True if UI registered successfully, False otherwise
        """
        with self._lock:
            # Check if plugin is active
            if self.get_plugin_status(plugin_name) != self.PLUGIN_STATUS["ACTIVE"]:
                self.log(f"[Plugin UI] Cannot register UI for inactive plugin: {plugin_name}")
                return False
                
            # Get plugin instance
            plugin = self.plugins.get(plugin_name)
            if not plugin:
                return False
                
            try:
                # Check for UI activation function
                if hasattr(plugin, "activate_ui") and callable(plugin.activate_ui):
                    # Call the UI activation function
                    result = plugin.activate_ui(ui_container)
                    
                    if result:
                        self.log(f"[Plugin UI] Registered UI components for {plugin_name}")
                        return True
                    else:
                        self.log(f"[Plugin UI] Failed to register UI for {plugin_name}")
                        return False
                else:
                    # Check for UI module with panel
                    try:
                        # Attempt to import ui module
                        module_name = f"plugins.{plugin_name}.ui"
                        ui_module = importlib.import_module(module_name)
                        
                        # Look for activate_ui function at module level
                        if hasattr(ui_module, "activate_ui") and callable(ui_module.activate_ui):
                            result = ui_module.activate_ui(ui_container)
                            
                            if result:
                                self.log(f"[Plugin UI] Registered UI from module for {plugin_name}")
                                return True
                        
                        # If no activate_ui function, check for Panel class
                        if hasattr(ui_module, "Panel"):
                            panel_class = getattr(ui_module, "Panel")
                            panel = panel_class(ui_container, plugin)
                            
                            # Store panel instance with the plugin
                            if not hasattr(plugin, "_ui_instances"):
                                setattr(plugin, "_ui_instances", [])
                            getattr(plugin, "_ui_instances").append(panel)
                            
                            self.log(f"[Plugin UI] Created UI panel for {plugin_name}")
                            return True
                            
                    except ImportError:
                        self.log(f"[Plugin UI] No UI module found for {plugin_name}")
                    except Exception as e:
                        self.log(f"[Plugin UI] Error creating UI for {plugin_name}: {e}")
                    
                    return False
                    
            except Exception as e:
                self.log(f"[Plugin UI] Error registering UI for {plugin_name}: {e}")
                return False

    def check_dependencies(self, plugin_name: str) -> Dict[str, bool]:
        """
        Check if all dependencies for a plugin are satisfied
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary mapping dependency names to satisfaction status
        """
        metadata = self.get_plugin_metadata(plugin_name)
        dependencies = metadata.get("dependencies", {})
        results = {}
        
        # Check Python version
        if "python" in dependencies:
            import pkg_resources
            python_req = dependencies["python"]
            try:
                # Use pkg_resources to check version requirement
                pkg_resources.require(f"python{python_req}")
                results["python"] = True
            except pkg_resources.VersionConflict:
                results["python"] = False
        
        # Check Irintai version
        if "irintai" in dependencies:
            irintai_req = dependencies["irintai"]
            try:
                pkg_resources.require(f"irintai{irintai_req}")
                results["irintai"] = True
            except (pkg_resources.VersionConflict, ImportError):
                results["irintai"] = False
        
        # Check external libraries
        if "external_libs" in dependencies and isinstance(dependencies["external_libs"], list):
            for lib in dependencies["external_libs"]:
                try:
                    importlib.import_module(lib.split(">=")[0].strip())
                    results[lib] = True
                except ImportError:
                    results[lib] = False
        
        # Check plugin dependencies
        if "plugins" in dependencies and isinstance(dependencies["plugins"], list):
            for dep_plugin in dependencies["plugins"]:
                # Check if plugin is loaded and active
                is_satisfied = (
                    dep_plugin in self.plugins and 
                    self.get_plugin_status(dep_plugin) == self.PLUGIN_STATUS["ACTIVE"]
                )
                results[f"plugin:{dep_plugin}"] = is_satisfied
        
        return results

    def install_dependencies(self, plugin_name: str) -> Dict[str, bool]:
        """
        Attempt to install missing dependencies for a plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary mapping dependency names to installation success status
        """
        results = {}
        metadata = self.get_plugin_metadata(plugin_name)
        dependencies = metadata.get("dependencies", {})
        
        # Only attempt to install external libraries
        if "external_libs" in dependencies and isinstance(dependencies["external_libs"], list):
            for lib in dependencies["external_libs"]:
                lib_name = lib.split(">=")[0].strip()
                
                try:
                    # Check if already installed
                    importlib.import_module(lib_name)
                    results[lib] = True
                    continue
                except ImportError:
                    pass
                    
                # Try to install with pip
                try:
                    import subprocess
                    self.log(f"[Plugin Dependencies] Installing {lib} for {plugin_name}")
                    
                    # Run pip install in a subprocess
                    process = subprocess.run(
                        [sys.executable, "-m", "pip", "install", lib],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if process.returncode == 0:
                        results[lib] = True
                        self.log(f"[Plugin Dependencies] Installed {lib}")
                    else:
                        results[lib] = False
                        self.log(f"[Plugin Dependencies] Failed to install {lib}: {process.stderr}")
                
                except Exception as e:
                    results[lib] = False
                    self.log(f"[Plugin Dependencies] Error installing {lib}: {e}")
        
        return results

    def register_event_handler(self, plugin_name: str, event_type: str, handler: Callable) -> bool:
        """
        Register a plugin's event handler for a specific event type
        
        Args:
            plugin_name: Name of the plugin
            event_type: Type of event to handle
            handler: Function to call when event occurs
            
        Returns:
            True if handler registered successfully, False otherwise
        """
        with self._lock:
            # Initialize event handlers dictionary if needed
            if not hasattr(self, "_event_handlers"):
                self._event_handlers = {}
                
            # Initialize handlers list for this event type
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
                
            # Register the handler with plugin info
            handler_info = {"plugin": plugin_name, "handler": handler}
            self._event_handlers[event_type].append(handler_info)
            
            self.log(f"[Plugin Events] Registered handler for {event_type} from {plugin_name}")
            return True

    def unregister_event_handler(self, plugin_name: str, event_type: str, handler: Optional[Callable] = None) -> bool:
        """
        Unregister a plugin's event handler
        
        Args:
            plugin_name: Name of the plugin
            event_type: Type of event to unregister from
            handler: Specific handler to unregister (if None, unregister all for plugin)
            
        Returns:
            True if handler(s) unregistered successfully, False otherwise
        """
        with self._lock:
            # Check if we have any handlers for this event
            if not hasattr(self, "_event_handlers") or event_type not in self._event_handlers:
                return False
                
            # Find handlers to remove
            handlers_to_remove = []
            for handler_info in self._event_handlers[event_type]:
                if handler_info["plugin"] == plugin_name:
                    if handler is None or handler_info["handler"] == handler:
                        handlers_to_remove.append(handler_info)
            
            # Remove the handlers
            for handler_info in handlers_to_remove:
                self._event_handlers[event_type].remove(handler_info)
                
            # Clean up empty lists
            if not self._event_handlers[event_type]:
                del self._event_handlers[event_type]
                
            self.log(f"[Plugin Events] Unregistered {len(handlers_to_remove)} handlers for {event_type} from {plugin_name}")
            return len(handlers_to_remove) > 0

    def trigger_event(self, event_type: str, **event_data) -> Dict[str, Any]:
        """
        Trigger an event to be handled by registered plugins
        
        Args:
            event_type: Type of event to trigger
            **event_data: Data to pass to event handlers
            
        Returns:
            Dictionary mapping plugin names to their handler results
        """
        results = {}
        
        # Check if we have any handlers for this event
        if not hasattr(self, "_event_handlers") or event_type not in self._event_handlers:
            return results
            
        # Call each handler
        for handler_info in self._event_handlers[event_type]:
            plugin_name = handler_info["plugin"]
            handler = handler_info["handler"]
            
            try:
                # Skip handlers for inactive plugins
                status = self.get_plugin_status(plugin_name)
                if status != self.PLUGIN_STATUS["ACTIVE"]:
                    continue
                    
                # Call the handler and store result
                result = handler(**event_data)
                results[plugin_name] = result
                
            except Exception as e:
                self.log(f"[Plugin Events] Error in {event_type} handler from {plugin_name}: {e}")
                results[plugin_name] = {"error": str(e)}
                
        return results

    def uninstall_plugin(self, plugin_name: str) -> bool:
        """
        Safely uninstall a plugin
        
        Args:
            plugin_name: Name of the plugin to uninstall
            
        Returns:
            True if plugin uninstalled successfully, False otherwise
        """
        with self._lock:
            # Deactivate the plugin if active
            if self.get_plugin_status(plugin_name) == self.PLUGIN_STATUS["ACTIVE"]:
                if not self.deactivate_plugin(plugin_name):
                    self.log(f"[Plugin] Cannot uninstall active plugin {plugin_name}")
                    return False
                    
            try:
                # Call uninstall method if available
                if plugin_name in self.plugins:
                    plugin = self.plugins[plugin_name]
                    if hasattr(plugin, "uninstall") and callable(plugin.uninstall):
                        plugin.uninstall()
                        
                    # Remove from loaded plugins
                    del self.plugins[plugin_name]
                
                # Remove configuration directory
                plugin_config_dir = os.path.join(self.config_dir, plugin_name)
                if os.path.exists(plugin_config_dir):
                    import shutil
                    shutil.rmtree(plugin_config_dir)
                    
                # Remove status and metadata
                if plugin_name in self.plugin_statuses:
                    del self.plugin_statuses[plugin_name]
                if plugin_name in self.plugin_metadata:
                    del self.plugin_metadata[plugin_name]
                    
                self.log(f"[Plugin] Uninstalled plugin: {plugin_name}")
                return True
                
            except Exception as e:
                self.log(f"[Plugin Error] Failed to uninstall {plugin_name}: {e}")
                return False

    def check_for_updates(self, plugin_name: str) -> Dict[str, Any]:
        """
        Check if a plugin has updates available
        
        Args:
            plugin_name: Name of the plugin to check
            
        Returns:
            Dictionary with update information
        """
        result = {
            "has_update": False,
            "current_version": "0.0.0",
            "latest_version": "0.0.0",
            "update_url": None,
            "changelog": None
        }
        
        # Get current version
        metadata = self.get_plugin_metadata(plugin_name)
        current_version = metadata.get("version", "0.0.0")
        result["current_version"] = current_version
        
        # Check if plugin has update URL defined
        update_url = metadata.get("update_url")
        if not update_url:
            return result
            
        try:
            # Call plugin's update checking method if available
            if plugin_name in self.plugins:
                plugin = self.plugins[plugin_name]
                if hasattr(plugin, "check_for_updates") and callable(plugin.check_for_updates):
                    update_info = plugin.check_for_updates()
                    if update_info and isinstance(update_info, dict):
                        result.update(update_info)
                        return result
            
            # Basic update check using a JSON file at the update URL
            import urllib.request
            import json
            
            # Try to fetch update info
            with urllib.request.urlopen(update_url, timeout=5) as response:
                update_data = json.loads(response.read().decode())
                
                # Get latest version
                latest_version = update_data.get("version", "0.0.0")
                result["latest_version"] = latest_version
                
                # Check if newer
                from pkg_resources import parse_version
                if parse_version(latest_version) > parse_version(current_version):
                    result["has_update"] = True
                    result["update_url"] = update_data.get("download_url")
                    result["changelog"] = update_data.get("changelog")
                    
                    self.log(f"[Plugin] Update available for {plugin_name}: {current_version} → {latest_version}")
                    
        except Exception as e:
            self.log(f"[Plugin] Failed to check updates for {plugin_name}: {e}")
            
        return result
    
    def set_plugin_config(self, plugin_id: str, config_data: Dict[str, Any]) -> bool:
        """
        Update a plugin's configuration
        
        Args:
            plugin_id: Unique identifier for the plugin
            config_data: Dictionary containing configuration settings
            
        Returns:
            True if configuration updated successfully, False otherwise
        """
        if plugin_id not in self.plugins:
            self.log(f"[Plugin Manager] Cannot set config for unknown plugin: {plugin_id}")
            return False
            
        try:
            # Get the plugin instance
            plugin_instance = self.plugins[plugin_id].get("instance")
            if not plugin_instance:
                self.log(f"[Plugin Manager] Plugin not loaded: {plugin_id}")
                return False
                
            # Update the plugin's configuration
            if hasattr(plugin_instance, "set_config"):
                plugin_instance.set_config(config_data)
                
            # Save the configuration to file
            config_file = os.path.join(self.config_dir, f"{plugin_id}.json")
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
                
            self.log(f"[Plugin Manager] Updated configuration for {plugin_id}")
            return True
            
        except Exception as e:
            self.log(f"[Plugin Manager] Failed to update config for {plugin_id}: {e}")
            return False