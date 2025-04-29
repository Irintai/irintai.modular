"""
Memory Diagnostic Module for IrintAI Assistant

This module provides diagnostics for the memory system including:
- Memory storage file integrity
- Chat history access
- Vector store connectivity
- Memory database operations
"""
import os
import sys
import json
import time
from typing import Dict, Any, List

# Add project root to sys.path to allow importing core modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.config_manager import ConfigManager
    from core.memory_system import MemorySystem
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure the script is run from the project root or the PYTHONPATH is set correctly.")

class MemoryDiagnostic:
    """Diagnostic tool for memory system checks"""
    
    def __init__(self, config_path='data/config.json'):
        """Initialize the memory diagnostic module"""
        self.config_path = config_path
        self.results = {}
        
        # Try to initialize config manager
        try:
            self.config_manager = ConfigManager(config_path)
            self.config_loaded = True
            
            # Get memory paths
            self.chat_history_path = self.config_manager.get("memory", {}).get("chat_history_path", "data/chat_history.json")
            if not os.path.isabs(self.chat_history_path):
                self.chat_history_path = os.path.join(project_root, self.chat_history_path)
                
            self.vector_store_path = self.config_manager.get("memory", {}).get("vector_store_path", "data/vector_store")
            if not os.path.isabs(self.vector_store_path):
                self.vector_store_path = os.path.join(project_root, self.vector_store_path)
                
            self.reflections_path = self.config_manager.get("memory", {}).get("reflections_path", "data/reflections")
            if not os.path.isabs(self.reflections_path):
                self.reflections_path = os.path.join(project_root, self.reflections_path)
                
        except Exception as e:
            self.config_loaded = False
            # Set default paths
            self.chat_history_path = os.path.join(project_root, "data/chat_history.json")
            self.vector_store_path = os.path.join(project_root, "data/vector_store")
            self.reflections_path = os.path.join(project_root, "data/reflections")
            print(f"Error loading configuration: {e}")        # Try to initialize memory system but catch any exceptions
        try:
            # Get the model name from config instead of passing the entire config manager
            model_name = self.config_manager.get("memory", {}).get("embedding_model", "all-MiniLM-L6-v2")
            index_path = os.path.join(self.vector_store_path, "vector_store.json")
            self.memory_system = MemorySystem(model_name=model_name, index_path=index_path)
            self.memory_system_loaded = True
        except Exception as e:
            self.memory_system_loaded = False
            self.memory_system = None  # Set to None to avoid AttributeError
            print(f"Error initializing memory system: {e}")
        
    def log(self, message):
        """Simple print-based logging for diagnostics"""
        print(f"[MEMORY DIAG] {message}")
    
    def check_chat_history_file(self):
        """Check if the chat history file exists and is valid JSON"""
        self.log(f"Checking chat history file: {self.chat_history_path}")
        
        # Check if file exists
        if not os.path.exists(self.chat_history_path):
            # It's okay if chat history doesn't exist yet, just warn
            self.results['chat_history_file'] = {
                'status': 'Warning',
                'message': f"Chat history file does not exist: {self.chat_history_path}"
            }
            self.log("Chat history file does not exist (this might be expected for new installations)")
            return True
            
        # Check if file is readable
        if not os.access(self.chat_history_path, os.R_OK):
            self.results['chat_history_file'] = {
                'status': 'Failure',
                'message': f"Chat history file is not readable: {self.chat_history_path}"
            }
            self.log("Chat history file is not readable")
            return False
            
        # Check if file is valid JSON
        try:
            with open(self.chat_history_path, 'r') as f:
                chat_history = json.load(f)
                
            # Check if chat history has the expected structure
            if not isinstance(chat_history, list):
                self.results['chat_history_file'] = {
                    'status': 'Warning',
                    'message': f"Chat history file does not contain a valid chat history array"
                }
                self.log("Chat history file structure is invalid")
                return False
                
            self.results['chat_history_file'] = {
                'status': 'Success',
                'message': f"Chat history file is valid with {len(chat_history)} entries"
            }
            self.log(f"Chat history file is valid with {len(chat_history)} entries")
            return True
                
        except json.JSONDecodeError as e:
            self.results['chat_history_file'] = {
                'status': 'Failure',
                'message': f"Chat history file contains invalid JSON: {e}"
            }
            self.log(f"Chat history file contains invalid JSON: {e}")
            return False
        except Exception as e:
            self.results['chat_history_file'] = {
                'status': 'Failure',
                'message': f"Error reading chat history file: {e}"
            }
            self.log(f"Error reading chat history file: {e}")
            return False
    
    def check_vector_store_directory(self):
        """Check if the vector store directory exists and is accessible"""
        self.log(f"Checking vector store directory: {self.vector_store_path}")
        
        # Check if directory exists
        if os.path.exists(self.vector_store_path):
            if os.path.isdir(self.vector_store_path):
                if os.access(self.vector_store_path, os.R_OK):
                    # Check if there are any files in the directory
                    try:
                        contents = os.listdir(self.vector_store_path)
                        if contents:
                            self.results['vector_store_directory'] = {
                                'status': 'Success',
                                'message': f"Vector store directory exists with {len(contents)} items"
                            }
                            self.log(f"Vector store directory exists with {len(contents)} items")
                        else:
                            # Empty vector store is a warning but not a failure
                            self.results['vector_store_directory'] = {
                                'status': 'Warning',
                                'message': f"Vector store directory exists but is empty"
                            }
                            self.log("Vector store directory is empty")
                        return True
                    except Exception as e:
                        self.results['vector_store_directory'] = {
                            'status': 'Warning',
                            'message': f"Error reading vector store directory contents: {e}"
                        }
                        self.log(f"Error reading vector store directory contents: {e}")
                        return False
                else:
                    self.results['vector_store_directory'] = {
                        'status': 'Failure',
                        'message': f"Vector store directory is not readable: {self.vector_store_path}"
                    }
                    self.log("Vector store directory is not readable")
                    return False
            else:
                self.results['vector_store_directory'] = {
                    'status': 'Failure',
                    'message': f"Vector store path exists but is not a directory: {self.vector_store_path}"
                }
                self.log("Vector store path is not a directory")
                return False
        else:
            # First run might not have a vector store yet
            self.results['vector_store_directory'] = {
                'status': 'Warning',
                'message': f"Vector store directory does not exist: {self.vector_store_path}"
            }
            self.log("Vector store directory does not exist")
            return False
    
    def check_reflections_directory(self):
        """Check if the reflections directory exists and is accessible"""
        self.log(f"Checking reflections directory: {self.reflections_path}")
        
        # Check if directory exists
        if os.path.exists(self.reflections_path):
            if os.path.isdir(self.reflections_path):
                if os.access(self.reflections_path, os.R_OK):
                    # Check if there are any files in the directory
                    try:
                        contents = os.listdir(self.reflections_path)
                        self.results['reflections_directory'] = {
                            'status': 'Success',
                            'message': f"Reflections directory exists with {len(contents)} items"
                        }
                        self.log(f"Reflections directory exists with {len(contents)} items")
                        return True
                    except Exception as e:
                        self.results['reflections_directory'] = {
                            'status': 'Warning',
                            'message': f"Error reading reflections directory contents: {e}"
                        }
                        self.log(f"Error reading reflections directory contents: {e}")
                        return False
                else:
                    self.results['reflections_directory'] = {
                        'status': 'Failure',
                        'message': f"Reflections directory is not readable: {self.reflections_path}"
                    }
                    self.log("Reflections directory is not readable")
                    return False
            else:
                self.results['reflections_directory'] = {
                    'status': 'Failure',
                    'message': f"Reflections path exists but is not a directory: {self.reflections_path}"
                }
                self.log("Reflections path is not a directory")
                return False
        else:
            # No reflections yet is acceptable
            self.results['reflections_directory'] = {
                'status': 'Warning',
                'message': f"Reflections directory does not exist: {self.reflections_path}"
            }
            self.log("Reflections directory does not exist")
            return False
    
    def check_memory_system_init(self):
        """Check if the memory system can be initialized"""
        self.log("Checking memory system initialization...")
        
        if not self.config_loaded:
            self.results['memory_system_init'] = {
                'status': 'Skipped',
                'message': 'Configuration manager not initialized'
            }
            self.log("Skipping memory system check - config not loaded")
            return False
            
        if self.memory_system_loaded:
            self.results['memory_system_init'] = {
                'status': 'Success',
                'message': 'Memory system initialized successfully'
            }
            self.log("Memory system initialized successfully")
            return True
        else:
            self.results['memory_system_init'] = {
                'status': 'Failure',
                'message': 'Failed to initialize memory system'
            }
            self.log("Memory system initialization failed")
            return False
    
    def check_memory_operations(self):
        """Check basic memory operations if memory system is initialized"""
        if not self.memory_system_loaded:
            self.results['memory_operations'] = {
                'status': 'Skipped',
                'message': 'Memory system not initialized'
            }
            self.log("Skipping memory operations check - memory system not initialized")
            return False
            
        self.log("Checking basic memory operations...")
        
        operations_results = {}
        failures = 0
        
        # Check if we can access chat history
        try:
            # Use a safe method to test memory access
            if hasattr(self.memory_system, 'get_chat_history'):
                chat_history = self.memory_system.get_chat_history(limit=1)
                operations_results['get_chat_history'] = {
                    'status': 'Success',
                    'message': f"Successfully retrieved chat history"
                }
            else:
                operations_results['get_chat_history'] = {
                    'status': 'Skipped',
                    'message': "Memory system does not expose get_chat_history method"
                }
        except Exception as e:
            failures += 1
            operations_results['get_chat_history'] = {
                'status': 'Failure',
                'message': f"Error retrieving chat history: {e}"
            }
            self.log(f"Error retrieving chat history: {e}")

        # Skip vector operations if they're likely to modify data
        # Instead check if vector store exists and is accessible
        
        # Determine overall status
        if failures == 0:
            self.results['memory_operations'] = {
                'status': 'Success',
                'message': 'All memory operations completed successfully',
                'details': operations_results
            }
            self.log("All memory operations completed successfully")
            return True
        else:
            self.results['memory_operations'] = {
                'status': 'Failure',
                'message': f"{failures} memory operations failed",
                'details': operations_results
            }
            self.log(f"{failures} memory operations failed")
            return False
    
    def check_memory_permissions(self):
        """Check write permissions for memory-related directories and files"""
        self.log("Checking memory system write permissions...")
        
        permission_results = {}
        permission_failures = 0
        
        # Check chat history file or its parent directory if it doesn't exist
        chat_history_dir = os.path.dirname(self.chat_history_path)
        if os.path.exists(self.chat_history_path):
            chat_history_writable = os.access(self.chat_history_path, os.W_OK)
        else:
            # Check if we can create the file
            chat_history_writable = os.path.exists(chat_history_dir) and os.access(chat_history_dir, os.W_OK)
            
        permission_results['chat_history'] = {
            'status': 'Success' if chat_history_writable else 'Failure',
            'message': f"Chat history {'is' if chat_history_writable else 'is not'} writable"
        }
        
        if not chat_history_writable:
            permission_failures += 1
        
        # Check vector store directory
        if os.path.exists(self.vector_store_path):
            vector_store_writable = os.path.isdir(self.vector_store_path) and os.access(self.vector_store_path, os.W_OK)
        else:
            # Check if we can create the directory
            vector_store_parent = os.path.dirname(self.vector_store_path)
            vector_store_writable = os.path.exists(vector_store_parent) and os.access(vector_store_parent, os.W_OK)
            
        permission_results['vector_store'] = {
            'status': 'Success' if vector_store_writable else 'Failure',
            'message': f"Vector store {'is' if vector_store_writable else 'is not'} writable"
        }
        
        if not vector_store_writable:
            permission_failures += 1
        
        # Check reflections directory
        if os.path.exists(self.reflections_path):
            reflections_writable = os.path.isdir(self.reflections_path) and os.access(self.reflections_path, os.W_OK)
        else:
            # Check if we can create the directory
            reflections_parent = os.path.dirname(self.reflections_path)
            reflections_writable = os.path.exists(reflections_parent) and os.access(reflections_parent, os.W_OK)
            
        permission_results['reflections'] = {
            'status': 'Success' if reflections_writable else 'Failure',
            'message': f"Reflections directory {'is' if reflections_writable else 'is not'} writable"
        }
        
        if not reflections_writable:
            permission_failures += 1
        
        # Determine overall status
        if permission_failures == 0:
            self.results['memory_permissions'] = {
                'status': 'Success',
                'message': 'All memory locations have write permissions',
                'details': permission_results
            }
            self.log("All memory locations have write permissions")
            return True
        else:
            self.results['memory_permissions'] = {
                'status': 'Failure',
                'message': f"{permission_failures} memory locations have permission issues",
                'details': permission_results
            }
            self.log(f"{permission_failures} memory locations have permission issues")
            return False
    
    def run_all_checks(self):
        """Run all memory diagnostic checks"""
        self.log("Starting memory diagnostics...")
        start_time = time.time()
        
        # Run checks
        self.check_chat_history_file()
        self.check_vector_store_directory()
        self.check_reflections_directory()
        self.check_memory_system_init()
        self.check_memory_operations()
        self.check_memory_permissions()
        
        elapsed_time = time.time() - start_time
        self.log(f"Memory diagnostics completed in {elapsed_time:.2f} seconds")
        return self.results
