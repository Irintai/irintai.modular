"""
Plugin configuration panel for IrintAI Assistant
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from typing import Dict, Any, Callable, List, Optional

class PluginConfigPanel:
    """Panel for configuring plugin settings"""
    
    def __init__(self, master, plugin_manager, config_manager, logger=None):
        """
        Initialize the plugin configuration panel
        
        Args:
            master: Parent widget
            plugin_manager: Plugin manager instance
            config_manager: Configuration manager
            logger: Optional logger
        """
        self.master = master
        self.plugin_manager = plugin_manager
        self.config_manager = config_manager
        self.logger = logger
        self.frame = ttk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Current plugin being configured
        self.current_plugin_id = None
        self.current_config = {}
        self.config_widgets = {}
        
        # Create UI components
        self.create_ui()
        
    def log(self, message, level="INFO"):
        """Log a message if logger is available"""
        if self.logger:
            if hasattr(self.logger, 'log'):
                self.logger.log(message, level)
            else:
                print(message)
                
    def create_ui(self):
        """Create the UI components"""
        # Create split pane with plugin list on left and config on right
        self.paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create left frame for plugin list
        left_frame = ttk.Frame(self.paned_window, width=200)
        self.paned_window.add(left_frame, weight=1)
        
        # Create plugin list
        ttk.Label(left_frame, text="Plugins:").pack(anchor=tk.W, padx=5, pady=5)
        
        # Plugin list frame with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.plugin_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.plugin_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.plugin_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.plugin_listbox.config(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.plugin_listbox.bind('<<ListboxSelect>>', self.on_plugin_selected)
        
        # Create right frame for config
        self.right_frame = ttk.Frame(self.paned_window, width=500)
        self.paned_window.add(self.right_frame, weight=3)
        
        # Create config area with scrolling
        self.config_canvas = tk.Canvas(self.right_frame)
        self.config_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.config_scrollbar = ttk.Scrollbar(self.right_frame, orient=tk.VERTICAL, command=self.config_canvas.yview)
        self.config_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.config_canvas.configure(yscrollcommand=self.config_scrollbar.set)
        self.config_canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Create a frame inside the canvas for config widgets
        self.config_frame = ttk.Frame(self.config_canvas)
        self.config_canvas_window = self.config_canvas.create_window((0, 0), window=self.config_frame, anchor=tk.NW)
        self.config_frame.bind('<Configure>', self._on_frame_configure)
        
        # Add header to config frame
        self.config_header = ttk.Label(self.config_frame, text="Select a plugin to configure", font=("", 12, "bold"))
        self.config_header.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)
        
        # Add description
        self.config_description = ttk.Label(self.config_frame, text="", wraplength=400)
        self.config_description.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(0, 10))
        
        # Add separator
        ttk.Separator(self.config_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=10)
        
        # Add config content
        self.config_content = ttk.Frame(self.config_frame)
        self.config_content.grid(row=3, column=0, columnspan=2, sticky=tk.NSEW, padx=10, pady=10)
        
        # Add buttons
        button_frame = ttk.Frame(self.config_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky=tk.E, padx=10, pady=10)
        
        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_config)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        self.save_button.state(['disabled'])
        
        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_config)
        self.reset_button.pack(side=tk.RIGHT, padx=5)
        self.reset_button.state(['disabled'])
        
        # Load plugins
        self.load_plugins()
        
    def load_plugins(self):
        """Load the list of available plugins"""
        # Clear the listbox
        self.plugin_listbox.delete(0, tk.END)
        
        # Get all plugins
        plugins = self.plugin_manager.get_all_plugins()
        
        # Sort plugins by name
        plugin_ids = sorted(plugins.keys())
        
        # Add plugins to listbox
        for plugin_id in plugin_ids:
            self.plugin_listbox.insert(tk.END, plugin_id)
            
    def on_plugin_selected(self, event):
        """Handle plugin selection"""
        # Get selected plugin
        selection = self.plugin_listbox.curselection()
        if not selection:
            return
            
        plugin_id = self.plugin_listbox.get(selection[0])
        
        # Load plugin config
        self.load_plugin_config(plugin_id)
        
    def load_plugin_config(self, plugin_id):
        """
        Load configuration for a plugin
        
        Args:
            plugin_id: Plugin identifier
        """
        # Store current plugin
        self.current_plugin_id = plugin_id
        
        # Get plugin info
        plugin_info = self.plugin_manager.get_plugin_info(plugin_id)
        
        # Update header and description
        plugin_name = plugin_info.get("name", plugin_id)
        self.config_header.config(text=f"Configure: {plugin_name}")
        
        description = plugin_info.get("description", "No description available.")
        version = plugin_info.get("version", "1.0.0")
        author = plugin_info.get("author", "Unknown")
        self.config_description.config(text=f"{description}\nVersion: {version} | Author: {author}")
        
        # Clear previous config widgets
        for widget in self.config_content.winfo_children():
            widget.destroy()
        self.config_widgets = {}
        
        # Load plugin config
        plugin_config = self.config_manager.get(f"plugins.{plugin_id}", {})
        
        # If plugin has a get_config_schema method, use it
        schema = self._get_plugin_config_schema(plugin_id)
        
        if not schema:
            # No schema, show a message
            ttk.Label(self.config_content, text="This plugin has no configurable settings.").grid(
                row=0, column=0, padx=10, pady=10)
            self.save_button.state(['disabled'])
            self.reset_button.state(['disabled'])
            self.current_config = {}
            return
            
        # Store current config
        self.current_config = plugin_config.copy()
        
        # Create widgets for config options
        row = 0
        for field_name, field_info in schema.items():
            field_label = field_info.get("label", field_name)
            field_type = field_info.get("type", "string")
            field_default = field_info.get("default", "")
            field_desc = field_info.get("description", "")
            field_options = field_info.get("options", [])
            field_value = plugin_config.get(field_name, field_default)
            
            # Create label
            label = ttk.Label(self.config_content, text=f"{field_label}:")
            label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            # Create widget based on type
            widget = None
            
            if field_type == "boolean":
                var = tk.BooleanVar(value=field_value)
                widget = ttk.Checkbutton(self.config_content, variable=var)
                self.config_widgets[field_name] = var
            
            elif field_type == "choice" and field_options:
                var = tk.StringVar(value=field_value)
                widget = ttk.Combobox(self.config_content, textvariable=var, values=field_options, state="readonly")
                self.config_widgets[field_name] = var
            
            elif field_type == "integer":
                var = tk.IntVar(value=int(field_value) if field_value else 0)
                widget = ttk.Spinbox(self.config_content, from_=0, to=1000000, textvariable=var, width=10)
                self.config_widgets[field_name] = var
            
            elif field_type == "float":
                var = tk.DoubleVar(value=float(field_value) if field_value else 0.0)
                widget = ttk.Spinbox(self.config_content, from_=0, to=1000000, increment=0.1, textvariable=var, width=10)
                self.config_widgets[field_name] = var
            
            elif field_type == "text":
                var = tk.StringVar(value=field_value)
                widget = ttk.Entry(self.config_content, textvariable=var, width=40)
                self.config_widgets[field_name] = var
            
            elif field_type == "multiline":
                frame = ttk.Frame(self.config_content)
                widget = tk.Text(frame, height=5, width=40)
                widget.insert(tk.END, field_value)
                scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=widget.yview)
                widget.configure(yscrollcommand=scrollbar.set)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                self.config_widgets[field_name] = widget
                widget = frame
            
            elif field_type == "password":
                var = tk.StringVar(value=field_value)
                widget = ttk.Entry(self.config_content, textvariable=var, width=40, show="*")
                self.config_widgets[field_name] = var
            
            elif field_type == "color":
                var = tk.StringVar(value=field_value)
                
                color_frame = ttk.Frame(self.config_content)
                entry = ttk.Entry(color_frame, textvariable=var, width=10)
                entry.pack(side=tk.LEFT, padx=(0, 5))
                
                color_preview = tk.Label(color_frame, text="   ", bg=field_value, relief=tk.RIDGE)
                color_preview.pack(side=tk.LEFT)
                
                def update_color(*args):
                    try:
                        color_preview.config(bg=var.get())
                    except:
                        color_preview.config(bg="gray")
                
                var.trace("w", update_color)
                self.config_widgets[field_name] = var
                widget = color_frame
            
            else:  # Default to string
                var = tk.StringVar(value=field_value)
                widget = ttk.Entry(self.config_content, textvariable=var, width=40)
                self.config_widgets[field_name] = var
            
            widget.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
            
            # Add tooltip/description if provided
            if field_desc:
                help_label = ttk.Label(self.config_content, text="ℹ️", cursor="question_arrow")
                help_label.grid(row=row, column=2, padx=5, pady=5)
                
                # Create tooltip
                self._create_tooltip(help_label, field_desc)
            
            row += 1
            
        # Enable buttons
        self.save_button.state(['!disabled'])
        self.reset_button.state(['!disabled'])
        
    def _get_plugin_config_schema(self, plugin_id):
        """
        Get configuration schema for a plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Configuration schema dictionary
        """
        plugin_instance = self.plugin_manager.get_plugin_instance(plugin_id)
        if not plugin_instance:
            return {}
            
        # Check if plugin has a get_config_schema method
        if hasattr(plugin_instance, "get_config_schema") and callable(plugin_instance.get_config_schema):
            try:
                return plugin_instance.get_config_schema()
            except Exception as e:
                self.log(f"Error getting config schema for plugin {plugin_id}: {e}", "ERROR")
                return {}
                
        # Check if plugin has a CONFIG_SCHEMA attribute
        if hasattr(plugin_instance, "CONFIG_SCHEMA"):
            return plugin_instance.CONFIG_SCHEMA
            
        # Check plugin directory for config_schema.json
        plugin_dir = os.path.join("plugins", plugin_id)
        schema_file = os.path.join(plugin_dir, "config_schema.json")
        
        if os.path.exists(schema_file):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"Error loading config schema from file for plugin {plugin_id}: {e}", "ERROR")
                return {}
                
        return {}
        
    def save_config(self):
        """Save the current plugin configuration"""
        if not self.current_plugin_id:
            return
            
        # Collect config values
        new_config = {}
        
        for field_name, widget in self.config_widgets.items():
            if isinstance(widget, (tk.BooleanVar, tk.StringVar, tk.IntVar, tk.DoubleVar)):
                new_config[field_name] = widget.get()
            elif isinstance(widget, tk.Text):
                new_config[field_name] = widget.get(1.0, tk.END).rstrip()
        
        # Save to config manager
        config_path = f"plugins.{self.current_plugin_id}"
        self.config_manager.set(config_path, new_config)
        self.config_manager.save_config()
        
        # Update current config
        self.current_config = new_config.copy()
        
        # Notify plugin of config change
        plugin_instance = self.plugin_manager.get_plugin_instance(self.current_plugin_id)
        if plugin_instance and hasattr(plugin_instance, "on_config_changed") and callable(plugin_instance.on_config_changed):
            try:
                plugin_instance.on_config_changed(new_config)
            except Exception as e:
                self.log(f"Error in plugin on_config_changed: {e}", "ERROR")
        
        # Show confirmation
        messagebox.showinfo("Configuration Saved", f"Configuration for plugin '{self.current_plugin_id}' has been saved.")
        
    def reset_config(self):
        """Reset the current plugin configuration to defaults"""
        if not self.current_plugin_id:
            return
            
        # Ask for confirmation
        result = messagebox.askyesno(
            "Reset Configuration",
            f"Are you sure you want to reset the configuration for plugin '{self.current_plugin_id}'?",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
            
        # Reset by reloading the plugin config
        self.load_plugin_config(self.current_plugin_id)
        
    def _on_frame_configure(self, event):
        """Handle frame configuration event"""
        # Update the scroll region to encompass the inner frame
        self.config_canvas.configure(scrollregion=self.config_canvas.bbox("all"))
        
    def _on_canvas_configure(self, event):
        """Handle canvas configuration event"""
        # Update the width of the inner frame to fill the canvas
        self.config_canvas.itemconfig(self.config_canvas_window, width=event.width)
        
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        # Tooltip functionality
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create toplevel window
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Create tooltip label
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief=tk.SOLID, borderwidth=1, 
                             wraplength=300, justify=tk.LEFT)
            label.pack(padx=5, pady=5)
            
        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
                
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)