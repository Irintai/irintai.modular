# File: plugins/model_training_performance/__init__.py
"""
Model Training Performance Plugin - Entry Point
"""

# Import the core plugin class
from plugins.model_training_performance.core.model_training_performance import IrintaiPlugin as CorePlugin

# Define plugin metadata (can be copied or referenced from the core class if static)
METADATA = {
    "name": "Model Training Performance Monitor",
    "description": "Monitors and tracks model performance metrics during inference/usage.",
    "version": "1.0.0",
    "author": "Irintai Project Contributor", # Placeholder author
    "url": "https://example.com/plugins/model_monitor", # Placeholder URL
    "compatibility": "1.0.0", # Matches IrintAI Version
    "tags": ["model", "performance", "monitoring", "resource"]
}

class IrintaiPlugin:
    """Wrapper class for the Model Training Performance Plugin"""
    METADATA = METADATA

    def __init__(self, core_system, config_path=None, logger=None, **kwargs):
        # Pass the plugin ID explicitly or derive it
        plugin_id = METADATA["name"].lower().replace(" ", "_")
        self.plugin = CorePlugin(plugin_id, core_system)

    def activate(self):
        return self.plugin.activate()

    def deactivate(self):
        return self.plugin.deactivate()