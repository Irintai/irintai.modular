"""
Terminal utilities for handling escape sequences and other terminal-related functions
"""
import re

# Regular expression to match ANSI escape sequences
ANSI_ESCAPE_PATTERN = re.compile(r'(\x1B\[[0-?]*[ -/]*[@-~]|\x1B[@-_]|[\x00-\x08\x0B-\x1F\x7F])')

def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI escape sequences from text
    
    Args:
        text: Input text that may contain ANSI escape sequences
        
    Returns:
        Clean text with escape sequences removed
    """
    if not text:
        return ""
    return ANSI_ESCAPE_PATTERN.sub('', text)
