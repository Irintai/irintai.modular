"""
Ollama Hub Plugin for Irintai Assistant

This plugin provides integration with Ollama Hub, allowing users to browse,
download, and manage Ollama models directly from the Irintai Assistant interface.
"""

import os
import sys
import json
import importlib
import threading
import logging
import re
import time
import pkg_resources
from typing import Dict, Any, Optional, Callable, List, Type, Union
from plugins.ollama_hub.core.ollama_client import OllamaClient

class PluginDependencyError(Exception):
    """
    Custom exception for plugin dependency issues
    """
    pass

class PluginConfigurationError(Exception):
    """
    Custom exception for plugin configuration errors
    """
    pass

class IrintaiPlugin:
    """
    Ollama Hub Plugin for Irintai Assistant
    
    Provides integration with Ollama model hub for:
    - Browsing available Ollama models
    - Downloading models from Ollama Hub
    - Managing local Ollama models
    - Using Ollama models with Irintai
    """
    
    # Plugin metadata
    METADATA = {
        "name": "Ollama Hub",
        "version": "1.0.0",
        "description": "Browse, download, and manage Ollama models",
        "author": "Irintai Team",
        "email": "contact@irintai.org",
        "license": "MIT",
        "dependencies": {
            "python": ">=3.8",
            "irintai": ">=1.0.0",
            "external_libs": ["requests"]
        },
        "capabilities": ["model_management", "ui_extension"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "server_url": {
                    "type": "string",
                    "description": "Ollama server URL",
                    "default": "http://localhost:11434"
                },                "auto_connect": {
                    "type": "boolean",
                    "description": "Automatically connect to Ollama server on startup",
                    "default": True
                }
            },
            "required": ["server_url"]
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
        plugin_id: str,
        core_system: Any,
        config_path: Optional[str] = None,
        logger: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the Ollama Hub plugin
        
        Args:
            plugin_id: Unique identifier for this plugin instance
            core_system: Reference to Irintai core system
            config_path: Path to plugin configuration
            logger: Optional logging function
            **kwargs: Additional initialization parameters
        """
        # Plugin identity
        self.plugin_id = plugin_id
        
        # Core system reference
        self.core = core_system
        
        # Logging setup
        self._logger = logger or getattr(core_system, 'logger', None) or self._default_logger
        
        # Configuration management
        self._config_path = config_path or self._generate_config_path()
        self._config: Dict[str, Any] = {}
        self._state: Dict[str, Any] = {
            "status": self.STATUS["UNINITIALIZED"],
            "last_error": None,
            "initialization_time": None,
            "dependencies_loaded": False,
            "connection_status": "Not connected"
        }
        
        # UI components
        self.ui_components = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize plugin
        self._initialize_plugin(**kwargs)
    
    def _default_logger(
        self, 
        message: str, 
        level: str = "INFO"
    ) -> None:
        """
        Fallback logging method
        
        Args:
            message: Log message
            level: Logging level
        """
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        
        log_method = {
            "INFO": logging.info,
            "WARNING": logging.warning,
            "ERROR": logging.error,
            "DEBUG": logging.debug
        }.get(level.upper(), logging.info)
        
        log_method(f"[Ollama Hub] {message}")
    
    def _generate_config_path(self) -> str:
        """
        Generate default configuration path
        
        Returns:
            Path to plugin configuration file
        """
        return os.path.join(
            "data", 
            "plugins", 
            "ollama_hub", 
            "config.json"
        )
    
    def _initialize_plugin(self, **kwargs) -> None:
        """
        Comprehensive plugin initialization
        
        Args:
            **kwargs: Flexible initialization parameters
        """
        try:
            # Update state
            self._state["status"] = self.STATUS["INITIALIZING"]
            
            # Validate and load dependencies
            self._load_dependencies()
            
            # Load configuration
            self._load_configuration(**kwargs)
            
            # Validate configuration
            self._validate_configuration()
            
            # Perform plugin-specific initialization
            self._setup_plugin_resources()
            
            # Mark initialization complete
            self._state["status"] = self.STATUS["ACTIVE"]
            self._state["initialization_time"] = time.time()
            
            self.log(
                f"Plugin {self.METADATA['name']} initialized successfully", 
                "INFO"
            )
        
        except Exception as e:
            # Handle initialization errors
            self._state["status"] = self.STATUS["ERROR"]
            self._state["last_error"] = str(e)
            
            self.log(
                f"Plugin initialization failed: {e}", 
                "ERROR"
            )
            
            # Optionally raise for critical errors
            raise
    
    def _load_dependencies(self) -> None:
        """
        Load and validate plugin dependencies
        
        Raises:
            PluginDependencyError: If dependencies cannot be loaded
        """
        dependencies = self.METADATA.get("dependencies", {})
        
        # Check Python version
        python_req = dependencies.get("python")
        if python_req:
            import sys
            import pkg_resources
            
            if not pkg_resources.parse_version(
                sys.version.split()[0]
            ) >= pkg_resources.parse_version(python_req.replace(">=", "")):
                raise PluginDependencyError(
                    f"Requires Python {python_req}, "
                    f"current version: {sys.version.split()[0]}"
                )
        
        # Load external libraries
        for lib in dependencies.get("external_libs", []):
            try:
                importlib.import_module(lib)
            except ImportError:
                raise PluginDependencyError(
                    f"Missing required library: {lib}"
                )
        
        self._state["dependencies_loaded"] = True
    
    def _load_configuration(self, **kwargs) -> None:
        """
        Load and merge plugin configuration
        
        Args:
            **kwargs: Additional configuration parameters
        """
        try:
            # Check if configuration file exists
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r') as f:
                    file_config = json.load(f)
            else:
                # Create default configuration
                file_config = {}
            
            # Merge configurations
            default_config = self._generate_default_config()
            self._config = {**default_config, **file_config, **kwargs}
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            
            # Save merged configuration
            with open(self._config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        
        except (IOError, json.JSONDecodeError) as e:
            self.log(
                f"Configuration loading error: {e}", 
                "ERROR"
            )
            raise PluginConfigurationError(
                f"Failed to load configuration: {e}"
            )
    
    def _generate_default_config(self) -> Dict[str, Any]:
        """
        Generate default configuration based on metadata
        
        Returns:
            Default configuration dictionary
        """
        schema = self.METADATA.get("configuration_schema", {})
        default_config = {}
        
        # Generate defaults from schema
        for prop, details in schema.get("properties", {}).items():
            default_config[prop] = details.get("default")
        
        return default_config
    
    def _validate_configuration(self) -> None:
        """
        Validate plugin configuration against schema
        
        Raises:
            PluginConfigurationError: If configuration is invalid
        """
        schema = self.METADATA.get("configuration_schema", {})
        
        # Basic validation
        for prop in schema.get("required", []):
            if prop not in self._config or self._config[prop] is None:
                raise PluginConfigurationError(
                    f"Missing required configuration property: {prop}"
                )
        
        # Type checking
        for prop, value in self._config.items():
            if prop in schema.get("properties", {}):
                prop_schema = schema["properties"][prop]
                prop_type = prop_schema.get("type")
                
                if prop_type == "string" and not isinstance(value, str):
                    raise PluginConfigurationError(
                        f"Configuration property {prop} must be a string"
                    )
                elif prop_type == "boolean" and not isinstance(value, bool):
                    raise PluginConfigurationError(
                        f"Configuration property {prop} must be a boolean"
                    )
    def _setup_plugin_resources(self) -> None:
        """
        Set up plugin-specific resources
        """
        # Import UI components to register
        from plugins.ollama_hub.ui.ollama_tab import OllamaHubTab
        
        # Store UI components for activation
        self.ui_components["ollama_tab"] = OllamaHubTab
        
        # Create ollama client if present in core system
        if hasattr(self.core, "model_manager") and hasattr(self.core.model_manager, "ollama_client"):
            self.log("Using model_manager's ollama_client", "INFO")
            self.ollama_client = self.core.model_manager.ollama_client
        elif hasattr(self.core, "ollama_client"):
            self.log("Using core's ollama_client", "INFO")
            self.ollama_client = self.core.ollama_client
        else:
            # Try to import from core system with better error handling
            self.log("Attempting to create new ollama client", "INFO")
            try:
                import importlib.util
                # Try finding the core module first
                if importlib.util.find_spec("core.ollama_client"):
                    from plugins.ollama_hub.core.ollama_client import OllamaClient
                    self.ollama_client = OllamaClient(logger=self.log)
                    self.log("Created ollama client from core module", "INFO")
                else:
                    self.ollama_client = OllamaClient(logger=self.log)
                    self.log("Created ollama client from plugin module", "INFO")
            except ImportError as e:
                self.log(f"ImportError when creating ollama client: {e}", "ERROR")
                # Create our own client as last resort
                try:
                    self.ollama_client = OllamaClient(logger=self.log)
                    self.log("Created ollama client from plugin module (fallback)", "INFO")
                except ImportError as e2:
                    self.log(f"Failed to create ollama client: {e2}", "ERROR")
                    raise PluginDependencyError(f"Cannot create Ollama client: {e2}")
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message using the logger
        
        Args:
            message: The message to log
            level: The log level
        """
        if self._logger:
            self._logger(message, level)
    
    def activate(self) -> bool:
        """
        Activate the plugin
        
        Returns:
            Boolean indicating successful activation
        """
        with self._lock:
            # Check current status
            if self._state["status"] == self.STATUS["ACTIVE"]:
                self.log("Plugin already active", "WARNING")
                return True
            
            try:
                # Perform activation logic
                self._on_activate()
                
                # Update status
                self._state["status"] = self.STATUS["ACTIVE"]
                
                self.log(
                    f"Plugin {self.METADATA['name']} activated", 
                    "INFO"
                )
                return True
            
            except Exception as e:
                # Handle activation errors
                self._state["status"] = self.STATUS["ERROR"]
                self._state["last_error"] = str(e)
                
                self.log(
                    f"Plugin activation failed: {e}", 
                    "ERROR"
                )
                return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the plugin
        
        Returns:
            Boolean indicating successful deactivation
        """
        with self._lock:
            # Check current status
            if self._state["status"] in [
                self.STATUS["UNINITIALIZED"], 
                self.STATUS["DISABLED"]
            ]:
                self.log("Plugin not active", "WARNING")
                return True
            
            try:
                # Perform deactivation logic
                self._on_deactivate()
                
                # Update status
                self._state["status"] = self.STATUS["DISABLED"]
                
                self.log(
                    f"Plugin {self.METADATA['name']} deactivated", 
                    "INFO"
                )
                return True
            
            except Exception as e:
                # Handle deactivation errors
                self._state["status"] = self.STATUS["ERROR"]
                self._state["last_error"] = str(e)
                
                self.log(
                    f"Plugin deactivation failed: {e}", 
                    "ERROR"
                )
                return False
    
    def _on_activate(self) -> None:
        """
        Plugin-specific activation logic
        """
        # Auto-connect to Ollama server if configured
        if self._config.get("auto_connect", True):
            threading.Thread(
                target=self._connect_to_ollama_thread,
                args=(self._config.get("server_url", "http://localhost:11434"),),
                daemon=True
            ).start()
    
    def _on_deactivate(self) -> None:
        """
        Plugin-specific deactivation logic
        """
        # Clean up any resources
        self._state["connection_status"] = "Not connected"
    
    def update_configuration(
        self, 
        **kwargs
    ) -> bool:
        """
        Update plugin configuration
        
        Args:
            **kwargs: Configuration parameters to update
        
        Returns:
            Boolean indicating successful configuration update
        """
        with self._lock:
            try:
                # Merge new configuration
                self._config.update(kwargs)
                
                # Validate updated configuration
                self._validate_configuration()
                
                # Save updated configuration
                with open(self._config_path, 'w') as f:
                    json.dump(self._config, f, indent=2)
                
                # Optionally trigger reconfiguration
                self._on_configuration_update()
                
                self.log(
                    "Plugin configuration updated", 
                    "INFO"
                )
                return True
            
            except Exception as e:
                self.log(
                    f"Configuration update failed: {e}", 
                    "ERROR"
                )
                return False
    
    def _on_configuration_update(self) -> None:
        """
        Handle configuration updates
        """
        # Reconnect to Ollama server if URL changed
        if self._state["status"] == self.STATUS["ACTIVE"]:
            server_url = self._config.get("server_url")
            threading.Thread(
                target=self._connect_to_ollama_thread,
                args=(server_url,),
                daemon=True
            ).start()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive plugin status
        
        Returns:
            Dictionary with plugin status details
        """
        return {
            "name": self.METADATA["name"],
            "version": self.METADATA["version"],
            "status": self._state["status"],
            "last_error": self._state["last_error"],
            "connection_status": self._state.get("connection_status", "Not connected"),
            "initialization_time": self._state.get("initialization_time"),
            "config_path": self._config_path,
            "server_url": self._config.get("server_url")
        }
    
    def get_actions(self) -> Dict[str, Callable]:
        """
        Get the actions provided by this plugin for UI integration
        
        Returns:
            Dictionary of action names to callable functions
        """
        return {
            "Connect to Ollama": self.connect_to_ollama,
            "Refresh Models": self.fetch_ollama_models,
        }
    
    def register_ui_components(self, ui_registry):
        """
        Register UI components with the main application
        
        Args:
            ui_registry: The UI component registry to register with
        """
        if hasattr(ui_registry, 'register_tab'):
            # Register our tab component
            ui_registry.register_tab(
                "Model Panel",
                "Ollama Hub",
                self.ui_components["ollama_tab"],
                {"plugin_instance": self}
            )
            
            self.log("Registered UI components", "INFO")
    
    def connect_to_ollama(self):
        """
        Connect to the Ollama server using the configured URL
        """
        server_url = self._config.get("server_url", "http://localhost:11434")
        self._state["connection_status"] = "Connecting..."
        
        # Make connection attempt in a separate thread
        threading.Thread(
            target=self._connect_to_ollama_thread,
            args=(server_url,),
            daemon=True
        ).start()
    
    def _connect_to_ollama_thread(self, url):
        """
        Thread function for connecting to Ollama server
        
        Args:
            url: The Ollama server URL to connect to
        """
        try:
            import requests
            import json
            
            # Try to connect to Ollama server
            response = requests.get(f"{url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                # Connection successful
                self._state["connection_status"] = "Connected"
                self.log(f"Connected to Ollama server at {url}", "INFO")
                
                # Fetch models
                self.fetch_ollama_models()
            else:
                # Connection failed
                self._state["connection_status"] = "Connection failed"
                self.log(f"Connection failed: Server returned {response.status_code}", "ERROR")
                
        except Exception as e:
            # Connection error
            self._state["connection_status"] = "Connection failed"
            self.log(f"Connection failed: {e}", "ERROR")
    
    def fetch_ollama_models(self):
        """
        Fetch available models from Ollama
        
        Returns:
            Boolean indicating success and model data
        """
        url = self._config.get("server_url", "http://localhost:11434")
        if self._state["connection_status"] != "Connected":
            self.log("Not connected to Ollama server", "WARNING")
            return False, {"error": "Not connected to Ollama server"}
            
        # Fetch models in a separate thread
        threading.Thread(
            target=self._fetch_ollama_models_thread,
            args=(url,),
            daemon=True
        ).start()
        
        return True, {"status": "Fetching models..."}
    
    def _fetch_ollama_models_thread(self, url):
        """
        Thread function for fetching Ollama models
        
        Args:
            url: The Ollama server URL
        """
        try:
            # Get local models
            self.log("Fetching locally installed models...", "INFO")
            success_local, local_data = self.ollama_client.list_models(remote=False)
            local_models = {}
            
            if success_local:
                for model in local_data.get('models', []):
                    name = model.get('name', '')
                    local_models[name] = model
                self.log(f"Found {len(local_models)} locally installed models")
            else:
                error = local_data.get('error', 'Unknown error')
                self.log(f"Failed to fetch local models: {error}", "ERROR")
            
            # Get remote models
            self.log("Fetching remote models from Ollama Hub...", "INFO")
            success_remote, remote_data = self.ollama_client.list_models(remote=True)
            library_models = []
            
            if success_remote:
                remote_models = remote_data.get('models', [])
                self.log(f"Successfully fetched {len(remote_models)} remote models", "INFO")
                
                for model in remote_models:
                    name = model.get('name', '')
                    
                    # Extract parameter info from model name if possible
                    parameters = model.get('parameters', '')
                    if not parameters:
                        param_match = re.search(r'(\d+)b', name, re.IGNORECASE)
                        parameters = f"{param_match.group(1)}B" if param_match else "Unknown"
                    
                    # Check if model is already downloaded
                    is_local = name in local_models
                    
                    # Extract tags
                    tags = model.get('tags', [])
                    # If no tags but we can infer from name
                    if not tags:
                        if 'code' in name.lower() or 'coder' in name.lower():
                            tags.append('code')
                        if 'vision' in name.lower() or 'vl' in name.lower():
                            tags.append('vision')
                        if 'instruct' in name.lower():
                            tags.append('instruct')
                    
                    library_models.append({
                        'name': name,
                        'description': "Official Ollama model", 
                        'parameters': parameters,
                        'size': model.get('size', 'Unknown'),
                        'is_local': is_local,
                        'tags': tags
                    })
            else:
                error = remote_data.get('error', 'Unknown error')
                self.log(f"Failed to fetch remote models: {error}", "ERROR")
                
            # Notify UI components of model data update
            self._notify_model_update(local_models, library_models)
                
        except Exception as e:
            self.log(f"Error fetching models: {e}", "ERROR")
    
    def _notify_model_update(self, local_models, library_models):
        """
        Notify UI components of model data update
        
        Args:
            local_models: Dictionary of local models
            library_models: List of library models
        """
        # Use event system if available
        if hasattr(self.core, 'event_bus'):
            self.core.event_bus.publish(
                f"{self.plugin_id}.models_updated",
                {
                    "local_models": local_models,
                    "library_models": library_models
                }
            )
    
    def download_ollama_model(self, model_name):
        """
        Download an Ollama model
        
        Args:
            model_name: Name of the model to download
            
        Returns:
            Boolean indicating if download was started
        """
        if not model_name:
            self.log("No model name provided for download", "ERROR")
            return False
        
        # Start download in a separate thread
        threading.Thread(
            target=self._download_ollama_model_thread,
            args=(model_name,),
            daemon=True
        ).start()
        
        return True
    
    def _download_ollama_model_thread(self, model_name):
        """
        Thread function for downloading an Ollama model
        
        Args:
            model_name: Name of the model to download
        """
        try:
            # Define a progress callback for real-time updates
            def progress_callback(percentage):
                # Report progress
                if hasattr(self.core, 'event_bus'):
                    self.core.event_bus.publish(
                        f"{self.plugin_id}.download_progress",
                        {
                            "model": model_name,
                            "percentage": percentage
                        }
                    )

            # Download the model with progress tracking
            success, message = self.ollama_client.pull_model(
                model_name,
                progress_callback=progress_callback
            )

            # Update UI based on result
            if success:
                self.log(f"Successfully downloaded model {model_name}", "INFO")
                # Refresh the model list
                self.fetch_ollama_models()
                
                if hasattr(self.core, 'event_bus'):
                    self.core.event_bus.publish(
                        f"{self.plugin_id}.model_downloaded",
                        {
                            "model": model_name,
                            "success": True
                        }
                    )
            else:
                self.log(f"Failed to download model {model_name}: {message}", "ERROR")
                if hasattr(self.core, 'event_bus'):
                    self.core.event_bus.publish(
                        f"{self.plugin_id}.model_downloaded",
                        {
                            "model": model_name,
                            "success": False,
                            "error": message
                        }
                    )
                    
        except Exception as e:
            self.log(f"Error downloading model {model_name}: {e}", "ERROR")
            if hasattr(self.core, 'event_bus'):
                self.core.event_bus.publish(
                    f"{self.plugin_id}.model_downloaded",
                    {
                        "model": model_name,
                        "success": False,
                        "error": str(e)
                    }
                )
    
    def delete_ollama_model(self, model_name):
        """
        Delete an Ollama model
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            Boolean indicating if deletion was started
        """
        if not model_name:
            self.log("No model name provided for deletion", "ERROR")
            return False
        
        # Start deletion in a separate thread
        threading.Thread(
            target=self._delete_ollama_model_thread,
            args=(model_name,),
            daemon=True
        ).start()
        
        return True
    
    def _delete_ollama_model_thread(self, model_name):
        """
        Thread function for deleting an Ollama model
        
        Args:
            model_name: Name of the model to delete
        """
        try:
            # Delete the model
            success, message = self.ollama_client.delete_model(model_name)
            
            # Update UI based on result
            if success:
                self.log(f"Successfully deleted model {model_name}", "INFO")
                # Refresh the model list
                self.fetch_ollama_models()
                
                if hasattr(self.core, 'event_bus'):
                    self.core.event_bus.publish(
                        f"{self.plugin_id}.model_deleted",
                        {
                            "model": model_name,
                            "success": True
                        }
                    )
            else:
                self.log(f"Failed to delete model {model_name}: {message}", "ERROR")
                if hasattr(self.core, 'event_bus'):
                    self.core.event_bus.publish(
                        f"{self.plugin_id}.model_deleted",
                        {
                            "model": model_name,
                            "success": False,
                            "error": message
                        }
                    )
                    
        except Exception as e:
            self.log(f"Error deleting model {model_name}: {e}", "ERROR")
            if hasattr(self.core, 'event_bus'):
                self.core.event_bus.publish(
                    f"{self.plugin_id}.model_deleted",
                    {
                        "model": model_name,
                        "success": False,
                        "error": str(e)
                    }
                )

# Plugin registration information
plugin_info = {
    "name": "Ollama Hub",
    "description": "Browse, download, and manage Ollama models",
    "version": "1.0.0",
    "author": "Irintai Team",
    "url": "https://irintai.org/plugins/ollama-hub",
    "plugin_class": IrintaiPlugin,
    "compatibility": "1.0.0",
    "dependencies": [],
    "tags": ["ollama", "models", "hub", "download"]}