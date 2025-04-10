# Irintai Module Development Guide

## 1. Module Development Workflow

### 1.1 Module Creation Checklist
- [ ] Identify Module Purpose
- [ ] Define Core Responsibilities
- [ ] Determine Integration Points
- [ ] Design Core Class Structure
- [ ] Implement Core Functionality
- [ ] Add Error Handling
- [ ] Create Comprehensive Logging
- [ ] Develop UI Component (if applicable)
- [ ] Write Documentation
- [ ] Implement Unit Tests

## 2. Module Template Generator

### 2.1 Core Module Template

```python
# core/module_name.py
"""
Module Description: Comprehensive explanation of module purpose and functionality
"""
import os
import json
from typing import Dict, List, Any, Optional, Callable

class ModuleNameManager:
    """
    Primary management class for the module
    
    Follows Irintai architectural principles:
    - Clear type annotations
    - Comprehensive error handling
    - Flexible configuration
    - Logging support
    """
    
    # Class-level constants for status and configuration
    MODULE_STATUS = {
        "INACTIVE": "Not Initialized",
        "LOADING": "Loading...",
        "ACTIVE": "Operational",
        "ERROR": "System Error"
    }
    
    def __init__(
        self, 
        config_path: str,
        logger: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the module manager
        
        Args:
            config_path: Path to module configuration
            logger: Optional logging function
            **kwargs: Additional configuration parameters
        """
        # Validate and set core configuration
        self.config_path = config_path
        self.log = logger or self._default_logger
        
        # Create configuration directory if not exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Core module state tracking
        self.status = self.MODULE_STATUS["INACTIVE"]
        self.configuration: Dict[str, Any] = {}
        
        # Additional initialization from kwargs
        self._initialize_module(**kwargs)
    
    def _default_logger(self, message: str, level: str = "INFO") -> None:
        """
        Fallback logging method if no logger provided
        
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
            
            # Update with provided kwargs
            self.configuration.update(kwargs)
            
            # Perform initial setup
            self._validate_configuration()
            
            # Update status
            self.status = self.MODULE_STATUS["ACTIVE"]
            
            self.log(f"[Module] Initialized successfully", "INFO")
        
        except Exception as e:
            self.status = self.MODULE_STATUS["ERROR"]
            self.log(f"[Module Error] Initialization failed: {e}", "ERROR")
    
    def _load_configuration(self) -> None:
        """
        Load module configuration from file
        
        Raises:
            FileNotFoundError: If configuration file is missing
            JSONDecodeError: If configuration is invalid
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.configuration = json.load(f)
            else:
                # Create default configuration if not exists
                self.configuration = self._generate_default_config()
                self._save_configuration()
        
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log(f"[Config Error] {e}", "WARNING")
            self.configuration = self._generate_default_config()
    
    def _generate_default_config(self) -> Dict[str, Any]:
        """
        Generate a default configuration
        
        Returns:
            Dictionary with default module settings
        """
        return {
            "version": "1.0.0",
            "enabled": True,
            # Add module-specific default configurations
        }
    
    def _validate_configuration(self) -> None:
        """
        Validate the current configuration
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Implement specific validation logic
        if not self.configuration.get("enabled", False):
            raise ValueError("Module is disabled in configuration")
    
    def _save_configuration(self) -> None:
        """
        Save current configuration to file
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
```

### 2.2 UI Panel Template

```python
# ui/module_name_panel.py
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

class ModuleNamePanel:
    """
    UI Panel for module interaction and configuration
    
    Follows Irintai UI component design principles:
    - Modular design
    - Consistent theming
    - Clear interaction patterns
    """
    
    def __init__(
        self, 
        parent: tk.Tk | ttk.Notebook,
        module_manager: Any,
        logger: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the module panel
        
        Args:
            parent: Parent Tkinter widget
            module_manager: Corresponding module manager instance
            logger: Optional logging function
            **kwargs: Additional configuration parameters
        """
        self.parent = parent
        self.module_manager = module_manager
        self.log = logger or print
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Initialize UI components
        self._create_ui_components(**kwargs)
    
    def _create_ui_components(self, **kwargs) -> None:
        """
        Create and layout UI components
        
        Args:
            **kwargs: Flexible configuration options
        """
        # Implement module-specific UI creation
        self._create_configuration_section()
        self._create_status_section()
        self._create_action_buttons()
    
    def _create_configuration_section(self) -> None:
        """
        Create configuration input elements
        """
        # Implement configuration UI elements
        pass
    
    def _create_status_section(self) -> None:
        """
        Display module status and metadata
        """
        # Create labels, progress indicators
        pass
    
    def _create_action_buttons(self) -> None:
        """
        Create interaction buttons for the module
        """
        # Implement module-specific action buttons
        pass
```

## 3. Module Integration Strategies

### 3.1 Core Integration Patterns

1. **Dependency Injection**
   - Pass module instances through constructor
   - Use configuration managers for shared settings
   - Minimize direct dependencies

2. **Event-Driven Communication**
   - Implement callback mechanisms
   - Use publish-subscribe patterns
   - Create clear communication interfaces

### 3.2 Configuration Management

- Use JSON for persistent configuration
- Implement default configuration generation
- Create validation methods
- Support runtime configuration updates

### 3.3 Error Handling Best Practices

- Use specific, descriptive exceptions
- Log all error scenarios
- Provide user-friendly error messages
- Implement graceful degradation

## 4. Development Recommendations

### 4.1 Pre-Development Checklist
- [ ] Define clear module responsibilities
- [ ] Identify integration points
- [ ] Design configuration schema
- [ ] Plan error handling strategy
- [ ] Sketch UI mockups (if applicable)

### 4.2 Development Phases
1. Core Logic Implementation
2. Configuration Management
3. Error Handling
4. Logging
5. UI Integration
6. Testing
7. Documentation

## 5. Testing Strategies

### 5.1 Test Coverage Requirements
- [ ] Unit tests for core methods
- [ ] Configuration validation tests
- [ ] Error handling scenarios
- [ ] Integration tests
- [ ] UI interaction tests

### 5.2 Recommended Testing Framework
- pytest for Python backend
- tkinter's testing utilities
- Mock objects for dependency simulation

## 6. Documentation Guidelines

### 6.1 Documentation Components
- Module purpose
- Architectural overview
- Configuration schema
- Method descriptions
- Integration instructions
- Example usage

## 7. Continuous Improvement

### 7.1 Feedback Loop
- Regular code reviews
- Performance monitoring
- User feedback integration
- Iterative refinement

## 8. Example Module Creation Workflow

```bash
# Module creation process
mkdir -p irintai/core/new_module
mkdir -p irintai/ui/new_module_panel
mkdir -p irintai/tests/new_module

# Create core module
touch irintai/core/new_module/module_manager.py
touch irintai/core/new_module/__init__.py

# Create UI panel
touch irintai/ui/new_module_panel.py

# Create tests
touch irintai/tests/new_module/test_module_manager.py
```

## Conclusion

This comprehensive guide provides a structured approach to creating new modules in the Irintai system. By following these guidelines, developers can:

- Reduce development complexity
- Ensure consistency
- Minimize debugging time
- Create extensible, maintainable modules

---

**Recommended Next Steps:**
1. Review existing modules
2. Study integration points
3. Design module specification
4. Create initial implementation
5. Conduct thorough testing
