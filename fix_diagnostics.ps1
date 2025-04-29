# Fix IrintAI Assistant Diagnostic System
# This script addresses issues in the diagnostics module

Write-Host "===== IrintAI Assistant Diagnostic System Fix =====" -ForegroundColor Cyan
Write-Host "This script will fix issues in the diagnostics module" -ForegroundColor Cyan

# Check if folder exists
if (-not (Test-Path ".\plugins\ollama_hub\core")) {
    Write-Host "Creating missing directory structure for ollama_hub plugin..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path ".\plugins\ollama_hub\core" -Force | Out-Null
}

# Fix plugin initialization
Write-Host "Ensuring proper plugin initialization files exist..." -ForegroundColor Green

# Create __init__.py files if they don't exist
if (-not (Test-Path ".\plugins\__init__.py")) {
    "" | Set-Content ".\plugins\__init__.py"
    Write-Host "Created .\plugins\__init__.py" -ForegroundColor Green
}

if (-not (Test-Path ".\plugins\ollama_hub\__init__.py")) {
    $initContent = @"
"""
Ollama Hub Plugin for IrintAI Assistant
Enables integration with Ollama API for local LLM functionality.
"""
import os
import sys
import importlib.util
import threading
from typing import Dict, Any, List, Optional, Tuple

# Import ollama client
from plugins.ollama_hub.core.ollama_client import OllamaClient

class OllamaHubPlugin:
    """Plugin for integrating with Ollama API"""
    
    def __init__(self, config=None):
        """Initialize the plugin with configuration"""
        self.name = "ollama_hub"
        self.config = config or {}
        self.ollama_client = OllamaClient(logger=print)
    
    def initialize(self):
        """Initialize the plugin"""
        print("Initializing Ollama Hub Plugin")
        return True
    
    def get_ollama_client(self):
        """Get the Ollama client instance"""
        return self.ollama_client
"@
    $initContent | Set-Content ".\plugins\ollama_hub\__init__.py"
    Write-Host "Created .\plugins\ollama_hub\__init__.py" -ForegroundColor Green
}

if (-not (Test-Path ".\plugins\ollama_hub\core\__init__.py")) {
    "" | Set-Content ".\plugins\ollama_hub\core\__init__.py"
    Write-Host "Created .\plugins\ollama_hub\core\__init__.py" -ForegroundColor Green
}

# Check if ollama_client.py exists, if not create it
if (-not (Test-Path ".\plugins\ollama_hub\core\ollama_client.py")) {
    Write-Host "Creating ollama_client.py..." -ForegroundColor Yellow
    $ollamaClientContent = @"
"""
Ollama Client - Direct interface to Ollama API
"""
import os
import sys
import json
import requests
import subprocess
import re  # For stripping ANSI escape codes
from typing import Dict, Any, Tuple, Optional, Callable, List

class OllamaClient:
    """Provides direct access to Ollama API for generating text responses"""
    
    def __init__(self, base_url: str = "http://localhost:11434", logger: Optional[Callable] = None):
        """
        Initialize the Ollama client
        
        Args:
            base_url: Base URL for Ollama API
            logger: Optional logging function
        """
        self.base_url = base_url
        self.log = logger or print
        
    def generate(self, model: str, prompt: str, params: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Generate a response using Ollama API
        
        Args:
            model: Model name
            prompt: The prompt to send
            params: Optional parameters for generation
            
        Returns:
            Tuple of (success, response)
        """
        try:
            # First try the API approach
            try:
                url = f"{self.base_url}/api/generate"
                
                # Prepare request data
                data = {
                    "model": model,
                    "prompt": prompt
                }
                
                if params:
                    for key, value in params.items():
                        # Only include supported parameters
                        if key in ["temperature", "top_p", "top_k", "repeat_penalty", "seed", "num_predict"]:
                            data[key] = value
                
                self.log(f"[API] Sending request to {url} for model {model}")
                
                # Send request
                response = requests.post(url, json=data, timeout=60)
                
                if response.status_code == 200:
                    try:
                        # Parse the response - it's JSONL format
                        result = ""
                        for line in response.text.strip().split('\n'):
                            data = json.loads(line)
                            if "response" in data:
                                result += data["response"]
                        
                        return True, result
                    except Exception as e:
                        self.log(f"[API] Error parsing response: {e}")
                        # Fall back to command-line approach
                        raise Exception("Fallback to command-line")
                else:
                    self.log(f"[API] Request failed with status code {response.status_code}")
                    # Fall back to command-line approach
                    raise Exception("Fallback to command-line")
            
            except Exception as api_error:
                # Fall back to command-line approach
                self.log(f"[API] Error using API approach: {api_error}. Falling back to command-line.")
                
                # Build command
                cmd = ["ollama", "run", model]
                # Add any parameters
                if params:
                    for key, value in params.items():
                        if key in ["temperature", "top_p", "top_k", "repeat_penalty", "context", "seed"]:
                            cmd.extend([f"--{key}", str(value)])
                # Append the prompt as positional argument
                cmd.append(prompt)
                self.log(f"[Run] Running command: {' '.join(cmd)}")
                # Execute command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env=os.environ.copy()
                )
                
                if result.returncode == 0:
                    # Strip ANSI escape codes from output
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    clean_output = ansi_escape.sub('', result.stdout)
                    return True, clean_output.strip()
                else:
                    self.log(f"[Run] Command failed with exit code {result.returncode}")
                    self.log(f"[Run] Error output: {result.stderr}")
                    return False, result.stderr
                
        except Exception as e:
            self.log(f"[Generate] Error: {e}")
            return False, str(e)
    
    def list_models(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        List available models using Ollama API
        
        Returns:
            Tuple of (success, model_list)
        """
        try:
            url = f"{self.base_url}/api/tags"
            self.log(f"[API] Sending request to {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return True, data.get("models", [])
            else:
                self.log(f"[API] Request failed with status code {response.status_code}")
                return False, []
                
        except Exception as e:
            self.log(f"[ListModels] Error: {e}")
            try:
                # Fallback to command line
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    env=os.environ.copy()
                )
                
                if result.returncode == 0:
                    # Parse the output to match API format
                    lines = result.stdout.strip().split('\n')
                    models = []
                    
                    # Skip header row
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 4:
                                model_name = parts[0]
                                size = parts[-2]
                                models.append({
                                    "name": model_name,
                                    "size": size
                                })
                    
                    return True, models
                else:
                    self.log(f"[Run] Command failed with exit code {result.returncode}")
                    return False, []
            except Exception as cmd_error:
                self.log(f"[ListModels] Command-line fallback error: {cmd_error}")
                return False, []
    
    def pull_model(self, model: str) -> Tuple[bool, str]:
        """
        Pull a model from Ollama
        
        Args:
            model: The model name to pull
            
        Returns:
            Tuple of (success, message)
        """
        try:
            url = f"{self.base_url}/api/pull"
            self.log(f"[API] Pulling model {model} via API")
            
            # Prepare request data
            data = {
                "name": model
            }
            
            # Make request but with a very long timeout
            # This is an async operation so we'll get a response quickly
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code in [200, 202]:
                return True, f"Started pulling model {model}"
            else:
                self.log(f"[API] Pull request failed with status code {response.status_code}")
                # Fall back to command-line approach
                raise Exception("Fallback to command-line")
                
        except Exception as e:
            self.log(f"[Pull] API error, trying command line: {e}")
            try:
                # Execute pull command
                self.log(f"[Run] Running command: ollama pull {model}")
                result = subprocess.run(
                    ["ollama", "pull", model],
                    capture_output=True,
                    text=True,
                    env=os.environ.copy()
                )
                
                if result.returncode == 0:
                    return True, f"Successfully pulled model {model}"
                else:
                    self.log(f"[Run] Command failed with exit code {result.returncode}")
                    self.log(f"[Run] Error output: {result.stderr}")
                    return False, result.stderr
            except Exception as cmd_error:
                self.log(f"[Pull] Command-line error: {cmd_error}")
                return False, str(cmd_error)
"@
    $ollamaClientContent | Set-Content ".\plugins\ollama_hub\core\ollama_client.py"
    Write-Host "Created ollama_client.py with improved error handling and API support" -ForegroundColor Green
}

# Fix Ollama panel diagnostic
Write-Host "Fixing Ollama panel diagnostic..." -ForegroundColor Green
$ollamaDiagContent = @"
"""
Ollama Panel Diagnostic for IrintAI Assistant
"""
import requests
import json
import sys
import os
import subprocess
from urllib.parse import urlparse
from typing import Dict, Any, Optional, List

# Add project root to sys.path to allow importing core modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from plugins.ollama_hub.core.ollama_client import OllamaClient
    from core.config_manager import ConfigManager
    from utils.logger import IrintaiLogger
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Please ensure the script is run from the project root.")
    sys.exit(1)

# Setup logger for diagnostics
logger = IrintaiLogger('ollama_diagnostic', 'ollama_diagnostic.log')

class OllamaPanelDiagnostic:
    """Diagnostic tool for Ollama integration"""
    
    def __init__(self, config_path='data/config.json'):
        """Initialize the Ollama panel diagnostic tool"""
        self.config_manager = ConfigManager(config_path)
        
        # Get Ollama URL from config, first try ollama.url, then ollama_url
        ollama_config = self.config_manager.get("ollama", {})
        self.ollama_url = ollama_config.get("url", self.config_manager.get("ollama_url", "http://localhost:11434"))
        
        self.results = {}
        
        # Initialize the Ollama client
        self.ollama_client = OllamaClient(base_url=self.ollama_url, logger=self.log)
    
    def log(self, message):
        """Simple print-based logging for diagnostics"""
        print(f"[OLLAMA DIAG] {message}")
        logger.info(message)
    
    def check_ollama_server_connection(self):
        """Check if the Ollama server is reachable"""
        self.log(f"Checking Ollama server connection at: {self.ollama_url}")
        
        try:
            # Try to connect to the Ollama server
            response = requests.get(f"{self.ollama_url}/api/version", timeout=5)
            
            if response.status_code == 200:
                version_info = response.json()
                self.results['server_connection'] = {
                    'status': 'Success',
                    'message': f"Connected to Ollama server at {self.ollama_url}, version: {version_info.get('version', 'unknown')}"
                }
                self.log("Ollama server connection successful")
                return True
            else:
                self.results['server_connection'] = {
                    'status': 'Failure',
                    'message': f"Connected to {self.ollama_url}, but got unexpected response: {response.status_code}"
                }
                self.log(f"Ollama server connection failed: Status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            # Try direct connection to root endpoint
            try:
                response = requests.get(f"{self.ollama_url}/", timeout=5)
                if response.status_code == 200 and "Ollama is running" in response.text:
                    self.results['server_connection'] = {
                        'status': 'Success',
                        'message': f"Connected to Ollama server at {self.ollama_url}"
                    }
                    self.log("Ollama server connection successful through root endpoint")
                    return True
                else:
                    self.results['server_connection'] = {
                        'status': 'Failure',
                        'message': f"Connected to {self.ollama_url}, but it doesn't appear to be an Ollama server"
                    }
                    self.log(f"Ollama server connection failed: Not an Ollama server")
                    return False
            except Exception as e:
                self.results['server_connection'] = {
                    'status': 'Failure',
                    'message': f"Failed to connect to Ollama server at {self.ollama_url}: {str(e)}"
                }
                self.log(f"Ollama server connection failed: {str(e)}")
                return False
        except Exception as e:
            self.results['server_connection'] = {
                'status': 'Failure',
                'message': f"Failed to connect to Ollama server at {self.ollama_url}: {str(e)}"
            }
            self.log(f"Ollama server connection failed: {str(e)}")
            return False
    
    def check_ollama_installation(self):
        """Check if Ollama is installed"""
        self.log("Checking Ollama installation")
        
        try:
            # Try multiple version command formats
            for cmd in [["ollama", "version"], ["ollama", "--version"], ["ollama", "-v"]]:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        self.results['ollama_installation'] = {
                            'status': 'Success',
                            'message': f"Ollama is installed: {version}"
                        }
                        self.log(f"Ollama is installed: {version}")
                        return True
                except:
                    continue
            
            # If we got here, none of the commands worked, but let's check if the server responds
            # even if the CLI isn't accessible
            if self.check_ollama_server_connection():
                self.results['ollama_installation'] = {
                    'status': 'Success',
                    'message': "Ollama is running but CLI command not found"
                }
                self.log("Ollama is running but CLI command not found")
                return True
            else:
                self.results['ollama_installation'] = {
                    'status': 'Failure',
                    'message': "Ollama is not installed or not in PATH"
                }
                self.log("Ollama is not installed or not in PATH")
                return False
                
        except Exception as e:
            self.results['ollama_installation'] = {
                'status': 'Failure',
                'message': f"Error checking Ollama installation: {str(e)}"
            }
            self.log(f"Error checking Ollama installation: {str(e)}")
            return False
    
    def list_local_models(self):
        """List locally available Ollama models"""
        self.log("Listing local Ollama models")
        
        success, models = self.ollama_client.list_models()
        
        if success:
            model_names = [model.get('name') for model in models]
            self.results['list_local_models'] = {
                'status': 'Success',
                'message': f"Found {len(models)} local models: {', '.join(model_names)}"
            }
            self.log(f"Found {len(models)} local models")
            return True
        else:
            self.results['list_local_models'] = {
                'status': 'Warning',
                'message': "Failed to list local models. Make sure Ollama is running."
            }
            self.log("Failed to list local models")
            return False
    
    def pull_model(self, model_name="phi3:mini"):
        """Pull a model from Ollama"""
        self.log(f"Pulling model: {model_name}")
        
        # First, let's check if the model is already available
        success, models = self.ollama_client.list_models()
        
        if success:
            for model in models:
                if model.get('name') == model_name:
                    self.results['pull_model'] = {
                        'status': 'Success',
                        'message': f"Model {model_name} is already available locally"
                    }
                    self.log(f"Model {model_name} is already available locally")
                    return True
        
        # If not, try to pull it
        success, message = self.ollama_client.pull_model(model_name)
        
        if success:
            self.results['pull_model'] = {
                'status': 'Success',
                'message': f"Started pulling model {model_name}"
            }
            self.log(f"Started pulling model {model_name}")
            return True
        else:
            self.results['pull_model'] = {
                'status': 'Warning',
                'message': f"Failed to pull model {model_name}: {message}"
            }
            self.log(f"Failed to pull model {model_name}: {message}")
            return False
    
    def run_all_checks(self):
        """Run all Ollama diagnostic checks"""
        self.log("Starting Ollama diagnostics...")
        
        # Check Ollama server connection
        self.check_ollama_server_connection()
        
        # Check Ollama installation
        self.check_ollama_installation()
        
        # If previous checks passed, try listing and pulling models
        if (self.results.get('server_connection', {}).get('status') == 'Success' or
            self.results.get('ollama_installation', {}).get('status') == 'Success'):
            self.list_local_models()
            
            # Only try pulling a model if local model listing was successful
            if self.results.get('list_local_models', {}).get('status') == 'Success':
                # Get default model from config
                default_model = self.config_manager.get('default_model', 'phi3:mini')
                self.pull_model(default_model)
        
        # Return results
        return self.results
"@
$ollamaDiagContent | Set-Content ".\diagnostics\ollama_panel_diagnostic.py"
Write-Host "Fixed ollama_panel_diagnostic.py with improved error handling" -ForegroundColor Green

# Create a master fix and verify script
$fixAndVerify = @"
@echo off
echo =================================
echo IrintAI Assistant Fix and Verify
echo =================================
echo.
echo Running diagnostic fixer...
echo.
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File fix_diagnostics.ps1
echo.
echo Starting Ollama server if not running...
call start_ollama.bat
echo.
echo Running diagnostics to verify fixes...
python diagnostics\diagnostic_suite.py
echo.
echo All fixes complete. Press any key to exit...
pause > nul
"@
$fixAndVerify | Set-Content ".\fix_and_verify.bat"
Write-Host "Created fix_and_verify.bat script" -ForegroundColor Green

Write-Host "All diagnostic fixes applied successfully!" -ForegroundColor Green
Write-Host "Run fix_and_verify.bat to verify the fixes" -ForegroundColor Green
