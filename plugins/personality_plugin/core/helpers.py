"""
Helper functions for the Personality Plugin
"""
import json
import os
import time
from typing import Dict, Any, List, Optional

def load_default_profiles() -> Dict[str, Any]:
    """
    Load default personality profiles from resources
    
    Returns:
        Dictionary of default profiles
    """
    # Try to load from resources file
    resource_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "resources",
        "default_profiles.json"
    )
    
    if os.path.exists(resource_path):
        try:
            with open(resource_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Fallback to hardcoded defaults
    return {
        "Standard": {
            "name": "Standard",
            "description": "Default balanced and neutral communication style",
            "tags": ["neutral", "balanced", "professional"],
            "author": "Irintai",
            "version": "1.0.0",
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prefix": "",
            "suffix": "",
            "style_modifiers": {
                "formality": 0.5,
                "creativity": 0.5,
                "complexity": 0.5,
                "empathy": 0.5,
                "directness": 0.5
            },
            "formatting": {
                "emphasize_key_points": False,
                "use_markdown": True,
                "paragraph_structure": "standard"
            }
        },
        # [Include other default profiles]
    }

def get_profile_metadata(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from a profile
    
    Args:
        profile: Profile data
        
    Returns:
        Dictionary with profile metadata
    """
    return {
        "name": profile.get("name", "Unknown"),
        "description": profile.get("description", ""),
        "tags": profile.get("tags", []),
        "author": profile.get("author", "Unknown"),
        "version": profile.get("version", "1.0.0"),
        "created": profile.get("created", "")
    }