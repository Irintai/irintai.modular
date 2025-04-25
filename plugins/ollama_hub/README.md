# Ollama Hub Plugin for Irintai Assistant

## Overview

The Ollama Hub plugin provides integration with Ollama, allowing users to browse, download, and manage Ollama models directly from within the Irintai Assistant interface.

## Features

- Browse available models from Ollama Hub
- Download models from Ollama Hub
- Manage your local Ollama models
- Use Ollama models with Irintai Assistant
- Configure advanced model parameters

## Installation

1. Make sure you have Ollama installed and running on your system
   - Default Ollama server runs at http://localhost:11434
   - Visit [Ollama's website](https://ollama.ai) for installation instructions

2. Place the `ollama_hub` directory in your Irintai Assistant's `plugins` folder

3. Restart Irintai Assistant

## Configuration

The plugin can be configured through the Irintai Assistant's plugin settings panel:

- **Server URL**: URL of the Ollama server (default: http://localhost:11434)
- **Auto Connect**: Whether to automatically connect to Ollama server on startup (default: true)

## Usage

1. Open the Irintai Assistant
2. Navigate to the "Models" tab
3. Select the "Ollama Hub" tab
4. Connect to your Ollama server
5. Browse available models:
   - Search by model name or tags
   - Filter by category
6. Download models by selecting them and clicking "Download Model"
7. Use a downloaded model by selecting it and clicking "Use Selected Model"
8. Configure advanced model parameters by clicking "Advanced Options"

## Requirements

- Irintai Assistant 1.0.0 or higher
- Python 3.8 or higher
- Ollama installed and running
- `requests` Python package

## Troubleshooting

**Cannot connect to Ollama server:**
- Ensure Ollama is installed and running
- Check the server URL in the plugin settings
- Verify there are no firewall issues blocking the connection

**Model download fails:**
- Check your internet connection
- Ensure you have sufficient disk space
- Check Ollama server logs for errors

## License

MIT License

## Credits

Developed by the Irintai Team.
