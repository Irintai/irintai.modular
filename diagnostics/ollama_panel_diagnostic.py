# filepath: d:\AI\IrintAI Assistant\diagnostics\ollama_panel_diagnostic.py
import requests
import json
import tkinter as tk
from tkinter import ttk
import sys
import os
from urllib.parse import urlparse

# Add project root to sys.path to allow importing core modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from plugins.ollama_hub.core.ollama_client import OllamaClient
    from core.config_manager import ConfigManager
    from utils.logger import IrintaiLogger # Assuming logger setup utility
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Please ensure the script is run from the project root or the PYTHONPATH is set correctly.")
    sys.exit(1)

# Setup a dummy logger for the client if needed
diagnostic_logger = IrintaiLogger('ollama_diagnostic', 'ollama_diagnostic.log')

class OllamaPanelDiagnostic:    
    def __init__(self, config_path='data/config.json'):
        self.config_manager = ConfigManager(config_path)
        self.ollama_url = self.config_manager.get("ollama_url", "http://localhost:11434")
        self.results = {}
        # Pass a proper logging function - using the print method from this class
        # since OllamaClient expects a callable function, not a logger object
        self.ollama_client = OllamaClient(logger=self.log) # Only pass logger since OllamaClient doesn't accept base_url

    def log(self, message):
        """Simple print-based logging for diagnostics."""
        print(f"[DIAGNOSTIC] {message}")

    def check_ollama_server_connection(self):
        """Checks if the Ollama server is reachable."""
        self.log(f"Attempting to connect to Ollama server at: {self.ollama_url}")
        try:
            response = requests.get(f"{self.ollama_url}/", timeout=5)
            if response.status_code == 200 and "Ollama is running" in response.text:
                self.results['server_connection'] = {'status': 'Success', 'message': f"Successfully connected to {self.ollama_url}."}
                self.log("Server connection successful.")
                return True
            else:
                self.results['server_connection'] = {'status': 'Failure', 'message': f"Connected, but unexpected response (Status: {response.status_code}). Is it an Ollama server?"}
                self.log(f"Server connection failed: Unexpected response {response.status_code}")
                return False
        except requests.exceptions.ConnectionError as e:
            self.results['server_connection'] = {'status': 'Failure', 'message': f"Connection Error: Could not connect to {self.ollama_url}. Is Ollama running? Details: {e}"}
            self.log(f"Server connection failed: Connection Error - {e}")
            return False
        except requests.exceptions.Timeout:
            self.results['server_connection'] = {'status': 'Failure', 'message': f"Connection Timeout: Timed out connecting to {self.ollama_url}."}
            self.log("Server connection failed: Timeout")
            return False
        except Exception as e:
            self.results['server_connection'] = {'status': 'Failure', 'message': f"An unexpected error occurred during connection: {e}"}
            self.log(f"Server connection failed: Unexpected error - {e}")
            return False

    def check_list_local_models(self):
        """Checks if local models can be listed via the API."""
        if not self.results.get('server_connection', {}).get('status') == 'Success':
            self.results['list_local_models'] = {'status': 'Skipped', 'message': 'Server connection failed.'}
            self.log("Skipping local model list check - server connection failed.")
            return False

        self.log("Attempting to list local models...")
        try:
            # Use the OllamaClient method
            success, data = self.ollama_client.list_models(remote=False)

            if success and isinstance(data.get('models'), list):
                count = len(data['models'])
                self.results['list_local_models'] = {'status': 'Success', 'message': f"Successfully listed {count} local models."}
                self.log(f"Local model list successful ({count} models found).")
                return True
            else:
                error_msg = data.get('error', 'Unknown error format')
                self.results['list_local_models'] = {'status': 'Failure', 'message': f"Failed to list local models. API Error: {error_msg}"}
                self.log(f"Local model list failed: {error_msg}")
                return False
        except Exception as e:
            self.results['list_local_models'] = {'status': 'Failure', 'message': f"An unexpected error occurred listing local models: {e}"}
            self.log(f"Local model list failed: Unexpected error - {e}")
            return False

    def check_list_remote_models(self):
        """Checks if remote models can be listed (simulated or via client)."""
        if not self.results.get('server_connection', {}).get('status') == 'Success':
            self.results['list_remote_models'] = {'status': 'Skipped', 'message': 'Server connection failed.'}
            self.log("Skipping remote model list check - server connection failed.")
            return False

        self.log("Attempting to list remote models...")
        try:
            # Use the OllamaClient method if it supports remote listing reliably
            success, data = self.ollama_client.list_models(remote=True)

            if success and isinstance(data.get('models'), list):
                count = len(data['models'])
                self.results['list_remote_models'] = {'status': 'Success', 'message': f"Successfully listed {count} remote models from Ollama Hub."}
                self.log(f"Remote model list successful ({count} models found).")
                return True
            elif not success and "failed to get location" in data.get('error', '').lower():
                 self.results['list_remote_models'] = {'status': 'Warning', 'message': f"Could not fetch remote models (API Error: {data.get('error', '')}). This might be a temporary Ollama Hub issue or network problem."}
                 self.log(f"Remote model list warning: {data.get('error', '')}")
                 return False # Treat as warning, not outright failure for diagnostics
            else:
                error_msg = data.get('error', 'Unknown error format')
                self.results['list_remote_models'] = {'status': 'Failure', 'message': f"Failed to list remote models. API Error: {error_msg}"}
                self.log(f"Remote model list failed: {error_msg}")
                return False        
        except Exception as e:
        # Handle connection issues with Ollama hub
        # Since OllamaClient doesn't have remote_registry_url attribute, use a default
            default_registry = "ollama.ai"
            if isinstance(e, requests.exceptions.ConnectionError) and default_registry in str(e):
                self.results['list_remote_models'] = {'status': 'Warning', 'message': f"Could not connect to Ollama Hub ({default_registry}): {e}. Check network/DNS."}
                self.log(f"Remote model list warning: Connection error to {default_registry} - {e}")
                return False
            else:
                self.results['list_remote_models'] = {'status': 'Failure', 'message': f"An unexpected error occurred listing remote models: {e}"}
                self.log(f"Remote model list failed: Unexpected error - {e}")
                return False

    def check_pull_model(self, model_name="phi3:mini"):
        """Attempts to pull a small model to test download functionality."""
        if not self.results.get('server_connection', {}).get('status') == 'Success':
            self.results['pull_model'] = {'status': 'Skipped', 'message': 'Server connection failed.'}
            self.log(f"Skipping pull model check ({model_name}) - server connection failed.")
            return False

        self.log(f"Attempting to pull model: {model_name} (this may take a moment)...")
        try:
            # Use the OllamaClient method
            success, message = self.ollama_client.pull_model(model_name, progress_callback=lambda p: None) # No progress needed for diagnostic

            if success:
                self.results['pull_model'] = {'status': 'Success', 'message': f"Successfully pulled model '{model_name}'."}
                self.log(f"Pull model successful: {model_name}")
                # Attempt to clean up the downloaded model
                self.check_delete_model(model_name, is_cleanup=True)
                return True
            else:
                self.results['pull_model'] = {'status': 'Failure', 'message': f"Failed to pull model '{model_name}'. API Error: {message}"}
                self.log(f"Pull model failed ({model_name}): {message}")
                return False
        except Exception as e:
            self.results['pull_model'] = {'status': 'Failure', 'message': f"An unexpected error occurred pulling model '{model_name}': {e}"}
            self.log(f"Pull model failed ({model_name}): Unexpected error - {e}")
            return False

    def check_delete_model(self, model_name="phi3:mini", is_cleanup=False):
        """Attempts to delete a model (used for cleanup after pull test)."""
        if not self.results.get('server_connection', {}).get('status') == 'Success':
            if not is_cleanup:
                self.results['delete_model'] = {'status': 'Skipped', 'message': 'Server connection failed.'}
            self.log(f"Skipping delete model check ({model_name}) - server connection failed.")
            return False

        self.log(f"Attempting to delete model: {model_name}...")
        try:
            # Use the OllamaClient method
            success, message = self.ollama_client.delete_model(model_name)

            result_key = 'delete_model_cleanup' if is_cleanup else 'delete_model'

            if success:
                self.results[result_key] = {'status': 'Success', 'message': f"Successfully deleted model '{model_name}'."}
                self.log(f"Delete model successful: {model_name}")
                return True
            else:
                # It's possible the model wasn't there to begin with (e.g., pull failed)
                if "model 'phi3:mini' not found" in message:
                     self.results[result_key] = {'status': 'Info', 'message': f"Model '{model_name}' not found for deletion (might be expected if pull failed)."}
                     self.log(f"Delete model info ({model_name}): Model not found.")
                     return True # Not a failure in this context
                else:
                    self.results[result_key] = {'status': 'Failure', 'message': f"Failed to delete model '{model_name}'. API Error: {message}"}
                    self.log(f"Delete model failed ({model_name}): {message}")
                    return False
        except Exception as e:
            result_key = 'delete_model_cleanup' if is_cleanup else 'delete_model'
            self.results[result_key] = {'status': 'Failure', 'message': f"An unexpected error occurred deleting model '{model_name}': {e}"}
            self.log(f"Delete model failed ({model_name}): Unexpected error - {e}")
            return False

    def run_all_checks(self):
        """Runs all diagnostic checks."""
        self.log("Starting Ollama Panel Diagnostics...")
        self.check_ollama_server_connection()
        self.check_list_local_models()
        self.check_list_remote_models()
        self.check_pull_model() # This implicitly tests delete on success
        self.log("Diagnostics complete.")

    def print_results(self):
        """Prints the results of the diagnostic checks."""
        print("\n--- Ollama Panel Diagnostic Results ---")
        print(f"Ollama URL Tested: {self.ollama_url}")
        print("-" * 35)
        for check, result in self.results.items():
            status = result.get('status', 'Unknown')
            message = result.get('message', 'No details.')
            print(f"[{status.upper()}] Check: {check.replace('_', ' ').title()}")
            print(f"  Message: {message}")
            print("-" * 35)
        print("--- End of Report ---")

if __name__ == "__main__":
    # Example usage: Run from the command line
    config_file = os.path.join(project_root, 'data', 'config.json')
    diagnostic = OllamaPanelDiagnostic(config_path=config_file)
    diagnostic.run_all_checks()
    diagnostic.print_results()

    # Optional: Keep window open if run directly without console
    input("Press Enter to exit...")
