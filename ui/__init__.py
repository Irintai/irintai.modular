"""
UI module initialization for Irintai assistant
"""
# Import all UI components for easy access
from ui.panels.chat_panel import ChatPanel
from ui.panels.model_panel import ModelPanel
from ui.panels.memory_panel import MemoryPanel
from ui.panels.config_panel import ConfigPanel
from ui.log_viewer import LogViewer
from ui.panels.plugin_panel import PluginPanel
from ui.panels.resource_monitor_panel import ResourceMonitorPanel
from plugins.plugin_config_panel import PluginConfigPanel
# Avoid circular imports - main_window is imported directly in irintai.py

__all__ = [
    'ChatPanel',
    'ModelPanel',
    'MemoryPanel',
    'ConfigPanel',
    'LogViewer',
    'PluginPanel',
    'ResourceMonitorPanel',
    'PluginConfigPanel']

# Added to resolve circular import
def _lazy_import():
    from ui.main_window import MainWindow  # Moved to avoid circular import
    pass