# Irintai Assistant Usage Guide

This guide provides comprehensive instructions for using the Irintai Assistant application effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Chat Interface](#chat-interface)
3. [Model Management](#model-management)
4. [Memory System](#memory-system)
5. [Configuration](#configuration)
6. [Dashboard](#dashboard)
7. [Advanced Features](#advanced-features)
8. [Tips and Best Practices](#tips-and-best-practices)

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
   python diagnostics.py
   ```
   
   This checks:
   - Required dependencies
   - Configuration file validity
   - Basic system setup

2. **Enhanced Diagnostics**

   For a comprehensive system check, use:
   ```powershell
   python enhanced_diagnostics.py
   ```
   
   This performs advanced checks:
   - Plugin manager interface validation
   - Missing method detection
   - UI thread safety issues
   - Configuration validation
   - Log analysis
   
   The enhanced diagnostics will generate a report (`irintai_diagnostic_report.txt`) with recommendations.

3. **Auto-Repair Tools**

   To automatically fix common plugin issues:
   ```powershell
   python fix_plugin_manager.py
   ```
   
   This repairs common plugin manager problems like missing methods.

### Handling Plugin Errors

If you encounter issues with specific plugins:

1. Navigate to the **Plugins** tab
2. Right-click on the problematic plugin
3. Select **View Log** to see plugin-specific error messages
4. Use **Reload Plugin** to attempt to fix loading issues
5. If problems persist, use **Deactivate Plugin** to disable it

For persistent issues, run the enhanced diagnostic tool to identify the root cause.

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
