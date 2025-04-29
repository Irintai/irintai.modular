"""
Utility modules for IrintAI Assistant
"""

from utils.logger import IrintaiLogger
from utils.system_monitor import SystemMonitor
from file_operations.file_ops import FileOps
from plugins.plugin_event_bus import EventBus
from plugins.plugin_dependency_manager import DependencyManager
from core.settings_manager import SettingsManager

# Import runtime patching utilities
try:
    from diagnostics.runtime_patching import ensure_attribute_exists, ensure_method_exists, patch_plugin_manager
except ImportError:
    # These will be defined if the file doesn't exist
    pass

# Make the plugin settings fix available
try:
    from plugins.plugin_settings_fix import fix_plugin_settings_panel
except ImportError:
    # This is fine if the file doesn't exist
    pass

__all__ = ["IrintaiLogger", "SystemMonitor", "FileOps", "EventBus", "DependencyManager", "SettingsManager", "fix_plugin_settings_panel"]