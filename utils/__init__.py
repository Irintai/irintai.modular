"""
Utilities module initialization for Irintai assistant
"""
# Import all utility modules for easy access
from .logger import IrintaiLogger, PluginLogger
from .system_monitor import SystemMonitor
from .file_ops import FileOps, SUPPORTED_EXTENSIONS, PluginSandboxedFileOps
from .plugin_event_bus import EventBus
from .plugin_dependency_manager import DependencyManager
from .attribute_checker import (
    check_required_attributes,
    verify_interface,
    safe_call,
    get_missing_attributes
)
from .runtime_patching import (
    ensure_attribute_exists,
    ensure_method_exists,
    patch_plugin_manager
)

__all__ = [
    'IrintaiLogger',
    'PluginLogger',
    'SystemMonitor',
    'FileOps',
    'SUPPORTED_EXTENSIONS',
    'PluginSandboxedFileOps',
    'EventBus',
    'DependencyManager',
    'check_required_attributes',
    'verify_interface',
    'safe_call',
    'get_missing_attributes'
]