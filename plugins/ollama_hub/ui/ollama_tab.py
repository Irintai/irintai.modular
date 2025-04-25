"""
Ollama Hub Tab UI Component

This module provides a tab component for browsing and managing Ollama models
in the Irintai Assistant interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import re
import time
from typing import Dict, Any, List, Optional, Callable

class OllamaHubTab:
    """
    UI Component for Ollama Hub functionality
    
    Provides a tab in the Irintai interface for browsing and managing Ollama models.
    """
    
    def __init__(self, parent, plugin_instance=None):
        """
        Initialize the Ollama Hub Tab
        
        Args:
            parent: Parent frame/notebook
            plugin_instance: Instance of the Ollama Hub plugin
        """
        self.parent = parent
        self.plugin = plugin_instance
        
        # Check if plugin is available
        if not self.plugin:
            raise ValueError("Ollama Hub plugin instance is required")
        
        # Create update queue for thread-safe UI updates
        self.update_queue = None
        if hasattr(parent, 'update_queue'):
            self.update_queue = parent.update_queue
        
        # UI state variables
        self.ollama_url_var = tk.StringVar(value=self.plugin._config.get("server_url", "http://localhost:11434"))
        self.ollama_status_var = tk.StringVar(value=self.plugin._state.get("connection_status", "Not connected"))
        self.ollama_search_var = tk.StringVar()
        self.ollama_category_var = tk.StringVar(value="All")
        self.ollama_selected_model_var = tk.StringVar(value="None")
        self.ollama_model_desc_var = tk.StringVar(value="")
        
        # Model data
        self.local_models = {}
        self.library_models = []
        
        # Setup UI components
        self.setup_ui()
        
        # Subscribe to plugin events
        if hasattr(self.plugin.core, 'event_bus'):
            subscriber_id = f"ollama_hub_tab_{id(self)}"
            self.plugin.core.event_bus.subscribe(
                f"{self.plugin.plugin_id}.models_updated",
                self._on_models_updated,
                subscriber_id
            )
            self.plugin.core.event_bus.subscribe(
                f"{self.plugin.plugin_id}.download_progress",
                self._on_download_progress,
                subscriber_id
            )
            self.plugin.core.event_bus.subscribe(
                f"{self.plugin.plugin_id}.model_downloaded",
                self._on_model_downloaded,
                subscriber_id
            )
            self.plugin.core.event_bus.subscribe(
                f"{self.plugin.plugin_id}.model_deleted",
                self._on_model_deleted,
                subscriber_id
            )
    
    def setup_ui(self):
        """
        Set up the UI components for the Ollama Hub tab
        """
        # Create main container frame with padding
        self.frame = ttk.Frame(self.parent, padding=(10, 10, 10, 10))
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create connection section
        connection_frame = ttk.LabelFrame(self.frame, text="Ollama Connection")
        connection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create connection controls
        conn_grid = ttk.Frame(connection_frame)
        conn_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Server URL
        ttk.Label(conn_grid, text="Server URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        url_entry = ttk.Entry(conn_grid, textvariable=self.ollama_url_var, width=30)
        url_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Connection status
        ttk.Label(conn_grid, text="Status:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        status_label = ttk.Label(conn_grid, textvariable=self.ollama_status_var)
        status_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Connect button
        connect_button = ttk.Button(
            conn_grid, 
            text="Connect", 
            command=self._on_connect_button_clicked
        )
        connect_button.grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        # Create available models section with list and search
        models_frame = ttk.LabelFrame(self.frame, text="Available Models")
        models_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create search and filter options
        filter_frame = ttk.Frame(models_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(filter_frame, textvariable=self.ollama_search_var, width=25)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.filter_models)
        
        # Category filter
        ttk.Label(filter_frame, text="Category:").pack(side=tk.LEFT, padx=(20, 5))
        categories = ["All", "Small", "Medium", "Large", "Multimodal", "Code", "Vision"]
        category_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.ollama_category_var,
            values=categories,
            state="readonly",
            width=15
        )
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind("<<ComboboxSelected>>", self.filter_models)
        
        # Refresh button
        ttk.Button(
            filter_frame,
            text="Refresh List",
            command=self._on_refresh_button_clicked
        ).pack(side=tk.RIGHT, padx=5)
        
        # Model list with columns for name, size, tags, parameters
        columns = ("Name", "Size", "Parameters", "Tags")
        self.model_tree = ttk.Treeview(
            models_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=10
        )
        
        # Configure columns
        self.model_tree.heading("Name", text="Model Name")
        self.model_tree.heading("Size", text="Size")
        self.model_tree.heading("Parameters", text="Parameters")
        self.model_tree.heading("Tags", text="Tags")
        
        self.model_tree.column("Name", width=200, anchor=tk.W)
        self.model_tree.column("Size", width=80, anchor=tk.CENTER)
        self.model_tree.column("Parameters", width=100, anchor=tk.CENTER)
        self.model_tree.column("Tags", width=200, anchor=tk.W)
        
        # Add scrollbar
        model_list_frame = ttk.Frame(models_frame)
        model_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(model_list_frame, orient=tk.VERTICAL, command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.model_tree.bind("<<TreeviewSelect>>", self.on_model_selected)
        
        # Model detail section
        detail_frame = ttk.LabelFrame(self.frame, text="Model Details")
        detail_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a frame for model details
        model_detail_grid = ttk.Frame(detail_frame)
        model_detail_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Selected model info
        ttk.Label(model_detail_grid, text="Selected:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(model_detail_grid, textvariable=self.ollama_selected_model_var, font=("", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(model_detail_grid, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(model_detail_grid, textvariable=self.ollama_model_desc_var, wraplength=400).grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        # Progress bar for downloads
        ttk.Label(model_detail_grid, text="Progress:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            model_detail_grid,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.grid(row=2, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=2)
        
        # Model actions
        action_frame = ttk.Frame(self.frame)
        action_frame.pack(fill=tk.X, padx=5, pady=(10, 5))
        
        # Download button
        self.download_btn = ttk.Button(
            action_frame,
            text="Download Model",
            command=self._on_download_button_clicked
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)
        self.download_btn.state(['disabled'])
        
        # Delete model button
        self.delete_btn = ttk.Button(
            action_frame,
            text="Delete Model",
            command=self._on_delete_button_clicked
        )
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        self.delete_btn.state(['disabled'])
        
        # Use model button
        self.use_btn = ttk.Button(
            action_frame,
            text="Use Selected Model",
            command=self._on_use_button_clicked,
            style="Accent.TButton" if hasattr(ttk, "Accent.TButton") else ""
        )
        self.use_btn.pack(side=tk.RIGHT, padx=5)
        self.use_btn.state(['disabled'])
        
        # Advanced options button
        self.options_btn = ttk.Button(
            action_frame,
            text="Advanced Options",
            command=self._on_options_button_clicked
        )
        self.options_btn.pack(side=tk.RIGHT, padx=5)
        self.options_btn.state(['disabled'])
        
        # Try to connect to Ollama automatically after a short delay
        self.frame.after(500, self._on_connect_button_clicked)
    
    def _on_connect_button_clicked(self):
        """
        Handle connect button click
        """
        # Update server URL in plugin config
        url = self.ollama_url_var.get().strip()
        if not url:
            self._show_error("No URL provided")
            return
        
        # Update status and config
        self.ollama_status_var.set("Connecting...")
        self.plugin.update_configuration(server_url=url)
        
        # Try to connect
        self.plugin.connect_to_ollama()
    
    def _on_refresh_button_clicked(self):
        """
        Handle refresh button click
        """
        # Fetch models from the plugin
        self.plugin.fetch_ollama_models()
    
    def _on_download_button_clicked(self):
        """
        Handle download button click
        """
        model_name = self.ollama_selected_model_var.get()
        if model_name == "None":
            return
            
        # Reset progress
        self.progress_var.set(0)
        
        # Disable download button during download
        self.download_btn.state(['disabled'])
        
        # Start download
        self.plugin.download_ollama_model(model_name)
    
    def _on_delete_button_clicked(self):
        """
        Handle delete button click
        """
        model_name = self.ollama_selected_model_var.get()
        if model_name == "None":
            return
        
        # Confirm deletion
        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete model {model_name}?"
        ):
            return
            
        # Disable delete button during deletion
        self.delete_btn.state(['disabled'])
        
        # Start deletion
        self.plugin.delete_ollama_model(model_name)
    
    def _on_use_button_clicked(self):
        """
        Handle use button click
        """
        model_name = self.ollama_selected_model_var.get()
        if model_name == "None":
            return
        
        # Check if model_manager exists in the core system
        if hasattr(self.plugin.core, 'model_manager'):
            model_manager = self.plugin.core.model_manager
            
            # Check if model_manager has select_model method
            if hasattr(model_manager, 'select_model'):
                # Call select_model method to use the selected model
                model_manager.select_model(f"ollama:{model_name}")
                messagebox.showinfo(
                    "Model Selected",
                    f"Model {model_name} has been selected for use."
                )
            else:
                self._show_error("Model manager does not support model selection")
        else:
            self._show_error("Model manager not available in the core system")
    
    def _on_options_button_clicked(self):
        """
        Handle advanced options button click
        """
        model_name = self.ollama_selected_model_var.get()
        if model_name == "None":
            return
            
        # Create options dialog
        options_dialog = tk.Toplevel(self.parent)
        options_dialog.title(f"Advanced Options for {model_name}")
        options_dialog.geometry("400x300")
        options_dialog.transient(self.parent)
        options_dialog.grab_set()
        
        # Create options form
        options_frame = ttk.Frame(options_dialog, padding=(20, 20))
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Temperature
        ttk.Label(options_frame, text="Temperature:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        temp_var = tk.DoubleVar(value=0.8)
        temp_scale = ttk.Scale(
            options_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=temp_var,
            length=200
        )
        temp_scale.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(options_frame, textvariable=temp_var).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Context size
        ttk.Label(options_frame, text="Context Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        context_var = tk.IntVar(value=4096)
        context_entry = ttk.Entry(options_frame, textvariable=context_var, width=10)
        context_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Threads
        ttk.Label(options_frame, text="Threads:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        threads_var = tk.IntVar(value=4)
        threads_entry = ttk.Entry(options_frame, textvariable=threads_var, width=10)
        threads_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # GPU Layers
        ttk.Label(options_frame, text="GPU Layers:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        gpu_var = tk.StringVar(value="auto")
        gpu_entry = ttk.Entry(options_frame, textvariable=gpu_var, width=10)
        gpu_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Seed
        ttk.Label(options_frame, text="Seed:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        seed_var = tk.IntVar(value=0)
        seed_entry = ttk.Entry(options_frame, textvariable=seed_var, width=10)
        seed_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(options_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(
            button_frame, 
            text="Apply",
            command=lambda: self._apply_model_options(
                model_name,
                {
                    "temperature": temp_var.get(),
                    "context": context_var.get(),
                    "threads": threads_var.get(),
                    "gpu": gpu_var.get(),
                    "seed": seed_var.get()
                },
                options_dialog
            )
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=options_dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _apply_model_options(self, model_name, options, dialog):
        """
        Apply advanced model options
        
        Args:
            model_name: Name of the model
            options: Dictionary of model options
            dialog: Options dialog to close after applying
        """
        # Check if model_manager exists in the core system
        if hasattr(self.plugin.core, 'model_manager'):
            model_manager = self.plugin.core.model_manager
            
            # Check if model_manager has configure_model method
            if hasattr(model_manager, 'configure_model'):
                # Call configure_model method to apply options
                model_manager.configure_model(f"ollama:{model_name}", options)
                messagebox.showinfo(
                    "Options Applied",
                    f"Advanced options have been applied to {model_name}."
                )
                dialog.destroy()
            else:
                self._show_error("Model manager does not support model configuration")
        else:
            self._show_error("Model manager not available in the core system")
    
    def on_model_selected(self, event=None):
        """
        Handle selection of a model in the tree view
        
        Args:
            event: Event object (optional)
        """
        selected_items = self.model_tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        values = self.model_tree.item(item, "values")
        tags = self.model_tree.item(item, "tags")

        # Get model name without the icon prefix
        model_name = values[0].replace("📂 ", "") if values[0].startswith("📂 ") else values[0]
        is_local = "local" in tags
        
        # Clean up model name if it has a download icon
        if model_name.startswith("📥"):
            model_name = model_name[1:]

        # Update selected model
        self.ollama_selected_model_var.set(model_name)

        # Update description based on model name
        if "code" in model_name.lower() or "coder" in model_name.lower():
            self.ollama_model_desc_var.set("A model fine-tuned for coding tasks and technical assistance.")
        elif "chat" in model_name.lower():
            self.ollama_model_desc_var.set("A conversational model designed for helpful dialogue.")
        else:
            self.ollama_model_desc_var.set("A general purpose language model.")

        # Update buttons based on model status
        if is_local:
            self.download_btn.state(['disabled'])
            self.delete_btn.state(['!disabled'])
            self.use_btn.state(['!disabled'])
            self.options_btn.state(['!disabled'])
        else:
            self.download_btn.state(['!disabled'])
            self.delete_btn.state(['disabled'])
            self.use_btn.state(['disabled'])
            self.options_btn.state(['disabled'])
    
    def filter_models(self, event=None):
        """
        Filter models based on search and category
        
        Args:
            event: Event object (optional)
        """
        search_term = self.ollama_search_var.get().lower()
        category = self.ollama_category_var.get()

        # Show all items
        for item in self.model_tree.get_children():
            self.model_tree.item(item, open=True)

            # Get values and tags
            values = self.model_tree.item(item, 'values')
            tags = self.model_tree.item(item, 'tags')
            
            model_name = values[0].replace("📂 ", "").lower() if values[0].startswith("📂 ") else values[0].lower()
            model_tags = values[3].lower()
            is_local = "local" in tags

            # Check if model matches search and category
            matches_search = search_term in model_name or search_term in model_tags
            matches_category = (
                category == "All" or
                (category == "Small" and "3b" in model_name or "7b" in model_name) or
                (category == "Medium" and "13b" in model_name or "15b" in model_name) or
                (category == "Large" and "30b" in model_name or "70b" in model_name) or
                (category == "Code" and ("code" in model_name or "coder" in model_name)) or
                (category == "Vision" and ("vision" in model_name or "vl" in model_name)) or
                (category == "Multimodal" and ("vision" in model_name or "multi" in model_name))
            )

            # If search term is empty, just filter by category
            if not search_term:
                matches_search = True

            # Show/hide based on matches
            if matches_search and matches_category:
                self.model_tree.item(item, tags=tags)  # Keep visible
            else:
                self.model_tree.detach(item)  # Hide
    
    def _on_models_updated(self, event_name, data, event_info=None):
        """
        Handle models updated event from plugin
        
        Args:
            event_name: Event name
            data: Event data
            event_info: Additional event info (optional)
        """
        # Update model data
        self.local_models = data.get("local_models", {})
        self.library_models = data.get("library_models", [])
        
        # Update UI on the main thread
        if self.update_queue:
            self.update_queue.put(lambda: self._update_models_ui())
        else:
            self._update_models_ui()
    
    def _update_models_ui(self):
        """
        Update the UI with model data
        """
        # Clear the tree
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
        
        # Track how many models we display
        local_count = 0
        remote_count = 0
        
        # First add local models
        for name, model in self.local_models.items():
            local_count += 1
            # Extract model details
            size = model.get('size', 'Unknown')
            if isinstance(size, int):
                # Convert size to human-readable format
                if size < 1024 * 1024:  # < 1MB
                    size_str = f"{size / 1024:.1f} KB"
                elif size < 1024 * 1024 * 1024:  # < 1GB
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                else:  # GB+
                    size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
            else:
                size_str = str(size)
                
            # Make a guess at parameters based on model name
            param_match = re.search(r'(\d+)b', name, re.IGNORECASE)
            parameters = f"{param_match.group(1)}B" if param_match else "Unknown"
            
            tags = model.get('tags', [])
            tag_str = ", ".join(tags) if tags else ""
            
            # Add to tree with local indicator
            self.model_tree.insert(
                "", tk.END, 
                values=(f"📂 {name}", size_str, parameters, tag_str),
                tags=["local"]
            )
        
        # Then add library models that aren't already local
        for model in self.library_models:
            if not model['is_local']:
                remote_count += 1

                # Get size information
                size_str = model.get('size', 'Remote')

                # Get parameter information
                parameters = model.get('parameters', 'Unknown')

                # Format tags
                tags = model.get('tags', [])
                # If no tags but we can infer from name
                if not tags:
                    if 'code' in model['name'].lower() or 'coder' in model['name'].lower():
                        tags.append('code')
                    if 'vision' in model['name'].lower() or 'vl' in model['name'].lower():
                        tags.append('vision')
                    if 'instruct' in model['name'].lower():
                        tags.append('instruct')

                tag_str = ", ".join(tags) if tags else ""

                # Add visual indicator for remote models
                self.model_tree.insert(
                    "", tk.END,
                    values=(f"📥{model['name']}", size_str, parameters, tag_str),
                    tags=["remote"] + (['recommended'] if 'recommended' in model and model['recommended'] else [])
                )

        # Apply visual styling based on tags
        for item in self.model_tree.get_children():
            tags = self.model_tree.item(item, 'tags')
            if 'recommended' in tags:
                # Use a different style for recommended models
                self.model_tree.item(item, tags=tags + ['highlighted'])
                
        # Update status in the plugin
        self.ollama_status_var.set(self.plugin._state.get("connection_status", "Unknown"))
    
    def _on_download_progress(self, event_name, data, event_info=None):
        """
        Handle download progress event from plugin
        
        Args:
            event_name: Event name
            data: Event data
            event_info: Additional event info (optional)
        """
        # Update progress on the main thread
        if self.update_queue:
            self.update_queue.put(lambda: self._update_download_progress(
                data.get("percentage", 0)
            ))
        else:
            self._update_download_progress(data.get("percentage", 0))
    
    def _update_download_progress(self, percentage):
        """
        Update the download progress bar
        
        Args:
            percentage: Download progress percentage
        """
        self.progress_var.set(percentage)
    
    def _on_model_downloaded(self, event_name, data, event_info=None):
        """
        Handle model downloaded event from plugin
        
        Args:
            event_name: Event name
            data: Event data
            event_info: Additional event info (optional)
        """
        # Update UI on the main thread
        if self.update_queue:
            self.update_queue.put(lambda: self._handle_download_completed(
                data.get("model", ""),
                data.get("success", False),
                data.get("error", "")
            ))
        else:
            self._handle_download_completed(
                data.get("model", ""),
                data.get("success", False),
                data.get("error", "")
            )
    
    def _handle_download_completed(self, model_name, success, error_message):
        """
        Handle completion of model download
        
        Args:
            model_name: Name of the model
            success: Whether download was successful
            error_message: Error message if unsuccessful
        """
        # Reset progress
        self.progress_var.set(0)
        
        # Re-enable download button
        self.download_btn.state(['!disabled'])
        
        # Show message
        if success:
            messagebox.showinfo(
                "Download Complete",
                f"Model {model_name} has been downloaded successfully."
            )
        else:
            self._show_error(f"Failed to download model {model_name}: {error_message}")
    
    def _on_model_deleted(self, event_name, data, event_info=None):
        """
        Handle model deleted event from plugin
        
        Args:
            event_name: Event name
            data: Event data
            event_info: Additional event info (optional)
        """
        # Update UI on the main thread
        if self.update_queue:
            self.update_queue.put(lambda: self._handle_deletion_completed(
                data.get("model", ""),
                data.get("success", False),
                data.get("error", "")
            ))
        else:
            self._handle_deletion_completed(
                data.get("model", ""),
                data.get("success", False),
                data.get("error", "")
            )
    
    def _handle_deletion_completed(self, model_name, success, error_message):
        """
        Handle completion of model deletion
        
        Args:
            model_name: Name of the model
            success: Whether deletion was successful
            error_message: Error message if unsuccessful
        """
        # Re-enable delete button
        self.delete_btn.state(['!disabled'])
        
        # Show message
        if success:
            messagebox.showinfo(
                "Deletion Complete",
                f"Model {model_name} has been deleted successfully."
            )
        else:
            self._show_error(f"Failed to delete model {model_name}: {error_message}")
    
    def _show_error(self, message):
        """
        Show an error message
        
        Args:
            message: Error message to show
        """
        messagebox.showerror("Error", message)
