"""
Plugin panel UI component for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import os
from typing import Callable, Dict, List, Any, Optional
import time

# Constants for model status
MODEL_STATUS = {
    "INSTALLED": "Installed",
    "RUNNING": "Running",
    "LOADING": "Loading",
    "ERROR": "Error",
    "NOT_INSTALLED": "Not Installed"
}

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
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create local plugins tab
        self.local_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.local_frame, text="Local Plugins")
        
        # Create marketplace tab
        self.marketplace_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.marketplace_frame, text="Plugin Marketplace")
        
        # Create sandbox tab
        self.sandbox_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sandbox_frame, text="Plugin Sandbox")
        
        # Setup local plugins tab
        self.setup_local_plugins_tab()
        
        # Setup marketplace tab
        self.setup_marketplace_tab()
        
        # Setup sandbox tab
        self.setup_sandbox_tab()
        
        # Create progress bar
        self.create_progress_bar()

    def setup_local_plugins_tab(self):
        """Setup the local plugins tab"""
        # Create plugin discovery section
        self.create_discovery_section()
        
        # Create plugin management section
        self.create_management_section()
        
        # Create plugin information section
        self.create_info_section()

    def setup_marketplace_tab(self):
        """Setup the plugin marketplace tab"""
        # Create search frame
        search_frame = ttk.Frame(self.marketplace_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Search Plugins:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            search_frame,
            text="Search",
            command=self.search_marketplace
        ).pack(side=tk.LEFT, padx=5)
        
        # Repository selector
        repo_frame = ttk.Frame(search_frame)
        repo_frame.pack(side=tk.RIGHT)
        
        ttk.Label(repo_frame, text="Repository:").pack(side=tk.LEFT)
        
        self.repo_var = tk.StringVar(value="Official")
        repo_combobox = ttk.Combobox(
            repo_frame,
            textvariable=self.repo_var,
            values=["Official", "Community", "All"],
            state="readonly",
            width=12
        )
        repo_combobox.pack(side=tk.LEFT, padx=5)
        
        # Create marketplace results treeview
        marketplace_frame = ttk.LabelFrame(self.marketplace_frame, text="Available Plugins")
        marketplace_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a tree view for marketplace plugins
        columns = ("Name", "Version", "Rating", "Downloads")
        self.marketplace_tree = ttk.Treeview(
            marketplace_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=10
        )
        
        # Configure columns
        self.marketplace_tree.heading("Name", text="Plugin Name")
        self.marketplace_tree.heading("Version", text="Version")
        self.marketplace_tree.heading("Rating", text="Rating")
        self.marketplace_tree.heading("Downloads", text="Downloads")
        
        self.marketplace_tree.column("Name", width=200, anchor=tk.W)
        self.marketplace_tree.column("Version", width=80, anchor=tk.CENTER)
        self.marketplace_tree.column("Rating", width=80, anchor=tk.CENTER)
        self.marketplace_tree.column("Downloads", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(marketplace_frame, orient="vertical", command=self.marketplace_tree.yview)
        self.marketplace_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        self.marketplace_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.marketplace_tree.bind("<<TreeviewSelect>>", self.on_marketplace_selected)
        
        # Plugin details section
        details_frame = ttk.LabelFrame(self.marketplace_frame, text="Plugin Details")
        details_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Plugin description
        ttk.Label(details_frame, text="Description:").pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        self.market_description = scrolledtext.ScrolledText(details_frame, height=5, wrap=tk.WORD)
        self.market_description.pack(fill=tk.X, padx=10, pady=5)
        
        # Plugin metadata
        meta_frame = ttk.Frame(details_frame)
        meta_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Author and rating info
        left_meta = ttk.Frame(meta_frame)
        left_meta.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_meta, text="Author:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.market_author_var = tk.StringVar(value="-")
        ttk.Label(left_meta, textvariable=self.market_author_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(left_meta, text="Category:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.market_category_var = tk.StringVar(value="-")
        ttk.Label(left_meta, textvariable=self.market_category_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Size and release info
        right_meta = ttk.Frame(meta_frame)
        right_meta.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(right_meta, text="Last Updated:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.market_updated_var = tk.StringVar(value="-")
        ttk.Label(right_meta, textvariable=self.market_updated_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(right_meta, text="Size:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.market_size_var = tk.StringVar(value="-")
        ttk.Label(right_meta, textvariable=self.market_size_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Dependencies section
        ttk.Label(details_frame, text="Dependencies:").pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        self.dependencies_var = tk.StringVar(value="None")
        ttk.Label(
            details_frame,
            textvariable=self.dependencies_var,
            wraplength=400
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(details_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            action_frame,
            text="Install Plugin",
            command=self.install_marketplace_plugin
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Visit Website",
            command=self.visit_plugin_website
        ).pack(side=tk.LEFT, padx=5)
        
        # Add dependency view button
        self.dependency_button = ttk.Button(
            action_frame,
            text="View Dependencies",
            command=self.view_plugin_dependencies
        )
        self.dependency_button.pack(side=tk.LEFT, padx=5)
        
        # Add update button
        self.update_button = ttk.Button(
            action_frame,
            text="Check for Updates",
            command=self.check_plugin_updates
        )
        self.update_button.pack(side=tk.RIGHT, padx=5)

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

    def create_plugin_action_menu(self):
        """Create menu for plugin-provided model actions"""
        # Find appropriate frame to add menu
        actions_frame = None
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Model Management":
                # Get the first child frame which should be the actions frame
                actions_frame = child.winfo_children()[0]
                break
                
        if not actions_frame:
            return
            
        # Create a menubutton for plugin actions
        self.plugin_action_button = ttk.Menubutton(
            actions_frame,
            text="Plugin Actions",
            direction="below"
        )
        self.plugin_action_button.pack(side=tk.RIGHT, padx=5)
        
        # Create the dropdown menu
        self.plugin_action_menu = tk.Menu(self.plugin_action_button, tearoff=0)
        self.plugin_action_button["menu"] = self.plugin_action_menu
        
        # Add placeholder when empty
        self.plugin_action_menu.add_command(
            label="No plugin actions available",
            state=tk.DISABLED
        )

    def register_plugin_extension(self, plugin_id, plugin):
        """
        Register plugin extensions for the model panel
        
        Args:
            plugin_id: Plugin identifier
            plugin: Plugin instance
        """
        # Skip if plugin doesn't have model extensions
        if not hasattr(plugin, "get_model_extensions"):
            return
            
        try:
            # Get extensions from plugin
            extensions = plugin.get_model_extensions()
            
            if not extensions or not isinstance(extensions, dict):
                return
                
            # Register model providers
            if "model_providers" in extensions and isinstance(extensions["model_providers"], dict):
                for name, provider_func in extensions["model_providers"].items():
                    if callable(provider_func):
                        self.plugin_model_providers[f"{plugin_id}.{name}"] = provider_func
                
            # Register model configurations
            if "model_configs" in extensions and isinstance(extensions["model_configs"], dict):
                for model_name, config_func in extensions["model_configs"].items():
                    if callable(config_func):
                        self.plugin_model_configs[f"{plugin_id}.{model_name}"] = config_func
                        
            # Register model actions
            if "model_actions" in extensions and isinstance(extensions["model_actions"], dict):
                for action_name, action_func in extensions["model_actions"].items():
                    if callable(action_func):
                        self.plugin_actions[f"{plugin_id}.{action_name}"] = {
                            "function": action_func,
                            "label": action_name.replace("_", " ").title()
                        }
            
            # Register UI extensions
            if "ui_extensions" in extensions and isinstance(extensions["ui_extensions"], list):
                self.add_plugin_ui_extensions(plugin_id, extensions["ui_extensions"])
                
            # Update UI to reflect new extensions            
            self.update_plugin_action_menu()
            
            # Refresh model list to include custom models if any
            if "model_providers" in extensions:
                self.refresh_model_list()
            
            self.log(f"[Model Panel] Registered extensions from plugin: {plugin_id}")
            
        except Exception as e:
            self.log(f"[Model Panel] Error registering extensions from plugin {plugin_id}: {e}")

    def unregister_plugin_extension(self, plugin_id):
        """
        Unregister plugin extensions
        
        Args:
            plugin_id: Plugin identifier
        """
        # Remove model providers
        providers_to_remove = [k for k in self.plugin_model_providers if k.startswith(f"{plugin_id}.")]
        for provider_id in providers_to_remove:
            del self.plugin_model_providers[provider_id]
        
        # Remove model configs
        configs_to_remove = [k for k in self.plugin_model_configs if k.startswith(f"{plugin_id}.")]
        for config_id in configs_to_remove:
            del self.plugin_model_configs[config_id]
        
        # Remove actions
        actions_to_remove = [k for k in self.plugin_actions if k.startswith(f"{plugin_id}.")]
        for action_id in actions_to_remove:
            del self.plugin_actions[action_id]
        
        # Remove UI extensions
        if plugin_id in self.plugin_ui_extensions:
            for extension in self.plugin_ui_extensions[plugin_id]:
                if extension.winfo_exists():
                    extension.destroy()
            del self.plugin_ui_extensions[plugin_id]
        
        # Update UI to reflect removed extensions
        self.update_plugin_action_menu()
        
        # Hide plugin frame if no more extensions
        if not any(self.plugin_ui_extensions.values()) and self.plugin_frame.winfo_ismapped():
            self.plugin_frame.pack_forget()
            
        # Refresh model list if we removed model providers
        if any(provider.startswith(f"{plugin_id}.") for provider in providers_to_remove):
            self.refresh_model_list()
        
        self.log(f"[Model Panel] Unregistered extensions from plugin: {plugin_id}")

    def add_plugin_ui_extensions(self, plugin_id, extensions):
        """
        Add plugin UI extensions to the model panel
        
        Args:
            plugin_id: Plugin identifier
            extensions: List of UI extension widgets
        """
        # Skip if no extensions
        if not extensions:
            return
            
        # Create container for this plugin if needed
        if plugin_id not in self.plugin_ui_extensions:
            self.plugin_ui_extensions[plugin_id] = []
        
        # Add each extension
        for extension in extensions:
            if isinstance(extension, tk.Widget):
                # Add to plugin frame
                extension.pack(in_=self.plugin_frame, fill=tk.X, padx=5, pady=2)
                
                # Add to our tracking list
                self.plugin_ui_extensions[plugin_id].append(extension)
        
        # Show the plugin frame if not already visible
        if not self.plugin_frame.winfo_ismapped() and any(self.plugin_ui_extensions.values()):
            self.plugin_frame.pack(fill=tk.X, padx=10, pady=10, before=self.frame.winfo_children()[2])

    def update_plugin_action_menu(self):
        """Update the plugin action menu with registered actions"""
        # Skip if menu doesn't exist
        if not hasattr(self, "plugin_action_menu"):
            return
            
        # Clear existing items
        self.plugin_action_menu.delete(0, tk.END)
        
        # Add plugin actions
        if self.plugin_actions:
            for action_id, action_info in sorted(self.plugin_actions.items(), key=lambda x: x[1]["label"]):
                # Add to menu
                self.plugin_action_menu.add_command(
                    label=action_info["label"],
                    command=lambda aid=action_id: self.execute_plugin_action(aid)
                )
        else:
            # Add placeholder
            self.plugin_action_menu.add_command(
                label="No plugin actions available",
                state=tk.DISABLED
            )

    def on_plugin_activated(self, plugin_id, plugin_instance):
        """
        Handle plugin activation event
        
        Args:
            plugin_id: ID of activated plugin
            plugin_instance: Plugin instance
        """
        # Register model extensions for newly activated plugin
        self.register_plugin_extension(plugin_id, plugin_instance)

    def on_plugin_deactivated(self, plugin_id):
        """
        Handle plugin deactivation event
        
        Args:
            plugin_id: ID of deactivated plugin
        """
        # Unregister model extensions
        self.unregister_plugin_extension(plugin_id)

    def on_plugin_unloaded(self, plugin_id):
        """
        Handle plugin unloading event
        
        Args:
            plugin_id: ID of unloaded plugin
        """
        # Ensure extensions are unregistered
        self.unregister_plugin_extension(plugin_id)

    def execute_plugin_action(self, action_id):
        """
        Execute a plugin-provided model action
        
        Args:
            action_id: ID of the action to execute
        """
        if action_id not in self.plugin_actions:
            return
            
        # Get selected model
        selection = self.model_tree.selection()
        if not selection:
            messagebox.showinfo("No Model Selected", "Please select a model first")
            return
            
        # Get model name
        item = selection[0]
        values = self.model_tree.item(item, "values")
        model_name = values[0]
        
        try:
            # Execute the action
            action_func = self.plugin_actions[action_id]["function"]
            result = action_func(model_name, self)
            
            # Show result if provided
            if result and isinstance(result, str):
                messagebox.showinfo("Action Result", result)
                
            self.log(f"[Model Panel] Executed action {action_id} on model {model_name}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log(f"[Model Panel] Error executing action {action_id}: {e}")

    def get_model_config(self, model_name):
        """
        Get model configuration including any plugin customizations
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model configuration
        """
        # Start with default configuration
        config = self.model_manager.get_model_config(model_name)
        
        # Apply plugin configurations if any
        if hasattr(self, "plugin_model_configs"):
            # Find specific configurations for this model
            for config_id, config_func in self.plugin_model_configs.items():
                try:
                    # Check if this config applies to this model
                    model_part = config_id.split(".", 1)[1]  # Get part after plugin ID
                    if model_part == "*" or model_part == model_name:
                        # Apply configuration
                        plugin_config = config_func(model_name, config.copy())
                        if plugin_config and isinstance(plugin_config, dict):
                            # Update configuration
                            config.update(plugin_config)
                            
                except Exception as e:
                    self.log(f"[Error] Model config {config_id} failed: {e}")
                    
        return config

    def start_selected_model(self):
        """Start the selected model"""
        selection = self.model_tree.selection()
        if not selection:
            return
                
        # Get model name
        item = selection[0]
        values = self.model_tree.item(item, "values")
        model_name = values[0]
        
        # Check if already running
        if self.model_manager.model_process and self.model_manager.model_process.poll() is None:
            result = messagebox.askyesno(
                "Model Already Running", 
                f"Another model is already running. Stop it and start '{model_name}' instead?",
                icon=messagebox.WARNING
            )
                
            if result:
                self.model_manager.stop_model()
            else:
                return
                
        # Update progress bar and status
        self.progress_mode.set("indeterminate")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start()
        self.status_var.set(f"Starting {model_name}...")
        
        # Event callback for model events
        def on_model_event(event_type, data):
            if event_type == "started":
                self.frame.after(0, lambda: self._update_model_status(model_name, MODEL_STATUS["RUNNING"]))
                self.frame.after(0, lambda: self._reset_progress_bar())
                self.frame.after(0, lambda: self.status_var.set(f"{model_name} is running"))
            elif event_type == "stopped":
                self.frame.after(0, lambda: self._update_model_status(model_name, MODEL_STATUS["INSTALLED"]))
                self.frame.after(0, lambda: self._reset_progress_bar())
                self.frame.after(0, lambda: self.status_var.set(f"{model_name} stopped"))
            elif event_type == "error":
                self.frame.after(0, lambda: self._update_model_status(model_name, MODEL_STATUS["ERROR"]))
                self.frame.after(0, lambda: self._reset_progress_bar())
                self.frame.after(0, lambda: self.status_var.set(f"Error: {data}"))
                
        # Get model configuration with plugin customizations
        model_config = self.get_model_config(model_name)
        
        # Start the model with config
        success = self.model_manager.start_model(model_name, on_model_event, model_config)
        
        if success:
            # Update tree item
            self.model_tree.item(
                item, 
                values=(model_name, values[1], MODEL_STATUS["LOADING"], values[3])
            )
                
            # Disable buttons during loading
            self.install_button.config(state=tk.DISABLED)
            self.uninstall_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
                
            # Select this model for use
            self.select_current_model()
        else:
            # Reset progress bar and status
            self._reset_progress_bar()
            self.status_var.set(f"Failed to start {model_name}")

    def setup_sandbox_tab(self):
        """Setup the plugin sandbox tab"""
        # Create sandbox controls
        controls_frame = ttk.Frame(self.sandbox_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            controls_frame,
            text="Plugin Sandbox Environment",
            font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W)
        
        ttk.Label(
            controls_frame,
            text="Test plugins in an isolated environment before activating them in the main application.",
            wraplength=600
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Plugin selector
        selector_frame = ttk.Frame(controls_frame)
        selector_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(selector_frame, text="Select Plugin:").pack(side=tk.LEFT)
        
        self.sandbox_plugin_var = tk.StringVar()
        self.sandbox_plugin_combobox = ttk.Combobox(
            selector_frame,
            textvariable=self.sandbox_plugin_var,
            state="readonly",
            width=30
        )
        self.sandbox_plugin_combobox.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            selector_frame,
            text="Load in Sandbox",
            command=self.load_plugin_in_sandbox
        ).pack(side=tk.LEFT, padx=5)
        
        # Sandbox options
        options_frame = ttk.LabelFrame(controls_frame, text="Sandbox Options")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Create a grid layout
        for i in range(3):
            options_frame.columnconfigure(i, weight=1)
        
        # File system access
        self.fs_access_var = tk.StringVar(value="read-only")
        ttk.Label(options_frame, text="File System Access:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(
            options_frame,
            text="None",
            variable=self.fs_access_var,
            value="none"
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(
            options_frame,
            text="Read-only",
            variable=self.fs_access_var,
            value="read-only"
        ).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Network access
        self.network_access_var = tk.BooleanVar(value=False)
        ttk.Label(options_frame, text="Network Access:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Checkbutton(
            options_frame,
            text="Allow",
            variable=self.network_access_var
        ).grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Memory limit
        ttk.Label(options_frame, text="Memory Limit:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.memory_limit_var = tk.StringVar(value="256 MB")
        memory_combobox = ttk.Combobox(
            options_frame,
            textvariable=self.memory_limit_var,
            values=["128 MB", "256 MB", "512 MB", "1 GB"],
            state="readonly",
            width=10
        )
        memory_combobox.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Sandbox output
        output_frame = ttk.LabelFrame(self.sandbox_frame, text="Sandbox Output")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create output text with syntax highlighting
        self.sandbox_output = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.sandbox_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add tag configurations for syntax highlighting
        self.sandbox_output.tag_config("success", foreground="green")
        self.sandbox_output.tag_config("error", foreground="red")
        self.sandbox_output.tag_config("warning", foreground="orange")
        self.sandbox_output.tag_config("info", foreground="blue")
        
        # Control buttons
        control_buttons = ttk.Frame(self.sandbox_frame)
        control_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            control_buttons,
            text="Run Tests",
            command=self.run_sandbox_tests
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_buttons,
            text="View Permissions",
            command=self.view_plugin_permissions
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_buttons,
            text="Clear Output",
            command=lambda: self.sandbox_output.delete(1.0, tk.END)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_buttons,
            text="Approve and Install",
            command=self.approve_sandbox_plugin,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        # Update sandbox plugin list
        self.update_sandbox_plugin_list()

    def update_sandbox_plugin_list(self):
        """Update the list of plugins available for sandboxing"""
        # Get all plugins
        plugin_info = self.plugin_manager.get_all_plugins()
        
        # Filter to unloaded or error plugins
        sandbox_plugins = [
            name for name, info in plugin_info.items() 
            if info.get("status") in ("Not Loaded", "Error")
        ]
        
        # Update combobox
        self.sandbox_plugin_combobox["values"] = sorted(sandbox_plugins) if sandbox_plugins else ["No plugins available"]
        if sandbox_plugins:
            self.sandbox_plugin_combobox.current(0)

    def load_plugin_in_sandbox(self):
        """Load selected plugin in the sandbox environment"""
        plugin_name = self.sandbox_plugin_var.get()
        
        if not plugin_name or plugin_name == "No plugins available":
            return
            
        # Clear output
        self.sandbox_output.delete(1.0, tk.END)
        
        # Show loading message
        self.sandbox_output.insert(tk.END, f"Loading plugin in sandbox: {plugin_name}\n", "info")
        self.sandbox_output.insert(tk.END, f"Sandbox configuration:\n")
        self.sandbox_output.insert(tk.END, f"- File system: {self.fs_access_var.get()}\n")
        self.sandbox_output.insert(tk.END, f"- Network access: {'Allowed' if self.network_access_var.get() else 'Blocked'}\n")
        self.sandbox_output.insert(tk.END, f"- Memory limit: {self.memory_limit_var.get()}\n\n")
        
        # Simulate sandbox loading
        self.sandbox_output.insert(tk.END, "Preparing sandbox environment...\n")
        self.frame.update_idletasks()
        
        # Start a background thread for sandbox operations
        threading.Thread(
            target=self._sandbox_load_thread,
            args=(plugin_name,),
            daemon=True
        ).start()
        
    def _sandbox_load_thread(self, plugin_name):
        """
        Load a plugin in the sandbox environment
        
        Args:
            plugin_name: Name of the plugin to load
        """
        try:
            # Get plugin path
            plugin_path = os.path.join(self.plugin_manager.plugin_dir, plugin_name)
            
            # Check plugin structure and files
            self._append_sandbox_output(f"Checking plugin structure...\n")
            
            # Check for __init__.py
            init_path = os.path.join(plugin_path, "__init__.py")
            if os.path.exists(init_path):
                self._append_sandbox_output(f"Found __init__.py file.\n", "success")
            else:
                self._append_sandbox_output(f"ERROR: Missing __init__.py file!\n", "error")
                return
                
            # Check for manifest.json
            manifest_path = os.path.join(plugin_path, "manifest.json")
            if os.path.exists(manifest_path):
                self._append_sandbox_output(f"Found manifest.json file.\n", "success")
                
                # Parse manifest
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        
                    # Check required fields
                    required_fields = ["name", "version", "description", "author"]
                    missing_fields = [field for field in required_fields if field not in manifest]
                    
                    if missing_fields:
                        self._append_sandbox_output(f"WARNING: Manifest missing fields: {', '.join(missing_fields)}\n", "warning")
                    else:
                        self._append_sandbox_output(f"Manifest validation successful.\n", "success")
                        
                    # Check dependencies
                    if "dependencies" in manifest and manifest["dependencies"]:
                        deps = manifest["dependencies"]
                        self._append_sandbox_output(f"Plugin has dependencies: {', '.join(deps)}\n", "info")
                        
                        # Check if dependencies are installed
                        for dep in deps:
                            if self.plugin_manager.is_plugin_loaded(dep):
                                self._append_sandbox_output(f"Dependency satisfied: {dep}\n", "success")
                            else:
                                self._append_sandbox_output(f"Missing dependency: {dep}\n", "warning")
                                
                except Exception as e:
                    self._append_sandbox_output(f"ERROR: Failed to parse manifest: {e}\n", "error")
            else:
                self._append_sandbox_output(f"WARNING: No manifest.json file found.\n", "warning")
                
            # Check for any potentially unsafe imports
            self._append_sandbox_output(f"Scanning for potentially unsafe imports...\n")
            
            unsafe_imports = self._scan_unsafe_imports(plugin_path)
            
            if unsafe_imports:
                self._append_sandbox_output(f"WARNING: Found potentially unsafe imports:\n", "warning")
                for imp in unsafe_imports:
                    self._append_sandbox_output(f"- {imp}\n", "warning")
            else:
                self._append_sandbox_output(f"No unsafe imports detected.\n", "success")
                
            # Static analysis complete
            self._append_sandbox_output(f"\nStatic analysis complete. The plugin appears to be structurally valid.\n", "info")
            self._append_sandbox_output(f"Use 'Run Tests' to perform dynamic testing in the sandbox.\n", "info")
            
        except Exception as e:
            self._append_sandbox_output(f"ERROR: Sandbox analysis failed: {e}\n", "error")
            
    def _scan_unsafe_imports(self, plugin_path):
        """
        Scan plugin files for potentially unsafe imports
        
        Args:
            plugin_path: Path to the plugin directory
            
        Returns:
            List of potentially unsafe imports
        """
        unsafe_imports = []
        unsafe_modules = [
            "os.system", "subprocess", "socket", "multiprocessing",
            "ctypes", "winreg", "msvcrt", "_winapi"
        ]
        
        # Walk through all Python files
        for root, _, files in os.walk(plugin_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Simple import scanning
                        for mod in unsafe_modules:
                            if f"import {mod}" in content or f"from {mod}" in content:
                                unsafe_imports.append(f"{os.path.relpath(file_path, plugin_path)}: {mod}")
                            
                    except Exception:
                        continue
                        
        return unsafe_imports

    def _append_sandbox_output(self, text, tag=None):
        """
        Append text to sandbox output with optional tag
        
        Args:
            text: Text to append
            tag: Optional tag for formatting
        """
        # Use after() to safely update from another thread
        self.frame.after(0, lambda: self._do_append_sandbox_output(text, tag))
        
        # Small sleep to allow UI updates
        time.sleep(0.01)
        
    def _do_append_sandbox_output(self, text, tag=None):
        """
        Actual implementation of append that runs on the main thread
        
        Args:
            text: Text to append
            tag: Optional tag for formatting
        """
        # Insert at end
        self.sandbox_output.insert(tk.END, text, tag)
        
        # Auto-scroll
        self.sandbox_output.see(tk.END)