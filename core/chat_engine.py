"""
Chat Engine - Handles conversation logic and prompt formatting
"""
import time
import json
import os
from typing import List, Dict, Any, Optional, Callable

class ChatEngine:
    """Manages chat history, prompt formatting, and conversation context"""
    
    def __init__(self, 
                 model_manager,
                 memory_system=None,
                 session_file: str = "data/chat_history.json",
                 logger: Optional[Callable] = None):
        """
        Initialize the chat engine
        
        Args:
            model_manager: ModelManager instance
            memory_system: Optional MemorySystem instance
            session_file: Path to save chat history
            logger: Optional logging function
        """
        self.model_manager = model_manager
        self.memory_system = memory_system
        self.session_file = session_file
        self.log = logger or print
        
        self.chat_history = []
        self.system_prompt = "You are Irintai, a helpful and knowledgeable assistant."
        self.memory_mode = "Off"  # Off, Manual, Auto, Background
        
        # Create directory for session file if it doesn't exist
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        
        # Load previous session if available
        self.load_session()
        
    def set_system_prompt(self, prompt: str) -> None:
        """
        Set the system prompt
        
        Args:
            prompt: System prompt text
        """
        self.system_prompt = prompt
        self.log(f"[System Prompt] Applied: {prompt}")
        
    def set_memory_mode(self, enabled=True, auto=False, background=False) -> None:
        """
        Set the memory mode
        
        Args:
            enabled: Whether memory is enabled
            auto: Whether to automatically use memory
            background: Whether to run memory processing in background
        """
        if not enabled:
            self.memory_mode = "off"
        elif enabled and not auto:
            self.memory_mode = "manual"
        elif enabled and auto and not background:
            self.memory_mode = "auto"
        elif enabled and auto and background:
            self.memory_mode = "background"
            
        self.log(f"[Memory Mode] Set to: {self.memory_mode.capitalize()}")
        
    def format_prompt(self, prompt: str, model_name: str) -> str:
        """
        Format a prompt for the given model
        
        Args:
            prompt: User prompt
            model_name: Name of the model
            
        Returns:
            Formatted prompt
        """
        model = model_name.lower()
        
        # Create a context from the recent chat history (last few exchanges)
        recent_history = []
        history_limit = 5  # Number of recent exchanges to include
        
        # Get the recent history
        if self.chat_history:
            recent_history = self.chat_history[-min(len(self.chat_history), history_limit*2):]
        
        # Check memory mode and add relevant context if enabled
        context = ""
        if self.memory_mode in ["Auto", "Background"] and self.memory_system:
            matches = self.memory_system.search(prompt)
            if matches:
                context = "\n\nRelevant context from documents:\n"
                for m in matches:
                    source = m.get("source", "Unknown")
                    text_preview = m.get("text", "")[:200]  # Get first 200 chars
                    context += f"From {source}: {text_preview}\n\n"
                
                self.log(f"[Memory] Added context from {len(matches)} relevant documents")
        
        # Format based on the model
        if any(k in model for k in ["llama", "mistral", "nous", "mythomax"]):
            # Build chat context with system prompt
            formatted_history = f"<|system|>\n{self.system_prompt}\n" if self.system_prompt else ""
            
            for msg in recent_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user":
                    formatted_history += f"<|user|>\n{content}\n"
                elif role == "assistant":
                    formatted_history += f"<|assistant|>\n{content}\n"
            
            # Add the current prompt
            return context + formatted_history + f"<|user|>\n{prompt.strip()}\n<|assistant|>\n"
        
        elif "phi" in model:
            # Format for Phi models
            formatted_history = f"System: {self.system_prompt}\n\n" if self.system_prompt else ""
            
            for msg in recent_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user":
                    formatted_history += f"Human: {content}\n"
                elif role == "assistant":
                    formatted_history += f"Assistant: {content}\n"
            
            # Add the current prompt
            return context + formatted_history + f"Human: {prompt.strip()}\n\nAssistant:"
        
        elif "codellama" in model or "deepseek" in model:
            # Specialized for code models
            formatted = f"""
            [INST] 
            {self.system_prompt}

            {context if context else ''}
            {prompt.strip()}
            [/INST]
            """
            return formatted
        else:
            # Generic format with conversation history
            formatted_history = f"System: {self.system_prompt}\n\n" if self.system_prompt else ""
            
            for msg in recent_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user":
                    formatted_history += f"User: {content}\n\n"
                elif role == "assistant":
                    formatted_history += f"Assistant: {content}\n\n"
            
            # Add the current prompt
            return context + formatted_history + f"User: {prompt.strip()}\n\nAssistant:"
    
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the chat history
        
        Args:
            content: Message content
        """
        message = {
            "role": "user", 
            "content": content,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.chat_history.append(message)
        
    def add_assistant_message(self, content: str, model: str) -> None:
        """
        Add an assistant message to the chat history
        
        Args:
            content: Message content
            model: Model name
        """
        message = {
            "role": "assistant", 
            "content": content,
            "model": model,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.chat_history.append(message)
    
    def send_message(self, content: str, on_response: Optional[Callable] = None) -> str:
        """
        Send a message and get a response
        
        Args:
            content: Message content
            on_response: Optional callback for when response is ready
            
        Returns:
            Response text
        """
        # Add user message to history
        self.add_user_message(content)
        
        # Check if model is running
        if not self.model_manager.current_model:
            error_msg = "Model is not running. Please start a model first."
            self.log(f"[Error] {error_msg}")
            return error_msg
        
        try:
            # Import the OllamaClient
            from plugins.ollama_hub.core.ollama_client import OllamaClient
            
            # Create a client with our logger
            ollama = OllamaClient(logger=self.log)
            
            # Format the prompt
            model_name = self.model_manager.current_model
            formatted_prompt = self.format_prompt(content, model_name)
            
            # Get model parameters if available
            params = getattr(self.model_manager, 'current_parameters', {})
            
            # Log that we're sending the prompt
            self.log(f"[Prompt] Sending to model: {content[:100]}...")
            
            # Send to model using direct Ollama API
            success, response = ollama.generate(model_name, formatted_prompt, params)
        except Exception as e:
            success = False
            response = f"Error occurred: {str(e)}"
            self.log(f"[Error] Exception while generating response: {e}")
        
        if success and response:
            # Add assistant message to history
            self.add_assistant_message(response, model_name)
            
            # Save session
            self.save_session()
            
            # Call callback if provided
            if on_response:
                on_response(response)
                
            return response
        else:
            error_msg = "Failed to get response from model."
            self.log(f"[Error] {error_msg}")
            return error_msg
            
    def save_session(self) -> bool:
        """
        Save the chat session to a file
        
        Returns:
            True if session saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, indent=2)
                
            self.log("[Session] Session saved")
            return True
        except Exception as e:
            self.log(f"[Session Error] Failed to save session: {e}")
            return False
            
    def load_session(self) -> bool:
        """
        Load a chat session from a file
        
        Returns:
            True if session loaded successfully, False otherwise
        """
        if not os.path.exists(self.session_file):
            self.log("[Session] No previous session found")
            return False
            
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                self.chat_history = json.load(f)
                
            self.log(f"[Session] Loaded {len(self.chat_history)} messages")
            return True
        except Exception as e:
            self.log(f"[Session Error] Failed to load session: {e}")
            return False
            
    def clear_history(self) -> None:
        """Clear the chat history"""
        self.chat_history = []
        self.log("[Session] Chat history cleared")
        
    def get_last_model(self) -> Optional[str]:
        """
        Get the last used model from chat history
        
        Returns:
            Model name or None if not found
        """
        if not self.chat_history:
            return None
            
        # Find the last model entry
        for entry in reversed(self.chat_history):
            if "model" in entry:
                return entry["model"]
                
        return None
        
    def generate_reflection(self, reflection_path: str = "data/reflections/session_reflections.json") -> Dict[str, Any]:
        """
        Generate a reflection on the current chat session
        
        Args:
            reflection_path: Path to save the reflection
            
        Returns:
            Reflection data dictionary
        """
        reflection = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": []
        }
        
        # Get recent exchanges
        recent_exchanges = self.chat_history[-min(5, len(self.chat_history)):]
        
        # Summarize exchanges
        for entry in recent_exchanges:
            if entry["role"] == "user":
                reflection["summary"].append(f"User asked: {entry['content']}")
            else:
                content_preview = entry['content'][:150] + "..." if len(entry['content']) > 150 else entry['content']
                reflection["summary"].append(f"Assistant responded: {content_preview}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(reflection_path), exist_ok=True)
            
            # Load existing reflections if any
            existing_reflections = []
            if os.path.exists(reflection_path):
                try:
                    with open(reflection_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():
                            # Handle trailing comma if present
                            if content.strip().endswith(','):
                                content = f"[{content.strip()[:-1]}]"
                            else:
                                content = f"[{content}]"
                            existing_reflections = json.loads(content)
                except:
                    # If there's an issue with the file format, start fresh
                    existing_reflections = []
            
            # Append new reflection
            existing_reflections.append(reflection)
            
            # Save reflections
            with open(reflection_path, 'w', encoding='utf-8') as f:
                json.dump(existing_reflections, f, indent=2)
                
            self.log(f"[Reflection] Saved to {reflection_path}")
            return reflection
        except Exception as e:
            self.log(f"[Reflection Error] Failed to save reflection: {e}")
            return reflection