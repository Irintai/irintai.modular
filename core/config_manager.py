"""
Configuration Manager - Handles application settings
"""
import os
import json
from typing import Dict, Any, Optional, Callable

# Default configuration settings
DEFAULT_CONFIG = {
    "temperature": 0.7,
    "use_8bit": False,
    "model_path": "data/models",
    "inference_mode": "GPU",
    "memory_mode": "Off",
    "nsfw_enabled": False,
    "system_prompt": "You are Irintai, a helpful and knowledgeable assistant."
}

class ConfigManager:
    """Manages application configuration settings"""
    
    def __init__(self, config_path: str = "data/config.json", logger: Optional[Callable] = None):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Path to the configuration file
            logger: Optional logging function
        """
        self.config_path = config_path
        self.log = logger or print
        self.config = DEFAULT_CONFIG.copy()
        
        # Create directory for config if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Load config if it exists
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
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        
    def load_config(self) -> bool:
        """
        Load configuration from file
        
        Returns:
            True if configuration loaded successfully, False otherwise
        """
        if not os.path.exists(self.config_path):
            self.log(f"[Config] No configuration file found at {self.config_path}, using defaults")
            return False
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                
            # Update configuration with loaded values
            self.config.update(loaded_config)
            
            self.log("[Config] Configuration loaded successfully")
            return True
        except Exception as e:
            self.log(f"[Config Error] Failed to load configuration: {e}")
            return False
            
    def save_config(self) -> bool:
        """
        Save configuration to file
        
        Returns:
            True if configuration saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
                
            self.log("[Config] Configuration saved successfully")
            return True
        except Exception as e:
            self.log(f"[Config Error] Failed to save configuration: {e}")
            return False
            
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self.config = DEFAULT_CONFIG.copy()
        self.log("[Config] Configuration reset to defaults")
        
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values
        
        Returns:
            Dictionary of all configuration values
        """
        return self.config.copy()
        
    def update(self, new_config: Dict[str, Any]) -> None:
        """
        Update multiple configuration values
        
        Args:
            new_config: Dictionary of configuration values to update
        """
        self.config.update(new_config)
        
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
            
            self.log(f"[Environment] OLLAMA_HOME={ollama_home}, OLLAMA_MODELS={path}")
            return True
        except Exception as e:
            self.log(f"[Error] Failed to update environment variables: {e}")
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
                self.log(f"[Config] Running command: {cmd}")
                
                # Run the command (requires elevation)
                process = subprocess.run(
                    cmd,
                    capture_output=True, 
                    text=True,
                    shell=True  # Required for setx
                )
                
                if process.returncode == 0:
                    self.log("[Config] System environment variable set successfully")
                    return True
                else:
                    self.log(f"[Error] Failed to set system variable: {process.stderr}")
                    return False
            else:
                # For Unix-like systems, we would need to modify .bashrc, .profile, etc.
                # This is more complex and would require different handling
                self.log("[Error] Setting system variables on non-Windows systems is not implemented")
                return False
        except Exception as e:
            self.log(f"[Error] Failed to set system variable: {e}")
            return False