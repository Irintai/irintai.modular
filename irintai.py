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
import sys
import warnings

import tkinter as tk
from tkinter import ttk
import traceback
import threading
import time

# Define base data directory - can be overridden by environment variable
BASE_DATA_DIR = os.environ.get("IRINTAI_DATA_DIR", "data")

# Create dictionary of data directories
DATA_DIRS = {
    "models": os.path.join(BASE_DATA_DIR, "models"),
    "logs": os.path.join(BASE_DATA_DIR, "logs"),
    "vector_store": os.path.join(BASE_DATA_DIR, "vector_store"),
    "reflections": os.path.join(BASE_DATA_DIR, "reflections"),
    "plugins": os.path.join(BASE_DATA_DIR, "plugins"),
    "plugins_config": os.path.join(BASE_DATA_DIR, "plugins", "config"),
    "plugins_data": os.path.join(BASE_DATA_DIR, "plugins", "data"),
}

# Create required directories
for dir_path in DATA_DIRS.values():
    os.makedirs(dir_path, exist_ok=True)

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

# Import the new SettingsManager
from core.settings_manager import SettingsManager

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
    logger = IrintaiLogger(log_dir=DATA_DIRS["logs"])
    setup_exception_handler(logger.log)
      # Start the application
    try:        # Config file path - allow override through environment variable
        config_file_path = os.environ.get("IRINTAI_CONFIG_FILE", 
                                         os.path.join(BASE_DATA_DIR, "config.json"))
        
        # Initialize configuration manager first
        config_manager = ConfigManager(path=config_file_path)
          # Initialize core components with proper dependencies
        # Get model path from config with fallback to a default location
        model_path = config_manager.get("model_path", os.path.join(os.path.expanduser("~"), "ollama", "models"))
        model_manager = ModelManager(
            model_path=model_path,
            logger=logger.log,
            config=config_manager,
            use_8bit=config_manager.get("model.use_8bit", False)
        )
        
        # Run Ollama diagnostics to identify version and path issues
        try:
            import subprocess
            import shutil
            
            # Log the Ollama version
            logger.log("[Diagnostics] Checking Ollama version...")
            version_result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5
            )
            if version_result.returncode == 0:
                logger.log(f"[Diagnostics] Ollama version: {version_result.stdout.strip()}")
            else:
                logger.log(f"[Diagnostics] Error getting Ollama version: {version_result.stderr.strip()}")
            
            # Log the path to the Ollama executable
            ollama_path = shutil.which("ollama")
            logger.log(f"[Diagnostics] Ollama executable path: {ollama_path}")
            
            # Log the default list command to be used (using remote)
            cmd = ["ollama", "list", "remote"]
            logger.log(f"[Diagnostics] Command to be executed: {cmd}")
            
            # Log environment PATH
            logger.log(f"[Diagnostics] PATH environment variable: {os.environ.get('PATH')}")
            
        except Exception as e:
            logger.log(f"[Diagnostics] Error during Ollama diagnostics: {e}")
        
        # Initialize SystemMonitor for resource tracking
        system_monitor = SystemMonitor(logger=logger.log, config=config_manager)
        
        # Start continuous monitoring with configurable interval
        monitoring_interval = config_manager.get("system.monitoring_interval", 1.0)        # Initialize EventBus for inter-plugin communication
        event_bus = EventBus(logger=logger.log)
        event_bus.start()  # Start the asynchronous event processing
        
        # Create file operations utility with proper sandboxing
        file_ops = FileOps(
            logger=logger.log
        )
        
        # Create a partial core_system dictionary with components we already have
        # This will be updated with additional components as they're initialized
        core_system = {
            "config_manager": config_manager,
            "logger": logger,
            "system_monitor": system_monitor,
            "event_bus": event_bus,
            "file_ops": file_ops
        }
        
        # Create a settings manager to provide centralized settings management
        settings_manager = SettingsManager(config_manager, logger=logger.log)
        core_system["settings_manager"] = settings_manager
        
        # Now pass event_bus to SystemMonitor
        system_monitor.event_bus = event_bus
        system_monitor.start_monitoring(interval=monitoring_interval)
          # Initialize MemorySystem
        memory_system = MemorySystem(
            index_path=os.path.join(DATA_DIRS["vector_store"], "vector_store.json"),
            logger=logger.log
        )

        # Initialize DependencyManager for plugin dependencies
        dependency_manager = DependencyManager(logger=logger.log)        # Create ChatEngine with model_manager dependency
        chat_engine = ChatEngine(
            model_manager=model_manager,
            memory_system=memory_system,
            session_file=os.path.join(BASE_DATA_DIR, "chat_history.json"),
            logger=logger.log
        )
        
        # Update the core_system with newly created components
        core_system.update({
            "model_manager": model_manager,
            "chat_engine": chat_engine,
            "memory_system": memory_system,
            "dependency_manager": dependency_manager
        })# Create plugin manager with all dependencies
        plugin_manager = PluginManager(
            plugin_dir=os.environ.get("IRINTAI_PLUGINS_DIR", "plugins"),
            config_dir=DATA_DIRS["plugins_config"],
            logger=logger.log,
            core_system=core_system,
        )
        
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

    # Integrate enhanced diagnostics
    try:
        from diagnostics.diagnostics_integration import integrate_with_settings_manager, setup_runtime_patching
        
        # Set up runtime patching utilities
        patch_plugin_manager, ensure_method_exists = setup_runtime_patching()
        
        # Apply runtime patching to plugin manager if needed
        if plugin_manager is not None:
            plugin_manager = patch_plugin_manager(plugin_manager)
        
        # Integrate with settings manager
        if settings_manager is not None:
            integrate_with_settings_manager(settings_manager)
            
        print("Enhanced diagnostics integrated successfully")
    except Exception as e:
        print(f"Warning: Could not integrate enhanced diagnostics: {e}")

if __name__ == "__main__":
    main()
