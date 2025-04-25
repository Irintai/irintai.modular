"""
System Diagnostic Module for IrintAI Assistant

This module provides diagnostics for the system environment including:
- Python version and dependencies
- System resources (CPU, memory, disk)
- Operating system information
- Network connectivity
"""
import os
import sys
import platform
import psutil
import socket
import subprocess
import pkg_resources
import importlib
from urllib.request import urlopen
from urllib.error import URLError
import threading
import time

class SystemDiagnostic:
    """Diagnostic tool for system environment checks"""
    
    def __init__(self):
        """Initialize the system diagnostic module"""
        self.results = {}
        
    def log(self, message):
        """Simple print-based logging for diagnostics"""
        print(f"[SYSTEM DIAG] {message}")
        
    def check_python_version(self):
        """Check Python version and compatibility"""
        self.log("Checking Python version...")
        python_version = sys.version
        version_info = sys.version_info
        
        # Check if Python version is compatible (expecting 3.8+)
        min_version = (3, 8)
        is_compatible = version_info >= min_version
        
        if is_compatible:
            status = "Success"
            message = f"Python {python_version.split()[0]} is compatible (>= 3.8)"
        else:
            status = "Failure"
            message = f"Python {python_version.split()[0]} is not compatible. Version 3.8 or higher is required."
            
        self.results["python_version"] = {
            "status": status,
            "message": message,
            "version": python_version.split()[0]
        }
        
        self.log(f"Python version check: {status}")
        return is_compatible
        
    def check_dependencies(self):
        """Check required Python dependencies"""
        self.log("Checking Python dependencies...")
        
        # Define required packages
        required_packages = [
            "requests", "numpy", "tkinter", "json", "threading",
            "psutil", "importlib", "os", "sys", "socket", "time",
            "datetime", "platform", "subprocess", "urllib"
        ]
        
        results = {}
        for package in required_packages:
            try:
                # Handle special cases
                if package == "tkinter":
                    import tkinter
                    version = "installed"
                elif package in ["os", "sys", "json", "threading", "socket", "time", "datetime", "platform", "subprocess", "urllib"]:
                    # Standard library modules don't have a clear version
                    importlib.import_module(package)
                    version = "standard library"
                else:
                    # For pip-installed packages
                    dist = pkg_resources.get_distribution(package)
                    version = dist.version
                    
                results[package] = {
                    "status": "Success",
                    "version": version
                }
            except (pkg_resources.DistributionNotFound, ImportError):
                results[package] = {
                    "status": "Failure",
                    "message": f"Package {package} is not installed"
                }
        
        # Count successes and failures
        success_count = sum(1 for pkg in results.values() if pkg["status"] == "Success")
        failure_count = len(results) - success_count
        
        if failure_count == 0:
            self.results["dependencies"] = {
                "status": "Success",
                "message": f"All {len(required_packages)} required dependencies are installed",
                "details": results
            }
        else:
            self.results["dependencies"] = {
                "status": "Failure",
                "message": f"{failure_count} required dependencies are missing",
                "details": results
            }
            
        self.log(f"Dependency check: {success_count} OK, {failure_count} missing")
        return failure_count == 0
    
    def check_system_resources(self):
        """Check system resources (CPU, memory, disk)"""
        self.log("Checking system resources...")
        
        # CPU information
        cpu_count = psutil.cpu_count(logical=True)
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory information (in GB)
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 ** 3)
        memory_available = memory.available / (1024 ** 3)
        memory_used = memory.used / (1024 ** 3)
        memory_percent = memory.percent
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024 ** 3)
        disk_free = disk.free / (1024 ** 3)
        disk_used = disk.used / (1024 ** 3)
        disk_percent = disk.percent
        
        # Evaluate CPU, memory, disk status
        cpu_status = "Success" if cpu_usage < 90 else "Warning"
        memory_status = "Success"
        if memory_percent > 95:
            memory_status = "Failure"
        elif memory_percent > 85:
            memory_status = "Warning"
        
        disk_status = "Success"
        if disk_percent > 95:
            disk_status = "Failure"
        elif disk_percent > 85:
            disk_status = "Warning"
            
        # Determine overall resource status
        statuses = [cpu_status, memory_status, disk_status]
        if "Failure" in statuses:
            overall_status = "Failure"
        elif "Warning" in statuses:
            overall_status = "Warning"
        else:
            overall_status = "Success"
        
        self.results["system_resources"] = {
            "status": overall_status,
            "message": f"CPU: {cpu_usage}% used, Memory: {memory_percent}% used, Disk: {disk_percent}% used",
            "details": {
                "cpu": {
                    "status": cpu_status,
                    "count": cpu_count,
                    "usage_percent": cpu_usage
                },
                "memory": {
                    "status": memory_status,
                    "total_gb": round(memory_total, 2),
                    "available_gb": round(memory_available, 2),
                    "used_gb": round(memory_used, 2),
                    "percent": memory_percent
                },
                "disk": {
                    "status": disk_status,
                    "total_gb": round(disk_total, 2),
                    "free_gb": round(disk_free, 2),
                    "used_gb": round(disk_used, 2),
                    "percent": disk_percent
                }
            }
        }
        
        self.log(f"System resources check: {overall_status}")
        return overall_status == "Success"
    
    def check_os_info(self):
        """Check operating system information"""
        self.log("Checking OS information...")
        
        os_name = platform.system()
        os_release = platform.release()
        os_version = platform.version()
        architecture = platform.machine()
        
        self.results["os_info"] = {
            "status": "Success",
            "message": f"OS: {os_name} {os_release}, Architecture: {architecture}",
            "details": {
                "name": os_name,
                "release": os_release,
                "version": os_version,
                "architecture": architecture
            }
        }
        
        self.log("OS information check: Success")
        return True
    
    def check_network_connectivity(self):
        """Check network connectivity to key resources"""
        self.log("Checking network connectivity...")
        
        # Define key resources to check
        resources = [
            {"name": "Google DNS", "host": "8.8.8.8", "port": 53},
            {"name": "Internet", "url": "https://www.google.com"},
            {"name": "Ollama Hub", "url": "https://ollama.ai"},
            {"name": "GitHub", "url": "https://api.github.com"}
        ]
        
        results = {}
        connection_failures = 0
        
        # Check socket connections
        for resource in resources:
            if "host" in resource and "port" in resource:
                host = resource["host"]
                port = resource["port"]
                name = resource["name"]
                try:
                    socket_timeout = 3
                    socket.create_connection((host, port), timeout=socket_timeout)
                    results[name] = {
                        "status": "Success",
                        "message": f"Connected to {name} ({host}:{port})"
                    }
                except (socket.timeout, socket.error) as e:
                    connection_failures += 1
                    results[name] = {
                        "status": "Failure",
                        "message": f"Failed to connect to {name} ({host}:{port}): {str(e)}"
                    }
            
            # Check HTTP connections
            elif "url" in resource:
                url = resource["url"]
                name = resource["name"]
                try:
                    urlopen(url, timeout=5)
                    results[name] = {
                        "status": "Success",
                        "message": f"Connected to {name} ({url})"
                    }
                except URLError as e:
                    connection_failures += 1
                    results[name] = {
                        "status": "Failure",
                        "message": f"Failed to connect to {name} ({url}): {str(e)}"
                    }
        
        # Determine overall network status
        if connection_failures == 0:
            status = "Success"
            message = "All network connectivity tests passed"
        elif connection_failures < len(resources):
            status = "Warning"
            message = f"{connection_failures} of {len(resources)} network connectivity tests failed"
        else:
            status = "Failure"
            message = "All network connectivity tests failed"
        
        self.results["network_connectivity"] = {
            "status": status,
            "message": message,
            "details": results
        }
        
        self.log(f"Network connectivity check: {status} ({connection_failures} failures)")
        return status != "Failure"
    def check_ollama_installation(self):
        """Check if Ollama is installed and get its version"""
        self.log("Checking Ollama installation...")
        
        try:
            # Try to run the ollama command to get version
            # Try multiple version command formats since different Ollama versions use different commands
            commands = [
                ["ollama", "--version"],  # New Ollama format
                ["ollama", "version"],     # Old format
                ["ollama", "-v"]           # Another common format
            ]
            
            for cmd in commands:
                try:
                    process = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=5
                    )
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Try the next command if this one fails
                    continue
            
            if process.returncode == 0:
                version = process.stdout.strip()
                self.results["ollama_installation"] = {
                    "status": "Success",
                    "message": f"Ollama is installed: {version}",
                    "version": version
                }
                self.log(f"Ollama installation check: Success ({version})")
                return True
            else:
                self.results["ollama_installation"] = {
                    "status": "Failure",
                    "message": f"Error checking Ollama version: {process.stderr.strip()}"
                }
                self.log("Ollama installation check: Failure (command failed)")
                return False
                
        except FileNotFoundError:
            self.results["ollama_installation"] = {
                "status": "Failure",
                "message": "Ollama is not installed or not in PATH"
            }
            self.log("Ollama installation check: Failure (not installed)")
            return False
        except subprocess.TimeoutExpired:
            self.results["ollama_installation"] = {
                "status": "Failure",
                "message": "Timeout while checking Ollama version"
            }
            self.log("Ollama installation check: Failure (timeout)")
            return False
        except Exception as e:
            self.results["ollama_installation"] = {
                "status": "Failure",
                "message": f"Error checking Ollama installation: {str(e)}"
            }
            self.log(f"Ollama installation check: Failure ({str(e)})")
            return False
    
    def run_all_checks(self):
        """Run all system diagnostic checks"""
        self.log("Starting system diagnostics...")
        start_time = time.time()
        
        # Run checks
        self.check_python_version()
        self.check_dependencies()
        self.check_system_resources()
        self.check_os_info()
        self.check_network_connectivity()
        self.check_ollama_installation()
        
        elapsed_time = time.time() - start_time
        self.log(f"System diagnostics completed in {elapsed_time:.2f} seconds")
        return self.results
