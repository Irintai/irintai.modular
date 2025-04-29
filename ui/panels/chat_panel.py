"""
Chat panel UI component for the Irintai assistant
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
        self.system_frame = ttk.Frame(self.frame)
        self.system_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # Add label
        ttk.Label(
            self.system_frame, 
            text="System Prompt:", 
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT)
        
        # Add entry for system prompt
        self.system_prompt_var = tk.StringVar(
            value=self.chat_engine.system_prompt
        )
        self.system_prompt_entry = ttk.Entry(
            self.system_frame, 
            textvariable=self.system_prompt_var, 
            width=70
        )
        self.system_prompt_entry.pack(
            side=tk.LEFT, 
            fill=tk.X, 
            expand=True, 
            padx=5
        )
        
        # Add apply button
        ttk.Button(
            self.system_frame, 
            text="Apply", 
            command=self.apply_system_prompt,
            style="Accent.TButton"
        ).pack(side=tk.LEFT)
        
        # Add presets section
        preset_frame = ttk.Frame(self.frame)
        preset_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(preset_frame, text="Presets:").pack(side=tk.LEFT)
        
        # Load presets from config or use defaults
        self.system_presets = self.config_manager.get(
            "system_presets", 
            [
                "You are Irintai, a helpful and knowledgeable assistant.",
                "You are Irintai, an AI programmer focused on writing clean, efficient code.",
                "You are Irintai, a creative writing assistant specializing in storytelling.",
                "You are Irintai, an academic research assistant with expertise in scholarly analysis.",
                "You are Irintai, a personal coach helping with motivation and productivity."
            ]
        )
        
        # Create preset dropdown
        self.system_preset_var = tk.StringVar()
        self.system_preset_dropdown = ttk.Combobox(
            preset_frame, 
            textvariable=self.system_preset_var, 
            values=self.system_presets,
            width=70,
            state="readonly"
        )
        self.system_preset_dropdown.pack(
            side=tk.LEFT, 
            fill=tk.X, 
            expand=True, 
            padx=5
        )
        self.system_preset_dropdown.bind(
            "<<ComboboxSelected>>", 
            self.on_system_preset_selected
        )
        
        # Add save preset button
        ttk.Button(
            preset_frame, 
            text="Save Current as Preset", 
            command=self.save_system_preset
        ).pack(side=tk.LEFT)
    
    def create_chat_console(self):
        """Create the chat console display area"""
        chat_frame = ttk.Frame(self.frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a labeled frame for the chat console
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
        
        # Make console read-only
        self.console.config(state=tk.DISABLED)
        
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
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Create the input entry
        self.prompt_entry = ttk.Entry(input_frame, font=("Helvetica", 10))
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.prompt_entry.bind("<Return>", self.submit_prompt)
        
        # Add submit button
        self.submit_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.submit_prompt,
            style="Accent.TButton"
        )
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # Add model control buttons
        ttk.Button(
            input_frame,
            text="Start Model",
            command=self.start_model
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            input_frame,
            text="Stop Model",
            command=self.stop_model
        ).pack(side=tk.LEFT, padx=2)
        
        # Add status indicator
        self.status_light = ttk.Label(
            input_frame,
            text="●",
            font=("Helvetica", 14),
            foreground="red"
        )
        self.status_light.pack(side=tk.LEFT, padx=5)
        
    def create_timeline_section(self):
        """Create the conversation timeline"""
        timeline_frame = ttk.Frame(self.frame)
        timeline_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(timeline_frame, text="Timeline:").pack(side=tk.LEFT)
        
        # Create the timeline listbox
        self.timeline_listbox = tk.Listbox(
            timeline_frame,
            height=3,
            font=("Helvetica", 9)
        )
        self.timeline_listbox.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=5
        )
        
        # Add scrollbar
        timeline_scrollbar = ttk.Scrollbar(
            timeline_frame,
            orient="vertical",
            command=self.timeline_listbox.yview
        )
        timeline_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.timeline_listbox.config(yscrollcommand=timeline_scrollbar.set)
        
        # Bind selection event
        self.timeline_listbox.bind(
            "<<ListboxSelect>>",
            self.on_timeline_selected
        )
        
        # Initialize timeline map
        self.timeline_map = {}
        
    def apply_system_prompt(self):
        """Apply the system prompt"""
        system_prompt = self.system_prompt_var.get().strip()
        if not system_prompt:
            return
        
        # Update the chat engine
        self.chat_engine.set_system_prompt(system_prompt)
        
        # Save to config
        self.config_manager.set("system_prompt", system_prompt)
        self.config_manager.save_config()
        
        # Log the change
        self.log(f"[System Prompt] Applied: {system_prompt}")
        
        # Enable text insertion
        self.console.config(state=tk.NORMAL)
        
        # Show in console
        self.console.insert(
            tk.END,
            f"[System] System prompt updated: {system_prompt}\n\n",
            "system"
        )
        self.console.see(tk.END)
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
        
    def on_system_preset_selected(self, event):
        """Handle system prompt preset selection"""
        selected = self.system_preset_var.get()
        if selected:
            self.system_prompt_var.set(selected)
            self.apply_system_prompt()
            
    def save_system_preset(self):
        """Save the current system prompt as a preset"""
        current = self.system_prompt_var.get().strip()
        if not current:
            return
            
        # Add to presets if not already present
        if current not in self.system_presets:
            self.system_presets.append(current)
            self.system_preset_dropdown['values'] = self.system_presets
            
            # Save to config
            self.config_manager.set("system_presets", self.system_presets)
            self.config_manager.save_config()
            
            self.log(f"[System Preset] Saved: {current}")
        else:
            self.log("[System Preset] This preset already exists")
    
    def load_chat_history(self):
        """Load and display chat history"""
        # Enable text insertion
        self.console.config(state=tk.NORMAL)
        
        # Clear the console first
        self.console.delete(1.0, tk.END)
        
        # Make console read-only between operations
        self.console.config(state=tk.DISABLED)
        
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
                
        # Update timeline
        self.update_timeline()

    def update_status_indicators(self): # <<< MODIFY THIS METHOD
        """Update the status indicator based on the model's status."""
        if hasattr(self, 'status_light') and hasattr(self.chat_engine, 'model_manager'):
            model_manager = self.chat_engine.model_manager
            is_running = model_manager.model_process and model_manager.model_process.poll() is None
            current_status = model_manager.model_statuses.get(model_manager.current_model, "Unknown")

            # Use the imported MODEL_STATUS dictionary
            if is_running and current_status == MODEL_STATUS["RUNNING"]:
                self.status_light.config(foreground="green", text="● Running")
            elif current_status == MODEL_STATUS["LOADING"]:
                 self.status_light.config(foreground="orange", text="● Loading")
            elif current_status == MODEL_STATUS["ERROR"]:
                self.status_light.config(foreground="red", text="● Error")
            else:
                self.status_light.config(foreground="red", text="● Stopped")
            self.frame.after(5000, self.update_status_indicators) # Check every 5 seconds

    def attach_keyboard_shortcuts(self): 
        """Attach keyboard shortcuts to the input entry."""

        self.prompt_entry.bind("<Control-Return>", self.submit_prompt)
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
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
    
    def display_assistant_message(self, content, timestamp=None):
        """
        Display an assistant message in the console
        
        Args:
            content: Message content
            timestamp: Optional timestamp
        """
        if not timestamp:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
        # Process content through plugin hooks
        processed_content = self.process_message_hooks(content, "assistant")
        
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
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
        
    def submit_prompt(self, event=None):
        """Submit the user prompt"""
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            return
            
        # Clear the entry
        self.prompt_entry.delete(0, tk.END)
        
        # Display user message
        self.display_user_message(prompt)
        
        # Add to timeline
        self.update_timeline(prompt)
        
        # Disable submit button while processing
        self.submit_button.config(state=tk.DISABLED)
        
        # Send to chat engine
        def on_response(response):
            # Display assistant response
            self.display_assistant_message(response)
            
            # Re-enable submit button
            self.submit_button.config(state=tk.NORMAL)
            
            # Focus on entry
            self.prompt_entry.focus_set()
            
        # Process in a separate thread
        import threading
        threading.Thread(
            target=self._process_prompt,
            args=(prompt, on_response),
            daemon=True
        ).start()
        
    def _process_prompt(self, prompt, callback):
        """
        Process a prompt in a separate thread
        
        Args:
            prompt: Prompt text
            callback: Function to call with response
        """
        # Send to chat engine
        response = self.chat_engine.send_message(prompt)
        
        # Call callback on main thread
        self.frame.after(0, lambda: callback(response))
        
    def update_timeline(self, prompt=None):
        """
        Update the conversation timeline
        
        Args:
            prompt: Optional new prompt to add
        """
        # If a new prompt is provided, add it to the timeline
        if prompt:
            entry = f"{time.strftime('%H:%M')} {prompt[:30]}{'...' if len(prompt) > 30 else ''}"
            self.timeline_listbox.insert(tk.END, entry)
            
            # Store the mapping
            idx = self.timeline_listbox.size() - 1
            self.timeline_map[idx] = prompt
        else:
            # Otherwise, update the entire timeline from chat history
            self.timeline_listbox.delete(0, tk.END)
            self.timeline_map = {}
            
            idx = 0
            for message in self.chat_engine.chat_history:
                if message.get("role") == "user":
                    content = message.get("content", "")
                    timestamp = message.get("timestamp", "").split()[1].split(":")[:2]
                    time_str = ":".join(timestamp)
                    
                    entry = f"{time_str} {content[:30]}{'...' if len(content) > 30 else ''}"
                    self.timeline_listbox.insert(tk.END, entry)
                    
                    # Store the mapping
                    self.timeline_map[idx] = content
                    idx += 1
                    
    def on_timeline_selected(self, event):
        """Handle timeline item selection"""
        selection = event.widget.curselection()
        if not selection:
            return
            
        idx = selection[0]
        if idx in self.timeline_map:
            # Get the prompt
            prompt = self.timeline_map[idx]
            
            # Insert into entry
            self.prompt_entry.delete(0, tk.END)
            self.prompt_entry.insert(0, prompt)
            
            # Focus on entry
            self.prompt_entry.focus_set()
            
    def apply_filter(self, event=None):
        """Apply console filter"""
        filter_type = self.filter_var.get()
        
        # Save current position
        current_pos = self.console.yview()
        
        # Get all text with tags
        text_data = []
        for tag in ["timestamp", "user", "user_message", "irintai", "irintai_message", "system"]:
            tag_ranges = self.console.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start = tag_ranges[i]
                end = tag_ranges[i+1]
                text = self.console.get(start, end)
                text_data.append((tag, start, end, text))
                
        # Clear the console
        self.console.delete(1.0, tk.END)
        
        # Reapply filtered content
        for tag, start, end, text in text_data:
            if filter_type == "All":
                self.console.insert(tk.END, text, tag)
            elif filter_type == "User" and (tag in ["timestamp", "user", "user_message"]):
                self.console.insert(tk.END, text, tag)
            elif filter_type == "Irintai" and (tag in ["timestamp", "irintai", "irintai_message"]):
                self.console.insert(tk.END, text, tag)
            elif filter_type == "System" and tag == "system":
                self.console.insert(tk.END, text, tag)
                
        # Restore view position if not at the end
        if current_pos[1] < 1.0:
            self.console.yview_moveto(current_pos[0])
        else:
            self.console.see(tk.END)
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
    
    def clear_console(self):
        """Clear the console display"""
        # Enable text insertion
        self.console.config(state=tk.NORMAL)
        
        # Clear the console
        self.console.delete(1.0, tk.END)
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
        
        self.log("[Chat] Console cleared")
        
    def save_conversation(self):
        """Save the conversation to a file"""
        from tkinter import filedialog
        import datetime
        
        # Generate default filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"irintai_conversation_{timestamp}.txt"
        
        # Open save dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=default_filename
        )
        
        if not filename:
            return
            
        try:
            # Get console content
            content = self.console.get(1.0, tk.END)
            
            # Save to file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== Irintai Conversation - {datetime.datetime.now()} ===\n\n")
                f.write(content)
                
            self.log(f"[Conversation] Saved to {filename}")
        except Exception as e:
            self.log(f"[Error] Failed to save conversation: {e}")
            
    def start_model(self):
        """Start the selected model"""
        # Get the selected model from the chat engine
        model_name = self.chat_engine.model_manager.current_model
        
        if not model_name:
            # Find the first available model
            for model, status in self.chat_engine.model_manager.model_statuses.items():
                if status == "Installed":
                    model_name = model
                    break
                    
        if not model_name:
            self.log("[Error] No model available to start")
            return
            
        # Start the model
        def on_model_event(event_type, data):
            if event_type == "started":
                self.status_light.config(foreground="green")
            elif event_type == "stopped":
                self.status_light.config(foreground="red")
            elif event_type == "error":
                self.status_light.config(foreground="red")
                
        success = self.chat_engine.model_manager.start_model(model_name, on_model_event)
        
        if success:
            self.log(f"[Model] Starting {model_name}")
            self.console.insert(
                tk.END,
                f"[System] Starting model: {model_name}...\n\n",
                "system"
            )
            self.console.see(tk.END)
            
            # Make console read-only again
            self.console.config(state=tk.DISABLED)
        else:
            self.log(f"[Error] Failed to start model {model_name}")
            
    def stop_model(self):
        """Stop the running model"""
        success = self.chat_engine.model_manager.stop_model()
        
        if success:
            self.status_light.config(foreground="red")
            self.log("[Model] Stopped")
            self.console.insert(
                tk.END,
                "[System] Model stopped.\n\n",
                "system"
            )
            self.console.see(tk.END)
            
            # Make console read-only again
            self.console.config(state=tk.DISABLED)
        else:
            self.log("[Error] Failed to stop model or no model running")
            
    def set_model(self, model_name):
        """
        Set the active model
        
        Args:
            model_name: Name of the model to set
        """
        # Update the model manager
        self.chat_engine.model_manager.current_model = model_name
        
        # Check if the model is running
        if (self.chat_engine.model_manager.model_process and 
            self.chat_engine.model_manager.model_process.poll() is None):
            # Model is running, but it's a different model
            if self.chat_engine.model_manager.current_model != model_name:
                # Stop the current model
                self.chat_engine.model_manager.stop_model()
                
                # Start the new model
                self.start_model()
        else:
            # No model running, show notice
            self.console.insert(
                tk.END,
                f"[System] Model set to {model_name}. Click 'Start Model' to begin.\n\n",
                "system"
            )
            self.console.see(tk.END)
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)

    # Extension point system for the chat panel    
    
    def initialize_plugin_hooks(self):
        """Initialize plugin extension points"""
        # Dictionary of registered UI hooks by plugin ID
        self.plugin_ui_extensions = {}

        # Get the chat frame (original parent of labeled frame containing console)
        chat_frame = self.console.master.master.master  # Go up to the right level
        
        # Store reference to existing widgets for later cleanup
        self.original_chat_widgets = chat_frame.winfo_children()
        
        # Original parent of the console for reference  
        self.original_console_parent = self.console.master
        
        # Instead of modifying the existing hierarchy, create new frames
        # that will be displayed alongside the existing ones
        
        # Create extension frames
        self.extension_frames = {
            "top_bar": ttk.Frame(self.frame),
            "side_panel": ttk.Frame(self.frame),
            "bottom_bar": ttk.Frame(self.frame),
            "floating": None
        }
        
        # Place extension frames in appropriate positions relative to console
        self.extension_frames["top_bar"].pack(in_=self.frame, fill=tk.X, side=tk.TOP, padx=5, pady=5)
        self.extension_frames["side_panel"].pack(in_=self.frame, fill=tk.Y, side=tk.RIGHT, padx=5, pady=5)
        self.extension_frames["bottom_bar"].pack(in_=self.frame, fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)        # Create extension frames
        self.extension_frames = {
            "top_bar": ttk.Frame(self.frame),
            "side_panel": ttk.Frame(self.frame),
            "bottom_bar": ttk.Frame(self.frame),
            "floating": None
        }
        
        # Add extension frames to appropriate places
        self.extension_frames["top_bar"].pack(in_=self.frame, fill=tk.X, side=tk.TOP, padx=5, pady=5)
        self.extension_frames["side_panel"].pack(in_=self.frame, fill=tk.Y, side=tk.RIGHT, padx=5, pady=5)
        self.extension_frames["bottom_bar"].pack(in_=self.frame, fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

        # Register notification methods for plugins
        self.register_plugin_callbacks()

    def register_plugin_callbacks(self):
        """Register plugin notification callbacks with the plugin manager"""
        if not hasattr(self.parent, "plugin_manager"):
            self.log("[Chat Panel] Plugin manager not available")
            return
            
        plugin_manager = self.parent.plugin_manager
        
        # Register for plugin lifecycle events
        plugin_manager.register_event_handler("chat_panel", "plugin_activated", 
                                             self.on_plugin_activated)
        plugin_manager.register_event_handler("chat_panel", "plugin_deactivated", 
                                             self.on_plugin_deactivated)
        plugin_manager.register_event_handler("chat_panel", "plugin_unloaded", 
                                             self.on_plugin_unloaded)

    def on_plugin_activated(self, plugin_id, plugin_instance):
        """
        Handle plugin activation event
        
        Args:
            plugin_id: ID of the activated plugin
            plugin_instance: Instance of the plugin
        """
        # Check if plugin has UI integration capability
        if hasattr(plugin_instance, "get_chat_ui_extension"):
            self.log(f"[Chat Panel] Plugin {plugin_id} has UI integration")
            
            try:
                # Get extension specification from plugin
                extension = plugin_instance.get_chat_ui_extension(self)
                
                if extension and isinstance(extension, dict):
                    # Store extension
                    self.plugin_ui_extensions[plugin_id] = extension
                    
                    # Process UI components
                    self.integrate_plugin_ui(plugin_id, extension)
            except Exception as e:
                self.log(f"[Chat Panel] Error integrating plugin {plugin_id}: {e}")

    def on_plugin_deactivated(self, plugin_id):
        """
        Handle plugin deactivation event
        
        Args:
            plugin_id: ID of the deactivated plugin
        """
        # Remove plugin UI if present
        if plugin_id in self.plugin_ui_extensions:
            self.remove_plugin_ui(plugin_id)

    def on_plugin_unloaded(self, plugin_id):
        """
        Handle plugin unloading event
        
        Args:
            plugin_id: ID of the unloaded plugin
        """
        # Ensure plugin UI is fully removed
        if plugin_id in self.plugin_ui_extensions:
            self.remove_plugin_ui(plugin_id)
            del self.plugin_ui_extensions[plugin_id]    
    
    def integrate_plugin_ui(self, plugin_id, extension):
        """
        Integrate a plugin's UI components
        
        Args:
            plugin_id: ID of the plugin
            extension: UI extension specification
        """
        # Process each extension location
        for location, components in extension.items():
            if location not in self.extension_frames:
                self.log(f"[Chat Panel] Unknown extension location: {location}")
                continue
                
            # Get the container frame
            container = self.extension_frames[location]
            
            # For floating windows, create a new toplevel if needed
            if location == "floating" and components:
                container = tk.Toplevel(self.frame)
                container.title(f"{plugin_id.capitalize()} Plugin")
                container.protocol("WM_DELETE_WINDOW", lambda: self.hide_floating_window(plugin_id))
                container.withdraw()  # Initially hidden
                self.extension_frames["floating"] = container
                
            # Create a frame specific to this plugin
            plugin_frame = ttk.LabelFrame(container, text=extension.get("title", plugin_id.capitalize()))
            plugin_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Store the frame reference
            extension["frame"] = plugin_frame
            
            # Add components if any were specified
            if isinstance(components, list):
                for component in components:
                    if hasattr(component, "pack") and component.master == plugin_frame:
                        # Only pack if the component was created with plugin_frame as parent
                        component.pack(fill=tk.BOTH, expand=True)
                    elif hasattr(component, "pack"):
                        # For components created with a different parent, recreate them
                        self.log(f"[Chat Panel] Component has incorrect parent for {plugin_id}. Skipping.")
                          # Show the container if it was hidden
            if location == "side_panel":
                # Ensure side panel is visible
                self.extension_frames["side_panel"].pack(fill=tk.Y, side=tk.RIGHT, padx=5, pady=5)

    def remove_plugin_ui(self, plugin_id):
        """
        Remove a plugin's UI components
        
        Args:
            plugin_id: ID of the plugin
        """
        extension = self.plugin_ui_extensions.get(plugin_id)
        if not extension:
            return
            
        # Get the plugin frame
        plugin_frame = extension.get("frame")
        if plugin_frame and plugin_frame.winfo_exists():
            plugin_frame.destroy()
            
        # If this was a floating window, destroy it
        if extension.get("location") == "floating" and self.extension_frames["floating"]:
            floating_window = self.extension_frames["floating"]
            if floating_window.winfo_exists():
                floating_window.destroy()
                self.extension_frames["floating"] = None

    def show_floating_window(self, plugin_id):
        """
        Show a plugin's floating window
        
        Args:
            plugin_id: ID of the plugin
        """
        extension = self.plugin_ui_extensions.get(plugin_id)
        if not extension or extension.get("location") != "floating":
            return
            
        # Get the window
        window = self.extension_frames["floating"]
        if window and window.winfo_exists():
            # Position near the main window
            window.geometry(f"+{self.frame.winfo_rootx() + 50}+{self.frame.winfo_rooty() + 50}")
            window.deiconify()
            window.lift()

    def hide_floating_window(self, plugin_id):
        """
        Hide a plugin's floating window
        
        Args:
            plugin_id: ID of the plugin
        """
        extension = self.plugin_ui_extensions.get(plugin_id)
        if not extension or extension.get("location") != "floating":
            return
            
        # Get the window
        window = self.extension_frames["floating"]
        if window and window.winfo_exists():
            window.withdraw()

    # Messages API for plugins to interact with the chat
    def register_message_hook(self, plugin_id, hook_function):
        """
        Register a plugin hook for message processing
        
        Args:
            plugin_id: ID of the plugin
            hook_function: Function to call for message processing
            
        Returns:
            Success flag
        """
        if not hasattr(self, "message_hooks"):
            self.message_hooks = {}
            
        self.message_hooks[plugin_id] = hook_function
        self.log(f"[Chat Panel] Registered message hook for plugin {plugin_id}")
        return True
        
    def unregister_message_hook(self, plugin_id):
        """
        Unregister a plugin message hook
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Success flag
        """
        if hasattr(self, "message_hooks") and plugin_id in self.message_hooks:
            del self.message_hooks[plugin_id]
            self.log(f"[Chat Panel] Unregistered message hook for plugin {plugin_id}")
            return True
        return False
        
    def process_message_hooks(self, message, role):
        """
        Process message hooks from plugins
        
        Args:
            message: Message content
            role: Message role (user/assistant)
            
        Returns:
            Possibly modified message
        """
        if not hasattr(self, "message_hooks") or not self.message_hooks:
            return message
            
        modified_message = message
        
        # Apply each hook in registration order
        for plugin_id, hook_function in self.message_hooks.items():
            try:
                result = hook_function(modified_message, role)
                if result is not None:
                    modified_message = result
            except Exception as e:
                self.log(f"[Chat Panel] Error in message hook for plugin {plugin_id}: {e}")
        
        return modified_message