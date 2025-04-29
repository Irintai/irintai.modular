"""
Settings Manager - Centralized management of application settings with observer pattern,
settings migration, and settings synchronization
"""
import os
import json
from typing import Dict, List, Any, Callable, Optional
import threading

class SettingsManager:
    """
    Centralized settings manager with observer pattern to ensure settings consistency
    throughout the application. This helps prevent duplicate or conflicting settings
    controls across different UI panels.
    """
    
    def __init__(self, config_manager, logger: Optional[Callable] = None):
        """
        Initialize the settings manager
        
        Args:
            config_manager: ConfigManager instance
            logger: Optional logging function
        """
        self.config_manager = config_manager
        self.log = logger or print
        self.observers = {}
        self.lock = threading.RLock()  # Use RLock for thread safety
        
    def register_observer(self, setting_key: str, observer: Callable):
        """
        Register an observer for a specific setting
        
        Args:
            setting_key: The setting key to observe
            observer: Callback function to be called when setting changes
        """
        with self.lock:
            if setting_key not in self.observers:
                self.observers[setting_key] = []
            
            if observer not in self.observers[setting_key]:
                self.observers[setting_key].append(observer)
                
    def unregister_observer(self, setting_key: str, observer: Callable):
        """
        Unregister an observer for a specific setting
        
        Args:
            setting_key: The setting key being observed
            observer: Callback function to remove
        """
        with self.lock:
            if setting_key in self.observers and observer in self.observers[setting_key]:
                self.observers[setting_key].remove(observer)
                
    def update_setting(self, setting_key: str, value: Any):
        """
        Update a setting and notify all observers
        
        Args:
            setting_key: The setting key to update
            value: The new value for the setting
        """
        with self.lock:
            # Update the setting in the config manager
            self.config_manager.set(setting_key, value)
            
            # Notify all observers for this setting
            if setting_key in self.observers:
                for observer in self.observers[setting_key]:
                    try:
                        observer(value)
                    except Exception as e:
                        self.log(f"[Settings] Error notifying observer for {setting_key}: {e}")
                        
            # Special case for patterns where settings have both specific and general observers
            parts = setting_key.split('.')
            if len(parts) > 1:
                pattern = '.'.join(parts[:-1]) + '.*'
                if pattern in self.observers:
                    for observer in self.observers[pattern]:
                        try:
                            observer(setting_key, value)
                        except Exception as e:
                            self.log(f"[Settings] Error notifying pattern observer for {setting_key}: {e}")
    
    def get_setting(self, setting_key: str, default: Any = None) -> Any:
        """
        Get a setting value
        
        Args:
            setting_key: The setting key to retrieve
            default: Default value if setting not found
            
        Returns:
            The setting value or default if not found
        """
        return self.config_manager.get(setting_key, default)
        
    def batch_update(self, settings: Dict[str, Any]):
        """
        Update multiple settings at once
        
        Args:
            settings: Dictionary of setting keys and values
        """
        with self.lock:
            # First update all settings
            for key, value in settings.items():
                self.config_manager.set(key, value)
                
            # Then notify all observers
            for key, value in settings.items():
                if key in self.observers:
                    for observer in self.observers[key]:
                        try:
                            observer(value)
                        except Exception as e:
                            self.log(f"[Settings] Error notifying observer for {key}: {e}")
    
    def migrate_legacy_settings(self, core_system):
        """
        Migrate settings from the old fragmented structure to the new unified settings structure
        
        Args:
            core_system: Dictionary containing core system components
            
        Returns:
            int: Number of migrated settings
        """
        self.log("[Settings] Starting settings migration...")
        
        config_manager = core_system.get("config_manager")
        if not config_manager:
            self.log("[Settings] Error: Config manager not found in core system")
            return 0
        
        # Get the old config
        old_config = config_manager.config
        
        # Mapping of old settings paths to new paths
        migration_map = {
            # Memory settings
            "memory_mode": "memory.mode",
            "memory_embedding_model": "memory.embedding_model",
            "pdf_ocr_enabled": "memory.pdf.ocr_enabled",
            
            # Model settings
            "default_model": "model.default",
            "model_temperature": "model.temperature",
            "use_8bit": "model.use_8bit",
            "use_gpu": "model.use_gpu",
            
            # UI settings
            "ui_theme": "ui.theme",
            
            # Plugin settings
            "plugin_auto_start": "plugins.auto_start",
            "plugin_directory": "plugins.directory",
            "plugin_sandbox": "plugins.sandbox",
            
            # System settings
            "system_autosave": "system.autosave",
            "monitoring_interval": "system.monitoring_interval",
            
            # Logging settings
            "log_level": "logging.level",
            "log_retention_days": "logging.retention_days"
        }
        
        # Track migrated settings
        migrated = 0
        
        # Migrate each setting if it exists in the old config
        for old_key, new_key in migration_map.items():
            if old_key in old_config:
                self.update_setting(new_key, old_config[old_key])
                migrated += 1
                
        # Migrate plugin-specific settings
        if "plugins" in old_config and isinstance(old_config["plugins"], dict):
            for plugin_id, plugin_settings in old_config["plugins"].items():
                # Skip internal plugin management settings
                if plugin_id in ["auto_start", "directory", "sandbox"]:
                    continue
                    
                if isinstance(plugin_settings, dict):
                    # Create a new plugin settings key
                    plugin_key = f"plugins.{plugin_id}"
                    self.update_setting(plugin_key, plugin_settings)
                    migrated += 1
                    
        self.log(f"[Settings] Migration complete: {migrated} settings migrated to new structure")
        
        # Settings are already saved by settings_manager.update_setting
        # No need for explicit save call
        
        return migrated

    def setup_settings_synchronization(self, core_system):
        """
        Set up observers to synchronize settings between components
        
        Args:
            core_system: Dictionary containing core system components
            
        Returns:
            bool: True if synchronization was set up successfully, False otherwise
        """
        self.log("[Settings] Setting up settings synchronization...")
        
        chat_engine = core_system.get("chat_engine")
        memory_system = core_system.get("memory_system")
        
        if not chat_engine:
            self.log("[Settings] Error: Chat engine not found in core system")
            return False
        
        # Set up memory mode synchronization
        def on_memory_mode_change(value):
            if value == "off":
                chat_engine.set_memory_mode(enabled=False)
            elif value == "manual":
                chat_engine.set_memory_mode(enabled=True, auto=False, background=False)
            elif value == "auto":
                chat_engine.set_memory_mode(enabled=True, auto=True, background=False)
            elif value == "background":
                chat_engine.set_memory_mode(enabled=True, auto=True, background=True)
                
            self.log(f"[Memory Mode] Set to: {value.capitalize()}")
        
        # Register the observer for memory mode changes
        self.register_observer("memory.mode", on_memory_mode_change)
        
        # Set up system prompt synchronization
        def on_system_prompt_change(value):
            chat_engine.set_system_prompt(value)
        
        # Register the observer for system prompt changes
        self.register_observer("chat.system_prompt", on_system_prompt_change)
        
        # Initialize with current settings
        current_mode = self.get_setting("memory.mode", "off")
        on_memory_mode_change(current_mode)
        
        current_prompt = self.get_setting("chat.system_prompt", 
                                          "You are Irintai, a helpful and knowledgeable assistant.")
        on_system_prompt_change(current_prompt)
        
        self.log("[Settings] Settings synchronization set up successfully")
        return True
