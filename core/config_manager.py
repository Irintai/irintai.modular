"""
Configuration management for the Irintai Assistant
"""
import os
import json
import threading
from typing import Any, Dict, Optional, List, Tuple

class ConfigManager:
    """Manages application configuration and settings"""
    
    def __init__(self, path: str = "data/config.json", auto_save: bool = True):
        """
        Initialize the configuration manager
        
        Args:
            path: Path to the configuration file
            auto_save: Whether to automatically save changes
        """
        self.config_path = path
        self.auto_save = auto_save
        self.config = {}
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Load configuration
        self.load_config()
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        with self.lock:
            return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        with self.lock:
            self.config[key] = value
            
            # Auto-save if enabled
            if self.auto_save:
                self.save_config()
        
    def load_config(self) -> bool:
        """
        Load configuration from file
        
        Returns:
            True if configuration loaded successfully, False otherwise
        """
        with self.lock:
            if not os.path.exists(self.config_path):
                return False
            
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                return True
            except Exception:
                return False
            
    def save_config(self) -> bool:
        """
        Save configuration to file
        
        Returns:
            True if configuration saved successfully, False otherwise
        """
        with self.lock:
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2)
                return True
            except Exception:
                return False
            
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self.config = {}
        
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values
        
        Returns:
            Dictionary of all configuration values
        """
        with self.lock:
            return self.config.copy()
        
    def update(self, new_config: Dict[str, Any]) -> None:
        """
        Update multiple configuration values
        
        Args:
            new_config: Dictionary of configuration values to update
        """
        with self.lock:
            self.config.update(new_config)
            
            # Auto-save if enabled
            if self.auto_save:
                self.save_config()
        
    def set_system_environment(self, model_path: Optional[str] = None) -> bool:
        """
        Set system environment variables for model path
        
        Args:
            model_path: Optional model path to set, uses the configured path if not provided
            
        Returns:
            True if environment variables set successfully, False otherwise
        """
        try:
            # Use provided path or get from config
            path = model_path or self.get("model_path")
            
            # Ensure the parent directory path is extracted correctly
            ollama_home = os.path.dirname(path)
            
            # Set environment variables
            os.environ["OLLAMA_HOME"] = ollama_home
            os.environ["OLLAMA_MODELS"] = path
            
            return True
        except Exception:
            return False
    
    def set_system_path_var(self, model_path: Optional[str] = None) -> bool:
        """
        Set system path environment variables using system commands (requires admin privileges)
        
        Args:
            model_path: Optional model path to set, uses the configured path if not provided
            
        Returns:
            True if system variables set successfully, False otherwise
        """
        import subprocess
        
        # Use provided path or get from config
        path = model_path or self.get("model_path")
        
        try:
            # For Windows, use setx command which requires admin privileges
            if os.name == 'nt':
                cmd = f'setx OLLAMA_MODELS "{path}" /M'
                
                # Run the command (requires elevation)
                process = subprocess.run(
                    cmd,
                    capture_output=True, 
                    text=True,
                    shell=True  # Required for setx
                )
                
                if process.returncode == 0:
                    return True
                else:
                    return False
            else:
                # For Unix-like systems, we would need to modify .bashrc, .profile, etc.
                # This is more complex and would require different handling
                return False
        except Exception:
            return False
        
    def export_config(self, export_path: str) -> bool:
        """
        Export configuration to another file
        
        Args:
            export_path: Path to export configuration to
            
        Returns:
            True if configuration exported successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Export configuration
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
                
            return True
        except Exception:
            return False
        
    def import_config(self, import_path: str, merge: bool = False) -> bool:
        """
        Import configuration from another file
        
        Args:
            import_path: Path to import configuration from
            merge: Whether to merge with existing configuration or replace entirely
            
        Returns:
            True if configuration imported successfully, False otherwise
        """
        if not os.path.exists(import_path):
            return False
            
        try:
            # Load configuration from file
            with open(import_path, 'r', encoding='utf-8') as f:
                import_config = json.load(f)
                
            # Validate imported configuration
            if not isinstance(import_config, dict):
                return False
                
            # Replace or merge configuration
            if merge:
                self.config.update(import_config)
            else:
                self.config = import_config
                
            self.save_config()  # Save the imported configuration
            return True
        except Exception:
            return False
        
    def get_nested(self, path: str, default: Any = None) -> Any:
        """
        Get a nested configuration value using dot notation
        
        Args:
            path: Path to configuration value (e.g., 'database.host')
            default: Default value if path doesn't exist
            
        Returns:
            Configuration value
        """
        parts = path.split('.')
        current = self.config
        
        try:
            for part in parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default
        
    def set_nested(self, path: str, value: Any) -> bool:
        """
        Set a nested configuration value using dot notation
        
        Args:
            path: Path to configuration value (e.g., 'database.host')
            value: Value to set
            
        Returns:
            True if value was set successfully, False otherwise
        """
        parts = path.split('.')
        current = self.config
        
        try:
            # Navigate to the parent of the target key
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
                
            # Set the value
            current[parts[-1]] = value
            return True
        except Exception:
            return False
        
    def validate_config(self, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate configuration against a schema
        
        Args:
            schema: Dictionary defining validation rules (optional)
            
        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}
        
        # Default schema based on expected types/ranges
        default_schema = {
            "temperature": {"type": float, "range": [0.0, 2.0]},
            "use_8bit": {"type": bool},
            "inference_mode": {"type": str, "values": ["CPU", "GPU", "MPS"]},
            "memory_mode": {"type": str, "values": ["Off", "Basic", "Advanced"]},
            "nsfw_enabled": {"type": bool},
            "model_path": {"type": str}
        }
        
        # Use provided schema or default
        validation_schema = schema or default_schema
        
        # Check each field against the schema
        for key, rules in validation_schema.items():
            if key in self.config:
                value = self.config[key]
                
                # Type checking
                if "type" in rules and not isinstance(value, rules["type"]):
                    errors[key] = f"Invalid type: expected {rules['type'].__name__}, got {type(value).__name__}"
                    continue
                    
                # Range checking for numeric values
                if "range" in rules and isinstance(value, (int, float)):
                    min_val, max_val = rules["range"]
                    if value < min_val or value > max_val:
                        errors[key] = f"Value out of range: {value} (range: {min_val}-{max_val})"
                        
                # Value checking for strings/enums
                if "values" in rules and isinstance(value, str):
                    if value not in rules["values"]:
                        errors[key] = f"Invalid value: {value} (valid values: {', '.join(rules['values'])})"
        
        return errors
    
    def set_secure(self, key: str, value: Any) -> None:
        """
        Set a secure configuration value (will be masked in logs)
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        
        # Add to secure keys set if not already
        if not hasattr(self, '_secure_keys'):
            self._secure_keys = set()
        
        self._secure_keys.add(key)
        
    def get_secure(self, key: str, default: Any = None) -> Any:
        """
        Get a secure configuration value
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
        
    def get_all_secure(self) -> Dict[str, str]:
        """
        Get a masked representation of all configuration values (for display)
        
        Returns:
            Dictionary with sensitive values masked
        """
        if not hasattr(self, '_secure_keys'):
            self._secure_keys = set()
            
        # Create a copy with masked secure values
        display_config = {}
        
        for key, value in self.config.items():
            if key in self._secure_keys:
                display_config[key] = "********"
            else:
                display_config[key] = value
                
        return display_config
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """
        Get all configuration values for a specific category
        
        Args:
            category: Configuration category prefix (e.g., 'ui', 'model')
            
        Returns:
            Dictionary of configuration values in the category
        """
        prefix = category + "."
        result = {}
        
        for key, value in self.config.items():
            if key.startswith(prefix):
                # Extract the key without prefix
                short_key = key[len(prefix):]
                result[short_key] = value
                
        return result
        
    def set_category(self, category: str, values: Dict[str, Any]) -> None:
        """
        Set multiple configuration values for a specific category
        
        Args:
            category: Configuration category prefix
            values: Dictionary of values to set
        """
        prefix = category + "."
        
        for key, value in values.items():
            # Combine category prefix with key
            full_key = prefix + key
            self.config[full_key] = value