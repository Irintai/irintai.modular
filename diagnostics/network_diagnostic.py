"""
Network Diagnostic Module for IrintAI Assistant

This module provides diagnostics for network connectivity and API endpoints including:
- Network interface status
- External API connectivity
- DNS resolution
- Proxy configuration
- Connection timeouts
"""
import os
import sys
import socket
import requests
import time
import platform
import subprocess
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import Dict, Any, List, Tuple

# Add project root to sys.path to allow importing core modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.config_manager import ConfigManager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure the script is run from the project root or the PYTHONPATH is set correctly.")

class NetworkDiagnostic:
    """Diagnostic tool for network connectivity checks"""
    
    def __init__(self, config_path='data/config.json'):
        """Initialize the network diagnostic module"""
        self.config_path = config_path
        self.results = {}
        
        # Try to initialize config manager
        try:
            self.config_manager = ConfigManager(config_path)
            self.config_loaded = True
            
            # Get network-specific configuration
            self.api_endpoints = self.config_manager.get("network", {}).get("api_endpoints", {})
            self.proxy_settings = self.config_manager.get("network", {}).get("proxy", {})
            self.timeout_settings = self.config_manager.get("network", {}).get("timeouts", {})
            
            # Default endpoints to check if none specified
            if not self.api_endpoints:
                self.api_endpoints = {
                    "ollama_api": "http://localhost:11434/api",
                    "github_api": "https://api.github.com",
                    "huggingface_api": "https://huggingface.co/api"
                }
                
        except Exception as e:
            self.config_loaded = False
            # Set some default endpoints to check
            self.api_endpoints = {
                "ollama_api": "http://localhost:11434/api",
                "github_api": "https://api.github.com",
                "huggingface_api": "https://huggingface.co/api"
            }
            self.proxy_settings = {}
            self.timeout_settings = {"connect": 5, "read": 10}
            print(f"Error loading configuration: {e}")
        
    def log(self, message):
        """Simple print-based logging for diagnostics"""
        print(f"[NETWORK DIAG] {message}")
    
    def check_internet_connectivity(self):
        """Check basic internet connectivity"""
        self.log("Checking internet connectivity...")
        
        # Define reliable external endpoints to check
        reliable_hosts = [
            ("Google DNS", "8.8.8.8", 53),
            ("Cloudflare DNS", "1.1.1.1", 53),
            ("Google Web", "www.google.com", 80)
        ]
        
        connected = False
        failures = []
        
        for name, host, port in reliable_hosts:
            try:
                # Try to create a connection with a short timeout
                socket.create_connection((host, port), timeout=3)
                connected = True
                self.log(f"Successfully connected to {name}")
                break
            except (socket.timeout, socket.error) as e:
                failures.append(f"{name}: {e}")
                self.log(f"Failed to connect to {name}: {e}")
        
        if connected:
            self.results['internet_connectivity'] = {
                'status': 'Success',
                'message': "Internet connectivity is available"
            }
            self.log("Internet connectivity check: Success")
            return True
        else:
            self.results['internet_connectivity'] = {
                'status': 'Failure',
                'message': f"No internet connectivity: {'; '.join(failures)}"
            }
            self.log("Internet connectivity check: Failure")
            return False
    
    def check_dns_resolution(self):
        """Check if DNS resolution is working properly"""
        self.log("Checking DNS resolution...")
        
        # Define domains to resolve
        domains = [
            "google.com",
            "github.com",
            "huggingface.co",
            "ollama.ai"
        ]
        
        resolved = []
        failed = []
        
        for domain in domains:
            try:
                ip_address = socket.gethostbyname(domain)
                resolved.append(f"{domain}: {ip_address}")
                self.log(f"Successfully resolved {domain} to {ip_address}")
            except socket.gaierror as e:
                failed.append(f"{domain}: {e}")
                self.log(f"Failed to resolve {domain}: {e}")
        
        if not failed:
            self.results['dns_resolution'] = {
                'status': 'Success',
                'message': f"All domains successfully resolved",
                'details': resolved
            }
            self.log("DNS resolution check: Success")
            return True
        elif len(failed) < len(domains):
            self.results['dns_resolution'] = {
                'status': 'Warning',
                'message': f"{len(failed)} of {len(domains)} domain resolutions failed: {'; '.join(failed)}",
                'details': {
                    'resolved': resolved,
                    'failed': failed
                }
            }
            self.log(f"DNS resolution check: Warning ({len(failed)} failures)")
            return True
        else:
            self.results['dns_resolution'] = {
                'status': 'Failure',
                'message': "All DNS resolutions failed",
                'details': failed
            }
            self.log("DNS resolution check: Failure")
            return False
    
    def check_api_endpoints(self):
        """Check connectivity to important API endpoints"""
        self.log("Checking API endpoints...")
        
        if not self.check_internet_connectivity():
            self.results['api_endpoints'] = {
                'status': 'Skipped',
                'message': 'Internet connectivity check failed'
            }
            self.log("Skipping API endpoint checks - No internet connectivity")
            return False
        
        successful = []
        warnings = []
        failures = []
        
        for name, url in self.api_endpoints.items():
            try:
                # Handle special case for localhost Ollama API
                if "localhost" in url or "127.0.0.1" in url:
                    try:
                        response = requests.get(url, timeout=3)
                        status_code = response.status_code
                        
                        if 200 <= status_code < 300:
                            successful.append(f"{name}: {url}")
                            self.log(f"Successfully connected to {name} ({url})")
                        else:
                            warnings.append(f"{name}: HTTP {status_code}")
                            self.log(f"Warning for {name}: HTTP {status_code}")
                    except requests.exceptions.ConnectionError:
                        # For Ollama API, this could just mean it's not running
                        warnings.append(f"{name}: Connection refused (service may not be running)")
                        self.log(f"Warning for {name}: Connection refused (service may not be running)")
                    except Exception as e:
                        failures.append(f"{name}: {str(e)}")
                        self.log(f"Failed to connect to {name}: {e}")
                else:
                    # For external APIs, make a simple HEAD request
                    headers = {'User-Agent': 'IrintAI-Assistant-Diagnostic/1.0'}
                    req = Request(url, headers=headers, method='HEAD')
                    response = urlopen(req, timeout=5)
                    status_code = response.status
                    
                    if 200 <= status_code < 300:
                        successful.append(f"{name}: {url}")
                        self.log(f"Successfully connected to {name} ({url})")
                    else:
                        warnings.append(f"{name}: HTTP {status_code}")
                        self.log(f"Warning for {name}: HTTP {status_code}")
            except HTTPError as e:
                # Some APIs return error codes for HEAD requests but still work
                if e.code == 405:  # Method Not Allowed
                    warnings.append(f"{name}: HTTP {e.code} (Method not allowed but API may still be accessible)")
                    self.log(f"Warning for {name}: HTTP {e.code} (Method not allowed)")
                else:
                    failures.append(f"{name}: HTTP {e.code}")
                    self.log(f"Failed to connect to {name}: HTTP {e.code}")
            except URLError as e:
                failures.append(f"{name}: {e.reason}")
                self.log(f"Failed to connect to {name}: {e.reason}")
            except Exception as e:
                failures.append(f"{name}: {str(e)}")
                self.log(f"Failed to connect to {name}: {e}")
        
        # Determine overall status
        if not failures and not warnings:
            self.results['api_endpoints'] = {
                'status': 'Success',
                'message': f"All {len(successful)} API endpoints are accessible",
                'details': {
                    'successful': successful
                }
            }
            self.log("API endpoints check: Success")
            return True
        elif not failures:
            self.results['api_endpoints'] = {
                'status': 'Warning',
                'message': f"{len(warnings)} API endpoints have warnings",
                'details': {
                    'successful': successful,
                    'warnings': warnings
                }
            }
            self.log(f"API endpoints check: Warning ({len(warnings)} warnings)")
            return True
        else:
            self.results['api_endpoints'] = {
                'status': 'Failure',
                'message': f"{len(failures)} API endpoints failed",
                'details': {
                    'successful': successful,
                    'warnings': warnings,
                    'failures': failures
                }
            }
            self.log(f"API endpoints check: Failure ({len(failures)} failures)")
            return len(failures) < len(self.api_endpoints)
    
    def check_network_latency(self):
        """Check network latency to key services"""
        self.log("Checking network latency...")
        
        hosts = [
            "8.8.8.8",           # Google DNS
            "1.1.1.1",           # Cloudflare DNS
            "www.google.com",    # Google
            "api.github.com",    # GitHub API
            "huggingface.co"     # HuggingFace
        ]
        
        latency_results = {}
        high_latency_count = 0
        error_count = 0
        
        for host in hosts:
            latency_ms = None
            error = None
            
            # Use platform-specific ping command
            if platform.system().lower() == "windows":
                command = ["ping", "-n", "4", host]
            else:
                command = ["ping", "-c", "4", host]
                
            try:
                # Run ping command
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if process.returncode == 0:
                    # Parse average ping time from output
                    output = process.stdout
                    
                    if platform.system().lower() == "windows":
                        # Parse Windows ping output
                        for line in output.split("\n"):
                            if "Average" in line:
                                parts = line.split("=")
                                if len(parts) > 1:
                                    avg_part = parts[1].strip()
                                    latency_ms = int(avg_part.split("ms")[0].strip())
                                    break
                    else:
                        # Parse Linux/macOS ping output
                        for line in output.split("\n"):
                            if "min/avg/max" in line:
                                parts = line.split("=")[1].strip().split("/")
                                if len(parts) > 2:
                                    latency_ms = float(parts[1])
                                    break
                    
                    if latency_ms is not None:
                        if latency_ms > 200:
                            high_latency_count += 1
                        latency_results[host] = {
                            'status': 'Warning' if latency_ms > 200 else 'Success',
                            'latency_ms': latency_ms
                        }
                        self.log(f"Latency to {host}: {latency_ms} ms")
                    else:
                        error_count += 1
                        latency_results[host] = {
                            'status': 'Warning',
                            'error': 'Could not parse ping output'
                        }
                else:
                    error_count += 1
                    latency_results[host] = {
                        'status': 'Failure',
                        'error': process.stderr or "Ping command failed"
                    }
                    self.log(f"Failed to ping {host}: {process.stderr}")
            except subprocess.TimeoutExpired:
                error_count += 1
                latency_results[host] = {
                    'status': 'Failure',
                    'error': 'Ping command timed out'
                }
                self.log(f"Ping to {host} timed out")
            except Exception as e:
                error_count += 1
                latency_results[host] = {
                    'status': 'Failure',
                    'error': str(e)
                }
                self.log(f"Error pinging {host}: {e}")
        
        # Determine overall status
        if error_count == 0 and high_latency_count == 0:
            self.results['network_latency'] = {
                'status': 'Success',
                'message': "Network latency is acceptable to all hosts",
                'details': latency_results
            }
            self.log("Network latency check: Success")
            return True
        elif error_count == 0:
            self.results['network_latency'] = {
                'status': 'Warning',
                'message': f"High latency detected for {high_latency_count} hosts",
                'details': latency_results
            }
            self.log(f"Network latency check: Warning ({high_latency_count} high latency)")
            return True
        elif error_count < len(hosts):
            self.results['network_latency'] = {
                'status': 'Warning',
                'message': f"Failed to measure latency for {error_count} hosts",
                'details': latency_results
            }
            self.log(f"Network latency check: Warning ({error_count} errors)")
            return True
        else:
            self.results['network_latency'] = {
                'status': 'Failure',
                'message': "Failed to measure latency for all hosts",
                'details': latency_results
            }
            self.log("Network latency check: Failure")
            return False
    
    def check_proxy_settings(self):
        """Check proxy settings and connectivity"""
        self.log("Checking proxy settings...")
        
        # Get current environment proxy settings
        env_proxies = {
            'http': os.environ.get('HTTP_PROXY', os.environ.get('http_proxy', '')),
            'https': os.environ.get('HTTPS_PROXY', os.environ.get('https_proxy', '')),
            'no_proxy': os.environ.get('NO_PROXY', os.environ.get('no_proxy', ''))
        }
        
        # Check if proxies are configured in environment or config
        if any(self.proxy_settings.values()) or any(filter(None, env_proxies.values())):
            # Proxy is configured, check if it works
            proxy_url = self.proxy_settings.get('http', 
                        self.proxy_settings.get('https',
                        env_proxies.get('http', 
                        env_proxies.get('https', ''))))
            
            if not proxy_url:
                self.results['proxy_settings'] = {
                    'status': 'Warning',
                    'message': "Proxy settings are inconsistent or incomplete",
                    'details': {
                        'config_proxies': self.proxy_settings,
                        'env_proxies': env_proxies
                    }
                }
                self.log("Proxy settings check: Warning (inconsistent settings)")
                return True
                
            # Test proxy connectivity
            try:
                proxies = {'http': proxy_url, 'https': proxy_url}
                response = requests.get('https://www.google.com', proxies=proxies, timeout=5)
                
                if response.status_code == 200:
                    self.results['proxy_settings'] = {
                        'status': 'Success',
                        'message': f"Proxy is configured and working: {proxy_url}",
                        'details': {
                            'config_proxies': self.proxy_settings,
                            'env_proxies': env_proxies
                        }
                    }
                    self.log(f"Proxy settings check: Success (proxy working: {proxy_url})")
                    return True
                else:
                    self.results['proxy_settings'] = {
                        'status': 'Warning',
                        'message': f"Proxy returned unexpected status: HTTP {response.status_code}",
                        'details': {
                            'config_proxies': self.proxy_settings,
                            'env_proxies': env_proxies
                        }
                    }
                    self.log(f"Proxy settings check: Warning (HTTP {response.status_code})")
                    return False
            except Exception as e:
                self.results['proxy_settings'] = {
                    'status': 'Failure',
                    'message': f"Proxy is configured but not working: {str(e)}",
                    'details': {
                        'config_proxies': self.proxy_settings,
                        'env_proxies': env_proxies,
                        'error': str(e)
                    }
                }
                self.log(f"Proxy settings check: Failure ({str(e)})")
                return False
        else:
            # No proxy configured, this is fine
            self.results['proxy_settings'] = {
                'status': 'Success',
                'message': "No proxy is configured",
                'details': {
                    'config_proxies': self.proxy_settings,
                    'env_proxies': env_proxies
                }
            }
            self.log("Proxy settings check: Success (no proxy configured)")
            return True
    
    def run_all_checks(self):
        """Run all network diagnostic checks"""
        self.log("Starting network diagnostics...")
        start_time = time.time()
        
        # Run checks
        self.check_internet_connectivity()
        self.check_dns_resolution()
        self.check_api_endpoints()
        self.check_network_latency()
        self.check_proxy_settings()
        
        elapsed_time = time.time() - start_time
        self.log(f"Network diagnostics completed in {elapsed_time:.2f} seconds")
        return self.results
