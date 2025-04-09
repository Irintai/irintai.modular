"""
Model panel UI component for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Callable, Dict, List, Any, Optional

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
        
        # Initialize UI components
        self.initialize_ui()
        
        # Fetch models
        self.refresh_model_list()
        
    def initialize_ui(self):
        """Initialize the UI components"""
        # Create model selection section
        self.create_model_selection()
        
        # Create model management section
        self.create_model_management()
        
        # Create model information section
        self.create_model_info()
        
        # Create progress bar
        self.create_progress_bar()
        
    def create_model_selection(self):
        """Create the model selection section"""
        selection_frame = ttk.LabelFrame(self.frame, text="Model Selection")
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
        
    def create_model_management(self):
        """Create the model management section"""
        mgmt_frame = ttk.LabelFrame(self.frame, text="Model Management")
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
        
    def create_model_info(self):
        """Create the model information section"""
        info_frame = ttk.LabelFrame(self.frame, text="Model Information")
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
            
            # Update UI on main thread
            self.frame.after(0, lambda: self._update_model_tree(all_models))
        except Exception as e:
            self.log(f"[Error] Failed to fetch models: {e}")
            self.frame.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
        finally:
            # Reset progress bar
            self.frame.after(0, lambda: self._reset_progress_bar())
            
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
                
        # Start the model
        success = self.model_manager.start_model(model_name, on_model_event)
        
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