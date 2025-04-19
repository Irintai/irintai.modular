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
from .resource_monitor_panel import ResourceMonitorPanel
from core.plugin_manager import PluginManager
from ui.plugin_panel import PluginPanel
from .plugin_config_panel import PluginConfigPanel

class MainWindow:
    """Main application window for the Irintai assistant"""
    
    def __init__(self, root: tk.Tk, core_app=None):
        """
        Initialize the main window
        
        Args:
            root: Tkinter root window
            core_app: Dictionary containing core application components
        """
        self.root = root
        self.root.title("Irintai - Local AI Assistant")
        self.root.minsize(800, 600)
        
        # Store core_app reference
        self.core_app = core_app or {}
        
        # Try to set the application icon
        try:
            if os.path.exists("resources/icons/irintai_icon.ico"):
                self.root.iconbitmap("resources/icons/irintai_icon.ico")
        except Exception:
            pass  # Ignore icon errors
        
        # Initialize logger (use from core_app if available)
        self.initialize_logger()
        
        # Initialize core components using core_app
        self.initialize_core_components()
        
        # Initialize UI components
        self.initialize_ui()
        
        # Initialize plugins after UI is ready
        self.initialize_plugins()
        
        # Update plugin menu
        self.update_plugin_menu()
        
        # Set up cleanup on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Schedule periodic updates
        self.schedule_updates()
        
        # Log startup message
        self.logger.log("[System] Irintai Assistant started")
        
    def initialize_logger(self):
        """Initialize the logger"""
        if "logger" in self.core_app:
            self.logger = self.core_app["logger"]
        else:
            self.logger = IrintaiLogger(
                log_dir="data/logs",
                latest_log_file="irintai_debug.log"
            )
        
    def initialize_core_components(self):
        """Initialize core application components"""
        # Use components from core_app if available, otherwise create new ones
        
        # Configuration manager
        if "config_manager" in self.core_app:
            self.config_manager = self.core_app["config_manager"]
        else:
            self.config_manager = ConfigManager(
                config_path="data/config.json",
                logger=self.logger.log
            )
        
        # File operations utility
        self.file_ops = FileOps(logger=self.logger.log)
        
        # System monitor
        self.system_monitor = SystemMonitor(logger=self.logger.log)
        
        # Get configuration values
        self.model_path = self.config_manager.get("model_path", "data/models")
        self.use_8bit = self.config_manager.get("use_8bit", False)
        
        # Model manager
        if "model_manager" in self.core_app:
            self.model_manager = self.core_app["model_manager"]
        else:
            self.model_manager = ModelManager(
                model_path=self.model_path,
                logger=self.logger.log,
                use_8bit=self.use_8bit
            )
        
        # Memory system
        if "memory_system" in self.core_app:
            self.memory_system = self.core_app["memory_system"]
        else:
            self.memory_system = MemorySystem(
                index_path="data/vector_store/vector_store.json",
                logger=self.logger.log
            )
        
        # Chat engine
        if "chat_engine" in self.core_app:
            self.chat_engine = self.core_app["chat_engine"]
        else:
            self.chat_engine = ChatEngine(
                model_manager=self.model_manager,
                memory_system=self.memory_system,
                session_file="data/chat_history.json",
                logger=self.logger.log
            )
        
        # Plugin manager
        if "plugin_manager" in self.core_app:
            self.plugin_manager = self.core_app["plugin_manager"]
        else:
            self.plugin_manager = PluginManager(
                plugin_dir="plugins",
                config_dir="data/plugins",
                logger=self.logger.log,
                core_system=self
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
        
        # Create resource monitor panel
        self.resource_monitor = ResourceMonitorPanel(
            self.notebook,
            self.logger.log,
            self.system_monitor  # Pass the SystemMonitor instance
        )
        self.notebook.add(self.resource_monitor.frame, text="Resources")
        
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
        
        # Create plugin panel
        self.plugin_panel = PluginPanel(
            self.notebook,
            self.plugin_manager,
            logger=self.logger.log
        )
        self.notebook.add(self.plugin_panel.frame, text="Plugins")
        
        # Create plugin config panel
        self.plugin_config_panel = PluginConfigPanel(
            self.notebook,
            self.plugin_manager,
            self.config_manager,
            self.logger.log
        )
        self.notebook.add(self.plugin_config_panel.frame, text="Plugin Settings")
        
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
        
        # Add plugins button with dropdown menu
        self.plugins_button = ttk.Menubutton(
            toolbar,
            text="Plugins",
            direction="below"
        )
        self.plugins_button.pack(side=tk.LEFT, padx=5)
        
        # Create the plugins menu
        self.plugins_menu = tk.Menu(self.plugins_button, tearoff=0)
        self.plugins_button["menu"] = self.plugins_menu
        
        # Add items to the menu (will be populated later)
        self.plugins_menu.add_command(label="Manage Plugins", command=self.show_plugins_tab)
        self.plugins_menu.add_command(label="Reload All Plugins", command=self.reload_all_plugins)
        self.plugins_menu.add_separator()
        self.plugins_menu.add_command(label="No active plugins", state=tk.DISABLED)
        
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

    def update_plugin_menu(self):
        """Update the plugins dropdown menu with active plugins"""
        # Remove existing plugin entries
        menu_size = self.plugins_menu.index("end")
        if menu_size > 3:  # Keep the first 4 items (Manage, Reload, Separator, No plugins)
            self.plugins_menu.delete(3, menu_size)
        
        # Get active plugins
        active_plugins = self.plugin_manager.get_active_plugins()
        
        if not active_plugins:
            # Show "No active plugins" if none are active
            self.plugins_menu.entryconfig(3, state=tk.NORMAL)
            return
        
        # Hide "No active plugins" entry
        self.plugins_menu.entryconfig(3, state=tk.DISABLED)
        
        # Add separator and active plugins
        if active_plugins:
            # Add each active plugin with its actions
            for plugin_id, plugin in active_plugins.items():
                # Check if plugin has a get_actions method
                if hasattr(plugin, "get_actions") and callable(plugin.get_actions):
                    try:
                        actions = plugin.get_actions()
                        if actions and isinstance(actions, dict):
                            # Create a submenu for this plugin
                            plugin_menu = tk.Menu(self.plugins_menu, tearoff=0)
                            self.plugins_menu.add_cascade(label=plugin_id, menu=plugin_menu)
                            
                            # Add each action to the submenu
                            for action_name, action_func in actions.items():
                                if callable(action_func):
                                    plugin_menu.add_command(label=action_name, command=action_func)
                    except Exception as e:
                        self.logger.log(f"[Error] Failed to get actions for plugin {plugin_id}: {e}")
                else:
                    # Just add the plugin name without actions
                    self.plugins_menu.add_command(label=plugin_id, state=tk.DISABLED)

    def show_plugins_tab(self):
        """Show the plugins tab in the notebook"""
        # Find the index of the plugins tab
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Plugins":
                self.notebook.select(i)
                break

    def reload_all_plugins(self):
        """Reload all plugins"""
        # Ask for confirmation
        result = messagebox.askyesno(
            "Reload Plugins",
            "This will reload all plugins. Any unsaved plugin data may be lost.\n\nContinue?",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
        
        # Get list of active plugins
        active_plugins = list(self.plugin_manager.get_active_plugins().keys())
        
        # Unload all plugins
        for plugin_id in self.plugin_manager.get_all_plugins().keys():
            self.plugin_manager.unload_plugin(plugin_id)
        
        # Rediscover and reload plugins
        self.plugin_manager.discover_plugins()
        
        # Reload previously active plugins
        for plugin_id in active_plugins:
            success = self.plugin_manager.load_plugin(plugin_id)
            if success:
                self.plugin_manager.activate_plugin(plugin_id)
        
        # Update UI
        if hasattr(self, 'plugin_panel'):
            self.plugin_panel.refresh_plugin_list()
        
        # Update menu
        self.update_plugin_menu()
        
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
        
        # Deactivate all active plugins
        self.cleanup_plugins()
        
        # Log shutdown
        self.logger.log("[System] Irintai Assistant shutting down")
        
        # Destroy the root window
        self.root.destroy()

    def cleanup_plugins(self):
        """Deactivate all active plugins"""
        self.logger.log("[Plugins] Deactivating all plugins")
        
        try:
            plugins_info = self.plugin_manager.get_all_plugins()
            for plugin_name, info in plugins_info.items():
                if info.get("status") == "Active":
                    self.logger.log(f"[Plugins] Deactivating plugin: {plugin_name}")
                    self.plugin_manager.deactivate_plugin(plugin_name)
                    
            # Allow a short delay for clean deactivation
            time.sleep(0.5)
        except Exception as e:
            self.logger.log(f"[Error] Failed to cleanup plugins: {e}", "ERROR")    
            
    def initialize_plugins(self):
        """Initialize the plugin system and load available plugins"""
        # Log plugin initialization
        self.logger.log("[Plugins] Initializing plugin system")
        
        # Check if plugin manager has all required methods before using them
        from utils.attribute_checker import check_required_attributes, verify_interface
        
        # Define required methods for plugin manager
        required_methods = ["set_error_handler", "discover_plugins", "load_plugin", 
                           "activate_plugin", "deactivate_plugin"]
        
        # Verify the plugin manager has all required methods
        if verify_interface(self.plugin_manager, required_methods, 
                          obj_name="PluginManager", logger=self.logger.log):
            # Set error handler - only if the method exists
            self.plugin_manager.set_error_handler(self.handle_plugin_error)
            
            # Register core components as services for plugins
            self.register_plugin_services()
            
            # Discover available plugins
            plugin_count = self.plugin_manager.discover_plugins()
            self.logger.log(f"[Plugins] Discovered {plugin_count} plugins")
        else:
            self.logger.log("[ERROR] Plugin manager is missing required methods. Plugin functionality will be limited.", "ERROR")
            # Continue with limited functionality by checking each method individually
            if hasattr(self.plugin_manager, "discover_plugins"):
                plugin_count = self.plugin_manager.discover_plugins()
                self.logger.log(f"[Plugins] Discovered {plugin_count} plugins")
        
        # Get auto-load plugins from config
        autoload_plugins = self.config_manager.get("autoload_plugins", [])
        
        # Auto-load plugins
        if autoload_plugins:
            self.logger.log(f"[Plugins] Auto-loading {len(autoload_plugins)} plugins")
            for plugin_name in autoload_plugins:
                success = self.plugin_manager.load_plugin(plugin_name)
                if success:
                    # Auto-activate plugin if in the list
                    activate = self.config_manager.get(f"autoactivate.{plugin_name}", False)
                    if activate:
                        self.plugin_manager.activate_plugin(plugin_name)
        
        # Register for plugin events
        self.plugin_manager.register_event_handler("main_window", "plugin_loaded", self.on_plugin_loaded)
        self.plugin_manager.register_event_handler("main_window", "plugin_activated", self.on_plugin_activated)
        self.plugin_manager.register_event_handler("main_window", "plugin_deactivated", self.on_plugin_deactivated)
        self.plugin_manager.register_event_handler("main_window", "plugin_unloaded", self.on_plugin_unloaded)
        self.plugin_manager.register_event_handler("main_window", "plugin_error", self.on_plugin_error)

    def register_plugin_services(self):
        """Register core services for plugins to access"""
        # Register core components as services
        services = {
            "logger": self.logger,
            "model_manager": self.model_manager,
            "chat_engine": self.chat_engine,
            "memory_system": self.memory_system,
            "config_manager": self.config_manager,
            "system_monitor": self.system_monitor,
            "file_ops": self.file_ops
        }
        
        # Add UI components (only if they're already initialized)
        if hasattr(self, 'chat_panel'):
            services["chat_panel"] = self.chat_panel
            
        if hasattr(self, 'model_panel'):
            services["model_panel"] = self.model_panel
            
        if hasattr(self, 'memory_panel'):
            services["memory_panel"] = self.memory_panel
        
        # Register each service
        for name, service in services.items():
            self.plugin_manager.register_service(name, service)
        
        self.logger.log(f"[Plugins] Registered {len(services)} core services for plugins")

    def handle_plugin_error(self, plugin_name, error_msg, error_type="ERROR"):
        """
        Handle plugin errors
        
        Args:
            plugin_name: Name of the plugin
            error_msg: Error message
            error_type: Type of error (ERROR, WARNING)
        """
        # Log the error
        self.logger.log(f"[Plugin Error] {plugin_name}: {error_msg}", error_type)
        
        # Update the plugin panel if it exists
        if hasattr(self, 'plugin_panel'):
            self.plugin_panel.refresh_plugin_list()
            
        # Show critical errors in UI
        if error_type == "ERROR" and self.config_manager.get("show_plugin_errors", True):
            messagebox.showerror(
                f"Plugin Error: {plugin_name}",
                f"An error occurred in plugin '{plugin_name}':\n\n{error_msg}"
            )

    def on_plugin_loaded(self, plugin_id, plugin_instance):
        """
        Handle plugin loaded event
        
        Args:
            plugin_id: Plugin identifier
            plugin_instance: Plugin instance
        """
        self.logger.log(f"[Plugins] Loaded plugin: {plugin_id}")
        
        # Update UI if needed
        if hasattr(self, 'plugin_panel'):
            self.plugin_panel.refresh_plugin_list()

    def on_plugin_activated(self, plugin_id, plugin_instance):
        """
        Handle plugin activation event
        
        Args:
            plugin_id: Plugin identifier
            plugin_instance: Plugin instance
        """
        self.logger.log(f"[Plugins] Activated plugin: {plugin_id}")
        
        # Update plugin state in config for auto-activation
        if self.config_manager.get(f"remember_plugin_state", True):
            self.config_manager.set(f"autoactivate.{plugin_id}", True)
            self.config_manager.save_config()
        
        # Update UI
        if hasattr(self, 'plugin_panel'):
            self.plugin_panel.refresh_plugin_list()

    def on_plugin_deactivated(self, plugin_id):
        """
        Handle plugin deactivation event
        
        Args:
            plugin_id: Plugin identifier
        """
        self.logger.log(f"[Plugins] Deactivated plugin: {plugin_id}")
        
        # Update plugin state in config
        if self.config_manager.get(f"remember_plugin_state", True):
            self.config_manager.set(f"autoactivate.{plugin_id}", False)
            self.config_manager.save_config()
        
        # Update UI
        if hasattr(self, 'plugin_panel'):
            self.plugin_panel.refresh_plugin_list()

    def on_plugin_unloaded(self, plugin_id):
        """
        Handle plugin unloaded event
        
        Args:
            plugin_id: Plugin identifier
        """
        self.logger.log(f"[Plugins] Unloaded plugin: {plugin_id}")
        
        # Update UI
        if hasattr(self, 'plugin_panel'):
            self.plugin_panel.refresh_plugin_list()

    def on_plugin_error(self, plugin_id, error_msg):
        """
        Handle plugin error event
        
        Args:
            plugin_id: Plugin identifier
            error_msg: Error message
        """
        self.handle_plugin_error(plugin_id, error_msg)