"""
Plugin configuration panel for IrintAI Assistant
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
import os
from typing import Dict, Any, Callable, List, Optional

class PluginConfigPanel:
    """Panel for configuring plugin settings with improved configuration loading"""
    
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
        
        # Create left frame for plugin list with better width
        left_frame = ttk.Frame(self.paned_window, width=220)
        self.paned_window.add(left_frame, weight=1)
        
        # Create plugin list with a better header
        ttk.Label(left_frame, text="Available Plugins", font=("", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        
        # Plugin list frame with scrollbar and better styling
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Use a better styled listbox
        self.plugin_listbox = tk.Listbox(list_frame, 
                                          selectmode=tk.SINGLE,
                                          activestyle='dotbox',
                                          font=("", 9),
                                          borderwidth=1,
                                          relief=tk.SOLID,
                                          highlightthickness=0)
        self.plugin_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.plugin_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.plugin_listbox.config(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.plugin_listbox.bind('<<ListboxSelect>>', self.on_plugin_selected)
        
        # Create right frame for config with more width
        self.right_frame = ttk.Frame(self.paned_window, width=580)
        self.paned_window.add(self.right_frame, weight=3)
        
        # Create config area with scrolling and better styling
        self.config_canvas = tk.Canvas(self.right_frame, highlightthickness=0)
        self.config_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.config_scrollbar = ttk.Scrollbar(self.right_frame, orient=tk.VERTICAL, command=self.config_canvas.yview)
        self.config_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.config_canvas.configure(yscrollcommand=self.config_scrollbar.set)
        self.config_canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Enable mousewheel scrolling for better usability
        self.config_canvas.bind_all('<MouseWheel>', lambda event: self.config_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # Create a frame inside the canvas for config widgets with padding
        self.config_frame = ttk.Frame(self.config_canvas)
        self.config_canvas_window = self.config_canvas.create_window((0, 0), window=self.config_frame, anchor=tk.NW)
        self.config_frame.bind('<Configure>', self._on_frame_configure)
        
        # Add header to config frame with improved styling
        self.config_header = ttk.Label(self.config_frame, text="Select a plugin to configure", font=("", 12, "bold"))
        self.config_header.grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=15, pady=15)
        
        # Add description with better wrapping and style
        self.config_description = ttk.Label(self.config_frame, text="", wraplength=500, font=("", 9))
        self.config_description.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=15, pady=(0, 10))
        
        # Add separator
        ttk.Separator(self.config_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=3, sticky=tk.EW, padx=10, pady=10)
        
        # Add config content with better styling
        self.config_content = ttk.Frame(self.config_frame)
        self.config_content.grid(row=3, column=0, columnspan=3, sticky=tk.NSEW, padx=15, pady=5)
        
        # Add buttons with better styling and positioning
        button_frame = ttk.Frame(self.config_frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.E, padx=15, pady=15)
        
        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_config, style="Accent.TButton")
        self.save_button.pack(side=tk.RIGHT, padx=5)
        self.save_button.state(['disabled'])
        
        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_config)
        self.reset_button.pack(side=tk.RIGHT, padx=5)
        self.reset_button.state(['disabled'])
        
        # Add refresh button for better UX
        self.refresh_button = ttk.Button(button_frame, text="Refresh Plugins", command=self.load_plugins)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Load plugins
        self.load_plugins()
        
    def load_plugins(self):
        """Load the list of available plugins"""
        # Clear the listbox
        self.plugin_listbox.delete(0, tk.END)        # Get all plugins
        plugins = self.plugin_manager.get_all_plugins()
        
        # Sort plugins by name
        plugin_ids = sorted(plugins.keys())
          # Keep track of active plugins for better visual indication
        active_plugins = [pid for pid in plugin_ids if plugins.get(pid, {}).get("status") == "active"]
        
        # Add plugins to listbox with active status indicator
        for plugin_id in plugin_ids:
            plugin_info = plugins.get(plugin_id, {})
            status = plugin_info.get("status", "unknown")
            display_name = f"✓ {plugin_id}" if status == "active" else plugin_id
            self.plugin_listbox.insert(tk.END, display_name)
            
        # Update status
        active_count = len([pid for pid in plugin_ids if plugins.get(pid, {}).get("status") == "active"])
        self.log(f"[Config] Loaded {len(plugin_ids)} plugins ({active_count} active)")
            
    def on_plugin_selected(self, event):
        """Handle plugin selection"""
        # Get selected plugin
        selection = self.plugin_listbox.curselection()
        if not selection:
            return
            
        plugin_name = self.plugin_listbox.get(selection[0])
        # Strip active indicator if present
        if plugin_name.startswith("✓ "):
            plugin_id = plugin_name[2:]
        else:
            plugin_id = plugin_name
        
        # Load plugin config
        self.load_plugin_config(plugin_id)
        
    def load_plugin_config(self, plugin_id):
        """
        Load configuration for a plugin with enhanced logic to find configurations
        
        Args:
            plugin_id: Plugin identifier
        """
        self.log(f"[Config] Loading configuration for plugin: {plugin_id}")
        
        # Store current plugin
        self.current_plugin_id = plugin_id          # Get plugin info
        plugin_info = self.plugin_manager.get_plugin_metadata(plugin_id)
        if not plugin_info:
            self.log(f"[Config] No plugin info found for {plugin_id}", "WARNING")
            plugin_info = {"name": plugin_id, "description": "No description available"}
            
        # Update header and description with better formatting
        plugin_name = plugin_info.get("name", plugin_id)
        plugin_data = self.plugin_manager.get_all_plugins().get(plugin_id, {})
        status = plugin_data.get("status", "unknown")
        self.config_header.config(text=f"Configure: {plugin_name} ({status})")
        description = plugin_info.get("description", "No description available.")
        version = plugin_info.get("version", "1.0.0")
        author = plugin_info.get("author", "Unknown")
        self.config_description.config(text=f"{description}\nVersion: {version} | Author: {author}")
        
        # Clear previous config widgets
        for widget in self.config_content.winfo_children():
            widget.destroy()
        self.config_widgets = {}
        
        # Enhanced plugin configuration loading
        plugin_config = self._get_plugin_config(plugin_id)
        
        # Log the source of the configuration
        if plugin_config:
            self.log(f"[Config] Loaded configuration for plugin: {plugin_id}")
        else:
            self.log(f"[Config] No configuration found for plugin: {plugin_id}")
            plugin_config = {}
        
        # Get schema with improved detection
        schema = self._get_plugin_config_schema(plugin_id)
        
        if not schema:
            # No schema, show a message
            ttk.Label(self.config_content, text="This plugin has no configurable settings.",
                      font=("", 10)).grid(row=0, column=0, padx=10, pady=25)
            self.save_button.state(['disabled'])
            self.reset_button.state(['disabled'])
            self.current_config = {}
            return
            
        # Store current config
        self.current_config = plugin_config.copy()
        
        # Create widgets for config options with better layout
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
                var = tk.IntVar(value=int(field_value) if field_value not in (None, "") else 0)
                min_val = field_info.get("min", 0)
                max_val = field_info.get("max", 1000000)
                widget = ttk.Spinbox(self.config_content, from_=min_val, to=max_val, textvariable=var, width=10)
                self.config_widgets[field_name] = var
            
            elif field_type == "float":
                var = tk.DoubleVar(value=float(field_value) if field_value not in (None, "") else 0.0)
                min_val = field_info.get("min", 0.0)
                max_val = field_info.get("max", 1000000.0)
                increment = field_info.get("increment", 0.1)
                widget = ttk.Spinbox(self.config_content, from_=min_val, to=max_val, increment=increment, textvariable=var, width=10)
                self.config_widgets[field_name] = var
            
            elif field_type == "text":
                var = tk.StringVar(value=str(field_value) if field_value is not None else "")
                widget = ttk.Entry(self.config_content, textvariable=var, width=40)
                self.config_widgets[field_name] = var
            
            elif field_type == "multiline":
                frame = ttk.Frame(self.config_content)
                widget = tk.Text(frame, height=5, width=40)
                if field_value is not None:
                    widget.insert(tk.END, str(field_value))
                scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=widget.yview)
                widget.configure(yscrollcommand=scrollbar.set)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                self.config_widgets[field_name] = widget
                widget = frame
            
            elif field_type == "password":
                var = tk.StringVar(value=str(field_value) if field_value is not None else "")
                widget = ttk.Entry(self.config_content, textvariable=var, width=40, show="*")
                self.config_widgets[field_name] = var
            
            elif field_type == "color":
                var = tk.StringVar(value=str(field_value) if field_value is not None else "#000000")
                
                color_frame = ttk.Frame(self.config_content)
                entry = ttk.Entry(color_frame, textvariable=var, width=10)
                entry.pack(side=tk.LEFT, padx=(0, 5))
                
                color_preview = tk.Label(color_frame, text="   ", bg=var.get(), relief=tk.RIDGE)
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
                var = tk.StringVar(value=str(field_value) if field_value is not None else "")
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
        
    def _get_plugin_config(self, plugin_id):
        """
        Enhanced method to get plugin configuration from multiple sources
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Plugin configuration dictionary
        """        # Strategy 1: Check for dedicated nested section (modern format)
        all_configs = self.config_manager.get("plugins", {}) or {}
        if plugin_id in all_configs and isinstance(all_configs[plugin_id], dict):
            self.log(f"[Config] Found configuration in 'plugins.{plugin_id}' section")
            return all_configs[plugin_id]
            
        # Strategy 2: Check for legacy format with plugin_id prefix
        prefix = f"plugins.{plugin_id}."
        prefixed_configs = {}
        # The config_manager might not have a get_all method, so we need to handle it safely
        try:
            # First try using get_all if it exists
            if hasattr(self.config_manager, 'get_all') and callable(self.config_manager.get_all):
                all_config = self.config_manager.get_all()
            # Fall back to accessing the config attribute directly
            elif hasattr(self.config_manager, 'config'):
                all_config = self.config_manager.config
            else:
                all_config = {}
                
            # Now process the prefixed keys
            for key, value in all_config.items():
                if key.startswith(prefix):
                    # Extract the actual config key (remove the prefix)
                    config_key = key[len(prefix):]
                    prefixed_configs[config_key] = value
        except Exception as e:
            self.log(f"[Config] Error getting prefixed configs: {e}", "ERROR")
            prefixed_configs = {}
        
        if prefixed_configs:
            self.log(f"[Config] Found legacy configuration with prefix: {prefix}")
            return prefixed_configs
                
        # Strategy 3: Check for direct plugin_id entry
        direct_config = self.config_manager.get(plugin_id, None)
        if isinstance(direct_config, dict):
            self.log(f"[Config] Found direct configuration under key: {plugin_id}")
            return direct_config
        
        # Strategy 4: Check for plugin-specific configuration file
        plugin_path = self._get_plugin_path(plugin_id)
        if plugin_path:
            config_paths = [
                os.path.join(plugin_path, "config.json"),
                os.path.join("data", "plugins", "config", f"{plugin_id}.json"),
                os.path.join("data", "plugins", "config", plugin_id, "config.json")
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            if isinstance(config, dict):
                                self.log(f"[Config] Loaded configuration from file: {config_path}")
                                return config
                    except Exception as e:
                        self.log(f"[Config] Error loading config from file {config_path}: {e}", "ERROR")
        
        # Strategy 5: If the plugin has a get_default_config method, use that
        plugin_instance = self.plugin_manager.get_plugin_instance(plugin_id)
        if plugin_instance:
            if hasattr(plugin_instance, "get_default_config") and callable(plugin_instance.get_default_config):
                try:
                    config = plugin_instance.get_default_config()
                    if isinstance(config, dict):
                        self.log(f"[Config] Using default configuration from plugin instance")
                        return config
                except Exception as e:
                    self.log(f"[Config] Error getting default config from plugin: {e}", "ERROR")
        
        return {}
        
    def _get_plugin_path(self, plugin_id):
        """
        Get the filesystem path to a plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Path to plugin directory or None if not found
        """
        plugins_dir = os.environ.get("IRINTAI_PLUGINS_DIR", "plugins")
        plugin_path = os.path.join(plugins_dir, plugin_id)
        
        if os.path.exists(plugin_path) and os.path.isdir(plugin_path):
            return plugin_path
            
        # Check if it might be a module-style plugin
        for path in sys.path:
            module_path = os.path.join(path, plugin_id)
            if os.path.exists(module_path) and os.path.isdir(module_path):
                return module_path
                
        return None
        
    def _get_plugin_config_schema(self, plugin_id):
        """
        Enhanced method to get configuration schema for a plugin from multiple sources
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Configuration schema dictionary
        """
        schema = {}
        
        # Strategy 1: Get schema from plugin instance
        plugin_instance = self.plugin_manager.get_plugin_instance(plugin_id)
        if plugin_instance:
            # Check for get_config_schema method (most flexible approach)
            if hasattr(plugin_instance, "get_config_schema") and callable(plugin_instance.get_config_schema):
                try:
                    plugin_schema = plugin_instance.get_config_schema()
                    if plugin_schema:
                        self.log(f"[Config] Found schema via get_config_schema() method")
                        return plugin_schema
                except Exception as e:
                    self.log(f"[Config] Error calling get_config_schema(): {e}", "ERROR")
            
            # Check for CONFIG_SCHEMA attribute
            if hasattr(plugin_instance, "CONFIG_SCHEMA"):
                try:
                    plugin_schema = plugin_instance.CONFIG_SCHEMA
                    if plugin_schema:
                        self.log(f"[Config] Found schema via CONFIG_SCHEMA attribute")
                        return plugin_schema
                except Exception as e:
                    self.log(f"[Config] Error accessing CONFIG_SCHEMA: {e}", "ERROR")
        
        # Strategy 2: Check for schema files
        plugin_path = self._get_plugin_path(plugin_id)
        if plugin_path:
            # Check multiple possible schema file locations
            schema_paths = [
                os.path.join(plugin_path, "config_schema.json"),
                os.path.join(plugin_path, "schema.json"),
                os.path.join("data", "plugins", "config", f"{plugin_id}_schema.json"),
                os.path.join("data", "plugins", "config", plugin_id, "schema.json")
            ]
            
            for schema_path in schema_paths:
                if os.path.exists(schema_path):
                    try:
                        with open(schema_path, 'r', encoding='utf-8') as f:
                            file_schema = json.load(f)
                            if file_schema:
                                self.log(f"[Config] Loaded schema from file: {schema_path}")
                                return file_schema
                    except Exception as e:
                        self.log(f"[Config] Error loading schema from {schema_path}: {e}", "ERROR")
        
        # Strategy 3: Infer schema from existing configuration
        plugin_config = self._get_plugin_config(plugin_id)
        if plugin_config:
            inferred_schema = {}
            for key, value in plugin_config.items():
                field_type = "string"
                if isinstance(value, bool):
                    field_type = "boolean"
                elif isinstance(value, int):
                    field_type = "integer"
                elif isinstance(value, float):
                    field_type = "float"
                
                inferred_schema[key] = {
                    "label": key.replace('_', ' ').title(),
                    "type": field_type,
                    "default": value,
                    "description": f"Configuration value for {key}"
                }
            
            if inferred_schema:
                self.log(f"[Config] Created inferred schema from existing configuration")
                return inferred_schema
        
        return schema
    def save_config(self):
        """Save the current plugin configuration with improved saving strategy"""
        if not self.current_plugin_id:
            return
            
        # Collect config values for current plugin
        new_config = {}
        
        for field_name, widget in self.config_widgets.items():
            if isinstance(widget, (tk.BooleanVar, tk.StringVar, tk.IntVar, tk.DoubleVar)):
                new_config[field_name] = widget.get()
            elif isinstance(widget, tk.Text):
                new_config[field_name] = widget.get(1.0, tk.END).rstrip()
        
        # Save into nested 'plugins' section in config manager (preferred method)
        all_configs = self.config_manager.get("plugins", {}) or {}
        all_configs[self.current_plugin_id] = new_config
        self.config_manager.set("plugins", all_configs)
        
        # Also ensure compatibility with code that might look for prefixed keys
        # by adding prefixed config entries (will be deprecated in future)
        for key, value in new_config.items():
            prefixed_key = f"plugins.{self.current_plugin_id}.{key}"
            self.config_manager.set(prefixed_key, value)
        
        # Save config to disk
        success = self.config_manager.save_config()
        if not success:
            self.log(f"[Config] Failed to save configuration for plugin: {self.current_plugin_id}", "ERROR")
            messagebox.showerror(
                "Configuration Error",
                f"Failed to save configuration for plugin '{self.current_plugin_id}'."
            )
            return
        
        # Update current config
        self.current_config = new_config.copy()
        
        # Use plugin manager's update_plugin_configuration method
        try:
            success = self.plugin_manager.update_plugin_configuration(self.current_plugin_id, new_config)
            if success:
                self.log(f"[Config] Updated plugin configuration via plugin manager")
            else:
                # Fall back to direct notification
                plugin_instance = self.plugin_manager.get_plugin_instance(self.current_plugin_id)
                if plugin_instance:
                    # First check for on_config_changed method
                    if hasattr(plugin_instance, "on_config_changed") and callable(plugin_instance.on_config_changed):
                        try:
                            plugin_instance.on_config_changed(new_config)
                            self.log(f"[Config] Notified plugin of configuration change via on_config_changed()")
                        except Exception as e:
                            self.log(f"[Config] Error in plugin.on_config_changed(): {e}", "ERROR")
                    
                    # Also check for configure method for older plugins
                    elif hasattr(plugin_instance, "configure") and callable(plugin_instance.configure):
                        try:
                            plugin_instance.configure(new_config)
                            self.log(f"[Config] Notified plugin of configuration change via configure()")
                        except Exception as e:
                            self.log(f"[Config] Error in plugin.configure(): {e}", "ERROR")
        except Exception as e:
            self.log(f"[Config] Error updating plugin configuration: {e}", "ERROR")
        
        # Show confirmation
        messagebox.showinfo(
            "Configuration Saved", 
            f"Configuration for plugin '{self.current_plugin_id}' has been saved successfully."
        )
        
    def reset_config(self):
        """Reset the current plugin configuration to defaults"""
        if not self.current_plugin_id:
            return
            
        # Ask for confirmation
        result = messagebox.askyesno(
            "Reset Configuration",
            f"Are you sure you want to reset the configuration for plugin '{self.current_plugin_id}'? This will revert to default values.",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
            
        # If the plugin has a get_default_config method, use that to reset
        plugin_instance = self.plugin_manager.get_plugin_instance(self.current_plugin_id)
        default_config = {}
        
        if plugin_instance and hasattr(plugin_instance, "get_default_config") and callable(plugin_instance.get_default_config):
            try:
                default_config = plugin_instance.get_default_config()
                self.log(f"[Config] Reset to default configuration from plugin instance")
            except Exception as e:
                self.log(f"[Config] Error getting default config: {e}", "ERROR")
        
        # Get the schema to find default values
        schema = self._get_plugin_config_schema(self.current_plugin_id)
        if schema:
            for field_name, field_info in schema.items():
                if field_name not in default_config:
                    default_config[field_name] = field_info.get("default", "")
        
        # Apply default config to widgets
        for field_name, value in default_config.items():
            if field_name in self.config_widgets:
                widget = self.config_widgets[field_name]
                if isinstance(widget, (tk.BooleanVar, tk.StringVar, tk.IntVar, tk.DoubleVar)):
                    widget.set(value)
                elif isinstance(widget, tk.Text):
                    widget.delete(1.0, tk.END)
                    widget.insert(tk.END, value)
        
        # Reset current config
        self.current_config = default_config.copy()
        
    def _on_frame_configure(self, event):
        """Handle frame configuration event"""
        # Update the scroll region to encompass the inner frame
        self.config_canvas.configure(scrollregion=self.config_canvas.bbox("all"))
        
    def _on_canvas_configure(self, event):
        """Handle canvas configuration event"""
        # Update the width of the inner frame to fill the canvas
        width = event.width - 5  # Subtract a bit to avoid horizontal scrollbar
        self.config_canvas.itemconfig(self.config_canvas_window, width=width)
        
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
        
    def get_settings(self):
        """
        Get all plugin settings (used by parent config panel)
        
        Returns:
            Dictionary of plugin configurations
        """
        # If a plugin is currently selected, make sure to save its state first
        if self.current_plugin_id and self.config_widgets:
            # Collect config values
            new_config = {}
            for field_name, widget in self.config_widgets.items():
                if isinstance(widget, (tk.BooleanVar, tk.StringVar, tk.IntVar, tk.DoubleVar)):
                    new_config[field_name] = widget.get()
                elif isinstance(widget, tk.Text):
                    new_config[field_name] = widget.get(1.0, tk.END).rstrip()
                    
            # Only update if values have changed
            if new_config != self.current_config:
                self.current_config = new_config.copy()
        
        # Read all plugin configs from the config manager
        all_configs = self.config_manager.get("plugins", {}) or {}
        return all_configs
    
    def apply_settings(self):
        """Apply current settings to plugins without saving to config file"""
        if not self.current_plugin_id:
            return
            
        # Collect config values for current plugin
        new_config = {}
        
        for field_name, widget in self.config_widgets.items():
            if isinstance(widget, (tk.BooleanVar, tk.StringVar, tk.IntVar, tk.DoubleVar)):
                new_config[field_name] = widget.get()
            elif isinstance(widget, tk.Text):
                new_config[field_name] = widget.get(1.0, tk.END).rstrip()
        
        # Update current config
        self.current_config = new_config.copy()
        
        # Use plugin manager's update_plugin_configuration method
        try:
            success = self.plugin_manager.update_plugin_configuration(self.current_plugin_id, new_config)
            if success:
                self.log(f"[Config] Applied settings via plugin manager")
                return True
            else:
                # Fall back to direct notification
                plugin_instance = self.plugin_manager.get_plugin_instance(self.current_plugin_id)
                if plugin_instance:
                    # First check for on_config_changed method
                    if hasattr(plugin_instance, "on_config_changed") and callable(plugin_instance.on_config_changed):
                        try:
                            plugin_instance.on_config_changed(new_config)
                            self.log(f"[Config] Applied settings via on_config_changed()")
                            return True
                        except Exception as e:
                            self.log(f"[Config] Error in plugin.on_config_changed(): {e}", "ERROR")
                    
                    # Also check for configure method for older plugins
                    elif hasattr(plugin_instance, "configure") and callable(plugin_instance.configure):
                        try:
                            plugin_instance.configure(new_config)
                            self.log(f"[Config] Applied settings via configure()")
                            return True
                        except Exception as e:
                            self.log(f"[Config] Error in plugin.configure(): {e}", "ERROR")
        except Exception as e:
            self.log(f"[Config] Error applying settings: {e}", "ERROR")
        return False
