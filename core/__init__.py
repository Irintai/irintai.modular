"""
Core module initialization for Irintai assistant
"""
# Import all core modules for easy access
from .model_manager import ModelManager, MODEL_STATUS, RECOMMENDED_MODELS
from .chat_engine import ChatEngine
from .memory_system import MemorySystem
from .config_manager import ConfigManager, DEFAULT_CONFIG
from .plugin_manager import PluginManager

__all__ = [
    'ModelManager', 
    'MODEL_STATUS', 
    'RECOMMENDED_MODELS',
    'ChatEngine',
    'MemorySystem',
    'ConfigManager', 
    'DEFAULT_CONFIG'
    'PluginManager'
]