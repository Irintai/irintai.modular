# Irintai Plugin Development Template (Extended)

## 1. Plugin Development Workflow

### 1.1 Comprehensive Plugin Creation Checklist
- [ ] Define plugin purpose and requirements
- [ ] Design plugin architecture
- [ ] Create plugin metadata
- [ ] Implement core functionality
- [ ] Develop configuration management
- [ ] Implement dependency handling
- [ ] Add comprehensive error management
- [ ] Create plugin lifecycle methods
- [ ] Develop testing strategy
- [ ] Write documentation
- [ ] Implement security considerations

## 2. Complete Plugin Template

```python
# plugins/[plugin_name]/__init__.py
"""
[Plugin Name] Plugin for Irintai Assistant

Comprehensive plugin framework with advanced features
"""

import os
import sys
import json
import importlib
import threading
import logging
from typing import (
    Dict, 
    Any, 
    Optional, 
    Callable, 
    List, 
    Type, 
    Union
)

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
    Advanced Plugin Base Class for Irintai Assistant
    
    Comprehensive plugin management with:
    - Robust lifecycle management
    - Advanced configuration handling
    - Dependency management
    - Error handling
    - Logging support
    """
    
    # Plugin metadata template
    METADATA = {
        "name": "[Plugin Name]",
        "version": "1.0.0",
        "description": "Comprehensive plugin description",
        "author": "Your Name",
        "email": "contact@example.com",
        "license": "MIT",
        "dependencies": {
            "python": ">=3.8",
            "irintai": ">=1.0.0",
            "external_libs": []
        },
        "capabilities": [],
        "configuration_schema": {
            "type": "object",
            "properties": {},
            "required": []
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
        Initialize the advanced plugin
        
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
        self._config_path = config_path or self._generate_config_path()
        self._config: Dict[str, Any] = {}
        self._state: Dict[str, Any] = {
            "status": self.STATUS["UNINITIALIZED"],
            "last_error": None,
            "initialization_time": None,
            "dependencies_loaded": False
        }
        
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
        
        log_method(message)
    
    def _generate_config_path(self) -> str:
        """
        Generate default configuration path
        
        Returns:
            Path to plugin configuration file
        """
        plugin_name = self.METADATA.get("name", "unnamed_plugin")
        return os.path.join(
            "data", 
            "plugins", 
            plugin_name, 
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
            
            self._logger(
                f"Plugin {self.METADATA['name']} initialized successfully", 
                "INFO"
            )
        
        except Exception as e:
            # Handle initialization errors
            self._state["status"] = self.STATUS["ERROR"]
            self._state["last_error"] = str(e)
            
            self._logger(
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
            ) >= pkg_resources.parse_version(python_req):
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
            self._logger(
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
        
        # Implement JSON Schema validation
        try:
            import jsonschema
            jsonschema.validate(instance=self._config, schema=schema)
        except ImportError:
            self._logger(
                "jsonschema library not available. Skipping strict validation", 
                "WARNING"
            )
        except jsonschema.ValidationError as e:
            raise PluginConfigurationError(
                f"Configuration validation failed: {e}"
            )
    
    def _setup_plugin_resources(self) -> None:
        """
        Set up plugin-specific resources
        
        Override in specific plugin implementations
        """
        pass
    
    def activate(self) -> bool:
        """
        Activate the plugin
        
        Returns:
            Boolean indicating successful activation
        """
        with self._lock:
            # Check current status
            if self._state["status"] == self.STATUS["ACTIVE"]:
                self._logger("Plugin already active", "WARNING")
                return True
            
            try:
                # Perform activation logic
                self._on_activate()
                
                # Update status
                self._state["status"] = self.STATUS["ACTIVE"]
                
                self._logger(
                    f"Plugin {self.METADATA['name']} activated", 
                    "INFO"
                )
                return True
            
            except Exception as e:
                # Handle activation errors
                self._state["status"] = self.STATUS["ERROR"]
                self._state["last_error"] = str(e)
                
                self._logger(
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
                self._logger("Plugin not active", "WARNING")
                return True
            
            try:
                # Perform deactivation logic
                self._on_deactivate()
                
                # Update status
                self._state["status"] = self.STATUS["DISABLED"]
                
                self._logger(
                    f"Plugin {self.METADATA['name']} deactivated", 
                    "INFO"
                )
                return True
            
            except Exception as e:
                # Handle deactivation errors
                self._state["status"] = self.STATUS["ERROR"]
                self._state["last_error"] = str(e)
                
                self._logger(
                    f"Plugin deactivation failed: {e}", 
                    "ERROR"
                )
                return False
    
    def _on_activate(self) -> None:
        """
        Plugin-specific activation logic
        
        Override in specific plugin implementations
        """
        pass
    
    def _on_deactivate(self) -> None:
        """
        Plugin-specific deactivation logic
        
        Override in specific plugin implementations
        """
        pass
    
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
                
                self._logger(
                    "Plugin configuration updated", 
                    "INFO"
                )
                return True
            
            except Exception as e:
                self._logger(
                    f"Configuration update failed: {e}", 
                    "ERROR"
                )
                return False
    
    def _on_configuration_update(self) -> None:
        """
        Handle configuration updates
        
        Override for plugin-specific reconfiguration logic
        """
        pass
    
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
            "initialization_time": self._state.get("initialization_time"),
            "config_path": self._config_path
        }
    
    def get_interface(self) -> Dict[str, Callable]:
        """
        Provide plugin's public interface
        
        Returns:
            Dictionary of callable methods
        """
        return {
            method: getattr(self, method)
            for method in dir(self)
            if (callable(getattr(self, method)) 
                and not method.startswith('_')
                and method not in ['get_interface', 'get_status'])
        }

# Plugin Manager to handle multiple plugins
class PluginManager:
    """
    Manages plugin lifecycle and interactions
    """
    
    def __init__(
        self, 
        core_system: Any, 
        plugin_dir: str = "plugins"
    ):
        """
        Initialize plugin manager
        
        Args:
            core_system: Reference to Irintai core system
            plugin_dir: Directory containing plugins
        """
        self.core_system = core_system
        self.plugin_dir = plugin_dir
        self.loaded_plugins: Dict[str, IrintaiPlugin] = {}
    
    def load_plugins(self) -> None:
        """
        Discover and load all available plugins
        """
        # Implementation of plugin discovery and loading
        pass
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Activate a specific plugin
        
        Args:
            plugin_name: Name of the plugin to activate
        
        Returns:
            Boolean indicating successful activation
        """
        # Implementation of plugin activation
        pass
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Deactivate a specific plugin
        
        Args:
            plugin_name: Name of the plugin to deactivate
        
        Returns:
            Boolean indicating successful deactivation
        """
        # Implementation of plugin deactivation
        pass
```

## 3. Plugin Development Best Practices

### 3.1 Design Principles
- Loose coupling
- Minimal system impact
- Clear interfaces
- Comprehensive error handling
- Flexible configuration

### 3.2 Dependency Management (continued)
- Implement fallback dependency resolution
- Support optional and required dependencies
- Provide clear dependency conflict resolution

### 3.3 Configuration Management
- Use JSON Schema for configuration validation
- Support dynamic configuration updates
- Implement configuration versioning
- Provide default configuration generation

### 3.4 Security Considerations
- Validate all plugin inputs
- Implement sandboxing mechanisms
- Restrict plugin access to system resources
- Use principle of least privilege

## 4. Plugin Development Workflow

### 4.1 Development Stages
1. Conceptualization
   - Define plugin purpose
   - Identify core functionality
   - Outline integration points

2. Design
   - Create metadata specification
   - Define configuration schema
   - Plan dependency management
   - Design public interface

3. Implementation
   - Develop core functionality
   - Implement lifecycle methods
   - Create configuration handlers
   - Add error management

4. Testing
   - Unit testing
   - Integration testing
   - Compatibility testing
   - Performance benchmarking

5. Documentation
   - Write comprehensive README
   - Document configuration options
   - Provide usage examples
   - Create API reference

## 5. Plugin Testing Strategy

### 5.1 Test Coverage Requirements
- [ ] Initialization process
- [ ] Dependency validation
- [ ] Configuration management
- [ ] Activation and deactivation
- [ ] Error handling scenarios
- [ ] Interface consistency
- [ ] Performance under load

### 5.2 Testing Tools and Frameworks
- pytest for unit and integration testing
- Mock objects for dependency simulation
- Coverage.py for test coverage analysis
- Hypothesis for property-based testing

## 6. Plugin Deployment Considerations

### 6.1 Distribution Channels
- Local plugin directory
- Online plugin repository
- Bundled with core system
- User-submitted plugins

### 6.2 Version Compatibility
- Implement version checking
- Support backwards compatibility
- Provide clear upgrade paths
- Maintain compatibility matrices

## 7. Advanced Plugin Features

### 7.1 Event-Driven Architecture
- Subscribe to system events
- Publish custom events
- Support event filtering
- Implement event prioritization

### 7.2 Dynamic Loading
- Support hot-reloading
- Implement plugin isolation
- Provide runtime configuration
- Support partial plugin updates

## 8. Troubleshooting and Debugging

### 8.1 Error Handling Strategies
- Comprehensive logging
- Graceful degradation
- User-friendly error messages
- Detailed error reporting

### 8.2 Diagnostic Tools
- Provide plugin health checks
- Generate diagnostic reports
- Support remote debugging
- Implement telemetry options

## 9. Example Plugin Structure
my_plugin/
│
├── init.py          # Main plugin implementation
├── config.json          # Default configuration
├── README.md            # Plugin documentation
├── requirements.txt     # Dependency specification
│
├── core/                # Core plugin logic
│   ├── init.py
│   ├── main.py
│   └── helpers.py
│
├── ui/                  # Optional UI components
│   ├── init.py
│   └── panel.py
│
└── tests/               # Plugin test suite
├── init.py
├── test_core.py
└── test_integration.py

## 10. Contribution and Community Guidelines

### 10.1 Plugin Submission Process
- Comprehensive code review
- Automated testing
- Security scanning
- Performance evaluation

### 10.2 Maintenance Expectations
- Regular updates
- Compatibility maintenance
- Security patch support
- Community-driven improvements

## 11. Future Extensions

### 11.1 Planned Enhancements
- Machine learning plugin support
- Advanced sandboxing
- Multi-language plugin development
- Cloud plugin distribution

## Conclusion

This comprehensive plugin development template provides a robust framework for creating extensible, maintainable, and secure plugins for the Irintai Assistant system.

---

**Key Takeaways:**
- Follow modular design principles
- Prioritize security and performance
- Implement comprehensive error handling
- Create clear, consistent interfaces
- Support dynamic configuration
Recommendations for Plugin Developers

Start with the provided template
Customize to specific use case
Implement comprehensive testing
Document thoroughly
Follow best practices in error handling and configuration management