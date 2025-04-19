#!/usr/bin/env python3
"""
Attribute Checker - Utility for checking object attributes
Helps prevent 'AttributeError: X has no attribute Y' errors by pre-checking objects
"""

import inspect
from typing import Any, List, Dict, Optional, Callable


def check_required_attributes(obj: Any, attributes: List[str], 
                             obj_name: Optional[str] = None,
                             logger: Optional[Callable] = None) -> bool:
    """
    Check if an object has all the required attributes.
    
    Args:
        obj: The object to check
        attributes: List of attribute names that should exist on the object
        obj_name: Name of the object for better error messages (defaults to obj.__class__.__name__)
        logger: Optional logging function
        
    Returns:
        True if all attributes exist, False otherwise
    """
    if obj is None:
        if logger:
            logger(f"[ERROR] Object check failed: Object is None")
        return False
    
    missing_attrs = []
    obj_name = obj_name or obj.__class__.__name__
    
    for attr in attributes:
        if not hasattr(obj, attr):
            missing_attrs.append(attr)
            
    if missing_attrs:
        error_msg = f"[ERROR] Object '{obj_name}' is missing required attributes: {', '.join(missing_attrs)}"
        if logger:
            logger(error_msg)
        return False
        
    return True


def verify_interface(obj: Any, interface_methods: List[str], 
                     obj_name: Optional[str] = None,
                     verify_callable: bool = True,
                     logger: Optional[Callable] = None) -> bool:
    """
    Verify that an object implements all methods in an interface.
    
    Args:
        obj: The object to check
        interface_methods: List of method names that should exist on the object
        obj_name: Name of the object for better error messages
        verify_callable: If True, verify that attributes are actually callable
        logger: Optional logging function
        
    Returns:
        True if object implements all methods, False otherwise
    """
    if obj is None:
        if logger:
            logger(f"[ERROR] Interface verification failed: Object is None")
        return False
        
    missing_methods = []
    not_callable = []
    obj_name = obj_name or obj.__class__.__name__
    
    for method in interface_methods:
        if not hasattr(obj, method):
            missing_methods.append(method)
        elif verify_callable and not callable(getattr(obj, method)):
            not_callable.append(method)
            
    if missing_methods:
        error_msg = f"[ERROR] Object '{obj_name}' is missing required methods: {', '.join(missing_methods)}"
        if logger:
            logger(error_msg)
        return False
            
    if not_callable:
        error_msg = f"[ERROR] Attributes of '{obj_name}' are not callable: {', '.join(not_callable)}"
        if logger:
            logger(error_msg)
        return False
            
    return True


def safe_call(obj: Any, method_name: str, args: List = None, 
              kwargs: Dict = None, default_return: Any = None, 
              logger: Optional[Callable] = None) -> Any:
    """
    Safely call a method on an object, handling AttributeError and other exceptions.
    
    Args:
        obj: The object containing the method
        method_name: Name of the method to call
        args: Positional arguments to pass to the method
        kwargs: Keyword arguments to pass to the method
        default_return: Value to return if the call fails
        logger: Optional logging function
        
    Returns:
        The result of the method call, or default_return if the call fails
    """
    args = args or []
    kwargs = kwargs or {}
    
    if obj is None:
        if logger:
            logger(f"[ERROR] Safe call failed: Object is None for method '{method_name}'")
        return default_return
        
    try:
        if hasattr(obj, method_name):
            method = getattr(obj, method_name)
            if callable(method):
                return method(*args, **kwargs)
            else:
                if logger:
                    logger(f"[ERROR] Attribute '{method_name}' is not callable on {obj.__class__.__name__}")
        else:
            if logger:
                logger(f"[ERROR] Object {obj.__class__.__name__} has no attribute '{method_name}'")
    except Exception as e:
        if logger:
            logger(f"[ERROR] Exception in safe_call to '{method_name}': {str(e)}")
            
    return default_return


def get_missing_attributes(obj: Any, attribute_list: List[str]) -> List[str]:
    """
    Get a list of attributes that are missing from an object.
    
    Args:
        obj: The object to check
        attribute_list: List of attribute names to check for
        
    Returns:
        List of missing attribute names
    """
    if obj is None:
        return attribute_list
        
    return [attr for attr in attribute_list if not hasattr(obj, attr)]
