import os
import importlib
import threading
from typing import Callable, Dict, Optional, Any, Type

PLUGIN_STATUS = {
    "LOADED": "Loaded but inactive",
    "ACTIVE": "Activated and running",
    "ERROR": "Failed to initialize",
    "NOT_FOUND": "Plugin not found"
}


class PluginManager:
    """
    Manages loading, activation, and interaction of Irintai plugins.
    
    Follows Irintai architectural standards:
    - Modular discovery and lifecycle handling
    - Type-safe interfaces
    - Structured logging and error tracking
    - Minimal side effects and no global state pollution
    """

    def __init__(
        self,
        plugin_dir: str = "plugins",
        logger: Optional[Callable[[str, str], None]] = None,
        core_app: Optional[Any] = None
    ):
        """
        Initialize the Plugin Manager
        
        Args:
            plugin_dir: Directory containing plugin folders
            logger: Optional logging function (message, level)
            core_system: Reference to the core Irintai system (for DI)
        """
        self.plugin_dir = plugin_dir
        self.log = logger or self._default_logger
        self.core_app = core_app
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        # Ensure plugin directory exists
        os.makedirs(self.plugin_dir, exist_ok=True)

    def _default_logger(self, message: str, level: str = "INFO") -> None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} [{level}] {message}")

    def load_plugins(self) -> None:
        """
        Discover and instantiate all plugins in the plugin directory
        """
        with self._lock:
            for entry in os.listdir(self.plugin_dir):
                plugin_path = os.path.join(self.plugin_dir, entry)
                if os.path.isdir(plugin_path):
                    try:
                        module_name = f"{self.plugin_dir}.{entry}"
                        module = importlib.import_module(module_name)
                        plugin_class = getattr(module, "IrintaiPlugin", None)

                        if plugin_class is None:
                            self.log(f"No IrintaiPlugin found in {entry}", "WARNING")
                            continue

                        plugin_instance = plugin_class(core_system=self.core_system)
                        self.plugins[entry] = {
                            "instance": plugin_instance,
                            "status": PLUGIN_STATUS["LOADED"]
                        }

                        self.log(f"Loaded plugin '{entry}'", "INFO")

                    except Exception as e:
                        self.plugins[entry] = {
                            "instance": None,
                            "status": PLUGIN_STATUS["ERROR"]
                        }
                        self.log(f"[Plugin Load Error] {entry}: {e}", "ERROR")

    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Activate a plugin by name
        
        Args:
            plugin_name: Name of plugin folder
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            plugin_entry = self.plugins.get(plugin_name)
            if not plugin_entry or not plugin_entry.get("instance"):
                self.log(f"Plugin '{plugin_name}' not found or not loaded", "WARNING")
                return False

            try:
                plugin_entry["instance"].activate()
                plugin_entry["status"] = PLUGIN_STATUS["ACTIVE"]
                self.log(f"Activated plugin '{plugin_name}'", "INFO")
                return True
            except Exception as e:
                plugin_entry["status"] = PLUGIN_STATUS["ERROR"]
                self.log(f"[Plugin Activation Error] {plugin_name}: {e}", "ERROR")
                return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Deactivate a plugin by name
        
        Args:
            plugin_name: Name of plugin
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            plugin_entry = self.plugins.get(plugin_name)
            if not plugin_entry or not plugin_entry.get("instance"):
                self.log(f"Plugin '{plugin_name}' not found or not loaded", "WARNING")
                return False

            try:
                plugin_entry["instance"].deactivate()
                plugin_entry["status"] = PLUGIN_STATUS["LOADED"]
                self.log(f"Deactivated plugin '{plugin_name}'", "INFO")
                return True
            except Exception as e:
                plugin_entry["status"] = PLUGIN_STATUS["ERROR"]
                self.log(f"[Plugin Deactivation Error] {plugin_name}: {e}", "ERROR")
                return False

    def get_plugin_interface(self, plugin_name: str) -> Optional[Dict[str, Callable]]:
        """
        Get the interface dictionary exposed by a plugin
        
        Args:
            plugin_name: Name of plugin
        
        Returns:
            Dictionary of interface methods or None
        """
        plugin_entry = self.plugins.get(plugin_name)
        if plugin_entry and plugin_entry.get("instance"):
            try:
                return plugin_entry["instance"].get_interface()
            except Exception as e:
                self.log(f"[Plugin Interface Error] {plugin_name}: {e}", "ERROR")
        return None

    def get_plugin_status(self, plugin_name: str) -> str:
        """
        Get the current status of a plugin
        
        Args:
            plugin_name: Name of plugin
        
        Returns:
            Status string
        """
        return self.plugins.get(plugin_name, {}).get("status", PLUGIN_STATUS["NOT_FOUND"])
