"""
Example Plugin for Irintai Assistant
Demonstrates the basic plugin structure and API usage
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

class IrintaiPlugin:
    """Example plugin demonstrating API usage"""
    
    def __init__(self, plugin_id, core_system):
        """
        Initialize the plugin
        
        Args:
            plugin_id: Unique identifier for this plugin
            core_system: Dictionary of core system components
        """
        self.plugin_id = plugin_id
        self.core = core_system
        
        # Get logger for plugin-specific logging
        self.logger = getattr(core_system, 'logger', None)
        
        # Track plugin state
        self.active = False
        self.background_thread = None
        
    def activate(self):
        """Called when the plugin is activated"""
        if self.logger:
            self.logger.log(f"[{self.plugin_id}] Plugin activated")
            
        # Register custom metrics if system_monitor is available
        system_monitor = getattr(self.core, 'system_monitor', None)
        if system_monitor:
            system_monitor.register_plugin_metric(
                self.plugin_id,
                "example_counter",
                self.get_counter_value,
                {
                    "name": "Example Counter",
                    "description": "A simple counter that increments over time",
                    "format": "numeric",
                    "unit": "ops"
                }
            )
        
        # Subscribe to events if event_bus is available
        event_bus = getattr(self.core, 'event_bus', None)
        if event_bus:
            event_bus.subscribe(
                "system.model_loaded", 
                self.on_model_loaded,
                self.plugin_id
            )
        
        # Initialize plugin data
        self.counter = 0
        self.active = True
        
        # Start background thread
        self.background_thread = threading.Thread(target=self.background_task, daemon=True)
        self.background_thread.start()
        
        return True
        
    def deactivate(self):
        """Called when the plugin is deactivated"""
        # Stop background thread
        self.active = False
        if self.background_thread:
            self.background_thread.join(timeout=2.0)
            
        # Unregister from events
        event_bus = getattr(self.core, 'event_bus', None)
        if event_bus:
            event_bus.unsubscribe_all(self.plugin_id)
            
        # Unregister custom metrics
        system_monitor = getattr(self.core, 'system_monitor', None)
        if system_monitor:
            system_monitor.unregister_plugin(self.plugin_id)
            
        if self.logger:
            self.logger.log(f"[{self.plugin_id}] Plugin deactivated")
            
        return True
        
    def get_actions(self):
        """
        Return actions for the UI
        
        Returns:
            Dictionary mapping action names to functions
        """
        return {
            "Show Example Dialog": self.show_dialog,
            "Reset Counter": self.reset_counter,
            "Show Resource Usage": self.show_resource_usage,
            "Publish Test Event": self.publish_test_event
        }
        
    def get_config_schema(self):
        """
        Return configuration schema for the plugin
        
        Returns:
            Dictionary defining configuration fields
        """
        return {
            "update_interval": {
                "type": "float",
                "label": "Update Interval",
                "description": "How often to update the counter (in seconds)",
                "default": 1.0
            },
            "counter_increment": {
                "type": "integer",
                "label": "Counter Increment",
                "description": "How much to increment the counter each time",
                "default": 1
            },
            "enable_logging": {
                "type": "boolean",
                "label": "Enable Logging",
                "description": "Log counter updates to the console",
                "default": False
            },
            "text_color": {
                "type": "color",
                "label": "Text Color",
                "description": "Color for text in the plugin dialog",
                "default": "#007bff"
            }
        }
        
    def on_config_changed(self, config):
        """
        Called when plugin configuration changes
        
        Args:
            config: New configuration dictionary
        """
        if self.logger:
            self.logger.log(f"[{self.plugin_id}] Configuration updated: {config}")
            
    def get_counter_value(self):
        """Get the current counter value for metrics"""
        return self.counter
        
    def on_model_loaded(self, event_name, data, event_info):
        """
        Event handler for model loading
        
        Args:
            event_name: Name of the event
            data: Event data
            event_info: Additional event information
        """
        if self.logger:
            self.logger.log(f"[{self.plugin_id}] Model loaded: {data.get('model_name')}")
            
    def background_task(self):
        """Background task that runs while the plugin is active"""
        while self.active:
            try:
                # Get configuration
                config = getattr(self.core, 'config_manager', {})
                if hasattr(config, 'get'):
                    plugin_config = config.get(f"plugins.{self.plugin_id}", {})
                    increment = plugin_config.get("counter_increment", 1)
                    interval = plugin_config.get("update_interval", 1.0)
                    enable_logging = plugin_config.get("enable_logging", False)
                else:
                    increment = 1
                    interval = 1.0
                    enable_logging = False
                
                # Increment counter
                self.counter += increment
                
                # Log if enabled
                if enable_logging and self.logger:
                    self.logger.log(f"[{self.plugin_id}] Counter: {self.counter}", "DEBUG")
                    
                # Sleep for the configured interval
                time.sleep(interval)
                
            except Exception as e:
                if self.logger:
                    self.logger.log(f"[{self.plugin_id}] Error in background task: {e}", "ERROR")
                time.sleep(1.0)  # Sleep on error to avoid tight loop
                
    def reset_counter(self):
        """Reset the counter to zero"""
        self.counter = 0
        if self.logger:
            self.logger.log(f"[{self.plugin_id}] Counter reset to 0")
            
        # Show confirmation
        messagebox.showinfo("Counter Reset", "The counter has been reset to 0.")
        
    def publish_test_event(self):
        """Publish a test event"""
        event_bus = getattr(self.core, 'event_bus', None)
        if event_bus:
            event_data = {
                "counter": self.counter,
                "timestamp": time.time(),
                "message": "This is a test event"
            }
            
            event_bus.publish(f"{self.plugin_id}.test_event", event_data)
            
            if self.logger:
                self.logger.log(f"[{self.plugin_id}] Published test event with counter={self.counter}")
                
            # Show confirmation
            messagebox.showinfo("Event Published", f"Test event published with counter={self.counter}")
        else:
            messagebox.showwarning("Event Bus Unavailable", "The event bus is not available.")
            
    def show_resource_usage(self):
        """Show resource usage in a dialog"""
        system_monitor = getattr(self.core, 'system_monitor', None)
        if not system_monitor:
            messagebox.showwarning("System Monitor Unavailable", "The system monitor is not available.")
            return
            
        # Create dialog
        dialog = tk.Toplevel()
        dialog.title("Resource Usage")
        dialog.geometry("500x400")
        dialog.transient(tk.Tk.winfo_toplevel(tk._default_root))  # Make dialog transient to main window
        
        # Create frame with padding
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add title
        ttk.Label(frame, text="Current Resource Usage", font=("", 14, "bold")).pack(pady=(0, 10))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # System tab
        system_tab = ttk.Frame(notebook)
        notebook.add(system_tab, text="System")
        
        # Get system info
        system_info = system_monitor.get_system_info()
        
        # Display system info
        row = 0
        ttk.Label(system_tab, text="CPU Usage:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(system_tab, text=f"{system_info['cpu']['usage_percent']}%").grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(system_tab, text="RAM Usage:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(system_tab, text=f"{system_info['ram']['usage_percent']}% ({system_info['ram']['used_gb']:.1f}/{system_info['ram']['total_gb']:.1f} GB)").grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(system_tab, text="GPU Usage:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(system_tab, text=f"{system_info['gpu']['usage_percent']} ({system_info['gpu']['memory']})").grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(system_tab, text="Disk Usage:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(system_tab, text=f"{system_info['disk']['usage_percent']}% ({system_info['disk']['free_gb']:.1f} GB free)").grid(row=row, column=1, sticky=tk.W)
        
        # Plugin metrics tab
        plugin_tab = ttk.Frame(notebook)
        notebook.add(plugin_tab, text="Plugin Metrics")
        
        # Get plugin metrics
        plugin_metrics = system_monitor.get_plugin_metrics()
        
        if plugin_metrics:
            # Create treeview for plugin metrics
            columns = ("Value", "Type", "Description")
            tree = ttk.Treeview(plugin_tab, columns=columns, show="headings")
            tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Configure columns
            tree.heading("Value", text="Value")
            tree.heading("Type", text="Type")
            tree.heading("Description", text="Description")
            
            tree.column("Value", width=100, anchor=tk.E)
            tree.column("Type", width=80, anchor=tk.CENTER)
            tree.column("Description", width=300, anchor=tk.W)
            
            # Add plugin metrics
            for key, metric in plugin_metrics.items():
                metadata = metric["metadata"]
                
                if metric["plugin_id"] == self.plugin_id:
                    # Format value based on type
                    if metadata["format"] == "percentage":
                        value = f"{metric['value']:.1f}%"
                    elif metadata["format"] == "numeric":
                        value = f"{metric['value']:.1f} {metadata.get('unit', '')}"
                    else:
                        value = str(metric['value'])
                        
                    tree.insert("", "end", values=(
                        value,
                        metadata["format"].capitalize(),
                        metadata["description"]
                    ))
        else:
            ttk.Label(plugin_tab, text="No plugin metrics available").pack(pady=20)
        
        # Button to close dialog
        ttk.Button(frame, text="Close", command=dialog.destroy).pack(pady=10)
            
    def show_dialog(self):
        """Show a custom dialog"""
        # Get configuration for text color
        config = getattr(self.core, 'config_manager', {})
        if hasattr(config, 'get'):
            plugin_config = config.get(f"plugins.{self.plugin_id}", {})
            text_color = plugin_config.get("text_color", "#007bff")
        else:
            text_color = "#007bff"
        
        # Create dialog window
        dialog = tk.Toplevel()
        dialog.title("Example Plugin Dialog")
        dialog.geometry("400x300")
        dialog.transient(tk.Tk.winfo_toplevel(tk._default_root))  # Make dialog transient to main window
        
        # Create frame with padding
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add some content
        ttk.Label(frame, text="Example Plugin", font=("", 16, "bold")).pack(pady=(0, 10))
        
        # Use tk.Label for colored text (ttk.Label doesn't support foreground)
        tk.Label(
            frame, 
            text=f"Current counter value: {self.counter}",
            font=("", 12),
            foreground=text_color
        ).pack(pady=10)
        
        # Add a button that increments the counter
        ttk.Button(
            frame, 
            text="Increment Counter", 
            command=self.increment_counter
        ).pack(pady=5)
        
        # Add a button to reset counter
        ttk.Button(
            frame, 
            text="Reset Counter", 
            command=self.reset_counter
        ).pack(pady=5)
        
        # Add information about the plugin
        info_text = (
            "This is an example plugin that demonstrates various features "
            "of the Irintai plugin API including resource monitoring, "
            "configuration, and event handling."
        )
        
        ttk.Label(frame, text=info_text, wraplength=350).pack(pady=20)
        
        # Close button
        ttk.Button(frame, text="Close", command=dialog.destroy).pack(pady=10)
        
    def increment_counter(self):
        """Increment the counter manually"""
        config = getattr(self.core, 'config_manager', {})
        if hasattr(config, 'get'):
            plugin_config = config.get(f"plugins.{self.plugin_id}", {})
            increment = plugin_config.get("counter_increment", 1)
        else:
            increment = 1
            
        self.counter += increment
        
        # Show confirmation
        messagebox.showinfo("Counter Incremented", f"Counter incremented by {increment} to {self.counter}")
        

# Plugin metadata - required for all plugins
plugin_info = {
    "name": "Example Plugin",
    "description": "A simple example plugin demonstrating the Irintai plugin API",
    "version": "1.0.0",
    "author": "Irintai Team",
    "url": "",
    "plugin_class": IrintaiPlugin,
    "compatibility": "1.0.0",
    "dependencies": [],
    "tags": ["example", "demo"]
}