# Irintai Development Standards and Conventions

## 1. Naming Conventions

### 1.1 General Naming Rules
- Use snake_case for:
  - Function names
  - Variable names
  - File names
- Use PascalCase for:
  - Class names
  - Type/Custom Type names
- Use UPPERCASE_WITH_UNDERSCORES for:
  - Constants
  - Global configuration variables

### 1.2 Specific Naming Patterns

#### Modules
- Descriptive, lowercase names
- Reflect primary responsibility
- Examples:
  - `model_manager.py`
  - `chat_engine.py`
  - `system_monitor.py`

#### Classes
- Descriptive noun or noun phrase
- Represent core abstractions
- Examples:
  - `ModelManager`
  - `ChatEngine`
  - `MemorySystem`

#### Methods
- Verb-first naming
- Describe primary action
- Follow pattern: `verb_noun()` or `verb()`
- Examples:
  - `detect_models()`
  - `add_to_index()`
  - `save_config()`
  - `get_system_info()`

#### Private Methods
- Prefixed with single underscore
- Indicate internal implementation
- Examples:
  - `_install_model_thread()`
  - `_update_model_status()`

## 2. Type Annotations and Formatting

### 2.1 Type Hints
- Always use type hints for method signatures
- Specify return types
- Use Optional for nullable parameters

```python
def add_to_index(
    self, 
    docs: List[str], 
    metadata: List[Dict[str, Any]]
) -> bool:
    """
    Add documents to the vector index
    
    Args:
        docs: List of document texts
        metadata: Associated metadata for documents
        
    Returns:
        True if documents added successfully
    """
    # Method implementation
```

### 2.2 Docstring Standards
- Use Google-style docstrings
- Include sections:
  - Brief description
  - Args (with types and descriptions)
  - Returns (with type and description)
- Optional: Raise section for exceptions

## 3. Class Structure Patterns

### 3.1 Initialization
- Use type hints in `__init__`
- Provide default values where possible
- Include optional logger/callback parameters

```python
class ModelManager:
    def __init__(
        self, 
        model_path: str, 
        logger: Optional[Callable] = None, 
        use_8bit: bool = False
    ):
        """
        Initialize the model manager
        
        Args:
            model_path: Directory to store models
            logger: Optional logging function
            use_8bit: Enable 8-bit model quantization
        """
        self.model_path = model_path
        self.log = logger or print
        self.use_8bit = use_8bit
```

### 3.2 Method Design Principles
- Single Responsibility Principle
- Prefer smaller, focused methods
- Use threading for long-running operations
- Implement robust error handling

### 3.3 Configuration and State Management
- Use class-level dictionaries for constants
- Implement getter/setter methods
- Provide clear state tracking mechanisms

```python
# Example from model_manager.py
MODEL_STATUS = {
    "NOT_INSTALLED": "Not Installed",
    "INSTALLING": "Installing...",
    "INSTALLED": "Installed",
    # ... other status states
}
```

## 4. Error Handling and Logging

### 4.1 Logging Conventions
- Use structured logging
- Include context in log messages
- Use consistent log level prefixes
  - `[INFO]`: Informational messages
  - `[WARNING]`: Potential issues
  - `[ERROR]`: Failure scenarios
  - `[DEBUG]`: Detailed debugging info

```python
def log_message(self, msg: str, level: str = "INFO"):
    """
    Log messages with consistent formatting
    
    Args:
        msg: Message to log
        level: Logging level (INFO, WARNING, ERROR)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"{timestamp} [{level}] {msg}"
    # Log to file/console
```

## 5. Asynchronous Operations

### 5.1 Threading Patterns
- Use daemon threads for background tasks
- Implement progress callbacks
- Ensure thread-safe state modifications

```python
def start_background_task(self):
    """
    Start a task in a separate thread
    """
    threading.Thread(
        target=self._background_method,
        daemon=True
    ).start()
```

## 6. Configuration and Environment

### 6.1 Configuration Management
- Use JSON for configuration storage
- Provide default configurations
- Support environment-specific overrides

## 7. Dependency and Import Management

### 7.1 Import Guidelines
- Group imports:
  1. Standard library imports
  2. Third-party library imports
  3. Local module imports
- Use absolute imports
- Avoid wildcard imports

```python
# Good import structure example
import os
import time
from typing import Dict, List, Optional

import torch
import sentence_transformers

from core.model_manager import ModelManager
from utils.logger import IrintaiLogger
```

## 8. Performance and Optimization

### 8.1 Code Efficiency
- Use list comprehensions
- Leverage built-in functions
- Minimize redundant computations
- Use `functools` and `itertools` for complex iterations

## 9. Testing and Validation

### 9.1 Method Validation
- Include input validation
- Handle edge cases
- Provide meaningful error messages

```python
def add_to_index(self, docs: List[str], metadata: List[Dict[str, Any]]) -> bool:
    if len(docs) != len(metadata):
        self.log("[Memory Error] Mismatched documents and metadata")
        return False
    
    # Validation passed, proceed with indexing
```

## 10. Extensibility Considerations

### 10.1 Design for Extension
- Use abstract base classes
- Implement clear interfaces
- Support plugin-like architectures
- Minimize tight coupling between components

---

**Note**: These conventions are guidelines. Pragmatism and readability should always take precedence over strict adherence to rules.
