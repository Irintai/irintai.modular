"""
Fixed implementation of the chat panel UI component for the Irintai assistant

This fixes the issue with the chat window not displaying messages properly by
ensuring the chat console is temporarily set to NORMAL state when inserting text.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import time
from typing import Callable, Optional, Dict, List, Any
import threading
from core.model_manager import MODEL_STATUS

class ChatPanel:
    """Chat interface panel for user interaction with the AI assistant"""

    def __init__(self, parent, chat_engine, logger: Callable, config_manager):
        """
        Initialize the chat panel

        Args:
            parent: Parent widget
            chat_engine: ChatEngine instance
            logger: Logging function
            config_manager: ConfigManager instance
        """
        self.parent = parent
        self.chat_engine = chat_engine
        self.log = logger
        self.config_manager = config_manager

        # Create the main frame
        self.frame = ttk.Frame(parent)

        # Initialize UI components
        self.initialize_ui()

        # Initialize plugin hooks 
        self.initialize_plugin_hooks()

        # Load chat history
        self.load_chat_history()

        # Update status indicators 
        self.update_status_indicators()

        # Set up keyboard shortcuts
        self.attach_keyboard_shortcuts()
        
    def initialize_ui(self):
        """Initialize the UI components"""
        # System prompt section
        self.create_system_prompt_section()
        
        # Chat console section
        self.create_chat_console()
        
        # Input section
        self.create_input_section()
        
        # Timeline section
        self.create_timeline_section()
        
    def create_system_prompt_section(self):
        """Create the system prompt input section"""
        # Implementation as in original file
        pass
        
    def create_chat_console(self):
        """Create the chat console display area"""
        chat_frame = ttk.Frame(self.frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a labeled frame for the chat window
        chat_label_frame = ttk.LabelFrame(chat_frame, text="Chat Window")
        chat_label_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the console with better styling
        self.console = scrolledtext.ScrolledText(
            chat_label_frame, 
            wrap=tk.WORD, 
            font=("Helvetica", 10),
            width=80,
            height=20
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for better formatting
        self.console.tag_configure(
            "user", 
            foreground="#000080", 
            font=("Helvetica", 10, "bold")
        )
        self.console.tag_configure(
            "irintai", 
            foreground="#800000", 
            font=("Helvetica", 10, "bold")
        )
        self.console.tag_configure(
            "user_message", 
            foreground="#000000", 
            lmargin1=20, 
            lmargin2=20
        )
        self.console.tag_configure(
            "irintai_message", 
            foreground="#000000", 
            background="#f8f8f8", 
            lmargin1=20, 
            lmargin2=20, 
            rmargin=10
        )
        self.console.tag_configure(
            "system", 
            foreground="#008000", 
            font=("Helvetica", 9, "italic")
        )
        self.console.tag_configure(
            "timestamp", 
            foreground="#888888", 
            font=("Helvetica", 8)
        )
        
        # Make console read-only by default
        self.console.config(state=tk.DISABLED)
        
        # Add filter controls
        filter_frame = ttk.Frame(self.frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="All")
        self.filter_dropdown = ttk.Combobox(
            filter_frame, 
            textvariable=self.filter_var,
            values=["All", "User", "Irintai", "System"],
            state="readonly",
            width=10
        )
        self.filter_dropdown.pack(side=tk.LEFT, padx=5)
        self.filter_dropdown.bind("<<ComboboxSelected>>", self.apply_filter)
        
        # Add clear button
        ttk.Button(
            filter_frame, 
            text="Clear Console", 
            command=self.clear_console
        ).pack(side=tk.RIGHT, padx=5)
        
        # Add save button
        ttk.Button(
            filter_frame, 
            text="Save Conversation", 
            command=self.save_conversation
        ).pack(side=tk.RIGHT, padx=5)
        
    def create_input_section(self):
        """Create the user input section"""
        # Implementation as in original file
        pass
        
    def create_timeline_section(self):
        """Create the conversation timeline"""
        # Implementation as in original file
        pass
        
    def display_user_message(self, content, timestamp=None):
        """
        Display a user message in the console
        
        Args:
            content: Message content
            timestamp: Optional timestamp
        """
        if not timestamp:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
        # Enable text insertion
        self.console.config(state=tk.NORMAL)
            
        # Add timestamp
        self.console.insert(
            tk.END,
            f"[{timestamp}] ",
            "timestamp"
        )
        
        # Add user header
        self.console.insert(
            tk.END,
            "[User] ",
            "user"
        )
        
        # Add message content
        self.console.insert(
            tk.END,
            f"{content}\n\n",
            "user_message"
        )
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
        
        # Scroll to end
        self.console.see(tk.END)
        
    def display_assistant_message(self, content, timestamp=None):
        """
        Display an assistant message in the console
        
        Args:
            content: Message content
            timestamp: Optional timestamp
        """
        if not timestamp:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
        # Process content through plugin hooks if available
        if hasattr(self, 'process_message_hooks'):
            processed_content = self.process_message_hooks(content, "assistant")
        else:
            processed_content = content
        
        # Enable text insertion
        self.console.config(state=tk.NORMAL)
            
        # Add timestamp
        self.console.insert(
            tk.END,
            f"[{timestamp}] ",
            "timestamp"
        )
        
        # Add assistant header
        self.console.insert(
            tk.END,
            "[Irintai] ",
            "irintai"
        )
        
        # Add message content
        self.console.insert(
            tk.END,
            f"{processed_content}\n\n",
            "irintai_message"
        )
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
        
        # Scroll to end
        self.console.see(tk.END)
        
    def load_chat_history(self):
        """Load and display chat history"""
        # First make console editable
        self.console.config(state=tk.NORMAL)
        
        # Clear the console first
        self.console.delete(1.0, tk.END)
        
        # Get history from chat engine
        history = self.chat_engine.chat_history
        
        # Display the history
        for message in history:
            role = message.get("role", "")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            if role == "user":
                self.display_user_message(content, timestamp)
            elif role == "assistant":
                self.display_assistant_message(content, timestamp)
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
                
        # Update timeline
        if hasattr(self, 'update_timeline'):
            self.update_timeline()
            
    def clear_console(self):
        """Clear the console display"""
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)
        self.log("[Chat] Console cleared")
