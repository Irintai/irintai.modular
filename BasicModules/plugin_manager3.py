import os
import importlib.util
import traceback
import json
from types import ModuleType
from typing import Dict, Optional, Any


class PluginManager:
    def __init__(self, plugin_dir: str = "plugins", logger=None, core_app: Optional[Any] = None):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Any] = {}
        self.plugin_status: Dict[str, str] = {}
        self.plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logger or print
        self.core_app = core_app

    def _load_plugin_module(self, plugin_name: str, plugin_path: str) -> Optional[ModuleType]:
        try:
            # Try loading from plugins/<name>/core/<name>.py
            direct_core_path = os.path.join(plugin_path, "core", f"{plugin_name}.py")
            if os.path.exists(direct_core_path):
                spec = importlib.util.spec_from_file_location(plugin_name, direct_core_path)
            else:
                # Fallback to core/__init__.py or plugin root __init__.py
                fallback_paths = [
                    os.path.join(plugin_path, "core", "__init__.py"),
                    os.path.join(plugin_path, "__init__.py")
                ]
                spec = None
                for fallback_path in fallback_paths:
                    if os.path.exists(fallback_path):
                        spec = importlib.util.spec_from_file_location(plugin_name, fallback_path)
                        break

            if not spec or not spec.loader:
                self.logger(f"[PluginManager] No valid module found for plugin '{plugin_name}'.", "ERROR")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        except Exception as e:
            self.logger(f"[PluginManager] Failed to load module {plugin_name}: {e}")
            self.logger(traceback.format_exc())
            return None

    def _get_plugin_class(self, module: ModuleType) -> Optional[Any]:
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and hasattr(obj, "activate") and hasattr(obj, "deactivate"):
                return obj
        return None

    def load_plugins(self) -> None:
        if not os.path.exists(self.plugin_dir):
            self.logger(f"[PluginManager] Plugin directory '{self.plugin_dir}' not found.")
            return

        for name in os.listdir(self.plugin_dir):
            path = os.path.join(self.plugin_dir, name)
            if not os.path.isdir(path):
                continue

            self.logger(f"[PluginManager] Loading plugin: {name}")
            module = self._load_plugin_module(name, path)
            if not module:
                self.plugin_status[name] = "Failed to import"
                continue

            plugin_class = self._get_plugin_class(module)
            if not plugin_class:
                self.plugin_status[name] = "No valid plugin class"
                continue

            try:
                instance = plugin_class()
                instance.log = self.logger
                instance.core_app = self.core_app
                self.plugins[name] = {
                    "instance": instance,
                    "status": "Loaded"
                }
                self.plugin_status[name] = "Loaded"

                self.plugin_metadata[name] = {
                    "name": getattr(instance, "name", name),
                    "friendly_name": getattr(instance, "friendly_name", name.replace("_", " ").title()),
                    "version": getattr(instance, "version", "0.1"),
                    "description": getattr(instance, "description", "No description provided."),
                    "tags": getattr(instance, "tags", [])
                }

            except Exception as e:
                self.logger(f"[PluginManager] Failed to instantiate plugin {name}: {e}")
                self.logger(traceback.format_exc())
                self.plugin_status[name] = "Initialization failed"

    def activate_plugin(self, name: str) -> bool:
        plugin = self.plugins.get(name)
        if not plugin:
            self.plugin_status[name] = "Not found"
            return False

        try:
            plugin.activate()
            self.plugin_status[name] = "Active"
            return True
        except Exception as e:
            self.plugin_status[name] = f"Activation failed: {e}"
            self.logger(f"[PluginManager] Activation error for {name}: {e}")
            self.logger(traceback.format_exc())
            return False

    def deactivate_plugin(self, name: str) -> bool:
        plugin = self.plugins.get(name)
        if not plugin:
            return False

        try:
            plugin.deactivate()
            self.plugin_status[name] = "Inactive"
            return True
        except Exception as e:
            self.plugin_status[name] = f"Deactivation failed: {e}"
            self.logger(f"[PluginManager] Deactivation error for {name}: {e}")
            self.logger(traceback.format_exc())
            return False

    def reload_plugin(self, name: str) -> bool:
        if name in self.plugins:
            self.deactivate_plugin(name)
        plugin_path = os.path.join(self.plugin_dir, name)
        module = self._load_plugin_module(name, plugin_path)
        if not module:
            return False
        plugin_class = self._get_plugin_class(module)
        if not plugin_class:
            return False
        try:
            instance = plugin_class()
            instance.log = self.logger
            instance.core_app = self.core_app
            self.plugins[name] = {
                "instance": instance,
                "status": "Reloaded"
            }
            self.plugin_status[name] = "Reloaded"
            return True
        except Exception as e:
            self.plugin_status[name] = f"Reload failed: {e}"
            self.logger(f"[PluginManager] Reload error for {name}: {e}")
            self.logger(traceback.format_exc())
            return False

    def get_plugin_interface(self, name: str) -> Optional[Dict[str, Any]]:
        plugin = self.plugins.get(name)
        if plugin and hasattr(plugin, "get_interface"):
            return plugin.get_interface()
        return None

    def list_plugins(self) -> Dict[str, str]:
        return self.plugin_status

    def get_plugin_metadata(self, name: str) -> Dict[str, Any]:
        return self.plugin_metadata.get(name, {})
