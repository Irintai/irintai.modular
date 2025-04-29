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
        except Exception as e:
            print(f"Error loading default profiles: {e}")
    
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
                "directness": 0.5,
                "humor": 0.5,
                "enthusiasm": 0.5,
                "conciseness": 0.5
            },
            "formatting": {
                "emphasize_key_points": False,
                "use_markdown": True,
                "paragraph_structure": "standard"
            },
            "text_replacements": {}
        },
        "Friendly": {
            "name": "Friendly",
            "description": "Warm and conversational communication style",
            "tags": ["warm", "casual", "conversational"],
            "author": "Irintai",
            "version": "1.0.0",
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prefix": "Hey there! ",
            "suffix": "",
            "style_modifiers": {
                "formality": 0.3,
                "creativity": 0.6,
                "complexity": 0.4,
                "empathy": 0.8,
                "directness": 0.6,
                "humor": 0.7,
                "enthusiasm": 0.8,
                "conciseness": 0.5
            },
            "formatting": {
                "emphasize_key_points": True,
                "use_markdown": True,
                "paragraph_structure": "conversational"
            },
            "text_replacements": {}
        },
        "Professional": {
            "name": "Professional",
            "description": "Formal and business-oriented communication style",
            "tags": ["formal", "business", "expert"],
            "author": "Irintai",
            "version": "1.0.0",
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prefix": "",
            "suffix": "",
            "style_modifiers": {
                "formality": 0.9,
                "creativity": 0.4,
                "complexity": 0.7,
                "empathy": 0.5,
                "directness": 0.8,
                "humor": 0.2,
                "enthusiasm": 0.5,
                "conciseness": 0.7
            },
            "formatting": {
                "emphasize_key_points": True,
                "use_markdown": True,
                "paragraph_structure": "structured"
            },
            "text_replacements": {}
        },
        "Creative": {
            "name": "Creative",
            "description": "Imaginative and expressive communication style",
            "tags": ["creative", "expressive", "imaginative"],
            "author": "Irintai",
            "version": "1.0.0",
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prefix": "",
            "suffix": "",
            "style_modifiers": {
                "formality": 0.4,
                "creativity": 0.9,
                "complexity": 0.6,
                "empathy": 0.7,
                "directness": 0.4,
                "humor": 0.7,
                "enthusiasm": 0.8,
                "conciseness": 0.3
            },
            "formatting": {
                "emphasize_key_points": True,
                "use_markdown": True,
                "paragraph_structure": "creative"
            },
            "text_replacements": {}
        }
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

def validate_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a profile and ensure it has all required fields
    
    Args:
        profile: Profile data to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {"valid": True, "errors": [], "warnings": []}
    
    # Required fields
    required_fields = ["name", "description"]
    for field in required_fields:
        if field not in profile:
            result["valid"] = False
            result["errors"].append(f"Missing required field: {field}")
    
    # Check style modifiers
    style_modifiers = profile.get("style_modifiers", {})
    if not isinstance(style_modifiers, dict):
        result["valid"] = False
        result["errors"].append("style_modifiers must be a dictionary")
    else:
        # Validate modifier values are between 0 and 1
        for mod_name, mod_value in style_modifiers.items():
            if not isinstance(mod_value, (int, float)) or mod_value < 0 or mod_value > 1:
                result["warnings"].append(f"Style modifier '{mod_name}' should be between 0 and 1")
    
    # Check for formatting settings
    if "formatting" in profile and not isinstance(profile["formatting"], dict):
        result["warnings"].append("formatting should be a dictionary")
    
    return result

def merge_profiles(base_profile: Dict[str, Any], overlay_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two profiles, with overlay values taking precedence
    
    Args:
        base_profile: Base profile to start with
        overlay_profile: Profile whose values will override the base
        
    Returns:
        New merged profile
    """
    # Create a deep copy of the base profile
    merged = base_profile.copy()
    
    # Merge top-level fields, excluding nested dictionaries
    for key, value in overlay_profile.items():
        if key not in merged or not isinstance(value, dict):
            merged[key] = value
    
    # Merge style modifiers
    base_modifiers = merged.get("style_modifiers", {})
    overlay_modifiers = overlay_profile.get("style_modifiers", {})
    merged["style_modifiers"] = {**base_modifiers, **overlay_modifiers}
    
    # Merge formatting settings
    base_formatting = merged.get("formatting", {})
    overlay_formatting = overlay_profile.get("formatting", {})
    merged["formatting"] = {**base_formatting, **overlay_formatting}
    
    # Update metadata
    merged["name"] = overlay_profile.get("name", merged.get("name", "Merged Profile"))
    merged["description"] = overlay_profile.get("description", merged.get("description", ""))
    
    # Add merge metadata
    merged["merged_from"] = [
        base_profile.get("name", "Unknown"),
        overlay_profile.get("name", "Unknown")
    ]
    merged["version"] = overlay_profile.get("version", "1.0.0")
    merged["created"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    return merged

def calculate_style_vector(profile: Dict[str, Any]) -> List[float]:
    """
    Calculate a numerical vector representation of a profile's style
    
    Args:
        profile: Personality profile
        
    Returns:
        List of normalized values representing the style
    """
    # Standard style dimensions in a consistent order
    dimensions = [
        "formality", "creativity", "complexity", 
        "empathy", "directness", "humor", 
        "enthusiasm", "conciseness"
    ]
    
    # Get style modifiers or empty dict if not present
    style_modifiers = profile.get("style_modifiers", {})
    
    # Create vector with default value of 0.5 for missing dimensions
    vector = [style_modifiers.get(dim, 0.5) for dim in dimensions]
    
    return vector

def apply_style_transforms(text: str, profile: Dict[str, Any]) -> str:
    """
    Apply style transformations to text based on profile settings
    
    Args:
        text: Input text to transform
        profile: Personality profile with transformation rules
        
    Returns:
        Transformed text
    """
    if not text or not profile:
        return text
        
    result = text
    
    # Apply prefix/suffix
    prefix = profile.get("prefix", "")
    suffix = profile.get("suffix", "")
    
    if prefix:
        result = prefix + result
    if suffix:
        result = result + suffix
    
    # Apply text replacements
    replacements = profile.get("text_replacements", {})
    for original, replacement in replacements.items():
        result = result.replace(original, replacement)
    
    # Apply formatting
    formatting = profile.get("formatting", {})
    
    # Emphasize key points if enabled
    if formatting.get("emphasize_key_points", False):
        # Simple heuristic: look for sentences with important-sounding phrases
        import re
        for phrase in ["important", "key", "critical", "essential", "crucial"]:
            pattern = re.compile(f"([^.!?]*{phrase}[^.!?]*[.!?])", re.IGNORECASE)
            result = pattern.sub(r"**\1**", result)
    
    # Convert to markdown if enabled and not already markdown
    if formatting.get("use_markdown", True) and "```" not in result and "**" not in result:
        # Simple conversion: add some basic markdown formatting
        # This is simplified and would need more sophisticated logic in a real implementation
        import re
        
        # Add headers for sections that appear to be headings
        result = re.sub(r"(?m)^([A-Z][A-Za-z\s]+):\s*$", r"## \1", result)
        
        # Add bullet points for lists (lines starting with - or *)
        result = re.sub(r"(?m)^(\s*)[•-]\s+", r"\1* ", result)
        
    return result

def find_similar_profiles(query: str, profiles: Dict[str, Any], 
                          max_results: int = 3) -> List[str]:
    """
    Find profiles similar to a query string
    
    Args:
        query: Search query
        profiles: Dictionary of available profiles
        max_results: Maximum number of results to return
        
    Returns:
        List of profile names sorted by relevance
    """
    if not query or not profiles:
        return []
        
    # Calculate relevance scores for each profile
    scores = []
    query = query.lower()
    
    for name, profile in profiles.items():
        score = 0
        
        # Check name match
        if query in name.lower():
            score += 10
        
        # Check description match
        description = profile.get("description", "").lower()
        if query in description:
            score += 5
        
        # Check tag matches
        for tag in profile.get("tags", []):
            if query in tag.lower():
                score += 3
        
        # Only include profiles with non-zero scores
        if score > 0:
            scores.append((name, score))
    
    # Sort by score (descending) and take top results
    scores.sort(key=lambda x: x[1], reverse=True)
    return [name for name, score in scores[:max_results]]

def export_profile_to_file(profile: Dict[str, Any], file_path: str) -> bool:
    """
    Export a profile to a JSON file
    
    Args:
        profile: Profile data to export
        file_path: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save to file with pretty formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error exporting profile: {e}")
        return False

def import_profile_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Import a profile from a JSON file
    
    Args:
        file_path: Path to the profile file
        
    Returns:
        Profile data or None if import failed
    """
    if not os.path.exists(file_path):
        return None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
            
        # Validate the imported profile
        validation = validate_profile(profile)
        if not validation["valid"]:
            print(f"Invalid profile: {', '.join(validation['errors'])}")
            return None
            
        return profile
    except Exception as e:
        print(f"Error importing profile: {e}")
        return None

def create_empty_profile(name: str = "New Profile") -> Dict[str, Any]:
    """
    Create a new empty profile template
    
    Args:
        name: Name for the new profile
        
    Returns:
        Dictionary with empty profile structure
    """
    return {
        "name": name,
        "description": "Custom personality profile",
        "tags": ["custom"],
        "author": "User",
        "version": "1.0.0",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": "",
        "suffix": "",
        "style_modifiers": {
            "formality": 0.5,
            "creativity": 0.5,
            "complexity": 0.5,
            "empathy": 0.5,
            "directness": 0.5,
            "humor": 0.5,
            "enthusiasm": 0.5,
            "conciseness": 0.5
        },
        "formatting": {
            "emphasize_key_points": False,
            "use_markdown": True,
            "paragraph_structure": "standard"
        },
        "text_replacements": {}
    }