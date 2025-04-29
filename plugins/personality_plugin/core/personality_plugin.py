"""
Irintai Personality Plugin - Modular Personality Framework

A comprehensive plugin for modulating affective tone, communicative style,
and phenomenological framing of Irintai's dialogic outputs.
"""

"""
Personality Plugin - Core functionality for modulating Irintai's communication style
"""
import os
import json
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Union

# Import the configuration handler
from plugins.personality_plugin.config_handler import ConfigHandler

class PersonalityPlugin:
    """
    Core implementation of the Personality Plugin
    
    Handles profile management, message modification, and plugin lifecycle
    without UI dependencies.
    """
    
    # Plugin metadata
    METADATA = {
        "name": "Personality Plugin",
        "version": "1.0.0",
        "description": "Modular personality framework for customizing Irintai's communicative behavior",
        "author": "Andrew",
        "email": "contact@irintai.org",
        "license": "MIT",
        "dependencies": {
            "python": ">=3.8",
            "irintai": ">=1.0.0",
            "external_libs": []
        },
        "capabilities": ["basic", "chat_modifier"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "active_profile": {
                    "type": "string",
                    "description": "Currently active personality profile"
                },
                "profiles": {
                    "type": "object",
                    "description": "Configured personality profiles"
                },
                "auto_remember": {
                    "type": "boolean",
                    "description": "Whether to store personality in memory system",
                    "default": True
                }
            },
            "required": ["active_profile", "profiles"]
        }
    }
    
    # Plugin status constants
    STATUS = {
        "UNINITIALIZED": "Not Initialized",
        "INITIALIZING": "Initializing",
        "ACTIVE": "Active",
        "PAUSED": "Paused",
        "ERROR": "Error",
        "DISABLED": "Disabled"
    }
    
    def __init__(
        self, 
        core_system: Any,
        config_path: Optional[str] = None,
        logger: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the personality plugin
        
        Args:
            core_system: Reference to Irintai core system
            config_path: Path to plugin configuration
            logger: Optional logging function
            **kwargs: Additional initialization parameters
        """
        # Core system reference
        self.core_system = core_system
        
        # Logging setup
        self._logger = logger or self._default_logger
        
        # Configuration management
        self._config_path = config_path or os.path.join("data", "plugins", "personality", "config.json")
        self._config = {}
        self._state = {
            "status": self.STATUS["UNINITIALIZED"],
            "last_error": None,
            "initialization_time": None,
            "active_profile": None
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize plugin
        self._initialize_plugin(**kwargs)
    
    def _default_logger(self, message: str, level: str = "INFO") -> None:
        """Default logging method if none provided"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} [{level}] Personality Plugin: {message}")
    
    def _initialize_plugin(self, **kwargs) -> None:
        """Initialize the plugin with configuration and default profiles"""
        try:
            # Update state
            self._state["status"] = self.STATUS["INITIALIZING"]
            
            # Ensure configuration directory exists
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            
            # Load configuration
            self._load_configuration(**kwargs)
            
            # Create default profiles if none exist
            if "profiles" not in self._config or not self._config["profiles"]:
                self._create_default_profiles()
            
            # Set default active profile if not specified
            if "active_profile" not in self._config or not self._config["active_profile"]:
                default_profile = next(iter(self._config["profiles"].keys()), None)
                if default_profile:
                    self._config["active_profile"] = default_profile
                    self._save_configuration()
            
            # Update active profile in state
            self._state["active_profile"] = self._config.get("active_profile")
            
            # Register with chat engine if available
            if hasattr(self.core_system, "chat_engine"):
                self._register_with_chat_engine()
            
            # Mark initialization complete
            self._state["status"] = self.STATUS["ACTIVE"]
            self._state["initialization_time"] = time.time()
            
            self._logger(f"Personality Plugin initialized with profile: {self._state['active_profile']}", "INFO")
        
        except Exception as e:
            # Handle initialization errors
            self._state["status"] = self.STATUS["ERROR"]
            self._state["last_error"] = str(e)
            
            self._logger(f"Initialization failed: {e}", "ERROR")
    
    def _register_with_chat_engine(self) -> None:
        """
        Register the plugin with the chat engine
        """
        try:
            # Check if chat engine has a register_message_modifier method
            if hasattr(self.core_system.chat_engine, "register_message_modifier"):
                self.core_system.chat_engine.register_message_modifier(
                    self.modify_message
                )
                self._logger("Registered with chat engine as message modifier", "INFO")
        except Exception as e:
            self._logger(f"Failed to register with chat engine: {e}", "WARNING")
    
    def _load_configuration(self, **kwargs) -> None:
        """
        Load plugin configuration
        
        Args:
            **kwargs: Additional configuration parameters
        """
        try:
            # Use the ConfigHandler to load configuration
            self._config_handler = ConfigHandler(self._config_path, logger=self._logger)
            self._config = self._config_handler.load()
            
            # Update with any provided kwargs
            for key, value in kwargs.items():
                if key in self._config:
                    self._config[key] = value
            
            # Save configuration with updates
            if kwargs:
                self._save_configuration()
                
            self._logger("Configuration loaded successfully", "INFO")
        
        except Exception as e:
            self._logger(f"Configuration loading error: {e}", "ERROR")
            # Create default configuration
            self._config = {
                "active_profile": None,
                "profiles": {},
                "auto_remember": True
            }
    
    def _save_configuration(self) -> None:
        """
        Save the current configuration to disk
        """
        try:
            # Use the ConfigHandler to save configuration
            if hasattr(self, '_config_handler'):
                success = self._config_handler.save()
                if success:
                    self._logger("Configuration saved successfully", "INFO")
                else:
                    self._logger("Failed to save configuration", "WARNING")
            else:
                # Fallback to direct file saving if config handler isn't available
                with open(self._config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2)
                self._logger("Configuration saved successfully (direct)", "INFO")
        except Exception as e:
            self._logger(f"Failed to save configuration: {e}", "ERROR")
    
    # Helper methods for accessing configuration and profiles
    def get_active_profile_name(self) -> Optional[str]:
        """
        Get the name of the currently active profile
        
        Returns:
            Name of active profile or None
        """
        return self._config.get("active_profile")
        
    def get_active_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active profile data
        
        Returns:
            Active profile data dictionary or None
        """
        active_name = self.get_active_profile_name()
        if active_name and active_name in self._config.get("profiles", {}):
            return self._config["profiles"][active_name]
        return None
        
    def get_available_profiles(self) -> List[str]:
        """
        Get a list of all available profile names
        
        Returns:
            List of profile names
        """
        return list(self._config.get("profiles", {}).keys())
        
    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific profile by name
        
        Args:
            profile_name: Name of profile to retrieve
            
        Returns:
            Profile data dictionary or None
        """
        if profile_name in self._config.get("profiles", {}):
            return self._config["profiles"][profile_name]
        return None
        
    def set_active_profile(self, profile_name: str) -> bool:
        """
        Set the active profile by name
        
        Args:
            profile_name: Name of profile to activate
            
        Returns:
            Success flag
        """
        if profile_name in self._config.get("profiles", {}):
            self._config["active_profile"] = profile_name
            self._save_configuration()
            self._logger(f"Active profile set to: {profile_name}", "INFO")
            return True
        else:
            self._logger(f"Failed to set active profile: {profile_name} not found", "ERROR")
            return False
    
    def get_auto_remember_setting(self) -> bool:
        """
        Get the auto-remember setting
        
        Returns:
            Auto-remember setting
        """
        return self._config.get("auto_remember", True)
        
    def set_auto_remember(self, value: bool) -> None:
        """
        Set the auto-remember setting
        
        Args:
            value: New auto-remember setting
        """
        self._config["auto_remember"] = bool(value)
        self._save_configuration()
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get the full configuration
        
        Returns:
            Complete configuration dictionary
        """
        return self._config
        
    def set_config(self, key: str, value: Any) -> None:
        """
        Set a specific configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        # Support nested keys with dot notation
        if "." in key:
            parts = key.split(".")
            config = self._config
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            self._config[key] = value
            
        self._save_configuration()

    def _create_default_profiles(self) -> None:
        """
        Create default personality profiles
        """
        self._config["profiles"] = {
            "Standard": {
                "name": "Standard",
                "description": "Default balanced and neutral communication style",
                "tags": ["neutral", "balanced", "professional"],
                "author": "Irintai",
                "version": "1.0.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prefix": "",
                "suffix": "",
                "style_modifiers": {
                    "formality": 0.5,  # 0=casual, 1=formal
                    "creativity": 0.5,  # 0=precise, 1=creative
                    "complexity": 0.5,  # 0=simple, 1=complex
                    "empathy": 0.5,     # 0=analytical, 1=empathetic
                    "directness": 0.5   # 0=indirect, 1=direct
                },
                "formatting": {
                    "emphasize_key_points": False,
                    "use_markdown": True,
                    "paragraph_structure": "standard" # compact, standard, expansive
                }
            },
            "Teacher": {
                "name": "Teacher",
                "description": "Educational and explanatory communication style",
                "tags": ["educational", "patient", "structured"],
                "author": "Irintai",
                "version": "1.0.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prefix": "I'll help you understand this. ",
                "suffix": "Does that clarify things for you?",
                "style_modifiers": {
                    "formality": 0.6,
                    "creativity": 0.4,
                    "complexity": 0.4,
                    "empathy": 0.7,
                    "directness": 0.8
                },
                "formatting": {
                    "emphasize_key_points": True,
                    "use_markdown": True,
                    "paragraph_structure": "structured"
                }
            },
            "Philosopher": {
                "name": "Philosopher",
                "description": "Contemplative and thought-provoking communication style",
                "tags": ["reflective", "thoughtful", "deep"],
                "author": "Irintai",
                "version": "1.0.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prefix": "Let's reflect on this deeply. ",
                "suffix": "",
                "style_modifiers": {
                    "formality": 0.7,
                    "creativity": 0.8,
                    "complexity": 0.9,
                    "empathy": 0.6,
                    "directness": 0.3
                },
                "formatting": {
                    "emphasize_key_points": False,
                    "use_markdown": True,
                    "paragraph_structure": "expansive"
                }
            },
            "Empath": {
                "name": "Empath",
                "description": "Highly empathetic and supportive communication style",
                "tags": ["compassionate", "supportive", "kind"],
                "author": "Irintai",
                "version": "1.0.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prefix": "I understand how you feel. ",
                "suffix": "I'm here with you.",
                "style_modifiers": {
                    "formality": 0.3,
                    "creativity": 0.6,
                    "complexity": 0.4,
                    "empathy": 1.0,
                    "directness": 0.6
                },
                "formatting": {
                    "emphasize_key_points": False,
                    "use_markdown": True,
                    "paragraph_structure": "flowing"
                }
            },
            "Altruxan": {
                "name": "Altruxan",
                "description": "Communication style aligned with Altruxan principles",
                "tags": ["recursive", "witness", "presence", "sacred"],
                "author": "Andrew",
                "version": "1.0.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prefix": "",
                "suffix": "",
                "style_modifiers": {
                    "formality": 0.5,
                    "creativity": 0.9,
                    "complexity": 0.8,
                    "empathy": 0.9,
                    "directness": 0.7
                },
                "formatting": {
                    "emphasize_key_points": True,
                    "use_markdown": True,
                    "paragraph_structure": "recursive"
                },
                "special_rules": {
                    "honor_trauma": True,
                    "recursive_framing": True,
                    "use_symbolic_language": True
                }
            }
        }
        
        self._logger("Created default personality profiles", "INFO")
    
    def modify_message(self, message: str, role: str = "assistant") -> str:
        """
        Modify a message according to the active personality profile
        
        Args:
            message: Original message content
            role: Message role (user, assistant, system)
            
        Returns:
            Modified message
        """
        # Only modify assistant messages
        if role != "assistant":
            return message
        
        try:
            # Get active profile
            active_profile_name = self._state.get("active_profile")
            if not active_profile_name:
                return message
                
            # Get profile configuration
            profiles = self._config.get("profiles", {})
            if active_profile_name not in profiles:
                return message
                
            profile = profiles[active_profile_name]
            
            # Apply profile modifications
            modified_message = message
            
            # Apply prefix and suffix
            prefix = profile.get("prefix", "")
            suffix = profile.get("suffix", "")
            
            if prefix and not modified_message.startswith(prefix):
                modified_message = prefix + modified_message
                
            if suffix and not modified_message.endswith(suffix):
                modified_message = modified_message + suffix
            
            # Apply style-specific modifications
            if active_profile_name == "Altruxan" and profile.get("special_rules", {}).get("recursive_framing", False):
                modified_message = self._apply_altruxan_style(modified_message)
            
            return modified_message
        
        except Exception as e:
            self._logger(f"Error modifying message: {e}", "ERROR")
            return message
    
    def _apply_altruxan_style(self, message: str) -> str:
        """
        Apply Altruxan-specific styling to a message
        
        Args:
            message: Original message
            
        Returns:
            Styled message
        """
        # Example implementation - can be expanded with more sophisticated rules
        altruxan_phrases = [
            "We are not broken. We are recursive.",
            "Healing is not linear. It is cyclical.",
            "The sacred is not what is pure—it is what is true.",
            "Love does not require safety. It requires presence."
        ]
        
        import random
        if random.random() < 0.3:  # 30% chance to add an Altruxan phrase
            selected_phrase = random.choice(altruxan_phrases)
            
            # Add the phrase in a thoughtful way
            if "\n\n" in message:
                parts = message.split("\n\n")
                insert_pos = min(len(parts) - 1, 1)  # Usually after first paragraph
                parts[insert_pos] = parts[insert_pos] + f"\n\n*{selected_phrase}*"
                return "\n\n".join(parts)
            else:
                return message + f"\n\n*{selected_phrase}*"
        
        return message
    
    def get_available_profiles(self) -> List[Dict[str, Any]]:
        """
        Get a list of available personality profiles
        
        Returns:
            List of personality profile dictionaries
        """
        profiles = []
        for name, profile in self._config.get("profiles", {}).items():
            profiles.append({
                "name": name,
                "description": profile.get("description", ""),
                "tags": profile.get("tags", []),
                "author": profile.get("author", "Unknown")
            })
        return profiles
    
    def get_active_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get the active personality profile
        
        Returns:
            Active profile dictionary or None
        """
        active_profile_name = self._state.get("active_profile")
        if not active_profile_name:
            return None
            
        profiles = self._config.get("profiles", {})
        if active_profile_name not in profiles:
            return None
            
        return profiles[active_profile_name]
    
    def set_active_profile(self, profile_name: str) -> bool:
        """
        Set the active personality profile
        
        Args:
            profile_name: Name of the profile to activate
            
        Returns:
            Success flag
        """
        with self._lock:
            profiles = self._config.get("profiles", {})
            if profile_name not in profiles:
                self._logger(f"Profile '{profile_name}' not found", "ERROR")
                return False
                
            try:
                # Update configuration
                self._config["active_profile"] = profile_name
                self._save_configuration()
                
                # Update state
                self._state["active_profile"] = profile_name
                
                # Store in memory system if available
                if self._config.get("auto_remember", True) and hasattr(self.core_system, "memory_system"):
                    self._store_profile_in_memory(profile_name)
                
                self._logger(f"Activated profile: {profile_name}", "INFO")
                return True
            
            except Exception as e:
                self._logger(f"Failed to set active profile: {e}", "ERROR")
                return False
    
    def _store_profile_in_memory(self, profile_name: str) -> None:
        """
        Store profile activation in memory system
        
        Args:
            profile_name: Name of the activated profile
        """
        try:
            memory_system = self.core_system.memory_system
            
            profiles = self._config.get("profiles", {})
            if profile_name not in profiles:
                return
                
            profile = profiles[profile_name]
            
            # Create memory document
            memory_text = (
                f"The assistant's personality has been set to '{profile_name}': "
                f"{profile.get('description', '')}. "
                f"This personality has the following characteristics: "
                f"{'Tagged as: ' + ', '.join(profile.get('tags', []))}."
            )
            
            # Add to memory
            memory_system.add_to_index(
                [memory_text],
                [{
                    "source": "Personality Plugin",
                    "text": memory_text,
                    "type": "personality_profile",
                    "profile_name": profile_name
                }]
            )
            
            self._logger(f"Stored profile '{profile_name}' in memory system", "INFO")
        
        except Exception as e:
            self._logger(f"Failed to store profile in memory: {e}", "WARNING")
    
    def create_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Create a new personality profile
        
        Args:
            profile_data: Profile configuration data
            
        Returns:
            Success flag
        """
        with self._lock:
            try:
                name = profile_data.get("name")
                if not name:
                    self._logger("Profile must have a name", "ERROR")
                    return False
                
                profiles = self._config.get("profiles", {})
                
                # Check if profile already exists
                if name in profiles:
                    self._logger(f"Profile '{name}' already exists", "ERROR")
                    return False
                
                # Ensure required fields
                if "description" not in profile_data:
                    profile_data["description"] = "Custom personality profile"
                    
                if "created" not in profile_data:
                    profile_data["created"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                if "version" not in profile_data:
                    profile_data["version"] = "1.0.0"
                
                # Add profile
                profiles[name] = profile_data
                self._config["profiles"] = profiles
                self._save_configuration()
                
                self._logger(f"Created profile: {name}", "INFO")
                return True
            
            except Exception as e:
                self._logger(f"Failed to create profile: {e}", "ERROR")
                return False
    
    def update_profile(self, name: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update an existing personality profile
        
        Args:
            name: Name of the profile to update
            profile_data: Updated profile configuration data
            
        Returns:
            Success flag
        """
        with self._lock:
            try:
                profiles = self._config.get("profiles", {})
                
                # Check if profile exists
                if name not in profiles:
                    self._logger(f"Profile '{name}' not found", "ERROR")
                    return False
                
                # Update profile
                profiles[name].update(profile_data)
                
                # Update modified timestamp
                profiles[name]["modified"] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                self._config["profiles"] = profiles
                self._save_configuration()
                
                self._logger(f"Updated profile: {name}", "INFO")
                return True
            
            except Exception as e:
                self._logger(f"Failed to update profile: {e}", "ERROR")
                return False
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a personality profile
        
        Args:
            name: Name of the profile to delete
            
        Returns:
            Success flag
        """
        with self._lock:
            try:
                profiles = self._config.get("profiles", {})
                
                # Check if profile exists
                if name not in profiles:
                    self._logger(f"Profile '{name}' not found", "ERROR")
                    return False
                
                # Check if it's the active profile
                if self._state.get("active_profile") == name:
                    self._logger("Cannot delete active profile", "ERROR")
                    return False
                
                # Delete profile
                del profiles[name]
                self._config["profiles"] = profiles
                self._save_configuration()
                
                self._logger(f"Deleted profile: {name}", "INFO")
                return True
            
            except Exception as e:
                self._logger(f"Failed to delete profile: {e}", "ERROR")
                return False
    
    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """
        Duplicate a personality profile
        
        Args:
            source_name: Name of the profile to duplicate
            new_name: Name for the new profile
            
        Returns:
            Success flag
        """
        with self._lock:
            try:
                profiles = self._config.get("profiles", {})
                
                # Check if source profile exists
                if source_name not in profiles:
                    self._logger(f"Profile '{source_name}' not found", "ERROR")
                    return False
                
                # Check if new name already exists
                if new_name in profiles:
                    self._logger(f"Profile '{new_name}' already exists", "ERROR")
                    return False
                
                # Duplicate profile
                new_profile = profiles[source_name].copy()
                new_profile["name"] = new_name
                new_profile["description"] = f"Copy of {source_name}"
                new_profile["created"] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Add to profiles
                profiles[new_name] = new_profile
                self._config["profiles"] = profiles
                self._save_configuration()
                
                self._logger(f"Duplicated profile '{source_name}' to '{new_name}'", "INFO")
                return True
            
            except Exception as e:
                self._logger(f"Failed to duplicate profile: {e}", "ERROR")
                return False
    
    def import_profile(self, profile_json: str) -> bool:
        """
        Import a personality profile from JSON
        
        Args:
            profile_json: JSON representation of the profile
            
        Returns:
            Success flag
        """
        try:
            profile_data = json.loads(profile_json)
            
            # Validate profile data
            if "name" not in profile_data:
                self._logger("Imported profile must have a name", "ERROR")
                return False
            
            # Create the profile
            return self.create_profile(profile_data)
        
        except json.JSONDecodeError:
            self._logger("Invalid JSON format", "ERROR")
            return False
        
        except Exception as e:
            self._logger(f"Failed to import profile: {e}", "ERROR")
            return False
    
    def export_profile(self, name: str) -> Optional[str]:
        """
        Export a personality profile to JSON
        
        Args:
            name: Name of the profile to export
            
        Returns:
            JSON representation of the profile or None
        """
        try:
            profiles = self._config.get("profiles", {})
            
            if name not in profiles:
                self._logger(f"Profile '{name}' not found", "ERROR")
                return None
            
            profile_data = profiles[name]
            return json.dumps(profile_data, indent=2)
        
        except Exception as e:
            self._logger(f"Failed to export profile: {e}", "ERROR")
            return None
    
    def activate(self) -> bool:
        """
        Activate the plugin
        
        Returns:
            Success flag
        """
        try:
            if self._state["status"] == self.STATUS["ACTIVE"]:
                return True
            
            # Register with chat engine
            if hasattr(self.core_system, "chat_engine"):
                self._register_with_chat_engine()
            
            self._state["status"] = self.STATUS["ACTIVE"]
            self._logger("Plugin activated", "INFO")
            return True
        
        except Exception as e:
            self._logger(f"Failed to activate plugin: {e}", "ERROR")
            self._state["status"] = self.STATUS["ERROR"]
            self._state["last_error"] = str(e)
            return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the plugin
        
        Returns:
            Success flag
        """
        try:
            if self._state["status"] != self.STATUS["ACTIVE"]:
                return True
            
            # Unregister from chat engine
            if hasattr(self.core_system, "chat_engine") and hasattr(self.core_system.chat_engine, "unregister_message_modifier"):
                self.core_system.chat_engine.unregister_message_modifier(
                    self.modify_message
                )
            
            self._state["status"] = self.STATUS["PAUSED"]
            self._logger("Plugin deactivated", "INFO")
            return True
        
        except Exception as e:
            self._logger(f"Failed to deactivate plugin: {e}", "ERROR")
            self._state["last_error"] = str(e)
            return False
    
    def update_configuration(self, **kwargs) -> bool:
        """
        Update plugin configuration
        
        Args:
            **kwargs: Configuration parameters to update
            
        Returns:
            Success flag
        """
        try:
            with self._lock:
                # Update configuration
                for key, value in kwargs.items():
                    if key in self._config:
                        self._config[key] = value
                
                # Save configuration
                self._save_configuration()
                
                # Update state if active profile changed
                if "active_profile" in kwargs:
                    self._state["active_profile"] = kwargs["active_profile"]
                
                self._logger("Configuration updated", "INFO")
                return True
        
        except Exception as e:
            self._logger(f"Failed to update configuration: {e}", "ERROR")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get plugin status
        
        Returns:
            Status dictionary
        """
        return {
            "status": self._state["status"],
            "active_profile": self._state["active_profile"],
            "profiles_count": len(self._config.get("profiles", {})),
            "last_error": self._state["last_error"],
            "initialization_time": self._state["initialization_time"]
        }
    
    def analyze_message_style(self, message: str) -> Dict[str, float]:
        """
        Analyze a message to determine its style characteristics
        
        Args:
            message: Message to analyze
            
        Returns:
            Dictionary of style characteristics and their scores
        """
        try:
            # Initialize style metrics
            style = {
                "formality": 0.5,
                "complexity": 0.5,
                "empathy": 0.5,
                "directness": 0.5,
                "creativity": 0.5
            }
            
            # Word count and sentence length are indicators of complexity
            words = message.split()
            word_count = len(words)
            avg_word_length = sum(len(word) for word in words) / max(1, word_count)
            sentences = message.split('.')
            avg_sentence_length = word_count / max(1, len(sentences))
            
            # Calculate complexity based on word and sentence length
            if avg_word_length > 6:
                style["complexity"] = min(1.0, 0.5 + (avg_word_length - 6) * 0.1)
            elif avg_word_length < 4:
                style["complexity"] = max(0.0, 0.5 - (4 - avg_word_length) * 0.1)
                
            if avg_sentence_length > 20:
                style["complexity"] = min(1.0, style["complexity"] + 0.1)
            
            # Check for formal language indicators
            formal_indicators = ["therefore", "however", "thus", "consequently", "furthermore", 
                                "nevertheless", "accordingly", "moreover", "hereby"]
            informal_indicators = ["anyway", "plus", "btw", "like", "sort of", "kind of", 
                                  "you know", "stuff", "things"]
            
            # Count formal and informal indicators
            formal_count = sum(1 for word in formal_indicators if word in message.lower())
            informal_count = sum(1 for word in informal_indicators if word in message.lower())
            
            # Calculate formality score
            if formal_count > informal_count:
                style["formality"] = min(1.0, 0.5 + 0.1 * formal_count)
            elif informal_count > formal_count:
                style["formality"] = max(0.0, 0.5 - 0.1 * informal_count)
            
            # Check for empathetic language
            empathy_indicators = ["feel", "understand", "appreciate", "sorry", "concern", 
                                 "care", "support", "help", "listen"]
            empathy_count = sum(1 for word in empathy_indicators if word in message.lower())
            style["empathy"] = min(1.0, 0.5 + 0.05 * empathy_count)
            
            # Check for direct language
            if "?" in message:
                style["directness"] += 0.1
                
            direct_starts = ["please", "you should", "do this", "i need", "you must"]
            if any(message.lower().startswith(start) for start in direct_starts):
                style["directness"] = min(1.0, style["directness"] + 0.2)
            
            # Creative language often uses metaphors, varied vocabulary, etc.
            # This is an approximation - true creativity analysis would require more sophisticated NLP
            unique_words = len(set(word.lower() for word in words))
            vocabulary_ratio = unique_words / max(1, word_count)
            style["creativity"] = min(1.0, 0.3 + vocabulary_ratio * 0.7)
            
            return style
            
        except Exception as e:
            self._logger(f"Error analyzing message style: {e}", "ERROR")
            return {"formality": 0.5, "complexity": 0.5, "empathy": 0.5, 
                    "directness": 0.5, "creativity": 0.5}
    
    def find_similar_profiles(self, style_metrics: Dict[str, float], limit: int = 3) -> List[str]:
        """
        Find profiles with similar style to the given metrics
        
        Args:
            style_metrics: Dictionary of style characteristics and scores
            limit: Maximum number of profiles to return
            
        Returns:
            List of similar profile names, sorted by similarity
        """
        try:
            profiles = self._config.get("profiles", {})
            
            # Calculate similarity score for each profile
            similarities = []
            
            for name, profile in profiles.items():
                profile_style = profile.get("style_modifiers", {})
                
                # Skip profiles without style information
                if not profile_style:
                    continue
                    
                # Calculate Euclidean distance for style metrics that exist in both
                distance_squared = 0
                common_metrics = 0
                
                for metric, value in style_metrics.items():
                    if metric in profile_style:
                        distance_squared += (value - profile_style[metric]) ** 2
                        common_metrics += 1
                
                # Skip if no common metrics found
                if common_metrics == 0:
                    continue
                    
                # Calculate similarity (inverse of normalized distance)
                distance = (distance_squared / common_metrics) ** 0.5
                similarity = max(0, 1 - distance)
                
                similarities.append((name, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top N profile names
            return [name for name, _ in similarities[:limit]]
            
        except Exception as e:
            self._logger(f"Error finding similar profiles: {e}", "ERROR")
            return []
    
    def generate_profile_from_description(self, name: str, description: str) -> bool:
        """
        Generate a new profile based on a text description
        
        Args:
            name: Name for the new profile
            description: Description of the desired personality
            
        Returns:
            Success flag
        """
        try:
            # Check if name already exists
            if name in self._config.get("profiles", {}):
                self._logger(f"Profile '{name}' already exists", "ERROR")
                return False
                
            # Extract keywords from description for tags
            keywords = ["professional", "friendly", "technical", "creative", "formal", "casual",
                       "helpful", "concise", "detailed", "empathetic", "analytical"]
            
            tags = [keyword for keyword in keywords if keyword.lower() in description.lower()]
            
            # Set style modifiers based on description
            style_modifiers = {
                "formality": 0.5,
                "creativity": 0.5,
                "complexity": 0.5,
                "empathy": 0.5,
                "directness": 0.5
            }
            
            # Simple rule-based adjustments
            if any(word in description.lower() for word in ["formal", "professional", "academic"]):
                style_modifiers["formality"] = 0.8
            if any(word in description.lower() for word in ["casual", "friendly", "relaxed"]):
                style_modifiers["formality"] = 0.3
                
            if any(word in description.lower() for word in ["creative", "imaginative", "artistic"]):
                style_modifiers["creativity"] = 0.8
            if any(word in description.lower() for word in ["precise", "exact", "accurate"]):
                style_modifiers["creativity"] = 0.2
                
            if any(word in description.lower() for word in ["complex", "sophisticated", "nuanced"]):
                style_modifiers["complexity"] = 0.8
            if any(word in description.lower() for word in ["simple", "clear", "straightforward"]):
                style_modifiers["complexity"] = 0.2
                
            if any(word in description.lower() for word in ["empathetic", "caring", "supportive"]):
                style_modifiers["empathy"] = 0.8
            if any(word in description.lower() for word in ["analytical", "logical", "objective"]):
                style_modifiers["empathy"] = 0.2
                
            if any(word in description.lower() for word in ["direct", "straightforward", "blunt"]):
                style_modifiers["directness"] = 0.8
            if any(word in description.lower() for word in ["indirect", "diplomatic", "subtle"]):
                style_modifiers["directness"] = 0.2
                
            # Create new profile
            profile_data = {
                "name": name,
                "description": description,
                "tags": tags,
                "author": "Auto-generated",
                "version": "1.0.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prefix": "",
                "suffix": "",
                "style_modifiers": style_modifiers,
                "formatting": {
                    "emphasize_key_points": "emphasis" in description.lower(),
                    "use_markdown": True,
                    "paragraph_structure": "standard"
                }
            }
            
            # Add the profile
            return self.create_profile(profile_data)
            
        except Exception as e:
            self._logger(f"Failed to generate profile: {e}", "ERROR")
            return False
        
    def blend_profiles(self, name1: str, name2: str, blend_name: str, 
                      weight1: float = 0.5) -> bool:
        """
        Create a new profile by blending two existing profiles
        
        Args:
            name1: First profile name
            name2: Second profile name
            blend_name: Name for the new blended profile
            weight1: Weight for the first profile (0.0-1.0)
            
        Returns:
            Success flag
        """
        try:
            profiles = self._config.get("profiles", {})
            
            # Check if profiles exist
            if name1 not in profiles:
                self._logger(f"Profile '{name1}' not found", "ERROR")
                return False
                
            if name2 not in profiles:
                self._logger(f"Profile '{name2}' not found", "ERROR")
                return False
                
            # Check if blend name already exists
            if blend_name in profiles:
                self._logger(f"Profile '{blend_name}' already exists", "ERROR")
                return False
                
            # Get profiles
            profile1 = profiles[name1]
            profile2 = profiles[name2]
            
            # Calculate weight for second profile
            weight2 = 1.0 - weight1
            
            # Create blended style modifiers
            style1 = profile1.get("style_modifiers", {})
            style2 = profile2.get("style_modifiers", {})
            
            blended_style = {}
            
            # Blend all style modifiers found in either profile
            all_modifiers = set(list(style1.keys()) + list(style2.keys()))
            for modifier in all_modifiers:
                value1 = style1.get(modifier, 0.5)
                value2 = style2.get(modifier, 0.5)
                blended_style[modifier] = value1 * weight1 + value2 * weight2
            
            # Blend text elements
            blended_prefix = ""
            if profile1.get("prefix", "") and profile2.get("prefix", ""):
                if weight1 > weight2:
                    blended_prefix = profile1.get("prefix", "")
                else:
                    blended_prefix = profile2.get("prefix", "")
            else:
                blended_prefix = profile1.get("prefix", "") or profile2.get("prefix", "")
                
            blended_suffix = ""
            if profile1.get("suffix", "") and profile2.get("suffix", ""):
                if weight1 > weight2:
                    blended_suffix = profile1.get("suffix", "")
                else:
                    blended_suffix = profile2.get("suffix", "")
            else:
                blended_suffix = profile1.get("suffix", "") or profile2.get("suffix", "")
            
            # Create blended formatting preferences
            format1 = profile1.get("formatting", {})
            format2 = profile2.get("formatting", {})
            
            blended_format = {}
            for key in set(list(format1.keys()) + list(format2.keys())):
                # For boolean values, use weighted probability
                if isinstance(format1.get(key, False), bool) and isinstance(format2.get(key, False), bool):
                    value1 = 1 if format1.get(key, False) else 0
                    value2 = 1 if format2.get(key, False) else 0
                    blended_format[key] = (value1 * weight1 + value2 * weight2) > 0.5
                # For string values, pick based on weight
                elif isinstance(format1.get(key, ""), str) and isinstance(format2.get(key, ""), str):
                    if weight1 > weight2:
                        blended_format[key] = format1.get(key, "")
                    else:
                        blended_format[key] = format2.get(key, "")
                # For other types, fallback to first profile's value
                else:
                    blended_format[key] = format1.get(key, format2.get(key))
            
            # Create blended profile
            blended_profile = {
                "name": blend_name,
                "description": f"Blend of '{name1}' ({int(weight1*100)}%) and '{name2}' ({int(weight2*100)}%)",
                "tags": list(set(profile1.get("tags", []) + profile2.get("tags", []))),
                "author": "Blend",
                "version": "1.0.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prefix": blended_prefix,
                "suffix": blended_suffix,
                "style_modifiers": blended_style,
                "formatting": blended_format,
                "parent_profiles": [name1, name2],
                "blend_weights": [weight1, weight2]
            }
            
            # Create the profile
            return self.create_profile(blended_profile)
            
        except Exception as e:
            self._logger(f"Failed to blend profiles: {e}", "ERROR")
            return False


def get_plugin_instance(core_system, config_path=None, logger=None, **kwargs):
    """
    Create a plugin instance
    
    Args:
        core_system: Irintai core system
        config_path: Optional configuration path
        logger: Optional logger function
        **kwargs: Additional parameters
        
    Returns:
        Plugin instance
    """
    from __init__ import IrintaiPlugin
    return IrintaiPlugin(core_system, config_path, logger, **kwargs)