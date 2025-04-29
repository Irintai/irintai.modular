# Irintai API Documentation

This document describes the internal API structure of the Irintai Assistant for developers who want to extend its functionality or integrate with other systems.

## Core Module APIs

### ModelManager

The `ModelManager` class handles all interactions with Ollama models.

```python
from core import ModelManager

# Initialize
model_manager = ModelManager(
    model_path="data/models",
    logger=print_function,
    use_8bit=False
)
```

#### Key Methods

```python
# Model detection and listing
available_models = model_manager.detect_models()
model_list = model_manager.fetch_available_models()

# Model installation
model_manager.install_model("mistral:7b-instruct", progress_callback=None)
model_manager.uninstall_model("mistral:7b-instruct")

# Model usage
model_manager.start_model("mistral:7b-instruct", callback_function)
success, response = model_manager.send_prompt(prompt, format_function)
model_manager.stop_model()

# Utility methods
model_manager.verify_model_status("mistral:7b-instruct")
model_manager.update_model_path("new/path/to/models")
system_info = model_manager.get_system_info()
```

#### Events

The `ModelManager` provides callbacks for various events:

```python
def on_model_event(event_type, data):
    # event_type can be: "started", "stopped", "error", "output"
    pass

model_manager.start_model("model_name", on_model_event)
```

### ChatEngine

The `ChatEngine` class manages conversations and message formatting.

```python
from core import ChatEngine

# Initialize with dependencies
chat_engine = ChatEngine(
    model_manager=model_manager,
    memory_system=memory_system,
    session_file="data/chat_history.json",
    logger=print_function
)
```

#### Key Methods

```python
# System prompts
chat_engine.set_system_prompt("You are a helpful assistant...")
chat_engine.set_memory_mode("Auto")  # Off, Manual, Auto, Background

# Message handling
chat_engine.add_user_message("Hello, how are you?")
chat_engine.add_assistant_message("I'm doing well, thanks!", "model_name")
response = chat_engine.send_message("What is the capital of France?", on_response)

# Formatted prompts
formatted = chat_engine.format_prompt("Hello", "model_name")

# Session management
chat_engine.save_session()
chat_engine.load_session()
chat_engine.clear_history()

# Reflection generation
reflection = chat_engine.generate_reflection("path/to/save/reflection.json")
```

### MemorySystem

The `MemorySystem` class handles vector embeddings and semantic search.

```python
from core import MemorySystem

# Initialize
memory_system = MemorySystem(
    model_name="all-MiniLM-L6-v2",
    index_path="data/vector_store/vector_store.json",
    logger=print_function
)
```

#### Key Methods

```python
# Loading the embedding model
success = memory_system.load_model()

# Adding content to index
memory_system.add_to_index(
    ["Document text 1", "Document text 2"],
    [{"source": "doc1.txt"}, {"source": "doc2.txt"}]
)

# Adding files with chunking
memory_system.add_file_to_index("path/to/file.txt", chunk_size=1000)

# Searching
results = memory_system.search("query text", top_k=5)

# Index management
memory_system.save_index()
memory_system.load_index()
memory_system.clear_index()

# Statistics
stats = memory_system.get_stats()
```

### ConfigManager

The `ConfigManager` class handles application settings.

```python
from core import ConfigManager

# Initialize
config_manager = ConfigManager(
    config_path="data/config.json",
    logger=print_function
)
```

#### Key Methods

```python
# Reading config values
value = config_manager.get("key", default_value)
all_config = config_manager.get_all()

# Writing config values
config_manager.set("key", value)
config_manager.update({"key1": "value1", "key2": "value2"})

# Managing config file
config_manager.save_config()
config_manager.load_config()
config_manager.reset_to_defaults()

# Environment variables
config_manager.set_system_environment()
config_manager.set_system_path_var()
```

## Utility Module APIs

### IrintaiLogger

The `IrintaiLogger` class provides enhanced logging capabilities.

```python
from utils import IrintaiLogger

# Initialize
logger = IrintaiLogger(
    log_dir="data/logs",
    latest_log_file="irintai_debug.log",
    console_callback=None
)
```

#### Key Methods

```python
# Logging methods
logger.log("Message", "INFO")
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# Console handling
lines = logger.get_console_lines(filter_type="Error")
logger.clear_console()
logger.save_console_log("output.log")
```

### SystemMonitor

The `SystemMonitor` class monitors system resources.

```python
from utils import SystemMonitor

# Initialize
monitor = SystemMonitor(logger=print_function)
```

#### Key Methods

```python
# Resource statistics
cpu_usage = monitor.get_cpu_usage()
ram_percent, ram_used, ram_total = monitor.get_ram_usage()
gpu_percent, gpu_memory = monitor.get_gpu_stats()
used_percent, free_gb, total_gb = monitor.get_disk_space("path/to/check")

# Formatted information
stats = monitor.get_performance_stats()
formatted = monitor.get_formatted_stats()
color = monitor.get_bgr_color()

# System information
system_info = monitor.get_system_info()
is_critical, message = monitor.is_resource_critical()
```

### FileOps

The `FileOps` class provides file management utilities.

```python
from utils import FileOps

# Initialize
file_ops = FileOps(logger=print_function)
```

#### Key Methods

```python
# Reading and writing
success, content = file_ops.read_file("path/to/file.txt")
success = file_ops.write_file("path/to/file.txt", "content")
success = file_ops.append_to_file("path/to/file.txt", "more content")

# JSON handling
success, data = file_ops.load_json("config.json")
success = file_ops.save_json("config.json", data_dict)

# File operations
files = file_ops.list_files("directory", extensions=[".txt", ".md"])
success = file_ops.copy_file("source.txt", "destination.txt")
success = file_ops.move_file("source.txt", "destination.txt")
success = file_ops.delete_file("file.txt")

# Directory operations
success = file_ops.ensure_dir("path/to/create")
success = file_ops.open_folder("path/to/open")

# File information
info = file_ops.get_file_info("file.txt")
tree = file_ops.get_file_tree("directory", max_depth=3)
results = file_ops.search_files("directory", "search term")
```

## UI Component APIs

UI components are designed to be used within the Tkinter framework and are generally not intended to be used as standalone APIs. However, they can be instantiated and embedded in custom interfaces.

### Example: Creating a standalone chat panel

```python
import tkinter as tk
from ui import ChatPanel

# Create Tkinter root
root = tk.Tk()

# Initialize dependencies
from core import ModelManager, ChatEngine, MemorySystem, ConfigManager
from utils import IrintaiLogger

# Create chat panel
chat_panel = ChatPanel(
    root,
    chat_engine=chat_engine,
    logger=logger.log,
    config_manager=config_manager
)

# Access methods
chat_panel.submit_prompt()
chat_panel.clear_console()
chat_panel.apply_system_prompt()

root.mainloop()
```

## Integration Examples

### Adding a Custom Model Provider

To add support for a different model provider (not just Ollama):

1. Create a new class that implements the same interface as `ModelManager`
2. Override key methods to communicate with your provider
3. Update the main window to use your provider

Example stub:

```python
class CustomModelManager:
    def __init__(self, model_path, logger, use_8bit=False):
        self.model_path = model_path
        self.log = logger
        self.use_8bit = use_8bit
        self.model_statuses = {}
        self.current_model = None
        self.model_process = None
        
    def detect_models(self):
        # Your implementation here
        pass
        
    def start_model(self, model_name, callback=None):
        # Your implementation here
        pass
        
    def send_prompt(self, prompt, format_function):
        # Your implementation here
        pass
        
    # Implement other required methods...
```

### Adding a Custom Embedding Provider

To use a different embedding system:

```python
class CustomMemorySystem:
    def __init__(self, model_name, index_path, logger):
        self.model_name = model_name
        self.index_path = index_path
        self.log = logger
        self.index = []
        self.documents = []
        
    def search(self, query, top_k=5):
        # Your implementation here
        pass
        
    def add_to_index(self, docs, metadata):
        # Your implementation here
        pass
    
    # Implement other required methods...
```

## Extension Points

The Irintai architecture provides several extension points for adding functionality:

1. **Memory System**: Create custom document processors for specialized file types
2. **Model Manager**: Add support for different model providers
3. **Chat Engine**: Implement custom prompt formatters for different model types
4. **UI Components**: Create new panels and widgets for the tab interface

## Debugging and Logging

All components accept a `logger` parameter that should be a callable function accepting a string message. This allows for centralized logging and debugging:

```python
def my_logger(message):
    print(f"[DEBUG] {message}")
    # You could also log to a file, send to a monitoring service, etc.

# Then pass to components
model_manager = ModelManager(model_path, logger=my_logger)
```

## Utility APIs

### Runtime Patching

The `runtime_patching` module provides tools to prevent attribute errors by dynamically adding missing methods and attributes:

```python
from utils.runtime_patching import ensure_method_exists, ensure_attribute_exists, patch_plugin_manager

# Add missing attribute to an object
ensure_attribute_exists(obj, "config", default_value={})

# Add missing method to an object
def default_implementation(self, arg1):
    return f"Default implementation with {arg1}"
    
ensure_method_exists(obj, "missing_method", default_implementation)

# Add common methods to plugin manager
plugin_manager = patch_plugin_manager(plugin_manager)
```

#### Key Functions

```python
# Check if attribute exists and add if missing
ensure_attribute_exists(obj, attr_name, default_value=None) -> bool

# Check if method exists and add default implementation if missing
ensure_method_exists(obj, method_name, default_implementation=None) -> bool

# Add commonly missing methods to the plugin manager
patch_plugin_manager(plugin_manager) -> plugin_manager
```

### Attribute Checker

The `attribute_checker` module provides tools for validating that objects have required attributes:

```python
from utils.attribute_checker import check_required_attributes, has_attribute

# Check if an object has all required attributes
missing_attrs = check_required_attributes(obj, ["name", "version", "activate"])
if missing_attrs:
    print(f"Missing attributes: {missing_attrs}")

# Check if a specific attribute exists and is callable
if not has_attribute(obj, "handle_event", callable_only=True):
    print("Object is missing required callable 'handle_event'")
```
