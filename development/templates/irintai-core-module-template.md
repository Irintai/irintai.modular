# Irintai Core Module Development Template

## Module Creation Checklist

### 1. Conceptualization
- [ ] Define module purpose
- [ ] Identify core responsibilities
- [ ] Determine integration points
- [ ] Assess data flow and interactions

### 2. Implementation Template

```python
# core/[module_name]/module_manager.py
"""
[Module Name] - [Brief Description of Module Functionality]

This module provides core functionality for [specific purpose]
in the Irintai assistant ecosystem.
"""

import os
import json
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

class [ModuleName]Manager:
    """
    Primary management class for [Module Name] functionality
    
    Core Responsibilities:
    - Configuration management
    - State tracking
    - Core operational logic
    - Error handling
    - Logging
    """
    
    # Module-specific status constants
    MODULE_STATUS = {
        "INACTIVE": "Not Initialized",
        "LOADING": "Loading Resources",
        "ACTIVE": "Operational",
        "ERROR": "System Error",
        "PAUSED": "Temporarily Suspended"
    }
    
    def __init__(
        self, 
        config_path: str = f"data/[module_name]/config.json",
        logger: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the module manager
        
        Args:
            config_path: Path to module configuration file
            logger: Optional logging function
            **kwargs: Additional configuration parameters
        """
        # Ensure configuration directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Core module attributes
        self.config_path = config_path
        self.log = logger or self._default_logger
        self.status = self.MODULE_STATUS["INACTIVE"]
        self.configuration: Dict[str, Any] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize module
        self._initialize_module(**kwargs)
    
    def _default_logger(self, message: str, level: str = "INFO") -> None:
        """
        Fallback logging method if no logger is provided
        
        Args:
            message: Log message
            level: Logging level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} [{level}] {message}")
    
    def _initialize_module(self, **kwargs) -> None:
        """
        Internal method to set up module-specific configurations
        
        Args:
            **kwargs: Flexible configuration parameters
        """
        try:
            # Load existing configuration
            self._load_configuration()
            
            # Update with provided parameters
            self.configuration.update(kwargs)
            
            # Validate configuration
            self._validate_configuration()
            
            # Perform any required setup
            self._setup_module_resources()
            
            # Update status
            self.status = self.MODULE_STATUS["ACTIVE"]
            
            self.log("[Module] Initialized successfully", "INFO")
        
        except Exception as e:
            self.status = self.MODULE_STATUS["ERROR"]
            self.log(f"[Module Error] Initialization failed: {e}", "ERROR")
    
    def _load_configuration(self) -> None:
        """
        Load module configuration from persistent storage
        
        Handles:
        - First-time configuration creation
        - Configuration file parsing
        - Default configuration generation
        """
        try:
            # Check if configuration exists
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.configuration = json.load(f)
            else:
                # Generate and save default configuration
                self.configuration = self._generate_default_config()
                self._save_configuration()
        
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log(f"[Config Error] {e}. Creating default configuration.", "WARNING")
            self.configuration = self._generate_default_config()
            self._save_configuration()
    
    def _generate_default_config(self) -> Dict[str, Any]:
        """
        Generate a default configuration for the module
        
        Returns:
            Dictionary with default module settings
        """
        return {
            "version": "1.0.0",
            "enabled": True,
            # Module-specific default configurations
            # Example:
            # "feature_flags": {},
            # "performance_settings": {},
        }
    
    def _validate_configuration(self) -> None:
        """
        Validate the current module configuration
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Implement specific validation logic
        if not self.configuration.get("enabled", False):
            raise ValueError("Module is currently disabled")
        
        # Add module-specific configuration validation
        # Example:
        # if not self._check_required_keys():
        #     raise ValueError("Missing required configuration keys")
    
    def _setup_module_resources(self) -> None:
        """
        Set up any required resources for the module
        
        Can include:
        - Creating necessary directories
        - Initializing databases
        - Loading external resources
        """
        # Implement module-specific resource setup
        pass
    
    def _save_configuration(self) -> None:
        """
        Save current configuration to persistent storage
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.configuration, f, indent=2)
            
            self.log("[Config] Configuration saved successfully", "INFO")
        
        except Exception as e:
            self.log(f"[Config Error] Failed to save configuration: {e}", "ERROR")
    
    def update_configuration(self, **kwargs) -> bool:
        """
        Update module configuration
        
        Args:
            **kwargs: Configuration parameters to update
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            with self._lock:
                # Update configuration
                self.configuration.update(kwargs)
                
                # Validate updated configuration
                self._validate_configuration()
                
                # Save changes
                self._save_configuration()
                
                return True
        
        except Exception as e:
            self.log(f"[Config Error] Configuration update failed: {e}", "ERROR")
            return False
    
    def get_status(self) -> str:
        """
        Retrieve current module status
        
        Returns:
            Current operational status
        """
        return self.status
    
    def reset(self) -> None:
        """
        Reset module to initial state
        """
        try:
            # Reset configuration to defaults
            self.configuration = self._generate_default_config()
            self._save_configuration()
            
            # Reinitialize module
            self._initialize_module()
            
            self.log("[Module] Reset to default configuration", "INFO")
        
        except Exception as e:
            self.log(f"[Module Error] Reset failed: {e}", "ERROR")
            self.status = self.MODULE_STATUS["ERROR"]

# Optional: Add module-specific implementation details
# Additional methods, core logic, etc.
```

## 3. Integration Considerations

### Configuration Management
- Use JSON for persistent configuration
- Implement default configuration generation
- Support runtime configuration updates
- Validate configuration inputs

### Error Handling
- Use specific, descriptive exceptions
- Log all error scenarios
- Provide user-friendly error messages
- Implement graceful degradation

### Logging
- Timestamp all log entries
- Use consistent log levels
- Support optional custom logger
- Provide fallback logging method

## 4. Development Checklist

### Pre-Development
- [ ] Define module purpose
- [ ] Identify core responsibilities
- [ ] Design configuration schema
- [ ] Plan error handling strategy

### Implementation Phases
1. Core Logic Implementation
2. Configuration Management
3. Error Handling
4. Logging
5. Integration Points
6. Testing
7. Documentation

## 5. Testing Strategies

### Test Coverage
- [ ] Unit tests for core methods
- [ ] Configuration validation
- [ ] Error handling scenarios
- [ ] Integration tests

## Appendix: Best Practices

1. Keep methods focused and modular
2. Use type hints consistently
3. Implement comprehensive logging
4. Validate all inputs
5. Design for extensibility
6. Minimize external dependencies
7. Write clear, descriptive docstrings

---

**Usage Notes:**
- Replace `[ModuleName]` and `[module_name]` with your specific module details
- Customize the template to fit specific module requirements
- Follow Irintai architectural and coding standards
