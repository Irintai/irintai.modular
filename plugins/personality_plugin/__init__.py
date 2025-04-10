"""
Personality Plugin for Irintai Assistant
"""
from .core.personality_plugin import PersonalityPlugin
from .ui.panel import Panel


# Export the activate_ui function at the module level
__all__ = ['IrintaiPlugin', 'activate_ui']
class IrintaiPlugin:
    """
    Plugin wrapper that integrates core functionality with UI
    
    This class implements the standard Irintai plugin interface
    and connects the core plugin with its UI representation.
    """
    
    # Forward metadata from core plugin
    METADATA = PersonalityPlugin.METADATA
    
    # Forward status constants
    STATUS = PersonalityPlugin.STATUS
    
    def __init__(
        self, 
        core_system,
        config_path=None,
        logger=None,
        **kwargs
    ):
        """
        Initialize the plugin wrapper
        
        Args:
            core_system: Reference to Irintai core system
            config_path: Path to plugin configuration
            logger: Optional logging function
            **kwargs: Additional initialization parameters
        """
        # Create core plugin instance
        self.plugin = PersonalityPlugin(
            core_system,
            config_path,
            logger,
            **kwargs
        )
        
        # UI components (initialized on demand)
        self.ui_panel = None
    
    def get_ui_panel(self, parent):
        """
        Create and return UI panel
        
        Args:
            parent: Parent widget
            
        Returns:
            UI panel frame
        """
        if self.ui_panel is None:
            # Create UI panel
            panel = Panel(parent, self.plugin)
            self.ui_panel = panel.ui_panel
        
        return self.ui_panel
    
    # Forward core methods
    def activate(self):
        """Activate the plugin"""
        return self.plugin.activate()
    
    def deactivate(self):
        """Deactivate the plugin"""
        return self.plugin.deactivate()
    
    def update_configuration(self, **kwargs):
        """Update plugin configuration"""
        return self.plugin.update_configuration(**kwargs)
    
    def get_status(self):
        """Get plugin status"""
        return self.plugin.get_status()

# Plugin instantiation function
def get_plugin_instance(core_system, config_path=None, logger=None, **kwargs):
    """
    Create a plugin instance
    
    Args:
        core_system: Irintai core system
        config_path: Optional configuration path
        logger: Optional logger function
        **kwargs: Additional parameters
        
    Returns:
        Plugin instance
    """
    # Import the bridge
    from .bridge import PersonalityBridge
    
    # Apply compatibility bridge
    bridge = PersonalityBridge(core_system)
    bridge.ensure_compatibility()
    
    # Create and return plugin instance
    return IrintaiPlugin(core_system, config_path, logger, **kwargs)