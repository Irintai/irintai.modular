#!/usr/bin/env python3
"""
IrintAI Assistant - Enhanced Diagnostic Tool
This script performs a comprehensive diagnostic check of the IrintAI Assistant system
to identify configuration issues, missing dependencies, code problems, and attribute errors.
"""

import os
import sys
import importlib
import traceback
import json
import subprocess
import platform
import time
import inspect
import re
import shutil
from pathlib import Path
import logging

def extract_class_methods_from_code(code_content, class_name):
    """
    Parse Python code to extract methods defined in a specific class
    
    Args:
        code_content: String containing Python code
        class_name: Name of the class to examine
        
    Returns:
        List of method names defined in the class
    """
    methods = []
    
    # Find the class definition
    class_pattern = rf"class\s+{class_name}\s*\(.*?\):"
    class_match = re.search(class_pattern, code_content)
    
    if not class_match:
        return methods
    
    # Find the start position of the class body
    start_pos = class_match.end()
    
    # Simple method to find proper indentation of the class
    lines = code_content[start_pos:].split("\n")
    if not lines:
        return methods
    
    # Find class indentation level by looking at first non-empty line after class definition
    class_indent = 0
    for line in lines:
        if line.strip():
            class_indent = len(line) - len(line.lstrip())
            break
    
    # Find method definitions with proper indentation
    method_pattern = rf"^\s{{{class_indent+4}}}def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
    
    # Search for methods in the code after the class definition
    for line in lines:
        if line.strip() and len(line) - len(line.lstrip()) == class_indent + 4:
            method_match = re.match(method_pattern, line)
            if method_match:
                method_name = method_match.group(1)
                # Skip private methods (starting with _)
                if not method_name.startswith("__"):
                    methods.append(method_name)
    
    return methods

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("irintai_diagnostic.log")
    ]
)
logger = logging

def print_header(text):
    """Print a section header"""
    print(f"\n{'=' * 80}")
    print(f" {text}")
    print(f"{'=' * 80}")
    logger.info(f"SECTION: {text}")

def check_environment():
    """Check the system environment"""
    print_header("SYSTEM ENVIRONMENT")
    
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Current Directory: {os.getcwd()}")
    
    # Check for critical environment variables
    env_vars = ["OLLAMA_HOME", "OLLAMA_MODELS"]
    for var in env_vars:
        value = os.environ.get(var)
        status = "✓ SET" if value else "✗ MISSING"
        print(f"{var}: {status} {f'({value})' if value else ''}")
    
    return True

def check_file_structure():
    """Verify the integrity of the file structure"""
    print_header("FILE STRUCTURE")
    
    critical_files = [
        "irintai.py", 
        "core/__init__.py",
        "core/plugin_manager.py",
        "core/model_manager.py",
        "core/chat_engine.py",
        "ui/main_window.py",
        "data/config.json"
    ]
    
    critical_dirs = [
        "plugins",
        "data/logs",
        "data/models",
        "data/plugins"
    ]
    
    issues_found = False
    
    print("Checking critical files:")
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (MISSING)")
            issues_found = True
    
    print("\nChecking critical directories:")
    for dir_path in critical_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} (MISSING)")
            issues_found = True
    
    if issues_found:
        print("\n⚠ Some critical files or directories are missing!")
    else:
        print("\n✓ All critical files and directories are present")
    
    # Check plugin directory
    if os.path.exists("plugins"):
        plugins = [d for d in os.listdir("plugins") if os.path.isdir(os.path.join("plugins", d))]
        print(f"\nFound {len(plugins)} plugin directories: {', '.join(plugins)}")
        
        for plugin in plugins:
            plugin_dir = os.path.join("plugins", plugin)
            init_file = os.path.join(plugin_dir, "__init__.py")
            manifest_file = os.path.join(plugin_dir, "manifest.json")
            
            if not os.path.exists(init_file):
                print(f"  ⚠ {plugin}: Missing __init__.py file")
                issues_found = True
                
            if not os.path.exists(manifest_file):
                print(f"  ⚠ {plugin}: Missing manifest.json file")
                issues_found = True
            else:
                # Check manifest.json structure
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                        
                    required_keys = ["name", "version", "description"]
                    missing_keys = [key for key in required_keys if key not in manifest]
                    
                    if missing_keys:
                        print(f"  ⚠ {plugin}: Manifest missing required fields: {', '.join(missing_keys)}")
                        issues_found = True
                except json.JSONDecodeError:
                    print(f"  ⚠ {plugin}: Invalid JSON in manifest.json")
                    issues_found = True
                except Exception as e:
                    print(f"  ⚠ {plugin}: Error reading manifest.json: {str(e)}")
                    issues_found = True
    
    return not issues_found

def check_dependencies():
    """Check Python dependencies"""
    print_header("DEPENDENCY CHECK")
    
    # Try to locate requirements.txt files
    requirements_files = [
        "requirements.txt",
        "docs/requirements.txt"
    ]
    
    found_file = None
    for file in requirements_files:
        if os.path.exists(file):
            found_file = file
            break
    
    if not found_file:
        print("⚠ No requirements.txt file found!")
        return False
    
    print(f"Using requirements from: {found_file}")
    
    # Parse requirements
    try:
        with open(found_file, 'r') as file:
            requirements = [line.strip() for line in file if line.strip() and not line.startswith('#')]
        
        print(f"Found {len(requirements)} dependencies in requirements file")
        
        # Check each dependency
        missing = []
        for req in requirements:
            # Extract package name from requirement line
            package = req.split('==')[0].split('>=')[0].strip()
            
            # Handle special cases for package names vs import names
            import_name = package
            if package == "python-docx":
                import_name = "docx"
            elif package == "sentence-transformers":
                import_name = "sentence_transformers"
            elif package == "pillow":
                import_name = "PIL"
            
            try:
                # Try to import the module
                importlib.import_module(import_name)
                print(f"  ✓ {package}")
            except ImportError:
                # Try pip show as a fallback
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "show", package],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print(f"  ⚠ {package} (INSTALLED BUT IMPORT FAILED)")
                    else:
                        missing.append(package)
                        print(f"  ✗ {package} (MISSING)")
                except Exception:
                    missing.append(package)
                    print(f"  ✗ {package} (MISSING)")
        
        if missing:
            print(f"\n⚠ {len(missing)} dependencies are missing!")
            print("\nTo install missing dependencies, run:")
            print(f"pip install -r {found_file}")
        else:
            print("\n✓ All dependencies are installed")
            
    except Exception as e:
        print(f"⚠ Error checking dependencies: {e}")
        return False
    
    return len(missing) == 0

def check_config():
    """Check configuration files"""
    print_header("CONFIGURATION CHECK")
    
    if not os.path.exists("data/config.json"):
        print("⚠ Main config file (data/config.json) is missing!")
        return False
    
    try:
        with open("data/config.json", 'r') as file:
            config = json.load(file)
        
        print("✓ Successfully loaded main configuration")
        
        # Check critical configuration keys
        critical_keys = ["model", "system_prompt", "autoload_plugins"]
        missing_keys = [key for key in critical_keys if key not in config]
        
        if missing_keys:
            print(f"⚠ Missing critical config keys: {', '.join(missing_keys)}")
        else:
            print("✓ All critical configuration keys are present")
            
        # Print some config info
        print("\nCurrent configuration:")
        if "model" in config:
            print(f"  - Model: {config['model']}")
        else:
            # Check for equivalent keys
            model_alternatives = ["model_path", "default_model", "current_model"]
            for alt in model_alternatives:
                if alt in config:
                    print(f"  - {alt}: {config[alt]} (alternative to 'model')")
                    break
            
        if "system_prompt" in config:
            prompt = config["system_prompt"]
            # Truncate long prompts
            if len(prompt) > 100:
                prompt = prompt[:97] + "..."
            print(f"  - System prompt: {prompt}")
        elif "system_message" in config:
            prompt = config["system_message"]
            if len(prompt) > 100:
                prompt = prompt[:97] + "..."
            print(f"  - System message: {prompt} (alternative to 'system_prompt')")
            
        if "autoload_plugins" in config:
            print(f"  - Auto-load plugins: {', '.join(config.get('autoload_plugins', []))}")
            
    except json.JSONDecodeError:
        print("⚠ The config.json file contains invalid JSON!")
        return False
    except Exception as e:
        print(f"⚠ Error checking configuration: {e}")
        return False
    
    return True

def check_class_attributes(class_obj, required_attributes, class_name=None):
    """Check if a class has all the required attributes"""
    class_name = class_name or class_obj.__name__
    missing_attrs = []
    
    for attr in required_attributes:
        if not hasattr(class_obj, attr):
            missing_attrs.append(attr)
    
    return missing_attrs

def check_plugin_manager():
    """Check the plugin manager implementation"""
    print_header("PLUGIN MANAGER CHECK")
    
    if not os.path.exists("core/plugin_manager.py"):
        print("⚠ Plugin manager file is missing!")
        return False
    
    try:
        # Add the current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Try to import the plugin manager
        from core.plugin_manager import PluginManager
        
        # Read the plugin_manager.py file to analyze its content directly
        with open("core/plugin_manager.py", "r") as file:
            plugin_manager_code = file.read()
            
        # Parse the file to detect methods defined in the PluginManager class
        defined_methods = extract_class_methods_from_code(plugin_manager_code, "PluginManager")
        print(f"Found {len(defined_methods)} methods defined in PluginManager class")
        
        # Instantiate the plugin manager
        plugin_manager = PluginManager()
        
        # Define required methods and their descriptions
        required_methods = [
            ("set_error_handler", "Handles UI error callbacks from plugins"),
            ("discover_plugins", "Discovers available plugins in the plugin directory"),
            ("load_plugin", "Loads a specific plugin by name"), 
            ("activate_plugin", "Activates a loaded plugin"), 
            ("deactivate_plugin", "Deactivates a running plugin"),
            ("unload_plugin", "Unloads a specific plugin from memory"),
            ("unload_all_plugins", "Unloads all plugins when application exits"),
            ("auto_load_plugins", "Automatically loads plugins marked for auto-loading"),
            ("get_plugin_metadata", "Retrieves metadata for a specific plugin"),
            ("get_all_plugins", "Retrieves information about all plugins"),
            ("reload_plugin", "Reloads a plugin by unloading and loading it again")
        ]
        
        # Check each required method
        missing_methods = []
        for method, description in required_methods:
            if hasattr(plugin_manager, method):
                print(f"✓ PluginManager has '{method}' method")
            else:
                missing_methods.append((method, description))
                print(f"⚠ PluginManager is missing '{method}' method! - {description}")
        
        if "set_error_handler" in missing_methods:
            print("\n⚠ CRITICAL: PluginManager is missing 'set_error_handler' method!")
            print("This will cause UI initialization to fail with AttributeError.")
            print("\nSuggested fix in core/plugin_manager.py:")
            print("\n    def set_error_handler(self, handler_func):")
            print('        """Set a callback function to handle plugin errors"""')
            print("        self.error_handler = handler_func")
        
        # Check for common attributes
        required_attributes = ["plugins", "plugin_statuses", "plugin_dir", "config_dir"]
        missing_attributes = []
        for attr in required_attributes:
            if hasattr(plugin_manager, attr):
                print(f"✓ PluginManager has '{attr}' attribute")
            else:
                missing_attributes.append(attr)
                print(f"⚠ PluginManager is missing '{attr}' attribute!")
        
        # Check implementation of critical methods
        if hasattr(plugin_manager, "discover_plugins"):
            try:
                plugin_count = plugin_manager.discover_plugins()
                print(f"✓ discover_plugins method works (found {plugin_count} plugins)")
            except Exception as e:
                print(f"⚠ Error calling discover_plugins: {str(e)}")
        
        return len(missing_methods) == 0 and len(missing_attributes) == 0
        
    except ImportError:
        print("⚠ Could not import PluginManager!")
        return False
    except Exception as e:
        print(f"⚠ Error checking plugin manager: {e}")
        traceback.print_exc()
        return False

def check_interface_consistency():
    """Check for interface consistency across core components"""
    print_header("INTERFACE CONSISTENCY CHECK")
    
    try:
        # Add the current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Import core components for inspection
        classes_to_check = [
            ("core.plugin_manager", "PluginManager"),
            ("core.model_manager", "ModelManager"),
            ("core.chat_engine", "ChatEngine"),
            ("core.memory_system", "MemorySystem"),
            ("ui.main_window", "MainWindow")
        ]
        
        interface_issues = False
        
        for module_name, class_name in classes_to_check:
            try:
                module = importlib.import_module(module_name)
                class_obj = getattr(module, class_name)
                
                print(f"Checking {class_name} interface...")
                
                # Extract expected method calls from other files
                expected_methods = find_expected_methods(class_name)
                if expected_methods:
                    print(f"Found {len(expected_methods)} expected methods for {class_name}")
                    
                    # Check if all expected methods exist
                    missing = []
                    for method in expected_methods:
                        if not hasattr(class_obj, method):
                            missing.append(method)
                            
                    if missing:
                        print(f"⚠ {class_name} is missing expected methods: {', '.join(missing)}")
                        print("This could lead to AttributeError exceptions at runtime.")
                        interface_issues = True
                    else:
                        print(f"✓ {class_name} implements all expected methods")
                
            except ImportError:
                print(f"⚠ Could not import {module_name}.{class_name}")
                interface_issues = True
            except Exception as e:
                print(f"⚠ Error checking {class_name}: {str(e)}")
                interface_issues = True
        
        if not interface_issues:
            print("\n✓ All core components have consistent interfaces")
            return True
        else:
            print("\n⚠ Interface inconsistencies detected")
            return False
            
    except Exception as e:
        print(f"⚠ Error in interface consistency check: {str(e)}")
        return False

def find_expected_methods(class_name):
    """Find method calls on instances of a specific class throughout the codebase"""
    methods = set()
    base_dir = os.getcwd()
    
    # Look for patterns like self.class_name.method_name or obj.method_name
    pattern = f"{class_name.lower()}\\."
    pattern_alt = r"self\.[a-zA-Z_]+\."
    
    # Directories to search
    dirs_to_search = ["core", "ui", "utils"]
    
    for directory in dirs_to_search:
        dir_path = os.path.join(base_dir, directory)
        if not os.path.exists(dir_path):
            continue
            
        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Simple regex would be more robust but for this demo
                    # we'll just do basic string checks
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        
                        # Skip comments
                        if line.startswith('#'):
                            continue
                            
                        # Look for method calls
                        if f".{class_name.lower()}." in line.lower() or pattern_alt in line.lower():
                            # Extract method name - this is a simple approach
                            parts = line.split('.')
                            if len(parts) >= 3:
                                # The method name would be after the object reference
                                method_part = parts[2].split('(')[0].strip()
                                methods.add(method_part)
                                
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    return list(methods)

def check_logs():
    """Check recent log files"""
    print_header("LOG ANALYSIS")
    
    log_file = "irintai_debug.log"
    if not os.path.exists(log_file):
        log_dir = "data/logs"
        if os.path.exists(log_dir):
            log_files = sorted([f for f in os.listdir(log_dir) if f.startswith("irintai_debug_")], reverse=True)
            if log_files:
                log_file = os.path.join(log_dir, log_files[0])
                print(f"Using most recent log: {log_file}")
            else:
                print("⚠ No log files found!")
                return False
        else:
            print("⚠ Log directory not found!")
            return False
    
    try:
        with open(log_file, 'r') as file:
            # Read the last 50 lines of the log
            lines = file.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines
            
            print(f"Analyzing {len(last_lines)} log entries from {log_file}")
            
            errors = [line for line in last_lines if "[ERROR]" in line]
            warnings = [line for line in last_lines if "[WARNING]" in line or "[WARN]" in line]
            
            # Look specifically for attribute errors
            attribute_errors = [line for line in errors if "AttributeError" in line]
            
            if attribute_errors:
                print(f"\n⚠ Found {len(attribute_errors)} AttributeError entries in the log:")
                for error in attribute_errors:
                    print(f"  {error.strip()}")
            
            if errors:
                print(f"\n⚠ Found {len(errors)} ERROR entries in the log:")
                for error in errors[:5]:  # Limit to first 5 errors
                    print(f"  {error.strip()}")
                if len(errors) > 5:
                    print(f"  ... (and {len(errors) - 5} more)")
                    
            if warnings:
                print(f"\n⚠ Found {len(warnings)} WARNING entries in the log:")
                for warning in warnings[:5]:  # Limit to first 5 warnings
                    print(f"  {warning.strip()}")
                if len(warnings) > 5:
                    print(f"  ... (and {len(warnings) - 5} more)")
                    
            if not errors and not warnings:
                print("✓ No errors or warnings found in recent logs")
                
            # Pattern recognition in errors
            patterns = {
                "attribute_error": (r"AttributeError: '.*' object has no attribute '.*'", 
                                   "Missing attributes or methods - consider using the runtime_patching.py utility"),
                "module_error": (r"ModuleNotFoundError: No module named '.*'",
                                "Missing Python module - check your dependencies"),
                "key_error": (r"KeyError: '.*'",
                             "Dictionary key error - check your configuration and data structures"),
                "value_error": (r"ValueError",
                               "Value error - check parameter types and values"),
                "index_error": (r"IndexError",
                               "Index error - list index out of range"),
                "file_error": (r"FileNotFoundError",
                              "File not found - check file paths")
            }
            
            pattern_counts = {name: 0 for name in patterns}
            
            for line in errors:
                for pattern_name, (pattern, _) in patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        pattern_counts[pattern_name] += 1
            
            recurring_issues = [(name, count) for name, count in pattern_counts.items() if count > 0]
            if recurring_issues:
                print("\n⚠ Recurring error patterns detected:")
                for name, count in recurring_issues:
                    pattern, suggestion = patterns[name]
                    print(f"  - {name}: {count} occurrences - {suggestion}")
                
    except Exception as e:
        print(f"⚠ Error analyzing log files: {e}")
        return False
    
    return True

def check_runtime_patching():
    """Check if runtime patching utilities are available and properly configured"""
    print_header("RUNTIME PATCHING CHECK")
    
    # Check for the runtime_patching.py utility
    if not os.path.exists("utils/runtime_patching.py"):
        print("⚠ runtime_patching.py utility not found!")
        print("This utility can help prevent AttributeError crashes.")
        print("Consider adding this file to provide automatic attribute error handling.")
        return False
    
    try:
        # Check if it's properly integrated in the main application
        with open("irintai.py", 'r') as f:
            content = f.read()
            
        if "runtime_patching" in content and "patch_plugin_manager" in content:
            print("✓ Runtime patching is integrated in the main application")
            
            # Check if utils/__init__.py imports and exposes these functions
            with open("utils/__init__.py", 'r') as f:
                init_content = f.read()
                
            if "runtime_patching" in init_content:
                print("✓ Runtime patching is properly exposed in utils/__init__.py")
            else:
                print("⚠ Runtime patching is not properly exposed in utils/__init__.py")
                print("Add the following to utils/__init__.py:")
                print("from .runtime_patching import ensure_attribute_exists, ensure_method_exists, patch_plugin_manager")
                print('__all__ += ["ensure_attribute_exists", "ensure_method_exists", "patch_plugin_manager"]')
        else:
            print("⚠ Runtime patching is not integrated in the main application")
            print("Consider adding the following to irintai.py after creating the plugin manager:")
            print("from utils.runtime_patching import patch_plugin_manager")
            print("plugin_manager = patch_plugin_manager(plugin_manager)")
        
        # Try to import and use the patching utility
        sys.path.insert(0, os.getcwd())
        from diagnostics.runtime_patching import patch_plugin_manager, ensure_method_exists
        
        # Create a test object to verify the patching works
        class TestObject:
            pass
            
        test_obj = TestObject()
        ensure_method_exists(test_obj, "test_method")
        
        if hasattr(test_obj, "test_method"):
            print("✓ Runtime patching utility is working correctly")
            return True
        else:
            print("⚠ Runtime patching utility is not working correctly")
            return False
            
    except ImportError:
        print("⚠ Could not import runtime_patching module!")
        return False
    except Exception as e:
        print(f"⚠ Error checking runtime patching: {e}")
        return False

def check_model_environment():
    """Check model environment variables and directories"""
    print_header("MODEL ENVIRONMENT CHECK")
    
    issues_found = False
    
    # Check environment variables
    ollama_home = os.environ.get("OLLAMA_HOME")
    ollama_models = os.environ.get("OLLAMA_MODELS")
    
    # Check OLLAMA_HOME
    if ollama_home:
        print(f"✓ OLLAMA_HOME is set: {ollama_home}")
        if not os.path.exists(ollama_home):
            print(f"⚠ OLLAMA_HOME directory does not exist: {ollama_home}")
            issues_found = True
        elif not os.path.isdir(ollama_home):
            print(f"⚠ OLLAMA_HOME is not a directory: {ollama_home}")
            issues_found = True
        elif not os.access(ollama_home, os.R_OK | os.W_OK):
            print(f"⚠ OLLAMA_HOME has insufficient permissions: {ollama_home}")
            issues_found = True
    else:
        print("⚠ OLLAMA_HOME is not set")
        issues_found = True
    
    # Check OLLAMA_MODELS
    if ollama_models:
        print(f"✓ OLLAMA_MODELS is set: {ollama_models}")
        if not os.path.exists(ollama_models):
            print(f"⚠ OLLAMA_MODELS directory does not exist: {ollama_models}")
            issues_found = True
        elif not os.path.isdir(ollama_models):
            print(f"⚠ OLLAMA_MODELS is not a directory: {ollama_models}")
            issues_found = True
        elif not os.access(ollama_models, os.R_OK | os.W_OK):
            print(f"⚠ OLLAMA_MODELS has insufficient permissions: {ollama_models}")
            issues_found = True
    else:
        print("⚠ OLLAMA_MODELS is not set")
        issues_found = True
    
    # Check for models in config.json
    if os.path.exists("data/config.json"):
        try:
            with open("data/config.json", 'r') as file:
                config = json.load(file)
            
            model_path = config.get("model_path")
            if model_path:
                print(f"✓ model_path in config: {model_path}")
                
                # Check if model_path exists and has proper permissions
                if not os.path.exists(model_path):
                    print(f"⚠ model_path directory does not exist: {model_path}")
                    issues_found = True
                elif not os.path.isdir(model_path):
                    print(f"⚠ model_path is not a directory: {model_path}")
                    issues_found = True
                elif not os.access(model_path, os.R_OK | os.W_OK):
                    print(f"⚠ model_path has insufficient permissions: {model_path}")
                    issues_found = True
                    
                # Check if model_path matches OLLAMA_MODELS
                if ollama_models and ollama_models != model_path:
                    print(f"⚠ model_path ({model_path}) doesn't match OLLAMA_MODELS ({ollama_models})")
                    issues_found = True
            else:
                print("⚠ model_path not defined in config.json")
                issues_found = True
                
            # Check current model setting
            current_model = config.get("model")
            if current_model:
                print(f"✓ Current model in config: {current_model}")
                
                # Try to verify if the model exists with ollama list
                try:
                    result = subprocess.run(
                        ["ollama", "list"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        models = []
                        for line in result.stdout.strip().splitlines():
                            if line and not line.startswith("NAME"):  # Skip header
                                parts = line.split()
                                if parts:
                                    models.append(parts[0])
                        
                        if current_model in models:
                            print(f"✓ Model '{current_model}' is installed")
                        else:
                            print(f"⚠ Model '{current_model}' is not installed! This will cause model loading to fail.")
                            issues_found = True
                    else:
                        print("⚠ Couldn't verify model installation status (ollama list failed)")
                        issues_found = True
                        
                except Exception as e:
                    print(f"⚠ Error checking model installation: {e}")
                    issues_found = True
            else:
                print("⚠ No default model specified in config.json")
                issues_found = True
                
        except json.JSONDecodeError:
            print("⚠ config.json contains invalid JSON")
            issues_found = True
        except Exception as e:
            print(f"⚠ Error checking configuration: {e}")
            issues_found = True
    else:
        print("⚠ config.json file not found")
        issues_found = True
    
    # Check disk space in model directory
    try:
        model_dir = ollama_models or "data/models"
        if os.path.exists(model_dir):
            import shutil
            usage = shutil.disk_usage(model_dir)
            free_gb = round(usage.free / (1024**3), 2)
            total_gb = round(usage.total / (1024**3), 2)
            percent_free = round((usage.free / usage.total) * 100, 1)
            
            print(f"\nDisk space in model directory ({model_dir}):")
            print(f"  Total: {total_gb} GB")
            print(f"  Free: {free_gb} GB ({percent_free}%)")
            
            if free_gb < 10:
                print(f"⚠ Low disk space! Less than 10GB available. This may prevent model downloads.")
                issues_found = True
        else:
            print(f"⚠ Model directory doesn't exist: {model_dir}")
            issues_found = True
    except Exception as e:
        print(f"⚠ Error checking disk space: {e}")
        issues_found = True
    
    if not issues_found:
        print("\n✓ No model environment issues detected")
        
    return not issues_found

def check_ollama_service():
    """Check if Ollama is installed and running properly"""
    print_header("OLLAMA SERVICE CHECK")
    
    try:
        # First check if ollama executable is available
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("✗ Ollama is not installed or not in PATH")
            print("\nInstall Ollama from: https://ollama.ai/download")
            print("Make sure it's added to your system PATH")
            return False
            
        # Get version information
        version = result.stdout.strip() or "Unknown"
        print(f"✓ Ollama is installed (version: {version})")
        
        # Check if ollama service is running
        print("\nChecking if Ollama service is running...")
        
        # Try to list models as a service check
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ Ollama service is running properly")
            
            # Show available models
            models = []
            lines = result.stdout.strip().splitlines()
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    if line.strip():
                        models.append(line.split()[0])
                        
                print(f"\nFound {len(models)} installed models: {', '.join(models)}")
            else:
                print("\n⚠ No models are currently installed")
                print("Install models using: ollama pull <model_name>")
        else:
            print("✗ Ollama service is not running properly")
            print(f"Error: {result.stderr.strip()}")
            
            # Check for common error messages
            error = result.stderr.lower()
            if "connection refused" in error:
                print("\nThe Ollama service is not running. To start it:")
                print("- Windows: Start the Ollama application")
                print("- Mac: Open Ollama application")
                print("- Linux: Run 'systemctl start ollama' or 'ollama serve' in a terminal")
            elif "not found" in error:
                print("\nOllama might not be properly installed. Please reinstall.")
            
            return False
            
        return True
        
    except FileNotFoundError:
        print("✗ Ollama is not installed or not in PATH")
        print("\nInstall Ollama from: https://ollama.ai/download")
        return False
    except subprocess.TimeoutExpired:
        print("✗ Ollama command timed out - service may be hanging")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama service: {e}")
        return False

def print_header(text):
    """Print a section header"""
    print(f"\n{'=' * 80}")
    print(f" {text}")
    print(f"{'=' * 80}")

def check_ollama_installation():
    """Check if Ollama is installed and working properly"""
    print_header("OLLAMA INSTALLATION CHECK")
    
    try:
        # Check if ollama executable is available
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("✗ Ollama is not installed or not in PATH")
            print("\nInstall Ollama from: https://ollama.ai/download")
            print("Make sure it's added to your system PATH")
            return False
            
        # Get version information
        version = result.stdout.strip() or "Unknown"
        print(f"✓ Ollama is installed (version: {version})")
        return True
        
    except FileNotFoundError:
        print("✗ Ollama is not installed or not in PATH")
        print("\nInstall Ollama from: https://ollama.ai/download")
        return False
    except subprocess.TimeoutExpired:
        print("✗ Ollama command timed out - service may be hanging")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama installation: {e}")
        return False

def check_ollama_service():
    """Check if Ollama service is running properly"""
    print_header("OLLAMA SERVICE CHECK")
    
    try:
        # Try to list models as a service health check
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ Ollama service is running properly")
            
            # Show available models
            models = []
            lines = result.stdout.strip().splitlines()
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            models.append(parts[0])
                        
                print(f"\nFound {len(models)} installed models: {', '.join(models)}")
            else:
                print("\n⚠ No models are currently installed")
                print("Install models using: ollama pull <model_name>")
                
            return True
        else:
            print("✗ Ollama service is not running properly")
            print(f"Error: {result.stderr.strip()}")
            
            # Check for common error messages
            error = result.stderr.lower()
            if "connection refused" in error:
                print("\nThe Ollama service is not running. To start it:")
                print("- Windows: Start the Ollama application")
                print("- Mac: Open Ollama application")
                print("- Linux: Run 'systemctl start ollama' or 'ollama serve' in a terminal")
            elif "not found" in error:
                print("\nOllama might not be properly installed. Please reinstall.")
            
            return False
            
    except FileNotFoundError:
        print("✗ Ollama executable not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("✗ Ollama command timed out - service may be hanging")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama service: {e}")
        return False

def check_environment_variables():
    """Check environment variables related to Ollama models"""
    print_header("MODEL ENVIRONMENT VARIABLES")
    
    issues_found = False
    
    # Check environment variables
    ollama_home = os.environ.get("OLLAMA_HOME")
    ollama_models = os.environ.get("OLLAMA_MODELS")
    
    # Check OLLAMA_HOME
    if ollama_home:
        print(f"✓ OLLAMA_HOME is set to: {ollama_home}")
        if not os.path.exists(ollama_home):
            print(f"⚠ OLLAMA_HOME directory does not exist: {ollama_home}")
            issues_found = True
        elif not os.path.isdir(ollama_home):
            print(f"⚠ OLLAMA_HOME is not a directory: {ollama_home}")
            issues_found = True
        elif not os.access(ollama_home, os.R_OK | os.W_OK):
            print(f"⚠ OLLAMA_HOME has insufficient permissions: {ollama_home}")
            issues_found = True
    else:
        print("⚠ OLLAMA_HOME is not set - this may cause model location issues")
        issues_found = True
    
    # Check OLLAMA_MODELS
    if ollama_models:
        print(f"✓ OLLAMA_MODELS is set to: {ollama_models}")
        if not os.path.exists(ollama_models):
            print(f"⚠ OLLAMA_MODELS directory does not exist: {ollama_models}")
            issues_found = True
        elif not os.path.isdir(ollama_models):
            print(f"⚠ OLLAMA_MODELS is not a directory: {ollama_models}")
            issues_found = True
        elif not os.access(ollama_models, os.R_OK | os.W_OK):
            print(f"⚠ OLLAMA_MODELS has insufficient permissions: {ollama_models}")
            issues_found = True
    else:
        print("⚠ OLLAMA_MODELS is not set - this may cause model download issues")
        issues_found = True
    
    return not issues_found

def check_model_configuration():
    """Check model configuration in config.json"""
    print_header("MODEL CONFIGURATION CHECK")
    
    issues_found = False
    config_file = "data/config.json"
    
    if not os.path.exists(config_file):
        print(f"✗ Configuration file not found: {config_file}")
        return False
    
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        
        print("✓ Successfully loaded configuration file")
        
        # Check model path
        model_path = config.get("model_path")
        if model_path:
            print(f"✓ model_path in config: {model_path}")
            
            # Check if model_path exists and has proper permissions
            if not os.path.exists(model_path):
                print(f"⚠ model_path directory does not exist: {model_path}")
                print("  Creating directory...")
                try:
                    os.makedirs(model_path, exist_ok=True)
                    print(f"✓ Created directory: {model_path}")
                except Exception as e:
                    print(f"✗ Failed to create directory: {e}")
                issues_found = True
            elif not os.path.isdir(model_path):
                print(f"⚠ model_path is not a directory: {model_path}")
                issues_found = True
            elif not os.access(model_path, os.R_OK | os.W_OK):
                print(f"⚠ model_path has insufficient permissions: {model_path}")
                issues_found = True
                
            # Check if model_path matches environment variables
            ollama_models = os.environ.get("OLLAMA_MODELS")
            if ollama_models and ollama_models != model_path:
                print(f"⚠ model_path ({model_path}) doesn't match OLLAMA_MODELS ({ollama_models})")
                print("  This discrepancy can cause models to be saved in one location but searched in another")
                issues_found = True
        else:
            print("⚠ model_path not defined in config.json")
            issues_found = True
            
        # Check current model
        current_model = config.get("model")
        if current_model:
            print(f"✓ Current model in config: {current_model}")
            
            # Check if model exists
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    models = []
                    for line in result.stdout.strip().splitlines():
                        if line and not line.startswith("NAME"):  # Skip header
                            parts = line.split()
                            if parts:
                                models.append(parts[0])
                    
                    if current_model in models:
                        print(f"✓ Model '{current_model}' is installed")
                    else:
                        print(f"⚠ Model '{current_model}' is not installed! This will cause model loading to fail.")
                        issues_found = True
                        
                        # Show available models
                        if models:
                            print(f"\nAvailable models: {', '.join(models)}")
                            print("\nTo install the configured model, run:")
                            print(f"ollama pull {current_model}")
                else:
                    print("⚠ Couldn't verify model installation (ollama list command failed)")
                    issues_found = True
                    
            except Exception as e:
                print(f"⚠ Error checking model installation: {e}")
                issues_found = True
        else:
            print("⚠ No model specified in config.json")
            issues_found = True
        
        # Check other model settings
        use_8bit = config.get("use_8bit")
        if use_8bit is not None:
            print(f"✓ use_8bit is set to: {use_8bit}")
        else:
            print("ℹ use_8bit is not set (defaults to false)")
            
    except json.JSONDecodeError:
        print("✗ config.json contains invalid JSON")
        issues_found = True
    except Exception as e:
        print(f"✗ Error checking configuration: {e}")
        issues_found = True
    
    return not issues_found

def check_system_resources():
    """Check system resources for model execution"""
    print_header("SYSTEM RESOURCES CHECK")
    
    issues_found = False
    
    # Check disk space
    try:
        model_dir = os.environ.get("OLLAMA_MODELS") or "data/models"
        if os.path.exists(model_dir):
            usage = shutil.disk_usage(model_dir)
            free_gb = round(usage.free / (1024**3), 2)
            total_gb = round(usage.total / (1024**3), 2)
            percent_free = round((usage.free / usage.total) * 100, 1)
            
            print(f"Disk space in model directory ({model_dir}):")
            print(f"  Total: {total_gb} GB")
            print(f"  Free: {free_gb} GB ({percent_free}%)")
            
            if free_gb < 10:
                print(f"⚠ Low disk space! Less than 10GB available. This may prevent model downloads.")
                issues_found = True
        else:
            print(f"⚠ Model directory doesn't exist: {model_dir}")
            issues_found = True
    except Exception as e:
        print(f"⚠ Error checking disk space: {e}")
        issues_found = True
    
    # Check memory
    try:
        import psutil
        total_ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        available_ram_gb = round(psutil.virtual_memory().available / (1024**3), 2)
        
        print(f"\nSystem memory:")
        print(f"  Total RAM: {total_ram_gb} GB")
        print(f"  Available RAM: {available_ram_gb} GB")
        
        if total_ram_gb < 8:
            print("⚠ System has less than 8GB of total RAM. This may be insufficient for running larger models.")
            issues_found = True
        elif available_ram_gb < 4:
            print("⚠ Less than 4GB of RAM is currently available. Close other applications before running models.")
            issues_found = True
        else:
            print("✓ System has sufficient RAM for model execution")
    except ImportError:
        print("Could not check memory - psutil module not installed")
        print("Install with: pip install psutil")
    except Exception as e:
        print(f"Error checking system memory: {e}")
        
    return not issues_found

def test_model_initialization():
    """Test model initialization"""
    print_header("MODEL INITIALIZATION TEST")
    
    issues_found = False
    
    try:
        # Add the current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Try to import the model manager
        print("Importing ModelManager...")
        try:
            from core.model_manager import ModelManager
            print("✓ Successfully imported ModelManager")
        except ImportError as e:
            print(f"✗ Failed to import ModelManager: {e}")
            print("Check that the core directory is in your Python path")
            return False
        except Exception as e:
            print(f"✗ Error importing ModelManager: {e}")
            return False
        
        # Create a test logger
        test_logs = []
        def test_logger(message):
            test_logs.append(message)
            print(f"[LOG] {message}")
        
        # Get model path
        model_path = "data/models"
        config_file = "data/config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as file:
                    config = json.load(file)
                model_path = config.get("model_path", model_path)
            except:
                pass
        
        if not os.path.exists(model_path):
            try:
                print(f"Creating model directory: {model_path}")
                os.makedirs(model_path, exist_ok=True)
            except Exception as e:
                print(f"✗ Failed to create model directory: {e}")
                issues_found = True
        
        # Initialize model manager
        print(f"\nInitializing ModelManager with path: {model_path}")
        try:
            model_manager = ModelManager(
                model_path=model_path,
                logger=test_logger
            )
            print("✓ Successfully initialized ModelManager")
            
            # Check environment variables were set properly
            print("\nChecking environment variables set by ModelManager:")
            if "OLLAMA_HOME" in os.environ:
                print(f"✓ OLLAMA_HOME set to: {os.environ['OLLAMA_HOME']}")
            else:
                print("✗ OLLAMA_HOME was not set by ModelManager")
                issues_found = True
                
            if "OLLAMA_MODELS" in os.environ:
                print(f"✓ OLLAMA_MODELS set to: {os.environ['OLLAMA_MODELS']}")
            else:
                print("✗ OLLAMA_MODELS was not set by ModelManager")
                issues_found = True
            
            # Test model detection
            print("\nTesting model detection...")
            try:
                available_models = model_manager.detect_models()
                if available_models:
                    print(f"✓ Found {len(available_models)} installed models: {', '.join(available_models)}")
                else:
                    print("⚠ No models detected")
                    print("  This could be normal if no models have been installed yet.")
            except Exception as e:
                print(f"✗ Error detecting models: {e}")
                traceback.print_exc()
                issues_found = True
                
            # Check for model statuses
            print("\nChecking model statuses:")
            try:
                if hasattr(model_manager, 'model_statuses') and model_manager.model_statuses:
                    print("✓ Model statuses initialized")
                    for model_name, status in model_manager.model_statuses.items():
                        print(f"  - {model_name}: {status}")
                else:
                    print("⚠ No model statuses available")
            except Exception as e:
                print(f"✗ Error checking model statuses: {e}")
                issues_found = True
                
            # Check for current model
            print("\nChecking current model:")
            try:
                current_model = model_manager.current_model
                if current_model:
                    print(f"✓ Current model is set to: {current_model}")
                else:
                    print("⚠ No current model is set")
            except Exception as e:
                print(f"✗ Error checking current model: {e}")
                issues_found = True
                
        except Exception as e:
            print(f"✗ Failed to initialize ModelManager: {e}")
            traceback.print_exc()
            issues_found = True
            
        # Check for any errors in the test logs
        errors = [log for log in test_logs if "[Error]" in log or "failed" in log.lower()]
        if errors:
            print("\n⚠ Errors detected during model initialization:")
            for error in errors:
                print(f"  {error}")
            issues_found = True
            
    except Exception as e:
        print(f"✗ Error in model initialization test: {e}")
        traceback.print_exc()
        issues_found = True
        
    return not issues_found

def check_model_panel():
    """Check model panel UI integration"""
    print_header("MODEL PANEL UI CHECK")
    
    issues_found = False
    
    try:
        # Add the current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Try to import the model panel
        print("Importing ModelPanel...")
        try:
            from ui.panels.model_panel import ModelPanel
            print("✓ Successfully imported ModelPanel")
        except ImportError as e:
            print(f"✗ Failed to import ModelPanel: {e}")
            print("Check that the ui directory is in your Python path")
            return False
        except Exception as e:
            print(f"✗ Error importing ModelPanel: {e}")
            return False
        
        # Check ModelPanel implementation
        print("\nChecking ModelPanel implementation...")
        
        # Read the model_panel.py file
        model_panel_path = "ui/model_panel.py"
        if os.path.exists(model_panel_path):
            try:
                with open(model_panel_path, 'r') as file:
                    content = file.read()
                
                # Check for key methods
                key_methods = [
                    "refresh_model_list", 
                    "install_selected_model",
                    "start_selected_model", 
                    "stop_running_model",
                    "_update_model_status",
                ]
                
                missing_methods = []
                for method in key_methods:
                    if f"def {method}" not in content:
                        missing_methods.append(method)
                
                if missing_methods:
                    print(f"⚠ ModelPanel is missing key methods: {', '.join(missing_methods)}")
                    issues_found = True
                else:
                    print("✓ ModelPanel has all key methods implemented")
                    
                # Check model initialization
                if "self.model_manager = model_manager" in content:
                    print("✓ ModelPanel correctly stores the model_manager reference")
                else:
                    print("⚠ ModelPanel might not correctly store the model_manager reference")
                    issues_found = True
                    
            except Exception as e:
                print(f"✗ Error analyzing ModelPanel code: {e}")
                issues_found = True
        else:
            print(f"✗ ModelPanel file not found: {model_panel_path}")
            issues_found = True
            
    except Exception as e:
        print(f"✗ Error checking model panel: {e}")
        issues_found = True
        
    return not issues_found

def check_model_logs():
    """Analyze logs for model-related issues"""
    print_header("MODEL LOG ANALYSIS")
    
    issues_found = False
    log_file = "irintai_debug.log"
    log_dir = "data/logs"
    
    # Find the most recent log file
    if not os.path.exists(log_file):
        if os.path.exists(log_dir):
            log_files = sorted([f for f in os.listdir(log_dir) if f.startswith("irintai_debug_")], reverse=True)
            if log_files:
                log_file = os.path.join(log_dir, log_files[0])
                print(f"Using most recent log: {log_file}")
            else:
                print("⚠ No log files found!")
                return False
        else:
            print("⚠ Log directory not found!")
            return False
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='replace') as file:
            log_content = file.read()
            
        # Split into lines for analysis
        log_lines = log_content.split('\n')
        
        # Look for model-related errors
        model_errors = []
        for line in log_lines:
            if "[Error]" in line and any(term in line for term in ["model", "Model", "ollama", "Ollama"]):
                model_errors.append(line)
                
        if model_errors:
            print(f"⚠ Found {len(model_errors)} model-related errors in logs:")
            for error in model_errors[:5]:  # Show at most 5 errors
                print(f"  {error}")
            if len(model_errors) > 5:
                print(f"  ... and {len(model_errors) - 5} more")
            issues_found = True
            
        # Look for specific error patterns
        error_patterns = {
            "no_ollama": ["command not found", "ollama", "executable"],
            "connection_refused": ["connection refused", "could not connect"],
            "model_not_found": ["model not found", "no such model"],
            "model_download_failed": ["download failed", "failed to pull"],
            "model_run_failed": ["failed to start model", "error running model"],
            "model_stop_failed": ["failed to stop model", "error stopping model"],
            "attribute_error": ["AttributeError", "has no attribute"]
        }
        
        pattern_matches = {pattern: [] for pattern in error_patterns}
        
        for line in log_lines:
            if "[Error]" in line or "[WARNING]" in line:
                for pattern, keywords in error_patterns.items():
                    if all(keyword.lower() in line.lower() for keyword in keywords):
                        pattern_matches[pattern].append(line)
        
        # Report on patterns found
        found_patterns = False
        for pattern, matches in pattern_matches.items():
            if matches:
                if not found_patterns:
                    print("\nDetected error patterns:")
                    found_patterns = True
                    
                print(f"  - {pattern}: {len(matches)} occurrences")
                # Show an example
                if matches:
                    print(f"    Example: {matches[0]}")
                issues_found = True
                
                # Provide specific advice based on the pattern
                if pattern == "no_ollama":
                    print("    Fix: Install Ollama from https://ollama.ai/download")
                elif pattern == "connection_refused":
                    print("    Fix: Start the Ollama service before running IrintAI")
                elif pattern == "model_not_found":
                    print("    Fix: Install the model with 'ollama pull <model_name>'")
                elif pattern == "model_download_failed":
                    print("    Fix: Check your internet connection and disk space")
                elif pattern == "attribute_error":
                    print("    Fix: Update your code to use the correct attribute names or implement missing methods")
        
        if not model_errors and not found_patterns:
            print("✓ No model-related errors found in logs")
            
    except Exception as e:
        print(f"✗ Error analyzing logs: {e}")
        issues_found = True
        
    return not issues_found

def run_full_model_diagnostics():
    """Run all model diagnostic checks"""
    print_header("FULL MODEL DIAGNOSTICS")
    results = {}
    
    # Define all the diagnostic checks
    checks = [
        ("Ollama Installation", check_ollama_installation),
        ("Ollama Service", check_ollama_service),
        ("Environment Variables", check_environment_variables),
        ("Model Configuration", check_model_configuration),
        ("System Resources", check_system_resources),
        ("Model Initialization", test_model_initialization),
        ("Model Panel UI", check_model_panel),
        ("Model Logs", check_model_logs)
    ]
    
    # Run all checks
    all_passed = True
    for name, check_func in checks:
        print(f"\nRunning {name} check...")
        
        try:
            result = check_func()
            results[name] = "✓ PASS" if result else "✗ FAIL"
            if not result:
                all_passed = False
        except Exception as e:
            print(f"\n✗ Error during {name} check: {e}")
            traceback.print_exc()
            results[name] = "✗ ERROR"
            all_passed = False
            
        # Add some visual separation between checks
        print("\n" + "-" * 80)
    
    # Print summary
    print_header("MODEL DIAGNOSTIC SUMMARY")
    
    for name, result in results.items():
        print(f"{name.ljust(25)}: {result}")
    
    if all_passed:
        print("\n✓ All model diagnostic checks passed!")
    else:
        print("\n⚠ Some model diagnostic checks failed. See details above.")
        
        # Provide recommendations based on failures
        print("\nRECOMMENDED ACTIONS:")
        
        if results.get("Ollama Installation") == "✗ FAIL":
            print("  1. Install Ollama from https://ollama.ai/download")
            
        if results.get("Ollama Service") == "✗ FAIL":
            print("  2. Start the Ollama service")
            print("     - Windows: Run Ollama application")
            print("     - Mac: Open Ollama application")
            print("     - Linux: Run 'systemctl start ollama' or 'ollama serve'")
            
        if results.get("Environment Variables") == "✗ FAIL" or results.get("Model Configuration") == "✗ FAIL":
            print("  3. Update your config.json with the correct model_path")
            print("     - Ensure it matches the OLLAMA_MODELS environment variable")
            
        if results.get("Model Initialization") == "✗ FAIL":
            print("  4. Check ModelManager implementation")
            print("     - Ensure all required methods are properly implemented")
            print("     - Fix any AttributeErrors in the code")
            
        if results.get("Model Panel UI") == "✗ FAIL":
            print("  5. Fix ModelPanel UI implementation")
            print("     - Ensure model_manager reference is correctly stored")
            print("     - Implement all required UI update methods")
    
    # Save report to file
    try:
        with open("model_diagnostic_report.txt", "w") as f:
            f.write("IRINTAI MODEL DIAGNOSTIC REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("SUMMARY:\n")
            for name, result in results.items():
                ascii_result = result.replace("✓", "PASS").replace("✗", "FAIL")
                f.write(f"{name.ljust(25)}: {ascii_result}\n")
        
        print(f"\nFull report saved to: model_diagnostic_report.txt")
        
    except Exception as e:
        print(f"Error saving report: {e}")
    
    return all_passed

if __name__ == "__main__":
    try:
        print("\nIrintAI Assistant - Model Diagnostics Tool")
        print("This tool will diagnose issues with model functionality\n")
        
        run_full_model_diagnostics()
        
    except Exception as e:
        print(f"Unhandled error during diagnostics: {e}")
        traceback.print_exc()

def run_diagnostics():
    """Run all diagnostic checks"""
    success = True
    
    print("\n" + "=" * 80)
    print(" IRINTAI ASSISTANT ENHANCED DIAGNOSTIC TOOL ")
    print("=" * 80)
    
    print("\nRunning comprehensive system diagnostics...")
    
    checks = [
        ("Environment", check_environment),
        ("File Structure", check_file_structure),
        ("Dependencies", check_dependencies),
        ("Configuration", check_config),
        ("Plugin Manager", check_plugin_manager),
        ("Interface Consistency", check_interface_consistency),
        ("Runtime Patching", check_runtime_patching),
        ("Ollama Service", check_ollama_service),
        ("Log Analysis", check_logs),
        ("Model Environment", check_model_environment)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            result = check_func()
            results[name] = "✓ PASS" if result else "✗ FAIL"
            if not result:
                success = False
        except Exception as e:
            logger.error(f"Error in {name} check: {e}")
            results[name] = "✗ ERROR"
            success = False
    
    # Print summary
    print("\n" + "=" * 80)
    print(" DIAGNOSTIC SUMMARY ")
    print("=" * 80)
    
    for name, result in results.items():
        print(f"{name.ljust(20)}: {result}")
    
    if success:
        print("\n✅ All diagnostic checks passed!")
    else:
        print("\n⚠ Some diagnostic checks failed. See details above.")
        
        # Suggest specific fixes based on results
        print("\nRecommended actions:")
        
        if results.get("Plugin Manager") == "✗ FAIL":
            print("  1. Fix plugin manager by adding missing methods (especially set_error_handler)")
            print("     - Use fix_plugin_manager.py or manually add required methods")
            
        if results.get("Interface Consistency") == "✗ FAIL":
            print("  2. Fix interface inconsistencies between components")
            print("     - Implement missing methods or use runtime_patching.py to add them dynamically")
            
        if results.get("Runtime Patching") == "✗ FAIL":
            print("  3. Implement the runtime_patching utility to prevent attribute errors")
            print("     - See utils/runtime_patching.py and integrate it into irintai.py")
    
    # Save summary to file - using UTF-8 encoding to handle special characters
    with open("irintai_diagnostic_report.txt", "w", encoding="utf-8") as f:
        f.write("IRINTAI ASSISTANT ENHANCED DIAGNOSTIC REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("SUMMARY:\n")
        # Convert special characters to ASCII for better compatibility
        for name, result in results.items():
            ascii_result = result.replace("✓", "PASS").replace("✗", "FAIL")
            f.write(f"{name.ljust(20)}: {ascii_result}\n")
            
        if not success:
            f.write("\nRECOMMENDED ACTIONS:\n")
            if results.get("Plugin Manager") == "✗ FAIL":
                f.write("  1. Fix plugin manager by adding missing methods\n")
            if results.get("Interface Consistency") == "✗ FAIL":
                f.write("  2. Fix interface inconsistencies between components\n")
            if results.get("Runtime Patching") == "✗ FAIL":
                f.write("  3. Implement runtime patching utilities\n")
    
    print(f"\nFull report saved to: irintai_diagnostic_report.txt")
    print(f"Detailed log saved to: irintai_diagnostic.log")
    
    return success

if __name__ == "__main__":
    try:
        run_diagnostics()
    except Exception as e:
        logger.error(f"Unhandled exception in diagnostics: {e}")
        traceback.print_exc()
        print("\n⚠ An error occurred while running diagnostics.")
        sys.exit(1)
