"""
Ollama Hub tab refresh utility for the main window

This module provides functions to add or refresh the Ollama Hub tab in the main window
after the plugin has been activated.
"""
import tkinter as tk
from tkinter import ttk

def add_ollama_hub_tab_to_main_window(main_window):
    """
    Add or refresh the Ollama Hub tab in the main window
    
    This function should be called after the Ollama Hub plugin has been activated.
    It will check if the plugin is active and add the tab if it's not already present.
    
    Args:
        main_window: The MainWindow instance
        
    Returns:
        True if the tab was added/refreshed, False otherwise
    """
    try:
        # Make sure we have all required components
        if not hasattr(main_window, 'notebook') or not hasattr(main_window, 'plugin_manager'):
            main_window.logger.log("[UI] Cannot add Ollama Hub tab: missing required components")
            return False
            
        # Check if the tab already exists
        for i in range(main_window.notebook.index("end")):
            if main_window.notebook.tab(i, "text") == "Ollama Hub":
                main_window.logger.log("[UI] Ollama Hub tab already exists")
                return True
        
        # Check if the ollama_hub plugin is active
        active_plugins = main_window.plugin_manager.get_active_plugins()
        if 'ollama_hub' not in active_plugins:
            main_window.logger.log("[UI] Ollama Hub plugin not active, skipping tab creation")
            return False
            
        # Get the plugin instance
        ollama_plugin = active_plugins.get('ollama_hub')
        
        # Import the module from the plugins directory
        from plugins.ollama_hub.ui.ollama_tab import OllamaHubTab
        
        # Create a frame for the tab
        ollama_tab_frame = ttk.Frame(main_window.notebook)
        
        # Create an instance of OllamaHubTab
        tab_instance = OllamaHubTab(ollama_tab_frame, plugin_instance=ollama_plugin)
        
        # Add the tab to the notebook
        main_window.notebook.add(ollama_tab_frame, text="Ollama Hub")
        
        # Store reference for later access
        main_window.ollama_hub_tab = tab_instance
        
        main_window.logger.log("[UI] Successfully added Ollama Hub tab")
        return True
    except Exception as e:
        import traceback
        main_window.logger.log(f"[UI] Error adding Ollama Hub tab: {e}", "ERROR")
        main_window.logger.log(traceback.format_exc(), "DEBUG")
        return False

def refresh_ollama_hub_tab(main_window):
    """
    Refresh the Ollama Hub tab in the main window
    
    This function will remove the existing tab if it exists and add a new one.
    
    Args:
        main_window: The MainWindow instance
        
    Returns:
        True if the tab was refreshed, False otherwise
    """
    try:
        # Remove existing tab if present
        for i in range(main_window.notebook.index("end")):
            if main_window.notebook.tab(i, "text") == "Ollama Hub":
                main_window.notebook.forget(i)
                break
                
        # Add the tab again
        return add_ollama_hub_tab_to_main_window(main_window)
    except Exception as e:
        main_window.logger.log(f"[UI] Error refreshing Ollama Hub tab: {e}", "ERROR")
        return False
