"""
Plugin settings panel fix for IrintAI Assistant
"""

def fix_plugin_settings_panel(panel):
    """
    Apply fixes to the plugin settings panel
    
    Args:
        panel: The plugin panel instance to fix
    """
    # Store the original methods we're overriding
    original_load_settings = panel.load_settings_plugins
    original_on_selected = panel.on_settings_plugin_selected
    original_load_config = panel.load_plugin_config
    
    # Override with fixed methods
    def fixed_load_settings_plugins():
        """Load the list of available plugins into the settings tab"""
        # Clear the listbox
        panel.settings_plugin_listbox.delete(0, tk.END)
        
        # Get all plugins
        plugins = panel.plugin_manager.get_all_plugins()
        if not plugins:
            # If plugins dict is empty, try to discover plugins first
            panel.plugin_manager.discover_plugins()
            # Try again to get plugins
            plugins = panel.plugin_manager.get_all_plugins()
            
        # Sort plugins by name
        plugin_ids = sorted(plugins.keys()) if plugins else []
        
        # Add plugins to listbox with status indicator
        for plugin_id in plugin_ids:
            plugin_info = plugins.get(plugin_id, {})
            status = plugin_info.get("status", "unknown")
            display_name = f"✓ {plugin_id}" if status == "active" else plugin_id
            panel.settings_plugin_listbox.insert(tk.END, display_name)
            
        # Log the number of plugins found
        if hasattr(panel, 'log') and panel.log:
            panel.log(f"[PluginPanel] Loaded {len(plugin_ids)} plugins into settings tab")
    
    def fixed_on_settings_plugin_selected(event):
        """Handle plugin selection in the settings tab"""
        # Get selected plugin
        selection = panel.settings_plugin_listbox.curselection()
        if not selection:
            return
            
        plugin_text = panel.settings_plugin_listbox.get(selection[0])
        # Strip active indicator if present
        if plugin_text.startswith("✓ "):
            plugin_id = plugin_text[2:]
        else:
            plugin_id = plugin_text
            
        fixed_load_plugin_config(plugin_id)
    
    def fixed_load_plugin_config(plugin_id):
        """Load the configuration for a plugin"""
        # Clear the config content
        for widget in panel.settings_content.winfo_children():
            widget.destroy()
        
        # Update current plugin
        panel.current_plugin_id = plugin_id
        panel.current_config = {}
        panel.config_widgets = {}
        
        # Get plugin info
        plugin_info = panel.plugin_manager.get_plugin_metadata(plugin_id)
        if not plugin_info:
            if hasattr(panel, 'log') and panel.log:
                panel.log(f"[PluginPanel] No metadata found for plugin: {plugin_id}")
            plugin_info = {"name": plugin_id, "description": "No description available"}
        
        # Get plugin status
        plugins = panel.plugin_manager.get_all_plugins()
        plugin_data = plugins.get(plugin_id, {})
        status = plugin_data.get("status", "unknown")
        
        # Update header and description
        plugin_name = plugin_info.get("name", plugin_id)
        panel.settings_header.config(text=f"Configure: {plugin_name} ({status})")
        
        description = plugin_info.get("description", "No description available.")
        version = plugin_info.get("version", "1.0.0")
        author = plugin_info.get("author", "Unknown")
        panel.settings_description.config(text=f"{description}\nVersion: {version} | Author: {author}")
        
        # Get plugin configuration
        config = get_plugin_config(panel, plugin_id)
        
        # Get schema
        schema = get_plugin_schema(panel, plugin_id)
        
        if not schema:
            # No schema, show a message
            import tkinter.ttk as ttk
            ttk.Label(panel.settings_content, text="This plugin has no configurable settings.",
                      font=("", 10)).grid(row=0, column=0, padx=10, pady=25)
            panel.settings_save_button.state(['disabled'])
            panel.settings_reset_button.state(['disabled'])
            panel.current_config = {}
            return
        
        # Store current config
        panel.current_config = config.copy()
        
        # Create settings UI based on schema
        create_settings_ui(panel, schema, config)
        
        # Enable buttons
        panel.settings_save_button.state(['!disabled'])
        panel.settings_reset_button.state(['!disabled'])
    
    # Replace original methods with fixed versions
    panel.load_settings_plugins = fixed_load_settings_plugins
    panel.on_settings_plugin_selected = lambda event: fixed_on_settings_plugin_selected(event)
    panel.load_plugin_config = fixed_load_plugin_config
    
    # Reload the settings plugins to apply the fix
    panel.load_settings_plugins()
    
    return panel

def get_plugin_config(panel, plugin_id):
    """Get configuration for a plugin from multiple sources"""
    config = {}
    
    # Try to get from config manager's plugins section
    if hasattr(panel, 'config_manager') and panel.config_manager:
        all_configs = panel.config_manager.get("plugins", {}) or {}
        if plugin_id in all_configs and isinstance(all_configs[plugin_id], dict):
            config = all_configs[plugin_id].copy()
            if hasattr(panel, 'log') and panel.log:
                panel.log(f"[PluginPanel] Found configuration in 'plugins.{plugin_id}' section")
            return config
            
        # Try legacy format with prefix
        prefix = f"plugins.{plugin_id}."
        prefixed_configs = {}
        try:
            if hasattr(panel.config_manager, 'get_all') and callable(panel.config_manager.get_all):
                all_config = panel.config_manager.get_all()
            elif hasattr(panel.config_manager, 'config'):
                all_config = panel.config_manager.config
            else:
                all_config = {}
                
            for key, value in all_config.items():
                if key.startswith(prefix):
                    config_key = key[len(prefix):]
                    prefixed_configs[config_key] = value
                    
            if prefixed_configs:
                if hasattr(panel, 'log') and panel.log:
                    panel.log(f"[PluginPanel] Found legacy configuration with prefix: {prefix}")
                return prefixed_configs
                
            # Try direct plugin_id entry
            direct_config = panel.config_manager.get(plugin_id, None)
            if isinstance(direct_config, dict):
                if hasattr(panel, 'log') and panel.log:
                    panel.log(f"[PluginPanel] Found direct configuration under key: {plugin_id}")
                return direct_config
        except Exception as e:
            if hasattr(panel, 'log') and panel.log:
                panel.log(f"[PluginPanel] Error getting config: {e}")
    
    # Try to get default config from plugin instance
    plugin_instance = panel.plugin_manager.get_plugin_instance(plugin_id)
    if plugin_instance:
        if hasattr(plugin_instance, "get_default_config") and callable(plugin_instance.get_default_config):
            try:
                default_config = plugin_instance.get_default_config()
                if default_config:
                    if hasattr(panel, 'log') and panel.log:
                        panel.log(f"[PluginPanel] Using default config from plugin")
                    return default_config
            except Exception as e:
                if hasattr(panel, 'log') and panel.log:
                    panel.log(f"[PluginPanel] Error getting default config: {e}")
    
    return config

def get_plugin_schema(panel, plugin_id):
    """Get schema for a plugin from multiple sources"""
    schema = {}
    
    # Try to get from plugin instance
    plugin_instance = panel.plugin_manager.get_plugin_instance(plugin_id)
    if plugin_instance:
        # Check for get_config_schema method
        if hasattr(plugin_instance, "get_config_schema") and callable(plugin_instance.get_config_schema):
            try:
                plugin_schema = plugin_instance.get_config_schema()
                if plugin_schema:
                    if hasattr(panel, 'log') and panel.log:
                        panel.log(f"[PluginPanel] Found schema via get_config_schema() method")
                    return plugin_schema
            except Exception as e:
                if hasattr(panel, 'log') and panel.log:
                    panel.log(f"[PluginPanel] Error calling get_config_schema(): {e}")
        
        # Check for CONFIG_SCHEMA attribute
        if hasattr(plugin_instance, "CONFIG_SCHEMA"):
            try:
                plugin_schema = plugin_instance.CONFIG_SCHEMA
                if plugin_schema:
                    if hasattr(panel, 'log') and panel.log:
                        panel.log(f"[PluginPanel] Found schema via CONFIG_SCHEMA attribute")
                    return plugin_schema
            except Exception as e:
                if hasattr(panel, 'log') and panel.log:
                    panel.log(f"[PluginPanel] Error accessing CONFIG_SCHEMA: {e}")
    
    # Try to infer schema from existing configuration
    config = get_plugin_config(panel, plugin_id)
    if config:
        inferred_schema = {}
        for key, value in config.items():
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
            if hasattr(panel, 'log') and panel.log:
                panel.log(f"[PluginPanel] Created inferred schema from existing configuration")
            return inferred_schema
    
    return schema

def create_settings_ui(panel, schema, config):
    """Create settings UI based on schema"""
    import tkinter as tk
    import tkinter.ttk as ttk
    
    # Create widgets for config options
    row = 0
    for field_name, field_info in schema.items():
        field_label = field_info.get("label", field_name)
        field_type = field_info.get("type", "string")
        field_default = field_info.get("default", "")
        field_desc = field_info.get("description", "")
        field_options = field_info.get("options", [])
        field_value = config.get(field_name, field_default)
        
        # Create label
        label = ttk.Label(panel.settings_content, text=f"{field_label}:")
        label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Create widget based on type
        widget = None
        
        if field_type == "boolean":
            var = tk.BooleanVar(value=field_value)
            widget = ttk.Checkbutton(panel.settings_content, variable=var)
            panel.config_widgets[field_name] = var
        
        elif field_type == "choice" and field_options:
            var = tk.StringVar(value=field_value)
            widget = ttk.Combobox(panel.settings_content, textvariable=var, values=field_options, state="readonly")
            panel.config_widgets[field_name] = var
        
        elif field_type == "integer":
            var = tk.IntVar(value=int(field_value) if field_value not in (None, "") else 0)
            min_val = field_info.get("min", 0)
            max_val = field_info.get("max", 1000000)
            widget = ttk.Spinbox(panel.settings_content, from_=min_val, to=max_val, textvariable=var, width=10)
            panel.config_widgets[field_name] = var
        
        elif field_type == "float":
            var = tk.DoubleVar(value=float(field_value) if field_value not in (None, "") else 0.0)
            min_val = field_info.get("min", 0.0)
            max_val = field_info.get("max", 1000000.0)
            increment = field_info.get("increment", 0.1)
            widget = ttk.Spinbox(panel.settings_content, from_=min_val, to=max_val, increment=increment, textvariable=var, width=10)
            panel.config_widgets[field_name] = var
        
        else:  # Default to string
            var = tk.StringVar(value=str(field_value) if field_value is not None else "")
            widget = ttk.Entry(panel.settings_content, textvariable=var, width=40)
            panel.config_widgets[field_name] = var
        
        widget.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Add tooltip/description if provided
        if field_desc:
            help_label = ttk.Label(panel.settings_content, text="ℹ️", cursor="question_arrow")
            help_label.grid(row=row, column=2, padx=5, pady=5)
            
            # Create tooltip
            create_tooltip(help_label, field_desc)
        
        row += 1

def create_tooltip(widget, text):
    """Create a tooltip for a widget"""
    import tkinter as tk
    import tkinter.ttk as ttk
    
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
