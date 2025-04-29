"""
Ollama Client - Direct interface to Ollama API
"""
import os
import subprocess
import json
import re  # For stripping ANSI escape codes
from typing import Dict, Any, Tuple, Optional, Callable

class OllamaClient:
    """Provides direct access to Ollama API for generating text responses"""
    
    def __init__(self, logger: Optional[Callable] = None):
        """
        Initialize the Ollama client
        
        Args:
            logger: Optional logging function
        """
        self.log = logger or print
        
    def generate(self, model: str, prompt: str, params: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Generate a response by invoking Ollama's run subcommand with prompt as argument
        Strips ANSI escape sequences from model output.
        
        Args:
            model: Model name
            prompt: The prompt to send
            params: Optional parameters for generation
            
        Returns:
            Tuple of (success, response)
        """
        try:
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
            # Strip ANSI escape codes from output
            raw = result.stdout or ""
            clean = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
            output = clean.sub('', raw).strip()
            # Handle errors
            if result.stderr:
                err = result.stderr.strip()
                self.log(f"[Error] Model error: {err}")
                return False, err
            return True, output
        except Exception as e:
            self.log(f"[Error] Failed to generate response: {e}")
            return False, f"Error: {str(e)}"
    def list_models(self, remote=False) -> Tuple[bool, Dict[str, Any]]:
        """
        List models available in Ollama
        
        Args:
            remote: Whether to list remote models (True) or local models (False)
            
        Returns:
            Tuple of (success, model_list_dict)
        """
        try:
            # Define command based on whether we're fetching remote or local models
            if remote:
                cmd = ["ollama", "list", "remote"]
                self.log(f"[Ollama] Listing remote models from Ollama Hub")
            else:
                cmd = ["ollama", "list"]
                self.log(f"[Ollama] Listing locally installed models")
            
            # Add timeout to prevent hanging
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30,  # Add a reasonable timeout
                env=os.environ.copy()
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                self.log(f"[Ollama] Error listing {'remote' if remote else 'local'} models: {error_msg}")
                
                # If we get a connection error for remote models, try an alternative command
                if remote and "connection refused" in error_msg.lower():
                    self.log("[Ollama] Connection refused. Checking if Ollama service is running...")
                    
                    # Check Ollama service status
                    try:
                        check_result = subprocess.run(
                            ["ollama", "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if check_result.returncode == 0:
                            self.log(f"[Ollama] Ollama is installed (version: {check_result.stdout.strip()})")
                            self.log("[Ollama] But service might not be running. Please start the Ollama service.")
                    except Exception as e:
                        self.log(f"[Ollama] Error checking Ollama installation: {e}")
                
                return False, {"error": error_msg}
                
            # Parse the output to get model list
            # Ollama returns a table-like format, we need to parse it
            models = []
            lines = result.stdout.strip().split('\n')
            
            if len(lines) > 1:  # First line is header, skip it
                header = lines[0].lower()
                has_tags = "tags" in header
                
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    
                    # Split by whitespace but keep quotes together
                    parts = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")++', line)
                    
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        size = parts[1].strip() if len(parts) > 1 else "Unknown"
                        
                        # Extract parameter info from model name if possible
                        param_match = re.search(r'(\d+)b', name, re.IGNORECASE)
                        parameters = f"{param_match.group(1)}B" if param_match else ""
                        
                        # Extract tags if available
                        tags = []
                        if has_tags and len(parts) > 3:
                            # Tags might be in the last column
                            potential_tags = parts[-1].strip()
                            if potential_tags and potential_tags != "-":
                                tags = [tag.strip() for tag in potential_tags.split(",")]
                        
                        model_info = {
                            "name": name,
                            "size": size,
                            "parameters": parameters,
                            "digest": parts[2] if len(parts) > 2 else "",
                            "modified": " ".join(parts[3:len(parts)-1 if has_tags else None]) if len(parts) > 3 else "",
                            "tags": tags
                        }
                        
                        models.append(model_info)
            self.log(f"[Ollama] Successfully found {len(models)} {'remote' if remote else 'local'} models")
            return True, {"models": models}
            
        except subprocess.TimeoutExpired:
            self.log(f"[Ollama] Timeout while listing {'remote' if remote else 'local'} models")
            return False, {"error": "Timeout while listing models. The Ollama service might be slow or not responding."}
        except Exception as e:
            self.log(f"[Ollama] Exception listing {'remote' if remote else 'local'} models: {e}")
            return False, {"error": str(e)}
            
        except Exception as e:
            self.log(f"[Ollama] Exception listing models: {e}")
            return False, {"error": str(e)}
    
    def pull_model(self, model_name: str, progress_callback=None) -> Tuple[bool, str]:
        """
        Pull a model from Ollama library
        
        Args:
            model_name: Name of the model to pull
            progress_callback: Optional callback function to report download progress
            
        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = ["ollama", "pull", model_name]
            self.log(f"[Ollama] Pulling model: {model_name}")
            
            # Use Popen to stream output for real-time progress tracking
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=os.environ.copy()
            )
            
            # Initialize variables
            success = True
            error_message = ""
            progress_pattern = re.compile(r'(\d+\.\d+)%')
            
            # Process stdout in real-time
            for line in iter(process.stdout.readline, ''):
                self.log(f"[Ollama Pull] {line.strip()}")
                
                # Check for progress indication and call the progress callback if provided
                if progress_callback and "%" in line:
                    match = progress_pattern.search(line)
                    if match:
                        try:
                            percentage = float(match.group(1))
                            progress_callback(percentage)
                        except ValueError:
                            pass
            
            # Process potential errors from stderr
            for line in iter(process.stderr.readline, ''):
                line = line.strip()
                if line:
                    error_message += line + "\n"
                    self.log(f"[Ollama Pull Error] {line}")
                    success = False
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code != 0:
                self.log(f"[Ollama] Error pulling model: {error_message}")
                return False, error_message or f"Process exited with return code {return_code}"
                
            return True, "Model pulled successfully"
            
        except Exception as e:
            self.log(f"[Ollama] Exception pulling model: {e}")
            return False, str(e)
    
    def delete_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Delete a model from Ollama
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = ["ollama", "rm", model_name]
            self.log(f"[Ollama] Deleting model: {model_name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )
            
            if result.returncode != 0:
                self.log(f"[Ollama] Error deleting model: {result.stderr}")
                return False, result.stderr
                
            return True, "Model deleted successfully"
            
        except Exception as e:
            self.log(f"[Ollama] Exception deleting model: {e}")
            return False, str(e)
    
    def get_model_info(self, model_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get detailed information about a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Tuple of (success, model_info)
        """
        try:
            cmd = ["ollama", "show", model_name]
            self.log(f"[Ollama] Getting info for model: {model_name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )
            
            if result.returncode != 0:
                self.log(f"[Ollama] Error getting model info: {result.stderr}")
                return False, {"error": result.stderr}
                
            # Parse the output
            info = {}
            current_section = "general"
            info[current_section] = {}
            
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                if line.startswith("#"):
                    # New section header
                    current_section = line.strip("# ").lower()
                    info[current_section] = {}
                    continue
                
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[current_section][key.strip()] = value.strip()
            
            return True, info
            
        except Exception as e:
            self.log(f"[Ollama] Exception getting model info: {e}")
            return False, {"error": str(e)}
