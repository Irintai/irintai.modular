"""
Version information for IrintAI Assistant
"""

# Version information in semantic versioning format (major.minor.patch)
VERSION = "1.1.0"

# Build information
BUILD_DATE = "2025-04-28"
BUILD_TYPE = "development"

# Version as tuple for comparison
VERSION_TUPLE = tuple(map(int, VERSION.split('.')))

def get_version_string(include_build: bool = False) -> str:
    """
    Get formatted version string
    
    Args:
        include_build: Whether to include build information
        
    Returns:
        Formatted version string
    """
    if include_build:
        return f"IrintAI Assistant v{VERSION} ({BUILD_TYPE} build, {BUILD_DATE})"
    return f"IrintAI Assistant v{VERSION}"