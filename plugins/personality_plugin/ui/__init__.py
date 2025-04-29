"""
UI Components for the Personality Plugin
"""

from plugins.personality_plugin.ui.panel import Panel

# Export the class at the package level
__all__ = ['Panel']

# Module level activation function for plugin manager
def activate_ui(container):
    """
    Create and return a panel for the plugin
    
    Args:
        container: UI container to place panel in
        
    Returns:
        The created panel
    """
    from plugins.personality_plugin.core import PersonalityPlugin
    from plugins.personality_plugin.ui.panel import Panel
    
    # Get plugin instance from plugin manager
    plugin_manager = container.master.plugin_manager
    plugin_instance = plugin_manager.get_plugin_instance("personality_plugin")
    
    if plugin_instance and isinstance(plugin_instance, PersonalityPlugin):
        # Create panel with plugin instance
        panel = Panel(container, plugin_instance)
        return panel
    else:
        import tkinter as tk
        # Show error if plugin is not available
        frame = tk.Frame(container)
        tk.Label(
            frame,
            text="Error: Personality plugin not loaded or active",
            foreground="red"
        ).pack(padx=10, pady=10)
        return frame