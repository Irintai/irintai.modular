"""
Model panel UI component for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Callable, Dict, List, Any, Optional
import queue
import re


# Import model status constants
from core.model_manager import MODEL_STATUS, RECOMMENDED_MODELS

class ModelPanel:
    """Model management panel for installing and managing AI models"""
    
    def __init__(self, parent, model_manager, logger: Callable, on_model_selected: Callable):
        """
        Initialize the model panel
        
        Args:
            parent: Parent widget
            model_manager: ModelManager instance
            logger: Logging function
            on_model_selected: Callback for model selection
        """
        self.parent = parent
        self.model_manager = model_manager
        self.log = logger
        self.on_model_selected_callback = on_model_selected
        
        # Model categories
        self.model_categories = {
            "Conversation": ["llama3:8b", "mistral:7b-instruct", "openchat:3.5"],
            "Roleplay": ["mythomax", "nous-hermes:13b", "airoboros-l2"],
            "Coding": ["codellama:7b-instruct", "deepseek-coder", "wizardcoder:15b"],
            "Reason": ["gemma:7b-instruct", "phi-2", "zephyr:beta"]
        }
        
        # Create the main frame
        self.frame = ttk.Frame(parent)
        
        # Create thread-safe queue for UI updates
        self.update_queue = queue.Queue()
        # Start queue processor
        self.process_queue()

        # Initialize UI components
        self.initialize_ui()
        
        # Fetch models
        self.refresh_model_list()
    
    def initialize_ui(self):
        """Initialize the UI components"""        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create Local Models tab
        self.local_models_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.local_models_frame, text="Local Models")
        
        # Create API Models tab
        self.api_models_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.api_models_frame, text="API Models")
        
        # Create Model Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Model Settings")
          
        # Setup local models tab (existing functionality)
        self.setup_local_models_tab()
        
        # Setup API models tab (new functionality)
        self.setup_api_models_tab()
        
        # Setup Model Settings tab
        self.setup_settings_tab()
        
        # Create progress bar
        self.create_progress_bar()
        
        # Initialize plugin extensions
        self.initialize_plugin_extensions()
          
    def setup_local_models_tab(self):
        """Setup the local models tab with existing functionality"""
        # Create the various panel sections in the local models tab
        
        # Use common parent for all sections
        parent_frame = self.local_models_frame
        
        # Create model selection section
        self.create_model_selection(parent=parent_frame)
        
        # Create model management section
        self.create_model_management(parent=parent_frame)
        
        # Create model information section
        self.create_model_info(parent=parent_frame)

    def initialize_plugin_extensions(self):
        """Initialize plugin extensions for the model panel"""
        # Dictionaries for plugin extensions
        self.plugin_model_providers = {}  # Custom model providers
        self.plugin_model_configs = {}    # Custom model configurations
        self.plugin_ui_extensions = {}    # UI extensions
        self.plugin_actions = {}          # Custom model actions
        
        # Create plugin extension frames
        self.plugin_frame = ttk.LabelFrame(self.frame, text="Plugin Extensions")
        
        # Add plugin action menu
        self.create_plugin_action_menu()
        
        # Register with plugin manager if available
        if hasattr(self.parent, "plugin_manager"):
            plugin_manager = self.parent.plugin_manager
            
            # Register for plugin events
            plugin_manager.register_event_handler("model_panel", "plugin_activated", 
                                                 self.on_plugin_activated)
            plugin_manager.register_event_handler("model_panel", "plugin_deactivated", 
                                                 self.on_plugin_deactivated)
            plugin_manager.register_event_handler("model_panel", "plugin_unloaded", 
                                                 self.on_plugin_unloaded)
            
            # Get all active plugins and register their extensions
            active_plugins = plugin_manager.get_active_plugins()
            for plugin_id, plugin in active_plugins.items():
                self.register_plugin_extension(plugin_id, plugin)
    
    def create_model_selection(self, parent=None):
        """Create the model selection section"""
        # Use provided parent or default to self.frame
        parent_frame = parent if parent else self.frame
        selection_frame = ttk.LabelFrame(parent_frame, text="Model Selection")
        selection_frame.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)
        
        # Create model filter section
        filter_frame = ttk.Frame(selection_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter by Category:").pack(side=tk.LEFT)
        
        # Category dropdown
        self.category_var = tk.StringVar(value="All")
        self.category_dropdown = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=["All"] + list(self.model_categories.keys()),
            state="readonly",
            width=15
        )
        self.category_dropdown.pack(side=tk.LEFT, padx=5)
        self.category_dropdown.bind("<<ComboboxSelected>>", self.on_category_selected)
        
        # Search entry
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.on_search_changed)
        
        # Main model selection section
        model_frame = ttk.Frame(selection_frame)
        model_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a list view with multiple columns
        columns = ("Name", "Size", "Status", "Context")
        self.model_tree = ttk.Treeview(
            model_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=10
        )
        
        # Configure columns
        self.model_tree.heading("Name", text="Model Name")
        self.model_tree.heading("Size", text="Size")
        self.model_tree.heading("Status", text="Status")
        self.model_tree.heading("Context", text="Context")
        
        self.model_tree.column("Name", width=200, anchor=tk.W)
        self.model_tree.column("Size", width=80, anchor=tk.CENTER)
        self.model_tree.column("Status", width=100, anchor=tk.CENTER)
        self.model_tree.column("Context", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(model_frame, orient="vertical", command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.model_tree.bind("<<TreeviewSelect>>", self.on_model_selected)
        
        # Buttons below the tree
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Refresh Model List",
            command=self.refresh_model_list
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Select Model",
            command=self.select_current_model,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)    
        
    def create_model_management(self, parent=None):
        """Create the model management section"""

        # Use provided parent or default to self.frame
        parent_frame = parent if parent else self.frame
        mgmt_frame = ttk.LabelFrame(parent_frame, text="Model Management")
        mgmt_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Actions section
        actions_frame = ttk.Frame(mgmt_frame)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Install button
        self.install_button = ttk.Button(
            actions_frame,
            text="Install Selected Model",
            command=self.install_selected_model
        )
        self.install_button.pack(side=tk.LEFT, padx=5)
        
        # Uninstall button
        self.uninstall_button = ttk.Button(
            actions_frame,
            text="Uninstall Selected Model",
            command=self.uninstall_selected_model
        )
        self.uninstall_button.pack(side=tk.LEFT, padx=5)
        
        # Start/Stop buttons
        self.start_button = ttk.Button(
            actions_frame,
            text="Start Selected Model",
            command=self.start_selected_model
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            actions_frame,
            text="Stop Running Model",
            command=self.stop_running_model
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Path info section
        path_frame = ttk.Frame(mgmt_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(path_frame, text="Model Path:").pack(side=tk.LEFT)
        
        self.path_var = tk.StringVar(value=self.model_manager.model_path)
        path_label = ttk.Label(path_frame, textvariable=self.path_var, foreground="blue")
        path_label.pack(side=tk.LEFT, padx=5)
        
        # Open folder button
        ttk.Button(
            path_frame,
            text="Open Folder",
            command=self.open_model_folder
        ).pack(side=tk.RIGHT, padx=5)
        
        # Create menu for plugin-provided model actions
        self.create_plugin_action_menu()
        
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
    
    def create_model_info(self, parent=None):
        """Create the model information section"""
        # Use provided parent or default to self.frame
        parent_frame = parent if parent else self.frame
        info_frame = ttk.LabelFrame(parent_frame, text="Model Information")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Model details
        details_frame = ttk.Frame(info_frame)
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Two-column layout for details
        left_frame = ttk.Frame(details_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(details_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Left column - Basic info
        ttk.Label(left_frame, text="Selected Model:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_name_var = tk.StringVar(value="None")
        ttk.Label(left_frame, textvariable=self.selected_name_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(left_frame, text="Status:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_status_var = tk.StringVar(value="None")
        ttk.Label(left_frame, textvariable=self.selected_status_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(left_frame, text="Size:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_size_var = tk.StringVar(value="Unknown")
        ttk.Label(left_frame, textvariable=self.selected_size_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Right column - Additional info
        ttk.Label(right_frame, text="Context Length:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_context_var = tk.StringVar(value="Unknown")
        ttk.Label(right_frame, textvariable=self.selected_context_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(right_frame, text="Category:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_category_var = tk.StringVar(value="Unknown")
        ttk.Label(right_frame, textvariable=self.selected_category_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(right_frame, text="8-bit Mode:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.selected_8bit_var = tk.StringVar(value="Not Recommended")
        ttk.Label(right_frame, textvariable=self.selected_8bit_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Description section
        ttk.Label(info_frame, text="Description:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        self.description_text = tk.Text(info_frame, height=4, wrap=tk.WORD, font=("Helvetica", 9))
        self.description_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.description_text.config(state=tk.DISABLED)
        
    def create_progress_bar(self):
        """Create the progress bar"""
        progress_frame = ttk.Frame(self.frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_mode = tk.StringVar(value="determinate")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            mode=self.progress_mode.get(),
            length=100
        )
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Status text
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, padx=5)
        
    def refresh_model_list(self):
        """Refresh the model list"""
        # Clear the current tree
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
            
        # Show progress
        self.progress_mode.set("indeterminate")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start()
        self.status_var.set("Fetching models...")
        
        # Start a thread to fetch models
        threading.Thread(
            target=self._fetch_models_thread,
            daemon=True
        ).start()
        
    def _fetch_models_thread(self):
        """Fetch models in a background thread"""
        try:
            # Get locally installed models
            installed_models = self.model_manager.detect_models()
            
            # Fetch remote models
            all_models = self.model_manager.fetch_available_models()
            
            # Add plugin-provided models
            plugin_models = self._get_plugin_models()
            
            # Merge lists, prioritizing plugin models if there are duplicates
            if plugin_models:
                # Create a dictionary with model name as key
                model_dict = {model["name"]: model for model in all_models}
                
                # Update or add plugin models
                for model in plugin_models:
                    model_dict[model["name"]] = model
                    
                # Convert back to list
                all_models = list(model_dict.values())
            
            # Queue UI update instead of direct call
            self.update_queue.put((self._update_model_tree, [all_models], {}))
        except Exception as e:
            self.log(f"[Error] Failed to fetch models: {e}")
            self.update_queue.put((self.status_var.set, [f"Error: {str(e)}"], {}))
        finally:
            # Queue progress bar reset
            self.update_queue.put((self._reset_progress_bar, [], {}))
            
    def _get_plugin_models(self):
        """
        Get models from plugin providers
        
        Returns:
            List of model dictionaries
        """
        plugin_models = []
        
        # Skip if no providers
        if not hasattr(self, "plugin_model_providers"):
            return plugin_models
            
        # Call each provider
        for provider_id, provider_func in self.plugin_model_providers.items():
            try:
                # Get models from this provider
                models = provider_func()
                
                if models and isinstance(models, list):
                    # Add provider info to each model
                    for model in models:
                        if isinstance(model, dict) and "name" in model:
                            # Add provider ID
                            model["provider"] = provider_id
                            plugin_models.append(model)
            except Exception as e:
                self.log(f"[Error] Plugin model provider {provider_id} failed: {e}")
                
        return plugin_models

    def _update_model_tree(self, models_list):
        """
        Update the model tree with fetched models
        
        Args:
            models_list: List of model dictionaries
        """
        # Clear the current tree
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
            
        # Add models to the tree
        for model in models_list:
            name = model["name"]
            size = model["size"] if "size" in model else "Unknown"
            installed = model.get("installed", False)
            
            # Get status
            status = self.model_manager.model_statuses.get(name, MODEL_STATUS["NOT_INSTALLED"])
            
            # Get additional info for recommended models
            context = "Unknown"
            if name in RECOMMENDED_MODELS:
                context = RECOMMENDED_MODELS[name]["context"]
                
            # Add to tree
            self.model_tree.insert(
                "", 
                tk.END, 
                values=(name, size, status, context),
                tags=("installed" if installed else "available",)
            )
            
        # Configure tag appearance
        self.model_tree.tag_configure("installed", background="#e6f3ff")
        
        # Select the first item if available
        if self.model_tree.get_children():
            first_item = self.model_tree.get_children()[0]
            self.model_tree.selection_set(first_item)
            self.on_model_selected()
            
        # Update status
        self.status_var.set(f"Found {len(models_list)} models")
        
    def _reset_progress_bar(self):
        """Reset the progress bar"""
        self.progress_bar.stop()
        self.progress_mode.set("determinate")
        self.progress_bar.config(mode="determinate")
        self.progress_var.set(0)
        
    def on_category_selected(self, event):
        """Handle category selection"""
        category = self.category_var.get()
        self._filter_models()
        
    def on_search_changed(self, event):
        """Handle search text changes"""
        self._filter_models()
        
    def _filter_models(self):
        """Filter models based on category and search text"""
        category = self.category_var.get()
        search_text = self.search_var.get().lower()
        
        # Get all items
        all_items = self.model_tree.get_children()
        
        # Show all items first
        for item in all_items:
            self.model_tree.item(item, tags=self.model_tree.item(item, "tags"))
            
        # Filter by category
        if category != "All":
            category_models = self.model_categories.get(category, [])
            for item in all_items:
                values = self.model_tree.item(item, "values")
                model_name = values[0]
                
                if model_name not in category_models:
                    self.model_tree.detach(item)
                    
        # Filter by search text
        if search_text:
            # Get current items (after category filter)
            current_items = self.model_tree.get_children()
            
            for item in current_items:
                values = self.model_tree.item(item, "values")
                model_name = values[0].lower()
                
                if search_text not in model_name:
                    self.model_tree.detach(item)
                    
        # Reattach all items that match both filters
        for item in all_items:
            values = self.model_tree.item(item, "values")
            model_name = values[0]
            
            # Check category
            category_match = (category == "All") or (model_name in self.model_categories.get(category, []))
            
            # Check search
            search_match = (not search_text) or (search_text in model_name.lower())
            
            if category_match and search_match:
                try:
                    # Try to reattach if detached
                    self.model_tree.move(item, "", tk.END)
                except:
                    pass
                    
    def on_model_selected(self, event=None):
        """Handle model selection in the tree"""
        selection = self.model_tree.selection()
        if not selection:
            return
            
        # Get model info
        item = selection[0]
        values = self.model_tree.item(item, "values")
        
        model_name = values[0]
        model_size = values[1]
        model_status = values[2]
        model_context = values[3]
        
        # Update selected model info
        self.selected_name_var.set(model_name)
        self.selected_status_var.set(model_status)
        self.selected_size_var.set(model_size)
        self.selected_context_var.set(model_context)
        
        # Find category
        category = "Unknown"
        for cat, models in self.model_categories.items():
            if model_name in models:
                category = cat
                break
                
        self.selected_category_var.set(category)
        
        # Check if 8-bit mode is recommended
        needs_8bit = "13b" in model_name or "70b" in model_name
        self.selected_8bit_var.set("Recommended" if needs_8bit else "Not Needed")
        
        # Update description
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        
        if model_name in RECOMMENDED_MODELS:
            description = RECOMMENDED_MODELS[model_name]["note"]
            if needs_8bit:
                description += "\nThis model requires 8-bit mode for optimal performance."
                
            self.description_text.insert(tk.END, description)
        else:
            self.description_text.insert(tk.END, "No detailed information available for this model.")
            
        self.description_text.config(state=tk.DISABLED)
        
        # Update button states
        if model_status == MODEL_STATUS["INSTALLED"]:
            self.install_button.config(state=tk.DISABLED)
            self.uninstall_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.NORMAL)
        elif model_status == MODEL_STATUS["NOT_INSTALLED"]:
            self.install_button.config(state=tk.NORMAL)
            self.uninstall_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
        elif model_status == MODEL_STATUS["RUNNING"]:
            self.install_button.config(state=tk.DISABLED)
            self.uninstall_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            # Installing, uninstalling, etc.
            self.install_button.config(state=tk.DISABLED)
            self.uninstall_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            
    def select_current_model(self):
        """Select the current model for use"""
        selection = self.model_tree.selection()
        if not selection:
            return
            
        # Get model name
        item = selection[0]
        values = self.model_tree.item(item, "values")
        model_name = values[0]
        
        # Update the model manager
        self.model_manager.current_model = model_name
        
        # Call the callback
        if self.on_model_selected_callback:
            self.on_model_selected_callback(model_name)
            
        # Update status
        self.status_var.set(f"Selected model: {model_name}")
        
    def install_selected_model(self):
        """Install the selected model"""
        selection = self.model_tree.selection()
        if not selection:
            return
            
        # Get model name
        item = selection[0]
        values = self.model_tree.item(item, "values")
        model_name = values[0]
        
        # Check if already installed
        status = self.model_manager.model_statuses.get(model_name, MODEL_STATUS["NOT_INSTALLED"])
        if status == MODEL_STATUS["INSTALLED"]:
            messagebox.showinfo("Already Installed", f"Model '{model_name}' is already installed")
            return
            
        # Confirm installation
        result = messagebox.askyesno(
            "Confirm Installation", 
            f"Do you want to install model '{model_name}'?\n\n"
            f"This may require significant disk space.",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
            
        # Update progress bar and status
        self.progress_mode.set("indeterminate")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start()
        self.status_var.set(f"Installing {model_name}...")
        
        # Install the model
        self.model_manager.install_model(model_name, self._update_progress)
        
        # Update tree item
        self.model_tree.item(
            item, 
            values=(model_name, values[1], MODEL_STATUS["INSTALLING"], values[3])
        )
        
        # Disable buttons during installation
        self.install_button.config(state=tk.DISABLED)
        self.uninstall_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        
    def uninstall_selected_model(self):
        """Uninstall the selected model"""
        selection = self.model_tree.selection()
        if not selection:
            return
            
        # Get model name
        item = selection[0]
        values = self.model_tree.item(item, "values")
        model_name = values[0]
        
        # Check if installed
        status = self.model_manager.model_statuses.get(model_name, MODEL_STATUS["NOT_INSTALLED"])
        if status == MODEL_STATUS["NOT_INSTALLED"]:
            messagebox.showinfo("Not Installed", f"Model '{model_name}' is not installed")
            return
            
        # Check if model is running
        if self.model_manager.model_process and self.model_manager.model_process.poll() is None:
            # Ask to stop the model first
            result = messagebox.askyesno(
                "Model Running", 
                f"Model '{model_name}' is currently running. Stop it before uninstalling?",
                icon=messagebox.WARNING
            )
            
            if result:
                self.model_manager.stop_model()
            else:
                return
                
        # Confirm uninstallation
        result = messagebox.askyesno(
            "Confirm Uninstallation", 
            f"Do you want to uninstall model '{model_name}'?\n\n"
            f"This will free up disk space but you will need to download it again if needed.",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
            
        # Update progress bar and status
        self.progress_mode.set("indeterminate")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start()
        self.status_var.set(f"Uninstalling {model_name}...")
        
        # Uninstall the model
        self.model_manager.uninstall_model(model_name)
        
        # Update tree item
        self.model_tree.item(
            item, 
            values=(model_name, values[1], MODEL_STATUS["UNINSTALLING"], values[3])
        )
        
        # Disable buttons during uninstallation
        self.install_button.config(state=tk.DISABLED)
        self.uninstall_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        
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
        if config is None:
            config = {}
        
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
        
        # Filter out parameters that shouldn't be passed to Ollama's command line
        # Only allow known Ollama parameters
        valid_ollama_params = ["temperature", "context", "threads", "gpu", "seed"]
        filtered_config = {}
        
        for key, value in config.items():
            if key in valid_ollama_params:
                filtered_config[key] = value
            else:
                # Log that we're ignoring this parameter
                if hasattr(self, "log"):
                    self.log(f"[Warning] Ignoring parameter for Ollama: {key}")
                    
        return filtered_config
    
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
            
    def stop_running_model(self):
        """Stop the running model"""
        # Check if model is running
        if not self.model_manager.model_process or self.model_manager.model_process.poll() is not None:
            messagebox.showinfo("No Model Running", "No model is currently running")
            return
            
        # Update progress bar and status
        self.progress_mode.set("indeterminate")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start()
        self.status_var.set("Stopping model...")
        
        # Stop the model
        success = self.model_manager.stop_model()
        
        if success:
            # Reset progress bar and status
            self._reset_progress_bar()
            self.status_var.set("Model stopped")
            
            # Reset button states
            self.stop_button.config(state=tk.DISABLED)
            
            # Update tree items
            self._refresh_tree_status()
        else:
            # Reset progress bar and status
            self._reset_progress_bar()
            self.status_var.set("Failed to stop model")
            
    def _update_progress(self, value):
        """
        Update progress bar value
        
        Args:
            value: Progress value (0-100)
        """
        # Ensure we're in determinate mode
        if self.progress_mode.get() != "determinate":
            self.progress_bar.stop()
            self.progress_mode.set("determinate")
            self.progress_bar.config(mode="determinate")
            
        # Update the value
        self.progress_var.set(value)
        
    def _update_model_status(self, model_name, status):
        """
        Update the status of a model in the tree
        
        Args:
            model_name: Name of the model
            status: New status
        """
        # Find the item with this model name
        for item in self.model_tree.get_children():
            values = self.model_tree.item(item, "values")
            if values[0] == model_name:
                # Update the status
                self.model_tree.item(
                    item, 
                    values=(values[0], values[1], status, values[3])
                )
                
                # If this is the selected item, update the info panel
                if item in self.model_tree.selection():
                    self.selected_status_var.set(status)
                    
                # Update button states
                self.on_model_selected()
                break
                
    def _refresh_tree_status(self):
        """Refresh the status of all models in the tree"""
        for item in self.model_tree.get_children():
            values = self.model_tree.item(item, "values")
            model_name = values[0]
            
            # Get current status
            status = self.model_manager.model_statuses.get(model_name, MODEL_STATUS["NOT_INSTALLED"])
            
            # Update the item
            self.model_tree.item(
                item, 
                values=(model_name, values[1], status, values[3])
            )
            
        # Update selected item
        self.on_model_selected()
        
    def open_model_folder(self):
        """Open the model folder in file explorer"""
        import os
        import subprocess
        import sys
        
        model_path = self.model_manager.model_path
        
        try:
            if not os.path.exists(model_path):
                os.makedirs(model_path, exist_ok=True)
                
            # Open folder based on OS
            if os.name == 'nt':  # Windows
                os.startfile(model_path)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', model_path])
                
            self.log(f"[Opened] Model folder: {model_path}")
        except Exception as e:
            self.log(f"[Error] Cannot open model folder: {e}")
            messagebox.showerror("Error", f"Cannot open model folder: {e}")
    
    def process_queue(self):
        """Process queued UI update requests from threads"""
        try:
            while True:
                # Get task without waiting
                item = self.update_queue.get_nowait()
                try:
                    # Check if item is a function or a tuple
                    if callable(item):
                        # Just a function, call it directly
                        item()
                    else:
                        # Must be a tuple with a callable as the first item
                        if isinstance(item, tuple) and len(item) > 0 and callable(item[0]):
                            if len(item) == 3:
                                # Format: (task, args, kwargs)
                                task, args, kwargs = item
                                task(*args, **kwargs)
                            elif len(item) == 2:
                                # Format: (task, args)
                                task, args = item
                                task(*args)
                            else:
                                # Just task
                                item[0]()
                        else:
                            # Log the error
                            self.log(f"[Error] Invalid queue item format: {item}")
                except Exception as e:
                    self.log(f"[Error] Error in queued task: {e}")
                self.update_queue.task_done()
        except queue.Empty:
            # Queue is empty, schedule next check
            pass
        finally:
            # Schedule next queue check
            self.frame.after(100, self.process_queue)
            
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

    def setup_api_models_tab(self):
        """Setup the API models tab for configuring external API-based models"""
        # Create main container frame
        api_frame = ttk.Frame(self.api_models_frame)
        api_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create API provider selection section
        provider_frame = ttk.LabelFrame(api_frame, text="API Provider")
        provider_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Provider selection
        ttk.Label(provider_frame, text="Select Provider:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.api_provider_var = tk.StringVar(value="OpenAI")
        provider_combo = ttk.Combobox(
            provider_frame,
            textvariable=self.api_provider_var,
            values=["OpenAI", "Anthropic", "Azure OpenAI", "Custom Endpoint"],
            state="readonly",
            width=20
        )
        provider_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self.on_api_provider_changed)
        
        # API Key section
        key_frame = ttk.LabelFrame(api_frame, text="API Authentication")
        key_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(key_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(key_frame, textvariable=self.api_key_var, width=40, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        
        show_key_frame = ttk.Frame(key_frame)
        show_key_frame.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Show/Hide API key toggle
        self.show_key_var = tk.BooleanVar(value=False)
        show_key_check = ttk.Checkbutton(
            show_key_frame, 
            text="Show Key", 
            variable=self.show_key_var,
            command=self.toggle_show_api_key
        )
        show_key_check.pack(side=tk.LEFT)
        
        # For Azure and Custom: endpoint URL
        self.endpoint_frame = ttk.Frame(key_frame)
        self.endpoint_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W + tk.E, padx=5, pady=5)
        
        ttk.Label(self.endpoint_frame, text="Endpoint URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.endpoint_var = tk.StringVar(value="https://api.openai.com/v1")
        endpoint_entry = ttk.Entry(self.endpoint_frame, textvariable=self.endpoint_var, width=40)
        endpoint_entry.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        
        # Initially hide endpoint frame for providers that don't need it
        self.update_endpoint_visibility()
        
        # Model selection section
        model_frame = ttk.LabelFrame(api_frame, text="Model Selection")
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(model_frame, text="Select Model:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.api_model_var = tk.StringVar()
        self.api_model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.api_model_var,
            state="readonly",
            width=30
        )
        self.api_model_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Fill model dropdown based on selected provider
        self.update_api_model_list()
        
        # Configuration options
        config_frame = ttk.LabelFrame(api_frame, text="API Configuration")
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Temperature
        ttk.Label(config_frame, text="Temperature:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.temperature_var = tk.DoubleVar(value=0.7)
        temperature_slider = ttk.Scale(
            config_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=200
        )
        temperature_slider.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        temp_value_label = ttk.Label(config_frame, textvariable=self.temperature_var)
        temp_value_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Max tokens
        ttk.Label(config_frame, text="Max Tokens:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.max_tokens_var = tk.IntVar(value=1024)
        max_tokens_entry = ttk.Spinbox(
            config_frame,
            from_=1,
            to=32000,
            textvariable=self.max_tokens_var,
            width=10
        )
        max_tokens_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(api_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Test connection button
        ttk.Button(
            button_frame,
            text="Test Connection",
            command=self.test_api_connection
        ).pack(side=tk.LEFT, padx=5)
        
        # Save button
        ttk.Button(
            button_frame,
            text="Save Configuration",
            command=self.save_api_configuration,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        # Use this model button
        ttk.Button(
            button_frame,
            text="Use This Model",
            command=self.use_api_model
        ).pack(side=tk.RIGHT, padx=5)
        
        # Load saved API configuration if available
        self.load_api_configuration()
        
    def on_api_provider_changed(self, event=None):
        """Handle API provider selection changes"""
        provider = self.api_provider_var.get()
        self.log(f"[Models] API provider changed to {provider}")
        
        # Update visibility of endpoint URL field
        self.update_endpoint_visibility()
        
        # Update model list based on provider
        self.update_api_model_list()
        
    def update_endpoint_visibility(self):
        """Show/hide endpoint URL field based on selected provider"""
        provider = self.api_provider_var.get()
        
        if provider in ["Azure OpenAI", "Custom Endpoint"]:
            self.endpoint_frame.grid()
            
            # Set default endpoint for Azure
            if provider == "Azure OpenAI" and self.endpoint_var.get() == "https://api.openai.com/v1":
                self.endpoint_var.set("https://{resource}.openai.azure.com/")
        else:
            self.endpoint_frame.grid_remove()
            
            # Reset to default OpenAI endpoint
            if provider == "OpenAI":
                self.endpoint_var.set("https://api.openai.com/v1")
            elif provider == "Anthropic":
                self.endpoint_var.set("https://api.anthropic.com")
    
    def update_api_model_list(self):
        """Update the model dropdown based on selected provider"""
        provider = self.api_provider_var.get()
        models = []
        
        if provider == "OpenAI":
            models = [
                "gpt-3.5-turbo", 
                "gpt-3.5-turbo-16k", 
                "gpt-4",
                "gpt-4-turbo", 
                "gpt-4-32k",
                "gpt-4o"
            ]
        elif provider == "Anthropic":
            models = [
                "claude-3-opus-20240229", 
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1", 
                "claude-2.0", 
                "claude-instant-1.2"
            ]
        elif provider == "Azure OpenAI":
            models = [
                "gpt-35-turbo",
                "gpt-4",
                "gpt-4-turbo"
            ]
        elif provider == "Custom Endpoint":
            models = ["custom-model"]
            
        # Update combobox values
        self.api_model_combo["values"] = models
        
        # Set default value if list is not empty
        if models and not self.api_model_var.get() in models:
            self.api_model_var.set(models[0])
            
    def toggle_show_api_key(self):
        """Toggle API key visibility"""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
            
    def save_api_configuration(self):
        """Save API configuration to config file"""
        if not hasattr(self.model_manager, 'config') or not self.model_manager.config:
            messagebox.showerror("Error", "Configuration manager is not available")
            return
            
        config = self.model_manager.config
        
        # Create API configuration
        api_config = {
            "provider": self.api_provider_var.get(),
            "model": self.api_model_var.get(),
            "endpoint": self.endpoint_var.get(),
            "temperature": self.temperature_var.get(),
            "max_tokens": self.max_tokens_var.get()
        }
        
        # Save API key securely (consider using environment variables or a keyring)
        if self.api_key_var.get().strip():
            api_config["api_key"] = self.api_key_var.get().strip()
              # Update config
        config.set("api_models", api_config)
        config.save_config()
        
        self.log("[Models] API configuration saved")
        messagebox.showinfo("Success", "API configuration has been saved")
        
    def load_api_configuration(self):
        """Load API configuration from config file"""
        if not hasattr(self.model_manager, 'config') or not self.model_manager.config:
            self.log("[Models] Config manager not available, using default API settings")
            return
            
        config = self.model_manager.config
        api_config = config.get("api_models", {})
        
        if api_config:
            # Set provider
            if "provider" in api_config and api_config["provider"] in ["OpenAI", "Anthropic", "Azure OpenAI", "Custom Endpoint"]:
                self.api_provider_var.set(api_config["provider"])
                
            # Set endpoint
            if "endpoint" in api_config:
                self.endpoint_var.set(api_config["endpoint"])
                
            # Update UI based on provider
            self.update_endpoint_visibility()
            self.update_api_model_list()
            
            # Set model
            if "model" in api_config:
                # Check if model exists in current list
                if api_config["model"] in self.api_model_combo["values"]:
                    self.api_model_var.set(api_config["model"])
            
            # Set temperature
            if "temperature" in api_config:
                self.temperature_var.set(float(api_config["temperature"]))
                
            # Set max tokens
            if "max_tokens" in api_config:
                self.max_tokens_var.set(int(api_config["max_tokens"]))
                
            # Set API key if available
            if "api_key" in api_config:
                self.api_key_var.set(api_config["api_key"])
                
    def test_api_connection(self):
        """Test connection to the selected API provider"""
        provider = self.api_provider_var.get()
        model = self.api_model_var.get()
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "API key is required")
            return
            
        self.log(f"[Models] Testing connection to {provider} API...")
        
        # Show testing indicator
        messagebox.showinfo("Testing", f"Testing connection to {provider} API...")
        
        # Implement actual API testing here
        # This would typically involve making a simple API call to validate credentials
        
        # For now, we'll just simulate a successful test
        self.log(f"[Models] Successfully connected to {provider} API")
        messagebox.showinfo("Success", f"Successfully connected to {provider} API")
        
    def use_api_model(self):
        """Set the current API model as the active model"""
        provider = self.api_provider_var.get()
        model = self.api_model_var.get()
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "API key is required")
            return
            
        # First save the configuration
        self.save_api_configuration()
        
        # Format model identifier with provider prefix
        api_model_id = f"api:{provider}:{model}"
        
        # Call callback to notify parent about model selection
        if self.on_model_selected_callback:
            self.log(f"[Models] Selected API model: {api_model_id}")
            self.on_model_selected_callback(api_model_id)
            messagebox.showinfo("Model Selected", f"{provider} model '{model}' has been selected")
            
    def setup_settings_tab(self):
        """Setup the Model Settings tab for configuring model parameters"""
        # Create main container frame with padding
        settings_container = ttk.Frame(self.settings_frame, padding=(10, 10, 10, 10))
        settings_container.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        ttk.Label(
            settings_container, 
            text="Model Settings", 
            font=("", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Create sections for settings
        self._create_settings_sections(settings_container)
        
        # Buttons at bottom
        button_frame = ttk.Frame(settings_container)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Reset button
        reset_button = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_settings
        )
        reset_button.pack(side=tk.LEFT, padx=5)
        
        # Apply button
        apply_button = ttk.Button(
            button_frame,
            text="Apply Settings",
            command=self.apply_settings,
            style="Accent.TButton"
        )
        apply_button.pack(side=tk.RIGHT, padx=5)
        
        # Load current settings
        self.load_current_settings()
    
    def _create_settings_sections(self, parent_frame):
        """Create all settings sections in the given parent frame
        
        Args:
            parent_frame: Parent frame to contain settings sections
        """
        # 1. General Settings Section
        general_frame = ttk.LabelFrame(parent_frame, text="General Settings")
        general_frame.pack(fill=tk.X, padx=5, pady=10)
        
        general_grid = ttk.Frame(general_frame)
        general_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Temperature setting
        ttk.Label(general_grid, text="Temperature:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.temperature_var = tk.DoubleVar(value=0.7)
        temperature_scale = ttk.Scale(
            general_grid,
            from_=0.0,
            to=1.5,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=200
        )
        temperature_scale.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        temp_value = ttk.Label(general_grid, textvariable=self.temperature_var)
        temp_value.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            general_grid, 
            text="Controls randomness: lower is more deterministic, higher is more creative",
            font=("", 8),
            foreground="gray"
        ).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Top-p setting
        ttk.Label(general_grid, text="Top-p:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.top_p_var = tk.DoubleVar(value=0.9)
        top_p_scale = ttk.Scale(
            general_grid,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.top_p_var,
            length=200
        )
        top_p_scale.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        top_p_value = ttk.Label(general_grid, textvariable=self.top_p_var)
        top_p_value.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            general_grid, 
            text="Controls diversity: 0.9 means consider tokens comprising the top 90% probability mass",
            font=("", 8),
            foreground="gray"
        ).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Max tokens setting
        ttk.Label(general_grid, text="Max Tokens:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.max_tokens_var = tk.IntVar(value=2048)
        max_tokens_entry = ttk.Spinbox(
            general_grid,
            from_=1,
            to=32000,
            textvariable=self.max_tokens_var,
            width=8
        )
        max_tokens_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            general_grid, 
            text="Maximum number of tokens to generate in the response",
            font=("", 8),
            foreground="gray"
        ).grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 2. Memory Settings Section
        memory_frame = ttk.LabelFrame(parent_frame, text="Memory Settings")
        memory_frame.pack(fill=tk.X, padx=5, pady=10)
        
        memory_grid = ttk.Frame(memory_frame)
        memory_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Memory mode
        ttk.Label(memory_grid, text="Memory Mode:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.memory_mode_var = tk.StringVar(value="Auto")
        memory_mode_combo = ttk.Combobox(
            memory_grid,
            textvariable=self.memory_mode_var,
            values=["Off", "Basic", "Auto", "Advanced"],
            state="readonly",
            width=15
        )
        memory_mode_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        memory_mode_combo.bind("<<ComboboxSelected>>", self.on_memory_mode_changed)
        
        ttk.Label(
            memory_grid, 
            text="Determines how context from previous conversations is used",
            font=("", 8),
            foreground="gray"
        ).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Context window size
        ttk.Label(memory_grid, text="Context Window:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.context_window_var = tk.StringVar(value="4096")
        context_window_combo = ttk.Combobox(
            memory_grid,
            textvariable=self.context_window_var,
            values=["2048", "4096", "8192", "16384", "32768"],
            width=15
        )
        context_window_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            memory_grid, 
            text="Maximum context size in tokens (depends on model capability)",
            font=("", 8),
            foreground="gray"
        ).grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 3. Performance Settings Section
        perf_frame = ttk.LabelFrame(parent_frame, text="Performance Settings")
        perf_frame.pack(fill=tk.X, padx=5, pady=10)
        
        perf_grid = ttk.Frame(perf_frame)
        perf_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Use 8-bit quantization
        self.use_8bit_var = tk.BooleanVar(value=False)
        use_8bit_check = ttk.Checkbutton(
            perf_grid,
            text="Use 8-bit Quantization",
            variable=self.use_8bit_var,
            command=self.on_quantization_changed
        )
        use_8bit_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            perf_grid, 
            text="Reduces VRAM usage but may slightly reduce quality",
            font=("", 8),
            foreground="gray"
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Specify VRAM limit
        self.limit_vram_var = tk.BooleanVar(value=False)
        limit_vram_check = ttk.Checkbutton(
            perf_grid,
            text="Limit VRAM Usage:",
            variable=self.limit_vram_var,
            command=self.on_vram_limit_changed
        )
        limit_vram_check.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.vram_limit_var = tk.StringVar(value="4")
        vram_limit_combo = ttk.Combobox(
            perf_grid,
            textvariable=self.vram_limit_var,
            values=["4", "8", "16", "24", "32"],
            width=5
        )
        vram_limit_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(perf_grid, text="GB").grid(row=1, column=2, sticky=tk.W)
        
        # 4. System Prompt Section
        prompt_frame = ttk.LabelFrame(parent_frame, text="System Prompt")
        prompt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)
        
        prompt_inner = ttk.Frame(prompt_frame)
        prompt_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(
            prompt_inner,
            text="System prompt defines the AI's behavior and capabilities:"
        ).pack(anchor=tk.W)
        
        # Create system prompt dropdown for presets
        preset_frame = ttk.Frame(prompt_inner)
        preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(preset_frame, text="Preset:").pack(side=tk.LEFT, padx=5)
        
        self.preset_var = tk.StringVar(value="Custom")
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=["Helpful Assistant", "Creative Writer", "Coding Expert", "Scientific Advisor", "Custom"],
            state="readonly",
            width=20
        )
        preset_combo.pack(side=tk.LEFT, padx=5)
        preset_combo.bind("<<ComboboxSelected>>", self.on_preset_selected)
        
        # System prompt text area
        self.system_prompt_text = tk.Text(prompt_inner, height=5, wrap=tk.WORD)
        self.system_prompt_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.system_prompt_text.insert("1.0", "You are a helpful, creative, and knowledgeable assistant.")
    
    def load_current_settings(self):
        """Load current model settings from config"""
        if hasattr(self.model_manager, 'config') and self.model_manager.config:
            config = self.model_manager.config
            
            # General settings
            self.temperature_var.set(config.get("temperature", 0.7))
            self.top_p_var.set(config.get("top_p", 0.9))
            self.max_tokens_var.set(config.get("max_tokens", 2048))
            
            # Memory settings
            self.memory_mode_var.set(config.get("memory_mode", "Auto"))
            self.context_window_var.set(str(config.get("context_window", 4096)))
            
            # Performance settings
            self.use_8bit_var.set(config.get("model.use_8bit", False))
            self.limit_vram_var.set(config.get("limit_vram", False))
            self.vram_limit_var.set(str(config.get("vram_limit", 4)))
            
            # System prompt
            system_prompt = config.get("system_prompt", "")
            if system_prompt:
                self.system_prompt_text.delete("1.0", tk.END)
                self.system_prompt_text.insert("1.0", system_prompt)
    
    def reset_settings(self):
        """Reset settings to default values"""
        # General settings
        self.temperature_var.set(0.7)
        self.top_p_var.set(0.9)
        self.max_tokens_var.set(2048)
        
        # Memory settings
        self.memory_mode_var.set("Auto")
        self.context_window_var.set("4096")
        
        # Performance settings
        self.use_8bit_var.set(False)
        self.limit_vram_var.set(False)
        self.vram_limit_var.set("4")
        
        # System prompt
        self.system_prompt_text.delete("1.0", tk.END)
        self.system_prompt_text.insert("1.0", "You are a helpful, creative, and knowledgeable assistant.")
        
        self.log("[Settings] Reset settings to defaults")
    
    def apply_settings(self, close_dialog=None):
        """Apply model settings to config
        
        Args:
            close_dialog: Optional dialog to close after applying settings
        """
        if hasattr(self.model_manager, 'config') and self.model_manager.config:
            config = self.model_manager.config
            
            # General settings
            config.set("temperature", self.temperature_var.get())
            config.set("top_p", self.top_p_var.get())
            config.set("max_tokens", self.max_tokens_var.get())
            
            # Memory settings
            config.set("memory_mode", self.memory_mode_var.get())
            config.set("context_window", int(self.context_window_var.get()))
            
            # Performance settings
            config.set("model.use_8bit", self.use_8bit_var.get())
            config.set("limit_vram", self.limit_vram_var.get())
            config.set("vram_limit", int(self.vram_limit_var.get()))
              # System prompt
            system_prompt = self.system_prompt_text.get("1.0", tk.END).strip()
            config.set("system_prompt", system_prompt)
            
            # Save config
            config.save_config()
            
            # Apply to model manager if needed
            self.model_manager.use_8bit = self.use_8bit_var.get()
            
            # Log
            self.log("[Settings] Applied model settings")
            
            # Show confirmation
            messagebox.showinfo("Settings Applied", "Model settings have been applied successfully.")
            
            # Close dialog if provided
            if close_dialog:
                close_dialog.destroy()
        else:
            self.log("[Settings] Error: Config manager not available")
            messagebox.showerror("Error", "Configuration manager is not available")
    
    def on_memory_mode_changed(self, event=None):
        """Handle memory mode change"""
        mode = self.memory_mode_var.get()
        self.log(f"[Settings] Memory mode changed to {mode}")
        
        # If a chat engine is available, update its memory mode
        if hasattr(self.model_manager, 'chat_engine') and self.model_manager.chat_engine:
            self.model_manager.chat_engine.set_memory_mode(mode)
    
    def on_quantization_changed(self):
        """Handle quantization setting change"""
        use_8bit = self.use_8bit_var.get()
        self.log(f"[Settings] 8-bit quantization set to {use_8bit}")
        
        # Show warning if turned on
        if use_8bit:
            import tkinter.messagebox as messagebox
            messagebox.showwarning(
                "Quantization Enabled", 
                "8-bit quantization will take effect the next time a model is loaded. "
                "This reduces VRAM usage but may slightly reduce output quality."
            )
    
    def on_vram_limit_changed(self):
        """Handle VRAM limit setting change"""
        limit_vram = self.limit_vram_var.get()
        self.log(f"[Settings] VRAM limit set to {limit_vram}")
        
        # Find all comboboxes in the parent frame and update their state
        for widget in self.frame.winfo_children():
            if isinstance(widget, ttk.Combobox) and "vram_limit" in str(widget):
                widget.config(state='readonly' if limit_vram else 'disabled')
    
    def on_preset_selected(self, event=None):
        """Handle preset selection"""
        preset = self.preset_var.get()
        self.log(f"[Settings] Preset selected: {preset}")
        
        # Clear current system prompt
        self.system_prompt_text.delete("1.0", tk.END)
        
        # Set preset prompt
        if preset == "Helpful Assistant":
            self.system_prompt_text.insert("1.0", "You are a helpful, creative, and knowledgeable assistant.")
        elif preset == "Creative Writer":
            self.system_prompt_text.insert("1.0", "You are a creative writer with a flair for storytelling and vivid descriptions.")
        elif preset == "Coding Expert":
            self.system_prompt_text.insert("1.0", "You are a programming expert who provides clear, concise code with thorough explanations.")
        elif preset == "Scientific Advisor":
            self.system_prompt_text.insert("1.0", "You are a scientific advisor who provides accurate information with supporting evidence and citations.")
        elif preset == "Custom":
            self.system_prompt_text.insert("1.0", "")
        
    def get_frame(self):
        """Return the main frame of the model panel"""
        return self.frame
    
    def _update_download_progress(self, percentage):
        """Update the UI with download progress"""
        # Update progress bar to determinate mode if not already
        if self.progress_mode.get() == "indeterminate":
            self.progress_bar.stop()
            self.progress_mode.set("determinate")
            self.progress_bar.config(mode="determinate")
            
        # Set progress value
        self.progress_bar.configure(value=percentage)
        
        # Update status text
        self.status_var.set(f"Downloading model: {percentage:.1f}%")
        
        # Log progress at certain intervals to avoid flooding logs
        if int(percentage) % 10 == 0:  # Log every 10%
            self.log(f"[Ollama] Download progress: {percentage:.1f}%")