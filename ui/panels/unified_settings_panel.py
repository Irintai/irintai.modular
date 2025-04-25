"""
Unified Settings Panel - Consolidated settings UI for all application components
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Dict, Any, Callable, Optional

class UnifiedSettingsPanel:
    """
    A consolidated settings panel that combines all application settings in one place,
    organized by categories. This helps prevent duplicate controls and ensures settings
    consistency throughout the application.
    """
    
    def __init__(self, parent, settings_manager, core_system, logger=None):
        """
        Initialize the unified settings panel
        
        Args:
            parent: Parent widget
            settings_manager: SettingsManager instance
            core_system: Dictionary containing core system components
            logger: Optional logging function
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.core_system = core_system
        self.log = logger or print
        
        # Extract commonly used components from core_system
        self.chat_engine = core_system.get("chat_engine")
        self.memory_system = core_system.get("memory_system")
        self.model_manager = core_system.get("model_manager")
        self.plugin_manager = core_system.get("plugin_manager")
        
        # Create the main frame
        self.frame = ttk.Frame(parent)
        
        # Initialize the UI components
        self.initialize_ui()
        
    def initialize_ui(self):
        """Initialize the settings UI components"""
        # Create notebook for settings categories
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs for different settings categories
        self.general_tab = ttk.Frame(self.notebook)
        self.model_tab = ttk.Frame(self.notebook)
        self.memory_tab = ttk.Frame(self.notebook)
        self.plugin_tab = ttk.Frame(self.notebook)
        self.advanced_tab = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.general_tab, text="General")
        self.notebook.add(self.model_tab, text="Model Settings")
        self.notebook.add(self.memory_tab, text="Memory Settings")
        self.notebook.add(self.plugin_tab, text="Plugin Settings")
        self.notebook.add(self.advanced_tab, text="Advanced")
        
        # Initialize tab contents
        self.initialize_general_tab()
        self.initialize_model_tab()
        self.initialize_memory_tab()
        self.initialize_plugin_tab()
        self.initialize_advanced_tab()
        
    def initialize_general_tab(self):
        """Initialize general settings tab"""
        frame = ttk.Frame(self.general_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        # UI Theme settings
        theme_frame = ttk.LabelFrame(frame, text="UI Theme")
        theme_frame.pack(fill="x", pady=5)
        
        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.theme_var = tk.StringVar(value=self.settings_manager.get_setting("ui.theme", "system"))
        themes = ["light", "dark", "system"]
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=themes, state="readonly", width=15)
        theme_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.settings_manager.update_setting("ui.theme", self.theme_var.get()))
        
        # System behavior
        behavior_frame = ttk.LabelFrame(frame, text="System Behavior")
        behavior_frame.pack(fill="x", pady=10)
        
        # Auto-save settings
        self.autosave_var = tk.BooleanVar(value=self.settings_manager.get_setting("system.autosave", True))
        ttk.Checkbutton(
            behavior_frame, 
            text="Auto-save settings", 
            variable=self.autosave_var,
            command=lambda: self.settings_manager.update_setting("system.autosave", self.autosave_var.get())
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # Auto-load plugins
        self.autoload_plugins_var = tk.BooleanVar(value=self.settings_manager.get_setting("plugins.auto_load", True))
        ttk.Checkbutton(
            behavior_frame, 
            text="Auto-load plugins on startup", 
            variable=self.autoload_plugins_var,
            command=lambda: self.settings_manager.update_setting("plugins.auto_load", self.autoload_plugins_var.get())
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # System prompt
        prompt_frame = ttk.LabelFrame(frame, text="System Prompt")
        prompt_frame.pack(fill="x", pady=10)
        
        self.system_prompt_var = tk.StringVar(value=self.settings_manager.get_setting(
            "chat.system_prompt", 
            "You are Irintai, a helpful and knowledgeable assistant."
        ))
        
        prompt_text = tk.Text(prompt_frame, height=4, width=50, wrap="word")
        prompt_text.insert("1.0", self.system_prompt_var.get())
        prompt_text.pack(fill="x", padx=5, pady=5)
        
        def update_system_prompt():
            new_prompt = prompt_text.get("1.0", "end-1c")
            self.settings_manager.update_setting("chat.system_prompt", new_prompt)
            self.log("[Settings] System prompt updated")
        
        ttk.Button(
            prompt_frame,
            text="Update System Prompt",
            command=update_system_prompt
        ).pack(anchor="e", padx=5, pady=5)
        
    def initialize_model_tab(self):
        """Initialize model settings tab"""
        frame = ttk.Frame(self.model_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        # Model preferences
        model_frame = ttk.LabelFrame(frame, text="Model Preferences")
        model_frame.pack(fill="x", pady=5)
        
        # Default model
        ttk.Label(model_frame, text="Default Model:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.default_model_var = tk.StringVar(value=self.settings_manager.get_setting("model.default", ""))
        models = self.model_manager.get_available_models() or [""]
        model_combo = ttk.Combobox(model_frame, textvariable=self.default_model_var, values=models, width=20)
        model_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        model_combo.bind("<<ComboboxSelected>>", lambda e: self.settings_manager.update_setting("model.default", self.default_model_var.get()))
        
        # Model optimizations
        optim_frame = ttk.LabelFrame(frame, text="Model Optimizations")
        optim_frame.pack(fill="x", pady=10)
        
        # 8-bit quantization
        self.use_8bit_var = tk.BooleanVar(value=self.settings_manager.get_setting("model.use_8bit", False))
        ttk.Checkbutton(
            optim_frame, 
            text="Enable 8-bit quantization (reduces memory usage)", 
            variable=self.use_8bit_var,
            command=lambda: self.settings_manager.update_setting("model.use_8bit", self.use_8bit_var.get())
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # GPU offloading
        self.use_gpu_var = tk.BooleanVar(value=self.settings_manager.get_setting("model.use_gpu", True))
        ttk.Checkbutton(
            optim_frame, 
            text="Use GPU acceleration when available", 
            variable=self.use_gpu_var,
            command=lambda: self.settings_manager.update_setting("model.use_gpu", self.use_gpu_var.get())
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # Model parameters
        param_frame = ttk.LabelFrame(frame, text="Generation Parameters")
        param_frame.pack(fill="x", pady=10)
        
        # Temperature
        ttk.Label(param_frame, text="Temperature:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.temperature_var = tk.DoubleVar(value=self.settings_manager.get_setting("model.temperature", 0.7))
        temperature_scale = ttk.Scale(
            param_frame, 
            from_=0.0, 
            to=1.0, 
            variable=self.temperature_var,
            orient="horizontal",
            length=200
        )
        temperature_scale.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        temperature_scale.bind("<ButtonRelease-1>", lambda e: self.settings_manager.update_setting("model.temperature", self.temperature_var.get()))
        
        temperature_value = ttk.Label(param_frame, textvariable=tk.StringVar(value=f"{self.temperature_var.get():.2f}"))
        temperature_value.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        def update_temp_display(*args):
            temperature_value["text"] = f"{self.temperature_var.get():.2f}"
            
        self.temperature_var.trace_add("write", update_temp_display)
        
    def initialize_memory_tab(self):
        """Initialize memory settings tab"""
        frame = ttk.Frame(self.memory_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        # Memory mode settings
        memory_mode_frame = ttk.LabelFrame(frame, text="Memory Mode")
        memory_mode_frame.pack(fill="x", pady=5)
        
        # Memory mode radio buttons
        self.memory_mode_var = tk.StringVar(value=self.settings_manager.get_setting("memory.mode", "off"))
        
        ttk.Radiobutton(memory_mode_frame, text="Off (No memory usage)", 
                       variable=self.memory_mode_var, 
                       value="off", 
                       command=self.sync_memory_mode).pack(anchor="w", padx=10, pady=2)
                       
        ttk.Radiobutton(memory_mode_frame, text="Manual (Use memory when explicitly requested)", 
                       variable=self.memory_mode_var, 
                       value="manual", 
                       command=self.sync_memory_mode).pack(anchor="w", padx=10, pady=2)
                       
        ttk.Radiobutton(memory_mode_frame, text="Auto (Automatically use relevant memories)", 
                       variable=self.memory_mode_var, 
                       value="auto", 
                       command=self.sync_memory_mode).pack(anchor="w", padx=10, pady=2)
                       
        ttk.Radiobutton(memory_mode_frame, text="Background (Continuously update memory with context)", 
                       variable=self.memory_mode_var, 
                       value="background", 
                       command=self.sync_memory_mode).pack(anchor="w", padx=10, pady=2)
        
        # Enhanced PDF settings
        pdf_frame = ttk.LabelFrame(frame, text="PDF Processing")
        pdf_frame.pack(fill="x", pady=10)
        
        # OCR Settings
        self.ocr_enabled_var = tk.BooleanVar(value=self.settings_manager.get_setting("memory.pdf.ocr_enabled", False))
        ttk.Checkbutton(
            pdf_frame, 
            text="Enable OCR for image-based PDFs", 
            variable=self.ocr_enabled_var,
            command=lambda: self.settings_manager.update_setting("memory.pdf.ocr_enabled", self.ocr_enabled_var.get())
        ).pack(anchor="w", padx=10, pady=5)
        
        ocr_note = "Note: OCR requires pytesseract and Pillow packages."
        ttk.Label(pdf_frame, text=ocr_note, font=("Helvetica", 8), foreground="gray").pack(anchor="w", padx=10, pady=0)
        
        # Add test OCR button
        ttk.Button(pdf_frame, text="Check OCR Installation", 
                  command=self.check_ocr_installation).pack(anchor="w", padx=10, pady=5)
        
        # Advanced memory settings
        advanced_frame = ttk.LabelFrame(frame, text="Advanced Memory Settings")
        advanced_frame.pack(fill="x", pady=10)
        
        # Memory embedding model
        ttk.Label(advanced_frame, text="Embedding Model:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.embedding_model_var = tk.StringVar(value=self.settings_manager.get_setting("memory.embedding_model", "all-MiniLM-L6-v2"))
        embedding_models = ["all-MiniLM-L6-v2", "all-mpnet-base-v2", "all-distilroberta-v1"]
        embedding_combo = ttk.Combobox(advanced_frame, textvariable=self.embedding_model_var, values=embedding_models, width=25)
        embedding_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        embedding_combo.bind("<<ComboboxSelected>>", lambda e: self.settings_manager.update_setting("memory.embedding_model", self.embedding_model_var.get()))
        
        # Clear memory button
        ttk.Button(advanced_frame, text="Clear Memory Index", 
                  command=self.clear_memory_index, style="Warning.TButton").grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=10)
        
    def initialize_plugin_tab(self):
        """Initialize plugin settings tab"""
        frame = ttk.Frame(self.plugin_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        # Plugin management
        mgmt_frame = ttk.LabelFrame(frame, text="Plugin Management")
        mgmt_frame.pack(fill="x", pady=5)
        
        # Auto-start plugins
        self.auto_start_plugins_var = tk.BooleanVar(value=self.settings_manager.get_setting("plugins.auto_start", True))
        ttk.Checkbutton(
            mgmt_frame, 
            text="Auto-start activated plugins on launch", 
            variable=self.auto_start_plugins_var,
            command=lambda: self.settings_manager.update_setting("plugins.auto_start", self.auto_start_plugins_var.get())
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # Plugin directory
        ttk.Label(mgmt_frame, text="Plugin Directory:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.plugin_dir_var = tk.StringVar(value=self.settings_manager.get_setting("plugins.directory", "plugins"))
        plugin_dir_entry = ttk.Entry(mgmt_frame, textvariable=self.plugin_dir_var, width=40)
        plugin_dir_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        def update_plugin_dir():
            new_dir = self.plugin_dir_var.get()
            if os.path.isdir(new_dir):
                self.settings_manager.update_setting("plugins.directory", new_dir)
                if self.plugin_manager:
                    self.plugin_manager.plugin_dir = new_dir
                    self.log(f"[Settings] Plugin directory updated to: {new_dir}")
            else:
                messagebox.showerror("Invalid Directory", f"The directory {new_dir} does not exist.")
        
        ttk.Button(mgmt_frame, text="Update", command=update_plugin_dir).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        # Plugin security
        security_frame = ttk.LabelFrame(frame, text="Plugin Security")
        security_frame.pack(fill="x", pady=10)
        
        # Sandbox plugins
        self.sandbox_plugins_var = tk.BooleanVar(value=self.settings_manager.get_setting("plugins.sandbox", True))
        ttk.Checkbutton(
            security_frame, 
            text="Run plugins in sandbox mode (recommended)", 
            variable=self.sandbox_plugins_var,
            command=lambda: self.settings_manager.update_setting("plugins.sandbox", self.sandbox_plugins_var.get())
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # Verify plugin signatures
        self.verify_plugins_var = tk.BooleanVar(value=self.settings_manager.get_setting("plugins.verify_signatures", False))
        ttk.Checkbutton(
            security_frame, 
            text="Verify plugin signatures", 
            variable=self.verify_plugins_var,
            command=lambda: self.settings_manager.update_setting("plugins.verify_signatures", self.verify_plugins_var.get())
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # Plugin settings section - will be populated based on loaded plugins
        if self.plugin_manager and hasattr(self.plugin_manager, "get_plugins"):
            plugins = self.plugin_manager.get_plugins()
            
            if plugins:
                plugins_frame = ttk.LabelFrame(frame, text="Plugin Settings")
                plugins_frame.pack(fill="both", expand=True, pady=10)
                
                # Create a notebook to hold plugin-specific settings
                plugin_notebook = ttk.Notebook(plugins_frame)
                plugin_notebook.pack(fill="both", expand=True, padx=5, pady=5)
                
                for plugin_id, plugin_info in plugins.items():
                    if plugin_info.get("status") in ["ACTIVE", "LOADED"]:
                        # Create a frame for this plugin
                        plugin_frame = ttk.Frame(plugin_notebook)
                        plugin_notebook.add(plugin_frame, text=plugin_info.get("name", plugin_id))
                        
                        try:
                            # Try to get plugin config
                            config = self.plugin_manager.get_plugin_config(plugin_id)
                            if config and isinstance(config, dict):
                                self.create_plugin_settings(plugin_frame, plugin_id, config)
                            else:
                                ttk.Label(plugin_frame, text="No configurable settings available").pack(padx=10, pady=10)
                        except Exception as e:
                            ttk.Label(plugin_frame, text=f"Error loading plugin settings: {e}").pack(padx=10, pady=10)
            else:
                ttk.Label(frame, text="No active plugins found").pack(pady=20)
        else:
            ttk.Label(frame, text="Plugin manager not initialized or no plugins available").pack(pady=20)
        
    def initialize_advanced_tab(self):
        """Initialize advanced settings tab"""
        frame = ttk.Frame(self.advanced_tab, padding=10)
        frame.pack(fill="both", expand=True)
        
        # System settings
        system_frame = ttk.LabelFrame(frame, text="System Settings")
        system_frame.pack(fill="x", pady=5)
        
        # Resource monitoring interval
        ttk.Label(system_frame, text="Resource Monitoring Interval (seconds):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.monitoring_interval_var = tk.DoubleVar(value=self.settings_manager.get_setting("system.monitoring_interval", 1.0))
        interval_spinner = ttk.Spinbox(
            system_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.monitoring_interval_var,
            width=5
        )
        interval_spinner.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        interval_spinner.bind("<FocusOut>", lambda e: self.settings_manager.update_setting("system.monitoring_interval", float(self.monitoring_interval_var.get())))
        
        # Logging settings
        log_frame = ttk.LabelFrame(frame, text="Logging Settings")
        log_frame.pack(fill="x", pady=10)
        
        # Log level
        ttk.Label(log_frame, text="Log Level:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.log_level_var = tk.StringVar(value=self.settings_manager.get_setting("logging.level", "INFO"))
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var, values=log_levels, state="readonly", width=10)
        log_level_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        log_level_combo.bind("<<ComboboxSelected>>", lambda e: self.settings_manager.update_setting("logging.level", self.log_level_var.get()))
        
        # Log file retention
        ttk.Label(log_frame, text="Log File Retention (days):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.log_retention_var = tk.IntVar(value=self.settings_manager.get_setting("logging.retention_days", 30))
        retention_spinner = ttk.Spinbox(
            log_frame,
            from_=1,
            to=365,
            textvariable=self.log_retention_var,
            width=5
        )
        retention_spinner.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        retention_spinner.bind("<FocusOut>", lambda e: self.settings_manager.update_setting("logging.retention_days", int(self.log_retention_var.get())))
        
        # Expert settings (show raw config file)
        expert_frame = ttk.LabelFrame(frame, text="Expert Settings")
        expert_frame.pack(fill="x", pady=10)
        
        ttk.Button(
            expert_frame,
            text="Edit Raw Configuration",
            command=self.show_raw_config
        ).pack(anchor="w", padx=5, pady=5)
        
    def sync_memory_mode(self):
        """Synchronize memory mode changes with the chat engine and settings"""
        mode = self.memory_mode_var.get()
        
        # Set memory mode in chat engine using the updated interface
        if mode == "off":
            self.chat_engine.set_memory_mode(enabled=False)
        elif mode == "manual":
            self.chat_engine.set_memory_mode(enabled=True, auto=False, background=False)
        elif mode == "auto":
            self.chat_engine.set_memory_mode(enabled=True, auto=True, background=False)
        elif mode == "background":
            self.chat_engine.set_memory_mode(enabled=True, auto=True, background=True)
            
        # Update the setting
        self.settings_manager.update_setting("memory.mode", mode)
        self.log(f"[Memory Mode] Set to: {mode.capitalize()}")
        
    def check_ocr_installation(self):
        """Check if OCR dependencies are installed"""
        try:
            import pytesseract
            from PIL import Image
            pytesseract.get_tesseract_version()
            messagebox.showinfo("OCR Check", "OCR dependencies are correctly installed.")
        except ImportError as e:
            messagebox.showerror("OCR Check", f"Missing OCR dependency: {str(e)}\n\nInstall with:\npip install pytesseract pillow")
        except Exception as e:
            messagebox.showerror("OCR Check", f"OCR error: {str(e)}\n\nMake sure Tesseract OCR is installed on your system.")
            
    def clear_memory_index(self):
        """Clear the memory index after confirmation"""
        # Ask for confirmation before clearing
        response = messagebox.askyesno(
            "Confirm Clear Memory",
            "Are you sure you want to clear the entire memory index?\n\nThis will remove all documents and cannot be undone.",
            icon="warning"
        )
        
        if response:
            # Clear the index
            self.memory_system.clear_index()
            self.log("[Memory] Memory index cleared")
            
            messagebox.showinfo(
                "Memory Cleared",
                "Memory index has been cleared successfully."
            )
            
    def create_plugin_settings(self, parent, plugin_id, config):
        """Create settings UI for a specific plugin"""
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill="both", expand=True)
        
        row = 0
        settings_vars = {}
        
        for key, value in config.items():
            # Skip internal settings that start with underscore
            if key.startswith('_'):
                continue
                
            # Create label for the setting
            ttk.Label(frame, text=f"{key}:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
            
            # Create appropriate control based on the setting type
            if isinstance(value, bool):
                # Boolean toggle
                var = tk.BooleanVar(value=value)
                ttk.Checkbutton(
                    frame,
                    variable=var,
                    command=lambda k=key, v=var: self.update_plugin_setting(plugin_id, k, v.get())
                ).grid(row=row, column=1, sticky="w", padx=5, pady=5)
                settings_vars[key] = var
                
            elif isinstance(value, (int, float)):
                # Numeric spinner
                var = tk.DoubleVar(value=value) if isinstance(value, float) else tk.IntVar(value=value)
                spinner = ttk.Spinbox(
                    frame,
                    from_=0,
                    to=9999,
                    increment=1 if isinstance(value, int) else 0.1,
                    textvariable=var,
                    width=10
                )
                spinner.grid(row=row, column=1, sticky="w", padx=5, pady=5)
                spinner.bind("<FocusOut>", lambda e, k=key, v=var: self.update_plugin_setting(plugin_id, k, float(v.get()) if isinstance(value, float) else int(v.get())))
                settings_vars[key] = var
                
            elif isinstance(value, str):
                # Text entry
                var = tk.StringVar(value=value)
                entry = ttk.Entry(frame, textvariable=var, width=30)
                entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
                entry.bind("<FocusOut>", lambda e, k=key, v=var: self.update_plugin_setting(plugin_id, k, v.get()))
                settings_vars[key] = var
                
            row += 1
            
        # Add save button at the bottom
        if row > 0:
            ttk.Button(
                frame,
                text="Save Plugin Settings",
                command=lambda: self.save_plugin_settings(plugin_id, settings_vars)
            ).grid(row=row, column=0, columnspan=2, sticky="e", padx=5, pady=10)
        
    def update_plugin_setting(self, plugin_id, key, value):
        """Update a single plugin setting"""
        try:
            # Get current config
            config = self.plugin_manager.get_plugin_config(plugin_id) or {}
            
            # Update the specific setting
            config[key] = value
            
            # Save back to plugin
            self.plugin_manager.set_plugin_config(plugin_id, config)
            
        except Exception as e:
            self.log(f"[Settings] Error updating plugin setting: {e}")
            messagebox.showerror("Settings Error", f"Failed to update plugin setting: {e}")
            
    def save_plugin_settings(self, plugin_id, settings_vars):
        """Save all plugin settings at once"""
        try:
            # Get current config
            config = self.plugin_manager.get_plugin_config(plugin_id) or {}
            
            # Update with all values from UI
            for key, var in settings_vars.items():
                config[key] = var.get()
                
            # Save back to plugin
            self.plugin_manager.set_plugin_config(plugin_id, config)
            
            self.log(f"[Settings] Updated settings for plugin: {plugin_id}")
            messagebox.showinfo("Settings Saved", f"Settings for {plugin_id} have been saved.")
            
        except Exception as e:
            self.log(f"[Settings] Error saving plugin settings: {e}")
            messagebox.showerror("Settings Error", f"Failed to save plugin settings: {e}")
            
    def show_raw_config(self):
        """Show and edit raw configuration in a text editor"""
        # Create a new top-level window
        editor = tk.Toplevel(self.parent)
        editor.title("Raw Configuration Editor")
        editor.geometry("800x600")
        
        # Make it modal
        editor.transient(self.parent)
        editor.grab_set()
        
        # Create a text editor
        import json
        raw_config = json.dumps(self.settings_manager.config_manager.config, indent=2)
        
        text_frame = ttk.Frame(editor, padding=10)
        text_frame.pack(fill="both", expand=True)
        
        ttk.Label(text_frame, text="Edit raw configuration JSON (experts only):").pack(anchor="w")
        
        text_editor = tk.Text(text_frame, wrap="none", font=("Consolas", 10))
        text_editor.insert("1.0", raw_config)
        text_editor.pack(fill="both", expand=True, pady=5)
        
        # Add scrollbars
        x_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal", command=text_editor.xview)
        x_scrollbar.pack(side="bottom", fill="x")
        
        y_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_editor.yview)
        y_scrollbar.pack(side="right", fill="y")
        
        text_editor.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        
        # Create save/cancel buttons
        button_frame = ttk.Frame(editor, padding=10)
        button_frame.pack(fill="x")
        
        def save_raw_config():
            try:
                # Get the edited JSON
                edited_json = text_editor.get("1.0", "end-1c")
                
                # Parse it to ensure it's valid
                new_config = json.loads(edited_json)
                
                # Update the config manager
                self.settings_manager.config_manager.config = new_config
                self.settings_manager.config_manager.save()
                
                messagebox.showinfo("Config Saved", "Configuration has been updated.")
                editor.destroy()
                
            except json.JSONDecodeError as e:
                messagebox.showerror("Invalid JSON", f"Configuration contains invalid JSON: {e}")
                
        ttk.Button(button_frame, text="Save", command=save_raw_config).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=editor.destroy).pack(side="right", padx=5)
