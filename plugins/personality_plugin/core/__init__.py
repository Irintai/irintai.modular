"""
Personality Plugin Core Module - Provides functionality for modulating assistant's communication style

This module contains the core functionality for the Personality Plugin, including:
- The main PersonalityPlugin class
- Helper functions for profile management
- Utilities for text transformation and style analysis
"""

# Import the main plugin class
from plugins.personality_plugin.core.personality_plugin import PersonalityPlugin

# Import helper functions for easy access
from plugins.personality_plugin.core.helpers import (create_empty_profile,
    load_default_profiles,
    validate_profile,
    merge_profiles,
    calculate_style_vector,
    apply_style_transforms,
    find_similar_profiles,
    export_profile_to_file,
    import_profile_from_file,
    create_empty_profile)

# Package metadata
__version__ = "1.0.0"
__author__ = "Andrew"
__license__ = "MIT"

# Constants for profile aspects
STYLE_DIMENSIONS = [
    "formality",
    "creativity", 
    "complexity",
    "empathy", 
    "directness",
    "humor",
    "enthusiasm", 
    "conciseness"
]

# Default style values
DEFAULT_STYLE = {dim: 0.5 for dim in STYLE_DIMENSIONS}

# Export public interface
__all__ = [
    # Main class
    'PersonalityPlugin',
    
    # Helper functions
    'load_default_profiles',
    'validate_profile',
    'merge_profiles',
    'calculate_style_vector',
    'apply_style_transforms',
    'find_similar_profiles',
    'export_profile_to_file',
    'import_profile_from_file',
    'create_empty_profile',
    
    # Constants
    'STYLE_DIMENSIONS',
    'DEFAULT_STYLE',
    
    # Metadata
    '__version__',
    '__author__',
    '__license__'
]