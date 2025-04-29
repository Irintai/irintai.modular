"""
IrintAI Assistant Diagnostic Fixer

This module provides automated fixes for issues identified by the diagnostic suite.
"""
import os
import sys
import json
import logging
from pathlib import Path
import importlib
from datetime import datetime
import requests

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from diagnostics.diagnostic_suite import DiagnosticSuite
from core.config_manager import ConfigManager
from utils.logger import IrintaiLogger

# Setup logger for diagnostic fixer
logger = IrintaiLogger('diagnostic_fixer', 'diagnostic_fixer.log')

class DiagnosticFixer:
    """Provides automated fixes for issues found by the diagnostic suite"""
    
    def __init__(self, config_path='data/config.json'):
        """Initialize the diagnostic fixer with configuration"""
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.diagnostic_suite = DiagnosticSuite(config_path=config_path)
        self.fix_functions = {
            'system': self._fix_system_issues,
            'config': self._fix_config_issues,
            'ollama': self._fix_ollama_issues,
            'plugin': self._fix_plugin_issues,
            'memory': self._fix_memory_issues,
            'network': self._fix_network_issues
        }
        self.fixed_issues = {
            'system': [],
            'config': [],
            'ollama': [],
            'plugin': [],
            'memory': [],
            'network': []
        }
        self.unfixable_issues = {
            'system': [],
            'config': [],
            'ollama': [],
            'plugin': [],
            'memory': [],
            'network': []
        }
    
    def run_diagnostics(self):
        """Run diagnostics to identify issues"""
        logger.info("Running diagnostics to identify issues...")
        self.diagnostic_suite.run_all_diagnostics()
        return self.diagnostic_suite.results
    
    def fix_all_issues(self):
        """Run diagnostics and fix all identified issues"""
        # First run diagnostics to identify issues
        results = self.run_diagnostics()
        
        # Get summary to check if there are issues
        summary = self.diagnostic_suite.get_summary()
        if isinstance(summary, str) or summary['overall_status'] == 'Success':
            logger.info("No issues found that need fixing")
            return {'fixed': 0, 'unfixable': 0}
        
        # Fix issues in each module
        fixed_count = 0
        unfixable_count = 0
        
        for module_name, module_results in results.items():
            if module_name in self.fix_functions:
                module_fixed, module_unfixable = self.fix_functions[module_name](module_results)
                fixed_count += module_fixed
                unfixable_count += module_unfixable
        
        # Run diagnostics again to verify fixes
        verification_results = self.run_diagnostics()
        verification_summary = self.diagnostic_suite.get_summary()
        
        return {
            'fixed': fixed_count,
            'unfixable': unfixable_count,
            'fixed_issues': self.fixed_issues,
            'unfixable_issues': self.unfixable_issues,
            'verification': verification_summary
        }
    
    def fix_module_issues(self, module_name):
        """Fix issues for a specific module"""
        if module_name not in self.fix_functions:
            logger.error(f"Unknown module: {module_name}")
            return {'error': f"Unknown module: {module_name}"}
        
        # Run specific diagnostic
        results = self.diagnostic_suite.run_specific_diagnostic(module_name)
        
        # Fix issues
        fixed_count, unfixable_count = self.fix_functions[module_name](results)
        
        # Verify fixes
        verification_results = self.diagnostic_suite.run_specific_diagnostic(module_name)
        
        return {
            'fixed': fixed_count,
            'unfixable': unfixable_count,
            'fixed_issues': self.fixed_issues[module_name],
            'unfixable_issues': self.unfixable_issues[module_name],
            'verification': verification_results
        }
    def _fix_system_issues(self, results):
        """Fix system-related issues"""
        fixed_count = 0
        unfixable_count = 0
        
        for check, result in results.items():
            if isinstance(result, dict) and result.get('status', '').lower() in ['failure', 'warning']:
                issue_description = f"{check}: {result.get('message', 'No details')}"
                
                if check == 'system_resources':
                    # Try to address high CPU/memory usage
                    try:
                        # Create a resource optimization script
                        resource_script = os.path.join(project_root, "optimize_resources.bat")
                        with open(resource_script, 'w') as f:
                            f.write('@echo off\n')
                            f.write('echo IrintAI Assistant Resource Optimizer\n')
                            f.write('echo ===============================\n')
                            f.write('echo.\n')
                            f.write('echo Checking for resource-intensive processes...\n')
                            f.write('echo.\n')
                            f.write('powershell -command "Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 | Format-Table -AutoSize Id, ProcessName, CPU, WorkingSet"\n')
                            f.write('echo.\n')
                            f.write('echo Cleaning up temporary files...\n')
                            f.write('powershell -command "Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue"\n')
                            f.write('echo.\n')
                            f.write('echo Checking for large log files in IrintAI Assistant...\n')
                            f.write('dir /s /b "%~dp0..\\data\\logs\\*.log" | findstr /v ""\n')
                            f.write('echo.\n')
                            f.write('echo Would you like to clean up old log files? (Y/N)\n')
                            f.write('set /p clean="Enter your choice: "\n')
                            f.write('if /i "%clean%" == "Y" (\n')
                            f.write('    echo Cleaning up logs older than 7 days...\n')
                            f.write('    forfiles /p "%~dp0..\\data\\logs" /s /m *.log /d -7 /c "cmd /c del @path" 2>nul\n')
                            f.write('    echo Done cleaning logs.\n')
                            f.write(')\n')
                            f.write('echo.\n')
                            f.write('echo Recommendations to improve system resources:\n')
                            f.write('echo 1. Close unnecessary applications\n')
                            f.write('echo 2. Restart the computer if it has been running for a long time\n')
                            f.write('echo 3. Consider upgrading memory if consistently at high usage\n')
                            f.write('echo 4. Check for malware that might be consuming resources\n')
                            f.write('echo.\n')
                            f.write('echo Press any key to exit...\n')
                            f.write('pause > nul\n')
                        
                        self.fixed_issues['system'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': "Created optimize_resources.bat script to help identify and reduce resource usage. Run this script to view top resource-intensive processes and clean temporary files."
                        })
                        fixed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create resource optimization script: {e}")
                        self.unfixable_issues['system'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to create resource optimization script: {e}"
                        })
                        unfixable_count += 1
                
                elif check == 'network_connectivity':
                    # Try to fix network connectivity issues
                    try:
                        # Create a network diagnostic script
                        network_script = os.path.join(project_root, "diagnose_network.bat")
                        with open(network_script, 'w') as f:
                            f.write('@echo off\n')
                            f.write('echo IrintAI Assistant Network Diagnostics\n')
                            f.write('echo =============================\n')
                            f.write('echo.\n')
                            f.write('echo Checking internet connectivity...\n')
                            f.write('ping -n 4 8.8.8.8\n')
                            f.write('echo.\n')
                            f.write('echo Checking DNS resolution...\n')
                            f.write('nslookup google.com\n')
                            f.write('nslookup ollama.ai\n')
                            f.write('nslookup api.github.com\n')
                            f.write('echo.\n')
                            f.write('echo Checking proxy settings...\n')
                            f.write('netsh winhttp show proxy\n')
                            f.write('echo.\n')
                            f.write('echo Checking firewall status...\n')
                            f.write('netsh advfirewall show allprofiles state\n')
                            f.write('echo.\n')
                            f.write('echo Attempting to access Ollama API...\n')
                            f.write('powershell -command "try { $response = Invoke-WebRequest -Uri http://localhost:11434/api/version -UseBasicParsing -TimeoutSec 5; Write-Host \"Response: $($response.StatusCode) $($response.StatusDescription)\"; Write-Host $response.Content } catch { Write-Host \"Error: $_\" }"\n')
                            f.write('echo.\n')
                            f.write('echo Would you like to reset network settings? (Y/N)\n')
                            f.write('set /p reset="Enter your choice: "\n')
                            f.write('if /i "%reset%" == "Y" (\n')
                            f.write('    echo Resetting network settings...\n')
                            f.write('    ipconfig /flushdns\n')
                            f.write('    netsh winsock reset\n')
                            f.write('    echo Network settings reset. A system restart is recommended.\n')
                            f.write(')\n')
                            f.write('echo.\n')
                            f.write('echo Press any key to exit...\n')
                            f.write('pause > nul\n')
                        
                        self.fixed_issues['system'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': "Created diagnose_network.bat script to help diagnose and fix network connectivity issues."
                        })
                        fixed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create network diagnostic script: {e}")
                        self.unfixable_issues['system'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to create network diagnostic script: {e}"
                        })
                        unfixable_count += 1
                
                elif check == 'python_version':
                    # Can't fix Python version automatically
                    self.unfixable_issues['system'].append({
                        'check': check,
                        'message': result.get('message', ''),
                        'reason': "Python version can't be changed automatically"
                    })
                    unfixable_count += 1
                
                elif check == 'memory_available':
                    # Can't fix memory issues automatically
                    self.unfixable_issues['system'].append({
                        'check': check,
                        'message': result.get('message', ''),
                        'reason': "Memory issues require hardware changes or closing other applications"
                    })
                    unfixable_count += 1
                
                elif check == 'disk_space':
                    # Attempt to clean temp files to free up space
                    try:
                        # Try to clean up logs older than 7 days
                        import shutil
                        from datetime import datetime, timedelta
                        
                        logs_dir = os.path.join(project_root, 'data', 'logs')
                        if os.path.exists(logs_dir):
                            cutoff_date = datetime.now() - timedelta(days=7)
                            cleaned_files = 0
                            bytes_freed = 0
                            
                            for log_file in os.listdir(logs_dir):
                                log_path = os.path.join(logs_dir, log_file)
                                if os.path.isfile(log_path):
                                    file_time = datetime.fromtimestamp(os.path.getmtime(log_path))
                                    if file_time < cutoff_date:
                                        file_size = os.path.getsize(log_path)
                                        os.remove(log_path)
                                        cleaned_files += 1
                                        bytes_freed += file_size
                            
                            if cleaned_files > 0:
                                self.fixed_issues['system'].append({
                                    'check': check,
                                    'message': result.get('message', ''),
                                    'fix': f"Removed {cleaned_files} old log files, freeing {bytes_freed / (1024*1024):.2f} MB"
                                })
                                fixed_count += 1
                            else:
                                self.unfixable_issues['system'].append({
                                    'check': check,
                                    'message': result.get('message', ''),
                                    'reason': "No old log files to clean up. Manual cleanup needed."
                                })
                                unfixable_count += 1
                    except Exception as e:
                        logger.error(f"Failed to fix disk space issue: {e}")
                        self.unfixable_issues['system'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Auto-cleanup failed: {e}"
                        })
                        unfixable_count += 1
                
                elif check == 'required_packages':
                    # Try to install missing packages
                    try:
                        message = result.get('message', '')
                        import re
                        missing_packages = re.findall(r"missing: ([a-zA-Z0-9_\-]+)", message)
                        
                        if missing_packages:
                            import subprocess
                            for package in missing_packages:
                                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                            
                            self.fixed_issues['system'].append({
                                'check': check,
                                'message': message,
                                'fix': f"Installed missing packages: {', '.join(missing_packages)}"
                            })
                            fixed_count += 1
                        else:
                            self.unfixable_issues['system'].append({
                                'check': check,
                                'message': message,
                                'reason': "Couldn't identify specific missing packages"
                            })
                            unfixable_count += 1
                    except Exception as e:
                        logger.error(f"Failed to fix package issue: {e}")
                        self.unfixable_issues['system'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Package installation failed: {e}"
                        })
                        unfixable_count += 1
                
                else:
                    # Generic unfixable issue
                    self.unfixable_issues['system'].append({
                        'check': check,
                        'message': result.get('message', ''),
                        'reason': "No automated fix available for this issue"
                    })
                    unfixable_count += 1
        
        return fixed_count, unfixable_count    
    
    def _fix_config_issues(self, results):
        """Fix configuration-related issues"""
        fixed_count = 0
        unfixable_count = 0
        
        for check, result in results.items():
            if isinstance(result, dict) and result.get('status', '').lower() in ['failure', 'warning']:
                issue_description = f"{check}: {result.get('message', 'No details')}"
                
                if check == 'ollama_url':
                    # Fix Ollama URL configuration
                    try:
                        config_path = os.path.join(project_root, self.config_path)
                        if os.path.exists(config_path):
                            with open(config_path, 'r') as f:
                                config_data = json.load(f)
                            
                            # Add or update the Ollama URL configuration
                            if 'ollama' not in config_data:
                                config_data['ollama'] = {}
                            
                            config_data['ollama']['url'] = 'http://localhost:11434'
                            
                            # Also add a top-level ollama_url for backward compatibility
                            config_data['ollama_url'] = 'http://localhost:11434'
                            
                            with open(config_path, 'w') as f:
                                json.dump(config_data, f, indent=2)
                            
                            self.fixed_issues['config'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'fix': "Set Ollama URL to http://localhost:11434 in configuration"
                            })
                            fixed_count += 1
                        else:
                            self.unfixable_issues['config'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'reason': "Config file doesn't exist. Fix 'config_file_exists' issue first."
                            })
                            unfixable_count += 1
                    except Exception as e:
                        logger.error(f"Failed to set Ollama URL: {e}")
                        self.unfixable_issues['config'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to set Ollama URL: {e}"
                        })
                        unfixable_count += 1
                        
                elif check == 'config_file_exists':
                    # Try to create default config file
                    try:
                        config_dir = os.path.dirname(os.path.join(project_root, self.config_path))
                        os.makedirs(config_dir, exist_ok=True)
                        
                        default_config = {
                            "model": {
                                "provider": "ollama",
                                "name": "llama3:8b",
                                "api_key": ""
                            },
                            "interface": {
                                "theme": "light",
                                "font_size": 12
                            },
                            "plugins": {
                                "enabled": ["memory", "personality"],
                                "settings": {},
                                "plugin_directory": "plugins"
                            },
                            "memory": {
                                "enabled": True,
                                "storage_type": "vector",
                                "max_history": 100
                            },
                            "ui": {
                                "theme": "System",
                                "font_size": 12,
                                "window_size": "1024x768"
                            },
                            "logging": {
                                "log_level": "INFO",
                                "log_directory": "data/logs"
                            },
                            "ollama": {
                                "url": "http://localhost:11434"
                            }
                        }
                        
                        with open(os.path.join(project_root, self.config_path), 'w') as f:
                            json.dump(default_config, f, indent=2)
                        
                        self.fixed_issues['config'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': "Created default configuration file"
                        })
                        fixed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create config file: {e}")
                        self.unfixable_issues['config'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to create config file: {e}"
                        })
                        unfixable_count += 1
                
                elif check == 'config_format':
                    # Try to fix JSON format
                    try:
                        config_path = os.path.join(project_root, self.config_path)
                        with open(config_path, 'r') as f:
                            config_text = f.read()
                        
                        # Try to parse and reformat
                        try:
                            config_data = json.loads(config_text)
                            with open(config_path, 'w') as f:
                                json.dump(config_data, f, indent=2)
                            
                            self.fixed_issues['config'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'fix': "Reformatted config JSON"
                            })
                            fixed_count += 1
                        except json.JSONDecodeError:
                            # If we can't parse it, we need manual intervention
                            self.unfixable_issues['config'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'reason': "Config file has JSON syntax errors that require manual fixing"
                            })
                            unfixable_count += 1
                    except Exception as e:
                        logger.error(f"Failed to fix config format: {e}")
                        self.unfixable_issues['config'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to fix config format: {e}"
                        })
                        unfixable_count += 1
                elif check in ['required_fields', 'required_settings', 'path_validations', 'models_configuration']:
                    # Try to add missing required fields and restructure the config
                    try:
                        config_path = os.path.join(project_root, self.config_path)
                        if not os.path.exists(config_path):
                            self.unfixable_issues['config'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'reason': "Config file doesn't exist. Fix 'config_file_exists' issue first."
                            })
                            unfixable_count += 1
                            continue
                        
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)
                        
                        # Create a new restructured configuration
                        restructured_config = {}
                        
                        # Model section
                        restructured_config["model"] = {
                            "provider": "ollama",
                            "name": config_data.get('model', 'llama3:8b'),
                            "api_key": "",
                            "use_8bit": config_data.get('use_8bit', True),
                            "top_p": config_data.get('top_p', 0.9),
                            "temperature": config_data.get('temperature', 0.7),
                            "max_tokens": config_data.get('max_tokens', 2048),
                            "context_window": config_data.get('context_window', 4096)
                        }
                        
                        # UI section
                        restructured_config["ui"] = {
                            "theme": config_data.get('theme', 'System'),
                            "font_size": config_data.get('font_size', 12),
                            "window_size": "1024x768",
                            "show_debug_messages": config_data.get('show_debug_messages', False),
                            "start_minimized": config_data.get('start_minimized', False),
                            "confirm_exit": config_data.get('confirm_exit', True)
                        }
                        
                        # Plugins section
                        restructured_config["plugins"] = {
                            "enabled": config_data.get('autoload_plugins', []),
                            "plugin_directory": "plugins",
                            "settings": {}
                        }
                        if 'autoload_plugins' in config_data:
                            restructured_config["plugins"]["enabled"] = config_data['autoload_plugins']
                        
                        # Memory section
                        restructured_config["memory"] = {
                            "enabled": config_data.get('auto_save_session', True),
                            "storage_type": "vector",
                            "max_history": 100,
                            "embedding_model": config_data.get('embedding_model', 'all-mpnet-base-v2'),
                            "relevance_threshold": config_data.get('relevance_threshold', 0.7),
                            "default_result_count": config_data.get('default_result_count', 5),
                            "index_path": config_data.get('index_path', 'data/vector_store/vector_store.json')
                        }
                        
                        # Logging section
                        restructured_config["logging"] = {
                            "log_level": config_data.get('log_level', 'INFO'),
                            "log_directory": config_data.get('log_dir', 'data/logs'),
                            "max_log_size_mb": config_data.get('max_log_size_mb', 10),
                            "keep_backup_logs": config_data.get('keep_backup_logs', True)
                        }
                        
                        # Ollama section
                        restructured_config["ollama"] = {
                            "url": config_data.get('ollama_url', 'http://localhost:11434'),
                            "model_path": config_data.get('model_path', '')
                        }
                        
                        # System section
                        restructured_config["system"] = {
                            "system_message": config_data.get('system_message', 'You are Irintai, a helpful and knowledgeable assistant.'),
                            "system_prompt": config_data.get('system_prompt', 'You are a helpful, creative, and knowledgeable assistant.'),
                            "inference_mode": config_data.get('inference_mode', 'GPU'),
                            "memory_mode": config_data.get('memory_mode', 'Auto'),
                            "check_updates": config_data.get('check_updates', True),
                            "nsfw_enabled": config_data.get('nsfw_enabled', False)
                        }
                        
                        # Write the restructured config
                        with open(config_path, 'w') as f:
                            json.dump(restructured_config, f, indent=2)
                        
                        self.fixed_issues['config'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': "Completely restructured configuration with proper sections and required fields"
                        })
                        fixed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to fix required fields: {e}")
                        self.unfixable_issues['config'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to fix required fields: {e}"
                        })
                        unfixable_count += 1
                
                else:
                    # Generic unfixable issue
                    self.unfixable_issues['config'].append({
                        'check': check,
                        'message': result.get('message', ''),
                        'reason': "No automated fix available for this issue"
                    })
                    unfixable_count += 1
        
        return fixed_count, unfixable_count
    def _fix_ollama_issues(self, results):
        """Fix Ollama-related issues"""
        fixed_count = 0
        unfixable_count = 0
        
        for check, result in results.items():
            if isinstance(result, dict) and result.get('status', '').lower() in ['failure', 'warning']:
                issue_description = f"{check}: {result.get('message', 'No details')}"
                if check in ['ollama_installed', 'ollama_installation', 'list_local_models', 'pull_model']:
                    # For Ollama-related issues, recommend installation and provide guidance
                    # We can't automatically install Ollama, but we can guide the user
                    
                    # First, create a shell script that tries multiple Ollama version commands
                    try:
                        # Create a batch file to check for Ollama using multiple version command formats
                        ollama_check_script = os.path.join(project_root, "check_ollama.bat")
                        with open(ollama_check_script, 'w') as f:
                            f.write('@echo off\n')
                            f.write('echo Checking Ollama installation...\n')
                            f.write('echo.\n')
                            f.write('echo Trying format 1: ollama --version\n')
                            f.write('ollama --version 2>nul\n')
                            f.write('if %ERRORLEVEL% EQU 0 goto :found\n\n')
                            f.write('echo Trying format 2: ollama -v\n')
                            f.write('ollama -v 2>nul\n')
                            f.write('if %ERRORLEVEL% EQU 0 goto :found\n\n')
                            f.write('echo Trying format 3: ollama version\n')
                            f.write('ollama version 2>nul\n')
                            f.write('if %ERRORLEVEL% EQU 0 goto :found\n\n')
                            f.write('echo Checking if Ollama is running...\n')
                            f.write('echo Checking http://localhost:11434/api/version\n')
                            f.write('powershell -command "try { $response = Invoke-WebRequest -Uri http://localhost:11434/api/version -UseBasicParsing; if($response.StatusCode -eq 200) { Write-Host \'Ollama API is responding\'; exit 0 } else { Write-Host \'Ollama API returned status code: \' $response.StatusCode; exit 1 } } catch { Write-Host \'Ollama API not responding: \' $_.Exception.Message; exit 1 }"\n')
                            f.write('if %ERRORLEVEL% EQU 0 goto :running\n\n')
                            f.write('echo Ollama not found or not running.\n')
                            f.write('goto :notfound\n\n')
                            f.write(':found\n')
                            f.write('echo Ollama is installed. Checking if it is running...\n')
                            f.write('powershell -command "try { $response = Invoke-WebRequest -Uri http://localhost:11434/api/version -UseBasicParsing; if($response.StatusCode -eq 200) { Write-Host \'Ollama API is responding\'; exit 0 } else { Write-Host \'Ollama API returned status code: \' $response.StatusCode; exit 1 } } catch { Write-Host \'Ollama API not responding: \' $_.Exception.Message; exit 1 }"\n')
                            f.write('if %ERRORLEVEL% EQU 0 goto :running\n')
                            f.write('echo Ollama is installed but not running. Starting Ollama service...\n')
                            f.write('start /B ollama serve\n')
                            f.write('timeout /t 5 /nobreak > nul\n')
                            f.write('goto :end\n\n')
                            f.write(':running\n')
                            f.write('echo Ollama is running properly!\n')
                            f.write('goto :end\n\n')
                            f.write(':notfound\n')
                            f.write('echo Checking common Ollama installation paths...\n')
                            for path in ["C:\\Program Files\\Ollama", "C:\\Ollama", "%USERPROFILE%\\Ollama", "%LOCALAPPDATA%\\Ollama"]:
                                f.write(f'if exist "{path}\\ollama.exe" (\n')
                                f.write(f'  echo Found Ollama at {path}\\ollama.exe\n')
                                f.write(f'  echo Adding {path} to PATH for this session\n')
                                f.write(f'  set "PATH=%PATH%;{path}"\n')
                                f.write('  echo Starting Ollama service...\n')
                                f.write('  start /B ollama serve\n')
                                f.write('  timeout /t 5 /nobreak > nul\n')
                                f.write('  goto :end\n')
                                f.write(')\n\n')
                            f.write('echo Ollama not found. Please install it from https://ollama.ai\n')
                            f.write(':end\n')
                        
                        # Create a second bat file that users can run to always start Ollama properly
                        startup_script = os.path.join(project_root, "start_ollama.bat")
                        with open(startup_script, 'w') as f:
                            f.write('@echo off\n')
                            f.write('echo Starting Ollama service...\n')
                            f.write('powershell -command "try { $response = Invoke-WebRequest -Uri http://localhost:11434/api/version -UseBasicParsing; if($response.StatusCode -eq 200) { Write-Host \'Ollama is already running\'; exit 0 } } catch {}\"\n')
                            f.write('if %ERRORLEVEL% EQU 0 goto :already_running\n\n')
                            f.write('for %%p in (\n')
                            f.write('  "C:\\Program Files\\Ollama\\ollama.exe"\n')
                            f.write('  "C:\\Ollama\\ollama.exe"\n')
                            f.write('  "%USERPROFILE%\\Ollama\\ollama.exe"\n')
                            f.write('  "%LOCALAPPDATA%\\Ollama\\ollama.exe"\n')
                            f.write(') do (\n')
                            f.write('  if exist %%p (\n')
                            f.write('    echo Found Ollama at %%p\n')
                            f.write('    echo Adding Ollama directory to PATH\n')
                            f.write('    for %%d in (%%p\\..) do set "OLLAMA_DIR=%%~fd"\n')
                            f.write('    set "PATH=%PATH%;%OLLAMA_DIR%"\n')
                            f.write('    echo Starting Ollama service...\n')
                            f.write('    start /B ollama serve\n')
                            f.write('    echo Ollama service started.\n')
                            f.write('    echo Waiting for the service to initialize...\n')
                            f.write('    timeout /t 5 /nobreak > nul\n')
                            f.write('    goto :end\n')
                            f.write('  )\n')
                            f.write(')\n\n')
                            f.write('echo Ollama executable not found. Please install Ollama from https://ollama.ai\n')
                            f.write('goto :end\n\n')
                            f.write(':already_running\n')
                            f.write('echo Ollama is already running.\n')
                            f.write(':end\n')
                            f.write('echo.\n')
                            f.write('echo You can now use IrintAI Assistant.\n')
                            f.write('echo Press any key to exit...\n')
                            f.write('pause > nul\n')

                        # Run the check script
                        import subprocess
                        subprocess.run([ollama_check_script], shell=True)
                        
                        self.fixed_issues['ollama'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': f"Created diagnostic scripts (check_ollama.bat and start_ollama.bat) to detect and fix Ollama installation issues. Please run start_ollama.bat before using IrintAI Assistant."
                        })
                        fixed_count += 1
                    
                    except Exception as e:
                        logger.error(f"Failed to create Ollama scripts: {e}")
                        
                        # Fallback: Check if Ollama is actually installed but just not in PATH
                        ollama_paths = [
                            "C:\\Program Files\\Ollama\\ollama.exe",
                            "C:\\Ollama\\ollama.exe",
                            os.path.expanduser("~\\Ollama\\ollama.exe"),
                            os.path.expanduser("~\\AppData\\Local\\Ollama\\ollama.exe")
                        ]
                        
                        found_ollama = False
                        for path in ollama_paths:
                            if os.path.exists(path):
                                found_ollama = True
                                # Try to create a simpler batch script
                                try:
                                    bat_path = os.path.join(project_root, "start_ollama_simple.bat")
                                    with open(bat_path, 'w') as f:
                                        f.write(f'@echo off\necho Adding Ollama to PATH...\nset "PATH=%PATH%;{os.path.dirname(path)}"\necho Starting Ollama server...\nstart /B ollama serve\necho Ollama server started in background.\n')
                                    
                                    self.fixed_issues['ollama'].append({
                                        'check': check,
                                        'message': result.get('message', ''),
                                        'fix': f"Created start_ollama_simple.bat script to add Ollama to PATH and start the server. Please run this script before using IrintAI Assistant."
                                    })
                                    fixed_count += 1
                                    break
                                except Exception as e2:
                                    logger.error(f"Failed to create simple Ollama startup script: {e2}")
                        
                        if not found_ollama:
                            # Provide detailed instructions for installing Ollama
                            self.unfixable_issues['ollama'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'reason': "Ollama needs to be installed manually. Please visit https://ollama.ai, download and install Ollama, then run 'ollama serve' from a terminal."
                            })
                            unfixable_count += 1
                
                elif check == 'ollama_running':
                    # Try to start Ollama service
                    try:
                        import subprocess
                        import platform
                        
                        system = platform.system().lower()
                        if system == 'windows':
                            # Start Ollama on Windows
                            subprocess.Popen(['start', 'ollama', 'serve'], 
                                           shell=True, 
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                        elif system == 'darwin':
                            # Start Ollama on macOS
                            subprocess.Popen(['open', '-a', 'Ollama'])
                        elif system == 'linux':
                            # Start Ollama on Linux
                            subprocess.Popen(['ollama', 'serve'], 
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                        
                        # Give it time to start
                        import time
                        time.sleep(3)
                        
                        # Check if it's running now
                        try:
                            response = requests.get('http://localhost:11434/api/version')
                            if response.status_code == 200:
                                self.fixed_issues['ollama'].append({
                                    'check': check,
                                    'message': result.get('message', ''),
                                    'fix': "Started Ollama service"
                                })
                                fixed_count += 1
                            else:
                                self.unfixable_issues['ollama'].append({
                                    'check': check,
                                    'message': result.get('message', ''),
                                    'reason': "Failed to start Ollama service automatically"
                                })
                                unfixable_count += 1
                        except requests.exceptions.RequestException:
                            self.unfixable_issues['ollama'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'reason': "Failed to start Ollama service automatically"
                            })
                            unfixable_count += 1
                    except Exception as e:
                        logger.error(f"Failed to start Ollama: {e}")
                        self.unfixable_issues['ollama'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to start Ollama: {e}"
                        })
                        unfixable_count += 1
                
                elif check == 'model_available':
                    # Try to pull the model
                    try:
                        # Get the model name from config
                        config_path = os.path.join(project_root, self.config_path)
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)
                        
                        model_name = config_data.get('model', {}).get('name', 'llama2')
                        
                        # Try to pull the model
                        import subprocess
                        result = subprocess.run(['ollama', 'pull', model_name], 
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             text=True)
                        
                        if result.returncode == 0:
                            self.fixed_issues['ollama'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'fix': f"Pulled model '{model_name}' successfully"
                            })
                            fixed_count += 1
                        else:
                            self.unfixable_issues['ollama'].append({
                                'check': check,
                                'message': result.get('message', ''),
                                'reason': f"Failed to pull model: {result.stderr}"
                            })
                            unfixable_count += 1
                    except Exception as e:
                        logger.error(f"Failed to pull model: {e}")
                        self.unfixable_issues['ollama'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to pull model: {e}"
                        })
                        unfixable_count += 1
                
                else:
                    # Generic unfixable issue
                    self.unfixable_issues['ollama'].append({
                        'check': check,
                        'message': result.get('message', ''),
                        'reason': "No automated fix available for this issue"
                    })
                    unfixable_count += 1
        
        return fixed_count, unfixable_count
    
    def _fix_plugin_issues(self, results):
        """Fix plugin-related issues"""
        fixed_count = 0
        unfixable_count = 0
        
        for check, result in results.items():
            if isinstance(result, dict) and result.get('status', '').lower() in ['failure', 'warning']:
                issue_description = f"{check}: {result.get('message', 'No details')}"
                
                if check == 'plugin_directory_exists':
                    # Try to create plugin directory
                    try:
                        plugins_dir = os.path.join(project_root, 'plugins')
                        os.makedirs(plugins_dir, exist_ok=True)
                        
                        self.fixed_issues['plugin'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': "Created plugins directory"
                        })
                        fixed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create plugin directory: {e}")
                        self.unfixable_issues['plugin'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to create plugin directory: {e}"
                        })
                        unfixable_count += 1
                
                elif check == 'plugin_dependencies':
                    # Try to install missing dependencies
                    try:
                        message = result.get('message', '')
                        import re
                        missing_deps = re.findall(r"missing: ([a-zA-Z0-9_\-]+)", message)
                        
                        if missing_deps:
                            import subprocess
                            for dep in missing_deps:
                                subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
                            
                            self.fixed_issues['plugin'].append({
                                'check': check,
                                'message': message,
                                'fix': f"Installed missing dependencies: {', '.join(missing_deps)}"
                            })
                            fixed_count += 1
                        else:
                            self.unfixable_issues['plugin'].append({
                                'check': check,
                                'message': message,
                                'reason': "Couldn't identify specific missing dependencies"
                            })
                            unfixable_count += 1
                    except Exception as e:
                        logger.error(f"Failed to fix plugin dependencies: {e}")
                        self.unfixable_issues['plugin'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to fix plugin dependencies: {e}"
                        })
                        unfixable_count += 1
                
                else:
                    # Generic unfixable issue
                    self.unfixable_issues['plugin'].append({
                        'check': check,
                        'message': result.get('message', ''),
                        'reason': "No automated fix available for this issue"
                    })
                    unfixable_count += 1
        
        return fixed_count, unfixable_count
    
    def _fix_memory_issues(self, results):
        """Fix memory system-related issues"""
        fixed_count = 0
        unfixable_count = 0
        
        for check, result in results.items():
            if isinstance(result, dict) and result.get('status', '').lower() in ['failure', 'warning']:
                issue_description = f"{check}: {result.get('message', 'No details')}"
                
                if check == 'memory_directory_exists':
                    # Try to create memory directory
                    try:
                        memory_dir = os.path.join(project_root, 'data', 'vector_store')
                        os.makedirs(memory_dir, exist_ok=True)
                        
                        self.fixed_issues['memory'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': "Created memory directory"
                        })
                        fixed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create memory directory: {e}")
                        self.unfixable_issues['memory'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to create memory directory: {e}"
                        })
                        unfixable_count += 1
                
                elif check == 'embedding_model':
                    # Try to install required embedding model packages
                    try:
                        # Install sentence-transformers which includes good embedding models
                        import subprocess
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'sentence-transformers'])
                        
                        self.fixed_issues['memory'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': "Installed sentence-transformers package for embedding models"
                        })
                        fixed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to install embedding model: {e}")
                        self.unfixable_issues['memory'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to install embedding model: {e}"
                        })
                        unfixable_count += 1
                
                else:
                    # Generic unfixable issue
                    self.unfixable_issues['memory'].append({
                        'check': check,
                        'message': result.get('message', ''),
                        'reason': "No automated fix available for this issue"
                    })
                    unfixable_count += 1
        
        return fixed_count, unfixable_count
    
    def _fix_network_issues(self, results):
        """Fix network-related issues"""
        fixed_count = 0
        unfixable_count = 0
        
        for check, result in results.items():
            if isinstance(result, dict) and result.get('status', '').lower() in ['failure', 'warning']:
                issue_description = f"{check}: {result.get('message', 'No details')}"
                
                # Most network issues require manual intervention
                if check == 'proxy_settings':
                    # Try to clear proxy settings that might be causing issues
                    try:
                        os.environ.pop('HTTP_PROXY', None)
                        os.environ.pop('HTTPS_PROXY', None)
                        os.environ.pop('http_proxy', None)
                        os.environ.pop('https_proxy', None)
                        
                        self.fixed_issues['network'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'fix': "Cleared proxy environment variables for this session"
                        })
                        fixed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to clear proxy settings: {e}")
                        self.unfixable_issues['network'].append({
                            'check': check,
                            'message': result.get('message', ''),
                            'reason': f"Failed to clear proxy settings: {e}"
                        })
                        unfixable_count += 1
                
                else:
                    # Generic unfixable network issue
                    self.unfixable_issues['network'].append({
                        'check': check,
                        'message': result.get('message', ''),
                        'reason': "Network issues typically require manual intervention"
                    })
                    unfixable_count += 1
        
        return fixed_count, unfixable_count
    
    def print_fix_report(self):
        """Print a report of fixed and unfixable issues"""
        print("\n===== IrintAI Assistant Diagnostic Fixer Report =====")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Count fixed and unfixable issues
        total_fixed = sum(len(issues) for issues in self.fixed_issues.values())
        total_unfixable = sum(len(issues) for issues in self.unfixable_issues.values())
        
        print(f"Total issues fixed: {total_fixed}")
        print(f"Total issues that need manual attention: {total_unfixable}")
        
        # Print fixed issues
        if total_fixed > 0:
            print("\n--- FIXED ISSUES ---")
            for module, issues in self.fixed_issues.items():
                if issues:
                    print(f"\n{module.upper()} Module:")
                    for i, issue in enumerate(issues, 1):
                        print(f"  {i}. {issue['check']}")
                        print(f"     Issue: {issue['message']}")
                        print(f"     Fix: {issue['fix']}")
        
        # Print unfixable issues
        if total_unfixable > 0:
            print("\n--- ISSUES REQUIRING MANUAL ATTENTION ---")
            for module, issues in self.unfixable_issues.items():
                if issues:
                    print(f"\n{module.upper()} Module:")
                    for i, issue in enumerate(issues, 1):
                        print(f"  {i}. {issue['check']}")
                        print(f"     Issue: {issue['message']}")
                        print(f"     Reason: {issue['reason']}")
        
        print("\n===== End of Fix Report =====")


# Add a command-line interface to run the fixer
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="IrintAI Assistant Diagnostic Fixer")
    parser.add_argument('--module', '-m', choices=['all', 'system', 'config', 'ollama', 'plugin', 'memory', 'network'],
                       default='all', help='Specific module to diagnose and fix')
    parser.add_argument('--config', '-c', default='data/config.json',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Initialize fixer
    fixer = DiagnosticFixer(config_path=args.config)
    
    # Run diagnostics and fixes
    if args.module == 'all':
        fixer.fix_all_issues()
    else:
        fixer.fix_module_issues(args.module)
    
    # Print report
    fixer.print_fix_report()


if __name__ == "__main__":
    main()
