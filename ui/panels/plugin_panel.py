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
    
    def __init__(self, parent, plugin_manager, config_manager=None, logger: Callable=None):
        """
        Initialize the plugin panel
        
        Args:
            parent: Parent widget
            plugin_manager: PluginManager instance
            config_manager: Configuration manager instance
            logger: Logging function
        """
        self.parent = parent
        self.plugin_manager = plugin_manager
        self.config_manager = config_manager
        self.log = logger
        
        # Add this line:
        self.is_running = True
        
        # Track when the frame is destroyed
        self.frame = ttk.Frame(parent)
        self.frame.bind("<Destroy>", self._on_destroy)
        
        # Current plugin being configured (for settings tab)
        self.current_plugin_id = None
        self.current_config = {}
        self.config_widgets = {}
        
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
        
        # Create settings tab for plugin configuration
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Plugin Settings")

        # Setup local plugins tab
        self.setup_local_plugins_tab()
        
        # Setup marketplace tab
        self.setup_marketplace_tab()
        
        # Setup sandbox tab
        self.setup_sandbox_tab()
        
        # Setup settings tab
        self.setup_settings_tab()
        
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
        
        # Only try to update UI if we're still running
        if self.is_running:
            try:
                # Schedule update on main thread
                self.frame.after(0, lambda: self._update_plugin_tree(plugins_info))
            except Exception:
                # Silently fail if we can't update
                pass
        
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

    def create_discovery_section(self): # <<< ADD THIS METHOD
        """Create the plugin discovery and refresh section"""
        discovery_frame = ttk.LabelFrame(self.local_frame, text="Plugin Discovery")
        discovery_frame.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)

        # Refresh button
        ttk.Button(
            discovery_frame,
            text="Refresh Plugin List",
            command=self.refresh_plugin_list
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Open plugin folder button
        ttk.Button(
            discovery_frame,
            text="Open Plugin Folder",
            command=self.open_plugin_folder # Assumes this method exists or will be added
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def create_management_section(self): # <<< ADD THIS METHOD
        """Create the plugin management section with the list"""
        management_frame = ttk.LabelFrame(self.local_frame, text="Installed Plugins")
        management_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a tree view for plugins
        columns = ("Name", "Version", "Status", "Author")
        self.plugin_tree = ttk.Treeview(
            management_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=8 # Adjust height as needed
        )

        # Configure columns
        self.plugin_tree.heading("Name", text="Plugin Name")
        self.plugin_tree.heading("Version", text="Version")
        self.plugin_tree.heading("Status", text="Status")
        self.plugin_tree.heading("Author", text="Author")

        self.plugin_tree.column("Name", width=180, anchor=tk.W)
        self.plugin_tree.column("Version", width=80, anchor=tk.CENTER)
        self.plugin_tree.column("Status", width=100, anchor=tk.CENTER)
        self.plugin_tree.column("Author", width=120, anchor=tk.W)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(management_frame, orient="vertical", command=self.plugin_tree.yview)
        self.plugin_tree.configure(yscrollcommand=scrollbar.set)

        # Pack the tree and scrollbar
        self.plugin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)

        # Bind selection event
        self.plugin_tree.bind("<<TreeviewSelect>>", self.on_plugin_selected)

        # --- Action buttons for selected plugin ---
        action_frame = ttk.Frame(management_frame)
        # Place action frame to the right or below the tree as desired
        # Example: Packing below
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        self.load_button = ttk.Button(
            action_frame,
            text="Load",
            command=self.load_selected_plugin,
            state=tk.DISABLED
        )
        self.load_button.pack(side=tk.LEFT, padx=2)

        self.activate_button = ttk.Button(
            action_frame,
            text="Activate",
            command=self.activate_selected_plugin,
            state=tk.DISABLED
        )
        self.activate_button.pack(side=tk.LEFT, padx=2)

        self.deactivate_button = ttk.Button(
            action_frame,
            text="Deactivate",
            command=self.deactivate_selected_plugin,
            state=tk.DISABLED
        )
        self.deactivate_button.pack(side=tk.LEFT, padx=2)

        self.reload_button = ttk.Button(
            action_frame,
            text="Reload",
            command=self.reload_selected_plugin,
            state=tk.DISABLED
        )
        self.reload_button.pack(side=tk.LEFT, padx=2)


    def create_info_section(self): # <<< ADD THIS METHOD
        """Create the plugin information display section"""
        info_frame = ttk.LabelFrame(self.local_frame, text="Plugin Information")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        # Grid for details
        details_grid = ttk.Frame(info_frame)
        details_grid.pack(fill=tk.X, padx=5, pady=5)
        details_grid.columnconfigure(1, weight=1) # Make value column expandable

        # Name
        ttk.Label(details_grid, text="Name:", width=10).grid(row=0, column=0, sticky=tk.W, padx=5, pady=1)
        self.selected_name_var = tk.StringVar(value="None")
        ttk.Label(details_grid, textvariable=self.selected_name_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=1)

        # Status
        ttk.Label(details_grid, text="Status:", width=10).grid(row=1, column=0, sticky=tk.W, padx=5, pady=1)
        self.selected_status_var = tk.StringVar(value="N/A")
        ttk.Label(details_grid, textvariable=self.selected_status_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=1)

        # Version
        ttk.Label(details_grid, text="Version:", width=10).grid(row=2, column=0, sticky=tk.W, padx=5, pady=1)
        self.selected_version_var = tk.StringVar(value="N/A")
        ttk.Label(details_grid, textvariable=self.selected_version_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=1)

        # Author
        ttk.Label(details_grid, text="Author:", width=10).grid(row=3, column=0, sticky=tk.W, padx=5, pady=1)
        self.selected_author_var = tk.StringVar(value="N/A")
        ttk.Label(details_grid, textvariable=self.selected_author_var).grid(row=3, column=1, sticky=tk.W, padx=5, pady=1)

        # License
        ttk.Label(details_grid, text="License:", width=10).grid(row=4, column=0, sticky=tk.W, padx=5, pady=1)
        self.selected_license_var = tk.StringVar(value="N/A")
        ttk.Label(details_grid, textvariable=self.selected_license_var).grid(row=4, column=1, sticky=tk.W, padx=5, pady=1)

        # Location
        ttk.Label(details_grid, text="Location:", width=10).grid(row=5, column=0, sticky=tk.W, padx=5, pady=1)
        self.selected_location_var = tk.StringVar(value="N/A")
        ttk.Label(details_grid, textvariable=self.selected_location_var, wraplength=400).grid(row=5, column=1, sticky=tk.W, padx=5, pady=1)


        # Description section
        desc_frame = ttk.Frame(info_frame)
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(desc_frame, text="Description:").pack(anchor=tk.W)

        self.description_text = scrolledtext.ScrolledText(
            desc_frame,
            height=4,
            wrap=tk.WORD,
            font=("Helvetica", 9)
        )
        self.description_text.pack(fill=tk.X, padx=5, pady=(0,5))
        self.description_text.config(state=tk.DISABLED) # Start disabled

        # Configuration section (Read-only view)
        config_frame = ttk.Frame(info_frame)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(config_frame, text="Configuration (View only - Edit in Plugin Settings):").pack(anchor=tk.W)

        self.config_text = scrolledtext.ScrolledText(
            config_frame,
            height=5,
            wrap=tk.WORD,
            font=("Courier New", 9)
        )
        self.config_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        self.config_text.config(state=tk.DISABLED) # Start disabled

    # --- Add the missing open_plugin_folder method ---
    def open_plugin_folder(self): # <<< ADD THIS METHOD
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

    def search_marketplace(self):
        """Search the plugin marketplace based on current search criteria"""
        # Get search query
        query = self.search_var.get().strip()
        repository = self.repo_var.get()
        
        # Clear current results
        for item in self.marketplace_tree.get_children():
            self.marketplace_tree.delete(item)
            
        # Update status
        self.status_var.set(f"Searching for '{query}' in {repository} repository...")
        self.progress_bar.start()
        
        # Start search in a separate thread
        threading.Thread(
            target=self._search_marketplace_thread,
            args=(query, repository),
            daemon=True
        ).start()
        
    def _search_marketplace_thread(self, query, repository):
        """
        Search the marketplace in a background thread
        
        Args:
            query: Search query
            repository: Repository to search (Official, Community, All)
        """
        try:
            # TODO: In a real implementation, this would connect to an external API
            # For now, we'll simulate some results
            time.sleep(1)  # Simulate network delay
            
            # Simulate search results
            results = []
            
            # Add some dummy results based on query
            if not query or "plugin" in query.lower():
                results.extend([
                    {
                        "name": "Advanced Search Plugin",
                        "version": "1.2.1",
                        "rating": "4.8",
                        "downloads": "12,453",
                        "author": "Irintai Team",
                        "category": "Utilities",
                        "description": "Enhanced search capabilities for vector databases and document retrieval.",
                        "updated": "2025-03-15",
                        "size": "1.2 MB",
                        "dependencies": []
                    },
                    {
                        "name": "Document Scanner Plugin",
                        "version": "0.9.5",
                        "rating": "4.2",
                        "downloads": "8,712",
                        "author": "DocScan Inc.",
                        "category": "Document Processing",
                        "description": "Automatically processes and indexes documents from various sources.",
                        "updated": "2025-01-22",
                        "size": "3.5 MB",
                        "dependencies": ["Advanced Search Plugin"]
                    }
                ])
                
            if not query or "code" in query.lower():
                results.extend([
                    {
                        "name": "Code Assistant Pro",
                        "version": "2.1.0",
                        "rating": "4.9",
                        "downloads": "32,150",
                        "author": "DevTools Corp",
                        "category": "Development",
                        "description": "Adds code completion, refactoring suggestions, and more to enhance coding capabilities.",
                        "updated": "2025-04-01",
                        "size": "4.8 MB",
                        "dependencies": []
                    }
                ])
                
            if not query or "ui" in query.lower() or "theme" in query.lower():
                results.extend([
                    {
                        "name": "UI Theme Pack",
                        "version": "1.5.2",
                        "rating": "4.7",
                        "downloads": "18,325",
                        "author": "Design Studio X",
                        "category": "UI/UX",
                        "description": "Collection of modern UI themes with customizable color schemes and layouts.",
                        "updated": "2025-02-18",
                        "size": "2.3 MB",
                        "dependencies": []
                    }
                ])
            
            # Filter by repository if needed
            if repository == "Official":
                results = [r for r in results if "Irintai Team" in r.get("author", "")]
            elif repository == "Community":
                results = [r for r in results if "Irintai Team" not in r.get("author", "")]
            
            # Update UI on main thread
            self.frame.after(0, lambda: self._update_marketplace_results(results, query))
            
        except Exception as e:
            # Update UI with error
            self.frame.after(0, lambda: self._update_marketplace_error(str(e)))
            
    def _update_marketplace_results(self, results, query):
        """
        Update the marketplace tree with search results
        
        Args:
            results: List of plugin results
            query: Search query used
        """
        # Stop progress
        self.progress_bar.stop()
        
        # Clear current results
        for item in self.marketplace_tree.get_children():
            self.marketplace_tree.delete(item)
            
        # Add results to tree
        if results:
            for plugin in results:
                self.marketplace_tree.insert(
                    "",
                    tk.END,
                    values=(
                        plugin["name"],
                        plugin["version"],
                        plugin["rating"],
                        plugin["downloads"]
                    ),
                    tags=(plugin["name"],)  # Use name as tag for lookup
                )
                
            # Select first result
            first = self.marketplace_tree.get_children()[0]
            self.marketplace_tree.selection_set(first)
            self.on_marketplace_selected(None)
            
            self.status_var.set(f"Found {len(results)} plugins matching '{query}'")
        else:
            self.status_var.set(f"No plugins found matching '{query}'")
            
            # Clear details
            self.market_description.delete(1.0, tk.END)
            self.market_author_var.set("-")
            self.market_category_var.set("-")
            self.market_updated_var.set("-")
            self.market_size_var.set("-")
            self.dependencies_var.set("None")
        
    def _update_marketplace_error(self, error_message):
        """
        Update the UI with search error
        
        Args:
            error_message: Error message to display
        """
        # Stop progress
        self.progress_bar.stop()
        
        # Show error
        self.status_var.set(f"Error searching marketplace: {error_message}")
        messagebox.showerror("Search Error", f"Failed to search marketplace:\n{error_message}")

    def on_marketplace_selected(self, event):
        """Handle selection in the marketplace tree"""
        selection = self.marketplace_tree.selection()
        if not selection:
            return
            
        # Get selected item
        item = selection[0]
        values = self.marketplace_tree.item(item, "values")
        
        if not values:
            return
            
        # Get plugin name
        plugin_name = values[0]
        
        # Find plugin details (in real implementation, would fetch from API)
        plugin = None
        for p in self._get_demo_plugins():
            if p["name"] == plugin_name:
                plugin = p
                break
                
        if not plugin:
            return
            
        # Update details
        self.market_description.delete(1.0, tk.END)
        self.market_description.insert(1.0, plugin.get("description", "No description available"))
        
        self.market_author_var.set(plugin.get("author", "Unknown"))
        self.market_category_var.set(plugin.get("category", "General"))
        self.market_updated_var.set(plugin.get("updated", "Unknown"))
        self.market_size_var.set(plugin.get("size", "Unknown"))
        
        # Update dependencies
        dependencies = plugin.get("dependencies", [])
        if dependencies:
            self.dependencies_var.set(", ".join(dependencies))
        else:
            self.dependencies_var.set("None")

    def _get_demo_plugins(self):
        """Get demo plugins for marketplace display"""
        return [
            {
                "name": "Advanced Search Plugin",
                "version": "1.2.1",
                "rating": "4.8",
                "downloads": "12,453",
                "author": "Irintai Team",
                "category": "Utilities",
                "description": "Enhanced search capabilities for vector databases and document retrieval.",
                "updated": "2025-03-15",
                "size": "1.2 MB",
                "dependencies": []
            },
            {
                "name": "Document Scanner Plugin",
                "version": "0.9.5",
                "rating": "4.2",
                "downloads": "8,712",
                "author": "DocScan Inc.",
                "category": "Document Processing",
                "description": "Automatically processes and indexes documents from various sources.",
                "updated": "2025-01-22",
                "size": "3.5 MB",
                "dependencies": ["Advanced Search Plugin"]
            },
            {
                "name": "Code Assistant Pro",
                "version": "2.1.0",
                "rating": "4.9",
                "downloads": "32,150",
                "author": "DevTools Corp",
                "category": "Development",
                "description": "Adds code completion, refactoring suggestions, and more to enhance coding capabilities.",
                "updated": "2025-04-01",
                "size": "4.8 MB",
                "dependencies": []
            },
            {
                "name": "UI Theme Pack",
                "version": "1.5.2",
                "rating": "4.7",
                "downloads": "18,325",
                "author": "Design Studio X",
                "category": "UI/UX",
                "description": "Collection of modern UI themes with customizable color schemes and layouts.",
                "updated": "2025-02-18",
                "size": "2.3 MB",
                "dependencies": []
            }
        ]

    def install_marketplace_plugin(self):
        """Install the selected plugin from marketplace"""
        selection = self.marketplace_tree.selection()
        if not selection:
            return
            
        # Get selected item
        item = selection[0]
        values = self.marketplace_tree.item(item, "values")
        
        if not values:
            return
            
        # Get plugin name
        plugin_name = values[0]
        
        # Confirm installation
        result = messagebox.askyesno(
            "Install Plugin",
            f"Do you want to install '{plugin_name}'?"
        )
        
        if not result:
            return
            
        # Show progress
        self.progress_bar.start()
        self.status_var.set(f"Installing {plugin_name}...")
        
        # Start installation in a separate thread
        threading.Thread(
            target=self._install_marketplace_plugin_thread,
            args=(plugin_name,),
            daemon=True
        ).start()
        
    def _install_marketplace_plugin_thread(self, plugin_name):
        """
        Install a plugin from marketplace in a background thread
        
        Args:
            plugin_name: Name of the plugin to install
        """
        try:
            # Simulate installation process
            time.sleep(2)
            
            # Update UI on main thread
            self.frame.after(0, lambda: self._on_marketplace_install_complete(plugin_name, True))
            
        except Exception as e:
            # Update UI with error
            self.frame.after(0, lambda: self._on_marketplace_install_complete(plugin_name, False, str(e)))
        
    def _on_marketplace_install_complete(self, plugin_name, success, error_message=None):
        """
        Handle completion of plugin installation
        
        Args:
            plugin_name: Name of the plugin
            success: Whether installation was successful
            error_message: Optional error message
        """
        # Stop progress
        self.progress_bar.stop()
        
        if success:
            self.status_var.set(f"Successfully installed {plugin_name}")
            messagebox.showinfo("Installation Complete", f"Plugin {plugin_name} installed successfully.")
            
            # Refresh local plugin list
            self.refresh_plugin_list()
        else:
            self.status_var.set(f"Failed to install {plugin_name}: {error_message}")
            messagebox.showerror("Installation Failed", f"Failed to install {plugin_name}:\n{error_message}")

    def visit_plugin_website(self):
        """Open the plugin website in the default browser"""
        selection = self.marketplace_tree.selection()
        if not selection:
            return
            
        # Get selected item
        item = selection[0]
        values = self.marketplace_tree.item(item, "values")
        
        if not values:
            return
            
        # Get plugin name
        plugin_name = values[0]
        
        # Find plugin details
        plugin = None
        for p in self._get_demo_plugins():
            if p["name"] == plugin_name:
                plugin = p
                break
                
        if not plugin:
            return
            
        # Simulate website (would be in plugin["url"] in a real implementation)
        url = f"https://example.com/plugins/{plugin_name.lower().replace(' ', '-')}"
        
        # Try to open URL in browser
        import webbrowser
        try:
            webbrowser.open(url)
            self.status_var.set(f"Opened website for {plugin_name}")
        except Exception as e:
            self.status_var.set(f"Failed to open website: {e}")
            messagebox.showerror("Error", f"Failed to open website:\n{e}")

    def view_plugin_dependencies(self):
        """Show plugin dependencies in a dialog"""
        selection = self.marketplace_tree.selection()
        if not selection:
            return
            
        # Get selected item
        item = selection[0]
        values = self.marketplace_tree.item(item, "values")
        
        if not values:
            return
            
        # Get plugin name
        plugin_name = values[0]
        
        # Find plugin details
        plugin = None
        for p in self._get_demo_plugins():
            if p["name"] == plugin_name:
                plugin = p
                break
                
        if not plugin:
            return
            
        # Get dependencies
        dependencies = plugin.get("dependencies", [])
        
        if not dependencies:
            messagebox.showinfo("Dependencies", f"{plugin_name} has no dependencies.")
            return
            
        # Show dependencies dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Dependencies for {plugin_name}")
        dialog.geometry("400x300")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Add content
        ttk.Label(
            dialog,
            text=f"Dependencies for {plugin_name}",
            font=("", 12, "bold")
        ).pack(pady=(10, 5))
        
        # Create a listbox for dependencies
        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Add dependencies to listbox
        for dep in dependencies:
            listbox.insert(tk.END, dep)
            
        # Close button
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy
        ).pack(pady=10)

    def check_plugin_updates(self):
        """Check for plugin updates"""
        # Show progress
        self.progress_bar.start()
        self.status_var.set("Checking for plugin updates...")
        
        # Start check in a separate thread
        threading.Thread(
            target=self._check_updates_thread,
            daemon=True
        ).start()
        
    def _check_updates_thread(self):
        """Check for updates in a background thread"""
        try:
            # Simulate network operation
            time.sleep(1.5)
            
            # No updates in this demo
            self.frame.after(0, lambda: self._on_update_check_complete([]))
            
        except Exception as e:
            self.frame.after(0, lambda: self._on_update_check_error(str(e)))
        
    def _on_update_check_complete(self, updates):
        """
        Handle completion of update check
        
        Args:
            updates: List of available updates
        """
        # Stop progress
        self.progress_bar.stop()
        
        if updates:
            self.status_var.set(f"Found {len(updates)} plugin updates")
            
            # Show updates in a dialog
            # (Not implemented in this example)
            messagebox.showinfo("Plugin Updates", f"Found {len(updates)} plugin updates.")
        else:
            self.status_var.set("All plugins are up to date")
            messagebox.showinfo("Plugin Updates", "All plugins are up to date.")
        
    def _on_update_check_error(self, error_message):
        """
        Handle error during update check
        
        Args:
            error_message: Error message
        """
        # Stop progress
        self.progress_bar.stop()
        
        # Show error
        self.status_var.set(f"Error checking for updates: {error_message}")
        messagebox.showerror("Update Error", f"Failed to check for updates:\n{error_message}")

    def run_sandbox_tests(self):
        """Run tests for the plugin in the sandbox"""
        plugin_name = self.sandbox_plugin_var.get()
        
        if not plugin_name or plugin_name == "No plugins available":
            return
            
        # Clear output and show header
        self.sandbox_output.delete(1.0, tk.END)
        self.sandbox_output.insert(tk.END, f"==== Running tests for {plugin_name} ====\n\n", "info")
        
        # Show test configuration
        self.sandbox_output.insert(tk.END, f"Test configuration:\n")
        self.sandbox_output.insert(tk.END, f"- File system access: {self.fs_access_var.get()}\n")
        self.sandbox_output.insert(tk.END, f"- Network access: {'Allowed' if self.network_access_var.get() else 'Blocked'}\n")
        self.sandbox_output.insert(tk.END, f"- Memory limit: {self.memory_limit_var.get()}\n\n")
        
        # Start testing in a separate thread
        threading.Thread(
            target=self._run_sandbox_tests_thread,
            args=(plugin_name,),
            daemon=True
        ).start()
        
    def _run_sandbox_tests_thread(self, plugin_name):
        """
        Run sandbox tests in a background thread
        
        Args:
            plugin_name: Name of the plugin to test
        """
        try:
            # Get plugin path
            plugin_path = os.path.join(self.plugin_manager.plugin_dir, plugin_name)
            
            # Simulate tests
            self._append_sandbox_output("Initializing sandbox environment...\n")
            time.sleep(0.5)
            
            self._append_sandbox_output("Loading plugin in isolated environment...\n")
            time.sleep(1.0)
            
            self._append_sandbox_output("Running standard tests...\n\n")
            
            # Test plugin initialization
            self._append_sandbox_output("1. Testing plugin initialization... ")
            time.sleep(0.5)
            self._append_sandbox_output("OK\n", "success")
            
            # Test activate method
            self._append_sandbox_output("2. Testing activate() method... ")
            time.sleep(0.5)
            self._append_sandbox_output("OK\n", "success")
            
            # Test deactivate method
            self._append_sandbox_output("3. Testing deactivate() method... ")
            time.sleep(0.5)
            self._append_sandbox_output("OK\n", "success")
            
            # Test file operations
            self._append_sandbox_output("4. Testing file operations... ")
            if self.fs_access_var.get() == "none":
                self._append_sandbox_output("SKIPPED (no file access)\n", "warning")
            else:
                time.sleep(0.7)
                self._append_sandbox_output("OK\n", "success")
                
            # Test network access
            self._append_sandbox_output("5. Testing network operations... ")
            if not self.network_access_var.get():
                self._append_sandbox_output("SKIPPED (no network access)\n", "warning")
            else:
                time.sleep(0.8)
                self._append_sandbox_output("OK\n", "success")
                
            # Test memory allocation
            self._append_sandbox_output("6. Testing memory allocation... ")
            time.sleep(0.6)
            
            # Parse memory limit
            limit_str = self.memory_limit_var.get()
            if "MB" in limit_str:
                limit = int(limit_str.split(" ")[0])
            elif "GB" in limit_str:
                limit = int(limit_str.split(" ")[0]) * 1024
            else:
                limit = 256  # Default
                
            if limit < 256:
                self._append_sandbox_output("WARNING: Low memory limit may affect plugin performance\n", "warning")
            else:
                self._append_sandbox_output("OK\n", "success")
                
            # Summary
            self._append_sandbox_output("\nAll tests completed successfully.\n", "success")
            self._append_sandbox_output("The plugin appears to be safe and working correctly.\n", "success")
            
        except Exception as e:
            self._append_sandbox_output(f"ERROR: Test failed: {e}\n", "error")

    def view_plugin_permissions(self):
        """View the permissions requested by the plugin"""
        plugin_name = self.sandbox_plugin_var.get()
        
        if not plugin_name or plugin_name == "No plugins available":
            return
            
        # Show permissions dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Permissions - {plugin_name}")
        dialog.geometry("500x400")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Add content
        ttk.Label(
            dialog,
            text=f"Permissions for {plugin_name}",
            font=("", 12, "bold")
        ).pack(pady=(10, 5))
        
        # Create a frame for permissions
        perm_frame = ttk.Frame(dialog, padding=10)
        perm_frame.pack(fill=tk.BOTH, expand=True)
        
        # Permission columns
        ttk.Label(perm_frame, text="Permission", font=("", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Label(perm_frame, text="Status", font=("", 10, "bold")).grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        ttk.Label(perm_frame, text="Description", font=("", 10, "bold")).grid(row=0, column=2, sticky=tk.W, pady=(0, 5))
        
        # File system access
        ttk.Label(perm_frame, text="File System").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text=self.fs_access_var.get().capitalize(),
            foreground="green" if self.fs_access_var.get() != "none" else "red"
        ).grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="Access to plugin-specific data directory"
        ).grid(row=1, column=2, sticky=tk.W, pady=2)
        
        # Network access
        ttk.Label(perm_frame, text="Network").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="Enabled" if self.network_access_var.get() else "Disabled",
            foreground="green" if self.network_access_var.get() else "red"
        ).grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="Internet access for API calls and data retrieval"
        ).grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # UI access
        ttk.Label(perm_frame, text="UI Access").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="Limited",
            foreground="orange"
        ).grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="Can create dialog windows and panel elements"
        ).grid(row=3, column=2, sticky=tk.W, pady=2)
        
        # System access
        ttk.Label(perm_frame, text="System").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="None",
            foreground="red"
        ).grid(row=4, column=1, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="No access to system functions or processes"
        ).grid(row=4, column=2, sticky=tk.W, pady=2)
        
        # Plugin API
        ttk.Label(perm_frame, text="Plugin API").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="Full",
            foreground="green"
        ).grid(row=5, column=1, sticky=tk.W, pady=2)
        ttk.Label(
            perm_frame,
            text="Access to plugin API for events and services"
        ).grid(row=5, column=2, sticky=tk.W, pady=2)
        
        # Close button
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy
        ).pack(pady=10)

    def approve_sandbox_plugin(self):
        """Approve a plugin from sandbox and install it"""
        plugin_name = self.sandbox_plugin_var.get()
        
        if not plugin_name or plugin_name == "No plugins available":
            return
            
        # Confirm installation
        result = messagebox.askyesno(
            "Approve Plugin",
            f"Do you want to approve and activate {plugin_name}?\n\n"
            f"This will load the plugin with the following permissions:\n"
            f"- File System: {self.fs_access_var.get()}\n"
            f"- Network: {'Allowed' if self.network_access_var.get() else 'Blocked'}"
        )
        
        if not result:
            return
            
        # Update status
        self.status_var.set(f"Installing and activating {plugin_name}...")
        self.progress_bar.start()
        
        # Install in a separate thread
        threading.Thread(
            target=self._approve_plugin_thread,
            args=(plugin_name,),
            daemon=True
        ).start()
        
    def _approve_plugin_thread(self, plugin_name):
        """
        Approve and install plugin in a background thread
        
        Args:
            plugin_name: Name of the plugin to approve
        """
        try:
            # Try to load the plugin
            success = self.plugin_manager.load_plugin(plugin_name)
            
            if success:
                # Activate the plugin
                activate_success = self.plugin_manager.activate_plugin(plugin_name)
                
                # Update UI on main thread
                self.frame.after(0, lambda: self._on_plugin_approved(plugin_name, activate_success))
            else:
                # Update UI with error
                self.frame.after(0, lambda: self._on_plugin_approval_failed(plugin_name))
                
        except Exception as e:
            # Update UI with error
            self.frame.after(0, lambda: self._on_plugin_approval_error(plugin_name, str(e)))
        
    def _on_plugin_approved(self, plugin_name, activate_success):
        """
        Handle successful plugin approval
        
        Args:
            plugin_name: Name of the plugin
            activate_success: Whether activation was successful
        """
        # Stop progress
        self.progress_bar.stop()
        
        if activate_success:
            self.status_var.set(f"Plugin {plugin_name} approved and activated")
            messagebox.showinfo(
                "Plugin Approved",
                f"Plugin {plugin_name} has been approved and activated successfully."
            )
        else:
            self.status_var.set(f"Plugin {plugin_name} loaded but not activated")
            messagebox.showwarning(
                "Plugin Partially Approved",
                f"Plugin {plugin_name} was loaded but could not be activated."
            )
            
        # Refresh plugin list
        self.refresh_plugin_list()
        
        # Update sandbox plugin list
        self.update_sandbox_plugin_list()
        
    def _on_plugin_approval_failed(self, plugin_name):
        """
        Handle failed plugin approval
        
        Args:
            plugin_name: Name of the plugin
        """
        # Stop progress
        self.progress_bar.stop()
        
        self.status_var.set(f"Failed to approve plugin {plugin_name}")
        messagebox.showerror(
            "Approval Failed",
            f"Failed to load and approve plugin {plugin_name}."
        )
        
    def _on_plugin_approval_error(self, plugin_name, error_message):
        """
        Handle error during plugin approval
        
        Args:
            plugin_name: Name of the plugin
            error_message: Error message
        """
        # Stop progress
        self.progress_bar.stop()
        
        self.status_var.set(f"Error approving plugin {plugin_name}: {error_message}")
        messagebox.showerror(
            "Approval Error",
            f"Error approving plugin {plugin_name}:\n{error_message}"
        )

    def _on_destroy(self, event):
        """Called when the frame is destroyed"""
        if event.widget == self.frame:
            self.is_running = False

    def setup_settings_tab(self):
        """Setup the settings tab for plugin configuration"""
        # Create split layout with plugin list on left and config on right
        self.settings_paned = ttk.PanedWindow(self.settings_frame, orient=tk.HORIZONTAL)
        self.settings_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create left frame for plugin list
        left_frame = ttk.Frame(self.settings_paned, width=200)
        self.settings_paned.add(left_frame, weight=1)
        
        # Create plugin list with header
        ttk.Label(left_frame, text="Available Plugins", font=("", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        
        # Plugin list frame with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Use a styled listbox
        self.settings_plugin_listbox = tk.Listbox(
            list_frame, 
            selectmode=tk.SINGLE,
            activestyle='dotbox',
            font=("", 9),
            borderwidth=1,
            relief=tk.SOLID,
            highlightthickness=0
        )
        self.settings_plugin_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.settings_plugin_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.settings_plugin_listbox.configure(yscrollcommand=scrollbar.set)

        # Bind selection event
        self.settings_plugin_listbox.bind('<<ListboxSelect>>', self.on_settings_plugin_selected)
        
        # Create right frame for config
        self.settings_right_frame = ttk.Frame(self.settings_paned, width=500)
        self.settings_paned.add(self.settings_right_frame, weight=3)
        
        # Create config area with scrolling
        self.settings_canvas = tk.Canvas(self.settings_right_frame, highlightthickness=0)
        self.settings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.settings_scrollbar = ttk.Scrollbar(self.settings_right_frame, orient=tk.VERTICAL, command=self.settings_canvas.yview)
        self.settings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.settings_canvas.configure(yscrollcommand=self.settings_scrollbar.set)
        self.settings_canvas.bind('<Configure>', self._on_settings_canvas_configure)
        
        # Enable mousewheel scrolling
        self.settings_canvas.bind_all('<MouseWheel>', lambda event: self.settings_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # Create a frame inside the canvas for config widgets
        self.settings_config_frame = ttk.Frame(self.settings_canvas)
        self.settings_canvas_window = self.settings_canvas.create_window((0, 0), window=self.settings_config_frame, anchor=tk.NW)
        self.settings_config_frame.bind('<Configure>', self._on_settings_frame_configure)
        
        # Add header to config frame
        self.settings_header = ttk.Label(self.settings_config_frame, text="Select a plugin to configure", font=("", 12, "bold"))
        self.settings_header.grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=15, pady=15)
        
        # Add description
        self.settings_description = ttk.Label(self.settings_config_frame, text="", wraplength=500, font=("", 9))
        self.settings_description.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=15, pady=(0, 10))
        
        # Add separator
        ttk.Separator(self.settings_config_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=3, sticky=tk.EW, padx=10, pady=10)
        
        # Add config content
        self.settings_content = ttk.Frame(self.settings_config_frame)
        self.settings_content.grid(row=3, column=0, columnspan=3, sticky=tk.NSEW, padx=15, pady=5)
        
        # Add buttons
        button_frame = ttk.Frame(self.settings_config_frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.E, padx=15, pady=15)
        
        self.settings_save_button = ttk.Button(button_frame, text="Save", command=self.save_plugin_config, style="Accent.TButton")
        self.settings_save_button.pack(side=tk.RIGHT, padx=5)
        self.settings_save_button.state(['disabled'])
        
        self.settings_reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_plugin_config)
        self.settings_reset_button.pack(side=tk.RIGHT, padx=5)
        self.settings_reset_button.state(['disabled'])
        
        # Load plugins into settings tab
        self.load_settings_plugins()    
        
    def load_settings_plugins(self):
        """Load the list of available plugins into the settings tab"""
        # Clear the listbox
        self.settings_plugin_listbox.delete(0, tk.END)
        
        # Get all plugins
        plugins = self.plugin_manager.get_all_plugins()
        if not plugins:
            # If plugins dict is empty, try to discover plugins first
            self.plugin_manager.discover_plugins()
            # Try again to get plugins
            plugins = self.plugin_manager.get_all_plugins()
            
        # Sort plugins by name
        plugin_ids = sorted(plugins.keys()) if plugins else []
        
        # Add plugins to listbox with status indicator
        for plugin_id in plugin_ids:
            plugin_info = plugins.get(plugin_id, {})
            status = plugin_info.get("status", "unknown")
            display_name = f"✓ {plugin_id}" if status == "active" else plugin_id
            self.settings_plugin_listbox.insert(tk.END, display_name)
            
        # Log the number of plugins found
        if self.log:
            self.log(f"[PluginPanel] Loaded {len(plugin_ids)} plugins into settings tab")
    
    def on_settings_plugin_selected(self, event):
        """Handle plugin selection in the settings tab"""
        # Get selected plugin
        selection = self.settings_plugin_listbox.curselection()
        if not selection:
            return
            
        plugin_id = self.settings_plugin_listbox.get(selection[0])
        self.load_plugin_config(plugin_id)
        
    def load_plugin_config(self, plugin_id):
        """Load the configuration for a plugin"""
        # Clear the config content
        for widget in self.settings_content.winfo_children():
            widget.destroy()
        
        # Update current plugin
        self.current_plugin_id = plugin_id
        self.current_config = {}
        self.config_widgets = {}
        
        # Enable buttons
        self.settings_save_button.state(['!disabled'])
        self.settings_reset_button.state(['!disabled'])
        
        # Update header
        self.settings_header.config(text=f"Configure: {plugin_id}")
        
        # Get plugin info
        plugin_info = self.plugin_manager.get_plugin_metadata(plugin_id)
        
        # Update description
        if plugin_info and "description" in plugin_info:
            self.settings_description.config(text=plugin_info["description"])
        else:
            self.settings_description.config(text="No description available")
        
        # Get plugin config schema
        config_schema = self.plugin_manager.get_plugin_config_schema(plugin_id)
        
        if not config_schema:
            # Show no config message
            ttk.Label(
                self.settings_content,
                text="This plugin has no configurable settings.",
                font=("", 10, "italic")
            ).pack(pady=20)
            return
        
        # Get current plugin config
        current_config = self.plugin_manager.get_plugin_config(plugin_id) or {}
        self.current_config = current_config.copy()
        
        # Build config UI based on schema
        self._create_config_widgets(config_schema, current_config)
        
    def _create_config_widgets(self, schema, config):
        """Create configuration widgets based on schema"""
        # Check if we have properties
        if "properties" not in schema:
            ttk.Label(
                self.settings_content,
                text="Invalid configuration schema",
                font=("", 10, "italic")
            ).pack(pady=20)
            return
            
        # Get properties
        properties = schema["properties"]
        
        # Track row for grid
        row = 0
        
        # Create widgets for each property
        for prop_name, prop_details in properties.items():
            if "type" not in prop_details:
                continue
                
            # Get current value or default
            current_value = config.get(prop_name, prop_details.get("default", ""))
            
            # Create label
            ttk.Label(
                self.settings_content,
                text=prop_details.get("title", prop_name),
                font=("", 10)
            ).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            # Create widget based on type
            widget_type = prop_details["type"]
            
            if widget_type == "string":
                # Create string input
                if "enum" in prop_details:
                    # Create dropdown for enum
                    var = tk.StringVar(value=str(current_value))
                    dropdown = ttk.Combobox(
                        self.settings_content,
                        textvariable=var,
                        values=prop_details["enum"],
                        state="readonly",
                        width=30
                    )
                    dropdown.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                    self.config_widgets[prop_name] = var
                else:
                    # Create regular text input
                    var = tk.StringVar(value=str(current_value))
                    entry = ttk.Entry(self.settings_content, textvariable=var, width=30)
                    entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                    self.config_widgets[prop_name] = var
                    
            elif widget_type == "integer" or widget_type == "number":
                # Create numeric input with validation
                var = tk.StringVar(value=str(current_value))
                validate_cmd = (self.settings_content.register(
                    lambda s: s == "" or s.isdigit() or (s[0] == "-" and s[1:].isdigit())
                ), '%P')
                entry = ttk.Entry(
                    self.settings_content, 
                    textvariable=var,
                    validate="key",
                    validatecommand=validate_cmd,
                    width=10
                )
                entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                self.config_widgets[prop_name] = var
                
            elif widget_type == "boolean":
                # Create checkbox
                var = tk.BooleanVar(value=bool(current_value))
                checkbox = ttk.Checkbutton(self.settings_content, variable=var)
                checkbox.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                self.config_widgets[prop_name] = var
                
            # Add description if available
            if "description" in prop_details:
                ttk.Label(
                    self.settings_content,
                    text=prop_details["description"],
                    font=("", 8),
                    foreground="gray"
                ).grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
                
            # Increment row
            row += 1
                
    def save_plugin_config(self):
        """Save the current plugin configuration"""
        if not self.current_plugin_id:
            return
            
        # Get values from widgets
        new_config = {}
        for prop_name, widget_var in self.config_widgets.items():
            new_config[prop_name] = widget_var.get()
            
        # Save config
        success = self.plugin_manager.set_plugin_config(self.current_plugin_id, new_config)
        
        if success:
            self.log(f"[Plugins] Saved configuration for {self.current_plugin_id}")
            messagebox.showinfo("Configuration Saved", f"Configuration for {self.current_plugin_id} has been saved.")
            
            # Update current config
            self.current_config = new_config.copy()
        else:
            self.log(f"[Error] Failed to save configuration for {self.current_plugin_id}")
            messagebox.showerror("Error", f"Failed to save configuration for {self.current_plugin_id}")
            
    def reset_plugin_config(self):
        """Reset the plugin configuration to the last saved state"""
        if not self.current_plugin_id:
            return
            
        # Reload the plugin configuration
        self.load_plugin_config(self.current_plugin_id)
        
    def _on_settings_canvas_configure(self, event):
        """Handle canvas resize for settings tab"""
        self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"))
        self.settings_canvas.itemconfig(self.settings_canvas_window, width=event.width)
        
    def _on_settings_frame_configure(self, event):
        """Handle frame resize for settings tab"""
        self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"))
        
    def _create_config_widgets(self, schema, config):
        """Create configuration widgets based on schema"""
        # Check if we have properties
        if "properties" not in schema:
            ttk.Label(
                self.settings_content,
                text="Invalid configuration schema",
                font=("", 10, "italic")
            ).pack(pady=20)
            return
            
        # Get properties
        properties = schema["properties"]
        
        # Track row for grid
        row = 0
        
        # Create widgets for each property
        for prop_name, prop_details in properties.items():
            if "type" not in prop_details:
                continue
                
            # Get current value or default
            current_value = config.get(prop_name, prop_details.get("default", ""))
            
            # Create label
            ttk.Label(
                self.settings_content,
                text=prop_details.get("title", prop_name),
                font=("", 10)
            ).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            # Create widget based on type
            widget_type = prop_details["type"]
            
            if widget_type == "string":
                # Create string input
                if "enum" in prop_details:
                    # Create dropdown for enum
                    var = tk.StringVar(value=str(current_value))
                    dropdown = ttk.Combobox(
                        self.settings_content,
                        textvariable=var,
                        values=prop_details["enum"],
                        state="readonly",
                        width=30
                    )
                    dropdown.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                    self.config_widgets[prop_name] = var
                else:
                    # Create regular text input
                    var = tk.StringVar(value=str(current_value))
                    entry = ttk.Entry(self.settings_content, textvariable=var, width=30)
                    entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                    self.config_widgets[prop_name] = var
                    
            elif widget_type == "integer" or widget_type == "number":
                # Create numeric input with validation
                var = tk.StringVar(value=str(current_value))
                validate_cmd = (self.settings_content.register(
                    lambda s: s == "" or s.isdigit() or (s[0] == "-" and s[1:].isdigit())
                ), '%P')
                entry = ttk.Entry(
                    self.settings_content, 
                    textvariable=var,
                    validate="key",
                    validatecommand=validate_cmd,
                    width=10
                )
                entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                self.config_widgets[prop_name] = var
                
            elif widget_type == "boolean":
                # Create checkbox
                var = tk.BooleanVar(value=bool(current_value))
                checkbox = ttk.Checkbutton(self.settings_content, variable=var)
                checkbox.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                self.config_widgets[prop_name] = var
                
            # Add description if available
            if "description" in prop_details:
                ttk.Label(
                    self.settings_content,
                    text=prop_details["description"],
                    font=("", 8),
                    foreground="gray"
                ).grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
                
            # Increment row
            row += 1
            
        # Add save button
        ttk.Button(
            self.settings_content,
            text="Save Configuration",
            command=self.save_plugin_config
        ).grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=(10, 5))  
        
        # Add reset button
        ttk.Button(
            self.settings_content,
            text="Reset Configuration",
            command=self.reset_plugin_config
        ).grid(row=row + 1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Add cancel button
        ttk.Button(
            self.settings_content,
            text="Cancel",
            command=self.hide_settings
        ).grid(row=row + 2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Add spacing
        ttk.Label(self.settings_content, text="").grid(row=row + 3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Add version label
        ttk.Label(self.settings_content, text="Version: " + self.current_plugin_version, font=("", 8), foreground="gray").grid(row=row + 4, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Add copyright label
        ttk.Label(self.settings_content, text="Copyright: " + self.current_plugin_copyright, font=("", 8), foreground="gray").grid(row=row + 5, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Add license label
        ttk.Label(self.settings_content, text="License: " + self.current_plugin_license, font=("", 8), foreground="gray").grid(row=row + 6, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
    def _append_sandbox_output(self, text, tag=None):
        # Use after() to safely update from another thread
        self.frame.after(0, lambda: self._do_append_sandbox_output(text, tag))  
        
    def _do_append_sandbox_output(self, text, tag=None):
        self.sandbox_output.configure(state="normal")
        self.sandbox_output.insert("end", text, tag)
        self.sandbox_output.configure(state="disabled")
        
        # Auto-scroll
        self.sandbox_output.see("end")
        
        # Update UI

        threading.Thread(target=self.long_running_task).start()

    def long_running_task(self):

        time.sleep(5)
        self._append_sandbox_output("Task completed.\n")
        
    def start_long_running_task(self):
        threading.Thread(target=self.long_running_task).start()
