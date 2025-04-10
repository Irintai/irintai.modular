# Irintai Utility Module Development Template

## Utility Module Development Guide

### 1. Utility Module Characteristics
- Focused, single-responsibility design
- Minimal external dependencies
- High reusability
- Comprehensive error handling
- Performance optimization

### 2. Implementation Template

```python
# utils/[module_name].py
"""
[Module Name] Utility - [Brief Description of Utility Functionality]

Provides utility functions for [specific purpose] in the Irintai ecosystem.
"""

import os
import logging
from typing import (
    Dict, 
    List, 
    Any, 
    Optional, 
    Union, 
    Callable, 
    Tuple
)

class [ModuleName]Utility:
    """
    Utility class for handling [specific functionality]
    
    Core Responsibilities:
    - Provide specialized utility functions
    - Implement robust error handling
    - Support flexible configuration
    - Minimal external dependencies
    """
    
    def __init__(
        self, 
        logger: Optional[Callable] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the utility module
        
        Args:
            logger: Optional custom logging function
            config: Optional configuration dictionary
        """
        # Logging setup
        self.log = logger or self._default_logger
        
        # Configuration management
        self.config = config or self._generate_default_config()
        
        # Initialize any required resources
        self._initialize_resources()
    
    def _default_logger(
        self, 
        message: str, 
        level: str = "INFO"
    ) -> None:
        """
        Fallback logging method if no logger is provided
        
        Args:
            message: Log message
            level: Logging level (INFO, WARNING, ERROR)
        """
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        
        log_method = {
            "INFO": logging.info,
            "WARNING": logging.warning,
            "ERROR": logging.error
        }.get(level.upper(), logging.info)
        
        log_method(message)
    
    def _generate_default_config(self) -> Dict[str, Any]:
        """
        Generate default configuration for the utility
        
        Returns:
            Dictionary with default utility settings
        """
        return {
            "version": "1.0.0",
            "performance_mode": "standard",
            "error_handling": {
                "retry_attempts": 3,
                "timeout": 30  # seconds
            }
        }
    
    def _initialize_resources(self) -> None:
        """
        Initialize any required resources for the utility
        
        Can include:
        - Resource allocation
        - Connection setup
        - Preliminary validations
        """
        try:
            # Implement resource initialization logic
            self.log("Utility resources initialized", "INFO")
        except Exception as e:
            self.log(f"Resource initialization error: {e}", "ERROR")
    
    def update_configuration(
        self, 
        **kwargs
    ) -> bool:
        """
        Update utility configuration
        
        Args:
            **kwargs: Configuration parameters to update
        
        Returns:
            Boolean indicating successful configuration update
        """
        try:
            # Validate and update configuration
            for key, value in kwargs.items():
                if key in self.config:
                    self.config[key] = value
                else:
                    self.log(f"Unknown configuration key: {key}", "WARNING")
            
            return True
        except Exception as e:
            self.log(f"Configuration update failed: {e}", "ERROR")
            return False
    
    def execute(
        self, 
        method: Callable, 
        *args, 
        **kwargs
    ) -> Optional[Any]:
        """
        Execute a method with standardized error handling
        
        Args:
            method: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Result of the method or None if execution fails
        """
        max_attempts = self.config.get(
            "error_handling", {}
        ).get("retry_attempts", 3)
        
        for attempt in range(max_attempts):
            try:
                return method(*args, **kwargs)
            except Exception as e:
                self.log(
                    f"Execution attempt {attempt + 1} failed: {e}", 
                    "WARNING"
                )
                
                # Optional: Add exponential backoff
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(2 ** attempt)
        
        self.log("Method execution failed after all attempts", "ERROR")
        return None
    
    def validate_input(
        self, 
        input_data: Any, 
        expected_type: Union[type, Tuple[type, ...]]
    ) -> bool:
        """
        Validate input data against expected type(s)
        
        Args:
            input_data: Data to validate
            expected_type: Expected type or tuple of types
        
        Returns:
            Boolean indicating input validity
        """
        return isinstance(input_data, expected_type)
    
    def safe_operation(
        self, 
        operation: Callable, 
        *args, 
        **kwargs
    ) -> Tuple[bool, Optional[Any]]:
        """
        Perform an operation with comprehensive error handling
        
        Args:
            operation: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Tuple (success_flag, result_or_error)
        """
        try:
            result = operation(*args, **kwargs)
            return True, result
        except Exception as e:
            self.log(f"Operation failed: {e}", "ERROR")
            return False, None

# Example Usage Method
def example_utility_method(
    input_data: List[Any], 
    transformation: Callable
) -> Optional[List[Any]]:
    """
    Example utility method demonstrating pattern
    
    Args:
        input_data: List to transform
        transformation: Function to apply to each element
    
    Returns:
        Transformed list or None if transformation fails
    """
    utility = [ModuleName]Utility()
    
    # Validate inputs
    if not utility.validate_input(input_data, list):
        utility.log("Invalid input type", "ERROR")
        return None
    
    # Use safe execution
    success, result = utility.safe_operation(
        lambda: [transformation(item) for item in input_data]
    )
    
    return result if success else None
```

## 3. Development Guidelines

### Design Principles
- Single Responsibility
- Minimal Dependencies
- Comprehensive Error Handling
- Performance Considerations
- Flexible Configuration

### Input Validation
- Always validate input types
- Use type hints consistently
- Implement robust error checking
- Provide meaningful error messages

### Error Handling Strategies
- Use try-except blocks
- Log all error scenarios
- Implement retry mechanisms
- Provide fallback behaviors

### Performance Optimization
- Use efficient algorithms
- Minimize memory allocations
- Implement lazy loading
- Use generator expressions
- Cache expensive computations

## 4. Testing Considerations

### Test Coverage Requirements
- [ ] Input validation tests
- [ ] Error handling scenarios
- [ ] Performance benchmarks
- [ ] Edge case handling
- [ ] Configurability tests

### Recommended Testing Approach
- Unit tests for individual methods
- Integration tests
- Performance profiling
- Comprehensive input validation

## 5. Best Practices Checklist

- [ ] Keep methods focused
- [ ] Use type hints
- [ ] Implement comprehensive logging
- [ ] Validate all inputs
- [ ] Design for extensibility
- [ ] Minimize external dependencies
- [ ] Write clear docstrings

## Customization Notes

1. Replace `[ModuleName]` with specific utility name
2. Adapt template to specific utility requirements
3. Follow Irintai coding standards
4. Maintain minimal external dependencies
5. Prioritize reusability

---

**Usage Guidelines:**
- Customize template for specific utility needs
- Maintain consistent error handling
- Focus on single, well-defined responsibility
