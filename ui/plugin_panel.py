"""
Plugin panel UI component for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import os
from typing import Callable, Dict, List, Any, Optional

class PluginPanel:
    """Plugin management panel for discovering, loading, and configuring plugins"""
    
    def __init__(self, parent, plugin_manager, logger: Callable):
        """
        Initialize the plugin panel
        
        Args:
            parent: Parent widget
            plugin_manager: PluginManager instance
            logger: Logging function
        """
        self.parent = parent
        self.plugin_manager = plugin_manager
        self.log = logger
        
        # Create the main frame
        self.frame = ttk.Frame(parent)
        
        # Initialize UI components
        self.initialize_ui()
        
        # Refresh plugin list
        self.refresh_plugin_list()
        
    def initialize_ui(self):
        """Initialize the UI components"""
        # Create plugin discovery section
        self.create_discovery_section()
        
        # Create plugin management section
        self.create_management_section()
        
        # Create plugin information section
        self.create_info_section()
        
        # Create progress bar
        self.create_progress_bar()
        
    def create_discovery_section(self):
        """Create the plugin discovery section"""
        discovery_frame = ttk.LabelFrame(self.frame, text="Plugin Discovery")
        discovery_frame.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)
        
        # Search path info
        path_frame = ttk.Frame(discovery_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(path_frame, text="Plugin Directory:").pack(side=tk.LEFT)
        
        self.path_var = tk.StringVar(value=self.plugin_manager.plugin_dir)
        path_label = ttk.Label(path_frame, textvariable=self.path_var, foreground="blue")
        path_label.pack(side=tk.LEFT, padx=5)
        
        # Add refresh button
        refresh_button = ttk.Button(
            path_frame,
            text="Refresh",
            command=self.refresh_plugin_list
        )
        refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # Add open folder button
        open_button = ttk.Button(
            path_frame,
            text="Open Folder",
            command=self.open_plugin_folder
        )
        open_button.pack(side=tk.RIGHT, padx=5)
        
    def create_management_section(self):
        """Create the plugin management section"""
        management_frame = ttk.LabelFrame(self.frame, text="Plugin Management")
        management_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a tree view for plugins
        columns = ("Name", "Version", "Status", "Author")
        self.plugin_tree = ttk.Treeview(
            management_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=10
        )
        
        # Configure columns
        self.plugin_tree.heading("Name", text="Plugin Name")
        self.plugin_tree.heading("Version", text="Version")
        self.plugin_tree.heading("Status", text="Status")
        self.plugin_tree.heading("Author", text="Author")
        
        self.plugin_tree.column("Name", width=150, anchor=tk.W)
        self.plugin_tree.column("Version", width=80, anchor=tk.CENTER)
        self.plugin_tree.column("Status", width=100, anchor=tk.CENTER)
        self.plugin_tree.column("Author", width=150, anchor=tk.W)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(management_frame, orient="vertical", command=self.plugin_tree.yview)
        self.plugin_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        self.plugin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.plugin_tree.bind("<<TreeviewSelect>>", self.on_plugin_selected)
        
        # Add action buttons
        action_frame = ttk.Frame(self.frame)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.load_button = ttk.Button(
            action_frame,
            text="Load Plugin",
            command=self.load_selected_plugin
        )
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        self.activate_button = ttk.Button(
            action_frame,
            text="Activate Plugin",
            command=self.activate_selected_plugin
        )
        self.activate_button.pack(side=tk.LEFT, padx=5)
        
        self.deactivate_button = ttk.Button(
            action_frame,
            text="Deactivate Plugin",
            command=self.deactivate_selected_plugin
        )
        self.deactivate_button.pack(side=tk.LEFT, padx=5)
        
        self.reload_button = ttk.Button(
            action_frame,
            text="Reload Plugin",
            command=self.reload_selected_plugin
        )
        self.reload_button.pack(side=tk.LEFT, padx=5)
        
    def create_info_section(self):
        """Create the plugin information section"""
        info_frame = ttk.LabelFrame(self.frame, text="Plugin Information")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Plugin details
        details_frame = ttk.Frame(info_frame)
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Two columns for details
        left_frame = ttk.Frame(details_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(details_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Left column - Basic info
        ttk.Label(left_frame, text="Selected Plugin:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_name_var = tk.StringVar(value="None")
        ttk.Label(left_frame, textvariable=self.selected_name_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(left_frame, text="Status:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_status_var = tk.StringVar(value="Unknown")
        ttk.Label(left_frame, textvariable=self.selected_status_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(left_frame, text="Version:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_version_var = tk.StringVar(value="Unknown")
        ttk.Label(left_frame, textvariable=self.selected_version_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Right column - Additional info
        ttk.Label(right_frame, text="Author:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_author_var = tk.StringVar(value="Unknown")
        ttk.Label(right_frame, textvariable=self.selected_author_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(right_frame, text="License:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_license_var = tk.StringVar(value="Unknown")
        ttk.Label(right_frame, textvariable=self.selected_license_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(right_frame, text="Location:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_location_var = tk.StringVar(value="Unknown")
        ttk.Label(right_frame, textvariable=self.selected_location_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Description section
        ttk.Label(info_frame, text="Description:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        self.description_text = scrolledtext.ScrolledText(info_frame, height=3, wrap=tk.WORD, font=("Helvetica", 9))
        self.description_text.pack(fill=tk.X, expand=True, padx=10, pady=5)
        
        # Configuration section
        ttk.Label(info_frame, text="Configuration:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        self.config_text = scrolledtext.ScrolledText(info_frame, height=5, wrap=tk.WORD, font=("Courier", 9))
        self.config_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configuration buttons
        config_button_frame = ttk.Frame(info_frame)
        config_button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            config_button_frame,
            text="Load Config",
            command=self.load_config
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            config_button_frame,
            text="Save Config",
            command=self.save_config
        ).pack(side=tk.LEFT, padx=5)
        
    def create_progress_bar(self):
        """Create the progress bar"""
        progress_frame = ttk.Frame(self.frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            mode="indeterminate",
            length=100
        )
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Status text
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, padx=5)
        
    def refresh_plugin_list(self):
        """Refresh the plugin list"""
        # Clear the current tree
        for item in self.plugin_tree.get_children():
            self.plugin_tree.delete(item)
            
        # Update progress bar
        self.progress_bar.start()
        self.status_var.set("Discovering plugins...")
        
        # Start discovery in a separate thread
        threading.Thread(
            target=self._discover_plugins_thread,
            daemon=True
        ).start()
        
    def _discover_plugins_thread(self):
        """Discover plugins in a background thread"""
        # Discover plugins
        self.plugin_manager.discover_plugins()
        
        # Get plugin information
        plugins_info = self.plugin_manager.get_all_plugins()
        
        # Update UI on main thread
        self.frame.after(0, lambda: self._update_plugin_tree(plugins_info))
        
    def _update_plugin_tree(self, plugins_info):
        """
        Update the plugin tree with discovered plugins
        
        Args:
            plugins_info: Dictionary of plugin information
        """
        # Clear current items
        for item in self.plugin_tree.get_children():
            self.plugin_tree.delete(item)
            
        # Add plugins to tree
        for plugin_name, info in plugins_info.items():
            self.plugin_tree.insert(
                "",
                tk.END,
                values=(
                    plugin_name,
                    info.get("version", "Unknown"),
                    info.get("status", "Unknown"),
                    info.get("author", "Unknown")
                )
            )
            
        # Stop progress bar
        self.progress_bar.stop()
        self.status_var.set(f"Found {len(plugins_info)} plugins")
        
        # Select first item if available
        if self.plugin_tree.get_children():
            first_item = self.plugin_tree.get_children()[0]
            self.plugin_tree.selection_set(first_item)
            self.on_plugin_selected()
            
    def on_plugin_selected(self, event=None):
        """Handle plugin selection in the tree"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
            
        # Get selected plugin info
        item = selection[0]
        values = self.plugin_tree.item(item, "values")
        
        plugin_name = values[0]
        plugin_status = values[2]
        
        # Get detailed metadata
        metadata = self.plugin_manager.get_plugin_metadata(plugin_name)
        
        # Update info display
        self.selected_name_var.set(plugin_name)
        self.selected_status_var.set(plugin_status)
        self.selected_version_var.set(metadata.get("version", "Unknown"))
        self.selected_author_var.set(metadata.get("author", "Unknown"))
        self.selected_license_var.set(metadata.get("license", "Unknown"))
        
        # Set location
        plugin_path = os.path.join(self.plugin_manager.plugin_dir, plugin_name)
        self.selected_location_var.set(plugin_path)
        
        # Update description
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, metadata.get("description", "No description available"))
        self.description_text.config(state=tk.DISABLED)
        
        # Update configuration display
        self.update_config_display(plugin_name)
        
        # Update button states based on plugin status
        self._update_button_states(plugin_status)
        
    def _update_button_states(self, status):
        """
        Update button states based on plugin status
        
        Args:
            status: Current plugin status
        """
        # Load button - enabled if not loaded
        self.load_button.config(
            state=tk.NORMAL if status in ["Not Loaded", "Error"] else tk.DISABLED
        )
        
        # Activate button - enabled if loaded but not active
        self.activate_button.config(
            state=tk.NORMAL if status in ["Loaded", "Inactive"] else tk.DISABLED
        )
        
        # Deactivate button - enabled if active
        self.deactivate_button.config(
            state=tk.NORMAL if status == "Active" else tk.DISABLED
        )
        
        # Reload button - enabled if loaded
        self.reload_button.config(
            state=tk.NORMAL if status in ["Loaded", "Active", "Inactive"] else tk.DISABLED
        )
        
    def update_config_display(self, plugin_name):
        """
        Update the configuration display for a plugin
        
        Args:
            plugin_name: Name of the plugin
        """
        # Clear current content
        self.config_text.config(state=tk.NORMAL)
        self.config_text.delete(1.0, tk.END)
        
        # Get plugin config path
        config_path = os.path.join(self.plugin_manager.config_dir, plugin_name, "config.json")
        
        # Check if config exists
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                # Format config as JSON
                formatted_config = json.dumps(config, indent=2)
                self.config_text.insert(tk.END, formatted_config)
            except Exception as e:
                self.config_text.insert(tk.END, f"Error loading configuration: {e}")
        else:
            self.config_text.insert(tk.END, "No configuration file found")
            
        # Make editable
        self.config_text.config(state=tk.NORMAL)
        
    def load_selected_plugin(self):
        """Load the selected plugin"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
            
        # Get selected plugin
        item = selection[0]
        values = self.plugin_tree.item(item, "values")
        plugin_name = values[0]
        
        # Update status
        self.status_var.set(f"Loading plugin: {plugin_name}...")
        self.progress_bar.start()
        
        # Load in a separate thread
        threading.Thread(
            target=self._load_plugin_thread,
            args=(plugin_name,),
            daemon=True
        ).start()
        
    def _load_plugin_thread(self, plugin_name):
        """
        Load a plugin in a background thread
        
        Args:
            plugin_name: Name of the plugin to load
        """
        # Load the plugin
        success = self.plugin_manager.load_plugin(plugin_name)
        
        # Update UI on main thread
        self.frame.after(0, lambda: self._on_plugin_loaded(plugin_name, success))
        
    def _on_plugin_loaded(self, plugin_name, success):
        """
        Handle plugin loading completion
        
        Args:
            plugin_name: Name of the plugin
            success: Whether loading was successful
        """
        # Stop progress
        self.progress_bar.stop()
        
        if success:
            self.status_var.set(f"Plugin loaded successfully: {plugin_name}")
            
            # Update plugin info in tree
            plugins_info = self.plugin_manager.get_all_plugins()
            info = plugins_info.get(plugin_name, {})
            
            for item in self.plugin_tree.get_children():
                values = self.plugin_tree.item(item, "values")
                if values[0] == plugin_name:
                    self.plugin_tree.item(
                        item,
                        values=(
                            plugin_name,
                            info.get("version", "Unknown"),
                            info.get("status", "Unknown"),
                            info.get("author", "Unknown")
                        )
                    )
                    break
                    
            # Update selection info
            if self.selected_name_var.get() == plugin_name:
                self.selected_status_var.set(info.get("status", "Unknown"))
                self._update_button_states(info.get("status", "Unknown"))
        else:
            self.status_var.set(f"Failed to load plugin: {plugin_name}")
            
    def activate_selected_plugin(self):
        """Activate the selected plugin"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
            
        # Get selected plugin
        item = selection[0]
        values = self.plugin_tree.item(item, "values")
        plugin_name = values[0]
        
        # Update status
        self.status_var.set(f"Activating plugin: {plugin_name}...")
        self.progress_bar.start()
        
        # Activate in a separate thread
        threading.Thread(
            target=self._activate_plugin_thread,
            args=(plugin_name,),
            daemon=True
        ).start()
        
    def _activate_plugin_thread(self, plugin_name):
        """
        Activate a plugin in a background thread
        
        Args:
            plugin_name: Name of the plugin to activate
        """
        # Activate the plugin
        success = self.plugin_manager.activate_plugin(plugin_name)
        
        # Update UI on main thread
        self.frame.after(0, lambda: self._on_plugin_activated(plugin_name, success))
        
    def _on_plugin_activated(self, plugin_name, success):
        """
        Handle plugin activation completion
        
        Args:
            plugin_name: Name of the plugin
            success: Whether activation was successful
        """
        # Stop progress
        self.progress_bar.stop()
        
        if success:
            self.status_var.set(f"Plugin activated successfully: {plugin_name}")
            
            # Update plugin info in tree
            plugins_info = self.plugin_manager.get_all_plugins()
            info = plugins_info.get(plugin_name, {})
            
            for item in self.plugin_tree.get_children():
                values = self.plugin_tree.item(item, "values")
                if values[0] == plugin_name:
                    self.plugin_tree.item(
                        item,
                        values=(
                            plugin_name,
                            info.get("version", "Unknown"),
                            info.get("status", "Unknown"),
                            info.get("author", "Unknown")
                        )
                    )
                    break
                    
            # Update selection info
            if self.selected_name_var.get() == plugin_name:
                self.selected_status_var.set(info.get("status", "Unknown"))
                self._update_button_states(info.get("status", "Unknown"))
        else:
            self.status_var.set(f"Failed to activate plugin: {plugin_name}")
            
    def deactivate_selected_plugin(self):
        """Deactivate the selected plugin"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
            
        # Get selected plugin
        item = selection[0]
        values = self.plugin_tree.item(item, "values")
        plugin_name = values[0]
        
        # Update status
        self.status_var.set(f"Deactivating plugin: {plugin_name}...")
        self.progress_bar.start()
        
        # Deactivate in a separate thread
        threading.Thread(
            target=self._deactivate_plugin_thread,
            args=(plugin_name,),
            daemon=True
        ).start()
        
    def _deactivate_plugin_thread(self, plugin_name):
        """
        Deactivate a plugin in a background thread
        
        Args:
            plugin_name: Name of the plugin to deactivate
        """
        # Deactivate the plugin
        success = self.plugin_manager.deactivate_plugin(plugin_name)
        
        # Update UI on main thread
        self.frame.after(0, lambda: self._on_plugin_deactivated(plugin_name, success))
        
    def _on_plugin_deactivated(self, plugin_name, success):
        """
        Handle plugin deactivation completion
        
        Args:
            plugin_name: Name of the plugin
            success: Whether deactivation was successful
        """
        # Stop progress
        self.progress_bar.stop()
        
        if success:
            self.status_var.set(f"Plugin deactivated successfully: {plugin_name}")
            
            # Update plugin info in tree
            plugins_info = self.plugin_manager.get_all_plugins()
            info = plugins_info.get(plugin_name, {})
            
            for item in self.plugin_tree.get_children():
                values = self.plugin_tree.item(item, "values")
                if values[0] == plugin_name:
                    self.plugin_tree.item(
                        item,
                        values=(
                            plugin_name,
                            info.get("version", "Unknown"),
                            info.get("status", "Unknown"),
                            info.get("author", "Unknown")
                        )
                    )
                    break
                    
            # Update selection info
            if self.selected_name_var.get() == plugin_name:
                self.selected_status_var.set(info.get("status", "Unknown"))
                self._update_button_states(info.get("status", "Unknown"))
        else:
            self.status_var.set(f"Failed to deactivate plugin: {plugin_name}")
            
    def reload_selected_plugin(self):
        """Reload the selected plugin"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
            
        # Get selected plugin
        item = selection[0]
        values = self.plugin_tree.item(item, "values")
        plugin_name = values[0]
        
        # Confirm reload
        result = messagebox.askyesno(
            "Reload Plugin",
            f"Are you sure you want to reload the plugin '{plugin_name}'?\n\n"
            "This will deactivate the plugin, unload it, and load it again.",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
            
        # Update status
        self.status_var.set(f"Reloading plugin: {plugin_name}...")
        self.progress_bar.start()
        
        # Reload in a separate thread
        threading.Thread(
            target=self._reload_plugin_thread,
            args=(plugin_name,),
            daemon=True
        ).start()
        
    def _reload_plugin_thread(self, plugin_name):
        """
        Reload a plugin in a background thread
        
        Args:
            plugin_name: Name of the plugin to reload
        """
        # Reload the plugin
        success = self.plugin_manager.reload_plugin(plugin_name)
        
        # Update UI on main thread
        self.frame.after(0, lambda: self._on_plugin_reloaded(plugin_name, success))
        
    def _on_plugin_reloaded(self, plugin_name, success):
        """
        Handle plugin reload completion
        
        Args:
            plugin_name: Name of the plugin
            success: Whether reload was successful
        """
        # Stop progress
        self.progress_bar.stop()
        
        if success:
            self.status_var.set(f"Plugin reloaded successfully: {plugin_name}")
            
            # Update plugin info in tree
            plugins_info = self.plugin_manager.get_all_plugins()
            info = plugins_info.get(plugin_name, {})
            
            for item in self.plugin_tree.get_children():
                values = self.plugin_tree.item(item, "values")
                if values[0] == plugin_name:
                    self.plugin_tree.item(
                        item,
                        values=(
                            plugin_name,
                            info.get("version", "Unknown"),
                            info.get("status", "Unknown"),
                            info.get("author", "Unknown")
                        )
                    )
                    break
                    
            # Update selection info
            if self.selected_name_var.get() == plugin_name:
                self.selected_status_var.set(info.get("status", "Unknown"))
                self._update_button_states(info.get("status", "Unknown"))
                
            # Update config display
            self.update_config_display(plugin_name)
        else:
            self.status_var.set(f"Failed to reload plugin: {plugin_name}")
            
    def load_config(self):
        """Load configuration from file"""
        plugin_name = self.selected_name_var.get()
        if plugin_name == "None":
            return
            
        # Get config path
        config_path = os.path.join(self.plugin_manager.config_dir, plugin_name, "config.json")
        
        # Check if config exists
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                # Format config as JSON
                formatted_config = json.dumps(config, indent=2)
                
                # Update display
                self.config_text.config(state=tk.NORMAL)
                self.config_text.delete(1.0, tk.END)
                self.config_text.insert(tk.END, formatted_config)
                
                self.status_var.set(f"Configuration loaded for {plugin_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
        else:
            messagebox.showinfo("Information", "No configuration file found")
            
    def save_config(self):
        """Save configuration to file"""
        plugin_name = self.selected_name_var.get()
        if plugin_name == "None":
            return
            
        # Get config from text box
        config_str = self.config_text.get(1.0, tk.END)
        
        try:
            # Parse JSON
            config = json.loads(config_str)
            
            # Create config directory
            config_dir = os.path.join(self.plugin_manager.config_dir, plugin_name)
            os.makedirs(config_dir, exist_ok=True)
            
            # Save config
            config_path = os.path.join(config_dir, "config.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            # Update plugin configuration
            self.plugin_manager.update_plugin_configuration(plugin_name, config)
            
            self.status_var.set(f"Configuration saved for {plugin_name}")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            
    def open_plugin_folder(self):
        """Open the plugin folder in file explorer"""
        import os
        import subprocess
        import sys
        
        plugin_dir = self.plugin_manager.plugin_dir
        
        try:
            if not os.path.exists(plugin_dir):
                os.makedirs(plugin_dir, exist_ok=True)
                
            # Open folder based on OS
            if os.name == 'nt':  # Windows
                os.startfile(plugin_dir)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', plugin_dir])
                
            self.log(f"[Opened] Plugin folder: {plugin_dir}")
        except Exception as e:
            self.log(f"[Error] Cannot open plugin folder: {e}")
            messagebox.showerror("Error", f"Cannot open plugin folder: {e}")