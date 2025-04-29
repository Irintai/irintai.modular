import tkinter
import customtkinter
import requests
import json
import threading
import queue  # For thread-safe communication
import time
import os
import datetime
import logging
from tkinter import filedialog

# Import configuration settings
import config
from model_manager import ModelManager, ModelBrowserDialog

# --- Set up logging ---
if config.LOGGING_ENABLED:
    log_level = getattr(logging, config.LOGGING_LEVEL)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("ollama_gui.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("OllamaGUI")
    logger.info("Starting Ollama Desktop GUI")

# --- Ensure upload directory exists ---
if not os.path.exists(config.UPLOAD_DIR):
    os.makedirs(config.UPLOAD_DIR)
    if config.LOGGING_ENABLED:
        logger.info(f"Created upload directory: {config.UPLOAD_DIR}")

# --- Main Application Class ---
class OllamaGUI(customtkinter.CTk):
    """
    Main application class for the Ollama Desktop GUI.
    Provides a graphical interface for interacting with Ollama models.
    """
    def __init__(self):
        """Initialize the application window and set up the UI components."""
        super().__init__()

        # --- Window Setup ---
        self.title(config.APP_TITLE)
        self.geometry(config.INITIAL_WINDOW_SIZE)
        customtkinter.set_appearance_mode(config.APPEARANCE_MODE)
        customtkinter.set_default_color_theme(config.COLOR_THEME)

        # Initialize model manager
        self.model_manager = ModelManager(config.OLLAMA_BASE_URL)

        # --- Internal State ---
        self.models = []
        self.selected_model = tkinter.StringVar(value="Select Model")
        self.is_generating = False
        self.response_queue = queue.Queue()  # Queue for thread communication
        self.active_request = None  # Reference to the active request for cancellation
        self.conversations = []  # Store conversation history
        self.current_conversation = []  # Current active conversation
        self.selected_file = None  # Currently selected file for upload
        
        # Model parameters
        self.temperature = tkinter.DoubleVar(value=config.DEFAULT_TEMPERATURE)
        self.max_tokens = tkinter.IntVar(value=config.DEFAULT_MAX_TOKENS)
        self.top_p = tkinter.DoubleVar(value=config.DEFAULT_ADDITIONAL_SETTINGS["top_p"])
        self.frequency_penalty = tkinter.DoubleVar(value=config.DEFAULT_ADDITIONAL_SETTINGS["frequency_penalty"])
        self.presence_penalty = tkinter.DoubleVar(value=config.DEFAULT_ADDITIONAL_SETTINGS["presence_penalty"])
        self.context_length = tkinter.IntVar(value=config.DEFAULT_CONTEXT_LIMIT)
        self.output_token_length = tkinter.IntVar(value=config.DEFAULT_OUTPUT_TOKEN_LENGTH)

        # --- Create Menu Bar ---
        self.create_menu_bar()

        # --- Create Main Layout ---
        self.create_layout()

        # --- Initialization ---
        self.fetch_models_async()
        self.after(100, self.process_response_queue)  # Start checking the queue
        
        if config.LOGGING_ENABLED:
            logger.info("GUI initialized")

    def create_menu_bar(self):
        """Create the application's menu bar with File and Settings options."""
        menubar = tkinter.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tkinter.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Conversation", command=self.new_conversation)
        file_menu.add_command(label="Save Conversation", command=self.save_conversation)
        file_menu.add_command(label="Upload File", command=self.upload_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Models menu
        models_menu = tkinter.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Models", menu=models_menu)
        models_menu.add_command(label="Browse & Download Models", command=self.open_model_browser)
        models_menu.add_command(label="Refresh Local Models", command=self.refresh_models)
        
        # Settings menu
        settings_menu = tkinter.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Model Parameters", command=self.open_model_settings)
        settings_menu.add_command(label="Appearance", command=self.open_appearance_settings)
        
        # Help menu
        help_menu = tkinter.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        if config.LOGGING_ENABLED:
            logger.debug("Menu bar created")

    def refresh_models(self):
        """Refresh the list of local models."""
        # Clear the current model list
        self.models = []
        self.model_menu.configure(values=["Fetching models..."])
        self.selected_model.set("Fetching models...")
        
        # Fetch models again
        self.fetch_models_async()
    
    if config.LOGGING_ENABLED:
        logger.info("Refreshing model list")

    def create_layout(self):
        """Create the main application layout with all UI components."""
        # --- Layout Configuration ---
        self.grid_rowconfigure(0, weight=1)  # Chat area expands
        self.grid_rowconfigure(1, weight=0)  # Input area fixed
        self.grid_columnconfigure(0, weight=1)

        # --- Top Frame (Model Selection & Chat History) ---
        self.top_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.top_frame.grid(row=0, column=0, sticky="nsew")
        self.top_frame.grid_rowconfigure(1, weight=1)  # Textbox row expands
        self.top_frame.grid_columnconfigure(0, weight=1)

        # Control Bar (Model Selection)
        self.control_bar = customtkinter.CTkFrame(self.top_frame)
        self.control_bar.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.control_bar.grid_columnconfigure(0, weight=1)

        # Control Bar (Model Selection)
        self.control_bar = customtkinter.CTkFrame(self.top_frame)
        self.control_bar.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.control_bar.grid_columnconfigure(0, weight=1)

        # Model Selection Dropdown
        self.model_menu = customtkinter.CTkOptionMenu(
            self.control_bar,
            variable=self.selected_model,
            values=["Fetching models..."],
            command=self.on_model_select
        )
        self.model_menu.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        self.model_menu.set("Fetching models...")  # Initial state

        # Browse Models Button
        self.browse_button = customtkinter.CTkButton(
            self.control_bar,
            text="Browse",
            width=70,
            command=self.open_model_browser
        )
        self.browse_button.grid(row=0, column=1, padx=(0, 10), pady=0)

        # Settings Button
        self.settings_button = customtkinter.CTkButton(
            self.control_bar,
            text="⚙️",
            width=30,
            command=self.open_model_settings
        )
        self.settings_button.grid(row=0, column=2, padx=0, pady=0)

        # Upload Button
        self.upload_button = customtkinter.CTkButton(
            self.control_bar,
            text="📁",
            width=30,
            command=self.upload_file
        )
        self.upload_button.grid(row=0, column=3, padx=(10, 0), pady=0)

        # Chat History Frame
        self.chat_frame = customtkinter.CTkFrame(self.top_frame)
        self.chat_frame.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        
        # Chat History Textbox
        self.chat_history = customtkinter.CTkTextbox(
            self.chat_frame,
            wrap=tkinter.WORD,  # Wrap text at word boundaries
            state="disabled"    # Start as read-only
        )
        self.chat_history.grid(row=0, column=0, sticky="nsew")
        
        # Configure tags for styling user/model messages
        self.chat_history.tag_config("user", foreground="blue")
        self.chat_history.tag_config("model", foreground="#006400")  # Dark Green
        self.chat_history.tag_config("error", foreground="red")
        self.chat_history.tag_config("system", foreground="gray")
        self.chat_history.tag_config("file", foreground="purple")

        # --- Bottom Frame (Input & Send Button) ---
        self.input_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)  # Entry expands

        # File indicator label
        self.file_label = customtkinter.CTkLabel(
            self.input_frame,
            text="",
            text_color="purple",
        )
        self.file_label.grid(row=0, column=0, padx=(0, 10), pady=(0, 5), sticky="w")

        # Prompt Entry Field
        self.prompt_entry = customtkinter.CTkEntry(
            self.input_frame,
            placeholder_text="Enter your prompt here..."
        )
        self.prompt_entry.grid(row=1, column=0, padx=(0, 10), pady=0, sticky="ew")
        self.prompt_entry.bind("<Return>", self.send_prompt_event)  # Bind Enter key

        # Send Button
        self.send_button = customtkinter.CTkButton(
            self.input_frame,
            text="Send",
            command=self.send_prompt_event
        )
        self.send_button.grid(row=1, column=1, padx=0, pady=0)

        # Cancel Button (hidden initially)
        self.cancel_button = customtkinter.CTkButton(
            self.input_frame,
            text="Cancel",
            fg_color="darkred",
            command=self.cancel_generation,
            state="disabled"
        )
        # Not added to grid initially - will be shown during generation
        
        if config.LOGGING_ENABLED:
            logger.debug("Main layout created")

    # --- Appearance Settings Dialog ---
    def open_appearance_settings(self):
        """Open a dialog to configure application appearance."""
        settings_window = customtkinter.CTkToplevel(self)
        settings_window.title("Appearance Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self)  # Set to be on top of the main window
        settings_window.grab_set()  # Make window modal
        
        # Appearance mode setting
        appearance_frame = customtkinter.CTkFrame(settings_window)
        appearance_frame.pack(fill="x", padx=20, pady=10)
        
        appearance_label = customtkinter.CTkLabel(appearance_frame, text="Appearance Mode:")
        appearance_label.pack(side="left", padx=10)
        
        # Variable to store the current appearance mode
        appearance_var = tkinter.StringVar(value=customtkinter.get_appearance_mode())
        
        # Function to change appearance mode
        def change_appearance_mode(new_mode):
            customtkinter.set_appearance_mode(new_mode)
            if config.LOGGING_ENABLED:
                logger.info(f"Appearance mode changed to {new_mode}")
        
        # Appearance mode dropdown
        appearance_dropdown = customtkinter.CTkOptionMenu(
            appearance_frame,
            values=["Light", "Dark", "System"],
            variable=appearance_var,
            command=change_appearance_mode
        )
        appearance_dropdown.pack(side="left", padx=10)
        
        # Color theme setting
        theme_frame = customtkinter.CTkFrame(settings_window)
        theme_frame.pack(fill="x", padx=20, pady=10)
        
        theme_label = customtkinter.CTkLabel(theme_frame, text="Color Theme:")
        theme_label.pack(side="left", padx=10)
        
        # Variable to store the current color theme
        theme_var = tkinter.StringVar(value=customtkinter.get_default_color_theme())
        
        # Function to change color theme
        def change_color_theme(new_theme):
            customtkinter.set_default_color_theme(new_theme)
            messagebox = customtkinter.CTkLabel(
                settings_window,
                text="Theme will be applied on restart",
                text_color="orange"
            )
            messagebox.pack(pady=10)
            if config.LOGGING_ENABLED:
                logger.info(f"Color theme changed to {new_theme}")
        
        # Color theme dropdown
        theme_dropdown = customtkinter.CTkOptionMenu(
            theme_frame,
            values=["blue", "green", "dark-blue"],
            variable=theme_var,
            command=change_color_theme
        )
        theme_dropdown.pack(side="left", padx=10)
        
        # Close button
        close_button = customtkinter.CTkButton(
            settings_window, 
            text="Close", 
            command=settings_window.destroy
        )
        close_button.pack(pady=20)
        
        if config.LOGGING_ENABLED:
            logger.debug("Appearance settings dialog opened")

    def open_model_browser(self):
        """Open the model browser dialog."""
        if config.LOGGING_ENABLED:
            logger.info("Opening model browser")
            
        browser = ModelBrowserDialog(self, self.model_manager)
        
    def on_model_browser_select(self, model_name):
        """
        Handle model selection from the model browser.
        
        Args:
            model_name (str): The selected model name
        """
        if config.LOGGING_ENABLED:
            logger.info(f"Model selected from browser: {model_name}")
            
        # Set the selected model
        self.selected_model.set(model_name)
        
        # Update the UI to reflect the selection
        self.add_message("System", f"Model selected: {model_name}\n")

    # --- Model Settings Dialog ---
    def open_model_settings(self):
        """Open a dialog to configure model parameters."""
        settings_window = customtkinter.CTkToplevel(self)
        settings_window.title("Model Parameters")
        settings_window.geometry("500x550")
        settings_window.transient(self)  # Set to be on top of the main window
        settings_window.grab_set()  # Make window modal
        
        # Create a scrollable frame for all settings
        scrollable_frame = customtkinter.CTkScrollableFrame(settings_window)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title label
        title_label = customtkinter.CTkLabel(
            scrollable_frame, 
            text="Model Parameter Settings",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Temperature setting
        self.create_slider_setting(
            scrollable_frame, 
            "Temperature:", 
            "Controls randomness (higher = more creative, lower = more deterministic)",
            self.temperature, 
            0.0, 
            2.0, 
            0.1
        )
        
        # Max tokens setting
        self.create_slider_setting(
            scrollable_frame, 
            "Max Tokens:", 
            "Maximum number of tokens to generate",
            self.max_tokens, 
            256, 
            8192, 
            256,
            is_int=True
        )
        
        # Context length setting
        self.create_slider_setting(
            scrollable_frame, 
            "Context Length:", 
            "Maximum context length for the model",
            self.context_length, 
            1024, 
            8192, 
            1024,
            is_int=True
        )
        
        # Output token length setting
        self.create_slider_setting(
            scrollable_frame, 
            "Default Output Length:", 
            "Default length of generated responses",
            self.output_token_length, 
            50, 
            1000, 
            50,
            is_int=True
        )
        
        # Top P setting
        self.create_slider_setting(
            scrollable_frame, 
            "Top P:", 
            "Nucleus sampling parameter (lower = more focused)",
            self.top_p, 
            0.0, 
            1.0, 
            0.05
        )
        
        # Frequency penalty setting
        self.create_slider_setting(
            scrollable_frame, 
            "Frequency Penalty:", 
            "Penalty for frequent tokens (higher = less repetition)",
            self.frequency_penalty, 
            0.0, 
            2.0, 
            0.1
        )
        
        # Presence penalty setting
        self.create_slider_setting(
            scrollable_frame, 
            "Presence Penalty:", 
            "Penalty for new tokens (higher = more topic changes)",
            self.presence_penalty, 
            0.0, 
            2.0, 
            0.1
        )
        
        # Buttons frame
        buttons_frame = customtkinter.CTkFrame(settings_window)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        # Reset button
        reset_button = customtkinter.CTkButton(
            buttons_frame, 
            text="Reset to Defaults", 
            command=self.reset_model_settings
        )
        reset_button.pack(side="left", padx=10)
        
        # Apply button
        apply_button = customtkinter.CTkButton(
            buttons_frame, 
            text="Apply", 
            command=settings_window.destroy
        )
        apply_button.pack(side="right", padx=10)
        
        if config.LOGGING_ENABLED:
            logger.debug("Model settings dialog opened")
    
    def create_slider_setting(self, parent, label_text, help_text, variable, min_val, max_val, step, is_int=False):
        """Helper method to create a slider setting with label and value display."""
        # Container frame
        frame = customtkinter.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=10)
        
        # Label frame
        label_frame = customtkinter.CTkFrame(frame)
        label_frame.pack(fill="x", pady=5)
        
        # Parameter label
        label = customtkinter.CTkLabel(label_frame, text=label_text, anchor="w")
        label.pack(side="left", padx=10)
        
        # Value display
        if is_int:
            value_text = str(variable.get())
        else:
            value_text = f"{variable.get():.2f}"
            
        value_label = customtkinter.CTkLabel(label_frame, text=value_text)
        value_label.pack(side="right", padx=10)
        
        # Help text
        help_label = customtkinter.CTkLabel(
            frame, 
            text=help_text, 
            font=customtkinter.CTkFont(size=12),
            text_color="gray"
        )
        help_label.pack(fill="x", padx=10, pady=(0, 5))
        
        # Slider
        slider = customtkinter.CTkSlider(
            frame, 
            from_=min_val, 
            to=max_val, 
            variable=variable,
            width=450
        )
        slider.pack(padx=10, pady=5)
        
        # Update value label when slider changes
        def update_value_label(value):
            if is_int:
                value_int = int(float(value))
                variable.set(value_int)
                value_label.configure(text=str(value_int))
            else:
                value_label.configure(text=f"{float(value):.2f}")
        
        slider.configure(command=update_value_label)
        
        return frame
    
    def reset_model_settings(self):
        """Reset all model parameters to their default values."""
        self.temperature.set(config.DEFAULT_TEMPERATURE)
        self.max_tokens.set(config.DEFAULT_MAX_TOKENS)
        self.context_length.set(config.DEFAULT_CONTEXT_LIMIT)
        self.output_token_length.set(config.DEFAULT_OUTPUT_TOKEN_LENGTH)
        self.top_p.set(config.DEFAULT_ADDITIONAL_SETTINGS["top_p"])
        self.frequency_penalty.set(config.DEFAULT_ADDITIONAL_SETTINGS["frequency_penalty"])
        self.presence_penalty.set(config.DEFAULT_ADDITIONAL_SETTINGS["presence_penalty"])
        
        if config.LOGGING_ENABLED:
            logger.info("Model settings reset to defaults")
            
        # Show confirmation
        messagebox = customtkinter.CTkLabel(
            self,
            text="Settings reset to defaults",
            text_color="green"
        )
        messagebox.place(relx=0.5, rely=0.9, anchor="center")
        
        # Remove message after a delay
        self.after(2000, lambda: messagebox.destroy())

    # --- File Upload Handling ---
    def upload_file(self):
        """Open a file dialog to select a file for upload."""
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return  # User canceled
        
        # Get the filename
        filename = os.path.basename(file_path)
        
        # Copy the file to the uploads directory
        destination = os.path.join(config.UPLOAD_DIR, filename)
        
        try:
            # Read the file content
            with open(file_path, 'rb') as source_file:
                file_content = source_file.read()
                
            # Save to destination
            with open(destination, 'wb') as dest_file:
                dest_file.write(file_content)
            
            # Update the UI to show the selected file
            self.selected_file = destination
            self.file_label.configure(text=f"Selected file: {filename}")
            
            # Add message to chat
            self.add_message("System", f"File uploaded: {filename}\n", tag="file")
            
            if config.LOGGING_ENABLED:
                logger.info(f"File uploaded: {filename}")
        
        except Exception as e:
            error_message = f"Error uploading file: {str(e)}\n"
            self.add_message("System", error_message, tag="error")
            
            if config.LOGGING_ENABLED:
                logger.error(f"File upload error: {str(e)}")

    # --- Conversation Management ---
    def new_conversation(self):
        """Start a new conversation, saving the current one to history."""
        if self.current_conversation:
            self.conversations.append(self.current_conversation)
            self.current_conversation = []
            
            # Clear the chat history
            self.chat_history.configure(state="normal")
            self.chat_history.delete("1.0", tkinter.END)
            self.chat_history.configure(state="disabled")
            
            # Clear selected file
            self.selected_file = None
            self.file_label.configure(text="")
            
            self.add_message("System", "Started a new conversation.\n")
            
            if config.LOGGING_ENABLED:
                logger.info("New conversation started")

    def save_conversation(self):
        """Save the current conversation to a file."""
        if not self.current_conversation:
            self.add_message("System", "No conversation to save.\n", tag="error")
            return
            
        # Ask user for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")],
            title="Save Conversation"
        )
        
        if not file_path:
            return  # User canceled
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Ollama Conversation - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write model information if available
                if hasattr(self, 'selected_model') and self.selected_model.get() not in ["Select Model", "Fetching models..."]:
                    f.write(f"Model: {self.selected_model.get()}\n\n")
                
                # Write conversation
                for message in self.current_conversation:
                    if message["sender"] == "User":
                        f.write(f"## User\n\n{message['content']}\n\n")
                    elif message["sender"] == "Model":
                        f.write(f"## Model\n\n{message['content']}\n\n")
                        
            self.add_message("System", f"Conversation saved to {file_path}\n")
            
            if config.LOGGING_ENABLED:
                logger.info(f"Conversation saved to {file_path}")
                
        except Exception as e:
            self.add_message("System", f"Error saving conversation: {e}\n", tag="error")
            
            if config.LOGGING_ENABLED:
                logger.error(f"Error saving conversation: {e}")

    def show_about(self):
        """Show information about the application."""
        about_window = customtkinter.CTkToplevel(self)
        about_window.title("About Ollama Desktop GUI")
        about_window.geometry("400x300")
        about_window.transient(self)
        
        title_label = customtkinter.CTkLabel(
            about_window, 
            text="Ollama Desktop GUI",
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        info_text = (
            "A desktop GUI for Ollama local LLM models.\n\n"
            "Features:\n"
            "- Chat with multiple Ollama models\n"
            "- Adjust model parameters\n"
            "- Save conversations\n"
            "- Upload reference files\n"
            "- Cancel running generations\n\n"
            "Created with Python and CustomTkinter"
        )
        
        info_label = customtkinter.CTkLabel(
            about_window, 
            text=info_text,
            justify="left"
        )
        info_label.pack(padx=20, pady=10)
        
        ok_button = customtkinter.CTkButton(
            about_window, 
            text="OK", 
            command=about_window.destroy
        )
        ok_button.pack(pady=20)
        
        if config.LOGGING_ENABLED:
            logger.debug("About dialog opened")

    # --- Model Handling ---
    def fetch_models_async(self):
        """Fetches models in a separate thread to avoid blocking the GUI."""
        self.add_message("System", "Fetching available Ollama models...\n")
        threading.Thread(target=self._fetch_models_worker, daemon=True).start()

    def _fetch_models_worker(self):
        """Worker function to fetch models from the Ollama API."""
        try:
            response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            self.models = sorted([model['name'] for model in data.get('models', [])])

            if self.models:
                # Schedule GUI update in the main thread
                self.after(0, self.update_model_menu, self.models)
                self.add_message("System", f"Found models: {', '.join(self.models)}\n")
                
                if config.LOGGING_ENABLED:
                    logger.info(f"Found {len(self.models)} models")
            else:
                self.after(0, self.update_model_menu, ["No models found"])
                self.add_message("System", "No Ollama models found. Is Ollama running and have you pulled models (e.g., `ollama pull llama3`)?\n", tag="error")
                
                if config.LOGGING_ENABLED:
                    logger.warning("No Ollama models found")

        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching models: {e}\nIs Ollama running at {config.OLLAMA_BASE_URL}?\n"
            self.add_message("System", error_message, tag="error")
            # Schedule GUI update in the main thread
            self.after(0, self.update_model_menu, ["Error fetching"])
            
            if config.LOGGING_ENABLED:
                logger.error(f"Error fetching models: {e}")
                
        except json.JSONDecodeError:
            error_message = "Error decoding response from Ollama API.\n"
            self.add_message("System", error_message, tag="error")
            self.after(0, self.update_model_menu, ["API Error"])
            
            if config.LOGGING_ENABLED:
                logger.error("Error decoding response from Ollama API")

    def update_model_menu(self, models_list):
        """Updates the model dropdown menu (runs in the main thread)."""
        if models_list:
            self.model_menu.configure(values=models_list)
            if models_list[0] not in ["Error fetching", "No models found", "API Error"]:
                self.selected_model.set(models_list[0])  # Select the first model by default
                self.model_menu.configure(state="normal")
                self.prompt_entry.configure(state="normal")
                self.send_button.configure(state="normal")
            else:
                self.selected_model.set(models_list[0])
                self.model_menu.configure(state="disabled")
                self.prompt_entry.configure(state="disabled")
                self.send_button.configure(state="disabled")
        else:
            self.model_menu.configure(values=["No models available"], state="disabled")
            self.selected_model.set("No models available")
            self.prompt_entry.configure(state="disabled")
            self.send_button.configure(state="disabled")

    def on_model_select(self, selected):
        """Callback when a model is selected."""
        self.add_message("System", f"Model selected: {selected}\n")
        
        if config.LOGGING_ENABLED:
            logger.info(f"Model selected: {selected}")

    # --- Chat Interaction ---
    def add_message(self, sender, message, tag=None):
        """
        Adds a message to the chat history (runs in the main thread).
        
        Args:
            sender (str): The sender of the message ('User', 'Model', or 'System')
            message (str): The message content
            tag (str, optional): Styling tag to apply. Defaults to None.
        """
        # Store message in conversation history
        if sender in ["User", "Model"]:
            self.current_conversation.append({
                "sender": sender,
                "content": message,
                "timestamp": datetime.datetime.now().isoformat()
            })
        
        # Update chat display
        self.chat_history.configure(state="normal")  # Enable editing
        if sender == "User":
            self.chat_history.insert(tkinter.END, f"You: {message}\n\n", "user")
        elif sender == "Model":
            # Append model responses without extra labels if streaming
            self.chat_history.insert(tkinter.END, message, "model")
        elif sender == "System":
            self.chat_history.insert(tkinter.END, f"[System] {message}", tag or "system")
        else:  # Error case from Ollama response etc.
            self.chat_history.insert(tkinter.END, f"[Error] {message}\n", "error")

        self.chat_history.see(tkinter.END)  # Scroll to the bottom
        self.chat_history.configure(state="disabled")  # Disable editing

    def add_model_response_chunk(self, chunk):
        """
        Appends a chunk of the model's streaming response.
        
        Args:
            chunk (str): Text chunk from the model's response
        """
        self.chat_history.configure(state="normal")  # Enable editing
        self.chat_history.insert(tkinter.END, chunk, "model")
        self.chat_history.see(tkinter.END)  # Scroll to the bottom
        self.chat_history.configure(state="disabled")  # Disable editing

    def send_prompt_event(self, event=None):
        """
        Handles sending the prompt when the button is clicked or Enter is pressed.
        
        Args:
            event: The event that triggered this function (optional)
        """
        if self.is_generating:
            return  # Don't send if already generating

        prompt = self.prompt_entry.get().strip()
        model = self.selected_model.get()

        if not prompt:
            self.add_message("System", "Please enter a prompt.\n", tag="error")
            return
        if model in ["Select Model", "Fetching models...", "No models found", "Error fetching", "API Error", "No models available"]:
            self.add_message("System", "Please select a valid model first.\n", tag="error")
            return

        # Display user prompt
        self.add_message("User", prompt)
        self.prompt_entry.delete(0, tkinter.END)  # Clear input field

        # Disable input elements while generating and show cancel button
        self.set_generating_state(True)

        # If a file is selected, include it in the context
        file_content = None
        if self.selected_file and os.path.exists(self.selected_file):
            try:
                with open(self.selected_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                if config.LOGGING_ENABLED:
                    logger.info(f"Including file in context: {os.path.basename(self.selected_file)}")
            except Exception as e:
                self.add_message("System", f"Error reading file: {str(e)}\n", tag="error")
                
                if config.LOGGING_ENABLED:
                    logger.error(f"Error reading file: {str(e)}")

        # Start generation in a background thread
        threading.Thread(
            target=self._generate_worker,
            args=(prompt, model, file_content),
            daemon=True
        ).start()

    def cancel_generation(self):
        """Cancels the current model generation if one is running."""
        if self.is_generating and self.active_request:
            try:
                # Close the active request connection
                self.active_request.close()
                
                # Indicate that cancellation is in progress
                self.cancel_button.configure(text="Canceling...", state="disabled")
                
                # Message will be added when the generation thread finishes
                if config.LOGGING_ENABLED:
                    logger.info("Generation canceled by user")
                    
            except Exception as e:
                self.add_message("System", f"Error canceling generation: {e}\n", tag="error")
                
                if config.LOGGING_ENABLED:
                    logger.error(f"Error canceling generation: {e}")

    def _generate_worker(self, prompt, model, file_content=None):
        """
        Worker function to send prompt to Ollama and handle streaming response.
        
        Args:
            prompt (str): The user's prompt text
            model (str): The selected model name
            file_content (str, optional): Content of the selected file
        """
        url = f"{config.OLLAMA_BASE_URL}/api/generate"
        
        # Prepare the context with file content if available
        full_prompt = prompt
        if file_content:
            full_prompt = f"I'm providing you with the following file content for reference:\n\n```\n{file_content}\n```\n\nNow, here's my question/request:\n\n{prompt}"
        
        # Prepare the payload with all model parameters
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": True,  # Enable streaming
            "options": {
                "temperature": self.temperature.get(),
                "num_predict": self.max_tokens.get(),
                "top_p": self.top_p.get(),
                "frequency_penalty": self.frequency_penalty.get(),
                "presence_penalty": self.presence_penalty.get()
            }
        }

        response_text = ""  # Collect the full response
        first_chunk = True
        canceled = False
        
        if config.LOGGING_ENABLED:
            logger.info(f"Generating response with model {model}")
            logger.debug(f"Parameters: {payload['options']}")
        
        try:
            # Store reference to the request for potential cancellation
            with requests.post(url, json=payload, stream=True, timeout=120) as response:
                self.active_request = response
                response.raise_for_status()  # Check for HTTP errors like 404 or 500

                # Add the initial "Model: " label once
                self.response_queue.put(("label", "Model: "))

                for line in response.iter_lines():
                    # Check if response is closed (due to cancellation)
                    if getattr(response, 'closed', False):
                        canceled = True
                        break
                        
                    if line:
                        try:
                            # Each line is a JSON object
                            data = json.loads(line.decode('utf-8'))
                            response_chunk = data.get("response", "")
                            is_done = data.get("done", False)
                            
                            # Add to complete response
                            response_text += response_chunk

                            # Put the received chunk into the queue for the main thread
                            self.response_queue.put(("chunk", response_chunk))

                            if is_done:
                                self.response_queue.put(("done", "\n\n"))  # Signal completion with newline
                                
                                if config.LOGGING_ENABLED:
                                    logger.info("Generation completed successfully")
                                    
                                break  # Exit loop once done

                        except json.JSONDecodeError:
                            self.response_queue.put(("error", f"Failed to decode JSON line: {line}\n"))
                            
                            if config.LOGGING_ENABLED:
                                logger.error(f"Failed to decode JSON line: {line}")
                                
                            break  # Stop processing on decode error
                        except Exception as e:  # Catch other potential errors during processing
                            self.response_queue.put(("error", f"Error processing stream: {e}\n"))
                            
                            if config.LOGGING_ENABLED:
                                logger.error(f"Error processing stream: {e}")
                                
                            break

        except requests.exceptions.ConnectionError:
            self.response_queue.put(("error", f"Connection Error: Could not connect to Ollama at {config.OLLAMA_BASE_URL}. Is it running?\n"))
            
            if config.LOGGING_ENABLED:
                logger.error(f"Connection Error: Could not connect to Ollama at {config.OLLAMA_BASE_URL}")
                
        except requests.exceptions.Timeout:
            self.response_queue.put(("error", "Request timed out. The model might be taking too long.\n"))
            
            if config.LOGGING_ENABLED:
                logger.error("Request timed out")
                
        except requests.exceptions.RequestException as e:
            self.response_queue.put(("error", f"API Request Error: {e}\n"))
            
            if config.LOGGING_ENABLED:
                logger.error(f"API Request Error: {e}")
                
        finally:
            # Clean up
            self.active_request = None
            
            # Add message about cancellation if needed
            if canceled:
                self.response_queue.put(("error", "Generation was canceled.\n"))
                
                if config.LOGGING_ENABLED:
                    logger.info("Generation was canceled")
            
            # Update conversation history with the complete response if it was generated
            if response_text and not canceled:
                # The first message is already added with the label
                # This full response is stored in the conversation history
                self.current_conversation[-1]["content"] = response_text
            
            # Always signal the main thread that generation is finished, even on error
            self.response_queue.put(("finished", None))

    def process_response_queue(self):
        """Processes items from the response queue in the main GUI thread."""
        try:
            while True:  # Process all available messages in the queue
                message_type, data = self.response_queue.get_nowait()

                if message_type == "label":
                    self.add_message("Model", data)  # Adds "Model: " prefix
                elif message_type == "chunk":
                    self.add_model_response_chunk(data)
                elif message_type == "done":
                    self.add_model_response_chunk(data)  # Add final newline
                    # Don't set generating state to false here, wait for "finished"
                elif message_type == "error":
                    self.add_message("Error", data)
                    # Still wait for "finished" to re-enable UI in case of stream errors
                elif message_type == "finished":
                    self.set_generating_state(False)  # Re-enable UI now

                self.response_queue.task_done()  # Mark task as done

        except queue.Empty:  # No more items in the queue right now
            pass
        finally:
            # Schedule this method to run again after a short delay
            self.after(100, self.process_response_queue)

    def set_generating_state(self, is_generating):
        """
        Enable/disable UI elements based on generation state.
        
        Args:
            is_generating (bool): Whether the model is currently generating a response
        """
        self.is_generating = is_generating
        
        # Show/hide cancel button and adjust input UI
        if is_generating:
            # Disable input controls
            self.prompt_entry.configure(state="disabled")
            self.send_button.configure(text="Generating...", state="disabled")
            self.model_menu.configure(state="disabled")
            self.upload_button.configure(state="disabled")
            
            # Show cancel button
            self.send_button.grid_remove()  # Hide send button
            self.cancel_button.configure(state="normal")
            self.cancel_button.grid(row=1, column=1, padx=0, pady=0)  # Show cancel button
            
            if config.LOGGING_ENABLED:
                logger.debug("UI set to generating state")
                
        else:
            # Re-enable input controls
            self.prompt_entry.configure(state="normal")
            self.send_button.configure(text="Send", state="normal")
            self.upload_button.configure(state="normal")
            
            # Hide cancel button
            self.cancel_button.grid_remove()  # Hide cancel button
            self.send_button.grid(row=1, column=1, padx=0, pady=0)  # Show send button
            
            # Only re-enable model menu if models were successfully loaded
            if self.models and self.selected_model.get() not in ["Error fetching", "No models found"]:
                self.model_menu.configure(state="normal")
                
            # Focus back on the entry field
            self.prompt_entry.focus()
            
            if config.LOGGING_ENABLED:
                logger.debug("UI set to idle state")

# --- Run the Application ---
if __name__ == "__main__":
    app = OllamaGUI()
    app.mainloop()