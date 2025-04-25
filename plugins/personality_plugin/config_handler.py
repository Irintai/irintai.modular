"""
Configuration handler for the Personality Plugin
"""
import os
import json
import time
from typing import Dict, Any, Optional

class ConfigHandler:
    """
    Handles configuration loading, saving, and validation for the Personality Plugin
    """
    
    def __init__(self, config_path: str, logger=None):
        """
        Initialize the configuration handler
        
        Args:
            config_path: Path to the configuration file
            logger: Optional logging function
        """
        self.config_path = config_path
        self.logger = logger or self._default_logger
        self.config = {}
        
        # Ensure configuration directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
    def _default_logger(self, message: str, level: str = "INFO") -> None:
        """Default logging method if none provided"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} [{level}] Personality Plugin Config: {message}")
        
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Returns:
            Configuration dictionary
        """
        try:
            # Check if configuration file exists
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    self.logger(f"Configuration loaded successfully from {self.config_path}", "INFO")
            else:
                # Create default configuration
                self.config = {
                    "active_profile": None,
                    "profiles": {},
                    "auto_remember": True
                }
                self.logger("Created default configuration", "INFO")
                self.save()
                
            return self.config
            
        except Exception as e:
            self.logger(f"Configuration loading error: {e}", "ERROR")
            # Create default configuration on error
            self.config = {
                "active_profile": None,
                "profiles": {},
                "auto_remember": True
            }
            return self.config
            
    def save(self) -> bool:
        """
        Save the current configuration to disk
        
        Returns:
            Success flag
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
                
            self.logger(f"Configuration saved successfully to {self.config_path}", "INFO")
            return True
            
        except Exception as e:
            self.logger(f"Failed to save configuration: {e}", "ERROR")
            return False
            
    def update(self, new_config: Dict[str, Any]) -> bool:
        """
        Update the configuration with new values
        
        Args:
            new_config: New configuration values
            
        Returns:
            Success flag
        """
        try:
            # Update configuration
            self.config.update(new_config)
            
            # Save to disk
            return self.save()
            
        except Exception as e:
            self.logger(f"Failed to update configuration: {e}", "ERROR")
            return False
            
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for the UI
        
        Returns:
            Schema dictionary for generating UI fields
        """
        return {
            "active_profile": {
                "type": "string",
                "label": "Active Profile",
                "description": "Currently active personality profile"
            },
            "auto_remember": {
                "type": "boolean",
                "label": "Store in Memory",
                "description": "Whether to store personality attributes in the memory system",
                "default": True
            }
        }
        
    def get_configuration_for_ui(self) -> Dict[str, Any]:
        """
        Get a UI-friendly version of the configuration
        
        Returns:
            UI-friendly configuration dictionary
        """
        profiles = self.config.get("profiles", {})
        profile_names = list(profiles.keys())
        
        ui_config = {
            "active_profile": self.config.get("active_profile"),
            "available_profiles": profile_names,
            "auto_remember": self.config.get("auto_remember", True)
        }
        
        return ui_config
