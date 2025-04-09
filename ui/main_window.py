"""
Main application window for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import time
import threading

# Import core modules
from core import ModelManager, ChatEngine, MemorySystem, ConfigManager

# Import utility modules
from utils import IrintaiLogger, SystemMonitor, FileOps

# Import UI components
from .chat_panel import ChatPanel
from .model_panel import ModelPanel
from .config_panel import ConfigPanel
from .log_viewer import LogViewer
from .memory_panel import MemoryPanel

class MainWindow:
    """Main application window for the Irintai assistant"""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the main window
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Irintai - Local AI Assistant")
        self.root.minsize(800, 600)
        
        # Try to set the application icon
        try:
            if os.path.exists("resources/icons/irintai_icon.ico"):
                self.root.iconbitmap("resources/icons/irintai_icon.ico")
        except Exception:
            pass  # Ignore icon errors
        
        # Initialize logger
        self.initialize_logger()
        
        # Initialize core components
        self.initialize_core_components()
        
        # Initialize UI components
        self.initialize_ui()
        
        # Set up cleanup on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Schedule periodic updates
        self.schedule_updates()
        
        # Log startup message
        self.logger.log("[System] Irintai Assistant started")
        
    def initialize_logger(self):
        """Initialize the logger"""
        self.logger = IrintaiLogger(
            log_dir="data/logs",
            latest_log_file="irintai_debug.log"
        )
        
    def initialize_core_components(self):
        """Initialize core application components"""
        # Initialize configuration manager
        self.config_manager = ConfigManager(
            config_path="data/config.json",
            logger=self.logger.log
        )
        
        # Initialize file operations utility
        self.file_ops = FileOps(logger=self.logger.log)
        
        # Initialize system monitor
        self.system_monitor = SystemMonitor(logger=self.logger.log)
        
        # Get configuration values
        self.model_path = self.config_manager.get("model_path")
        self.use_8bit = self.config_manager.get("use_8bit")
        
        # Initialize model manager
        self.model_manager = ModelManager(
            model_path=self.model_path,
            logger=self.logger.log,
            use_8bit=self.use_8bit
        )
        
        # Initialize memory system
        self.memory_system = MemorySystem(
            index_path="data/vector_store/vector_store.json",
            logger=self.logger.log
        )
        
        # Initialize chat engine
        self.chat_engine = ChatEngine(
            model_manager=self.model_manager,
            memory_system=self.memory_system,
            session_file="data/chat_history.json",
            logger=self.logger.log
        )
        
        # Set memory mode from config
        self.chat_engine.set_memory_mode(
            self.config_manager.get("memory_mode", "Off")
        )
        
        # Set system prompt from config
        self.chat_engine.set_system_prompt(
            self.config_manager.get("system_prompt", 
                "You are Irintai, a helpful and knowledgeable assistant.")
        )
        
    def initialize_ui(self):
        """Initialize the user interface components"""
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create top toolbar
        self.create_toolbar()
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create chat panel
        self.chat_panel = ChatPanel(
            self.notebook,
            self.chat_engine,
            self.logger.log,
            self.config_manager
        )
        self.notebook.add(self.chat_panel.frame, text="Chat")
        
        # Create model panel
        self.model_panel = ModelPanel(
            self.notebook,
            self.model_manager,
            self.logger.log,
            self.on_model_selected
        )
        self.notebook.add(self.model_panel.frame, text="Models")
        
        # Create memory panel
        self.memory_panel = MemoryPanel(
            self.notebook,
            self.memory_system,
            self.file_ops,
            self.logger.log,
            self.chat_engine
        )
        self.notebook.add(self.memory_panel.frame, text="Memory")
        
        # Create config panel
        self.config_panel = ConfigPanel(
            self.notebook,
            self.config_manager,
            self.model_manager,
            self.memory_system,
            self.chat_engine,
            self.logger.log,
            self.on_config_updated
        )
        self.notebook.add(self.config_panel.frame, text="Settings")
        
        # Create status bar
        self.create_status_bar()
        
    def create_toolbar(self):
        """Create the top toolbar"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Add toolbar buttons
        ttk.Button(
            toolbar, 
            text="Load Files", 
            command=self.load_files
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar, 
            text="View Logs", 
            command=self.view_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="Save Logs", 
            command=self.save_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="Model Folder", 
            command=self.open_model_folder
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="Dashboard", 
            command=self.show_dashboard
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="Generate Reflection", 
            command=self.generate_reflection
        ).pack(side=tk.LEFT, padx=5)
        
        # Add memory mode selector to toolbar
        ttk.Label(toolbar, text="Memory Mode:").pack(side=tk.LEFT, padx=(20, 5))
        self.memory_mode_var = tk.StringVar(value=self.chat_engine.memory_mode)
        memory_modes = ["Off", "Manual", "Auto", "Background"]
        memory_dropdown = ttk.Combobox(
            toolbar, 
            textvariable=self.memory_mode_var,
            values=memory_modes,
            state="readonly",
            width=10
        )
        memory_dropdown.pack(side=tk.LEFT, padx=5)
        memory_dropdown.bind("<<ComboboxSelected>>", self.on_memory_mode_changed)
        
    def create_status_bar(self):
        """Create the status bar at the bottom of the window"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
        # Model status
        self.model_status_var = tk.StringVar(value="No model running")
        model_status = ttk.Label(status_frame, textvariable=self.model_status_var)
        model_status.pack(side=tk.LEFT, padx=5)
        
        # Performance stats
        self.perf_status_var = tk.StringVar(value="CPU: --% | RAM: --% | GPU: --% | VRAM: --")
        perf_label = ttk.Label(status_frame, textvariable=self.perf_status_var)
        perf_label.pack(side=tk.RIGHT, padx=5)
        
    def load_files(self):
        """Load files into memory"""
        from tkinter import filedialog
        
        # Get list of supported extensions
        extensions = self.file_ops.get_supported_extensions()
        
        # Create file type string for dialog
        file_types = [("Supported Files", " ".join(f"*{ext}" for ext in extensions))]
        for ext in extensions:
            content_types = self.file_ops.get_content_types()
            desc = content_types.get(ext, ext[1:].upper() + " Files")
            file_types.append((desc, f"*{ext}"))
        
        # Open file dialog
        files = filedialog.askopenfilenames(
            title="Select files to load",
            filetypes=file_types
        )
        
        if not files:
            return
            
        # Load and index each file
        for file_path in files:
            # Read the file
            success, content = self.file_ops.read_file(file_path)
            
            if success:
                # Add to memory system
                self.memory_system.add_file_to_index(file_path, content)
                self.logger.log(f"[Loaded] {os.path.basename(file_path)}")
            else:
                self.logger.log(f"[Error] Failed to load {file_path}")
                
        # Update memory panel if it exists
        if hasattr(self, 'memory_panel'):
            self.memory_panel.refresh_stats()
            
        # Show confirmation
        messagebox.showinfo(
            "Files Loaded", 
            f"Successfully loaded {len(files)} files into memory."
        )
        
    def view_logs(self):
        """Open the log viewer"""
        LogViewer(self.root, self.logger)
        
    def save_logs(self):
        """Save logs to a file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"irintai_logs_{timestamp}.txt"
        
        if self.logger.save_console_log(filename):
            messagebox.showinfo("Logs Saved", f"Logs saved to {filename}")
        else:
            messagebox.showerror("Error", "Failed to save logs")
            
    def open_model_folder(self):
        """Open the model folder in the file explorer"""
        if self.file_ops.open_folder(self.model_path):
            self.logger.log(f"[Opened] Model folder: {self.model_path}")
        else:
            messagebox.showerror("Error", f"Could not open folder: {self.model_path}")
            
    def show_dashboard(self):
        """Show the dashboard dialog"""
        from .dashboard import Dashboard
        
        Dashboard(
            self.root,
            self.chat_engine,
            self.model_manager,
            self.memory_system,
            self.system_monitor,
            self.logger.log
        )
        
    def generate_reflection(self):
        """Generate session reflection"""
        reflection = self.chat_engine.generate_reflection()
        
        if reflection:
            messagebox.showinfo(
                "Reflection Generated", 
                "Session reflection has been saved to data/reflections/session_reflections.json"
            )
            
    def on_memory_mode_changed(self, event):
        """Handle memory mode changes"""
        new_mode = self.memory_mode_var.get()
        self.chat_engine.set_memory_mode(new_mode)
        
        # Save to config
        self.config_manager.set("memory_mode", new_mode)
        self.config_manager.save_config()
        
    def on_model_selected(self, model_name):
        """
        Handle model selection from the model panel
        
        Args:
            model_name: Name of the selected model
        """
        # Update the model status display
        self.model_status_var.set(f"Model: {model_name}")
        
        # Update the chat panel
        self.chat_panel.set_model(model_name)
        
    def on_config_updated(self):
        """Handle configuration updates"""
        # Reload config values
        model_path = self.config_manager.get("model_path")
        use_8bit = self.config_manager.get("use_8bit")
        
        # Update model manager if path changed
        if model_path != self.model_path:
            self.model_path = model_path
            self.model_manager.update_model_path(model_path)
            self.model_panel.refresh_model_list()
            
        # Update 8-bit setting
        self.model_manager.use_8bit = use_8bit
        
        # Update system prompt
        system_prompt = self.config_manager.get("system_prompt")
        self.chat_engine.set_system_prompt(system_prompt)
        
        # Update memory mode
        memory_mode = self.config_manager.get("memory_mode")
        self.chat_engine.set_memory_mode(memory_mode)
        self.memory_mode_var.set(memory_mode)
        
    def update_performance_stats(self):
        """Update the performance statistics in the status bar"""
        stats = self.system_monitor.get_formatted_stats()
        self.perf_status_var.set(stats)
        
        # Set background color based on resource usage
        bg_color = self.system_monitor.get_bgr_color()
        # TODO: Update status bar background color when necessary
        
    def schedule_updates(self):
        """Schedule periodic updates"""
        # Update performance stats every second
        def update_stats():
            self.update_performance_stats()
            self.root.after(1000, update_stats)
            
        # Start the update cycle
        update_stats()
        
    def on_closing(self):
        """Handle application closing"""
        # Stop the model if running
        if self.model_manager.model_process and self.model_manager.model_process.poll() is None:
            self.model_manager.stop_model()
            
        # Save chat session
        self.chat_engine.save_session()
        
        # Save configuration
        self.config_manager.save_config()
        
        # Log shutdown
        self.logger.log("[System] Irintai Assistant shutting down")
        
        # Destroy the root window
        self.root.destroy()