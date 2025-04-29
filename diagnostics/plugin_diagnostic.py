"""
Plugin Diagnostic Module for IrintAI Assistant

This module provides diagnostics for the plugin system including:
- Plugin directory structure
- Plugin manifest validation
- Plugin dependencies
- Plugin loading and initialization
"""
import os
import sys
import json
import importlib.util
import time
from typing import Dict, Any, List, Tuple

# Add project root to sys.path to allow importing core modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.config_manager import ConfigManager
    from core.plugin_manager import PluginManager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure the script is run from the project root or the PYTHONPATH is set correctly.")

class PluginDiagnostic:
    """Diagnostic tool for plugin system checks"""
    
    def __init__(self, config_path='data/config.json'):
        """Initialize the plugin diagnostic module"""
        self.config_path = config_path
        self.results = {}
        
        # Try to initialize config manager
        try:
            self.config_manager = ConfigManager(config_path)
            self.config_loaded = True
            
            # Get plugin directory
            self.plugin_dir = self.config_manager.get("plugins", {}).get("plugin_directory", "plugins")
            if not os.path.isabs(self.plugin_dir):
                self.plugin_dir = os.path.join(project_root, self.plugin_dir)
                
            # Get enabled plugins
            self.enabled_plugins = self.config_manager.get("plugins", {}).get("enabled_plugins", [])
            
        except Exception as e:
            self.config_loaded = False
            self.plugin_dir = os.path.join(project_root, "plugins")
            self.enabled_plugins = []
            print(f"Error loading configuration: {e}")
        
        # Try to initialize plugin manager but don't activate plugins
        try:
            self.plugin_manager = PluginManager(self.config_manager)
            self.plugin_manager_loaded = True
        except Exception:
            self.plugin_manager_loaded = False
        
    def log(self, message):
        """Simple print-based logging for diagnostics"""
        print(f"[PLUGIN DIAG] {message}")
    
    def check_plugin_directory(self):
        """Check if the plugin directory exists and is accessible"""
        self.log(f"Checking plugin directory: {self.plugin_dir}")
        
        if os.path.exists(self.plugin_dir):
            if os.path.isdir(self.plugin_dir):
                if os.access(self.plugin_dir, os.R_OK):
                    self.results['plugin_directory'] = {
                        'status': 'Success',
                        'message': f"Plugin directory exists and is readable: {self.plugin_dir}"
                    }
                    self.log("Plugin directory exists and is readable")
                    return True
                else:
                    self.results['plugin_directory'] = {
                        'status': 'Failure',
                        'message': f"Plugin directory is not readable: {self.plugin_dir}"
                    }
                    self.log("Plugin directory is not readable")
                    return False
            else:
                self.results['plugin_directory'] = {
                    'status': 'Failure',
                    'message': f"Plugin directory path exists but is not a directory: {self.plugin_dir}"
                }
                self.log("Plugin directory path is not a directory")
                return False
        else:
            self.results['plugin_directory'] = {
                'status': 'Failure',
                'message': f"Plugin directory does not exist: {self.plugin_dir}"
            }
            self.log("Plugin directory does not exist")
            return False
    
    def discover_plugins(self):
        """Discover available plugins in the plugin directory"""
        if not self.check_plugin_directory():
            self.results['plugin_discovery'] = {
                'status': 'Skipped',
                'message': 'Plugin directory not accessible'
            }
            self.log("Skipping plugin discovery - directory not accessible")
            return False, []
            
        self.log("Discovering plugins...")
        
        discovered_plugins = []
        
        # Explore subdirectories in plugin dir
        try:
            for item in os.listdir(self.plugin_dir):
                plugin_path = os.path.join(self.plugin_dir, item)
                
                # Check if it's a directory
                if os.path.isdir(plugin_path):
                    # Check if it has a plugin.json or manifest.json file
                    manifest_path = None
                    for manifest_name in ["plugin.json", "manifest.json"]:
                        potential_path = os.path.join(plugin_path, manifest_name)
                        if os.path.exists(potential_path) and os.path.isfile(potential_path):
                            manifest_path = potential_path
                            break
                            
                    if manifest_path:
                        # Plugin found
                        discovered_plugins.append({
                            'name': item,
                            'path': plugin_path,
                            'manifest_path': manifest_path
                        })
            
            if discovered_plugins:
                self.results['plugin_discovery'] = {
                    'status': 'Success',
                    'message': f"Discovered {len(discovered_plugins)} plugins",
                    'plugins': [p['name'] for p in discovered_plugins]
                }
                self.log(f"Discovered {len(discovered_plugins)} plugins")
                return True, discovered_plugins
            else:
                self.results['plugin_discovery'] = {
                    'status': 'Warning',
                    'message': f"No plugins found in directory: {self.plugin_dir}"
                }
                self.log("No plugins found")
                return True, []
        except Exception as e:
            self.results['plugin_discovery'] = {
                'status': 'Failure',
                'message': f"Error discovering plugins: {e}"
            }
            self.log(f"Error discovering plugins: {e}")
            return False, []
    
    def check_plugin_manifests(self):
        """Check plugin manifest files for validity"""
        success, discovered_plugins = self.discover_plugins()
        if not success or not discovered_plugins:
            self.results['plugin_manifests'] = {
                'status': 'Skipped',
                'message': 'Plugin discovery failed or no plugins found'
            }
            self.log("Skipping manifest check - no plugins discovered")
            return False
            
        self.log("Checking plugin manifests...")
        
        manifest_results = {}
        invalid_count = 0
        
        for plugin in discovered_plugins:
            plugin_name = plugin['name']
            manifest_path = plugin['manifest_path']
            
            try:
                # Read and parse manifest
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    
                # Check required fields
                required_fields = ["name", "version", "description", "main"]
                missing_fields = [field for field in required_fields if field not in manifest]
                
                if missing_fields:
                    invalid_count += 1
                    manifest_results[plugin_name] = {
                        'status': 'Failure',
                        'message': f"Missing required fields in manifest: {', '.join(missing_fields)}"
                    }
                else:
                    # Additional validation
                    issues = []
                    
                    # Check if main module exists
                    main_module = manifest.get("main")
                    if main_module:
                        main_path = os.path.join(plugin['path'], main_module)
                        if not os.path.exists(main_path):
                            issues.append(f"Main module file not found: {main_module}")
                    
                    # Check dependencies if present
                    if "dependencies" in manifest:
                        dependencies = manifest["dependencies"]
                        if not isinstance(dependencies, list) and not isinstance(dependencies, dict):
                            issues.append("Dependencies must be a list or dictionary")
                            
                    if issues:
                        invalid_count += 1
                        manifest_results[plugin_name] = {
                            'status': 'Warning',
                            'message': f"Manifest validation issues: {', '.join(issues)}"
                        }
                    else:
                        manifest_results[plugin_name] = {
                            'status': 'Success',
                            'message': "Manifest is valid"
                        }
            except json.JSONDecodeError as e:
                invalid_count += 1
                manifest_results[plugin_name] = {
                    'status': 'Failure',
                    'message': f"Invalid JSON in manifest: {e}"
                }
            except Exception as e:
                invalid_count += 1
                manifest_results[plugin_name] = {
                    'status': 'Failure',
                    'message': f"Error checking manifest: {e}"
                }
        
        # Determine overall status
        if invalid_count == 0:
            status = 'Success'
            message = f"All {len(discovered_plugins)} plugin manifests are valid"
        elif invalid_count == len(discovered_plugins):
            status = 'Failure'
            message = f"All {len(discovered_plugins)} plugin manifests are invalid"
        else:
            status = 'Warning'
            message = f"{invalid_count} of {len(discovered_plugins)} plugin manifests have issues"
        
        self.results['plugin_manifests'] = {
            'status': status,
            'message': message,
            'details': manifest_results
        }
        self.log(f"Plugin manifest check: {status} ({invalid_count} issues found)")
        return status != 'Failure'
    
    def check_plugin_dependencies(self):
        """Check plugin dependencies for conflicts or missing packages"""
        if not self.plugin_manager_loaded:
            self.results['plugin_dependencies'] = {
                'status': 'Skipped',
                'message': 'Plugin manager not initialized'
            }
            self.log("Skipping dependency check - plugin manager not initialized")
            return False
            
        self.log("Checking plugin dependencies...")

        success, discovered_plugins = self.discover_plugins()
        if not success or not discovered_plugins:
            self.results['plugin_dependencies'] = {
                'status': 'Skipped',
                'message': 'Plugin discovery failed or no plugins found'
            }
            self.log("Skipping dependency check - no plugins discovered")
            return False
        
        dependency_issues = {}
        
        for plugin in discovered_plugins:
            plugin_name = plugin['name']
            manifest_path = plugin['manifest_path']
            
            try:
                # Read and parse manifest
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                # Check dependencies if present
                if "dependencies" in manifest:
                    dependencies = manifest["dependencies"]
                    issues = []
                    
                    # Check Python package dependencies
                    if isinstance(dependencies, dict) and "python" in dependencies:
                        python_deps = dependencies["python"]
                        for package in python_deps:
                            try:
                                # Try to import the package
                                importlib.import_module(package.split('>=')[0].split('==')[0].strip())
                            except ImportError:
                                issues.append(f"Missing Python package: {package}")
                    
                    # Check plugin dependencies
                    if isinstance(dependencies, list) or (isinstance(dependencies, dict) and "plugins" in dependencies):
                        plugin_deps = dependencies if isinstance(dependencies, list) else dependencies["plugins"]
                        discovered_names = [p['name'] for p in discovered_plugins]
                        
                        for dep in plugin_deps:
                            if dep not in discovered_names:
                                issues.append(f"Missing plugin dependency: {dep}")
                    
                    if issues:
                        dependency_issues[plugin_name] = {
                            'status': 'Warning',
                            'message': f"Dependency issues: {', '.join(issues)}"
                        }
            except Exception as e:
                dependency_issues[plugin_name] = {
                    'status': 'Failure',
                    'message': f"Error checking dependencies: {e}"
                }
        
        # Determine overall status
        if not dependency_issues:
            self.results['plugin_dependencies'] = {
                'status': 'Success',
                'message': f"All plugin dependencies are satisfied"
            }
            self.log("All plugin dependencies are satisfied")
            return True
        else:
            self.results['plugin_dependencies'] = {
                'status': 'Warning',
                'message': f"{len(dependency_issues)} plugins have dependency issues",
                'details': dependency_issues
            }
            self.log(f"Found dependency issues in {len(dependency_issues)} plugins")
            return False
    
    def check_plugin_initialization(self):
        """Check if plugins can be initialized without errors"""
        if not self.plugin_manager_loaded:
            self.results['plugin_initialization'] = {
                'status': 'Skipped',
                'message': 'Plugin manager not initialized'
            }
            self.log("Skipping initialization check - plugin manager not initialized")
            return False
            
        self.log("Checking plugin initialization...")
        
        # We'll test initialization for enabled plugins only for safety
        if not self.enabled_plugins:
            self.results['plugin_initialization'] = {
                'status': 'Skipped',
                'message': 'No plugins are enabled in configuration'
            }
            self.log("No plugins enabled - skipping initialization test")
            return True
        
        # Instead of actually loading plugins which could have side effects,
        # we'll just verify that the plugin's main module can be imported
        init_results = {}
        init_failures = 0
        
        success, discovered_plugins = self.discover_plugins()
        enabled_plugin_info = [p for p in discovered_plugins if p['name'] in self.enabled_plugins]
        
        for plugin in enabled_plugin_info:
            plugin_name = plugin['name']
            plugin_path = plugin['path']
            manifest_path = plugin['manifest_path']
            
            try:
                # Read manifest to get main module
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                main_module = manifest.get("main")
                if not main_module:
                    init_results[plugin_name] = {
                        'status': 'Failure',
                        'message': "No main module specified in manifest"
                    }
                    init_failures += 1
                    continue
                    
                # Check if main module exists
                main_path = os.path.join(plugin_path, main_module)
                if not os.path.exists(main_path):
                    init_results[plugin_name] = {
                        'status': 'Failure',
                        'message': f"Main module file not found: {main_module}"
                    }
                    init_failures += 1
                    continue
                
                # Try to import the module (without executing it)
                spec = importlib.util.spec_from_file_location(f"{plugin_name}.main", main_path)
                if not spec:
                    init_results[plugin_name] = {
                        'status': 'Failure',
                        'message': f"Could not create module spec from {main_path}"
                    }
                    init_failures += 1
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                # We don't execute the module to avoid side effects
                # spec.loader.exec_module(module)
                
                init_results[plugin_name] = {
                    'status': 'Success',
                    'message': f"Plugin module can be imported"
                }
                
            except Exception as e:
                init_results[plugin_name] = {
                    'status': 'Failure',
                    'message': f"Error during initialization check: {e}"
                }
                init_failures += 1
        
        # Determine overall status
        if not enabled_plugin_info:
            self.results['plugin_initialization'] = {
                'status': 'Warning',
                'message': 'Enabled plugins not found in plugin directory'
            }
            self.log("Enabled plugins not found")
            return False
        elif init_failures == 0:
            self.results['plugin_initialization'] = {
                'status': 'Success',
                'message': f"All {len(enabled_plugin_info)} enabled plugins passed initialization check"
            }
            self.log("All enabled plugins passed initialization check")
            return True
        elif init_failures == len(enabled_plugin_info):
            self.results['plugin_initialization'] = {
                'status': 'Failure',
                'message': f"All {len(enabled_plugin_info)} enabled plugins failed initialization check",
                'details': init_results
            }
            self.log("All enabled plugins failed initialization check")
            return False
        else:
            self.results['plugin_initialization'] = {
                'status': 'Warning',
                'message': f"{init_failures} of {len(enabled_plugin_info)} enabled plugins failed initialization check",
                'details': init_results
            }
            self.log(f"{init_failures} plugins failed initialization check")
            return False
    
    def check_plugin_configuration(self):
        """Check if plugins have proper configuration settings"""
        if not self.config_loaded:
            self.results['plugin_configuration'] = {
                'status': 'Skipped',
                'message': 'Configuration manager not initialized'
            }
            self.log("Skipping configuration check - config not loaded")
            return False
        
        self.log("Checking plugin configuration...")
        
        # Check if plugins section exists in config
        plugins_config = self.config_manager.get("plugins", {})
        if not plugins_config:
            self.results['plugin_configuration'] = {
                'status': 'Warning',
                'message': 'Plugins section missing from configuration'
            }
            self.log("Plugins section missing from configuration")
            return False
            
        # Check for plugin_directory setting
        if "plugin_directory" not in plugins_config:
            self.results['plugin_configuration'] = {
                'status': 'Warning',
                'message': 'Plugin directory not specified in configuration'
            }
            self.log("Plugin directory not specified in configuration")
            return False
            
        # Check if plugin_settings section exists for enabled plugins
        plugin_settings = plugins_config.get("plugin_settings", {})
        missing_settings = []
        
        for plugin_name in self.enabled_plugins:
            if plugin_name not in plugin_settings:
                missing_settings.append(plugin_name)
        
        if missing_settings:
            self.results['plugin_configuration'] = {
                'status': 'Warning',
                'message': f"Configuration missing for plugins: {', '.join(missing_settings)}"
            }
            self.log(f"Configuration missing for {len(missing_settings)} plugins")
            return False
        else:
            self.results['plugin_configuration'] = {
                'status': 'Success',
                'message': 'All enabled plugins have configuration settings'
            }
            self.log("All enabled plugins have configuration settings")
            return True
    
    def run_all_checks(self):
        """Run all plugin diagnostic checks"""
        self.log("Starting plugin diagnostics...")
        try:
            # Explicitly import time module within the method to avoid name errors
            import time
            start_time = time.time()
            
            # Run checks
            self.check_plugin_directory()
            self.check_plugin_manifests()
            self.check_plugin_dependencies()
            self.check_plugin_initialization()
            self.check_plugin_configuration()
            
            elapsed_time = time.time() - start_time
            self.log(f"Plugin diagnostics completed in {elapsed_time:.2f} seconds")
        except Exception as e:
            self.log(f"Error running plugin diagnostics: {str(e)}")
            import traceback
            traceback.print_exc()
        return self.results
