"""
Configuration panel UI component for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import sys
from typing import Callable, Dict, List, Any, Optional

class ConfigPanel:
    """Configuration panel for managing application settings"""

    def __init__(self, parent, config_manager, model_manager, memory_system, chat_engine, logger: Callable, on_config_updated: Callable):
        """
        Initialize the configuration panel

        Args:
            parent: Parent widget
            config_manager: ConfigManager instance
            model_manager: ModelManager instance
            memory_system: MemorySystem instance
            chat_engine: ChatEngine instance
            logger: Logging function
            on_config_updated: Callback for configuration updates
        """
        self.parent = parent
        self.config_manager = config_manager
        self.model_manager = model_manager
        self.memory_system = memory_system
        self.chat_engine = chat_engine
        self.log = logger
        self.on_config_updated_callback = on_config_updated

        # Create the main frame
        self.frame = ttk.Frame(parent)

        # Initialize dictionary for plugin settings widgets <<< ADD THIS LINE
        self.plugin_settings_widgets = {}

        # Initialize UI components
        self.initialize_ui()
        
    def initialize_ui(self):
        """Initialize the UI components"""
        # Create notebook for tabbed settings
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create general settings tab
        self.create_general_settings()
        
        # Create model settings tab
        self.create_model_settings()
        
        # Create memory settings tab
        self.create_memory_settings()
        
        # Create system settings tab
        self.create_system_settings()
        
        # Add save and reset buttons at the bottom
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Save All Settings",
            command=self.save_all_settings,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Apply Changes",
            command=self.apply_changes
        ).pack(side=tk.RIGHT, padx=5)
        
    def create_general_settings(self):
        """Create the general settings tab"""
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="General")
        
        # Create UI section
        ui_frame = ttk.LabelFrame(general_frame, text="UI Settings")
        ui_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Theme selection
        theme_frame = ttk.Frame(ui_frame)
        theme_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.theme_var = tk.StringVar(
            value=self.config_manager.get("theme", "Light")
        )
        theme_dropdown = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["Light", "Dark", "System"],
            state="readonly",
            width=15
        )
        theme_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Font size
        ttk.Label(theme_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.font_size_var = tk.StringVar(
            value=str(self.config_manager.get("font_size", 10))
        )
        font_size_spinbox = ttk.Spinbox(
            theme_frame,
            textvariable=self.font_size_var,
            from_=8,
            to=16,
            width=5
        )
        font_size_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Show debug messages
        self.show_debug_var = tk.BooleanVar(
            value=self.config_manager.get("show_debug_messages", False)
        )
        ttk.Checkbutton(
            theme_frame,
            text="Show Debug Messages",
            variable=self.show_debug_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # App behavior section
        behavior_frame = ttk.LabelFrame(general_frame, text="Behavior")
        behavior_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Auto-start last model
        self.auto_start_var = tk.BooleanVar(
            value=self.config_manager.get("auto_start_last_model", True)
        )
        ttk.Checkbutton(
            behavior_frame,
            text="Auto-start Last Used Model on Startup",
            variable=self.auto_start_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Auto-save session
        self.auto_save_var = tk.BooleanVar(
            value=self.config_manager.get("auto_save_session", True)
        )
        ttk.Checkbutton(
            behavior_frame,
            text="Auto-save Session on Exit",
            variable=self.auto_save_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # System prompt section
        prompt_frame = ttk.LabelFrame(general_frame, text="Default System Prompt")
        prompt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System prompt entry
        self.system_prompt_var = tk.StringVar(
            value=self.config_manager.get(
                "system_prompt", 
                "You are Irintai, a helpful and knowledgeable assistant."
            )
        )
        
        system_entry = ttk.Entry(
            prompt_frame,
            textvariable=self.system_prompt_var,
            width=70
        )
        system_entry.pack(fill=tk.X, padx=5, pady=5)
        
        # System prompt description
        ttk.Label(
            prompt_frame,
            text="This prompt will be used when starting a new conversation.",
            font=("Helvetica", 9, "italic")
        ).pack(anchor=tk.W, padx=5, pady=2)
        
    def create_model_settings(self):
        """Create the model settings tab"""
        model_frame = ttk.Frame(self.notebook)
        self.notebook.add(model_frame, text="Models")
        
        # Model path section
        path_frame = ttk.LabelFrame(model_frame, text="Model Storage")
        path_frame.pack(fill=tk.X, padx=10, pady=10)
        
        path_input_frame = ttk.Frame(path_frame)
        path_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(path_input_frame, text="Model Path:").pack(side=tk.LEFT)
        
        self.model_path_var = tk.StringVar(
            value=self.config_manager.get("model_path", "data/models")
        )
        path_entry = ttk.Entry(
            path_input_frame,
            textvariable=self.model_path_var,
            width=50
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(
            path_input_frame,
            text="Browse",
            command=self.browse_model_path
        ).pack(side=tk.LEFT)
        
        # Disk space info
        self.disk_frame = ttk.Frame(path_frame)
        self.disk_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.update_disk_space_info()
        
        ttk.Label(
            self.disk_frame,
            text="Note: Changing model path requires restart to take full effect.",
            font=("Helvetica", 9, "italic")
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Set system environment variable option
        system_var_frame = ttk.Frame(path_frame)
        system_var_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.set_sys_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            system_var_frame,
            text="Set OLLAMA_MODELS as system environment variable (recommended)",
            variable=self.set_sys_var
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            system_var_frame,
            text="Apply System Variable",
            command=self.set_system_variable
        ).pack(side=tk.LEFT, padx=5)
        
        # Model performance section
        perf_frame = ttk.LabelFrame(model_frame, text="Model Performance")
        perf_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 8-bit mode option
        self.use_8bit_var = tk.BooleanVar(
            value=self.config_manager.get("use_8bit", False)
        )
        ttk.Checkbutton(
            perf_frame,
            text="Enable 8-bit mode for large models (13B+)",
            variable=self.use_8bit_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Temperature setting
        temp_frame = ttk.Frame(perf_frame)
        temp_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(temp_frame, text="Temperature:").pack(side=tk.LEFT)
        
        self.temperature_var = tk.DoubleVar(
            value=self.config_manager.get("temperature", 0.7)
        )
        temp_scale = ttk.Scale(
            temp_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=200
        )
        temp_scale.pack(side=tk.LEFT, padx=5)
        
        temp_label = ttk.Label(temp_frame, textvariable=self.temperature_var, width=5)
        temp_label.pack(side=tk.LEFT)
        
        # Update temperature label when scale changes
        temp_scale.bind("<Motion>", lambda e: self.temperature_var.set(round(self.temperature_var.get(), 1)))
        
        # Temperature description
        ttk.Label(
            temp_frame,
            text="(Higher = more creative, Lower = more precise)",
            font=("Helvetica", 9, "italic")
        ).pack(side=tk.LEFT, padx=5)
        
        # Inference mode
        inference_frame = ttk.Frame(perf_frame)
        inference_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(inference_frame, text="Inference Mode:").pack(side=tk.LEFT)
        
        self.inference_mode_var = tk.StringVar(
            value=self.config_manager.get("inference_mode", "GPU")
        )
        mode_dropdown = ttk.Combobox(
            inference_frame,
            textvariable=self.inference_mode_var,
            values=["GPU", "CPU"],
            state="readonly",
            width=10
        )
        mode_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Mode description
        gpu_desc = "Use GPU acceleration if available (recommended)"
        cpu_desc = "Force CPU-only mode (slower but more compatible)"
        
        self.mode_desc_var = tk.StringVar(
            value=gpu_desc if self.inference_mode_var.get() == "GPU" else cpu_desc
        )
        
        ttk.Label(
            inference_frame,
            textvariable=self.mode_desc_var,
            font=("Helvetica", 9, "italic")
        ).pack(side=tk.LEFT, padx=5)
        
        # Update description when mode changes
        mode_dropdown.bind("<<ComboboxSelected>>", lambda e: self.mode_desc_var.set(
            gpu_desc if self.inference_mode_var.get() == "GPU" else cpu_desc
        ))
        
    def create_memory_settings(self):
        """Create the memory settings tab"""
        memory_frame = ttk.Frame(self.notebook)
        self.notebook.add(memory_frame, text="Memory")
        
        # Memory mode section
        mode_frame = ttk.LabelFrame(memory_frame, text="Memory Mode")
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Mode selection
        self.memory_mode_var = tk.StringVar(
            value=self.config_manager.get("memory_mode", "Off")
        )
        
        modes = [
            ("Off", "Memory not used for responses"),
            ("Manual", "Manual search only"),
            ("Auto", "Automatically adds context to prompts"),
            ("Background", "Silently adds context to all prompts")
        ]
        
        for i, (mode, desc) in enumerate(modes):
            frame = ttk.Frame(mode_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            radio = ttk.Radiobutton(
                frame,
                text=mode,
                variable=self.memory_mode_var,
                value=mode
            )
            radio.pack(side=tk.LEFT)
            
            ttk.Label(
                frame,
                text=f"- {desc}",
                font=("Helvetica", 9, "italic")
            ).pack(side=tk.LEFT, padx=5)
        
        # Vector store settings
        vector_frame = ttk.LabelFrame(memory_frame, text="Vector Store")
        vector_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Index path
        path_frame = ttk.Frame(vector_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(path_frame, text="Index Path:").pack(side=tk.LEFT)
        
        self.index_path_var = tk.StringVar(
            value=self.config_manager.get("index_path", "data/vector_store/vector_store.json")
        )
        index_entry = ttk.Entry(
            path_frame,
            textvariable=self.index_path_var,
            width=50
        )
        index_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(
            path_frame,
            text="Browse",
            command=self.browse_index_path
        ).pack(side=tk.LEFT)
        
        # Embedding model
        model_frame = ttk.Frame(vector_frame)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(model_frame, text="Embedding Model:").pack(side=tk.LEFT)
        
        self.embedding_model_var = tk.StringVar(
            value=self.config_manager.get("embedding_model", "all-MiniLM-L6-v2")
        )
        model_dropdown = ttk.Combobox(
            model_frame,
            textvariable=self.embedding_model_var,
            values=[
                "all-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "paraphrase-multilingual-MiniLM-L12-v2"
            ],
            state="readonly",
            width=30
        )
        model_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Search settings
        search_frame = ttk.LabelFrame(memory_frame, text="Search Settings")
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Result count
        count_frame = ttk.Frame(search_frame)
        count_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(count_frame, text="Default Results:").pack(side=tk.LEFT)
        
        self.result_count_var = tk.IntVar(
            value=self.config_manager.get("default_result_count", 5)
        )
        count_spinbox = ttk.Spinbox(
            count_frame,
            textvariable=self.result_count_var,
            from_=1,
            to=20,
            width=5
        )
        count_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Relevance threshold
        threshold_frame = ttk.Frame(search_frame)
        threshold_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(threshold_frame, text="Relevance Threshold:").pack(side=tk.LEFT)
        
        self.threshold_var = tk.DoubleVar(
            value=self.config_manager.get("relevance_threshold", 0.7)
        )
        threshold_scale = ttk.Scale(
            threshold_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            length=200
        )
        threshold_scale.pack(side=tk.LEFT, padx=5)
        
        threshold_label = ttk.Label(threshold_frame, textvariable=self.threshold_var, width=5)
        threshold_label.pack(side=tk.LEFT)
        
        # Update threshold label when scale changes
        threshold_scale.bind("<Motion>", lambda e: self.threshold_var.set(round(self.threshold_var.get(), 2)))
        
    def create_system_settings(self):
        """Create the system settings tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="System")
        
        # Logging settings
        log_frame = ttk.LabelFrame(system_frame, text="Logging")
        log_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Log file path
        log_path_frame = ttk.Frame(log_frame)
        log_path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(log_path_frame, text="Log Directory:").pack(side=tk.LEFT)
        
        self.log_dir_var = tk.StringVar(
            value=self.config_manager.get("log_dir", "data/logs")
        )
        log_entry = ttk.Entry(
            log_path_frame,
            textvariable=self.log_dir_var,
            width=50
        )
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(
            log_path_frame,
            text="Browse",
            command=self.browse_log_dir
        ).pack(side=tk.LEFT)
        
        # Log level
        log_level_frame = ttk.Frame(log_frame)
        log_level_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(log_level_frame, text="Log Level:").pack(side=tk.LEFT)
        
        self.log_level_var = tk.StringVar(
            value=self.config_manager.get("log_level", "INFO")
        )
        level_dropdown = ttk.Combobox(
            log_level_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly",
            width=10
        )
        level_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Max log size
        log_size_frame = ttk.Frame(log_frame)
        log_size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(log_size_frame, text="Max Log Size (MB):").pack(side=tk.LEFT)
        
        self.max_log_size_var = tk.IntVar(
            value=self.config_manager.get("max_log_size_mb", 10)
        )
        size_spinbox = ttk.Spinbox(
            log_size_frame,
            textvariable=self.max_log_size_var,
            from_=1,
            to=100,
            width=5
        )
        size_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Keep backup logs
        self.keep_logs_var = tk.BooleanVar(
            value=self.config_manager.get("keep_backup_logs", True)
        )
        ttk.Checkbutton(
            log_frame,
            text="Keep Backup Logs",
            variable=self.keep_logs_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Startup settings
        startup_frame = ttk.LabelFrame(system_frame, text="Startup & Shutdown")
        startup_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Check for updates
        self.check_updates_var = tk.BooleanVar(
            value=self.config_manager.get("check_updates", True)
        )
        ttk.Checkbutton(
            startup_frame,
            text="Check for Updates on Startup",
            variable=self.check_updates_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Start minimized
        self.start_minimized_var = tk.BooleanVar(
            value=self.config_manager.get("start_minimized", False)
        )
        ttk.Checkbutton(
            startup_frame,
            text="Start Minimized to System Tray",
            variable=self.start_minimized_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Confirm on exit
        self.confirm_exit_var = tk.BooleanVar(
            value=self.config_manager.get("confirm_exit", True)
        )
        ttk.Checkbutton(
            startup_frame,
            text="Confirm Before Exiting",
            variable=self.confirm_exit_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
    def update_disk_space_info(self):
        """Update the disk space information display"""
        path = self.model_path_var.get()
        
        try:
            # Get drive letter
            if os.name == 'nt':  # Windows
                drive = os.path.splitdrive(path)[0]
                if drive:
                    drive = drive + "\\"
                else:
                    drive = "C:\\"  # Default to C: if no drive letter found
            else:
                drive = "/"  # Unix root
                
            # Get disk space info
            import shutil
            usage = shutil.disk_usage(drive)
            free_space = round(usage.free / (1024**3), 2)  # Convert to GB
            total_space = round(usage.total / (1024**3), 2)  # Convert to GB
            
            # Set color based on free space
            color = "green" if free_space > 20 else "red"
            
            # Update label with disk space info
            if hasattr(self, 'disk_info_label'):
                self.disk_info_label.destroy()
                
            self.disk_info_label = ttk.Label(
                self.disk_frame,
                text=f"Free space on {drive}: {free_space} GB / {total_space} GB",
                foreground=color
            )
            self.disk_info_label.pack(anchor=tk.W, padx=5, pady=2)
        except Exception as e:
            if hasattr(self, 'disk_info_label'):
                self.disk_info_label.destroy()
                
            self.disk_info_label = ttk.Label(
                self.disk_frame,
                text=f"Error checking disk space: {e}",
                foreground="red"
            )
            self.disk_info_label.pack(anchor=tk.W, padx=5, pady=2)
            
    def browse_model_path(self):
        """Browse for model path"""
        path = filedialog.askdirectory(
            initialdir=self.model_path_var.get(),
            title="Select Model Directory"
        )
        
        if path:
            self.model_path_var.set(path)
            self.update_disk_space_info()
            
    def browse_index_path(self):
        """Browse for index path"""
        path = filedialog.asksaveasfilename(
            initialdir=os.path.dirname(self.index_path_var.get()),
            initialfile=os.path.basename(self.index_path_var.get()),
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Select Index File"
        )
        
        if path:
            self.index_path_var.set(path)
            
    def browse_log_dir(self):
        """Browse for log directory"""
        path = filedialog.askdirectory(
            initialdir=self.log_dir_var.get(),
            title="Select Log Directory"
        )
        
        if path:
            self.log_dir_var.set(path)
            
    def set_system_variable(self):
        """Set system environment variable for model path"""
        path = self.model_path_var.get()
        
        # Confirm action
        result = messagebox.askyesno(
            "Set System Variable",
            f"This will set OLLAMA_MODELS={path} as a system environment variable.\n\n"
            "This requires administrator privileges and may prompt for elevation.\n\n"
            "Do you want to continue?",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
            
        # Try to set the variable
        success = self.config_manager.set_system_path_var(path)
        
        if success:
            messagebox.showinfo(
                "System Variable Set",
                "Successfully set OLLAMA_MODELS system environment variable.\n\n"
                "You may need to restart your computer for the change to take full effect."
            )
        else:
            messagebox.showerror(
                "Error",
                "Failed to set system environment variable.\n\n"
                "This might be due to insufficient privileges."
            )
            
    def save_all_settings(self):
        """Save all settings to config"""
        # Collect all settings from UI
        config = {}
        
        # General settings
        config["theme"] = self.theme_var.get()
        config["font_size"] = int(self.font_size_var.get())
        config["show_debug_messages"] = self.show_debug_var.get()
        config["auto_start_last_model"] = self.auto_start_var.get()
        config["auto_save_session"] = self.auto_save_var.get()
        config["system_prompt"] = self.system_prompt_var.get()
        
        # Model settings
        config["model_path"] = self.model_path_var.get()
        config["use_8bit"] = self.use_8bit_var.get()
        config["temperature"] = self.temperature_var.get()
        config["inference_mode"] = self.inference_mode_var.get()
        
        # Memory settings
        config["memory_mode"] = self.memory_mode_var.get()
        config["index_path"] = self.index_path_var.get()
        config["embedding_model"] = self.embedding_model_var.get()
        config["default_result_count"] = self.result_count_var.get()
        config["relevance_threshold"] = self.threshold_var.get()
        
        # System settings
        config["log_dir"] = self.log_dir_var.get()
        config["log_level"] = self.log_level_var.get()
        config["max_log_size_mb"] = self.max_log_size_var.get()
        config["keep_backup_logs"] = self.keep_logs_var.get()
        config["check_updates"] = self.check_updates_var.get()
        config["start_minimized"] = self.start_minimized_var.get()
        config["confirm_exit"] = self.confirm_exit_var.get()
        
        # Collect plugin settings
        for plugin_id, settings_widget in self.plugin_settings_widgets.items():
            # Check if widget has get_settings method
            if hasattr(settings_widget, "get_settings"):
                try:
                    # Get settings from plugin
                    plugin_settings = settings_widget.get_settings()
                    
                    if plugin_settings:
                        # Add plugin settings with plugin_id prefix
                        for key, value in plugin_settings.items():
                            config[f"{plugin_id}.{key}"] = value
                except Exception as e:
                    self.log(f"[Config] Error getting settings from plugin {plugin_id}: {e}")
        
        # Update config manager
        self.config_manager.update(config)
        
        # Save config
        success = self.config_manager.save_config()
        
        if success:
            messagebox.showinfo(
                "Settings Saved",
                "All settings have been saved successfully."
            )
            
            # Apply changes
            self.apply_changes()
        else:
            messagebox.showerror(
                "Error",
                "Failed to save settings."
            )
            
    def reset_to_defaults(self):
        """Reset settings to default values"""
        # Confirm action
        result = messagebox.askyesno(
            "Reset to Defaults",
            "Are you sure you want to reset all settings to default values?",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
            
        # Reset config to defaults
        self.config_manager.reset_to_defaults()
        
        # Update UI with default values
        self.theme_var.set("Light")
        self.font_size_var.set("10")
        self.show_debug_var.set(False)
        self.auto_start_var.set(True)
        self.auto_save_var.set(True)
        self.system_prompt_var.set("You are Irintai, a helpful and knowledgeable assistant.")
        
        self.model_path_var.set("data/models")
        self.use_8bit_var.set(False)
        self.temperature_var.set(0.7)
        self.inference_mode_var.set("GPU")
        
        self.memory_mode_var.set("Off")
        self.index_path_var.set("data/vector_store/vector_store.json")
        self.embedding_model_var.set("all-MiniLM-L6-v2")
        self.result_count_var.set(5)
        self.threshold_var.set(0.7)
        
        self.log_dir_var.set("data/logs")
        self.log_level_var.set("INFO")
        self.max_log_size_var.set(10)
        self.keep_logs_var.set(True)
        self.check_updates_var.set(True)
        self.start_minimized_var.set(False)
        self.confirm_exit_var.set(True)
        
        # Update disk space info
        self.update_disk_space_info()
        
        messagebox.showinfo(
            "Settings Reset",
            "All settings have been reset to default values.\n\n"
            "Click 'Save All Settings' to apply these changes."
        )
        
    def apply_changes(self):
        """Apply changes without saving to config file"""
        # Update model path environment variables
        if self.model_path_var.get() != self.model_manager.model_path:
            self.model_manager.update_model_path(self.model_path_var.get())
            
        # Update model manager settings
        self.model_manager.use_8bit = self.use_8bit_var.get()
        
        # Update memory system settings
        if self.index_path_var.get() != self.memory_system.index_path:
            # Create a new memory system with the new path
            old_path = self.memory_system.index_path
            new_path = self.index_path_var.get()
            
            # Ask if the user wants to copy the old index to the new path
            if os.path.exists(old_path):
                result = messagebox.askyesno(
                    "Copy Index",
                    f"Do you want to copy the existing index from\n{old_path}\nto\n{new_path}?",
                    icon=messagebox.QUESTION
                )
                
                if result:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    
                    # Copy the file
                    import shutil
                    try:
                        shutil.copy2(old_path, new_path)
                        self.log(f"[Config] Copied index from {old_path} to {new_path}")
                    except Exception as e:
                        self.log(f"[Error] Failed to copy index: {e}")
                        messagebox.showerror(
                            "Error",
                            f"Failed to copy index: {e}"
                        )
            
            # Update memory system path
            self.memory_system.index_path = new_path
            
            # Reload index
            self.memory_system.load_index()
        
        # Update chat engine settings
        self.chat_engine.set_system_prompt(self.system_prompt_var.get())
        self.chat_engine.set_memory_mode(self.memory_mode_var.get())
        
        # Apply plugin settings
        for plugin_id, settings_widget in self.plugin_settings_widgets.items():
            # Check if widget has apply_settings method
            if hasattr(settings_widget, "apply_settings"):
                try:
                    # Apply settings
                    settings_widget.apply_settings()
                except Exception as e:
                    self.log(f"[Config] Error applying settings for plugin {plugin_id}: {e}")
        
        # Call the callback to notify parent
        if self.on_config_updated_callback:
            self.on_config_updated_callback()
            
        messagebox.showinfo(
            "Changes Applied",
            "Changes have been applied to the running system.\n\n"
            "Note that some changes may require a restart to take full effect."
        )