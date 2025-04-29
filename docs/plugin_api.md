# Irintai Plugin API Documentation

## Overview

The Irintai Plugin API provides a robust, containerized framework for developing plugins that extend the Irintai Assistant. Plugins can add new UI panels, processing features, integrations, and more—while running in a secure, isolated environment.

## Plugin Architecture

Irintai uses a modular, containerized plugin architecture with:

1. **Isolation**: Each plugin runs in its own environment with controlled access to system resources
2. **Resource Monitoring**: Plugins can register custom metrics for performance tracking
3. **Inter-Plugin Communication**: Plugins communicate via an event bus
4. **Dependency Management**: Plugins can declare and check dependencies (including external libraries)
5. **Configuration Management**: Plugins can have user-configurable settings and schemas
6. **Sandboxed File Operations**: Plugins have limited, secure file system access
7. **Error Handling**: Robust error handling and error callbacks
8. **Runtime Attribute Protection**: Automatic patching for missing attributes/methods
9. **Thread Safety**: Tools for safe UI updates from plugin threads

## Creating a Plugin

### Basic Structure

A plugin is a Python package with the following structure:

```
plugins/
  my_plugin/
    __init__.py         # Main plugin code with IrintaiPlugin class and plugin_info
    core/               # (Recommended) Core logic for the plugin
    ui/                 # (Optional) UI components for the plugin
    config_schema.json  # (Optional) Plugin configuration schema
    requirements.txt    # (Optional) Plugin-specific dependencies
    resources/          # (Optional) Additional resources (icons, etc.)
    README.md           # (Optional) Plugin documentation
```

### Plugin Class

Every plugin must define a class named `IrintaiPlugin` in its `__init__.py` file:

```python
class IrintaiPlugin:
    def __init__(self, plugin_id, core_system):
        self.plugin_id = plugin_id
        self.core = core_system
        self.logger = getattr(core_system, 'logger', None)
        # ...additional initialization...

    def activate(self):
        """Called when the plugin is activated"""
        return True

    def deactivate(self):
        """Called when the plugin is deactivated"""
        return True

    def get_actions(self):
        """Return a dictionary of actions for UI integration"""
        return {
            "Do Something": self.do_something
        }

    def get_config_schema(self):
        """Return configuration schema for the plugin"""
        return {
            "api_key": {
                "type": "password",
                "label": "API Key",
                "description": "Your service API key",
                "default": ""
            }
        }

    def on_config_changed(self, config):
        """Called when plugin configuration changes"""
        pass
```

### Plugin Metadata

You must define plugin metadata in the `__init__.py` file:

```python
plugin_info = {
    "name": "My Plugin",
    "description": "Does something useful",
    "version": "1.0.0",
    "author": "Your Name",
    "url": "https://example.com/plugin",
    "plugin_class": IrintaiPlugin,
    "compatibility": "1.0.0",  # Minimum Irintai version required
    "dependencies": ["other_plugin>=1.0.0"],  # Optional dependencies
    "tags": ["utility", "example"]
}
```

### Plugin Requirements

- List any extra dependencies in a `requirements.txt` inside your plugin folder (optional, recommended for advanced plugins).
- All core dependencies (e.g., `customtkinter`, `pymupdf`, `pytesseract`, etc.) are available if listed in the main `requirements.txt`.
- If your plugin requires external binaries (e.g., Tesseract for OCR), document this in your plugin README.

## Plugin SDK and Core Services

The `PluginSDK` class is provided to each plugin during initialization, offering standardized access to Irintai services:

### Logging

```python
# Log messages
self.core.logger.log("Something happened", "INFO")  # Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Event Communication

```python
# Publish an event
self.core.event_bus.publish("my_plugin.event", {"data": "value"})

# Subscribe to an event
def handle_event(event_name, data, event_info):
    print(f"Event received: {event_name} with data {data}")
    
subscriber_id = self.plugin_id
self.core.event_bus.subscribe("other_plugin.event", handle_event, subscriber_id)

# Unsubscribe when done
self.core.event_bus.unsubscribe_all(self.plugin_id)
```

### Resource Monitoring

```python
# Register a custom metric
def get_metric_value():
    return 42.5

self.core.system_monitor.register_plugin_metric(
    self.plugin_id,
    "custom_metric",
    get_metric_value,
    {
        "name": "My Custom Metric",
        "description": "Measures something important",
        "format": "percentage"  # or "numeric", "text"
    }
)

# Register a process for monitoring
import os
pid = os.getpid()
self.core.system_monitor.register_monitored_process(
    self.plugin_id, 
    pid, 
    "My Plugin Process"
)
```

### File Operations

Plugins have sandboxed access to the file system:

```python
# Plugin-specific data directory
data_dir = self.core.file_ops.get_plugin_data_dir(self.plugin_id)

# Read a file in the plugin's data directory
content = self.core.file_ops.read_file(
    f"{self.plugin_id}/settings.json",
    plugin_id=self.plugin_id
)

# Write a file in the plugin's data directory
self.core.file_ops.write_file(
    f"{self.plugin_id}/settings.json",
    '{"setting": "value"}',
    plugin_id=self.plugin_id
)
```

### Model Access

```python
# Generate text with the current model
response = self.core.model_manager.generate_text("Hello, how are you?")

# Get available models
models = self.core.model_manager.get_available_models()
```

### Configuration

```python
# Get plugin configuration
config = self.core.config_manager.get(f"plugins.{self.plugin_id}", {})
api_key = config.get("api_key", "")

# Update configuration
self.core.config_manager.set(f"plugins.{self.plugin_id}.api_key", "new_key")
self.core.config_manager.save_config()
```

## Resource Management Best Practices

### CPU & Memory Usage

1. **Asynchronous Processing**: Use threading for long-running operations to avoid blocking the UI
2. **Resource Cleanup**: Always clean up resources in the `deactivate()` method
3. **Progress Reporting**: Report progress for long operations through events

### Memory Management

```python
# Monitor your plugin's memory usage
def get_memory_usage():
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    return memory_mb

self.core.system_monitor.register_plugin_metric(
    self.plugin_id,
    "memory_usage",
    get_memory_usage,
    {
        "name": "Memory Usage",
        "description": "Current memory usage of the plugin",
        "format": "numeric",
        "unit": "MB"
    }
)
```

## Configuration Schema

Plugin configuration is defined using a schema:

```python
{
    "field_name": {
        "type": "string",  # string, boolean, integer, float, choice, text, password, color
        "label": "User-friendly label",
        "description": "Help text for the user",
        "default": "Default value",
        "options": ["option1", "option2"]  # For choice type only
    }
}
```

## UI Integration

Plugins can add actions to the UI:

```python
def get_actions(self):
    return {
        "Do Something": self.do_something,
        "Show Dialog": self.show_dialog
    }
    
def show_dialog(self):
    import tkinter as tk
    from tkinter import ttk
    
    dialog = tk.Toplevel()
    dialog.title("Plugin Dialog")
    dialog.geometry("400x300")
    
    ttk.Label(dialog, text="Hello from plugin!").pack(pady=20)
    ttk.Button(dialog, text="Close", command=dialog.destroy).pack()
```

## Security Considerations

1. **File Access**: Only use the provided FileOps methods to access files
2. **Network Access**: Clearly document network usage in your plugin description
3. **Resource Usage**: Be mindful of CPU, memory and GPU usage
4. **Error Handling**: Always catch exceptions to prevent application crashes

## Debugging

1. Set the logging level to DEBUG for more detailed information:
   ```python
   self.core.logger.log("Detailed debug info", "DEBUG")
   ```

2. Monitor your plugin's resource usage in the Resource Monitor panel

## Distribution

Distribute your plugin as a ZIP file with the following structure:
```
my_plugin.zip
  my_plugin/
    __init__.py
    core/
    ui/
    config_schema.json
    requirements.txt
    ...
```

Users can install the plugin by extracting it to their `plugins/` directory.

## Example Plugin

See the `plugins/example_plugin` directory for a complete example plugin implementation.