"""
Model Manager - Handles all interactions with Ollama models
"""
import os
import json
import subprocess
import threading
import re
import time
from typing import Dict, List, Optional, Callable, Tuple

# Model status constants
MODEL_STATUS = {
    "NOT_INSTALLED": "Not Installed",
    "INSTALLING": "Installing...",
    "INSTALLED": "Installed",
    "LOADING": "Loading...",
    "RUNNING": "Running",
    "PROCESSING": "Processing...",
    "GENERATING": "Generating...",
    "UNINSTALLING": "Uninstalling...",
    "ERROR": "Error"
}

# Recommended models with metadata
RECOMMENDED_MODELS = {
    "deepseek-coder:6.7b": {"context": "4K", "note": "Great for code"},
    "starcoder2:7b": {"context": "16K", "note": "Strong coder model"},
    "mistral:instruct": {"context": "8K", "note": "Balanced assistant"},
    "zephyr:beta": {"context": "8K", "note": "Conversational chat"},
    "nous-hermes-llama2-13b": {"context": "4K", "note": "Deep thinker, needs 8-bit"},
    "codellama:13b-python": {"context": "4K–16K", "note": "Strong dev model (8-bit)"},
}

class ModelManager:
    """Manages Ollama models: installation, running, and status tracking"""
    
    def __init__(self, model_path: str, logger: Callable, use_8bit: bool = False):
        """
        Initialize the model manager
        
        Args:
            model_path: Path to store Ollama models
            logger: Logging function
            use_8bit: Whether to use 8-bit quantization
        """
        self.model_path = model_path
        self.log = logger
        self.use_8bit = use_8bit
        self.model_statuses = {}  # Track model status
        self.current_model = None
        self.model_process = None
        self.on_status_changed = None  # Callback for status changes
        
        # Initialize environment
        self._update_environment()
        
    def _update_environment(self) -> None:
        """Update environment variables for model path"""
        try:
            # Ensure the parent directory path is extracted correctly
            ollama_home = os.path.dirname(self.model_path)
            
            # Set environment variables
            os.environ["OLLAMA_HOME"] = ollama_home
            os.environ["OLLAMA_MODELS"] = self.model_path
            
            self.log(f"[Environment] OLLAMA_HOME={ollama_home}, OLLAMA_MODELS={self.model_path}")
        except Exception as e:
            self.log(f"[Error] Failed to update environment variables: {e}")
    
    def update_model_path(self, new_path: str) -> None:
        """
        Update the model path and environment variables
        
        Args:
            new_path: New path for model storage
        """
        if new_path != self.model_path:
            self.model_path = new_path
            self._update_environment()
            
    def set_callback(self, callback: Callable) -> None:
        """
        Set callback for status changes
        
        Args:
            callback: Function to call when model status changes
        """
        self.on_status_changed = callback
            
    def _update_model_status(self, model_name: str, status: str) -> None:
        """
        Update the status of a model
        
        Args:
            model_name: Name of the model
            status: New status string
        """
        try:
            # Update status
            self.model_statuses[model_name] = status
            
            # Call status change callback if set
            if self.on_status_changed and model_name == self.current_model:
                self.on_status_changed(model_name, status)
            
            # Log the status change
            self.log(f"[Model Status] {model_name}: {status}")
        except Exception as e:
            self.log(f"[Error] Failed to update model status: {e}")
            
    def detect_models(self) -> List[str]:
        """
        Detect installed models
        
        Returns:
            List of installed model names
        """
        self.log("[Checking] Looking for installed models...")
        available_models = []
        
        # Retry mechanism
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                # Call ollama list with proper environment
                env = os.environ.copy()
                result = subprocess.run(
                    ["ollama", "list"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10, 
                    env=env
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().splitlines():
                        if line and not line.startswith("NAME"):  # Skip header
                            parts = line.split()
                            if parts:
                                name = parts[0]
                                available_models.append(name)
                                # Mark this model as installed
                                self.model_statuses[name] = MODEL_STATUS["INSTALLED"]
                                
                    self.log(f"[Found] {len(available_models)} installed models")
                    success = True
                else:
                    error_msg = result.stderr.strip()
                    self.log(f"[Error] ollama list returned: {error_msg}")
                    
                    # Check if Ollama service is not running
                    if "connection refused" in error_msg.lower():
                        self.log("[Warning] Ollama service appears to be offline. Starting retry...")
                        time.sleep(2)  # Wait before retry
                    
                    retry_count += 1
            except Exception as e:
                self.log(f"[Model Check Error] {e}")
                retry_count += 1
                time.sleep(2)  # Wait before retry
        
        # Add recommended models to the status dict
        for model in RECOMMENDED_MODELS:
            if model not in self.model_statuses:
                self.model_statuses[model] = MODEL_STATUS["NOT_INSTALLED"]
        
        return available_models
    
    def fetch_available_models(self) -> List[Dict]:
        """
        Fetch available models from Ollama repository
        
        Returns:
            List of model dictionaries with metadata
        """
        self.log("[Fetching] Getting model list from Ollama repository...")
        models_list = []
        
        try:
            # First get locally installed models
            try:
                result = subprocess.run(
                    ["ollama", "list"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5,
                    env=os.environ.copy()
                )
                
                if result.returncode == 0:
                    # Skip header
                    for line in result.stdout.strip().splitlines()[1:]:
                        if line.strip():
                            parts = line.split()
                            if parts:
                                name = parts[0]
                                size = parts[1] if len(parts) > 1 else "Unknown"
                                models_list.append({
                                    "name": name,
                                    "size": size,
                                    "installed": True
                                })
                else:
                    self.log(f"[Error] ollama list command failed: {result.stderr}")
            except Exception as e:
                self.log(f"[Error] Failed to get installed models: {e}")
            
            # Check Ollama version to determine the correct command
            supports_all_flag = False
            version_text = "Unknown"  # Default value to prevent reference errors
            
            try:
                version_result = subprocess.run(
                    ["ollama", "version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if version_result.returncode == 0:
                    version_text = version_result.stdout.strip()
                    
                    # Check if version likely supports "--all" flag
                    if any(f"{i}." in version_text for i in range(0, 20)):
                        # Most versions should support 'list --all' or 'list remote'
                        supports_all_flag = True
                
                self.log(f"[Ollama Version] {version_text} (Supports --all: {supports_all_flag})")
            except Exception as e:
                self.log(f"[Warning] Could not determine Ollama version: {e}")
            
            # Try both commands in case one fails
            commands_to_try = [
                ["ollama", "list", "--all"],
                ["ollama", "list", "remote"]
            ]
            
            success = False
            
            for cmd in commands_to_try:
                if success:
                    break
                    
                try:
                    self.log(f"[Fetching] Trying: {' '.join(cmd)}")
                    repo_result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=10,
                        env=os.environ.copy()
                    )
                    
                    if repo_result.returncode == 0:
                        # Skip header
                        for line in repo_result.stdout.strip().splitlines()[1:]:
                            if line.strip():
                                parts = line.split()
                                if parts and len(parts) >= 2:
                                    name = parts[0]
                                    
                                    # Check if already in our list (installed)
                                    already_installed = any(m["name"] == name for m in models_list)
                                    
                                    if not already_installed:
                                        models_list.append({
                                            "name": name,
                                            "size": "Remote",
                                            "installed": False
                                        })
                        success = True
                    else:
                        self.log(f"[Warning] Command failed: {' '.join(cmd)}: {repo_result.stderr}")
                except Exception as e:
                    self.log(f"[Warning] Error with command {' '.join(cmd)}: {e}")
            
            if not success:
                self.log("[Warning] Could not fetch remote models with any command")
                    
            # Add recommended models if not in the list
            for model_name in RECOMMENDED_MODELS:
                if not any(m["name"] == model_name for m in models_list):
                    models_list.append({
                        "name": model_name,
                        "size": "Unknown",
                        "installed": False,
                        "recommended": True
                    })
            
            return models_list
            
        except Exception as e:
            self.log(f"[Error] Failed to fetch models: {e}")
            return []

    def install_model(self, model: str, progress_callback: Optional[Callable] = None) -> None:
        """
        Install a model
        
        Args:
            model: Name of the model to install
            progress_callback: Optional callback for installation progress
        """
        self.log(f"[Installing] Starting installation of {model}")
        
        # Update model status
        self._update_model_status(model, MODEL_STATUS["INSTALLING"])
        
        # Start a thread for installation
        threading.Thread(
            target=self._install_model_thread,
            args=(model, progress_callback),
            daemon=True
        ).start()
    
    def _install_model_thread(self, model: str, progress_callback: Optional[Callable]) -> None:
        """
        Handle model installation with robust error handling
        
        Args:
            model: Name of the model to install
            progress_callback: Optional callback for installation progress
        """
        try:
            # Use subprocess with universal_newlines=True and encoding set
            env = os.environ.copy()
            
            # Start process with explicit encoding
            process = subprocess.Popen(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env
            )
            
            # Process output with more robust error handling
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    # Update log safely
                    safe_line = line.strip().encode('ascii', 'replace').decode('ascii')
                    self.log(f"[Install] {safe_line}")
                    
                    # Check for progress 
                    if "%" in safe_line and progress_callback:
                        try:
                            percent_match = re.search(r'(\d+(\.\d+)?)%', safe_line)
                            if percent_match:
                                percent = float(percent_match.group(1))
                                progress_callback(percent)
                        except:
                            pass
            
            # Wait for completion
            return_code = process.wait()
            
            # Update status based on result
            if return_code == 0:
                self.log(f"[Installed] {model} successfully installed")
                self._update_model_status(model, MODEL_STATUS["INSTALLED"])
            else:
                self.log(f"[Error] Failed to install {model}")
                self._update_model_status(model, MODEL_STATUS["ERROR"])
            
        except Exception as e:
            self.log(f"[Error] Installation failed: {e}")
            self._update_model_status(model, MODEL_STATUS["ERROR"])
    
    def uninstall_model(self, model: str) -> None:
        """
        Uninstall a model
        
        Args:
            model: Name of the model to uninstall
        """
        self.log(f"[Uninstalling] Starting uninstallation of {model}")
        
        # Update model status
        self._update_model_status(model, MODEL_STATUS["UNINSTALLING"])
        
        # Start a thread for uninstallation
        threading.Thread(
            target=self._uninstall_model_thread,
            args=(model,),
            daemon=True
        ).start()
    
    def _uninstall_model_thread(self, model: str) -> None:
        """
        Handle model uninstallation in a separate thread
        
        Args:
            model: Name of the model to uninstall
        """
        try:
            # Use subprocess to run ollama rm
            env = os.environ.copy()
            
            # Run the command with real-time output
            process = subprocess.Popen(
                ["ollama", "rm", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            # Process output in real-time
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    # Update log
                    self.log(f"[Uninstall] {line.strip()}")
            
            # Wait for process to complete
            return_code = process.wait()
            
            # Update status based on result
            if return_code == 0:
                self.log(f"[Uninstalled] {model} successfully uninstalled")
                self._update_model_status(model, MODEL_STATUS["NOT_INSTALLED"])
            else:
                self.log(f"[Error] Failed to uninstall {model}")
                self._update_model_status(model, MODEL_STATUS["ERROR"])
            
        except Exception as e:
            self.log(f"[Error] Uninstallation failed: {e}")
            self._update_model_status(model, MODEL_STATUS["ERROR"])
            
    def verify_model_status(self, model_name: str) -> bool:
        """
        Verify if a model is installed
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model is installed, False otherwise
        """
        try:
            # Check if model exists in filesystem first
            model_path = os.path.join(self.model_path, model_name)
            if os.path.exists(model_path) and os.path.isdir(model_path):
                self._update_model_status(model_name, MODEL_STATUS["INSTALLED"])
                return True
            
            # If not in filesystem, try checking via ollama list
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                timeout=5,
                env=os.environ.copy()
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                for line in lines:
                    if model_name in line:
                        self._update_model_status(model_name, MODEL_STATUS["INSTALLED"])
                        return True
            
            # Model doesn't exist
            self._update_model_status(model_name, MODEL_STATUS["NOT_INSTALLED"])
            return False
            
        except Exception as e:
            self.log(f"[Error] Failed to verify model status: {e}")
            self._update_model_status(model_name, "Error checking")
            return False
            
    def start_model(self, model_name: str, callback: Optional[Callable] = None) -> bool:
        """
        Start running a model
        
        Args:
            model_name: Name of the model to start
            callback: Optional callback for model output
            
        Returns:
            True if model started successfully, False otherwise
        """
        # Check if a model is already running
        if self.model_process and self.model_process.poll() is None:
            self.log("[Warning] A model is already running. Please stop it first.")
            return False
        
        # Check if model is installed
        status = self.model_statuses.get(model_name, MODEL_STATUS["NOT_INSTALLED"])
        
        if status == MODEL_STATUS["NOT_INSTALLED"]:
            # Need to install model first
            self.log(f"[Error] Model {model_name} needs to be installed first.")
            return False
                
        # Update status
        self._update_model_status(model_name, MODEL_STATUS["LOADING"])
        self.current_model = model_name
        
        self.log(f"[Starting Model] {model_name}{' (8-bit mode)' if self.use_8bit else ''}")
        
        try:
            # Build the command
            cmd = ["ollama", "run", model_name]
            
            # Check if 8-bit mode is requested and handle it safely
            if self.use_8bit:
                # First check if Ollama version supports the --quantization flag
                try:
                    # Get Ollama version
                    version_result = subprocess.run(
                        ["ollama", "version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if version_result.returncode == 0:
                        version_text = version_result.stdout.strip()
                        self.log(f"[Ollama Version] {version_text}")
                        
                        # Check if version supports 8-bit quantization
                        if "0.1." in version_text or any(f"{i}." in version_text for i in range(1, 20)):
                            # Newer versions support this flag
                            cmd.append("--quantization=8bit")
                        else:
                            self.log("[Warning] 8-bit mode requested but your Ollama version may not support it.")
                            # Try with f16 instead as a fallback for some versions
                            cmd.append("--f16")
                    else:
                        self.log("[Warning] Could not determine Ollama version, skipping quantization flag")
                except Exception as e:
                    self.log(f"[Warning] Error checking Ollama version: {e}. Skipping quantization flag.")
            
            # Create a thread to handle model execution
            threading.Thread(
                target=self._run_model_process,
                args=(cmd, model_name, callback),
                daemon=True
            ).start()
            
            return True
        except Exception as e:
            self.log(f"[Error Starting Model] {e}")
            self._update_model_status(model_name, MODEL_STATUS["ERROR"])
            return False
            
    def _run_model_process(self, cmd: List[str], model_name: str, callback: Optional[Callable]) -> None:
        """
        Run the model process in a separate thread
        
        Args:
            cmd: Command to run
            model_name: Name of the model being run
            callback: Optional callback for model output and status changes
        """
        try:
            # Create a fresh environment copy
            env = os.environ.copy()
            
            # Start the process
            self.model_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            # Update status to show model is running
            self.log(f"[Started Model] {model_name}")
            self._update_model_status(model_name, MODEL_STATUS["RUNNING"])
            
            # Notify callback if provided
            if callback:
                callback("started", model_name)
            
            # Process output in real-time
            for line in iter(self.model_process.stdout.readline, ''):
                if line.strip():
                    # Log the output
                    self.log(line.strip())
                    
                    # Notify callback if provided
                    if callback:
                        callback("output", line.strip())
            
            # When the process exits
            self.log("[Model Stopped]")
            self._update_model_status(model_name, MODEL_STATUS["INSTALLED"])
            self.model_process = None
            
            # Notify callback if provided
            if callback:
                callback("stopped", model_name)
            
        except Exception as e:
            # Handle errors
            self.log(f"[Model Error] {e}")
            self._update_model_status(model_name, MODEL_STATUS["ERROR"])
            self.model_process = None
            
            # Notify callback if provided
            if callback:
                callback("error", str(e))
                
    def stop_model(self) -> bool:
        """
        Stop the running model process
        
        Returns:
            True if model stopped successfully, False otherwise
        """
        if not self.model_process or self.model_process.poll() is not None:
            self.log("[Warning] No model is currently running")
            return False
        
        model_name = self.current_model
        
        try:
            # Give the process a chance to close gracefully
            self.log("[Stopping Model] Sending termination signal...")
            self.model_process.terminate()
            
            # Update status
            self._update_model_status(model_name, MODEL_STATUS["INSTALLED"])
            
            # Wait for up to 5 seconds for clean shutdown
            start_time = time.time()
            while self.model_process.poll() is None and time.time() - start_time < 5:
                time.sleep(0.1)
            
            # If still running, force kill
            if self.model_process.poll() is None:
                self.log("[Stopping Model] Force killing process...")
                self.model_process.kill()
            
            self.model_process = None
            self.log(f"[Stopped Model] {model_name}")
            
            return True
            
        except Exception as e:
            self.log(f"[Error Stopping Model] {e}")
            return False
            
    def send_prompt(self, prompt: str, format_function: Callable, timeout: int = 60) -> Tuple[bool, str]:
        """
        Send a prompt to the running model
        
        Args:
            prompt: Prompt to send
            format_function: Function to format the prompt for the model
            timeout: Timeout in seconds
            
        Returns:
            Tuple containing success flag and response text
        """
        if not self.model_process or self.model_process.poll() is not None:
            self.log("[Error] Model is not running")
            return False, "Model is not running"
        
        # Update status to generating
        model_name = self.current_model
        self._update_model_status(model_name, MODEL_STATUS["GENERATING"])
        
        try:
            # Format the prompt
            formatted = format_function(prompt)
            
            # Format the input properly
            input_text = formatted + "\n"
            
            # Write to stdin and flush immediately
            self.model_process.stdin.write(input_text)
            self.model_process.stdin.flush()
            
            # Collect the response
            response = ""
            start_time = time.time()
            
            # Read from stdout with a timeout
            while time.time() - start_time < timeout:
                # Check if the process is still running
                if self.model_process.poll() is not None:
                    break
                
                # Read available output
                line = self.model_process.stdout.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                # Add to response and display in real-time
                cleaned_line = line.strip()
                if cleaned_line:
                    response += cleaned_line + "\n"
                    # Log the output
                    self.log(cleaned_line)
                
                # If we detect the model is waiting for the next input
                if "> " in line or "▌" in line:
                    break
            
            # Update status when done generating
            self._update_model_status(model_name, MODEL_STATUS["RUNNING"])
            
            # Return success and response
            return True, response.strip()
            
        except Exception as e:
            self.log(f"[Execution Error] {e}")
            self._update_model_status(model_name, MODEL_STATUS["ERROR"])
            return False, f"Error: {str(e)}"
    
    def get_system_info(self) -> Dict:
        """
        Get system information related to model usage
        
        Returns:
            Dictionary with system information
        """
        info = {
            "models_path": self.model_path,
            "path_exists": os.path.exists(self.model_path),
            "use_8bit": self.use_8bit,
            "installed_models": []
        }
        
        # Get installed models
        installed = [model for model, status in self.model_statuses.items() 
                   if status == MODEL_STATUS["INSTALLED"]]
        info["installed_models"] = installed
        info["installed_count"] = len(installed)
        
        # Get drive free space
        try:
            drive = os.path.splitdrive(self.model_path)[0] + "\\"
            if not drive:
                drive = "C:\\"  # Default to C: if no drive letter found
                
            import shutil
            usage = shutil.disk_usage(drive)
            info["drive"] = drive
            info["free_space_gb"] = round(usage.free / (1024**3), 2)  # Convert to GB
        except Exception as e:
            self.log(f"[Error] Could not check disk space: {e}")
            info["free_space_gb"] = -1
        
        return info