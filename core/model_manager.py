"""
Model Manager - Handles all interactions with Ollama models
"""
import os
import json
import subprocess
import threading
import re
import time
from typing import Dict, List, Optional, Callable, Tuple, Any
import shutil   # Add this if not already imported

# ------------------------------------------------------------------------------
# At module top you should have something like:
#
# RECOMMENDED_MODELS = {
#     "llama2": { "context": "4K" },
#     "gpt4all": { "context": "8K" },
#     ...
# }
# MODEL_STATUS = {
#     "INSTALLED": "installed",
#     "NOT_INSTALLED": "not_installed",
#     "OUT_OF_DATE": "out_of_date"
# }
# ------------------------------------------------------------------------------

# Regular expression to match ANSI escape sequences
ANSI_ESCAPE_PATTERN = re.compile(r'(\x1B\[[0-?]*[ -/]*[@-~]|\x1B[@-_]|[\x00-\x08\x0B-\x1F\x7F])')

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
    
    def __init__(self, model_path: str, logger: Callable, use_8bit: bool = False, config=None):
        """
        Initialize the model manager
        
        Args:
            model_path: Path to store Ollama models
            logger: Logging function
            use_8bit: Whether to use 8-bit quantization
            config: Optional configuration manager
        """        
        self.model_path = model_path
        self.log = logger
        self.use_8bit = use_8bit
        self.config = config
        self.model_statuses = {}  # Track model status
        self.current_model = None
        self.model_process = None
        self.on_status_changed = None  # Callback for status changes
        self.current_parameters = {}  # Store current model parameters
        # Default context size (can be overridden by config)
        self.context_size = config.get("model.context_size", 4096) if config else 4096
        
        # Initialize environment
        self._update_environment()
        # Populate available models dynamically
        self.available_models = [{'name': model} for model in self.detect_models()]
        
    def _strip_ansi_codes(self, text: str) -> str:
        """
        Remove ANSI escape sequences from text
        
        Args:
            text: Input text that may contain ANSI escape sequences
            
        Returns:
            Clean text with escape sequences removed
        """
        if not text:
            return ""
        return ANSI_ESCAPE_PATTERN.sub('', text)
        
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
        # Early exit if Ollama is not installed or not in PATH
        if shutil.which("ollama") is None:
            self.log("[Error] Ollama executable not found. Please install Ollama and ensure it is in your PATH.")
            # Mark all recommended models as not installed
            for model in RECOMMENDED_MODELS:
                self.model_statuses[model] = MODEL_STATUS["NOT_INSTALLED"]
            return []

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
                    encoding='utf-8',
                    errors='replace',
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
        Fetch remote model list from Ollama
        Returns:
            List of model dicts with metadata
        """
        self.log("[Fetching] Getting model list from Ollama repository...")
        # Initialize list to collect models
        models_list: List[Dict] = []
        # Early exit if Ollama is not installed or not in PATH
        if shutil.which("ollama") is None:
            self.log("[Error] Ollama executable not found. Please install Ollama and ensure it is in your PATH.")
            # Return only recommended models
            for name, meta in RECOMMENDED_MODELS.items():
                models_list.append({
                    "name": name,
                    "size": meta.get("context", "Unknown"),
                    "installed": False,
                    "recommended": True
                })
            return models_list

        try:
            # First get locally installed models
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
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
              # Try to get Ollama version using "--version" flag (for Ollama 0.6.5+)
            supports_all_flag = False
            version_text = "0.6.5"  # Default to your known version
            
            try:
                # First try the newer "--version" flag (Ollama 0.6.5+)
                version_result = subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=5
                )
                
                if version_result.returncode == 0 and version_result.stdout.strip():
                    version_text = version_result.stdout.strip()
                    self.log(f"[Ollama Version] {version_text} (using --version flag)")
                    supports_all_flag = True
                else:
                    # Fall back to "version" command (some versions)
                    version_result = subprocess.run(
                        ["ollama", "version"],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=5
                    )
                    
                    if version_result.returncode == 0:
                        version_text = version_result.stdout.strip()
                        self.log(f"[Ollama Version] {version_text} (using version command)")
                        supports_all_flag = True
                    else:
                        self.log(f"[Ollama Version] Assuming version 0.6.5 (version check failed)")
            except Exception as e:
                self.log(f"[Warning] Could not determine Ollama version: {e}")
            
            # Use commands appropriate for Ollama 0.6.5+
            commands_to_try = [
                ["ollama", "list", "remote"]  # This works in 0.6.5
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
                        encoding='utf-8',
                        errors='replace',
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
    
# Define a proper send_prompt implementation
    def send_prompt(self, prompt: str, formatter: Callable = None) -> Tuple[bool, str]:
        """
        Send a prompt to the model and get a response
        Compatible with Ollama 0.6.5
        
        Args:
            prompt: The prompt to send to the model
            formatter: Optional function to format the prompt
            
        Returns:
            Tuple of (success, response)
        """
        try:
            # Check if we have a current model and if it's running
            if not self.current_model:
                self.log("[Error] No model is selected")
                return False, "No model is selected. Please start a model first."
            
            if not self.model_process or self.model_process.poll() is not None:
                self.log("[Error] Model is not running")
                return False, "Model is not running. Please start a model first."
            
            # Format prompt if formatter is provided
            formatted_prompt = formatter(prompt) if formatter else prompt
            
            # Update status
            self._update_model_status(self.current_model, "Generating...")
            
            # Log that we're sending the prompt
            self.log(f"[Prompt] Sending prompt to model ({len(formatted_prompt)} chars)")
            
            # This is the key fix: communicate directly with the running model process
            try:
                # Write prompt to stdin and flush
                self.model_process.stdin.write(formatted_prompt + "\n")
                self.model_process.stdin.flush()
                
                # Capture response - Ollama will output the response followed by a prompt marker
                response = ""
                waiting_for_response = True
                timeout = time.time() + 60  # 60 second timeout
                
                # Read output until we get a response
                while waiting_for_response and time.time() < timeout:
                    # Check if process is still alive
                    if self.model_process.poll() is not None:
                        self.log("[Error] Model process terminated while generating response")
                        return False, "Model process terminated unexpectedly"
                        
                    # Try to read a line of output
                    line = self.model_process.stdout.readline()
                    if not line:  # No output available yet
                        time.sleep(0.1)
                        continue
                        
                    line = line.strip()
                    if not line:  # Empty line
                        continue
                        
                    # If the line contains the prompt marker, we're done
                    if ">" in line or "▌" in line:
                        waiting_for_response = False
                        break
                        
                    # Otherwise, add the line to our response
                    response += line + "\n"
                    
                # Check for timeout
                if waiting_for_response:
                    self.log("[Error] Timed out waiting for response")
                    return False, "Timed out waiting for model response"
                    
                # Update status back to running
                self._update_model_status(self.current_model, "Running")
                
                # Log success
                self.log(f"[Generate] Successfully received response ({len(response)} chars)")
                
                return True, response.strip()
                
            except BrokenPipeError:
                self.log("[Error] Connection to model lost (broken pipe)")
                return False, "Connection to model process lost. Please restart the model."
                
        except Exception as e:
            self.log(f"[Error] Failed to generate response: {e}")
            return False, f"Error: {str(e)}"
    
    def _uninstall_model_thread(self, model: str) -> None:
        """
        Handle model uninstallation in a separate thread
        
        Args:
            model: Name of the model to uninstall
        """
        try:
            # Use subprocess to run ollama rm
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            threading.Thread(
            target=self._uninstall_model_thread,
            args=(model,),
            daemon=True).start()
            
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
                encoding='utf-8',
                errors='replace',
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
            
    def start_model(self, model_name: str, callback: Optional[Callable] = None, model_config: Optional[dict] = None) -> bool:
        """
        Start running a model

        Args:
            model_name: Name of the model to start
            callback: Optional callback for model output
            model_config: Optional configuration for the model

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
              # Apply model-specific configurations if provided
            if model_config:
                # Check for valid Ollama run parameters and filter out any invalid ones
                valid_ollama_params = ["temperature", "context", "threads", "gpu", "seed"]
                
                # First log all parameters for debugging
                self.log(f"[Model Config] Received parameters: {list(model_config.keys())}")
                
                # Only use parameters that are valid for Ollama command line
                for key, value in model_config.items():
                    if key in valid_ollama_params:
                        # Add valid parameter to command
                        cmd.extend([f"--{key}", str(value)])
                        self.log(f"[Model Config] Using parameter: {key}={value}")
                    else:
                        self.log(f"[Warning] Skipping unsupported Ollama parameter: {key}")

            # Check if 8-bit mode is requested and handle it safely
            if self.use_8bit:
                # First check if Ollama version supports the --quantization flag
                try:
                    # Get Ollama version
                    version_result = subprocess.run(
                        ["ollama", "version"],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
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
                    self.log(f"[Error] Failed to check quantization support: {e}")

            # Create a thread to handle model execution
            threading.Thread(
                target=self._run_model_process,
                args=(cmd, model_name, callback),
                daemon=True
            ).start()
            
            return True
        except Exception as e:
            self.log(f"[Error] Failed to start model {model_name}: {e}")
            self._update_model_status(model_name, "Error starting")
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
            # Keep a local reference to avoid NoneType errors if model_process is cleared by another thread
            local_process = self.model_process
            
            try:                
                for line in iter(local_process.stdout.readline, ''):
                    # Check if the process was terminated
                    if local_process.poll() is not None:
                        self.log("[Info] Process terminated while reading output")
                        break
                        
                    if line.strip():
                        # Clean ANSI escape sequences from output
                        clean_line = self._strip_ansi_codes(line.strip())
                        
                        # Log the clean output
                        self.log(clean_line)
                        
                        # Notify callback if provided
                        if callback:
                            callback("output", clean_line)
            except Exception as read_error:
                self.log(f"[Warning] Error while reading process output: {read_error}")
            
            # Check if the process exited unexpectedly (exit code != 0)
            exit_code = local_process.poll()
            if exit_code is not None and exit_code != 0:
                self.log(f"[Warning] Model process exited unexpectedly with code {exit_code}. Attempting restart.")
            
            # Clear the current process reference
            self.model_process = None
            
            # Attempt to restart up to 3 times
            for attempt in range(1, 4):
                self.log(f"[Auto-Recovery] Attempt {attempt} to restart model {model_name}")
                time.sleep(2)  # Give some time before restarting
                
                try:
                    # Create a new process
                    self.model_process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        env=env
                    )
                    
                    # Update status
                    self._update_model_status(model_name, MODEL_STATUS["RUNNING"])
                    
                    if callback:
                        callback("restarted", model_name)
                        
                    # Process output from the restarted model
                    for line in iter(self.model_process.stdout.readline, ''):
                        if line.strip():
                            # Log the output
                            self.log(line.strip())
                            
                            # Notify callback if provided
                            if callback:
                                callback("output", line.strip())
                                
                    # If we get here, the model has stopped again
                    break
                    
                except Exception as restart_error:
                    self.log(f"[Error] Restart attempt {attempt} failed: {restart_error}")
                    
                    if attempt == 3:
                        self.log("[Error] Maximum restart attempts reached. Model service appears unstable.")
                        # Update the status to error after all attempts fail
                        self._update_model_status(model_name, MODEL_STATUS["ERROR"])
                        
                        # Notify callback if provided
                        if callback:
                            callback("error", "Model service appears unstable after multiple restart attempts")
            else:
                # Normal exit scenario
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
        # First check if there's any model running
        if not self.model_process:
            self.log("[Warning] No model is currently running")
            return False
            
        # Store local references to avoid race conditions
        model_process = self.model_process
        current_model = self.current_model
        
        # Clear the reference immediately to prevent double-stop attempts
        self.model_process = None
        
        try:
            # Check if process is still running
            if model_process.poll() is not None:
                self.log("[Warning] Model process has already exited")
                if current_model:
                    self._update_model_status(current_model, MODEL_STATUS["INSTALLED"])
                return True
            
            # Give the process a chance to close gracefully
            self.log("[Stopping Model] Sending termination signal...")
            model_process.terminate()
            
            # Update status
            if current_model:
                self._update_model_status(current_model, MODEL_STATUS["INSTALLED"])
            
            # Wait for up to 5 seconds for clean shutdown
            start_time = time.time()
            while model_process.poll() is None and time.time() - start_time < 5:
                time.sleep(0.1)
            
            # If still running, force kill
            if model_process.poll() is None:
                self.log("[Stopping Model] Force killing process...")
                try:
                    model_process.kill()
                except Exception as kill_error:
                    self.log(f"[Warning] Error during force kill: {kill_error}")
                    
            if current_model:
                self.log(f"[Stopped Model] {current_model}")
            else:
                self.log("[Stopped Model] Unknown model")
                
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
            if self.model_process is not None:
                exit_code = self.model_process.poll()
                self.log(f"[Warning] Model process exited with code {exit_code} before sending prompt")
            else:
                self.log("[Warning] Model is not running. Please start a model first.")
            # Notify caller to start the model
            return False, "Model is not running. Please start a model first."
        
        # Update status to generating
        model_name = self.current_model
        self._update_model_status(model_name, MODEL_STATUS["GENERATING"])
        
        try:
            # Format the prompt
            formatted = format_function(prompt)
            
            # Format the input properly
            input_text = formatted + "\n"
            
            # Log start of interaction
            self.log(f"[Prompt] Sending prompt to {model_name} (length: {len(input_text)})")
            
            # Write to stdin and flush immediately
            self.model_process.stdin.write(input_text)
            self.model_process.stdin.flush()
            
            # Check if process is still alive after sending prompt
            if self.model_process.poll() is not None:
                exit_code = self.model_process.poll()
                self.log(f"[Warning] Model process terminated with code {exit_code} right after sending prompt")
                return False, f"Model process terminated (exit code: {exit_code})"
            
            # Collect the response
            response = ""
            start_time = time.time()
            
            # Read from stdout with a timeout
            while time.time() - start_time < timeout:
                # Check if the process is still running
                if self.model_process.poll() is not None:
                    exit_code = self.model_process.poll()
                    self.log(f"[Warning] Model process terminated with code {exit_code} during response generation")
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
                    self.log("[Prompt] Detected model completion marker")
                    break
            
            # Check for timeout
            if time.time() - start_time >= timeout:
                self.log(f"[Warning] Response generation timed out after {timeout} seconds")
                
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
    
    def get_current_model_format(self) -> str:
        """
        Get the format of the currently running model
        
        Returns:
            String identifier of the model format (chatml, llama, etc.)
        """
        if not self.current_model:
            return "default"
            
        # Check model name to guess format
        model_name = self.current_model.lower()
        
        # Determine format based on model name
        if any(name in model_name for name in ["gpt", "claude", "chatgpt", "deepseek"]):
            return "chatml"
        elif any(name in model_name for name in ["llama", "mistral", "mixtral", "alpaca"]):
            return "llama"
        elif any(name in model_name for name in ["starcoder", "codellama"]):
            return "coder"
        
        # Default to a simple format for other models
        return "default"

    def get_model_details(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary of model details
        """
        details = {
            "name": model_name,
            "status": self.model_statuses.get(model_name, MODEL_STATUS["NOT_INSTALLED"]),
            "is_current": model_name == self.current_model,
        }
        
        # Add recommended model info if available
        if model_name in RECOMMENDED_MODELS:
            details.update(RECOMMENDED_MODELS[model_name])
        
        # Try to get model size from filesystem
        try:
            model_dir = os.path.join(self.model_path, model_name)
            if os.path.exists(model_dir):
                # Calculate directory size
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(model_dir):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp)
                
                # Convert to GB
                details["size_gb"] = round(total_size / (1024**3), 2)
        except Exception as e:
            self.log(f"[Warning] Could not get model size: {e}")
        
        return details

    def get_model_parameters(self, model_name: str) -> Dict[str, Any]:
        """
        Get available parameters for a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary of parameters
        """
        params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
        }
        
        # Adjust default parameters based on model type
        if "code" in model_name.lower() or "coder" in model_name.lower():
            # Better defaults for code generation
            params["temperature"] = 0.3
            params["repeat_penalty"] = 1.2
        elif any(creative in model_name.lower() for creative in ["creative", "novel", "story"]):
            # More creative defaults
            params["temperature"] = 0.9
            params["top_p"] = 0.95
        
        return params

    def set_model_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Set parameters for the current model
        
        Args:
            params: Dictionary of parameter key-value pairs
            
        Returns:
            True if parameters were set successfully, False otherwise
        """
        if not self.current_model:
            self.log("[Error] No model is currently running")
            return False
        
        try:
            # Log the parameter update
            valid_params = {}
            for key, value in params.items():
                # Validate parameter values
                if key == "temperature":
                    valid_params[key] = max(0.0, min(2.0, float(value)))
                elif key in ["top_p", "top_k", "repeat_penalty"]:
                    valid_params[key] = max(0.0, float(value))
                else:
                    # Skip unknown parameters
                    self.log(f"[Warning] Unknown parameter: {key}")
                    continue
                    
                self.log(f"[Parameters] {key} = {valid_params[key]}")
            
            # Store parameters for future reference
            self.current_parameters = valid_params
            return True
        except Exception as e:
            self.log(f"[Error] Failed to set parameters: {e}")
            return False

    def export_model_config(self, path: str) -> bool:
        """
        Export model configurations to a file
        
        Args:
            path: Path to save configuration file
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            # Collect configuration data
            config = {
                "model_path": self.model_path,
                "use_8bit": self.use_8bit,
                "current_model": self.current_model,
                "models": {},
            }
            
            # Add information about each known model
            for model_name, status in self.model_statuses.items():
                config["models"][model_name] = {
                    "status": status,
                    "recommended": model_name in RECOMMENDED_MODELS,
                }
                
                # Add recommended model metadata if available
                if model_name in RECOMMENDED_MODELS:
                    config["models"][model_name].update(RECOMMENDED_MODELS[model_name])
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Save to file
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
                
            self.log(f"[Config] Exported model configuration to {path}")
            return True
            
        except Exception as e:
            self.log(f"[Error] Failed to export model configuration: {e}")
            return False

    def import_model_config(self, path: str) -> bool:
        """
        Import model configurations from a file
        
        Args:
            path: Path to configuration file
            
        Returns:
            True if imported successfully, False otherwise
        """
        if not os.path.exists(path):
            self.log(f"[Error] Configuration file not found: {path}")
            return False
            
        try:
            # Load from file
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
                
            # Update model path if specified
            if "model_path" in config and config["model_path"] != self.model_path:
                self.update_model_path(config["model_path"])
                
            # Update 8-bit setting
            if "use_8bit" in config:
                self.use_8bit = config["use_8bit"]
                
            # Refresh model status information if provided
            if "models" in config:
                for model_name, model_info in config["models"].items():
                    if "status" in model_info:
                        status = model_info["status"]
                        # Only update if the status indicates the model is installed
                        if status == MODEL_STATUS["INSTALLED"]:
                            # Verify model is actually installed
                            if self.verify_model_status(model_name):
                                self._update_model_status(model_name, status)
            
            self.log(f"[Config] Imported model configuration from {path}")
            return True
            
        except Exception as e:
            self.log(f"[Error] Failed to import model configuration: {e}")
            return False
        
    def chat_stream(self, prompt: str, format_function: Callable, 
                   callback: Callable[[str, str], None]) -> bool:
        """
        Send a prompt to the model and stream back the response
        
        Args:
            prompt: Prompt to send
            format_function: Function to format the prompt for the model
            callback: Function to call with chunks of the response
            
        Returns:
            True if chat completed successfully, False otherwise
        """
        if not self.model_process or self.model_process.poll() is not None:
            self.log("[Error] Model is not running")
            callback("error", "Model is not running")
            return False
        
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
            
            # Create a thread for reading the response
            def read_response():
                response_buffer = ""
                
                try:
                    while True:
                        if self.model_process.poll() is not None:
                            # Process ended unexpectedly
                            callback("error", "Model process terminated unexpectedly")
                            break
                            
                        line = self.model_process.stdout.readline()
                        if not line:
                            time.sleep(0.1)
                            continue
                            
                        # Clean the line
                        chunk = line.strip()
                        if not chunk:
                            continue
                            
                        # Check if response is complete
                        if "> " in chunk or "▌" in chunk:
                            # Send final complete flag
                            callback("complete", response_buffer.strip())
                            break
                            
                        # Add to buffer and send the chunk
                        response_buffer += chunk + "\n"
                        callback("chunk", chunk)
                        
                    # Update status when done
                    self._update_model_status(model_name, MODEL_STATUS["RUNNING"])
                    
                except Exception as e:
                    self.log(f"[Stream Error] {e}")
                    callback("error", str(e))
                    self._update_model_status(model_name, MODEL_STATUS["ERROR"])
            
            # Start the response thread
            threading.Thread(target=read_response, daemon=True).start()
            return True
            
        except Exception as e:
            self.log(f"[Chat Error] {e}")
            self._update_model_status(model_name, MODEL_STATUS["ERROR"])
            callback("error", str(e))
            return False
        
    def get_model_config(self, model_name):
        """
        Get configuration details for a specific model
        
        Args:
            model_name (str): Name of the model
            
        Returns:
            dict: Model configuration or None if model not found
        """
        # Check if model exists in available models
        for model in self.available_models:
            if model['name'] == model_name:
                return model
                
        # If model not found in available models, check if it's a custom model
        custom_models = self.config.get("models.custom_models", [])
        for model in custom_models:
            if model['name'] == model_name:
                return model
        
        # Model not found
        self.logger(f"[ModelManager] Model config not found for: {model_name}")
        return None
    
    def list_models(self, remote=False):
        """
        List installed Ollama models or remote models
        
        Args:
            remote: Whether to list remote models (True) or local models (False)
            
        Returns:
            Tuple of (success, data) where data is a dict with models list or error
        """
        self.log(f"[Models] Listing {'remote' if remote else 'local'} Ollama models")
        
        try:
            # Check if Ollama is installed
            if shutil.which("ollama") is None:
                return False, {"error": "Ollama executable not found"}
                
            # Command to list models
            cmd = ["ollama", "list"]
            if remote:
                cmd.append("remote")
                
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10,
                env=os.environ.copy()
            )
            
            if result.returncode != 0:
                return False, {"error": f"Command failed: {result.stderr}"}
                
            # Parse the output to extract model names
            output = self._strip_ansi_codes(result.stdout)
            lines = output.strip().split('\n')
            models = []
            
            # Skip header line if present
            start_idx = 1 if len(lines) > 0 and ('NAME' in lines[0] or 'MODEL' in lines[0]) else 0
            
            # Parse each line to extract model info
            for line in lines[start_idx:]:
                if line.strip():
                    # First column is name, try to extract tags too
                    parts = line.split()
                    if not parts:
                        continue
                        
                    name = parts[0]
                    models.append({
                        "name": name,
                        "status": "installed" if not remote else "available",
                    })
            
            return True, {"models": models}
            
        except Exception as e:
            self.log(f"[Error] Failed to list models: {e}")
            return False, {"error": str(e)}
    
    def get_available_models(self) -> list:
        """
        Return a list of available model names (for UI compatibility).
        """
        try:
            # Try to get all available models (installed and remote)
            models = self.fetch_available_models()
            return [m["name"] for m in models if "name" in m]
        except Exception as e:
            self.log(f"[Error] get_available_models failed: {e}")
            return []