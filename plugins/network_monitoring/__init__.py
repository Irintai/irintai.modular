"""
Network Monitoring Plugin - Entry Point
"""

# Import the core plugin class
from plugins.network_monitoring.core.network_monitoring import IrintaiPlugin as CorePlugin

# Define plugin metadata (can be copied or referenced from the core class if static)
METADATA = {
    "name": "Network Monitor",
    "description": "Monitors network traffic and API endpoint status.",
    "version": "1.0.0",
    "author": "Irintai Project Contributor", # Placeholder author
    "url": "https://example.com/plugins/network_monitor", # Placeholder URL
    "compatibility": "1.0.0", # Matches IrintAI Version
    "tags": ["network", "monitoring", "performance"]
}

class IrintaiPlugin:
    """Wrapper class for the Network Monitoring Plugin"""
    METADATA = METADATA

    def __init__(self, core_system, config_path=None, logger=None, **kwargs):
        # Pass the plugin ID explicitly or derive it
        plugin_id = METADATA["name"].lower().replace(" ", "_")
        self.plugin = CorePlugin(plugin_id, core_system)

    def activate(self):
        return self.plugin.activate()

    def deactivate(self):
        return self.plugin.deactivate()