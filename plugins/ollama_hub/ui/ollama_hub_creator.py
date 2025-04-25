"""
Direct method to create Ollama Hub tab in the main UI

This fixes the error: 'MainWindow' object has no attribute 'create_ollama_hub_tab'
"""
import tkinter as ttk
def create_ollama_hub_tab_direct(self):
    """
    Create the Ollama Hub tab if the plugin is active
    
    This method is implemented directly in the MainWindow class to create
    and integrate the Ollama Hub UI tab into the application.
    """
    try:
        # Check if plugin manager is available
        if not hasattr(self, 'plugin_manager'):
            self.logger.log("[UI] Plugin manager not available, skipping Ollama Hub tab creation")
            return
            
        # Check if the ollama_hub plugin is active
        active_plugins = self.plugin_manager.get_active_plugins()
        
        # Skip if ollama_hub plugin is not active
        if 'ollama_hub' not in active_plugins:
            self.logger.log("[UI] Ollama Hub plugin not active, skipping tab creation")
            return
            
        # Get the plugin instance
        ollama_plugin = active_plugins.get('ollama_hub')
        
        # Create a frame for the tab
        ollama_tab_frame = ttk.Frame(self.notebook)
        
        # Try direct import of OllamaHubTab
        try:
            # Import the OllamaHubTab class
            import sys
            import importlib.util
            
            # First try if the plugin has ui_components attribute
            if hasattr(ollama_plugin, 'ui_components') and 'ollama_tab' in ollama_plugin.ui_components:
                # Create an instance of the tab
                OllamaHubTab = ollama_plugin.ui_components['ollama_tab']
                tab_instance = OllamaHubTab(ollama_tab_frame, plugin_instance=ollama_plugin)
                
                # Add the tab to the notebook
                self.notebook.add(ollama_tab_frame, text="Ollama Hub")
                
                # Store reference for later access
                self.ollama_hub_tab = tab_instance
                
                self.logger.log("[UI] Successfully added Ollama Hub tab")
                return True
                
            # If the plugin doesn't have ui_components, try direct import
            module_name = "plugins.ollama_hub.ui.ollama_tab"
            
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                # Find and load the module
                spec = importlib.util.find_spec(module_name)
                if spec:
                    module = importlib.util.import_module(module_name)
                else:
                    self.logger.log("[UI] Could not find Ollama Hub tab module", "ERROR")
                    return False
            
            # Check if OllamaHubTab exists in the module
            if hasattr(module, "OllamaHubTab"):
                OllamaHubTab = getattr(module, "OllamaHubTab")
                
                # Create an instance of OllamaHubTab
                tab_instance = OllamaHubTab(ollama_tab_frame, plugin_instance=ollama_plugin)
                
                # Add the tab to the notebook
                self.notebook.add(ollama_tab_frame, text="Ollama Hub")
                
                # Store reference for later access
                self.ollama_hub_tab = tab_instance
                
                self.logger.log("[UI] Successfully added Ollama Hub tab")
                return True
            else:
                self.logger.log("[UI] OllamaHubTab class not found in module", "ERROR")
                return False
                
        except Exception as e:
            self.logger.log(f"[UI] Error creating Ollama Hub tab: {e}", "ERROR")
            import traceback
            self.logger.log(f"[UI] {traceback.format_exc()}", "DEBUG")
            return False
            
    except Exception as e:
        self.logger.log(f"[UI] Error in create_ollama_hub_tab: {e}", "ERROR")
        return False
