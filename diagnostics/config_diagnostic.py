"""
Configuration Diagnostic Module for IrintAI Assistant

This module provides diagnostics for configuration files including:
- Config file existence and validity
- Required settings presence
- Configuration permissions
- Path validation for referenced directories and files
"""
import os
import json
import sys
from typing import Dict, Any, List
import time

# Add project root to sys.path to allow importing core modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.config_manager import ConfigManager
except ImportError as e:
    print(f"Error importing ConfigManager: {e}")
    sys.exit(1)

class ConfigDiagnostic:
    """Diagnostic tool for configuration checks"""
    
    def __init__(self, config_path='data/config.json'):
        """Initialize the configuration diagnostic module"""
        self.config_path = config_path
        self.results = {}
        
        # Define required configuration settings
        self.required_settings = {
            'main': ['ollama_url', 'default_model'],
            'ui': ['theme', 'window_size', 'font_size'],
            'plugins': ['enabled_plugins', 'plugin_directory'],
            'logging': ['log_level', 'log_directory']
        }
        
        # Initialize config manager if possible
        try:
            self.config_manager = ConfigManager(config_path)
            self.config_loaded = True
        except Exception:
            self.config_loaded = False
            self.config_manager = None
        
    def log(self, message):
        """Simple print-based logging for diagnostics"""
        print(f"[CONFIG DIAG] {message}")
    
    def check_config_existence(self):
        """Check if the configuration file exists"""
        self.log(f"Checking configuration file existence: {self.config_path}")
        
        # Get absolute path
        if not os.path.isabs(self.config_path):
            abs_path = os.path.join(project_root, self.config_path)
        else:
            abs_path = self.config_path
            
        if os.path.exists(abs_path):
            self.results['config_existence'] = {
                'status': 'Success',
                'message': f"Configuration file exists: {abs_path}"
            }
            self.log("Configuration file exists")
            return True
        else:
            self.results['config_existence'] = {
                'status': 'Failure',
                'message': f"Configuration file does not exist: {abs_path}"
            }
            self.log("Configuration file does not exist")
            return False
    
    def check_config_validity(self):
        """Check if the configuration file contains valid JSON"""
        if not self.check_config_existence():
            self.results['config_validity'] = {
                'status': 'Skipped',
                'message': 'Configuration file does not exist'
            }
            self.log("Skipping validity check - file does not exist")
            return False
            
        self.log("Checking configuration file validity")
        
        # Get absolute path
        if not os.path.isabs(self.config_path):
            abs_path = os.path.join(project_root, self.config_path)
        else:
            abs_path = self.config_path
            
        try:
            with open(abs_path, 'r') as f:
                json.load(f)
            
            self.results['config_validity'] = {
                'status': 'Success',
                'message': 'Configuration file contains valid JSON'
            }
            self.log("Configuration file is valid JSON")
            return True
        except json.JSONDecodeError as e:
            self.results['config_validity'] = {
                'status': 'Failure',
                'message': f"Configuration file contains invalid JSON: {e}"
            }
            self.log(f"Configuration file contains invalid JSON: {e}")
            return False
        except Exception as e:
            self.results['config_validity'] = {
                'status': 'Failure',
                'message': f"Error reading configuration file: {e}"
            }
            self.log(f"Error reading configuration file: {e}")
            return False
    
    def check_required_settings(self):
        """Check if all required configuration settings are present"""
        if not self.config_loaded:
            self.results['required_settings'] = {
                'status': 'Skipped',
                'message': 'Configuration file not loaded'
            }
            self.log("Skipping required settings check - config not loaded")
            return False
            
        self.log("Checking required configuration settings")
        
        # Get configuration
        config = self.config_manager.config
        
        # Check each required setting
        missing_settings = {}
        for category, settings in self.required_settings.items():
            missing_in_category = []
            for setting in settings:
                # For top-level settings
                if category == 'main':
                    if setting not in config:
                        missing_in_category.append(setting)
                # For nested settings
                elif category in config:
                    if setting not in config[category]:
                        missing_in_category.append(setting)
                else:
                    missing_in_category.append(setting)
            
            if missing_in_category:
                missing_settings[category] = missing_in_category
        
        # Determine status based on missing settings
        if not missing_settings:
            self.results['required_settings'] = {
                'status': 'Success',
                'message': 'All required configuration settings are present'
            }
            self.log("All required settings are present")
            return True
        else:
            # Create message with missing settings
            message_parts = ["Missing required settings:"]
            for category, settings in missing_settings.items():
                message_parts.append(f"- {category}: {', '.join(settings)}")
                
            self.results['required_settings'] = {
                'status': 'Failure',
                'message': '\n'.join(message_parts),
                'missing': missing_settings
            }
            self.log(f"Missing {sum(len(s) for s in missing_settings.values())} required settings")
            return False
    
    def check_config_permissions(self):
        """Check if the configuration file has correct permissions"""
        if not self.check_config_existence():
            self.results['config_permissions'] = {
                'status': 'Skipped',
                'message': 'Configuration file does not exist'
            }
            self.log("Skipping permissions check - file does not exist")
            return False
            
        self.log("Checking configuration file permissions")
        
        # Get absolute path
        if not os.path.isabs(self.config_path):
            abs_path = os.path.join(project_root, self.config_path)
        else:
            abs_path = self.config_path
        
        try:
            # Check if file is readable
            is_readable = os.access(abs_path, os.R_OK)
            # Check if file is writable
            is_writable = os.access(abs_path, os.W_OK)
            
            if is_readable and is_writable:
                self.results['config_permissions'] = {
                    'status': 'Success',
                    'message': 'Configuration file has correct read/write permissions'
                }
                self.log("Configuration file has correct permissions")
                return True
            else:
                issues = []
                if not is_readable:
                    issues.append("not readable")
                if not is_writable:
                    issues.append("not writable")
                    
                self.results['config_permissions'] = {
                    'status': 'Failure',
                    'message': f"Configuration file is {' and '.join(issues)}"
                }
                self.log(f"Configuration file has permission issues: {' and '.join(issues)}")
                return False
        except Exception as e:
            self.results['config_permissions'] = {
                'status': 'Failure',
                'message': f"Error checking configuration file permissions: {e}"
            }
            self.log(f"Error checking permissions: {e}")
            return False
    
    def check_path_validations(self):
        """Check if paths referenced in configuration exist"""
        if not self.config_loaded:
            self.results['path_validations'] = {
                'status': 'Skipped',
                'message': 'Configuration file not loaded'
            }
            self.log("Skipping path validations - config not loaded")
            return False
            
        self.log("Checking path validations in configuration")
        
        # Define paths to validate (key is config path, value is whether it's required)
        paths_to_validate = {
            'plugins.plugin_directory': True,
            'logging.log_directory': True,
            'data_directory': False,
            'models.models_directory': False
        }
        
        # Get configuration
        config = self.config_manager.config
        
        # Check each path
        invalid_paths = {}
        for path_key, is_required in paths_to_validate.items():
            # Parse path from config using dot notation
            config_value = config
            path_parts = path_key.split('.')
            
            try:
                for part in path_parts:
                    config_value = config_value[part]
                    
                # Skip if path is not set and not required
                if not config_value and not is_required:
                    continue
                    
                # Convert to absolute path if relative
                if not os.path.isabs(config_value):
                    abs_path = os.path.join(project_root, config_value)
                else:
                    abs_path = config_value
                
                if not os.path.exists(abs_path):
                    invalid_paths[path_key] = {
                        'path': config_value,
                        'absolute_path': abs_path,
                        'reason': 'Path does not exist'
                    }
                elif not os.path.isdir(abs_path):
                    invalid_paths[path_key] = {
                        'path': config_value,
                        'absolute_path': abs_path,
                        'reason': 'Path is not a directory'
                    }
            except (KeyError, TypeError):
                if is_required:
                    invalid_paths[path_key] = {
                        'path': None,
                        'reason': 'Path not found in configuration'
                    }
        
        # Determine status based on invalid paths
        if not invalid_paths:
            self.results['path_validations'] = {
                'status': 'Success',
                'message': 'All configured paths exist and are valid'
            }
            self.log("All configured paths are valid")
            return True
        else:
            # Create message with invalid paths
            message_parts = ["Invalid configured paths:"]
            for path_key, details in invalid_paths.items():
                reason = details['reason']
                path = details.get('path', 'Not set')
                message_parts.append(f"- {path_key}: {path} ({reason})")
                
            self.results['path_validations'] = {
                'status': 'Failure' if any(paths_to_validate[k] for k in invalid_paths if k in paths_to_validate) else 'Warning',
                'message': '\n'.join(message_parts),
                'invalid_paths': invalid_paths
            }
            self.log(f"Found {len(invalid_paths)} invalid configured paths")
            return False
    
    def check_ollama_url_setting(self):
        """Specific check for the Ollama URL setting"""
        if not self.config_loaded:
            self.results['ollama_url'] = {
                'status': 'Skipped',
                'message': 'Configuration file not loaded'
            }
            self.log("Skipping Ollama URL check - config not loaded")
            return False
            
        self.log("Checking Ollama URL configuration")
        
        # Get Ollama URL from config
        ollama_url = self.config_manager.get('ollama_url', None)
        
        if not ollama_url:
            self.results['ollama_url'] = {
                'status': 'Failure',
                'message': 'Ollama URL is not set in configuration'
            }
            self.log("Ollama URL is not configured")
            return False
        
        # Validate URL format (basic check)
        if not ollama_url.startswith(('http://', 'https://')):
            self.results['ollama_url'] = {
                'status': 'Warning',
                'message': f"Ollama URL '{ollama_url}' does not start with http:// or https://"
            }
            self.log(f"Ollama URL has invalid format: {ollama_url}")
            return False
            
        # If URL is valid format, consider it a success
        self.results['ollama_url'] = {
            'status': 'Success',
            'message': f"Ollama URL is configured: {ollama_url}"
        }
        self.log(f"Ollama URL is properly configured: {ollama_url}")
        return True
    
    def check_models_configuration(self):
        """Check models configuration settings"""
        if not self.config_loaded:
            self.results['models_configuration'] = {
                'status': 'Skipped',
                'message': 'Configuration file not loaded'
            }
            self.log("Skipping models configuration check - config not loaded")
            return False
            
        self.log("Checking models configuration")
        
        # Get model-related settings
        default_model = self.config_manager.get('default_model', None)
        models_config = self.config_manager.get('models', {})
        
        issues = []
        
        # Check default model
        if not default_model:
            issues.append("Default model is not configured")
        
        # Check models configuration
        if not models_config:
            issues.append("Models section is missing from configuration")
        else:
            # Check for available models list
            available_models = models_config.get('available_models', [])
            if not available_models:
                issues.append("No available models are configured")
            
            # Check if default model is in available models
            elif default_model and default_model not in available_models:
                issues.append(f"Default model '{default_model}' is not in the list of available models")
        
        # Determine status based on issues
        if not issues:
            self.results['models_configuration'] = {
                'status': 'Success',
                'message': 'Models configuration is valid'
            }
            self.log("Models configuration is valid")
            return True
        else:
            self.results['models_configuration'] = {
                'status': 'Warning',
                'message': f"Models configuration has issues: {', '.join(issues)}"
            }
            self.log(f"Models configuration has issues: {', '.join(issues)}")
            return False
    
    def run_all_checks(self):
        """Run all configuration diagnostic checks"""
        self.log("Starting configuration diagnostics...")
        start_time = time.time()
        
        # Run checks
        self.check_config_existence()
        self.check_config_validity()
        self.check_config_permissions()
        self.check_required_settings()
        self.check_path_validations()
        self.check_ollama_url_setting()
        self.check_models_configuration()
        
        elapsed_time = time.time() - start_time
        self.log(f"Configuration diagnostics completed in {elapsed_time:.2f} seconds")
        return self.results
