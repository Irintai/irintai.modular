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

__all__ = [
    'MainWindow',
    'ChatPanel',
    'ModelPanel',
    'MemoryPanel',
    'ConfigPanel',
    'LogViewer'
]