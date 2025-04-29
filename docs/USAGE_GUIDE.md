# Irintai Assistant Usage Guide

This guide provides comprehensive instructions for using the Irintai Assistant application effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Chat Interface](#chat-interface)
3. [Model Management](#model-management)
4. [Memory System](#memory-system)
5. [Plugin System](#plugin-system)
6. [Configuration](#configuration)
7. [Dashboard](#dashboard)
8. [Advanced Features](#advanced-features)
9. [Tips and Best Practices](#tips-and-best-practices)
10. [Installation and Requirements](#installation-and-requirements)

## Getting Started

### Application Layout

The Irintai interface consists of several key sections:

- **Toolbar**: Quick access to common functions
- **Tab Interface**: Contains Chat, Models, Memory, and Settings tabs
- **Status Bar**: Shows current model status and system performance

### Initial Setup

1. Start the application with `python irintai.py`
2. Go to the "Models" tab to install and start a model
3. Return to the "Chat" tab to begin interacting with the assistant

## Chat Interface

### Starting a Conversation

1. Ensure a model is running (status light should be green)
2. Type your message in the input field at the bottom of the Chat tab
3. Press Enter or click "Send" to submit your message

### System Prompts

System prompts provide instructions to the AI about how to behave. To set a system prompt:

1. Enter text in the "System Prompt" field at the top of the chat window
2. Click "Apply" to set the prompt
3. Alternatively, select a preset from the dropdown and it will be applied automatically

### Chat History

- Your conversation history is saved automatically between sessions
- The timeline panel shows recent messages for quick reference
- Click on an item in the timeline to reload that prompt in the input field

### Filtering and Saving

- Use the "Filter" dropdown to view specific message types
- Click "Clear Console" to reset the display (this does not delete history)
- Use "Save Conversation" to export the current conversation to a text file

## Model Management

### Installing Models

1. Go to the "Models" tab
2. Filter models by category or search for specific models
3. Select a model from the list
4. Click "Install Model" to download the selected model
5. Wait for the installation to complete (this may take several minutes depending on model size)

### Starting and Stopping Models

1. Select the model you wish to use
2. Click "Start Model" to load it
3. When finished, click "Stop Model" to free up system resources

### Model Information

The Models tab provides detailed information about each model:

- **Status**: Current state (Installed, Running, Not Installed)
- **Size**: Storage size of the model
- **Context Length**: Maximum context window size
- **Description**: Details about the model's capabilities

### Recommended Models

For beginners, we recommend these models:

- **mistral:7b-instruct**: Good all-around assistant
- **llama3:8b**: Balanced performance and quality
- **phi-2**: Lightweight model for systems with limited resources

## Memory System

### Memory Modes

The Memory system allows the AI to reference loaded documents. Available modes:

- **Off**: No memory context is added to prompts
- **Manual**: Look up information with the search function
- **Auto**: Automatically adds relevant context from documents to your prompts
- **Background**: Silently adds context without showing it in the UI

### Loading Documents

1. Go to the "Memory" tab
2. Click "Load Files" or "Load Folder" to select documents
3. Supported formats include .txt, .md, .py, .pdf, .docx, and more
4. Documents are processed and added to the vector index

### Searching Memory

1. Enter a search query in the "Memory Search" field
2. Click "Search" or press Enter
3. View matching documents and their relevance scores
4. Use this information to form more informed prompts

### Managing Documents

- The document list shows all indexed files
- Select a document to see a preview
- Click "Remove from Index" to delete it from memory
- Use "Clear Index" to remove all documents

## Plugin System

Irintai's plugin system allows you to extend the assistant's functionality with custom modules.

### Accessing Plugins

1. Click on the "Plugins" tab in the main interface
2. The plugin panel contains four tabs:
   - **Local Plugins**: Manage installed plugins
   - **Plugin Marketplace**: Browse and install new plugins
   - **Plugin Sandbox**: Test plugins in an isolated environment
   - **Plugin Settings**: Configure installed plugins

### Managing Local Plugins

1. In the "Local Plugins" tab:
   - View all installed plugins with their status (Active, Loaded, Not Loaded)
   - Select a plugin to see its details
   - Use the action buttons to Load, Activate, Deactivate, or Reload plugins
   
2. Plugin actions:
   - **Load**: Import the plugin code but don't activate it
   - **Activate**: Enable the plugin's functionality
   - **Deactivate**: Disable the plugin temporarily
   - **Reload**: Refresh the plugin code (useful during development)

### Installing New Plugins

1. From the "Plugin Marketplace" tab:
   - Browse available plugins by category
   - Search for specific plugins
   - Select a plugin to view its details
   
2. To install a plugin:
   - Select the plugin in the marketplace
   - Click "Install Plugin"
   - Wait for the installation to complete
   - The plugin will appear in your Local Plugins tab

### Plugin Configuration

1. To configure a plugin:
   - Select the plugin in the Local Plugins tab
   - Click on the "Plugin Settings" tab
   - Adjust the settings specific to that plugin
   - Click "Save Configuration" to apply changes

### Built-in Plugins

Irintai comes with several built-in plugins:

- **Ollama Hub**: Provides integration with the Ollama model repository
- **Model Training Performance**: Monitors and optimizes model performance
- **Network Monitoring**: Tracks network usage and connectivity
- **Personality Plugin**: Allows customization of the assistant's personality

### Creating Your Own Plugins

For developers interested in creating custom plugins:

1. Refer to our [Plugin API Documentation](plugin_api.md)
2. Use the Plugin SDK available in the Irintai codebase
3. Follow our [Plugin Integration Guide](Plugin_integration.md) for best practices

## Configuration

### General Settings

Configure basic application behavior:

- **Theme**: Choose between Light, Dark, or System theme
- **Font Size**: Adjust text size 
- **Auto-start**: Enable/disable automatic model loading on startup
- **Default System Prompt**: Set the default instructions for the AI

### Model Settings

Configure how models are stored and run:

- **Model Path**: Where model files are stored
- **8-bit Mode**: Enable for reduced memory usage with larger models
- **Temperature**: Control randomness in model responses

### Memory Settings

Configure the vector memory system:

- **Memory Mode**: Default memory retrieval mode
- **Index Path**: Where vector indices are stored
- **Embedding Model**: Select the model used for document embeddings

### System Settings

Configure application behavior:

- **Logging**: Set log level and location
- **Startup**: Control application behavior on launch
- **Environment Variables**: Set system variables for better integration

## Dashboard

Access the dashboard by clicking "Dashboard" in the toolbar.

### Overview Tab

Shows a summary of:
- Total interactions
- Current model
- Memory status
- System performance metrics

### Chat Stats Tab

Provides analytics about:
- Message counts
- Response lengths
- Models used
- Session duration

### System Info Tab

Displays detailed information about:
- CPU, RAM, and GPU usage
- Operating system details
- Directory paths
- Process information

### Memory Stats Tab

Shows statistics about:
- Document count
- File types
- Index size
- Recent searches

## Advanced Features

### Log Viewer

Access the log viewer by clicking "View Logs" in the toolbar:

- Filter logs by type
- Search for specific text
- Save logs to a file
- Enable auto-refresh to see real-time updates

### Session Reflections

Generate summaries of your conversations:

1. Click "Generate Reflection" in the toolbar
2. Reflections are saved to `data/reflections/session_reflections.json`
3. These can be useful for reviewing past interactions

### Diagnostics and Troubleshooting

### Using Diagnostic Tools

Irintai Assistant includes powerful diagnostic tools to help identify and resolve issues:

1. **Basic Diagnostics**

   Run the basic diagnostic check to verify your installation and configuration:
   ```powershell
   cd "D:\AI\IrintAI Assistant"
   python diagnostics\enhanced_diagnostics.py --basic
   ```
   
   This checks:
   - Required dependencies
   - Configuration file validity
   - Basic system setup

2. **Enhanced Diagnostics**

   For a comprehensive system check, use:
   ```powershell
   cd "D:\AI\IrintAI Assistant"
   python diagnostics\enhanced_diagnostics.py
   ```
   
   This performs advanced checks:
   - Plugin manager interface validation
   - Missing method detection
   - UI thread safety issues
   - Configuration validation
   - Log analysis
   
   The enhanced diagnostics will generate a report (`irintai_diagnostic_report.txt`) with recommendations.

3. **Ollama Diagnostics**

   For Ollama-specific issues, use:
   ```powershell
   cd "D:\AI\IrintAI Assistant"
   python diagnostics\ollama_panel_diagnostic.py
   ```
   
   This utility helps troubleshoot Ollama connection and configuration issues.

### Handling Plugin Errors

If you encounter issues with specific plugins:

1. Navigate to the **Plugins** tab
2. Select the problematic plugin in the list
3. Check the status and error messages displayed in the information section
4. Click **Reload** to attempt to fix loading issues
5. If problems persist, click **Deactivate** to disable the plugin

Common plugin issues and solutions:

- **Plugin fails to load**: Check that all dependencies are installed
- **Plugin UI not visible**: Try reloading the plugin or restart the application
- **Plugin freezes the UI**: The plugin might be attempting UI updates from a background thread

For persistent issues:
1. Run the enhanced diagnostic tool to identify the root cause
2. Check the application logs in the `data/logs/` directory
3. Look for plugin-specific errors in the log files
4. Consider disabling problematic plugins using `python diagnostics\enhanced_diagnostics.py --disable-plugin plugin_name`

## Tips and Best Practices

### Efficient Model Usage

- Close models when not in use to free up system resources
- For coding tasks, use specialized coding models like codellama or deepseek-coder
- For general chat, smaller models like llama3:8b or mistral:7b offer good performance

### Effective Prompting

- Be specific and clear in your instructions
- Use system prompts to set context for the entire conversation
- For complex tasks, break them down into smaller steps

### Memory Management

- Group related documents when loading them
- Use specific queries when searching memory
- Clear the index periodically to remove outdated information

### Performance Optimization

- Monitor the dashboard to spot performance issues
- Enable 8-bit mode for large models if you have limited GPU memory
- Use CPU mode on systems without a compatible GPU
- Close other resource-intensive applications when using larger models

### Backups

It's a good practice to occasionally back up these directories:

- `data/vector_store/`: Contains your document indices
- `data/config.json`: Contains your settings
- `data/chat_history.json`: Contains your conversation history

## Installation and Requirements

Before using Irintai Assistant, ensure you have installed all required dependencies. These are listed in `requirements.txt` and include:

- sentence-transformers (vector embeddings)
- torch (deep learning backend)
- numpy (array operations)
- psutil (system monitoring)
- python-docx, PyPDF2, pymupdf (document processing)
- pillow, pytesseract (image processing and OCR)
- pyyaml, python-dotenv (configuration)
- customtkinter, ttkthemes, matplotlib (UI enhancements)
- requests (networking)
- loguru (logging)
- scikit-learn (ML utilities)
- pytest, mypy, black (development/testing)

To install all dependencies, run:

```powershell
pip install -r requirements.txt
```

> **Note:**
> - `customtkinter` is required for some plugin UIs (e.g., Ollama Hub). 
> - `pymupdf` (imported as `fitz`) is required for advanced PDF processing.
> - For OCR features, you must also install the Tesseract OCR engine separately (see INSTALLATION.md for details).

For full installation instructions, see [INSTALLATION.md](INSTALLATION.md).
