# IrintAI Assistant

A local-first AI assistant for chat interactions, vector memory, and knowledge management.

![Irintai Logo](resources/icons/irintai_logo.png)

## Overview

IrintAI Assistant is a desktop application that provides an interface for interacting with local AI language models through Ollama. It features a chat interface, vector-based memory system, plugin support, and comprehensive model management capabilities—all while keeping your data private and on your own hardware.

## Features

- **Local-First**: Runs entirely on your computer with no data sent to external servers
- **Chat Interface**: Clean, intuitive interface for conversations with AI models
- **Vector Memory**: Store and retrieve documents with semantic search capabilities
- **Model Management**: Download, manage, and switch between different AI models
- **Plugin System**: Extend functionality with modular plugins (including advanced UI plugins)
- **System Configuration**: Comprehensive settings for customizing behavior
- **Performance Monitoring**: Real-time monitoring of system resources
- **Configurable Prompting**: System prompts, memory usage, and more

## Requirements

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running
- Required Python packages (see `requirements.txt`)
  - Includes: `customtkinter`, `pymupdf`, `pytesseract`, `pillow`, and more
- Sufficient disk space for AI models (varies by model, typically 4GB-15GB per model)
- GPU recommended but not required
- For OCR features: [Tesseract OCR engine](https://github.com/UB-Mannheim/tesseract/wiki) (see USAGE_GUIDE.md)

## Installation

1. Clone the repository:
   ```powershell
   git clone https://github.com/irintai/irintai.git
   cd irintai
   ```

2. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```

   > If you plan to use OCR features (PDF/image text extraction), you must also install the Tesseract OCR engine separately. See [USAGE_GUIDE.md](docs/USAGE_GUIDE.md) for details.

3. Install Ollama following the instructions at [ollama.ai](https://ollama.ai)

4. Run the application:
   ```powershell
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
# Irintai Assistant Project Structure

irintai/
│
├── irintai.py                    # Main entry point
│
├── core/                         # Core functionality
│   ├── __init__.py
│   ├── model_manager.py          # Ollama model management
│   ├── chat_engine.py            # Conversation logic
│   ├── memory_system.py          # Embedding and retrieval logic
│   ├── config_manager.py         # Application settings management
│   ├── plugin_manager.py         # Plugin discovery and management
│   └── plugin_sdk.py             # Plugin development SDK
│
├── ui/                           # UI components
│   ├── __init__.py
│   ├── main_window.py            # Main application window
│   ├── chat_panel.py             # Chat display and interaction
│   ├── model_panel.py            # Model management UI
│   ├── memory_panel.py           # Memory and embedding UI
│   ├── config_panel.py           # Configuration UI
│   ├── plugin_panel.py           # Plugin management interface
│   ├── plugin_config_panel.py    # Plugin configuration 
│   ├── resource_monitor_panel.py # System resource monitoring
│   └── log_viewer.py             # Enhanced log viewer
│
├── utils/                        # Utility functions
│   ├── __init__.py
│   ├── logger.py                 # Enhanced logging functionality
│   ├── system_monitor.py         # System monitoring utilities
│   ├── file_ops.py               # File operations helpers
│   ├── plugin_event_bus.py       # Plugin communication system
│   ├── plugin_dependency_manager.py # Plugin dependency handling
│   └── ollama_hub_integrator.py  # Ollama integration utilities
│
├── plugins/                      # Plugin directory
│   ├── ollama_hub/               # Ollama Hub integration plugin
│   ├── model_training_performance/ # Model performance plugin
│   ├── network_monitoring/       # Network monitoring plugin
│   └── personality_plugin/       # Personality customization
│
├── diagnostics/                  # Diagnostic tools
│   ├── enhanced_diagnostics.py   # System diagnostic utility
│   └── ollama_panel_diagnostic.py # Ollama-specific diagnostics
│
├── data/                         # Data storage
│   ├── models/                   # Default model storage location
│   ├── logs/                     # Log files
│   ├── plugins/                  # Plugin configurations
│   ├── reflections/              # Session reflections
│   └── vector_store/             # Vector embeddings
│
└── docs/                         # Documentation
    ├── README.md                 # This file
    ├── USAGE_GUIDE.md            # Detailed usage instructions
    ├── TROUBLESHOOTING.md        # Troubleshooting information
    ├── plugin_api.md             # Plugin development guide
    └── resources/                # Documentation resources
```

## Memory System

Irintai includes a vector-based memory system that allows the AI to recall information from documents. Available modes:

- **Off**: No memory used
- **Manual**: Look up information manually
- **Auto**: Automatically add context to prompts
- **Background**: Silently add context to all prompts

## Troubleshooting

Irintai Assistant includes robust diagnostic tools to help identify and resolve issues:

- **Run diagnostics**: `python enhanced_diagnostics.py` for comprehensive system checks
- **Auto-repair**: `python fix_plugin_manager.py` to fix common plugin issues
- **Runtime protection**: Automatic error prevention for missing attributes

For detailed troubleshooting guidance, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Common Issues

1. **Model won't start**: 
   - Ensure Ollama is running
   - Check available disk space
   - Try using 8-bit mode for larger models

2. **Memory search not working**:
   - Ensure documents are loaded 
   - Check if memory mode is enabled
   - Verify the index file exists

3. **Plugin or threading errors**:
   - Run enhanced diagnostics to identify and fix issues
   - Check logs for specific error messages
   - Verify plugin manifest files exist and are valid

4. **Performance issues**:
   - Monitor resource usage in dashboard
   - Try smaller models if on limited hardware
   - Enable 8-bit mode for large models

### Logs

Logs are stored in `data/logs/` and can be viewed within the application by clicking "View Logs" in the toolbar. The diagnostic tools can automatically analyze these logs to identify recurring issues.

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
