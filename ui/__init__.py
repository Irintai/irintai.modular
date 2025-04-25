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
from ui.main_window import MainWindow
from ui.panels.resource_monitor_panel import ResourceMonitorPanel
from plugins.plugin_config_panel import PluginConfigPanel

__all__ = [
    'MainWindow',
    'ChatPanel',
    'ModelPanel',
    'MemoryPanel',
    'ConfigPanel',
    'LogViewer',
    'PluginPanel',
    'ResourceMonitorPanel',
    'PluginConfigPanel'
]