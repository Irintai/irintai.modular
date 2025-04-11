"""
UI module initialization for Irintai assistant
"""
# Import all UI components for easy access
from .main_window import MainWindow
from .chat_panel import ChatPanel
from .model_panel import ModelPanel
from .memory_panel import MemoryPanel
from .config_panel import ConfigPanel
from .log_viewer import LogViewer
from .plugin_panel import PluginPanel
from .resource_monitor_panel import ResourceMonitorPanel
from .plugin_config_panel import PluginConfigPanel

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