# Irintai Assistant

A local-first AI assistant for chat interactions, vector memory, and knowledge management.

![Irintai Logo](resources/icons/irintai_logo.png)

## Overview

Irintai Assistant is a desktop application that provides an interface for interacting with local AI language models through Ollama. It features a chat interface, vector-based memory system, and comprehensive model management capabilities - all while keeping your data private and on your own hardware.

## Features

- **Local-First**: Runs entirely on your computer with no data sent to external servers
- **Chat Interface**: Clean, intuitive interface for conversations with AI models
- **Vector Memory**: Store and retrieve documents with semantic search capabilities
- **Model Management**: Download, manage, and switch between different AI models
- **System Configuration**: Comprehensive settings for customizing behavior
- **Performance Monitoring**: Real-time monitoring of system resources
- **Configurable Prompting**: System prompts, memory usage, and more

## Requirements

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running
- Required Python packages (see `requirements.txt`)
- Sufficient disk space for AI models (varies by model, typically 4GB-15GB per model)
- GPU recommended but not required

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/irintai.git
   cd irintai
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Install Ollama following the instructions at [ollama.ai](https://ollama.ai)

4. Run the application:
   ```
   python irintai.py
   ```

## Quick Start

1. Start the application with `python irintai.py`
2. Select a model from the "Models" tab (install one if none are available)
3. Click "Start Model" to load the selected model
4. Begin chatting in the "Chat" tab
5. Load documents into memory using the "Memory" tab for context-aware responses

## Configuration

The application can be configured through the Settings tab or by editing `data/config.json`. Some key settings:

- **Model Path**: Where to store AI models
- **Memory Mode**: How context from vector memory should be used
- **System Prompt**: Default instructions for the AI assistant 
- **8-bit Mode**: Enable for reduced memory usage with larger models

## Project Structure

```
# Irintai: Refactored Project Structure

```
irintai/
│
├── irintai.py                  # Main entry point
│
├── core/                       # Core functionality
│   ├── __init__.py
│   ├── model_manager.py        # Ollama model management
│   ├── chat_engine.py          # Conversation logic
│   ├── memory_system.py        # Embedding and retrieval logic
│   └── config_manager.py       # Application settings management
│
├── ui/                         # UI components
│   ├── __init__.py
│   ├── main_window.py          # Main application window
│   ├── chat_panel.py           # Chat display and interaction
│   ├── model_panel.py          # Model management UI
│   ├── memory_panel.py         # Memory and embedding UI
│   ├── config_panel.py         # Configuration UI
│   └── log_viewer.py           # Enhanced log viewer
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── logger.py               # Enhanced logging functionality
│   ├── system_info.py          # System monitoring utilities
│   └── file_ops.py             # File operations helpers
│
├── data/                       # Data storage
│   ├── models/                 # Default model storage location
│   ├── logs/                   # Log files
│   ├── reflections/            # Session reflections
│   └── vector_store/           # Vector embeddings
│
└── resources/                  # Application resources
    ├── presets/                # System prompt presets
    └── icons/                  # UI icons
```

## Memory System

Irintai includes a vector-based memory system that allows the AI to recall information from documents. Available modes:

- **Off**: No memory used
- **Manual**: Look up information manually
- **Auto**: Automatically add context to prompts
- **Background**: Silently add context to all prompts

## Troubleshooting

### Common Issues

1. **Model won't start**: 
   - Ensure Ollama is running
   - Check available disk space
   - Try using 8-bit mode for larger models

2. **Memory search not working**:
   - Ensure documents are loaded 
   - Check if memory mode is enabled
   - Verify the index file exists

3. **Performance issues**:
   - Monitor resource usage in dashboard
   - Try smaller models if on limited hardware
   - Enable 8-bit mode for large models

### Logs

Logs are stored in `data/logs/` and can be viewed within the application by clicking "View Logs" in the toolbar.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Ollama](https://ollama.ai/) for the local model serving capabilities
- [Sentence Transformers](https://www.sbert.net/) for embedding functionality
- All the awesome open-source language models that make local AI possible
