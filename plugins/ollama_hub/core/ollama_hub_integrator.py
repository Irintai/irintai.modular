"""
Integration module for Ollama Hub UI components
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import threading
import webbrowser

def integrate_ollama_hub_ui(notebook, plugin_manager, logger):
    """
    Integrates Ollama Hub UI if the plugin is available and active
    
    Args:
        notebook: The tkinter notebook to add the tab to
        plugin_manager: The plugin manager instance
        logger: Logger function to log messages
    
    Returns:
        bool: True if integration was successful, False otherwise
    """
    # Check if the plugin manager is available
    if not plugin_manager or not hasattr(plugin_manager, 'get_active_plugins'):
        logger("[Ollama Hub] Plugin manager not available")
        return False
      # Get active plugins (could be a list or a dictionary)
    active_plugins = plugin_manager.get_active_plugins()
    ollama_plugin = None
    
    # Handle both list and dictionary return types
    if isinstance(active_plugins, dict):
        # If it's a dictionary, use the get method
        ollama_plugin = active_plugins.get('ollama_hub')
    elif isinstance(active_plugins, list):
        # If it's a list of plugin names (strings)
        if 'ollama_hub' in active_plugins:
            # Get the plugin instance
            if hasattr(plugin_manager, 'get_plugin_instance'):
                ollama_plugin = plugin_manager.get_plugin_instance('ollama_hub')
            elif hasattr(plugin_manager, 'plugins'):
                # Direct access to plugins dictionary
                ollama_plugin = plugin_manager.plugins.get('ollama_hub')
        # If it's a list of plugin objects
        else:
            for plugin in active_plugins:
                if hasattr(plugin, 'plugin_id') and plugin.plugin_id == 'ollama_hub':
                    ollama_plugin = plugin
                    break
    
    if not ollama_plugin:
        # Ollama plugin not active, don't add tab
        logger("[Ollama Hub] Plugin not active, skipping UI integration")
        return False
    
    try:
        # Check if the plugin provides a UI integration method
        if hasattr(ollama_plugin, 'get_notebook_frame'):
            # Create the frame using the plugin's method
            ollama_frame = ollama_plugin.get_notebook_frame(notebook)
            
            if ollama_frame:
                # Add the frame to the notebook
                notebook.add(ollama_frame, text="Ollama Hub")
                logger("[Ollama Hub] UI integrated successfully")
                return True
            else:
                logger("[Ollama Hub] Plugin returned empty frame")
                return False
        else:
            # Create a basic frame with a link to Ollama website
            ollama_frame = create_basic_ollama_frame(notebook)
            notebook.add(ollama_frame, text="Ollama Hub")
            logger("[Ollama Hub] Basic UI integrated")
            return True
    
    except Exception as e:
        logger(f"[Ollama Hub] Error integrating UI: {str(e)}")
        return False

def create_basic_ollama_frame(parent):
    """
    Creates a basic Ollama Hub frame with links to the website
    
    Args:
        parent: Parent widget
        
    Returns:
        ttk.Frame: The frame with basic Ollama Hub content
    """
    frame = ttk.Frame(parent)
    
    # Create content
    ttk.Label(
        frame, 
        text="Ollama Hub Integration", 
        font=("Arial", 16)
    ).pack(pady=20)
    
    ttk.Label(
        frame,
        text="The Ollama plugin is active, but no custom UI is available.\n"
             "You can use the buttons below to access Ollama services."
    ).pack(pady=10)
    
    # Create buttons frame
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=20)
    
    # Add buttons
    ttk.Button(
        btn_frame,
        text="Open Ollama Website",
        command=lambda: webbrowser.open("https://ollama.ai")
    ).grid(row=0, column=0, padx=10, pady=10)
    
    ttk.Button(
        btn_frame,
        text="View Ollama Models",
        command=lambda: webbrowser.open("https://ollama.ai/library")
    ).grid(row=0, column=1, padx=10, pady=10)
    
    ttk.Button(
        btn_frame,
        text="Ollama Documentation",
        command=lambda: webbrowser.open("https://github.com/ollama/ollama/blob/main/README.md")
    ).grid(row=1, column=0, padx=10, pady=10)
    
    ttk.Button(
        btn_frame,
        text="Refresh Integration",
        command=lambda: messagebox.showinfo("Not Implemented", "This functionality is not implemented yet.")
    ).grid(row=1, column=1, padx=10, pady=10)
    
    return frame
