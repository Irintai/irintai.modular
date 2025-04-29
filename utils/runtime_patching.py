"""
Runtime patching utilities for Irintai Assistant.

This module provides functions to patch and modify components at runtime,
enabling dynamic behavior modification and fixes without requiring restarts.
"""

import inspect
import logging
import types
import functools

def patch_method(instance, method_name, new_method):
    """
    Replace a method on an instance with a new implementation.
    
    Args:
        instance: The object instance to patch
        method_name: Name of the method to replace
        new_method: New method implementation
        
    Returns:
        The original method or None if method didn't exist
    """
    if not hasattr(instance, method_name):
        logging.warning(f"Cannot patch {method_name}: method does not exist")
        return None
        
    original_method = getattr(instance, method_name)
    setattr(instance, method_name, types.MethodType(new_method, instance))
    return original_method

def ensure_method_exists(instance, method_name, default_implementation):
    """
    Ensure a method exists on an instance, adding it if missing.
    
    Args:
        instance: The object instance to check/modify
        method_name: Name of the method to ensure exists
        default_implementation: Function to use if method is missing
        
    Returns:
        True if method was added, False if it already existed
    """
    if hasattr(instance, method_name):
        return False
        
    setattr(instance, method_name, types.MethodType(default_implementation, instance))
    return True

def create_patched_class(original_class, patches=None, additions=None):
    """
    Create a patched subclass of an original class.
    
    Args:
        original_class: The class to patch
        patches: Dict mapping method names to new implementations
        additions: Dict mapping new method names to implementations
        
    Returns:
        A new subclass with the specified modifications
    """
    patches = patches or {}
    additions = additions or {}
    
    class PatchedClass(original_class):
        pass
    
    # Apply patches by overriding methods
    for method_name, new_implementation in patches.items():
        if hasattr(original_class, method_name):
            setattr(PatchedClass, method_name, new_implementation)
    
    # Add new methods
    for method_name, implementation in additions.items():
        setattr(PatchedClass, method_name, implementation)
    
    return PatchedClass

def monkey_patch_module(module, patches):
    """
    Apply patches to a module.
    
    Args:
        module: The module to patch
        patches: Dict mapping attribute names to new values
        
    Returns:
        The number of successfully applied patches
    """
    count = 0
    for attr_name, new_value in patches.items():
        if hasattr(module, attr_name):
            setattr(module, attr_name, new_value)
            count += 1
    return count