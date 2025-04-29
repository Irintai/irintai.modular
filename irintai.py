#!/usr/bin/env python3
"""
Irintai - Local AI Assistant
A modular, user-friendly interface for local language models

This application provides a graphical interface for interacting with local AI models,
managing embeddings for context-aware responses, and configuring various aspects
of the assistant.
"""

# Suppress TensorFlow logging messages
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=info+warn+error, 2=warn+error, 3=error only
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '1'  # Keep optimizations but suppress the message
# Suppress TensorFlow deprecation warnings
os.environ['TF_ENABLE_DEPRECATION_WARNINGS'] = '0'  # Disable deprecation warnings completely

import sys
import warnings
# Filter TensorFlow deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='tensorflow')
warnings.filterwarnings('ignore', message='.*The name tf\..*is deprecated.*')

import tkinter as tk
from tkinter import ttk
import traceback
import threading
import time

# Create required directories
os.makedirs("data/models", exist_ok=True)
os.makedirs("data/logs", exist_ok=True) 
os.makedirs("data/vector_store", exist_ok=True)
os.makedirs("data/reflections", exist_ok=True)
os.makedirs("data/plugins", exist_ok=True)
os.makedirs("data/plugins/config", exist_ok=True)
os.makedirs("data/plugins/data", exist_ok=True)

# Import core modules
from core import (
    ModelManager, 
    ChatEngine, 
    MemorySystem, 
    ConfigManager,
    PluginManager,
    PluginSDK
)

# Import utility modules
from utils import (
    IrintaiLogger,
    SystemMonitor,
    FileOps,
    EventBus,
    DependencyManager
)

# Import UI components
from ui import MainWindow

def setup_exception_handler(logger):
    """Set up global exception handler to log errors"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        # Log the exception
        if issubclass(exc_type, KeyboardInterrupt):
            # Special case for keyboard interrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Log the exception
        logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Show error dialog
        import tkinter.messagebox as messagebox
        error_msg = f"An unexpected error occurred:\n\n{exc_value}\n\nSee log file for details."
        messagebox.showerror("Error", error_msg)
        
    # Install exception handler
    sys.excepthook = handle_exception

def configure_theme():
    """Configure the application theme"""
    style = ttk.Style()
    
    # Configure default style
    style.configure("TButton", padding=5)
    style.configure("TFrame", background="#f0f0f0")
    style.configure("TLabel", background="#f0f0f0")
    
    # Configure accent style for primary buttons
    style.configure("Accent.TButton", background="#007bff", foreground="white")
    style.map("Accent.TButton",
        background=[("active", "#0069d9"), ("disabled", "#cccccc")],
        foreground=[("disabled", "#666666")]
    )
    
    # Configure warning style for critical buttons
    style.configure("Warning.TButton", background="#dc3545", foreground="white")
    style.map("Warning.TButton",
        background=[("active", "#c82333"), ("disabled", "#cccccc")],
        foreground=[("disabled", "#666666")]
    )
    
def main():
    """Main application entry point"""
    # Create the main window
    root = tk.Tk()
    root.title("Irintai - Local AI Assistant")
    root.minsize(800, 600)
    root.geometry("1024x768")
    
    # Try to set the application icon
    try:
        if os.path.exists("resources/icons/irintai_icon.ico"):
            root.iconbitmap("resources/icons/irintai_icon.ico")
    except Exception:
        pass  # Ignore icon errors
    
    # Configure theme
    configure_theme()
    
    # Handle uncaught exceptions
    logger = IrintaiLogger(log_dir="data/logs")
    setup_exception_handler(logger.log)
    
    # Start the application
    try:
        # Initialize configuration manager first
        config_manager = ConfigManager(path="data/config.json")
        
        # Initialize core components with proper dependencies
        model_manager = ModelManager(
            model_path="data/models",
            logger=logger.log,
            config=config_manager,
            use_8bit=config_manager.get("model.use_8bit", False)
        )

        # Initialize SystemMonitor for resource tracking
        system_monitor = SystemMonitor(logger=logger.log, config=config_manager)

        # Start continuous monitoring with configurable interval
        monitoring_interval = config_manager.get("system.monitoring_interval", 1.0)
        system_monitor.start_monitoring(interval=monitoring_interval)

        # Initialize EventBus for inter-plugin communication
        event_bus = EventBus(logger=logger.log)
        event_bus.start()  # Start the asynchronous event processing        # Initialize MemorySystem
        memory_system = MemorySystem(
            index_path="data/vector_store/vector_store.json",
            logger=logger.log
        )

        # Initialize DependencyManager for plugin dependencies
        dependency_manager = DependencyManager(logger=logger.log)
        
        # Create ChatEngine with model_manager dependency
        chat_engine = ChatEngine(
            model_manager=model_manager,
            memory_system=memory_system,
            session_file="data/chat_history.json",
            logger=logger.log
        )
        
        # Create file operations utility with proper sandboxing
        file_ops = FileOps(
            logger=logger.log
        )
        
        # Create a template core system for plugins
        core_system = {
            "model_manager": model_manager,
            "chat_engine": chat_engine,
            "memory_system": memory_system,
            "config_manager": config_manager,
            "logger": logger,
            "system_monitor": system_monitor,
            "event_bus": event_bus,
            "file_ops": file_ops
        }
          # Create plugin manager with all dependencies
        plugin_manager = PluginManager(
            plugin_dir="plugins",
            config_dir="data/plugins/config",
            logger=logger.log,
            core_system=core_system,
        )
        
        # Patch the plugin manager with any missing attributes/methods
        # This prevents AttributeError crashes if methods are missing
        from utils.runtime_patching import patch_plugin_manager
        plugin_manager = patch_plugin_manager(plugin_manager)
        logger.log("[System] Verified plugin manager interface")
        
        # Register plugin manager with the core system
        core_system["plugin_manager"] = plugin_manager
        
        # Create main window with core_app
        app = MainWindow(root, core_app=core_system)
        
        # Log application start
        logger.log("Irintai Assistant started successfully")
        
        # Auto-load plugins if configured
        if config_manager.get("plugins.auto_load", True):
            def delayed_plugin_loading():
                # Wait for UI to initialize
                time.sleep(1)
                logger.log("Auto-loading plugins...")
                plugin_manager.auto_load_plugins()
                
            # Start plugin loading in a separate thread
            threading.Thread(target=delayed_plugin_loading, daemon=True).start()
        
        # Start the UI main loop
        root.mainloop()
        
        # Perform cleanup when the application exits
        logger.log("Shutting down Irintai Assistant...")
        
        # Stop event bus
        event_bus.stop()
        
        # Stop system monitoring
        system_monitor.stop_monitoring()
        
        # Unload all plugins
        plugin_manager.unload_all_plugins()
        
        # Log application exit
        logger.log("Irintai Assistant shut down successfully")
        
    except Exception as e:
        # Log the exception
        logger.error(f"Unhandled exception in main: {e}")
        logger.error(traceback.format_exc())
        
        # Show error dialog if UI is available
        try:
            import tkinter.messagebox as messagebox
            error_msg = f"An error occurred:\n\n{e}\n\nSee log for details."
            messagebox.showerror("Error", error_msg)
        except:
            pass

if __name__ == "__main__":
    main()
