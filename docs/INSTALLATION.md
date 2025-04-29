# Installation Guide

This guide provides detailed instructions for installing and setting up the Irintai Assistant.

## System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+ recommended)
- **Python**: Version 3.8 or higher
- **RAM**: Minimum 8GB (16GB+ recommended for larger models)
- **Disk Space**: 
  - Application: ~100MB
  - Models: 4GB-15GB per model (varies by model size)
  - Vector store: Depends on number and size of documents indexed
- **GPU**: Optional but recommended for better performance
  - NVIDIA GPU with CUDA support for optimal performance
  - At least 6GB VRAM for running larger models

## Prerequisites

### 1. Install Python

If you don't have Python 3.8+ installed:

#### Windows
1. Download the installer from the [Python website](https://www.python.org/downloads/)
2. Run the installer and check "Add Python to PATH"
3. Complete the installation

#### macOS
1. Install using Homebrew:
   ```
   brew install python
   ```
   
#### Linux
1. Most distributions come with Python pre-installed
2. If not, install it using your package manager:
   ```
   sudo apt update
   sudo apt install python3 python3-pip
   ```

### 2. Install Ollama

Ollama is required for running the language models.

1. Download and install Ollama from the [official website](https://ollama.ai/download)
2. Follow the installation instructions for your platform
3. Verify Ollama is installed by running in a terminal/command prompt:
   ```
   ollama --version
   ```

## Installation Steps

### Option 1: From Source

1. Clone the repository:
   ```
   git clone https://github.com/Irintai/irintai.modular
   cd irintai
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Option 2: Using pip (if available)

```
pip install irintai
```

## First-Time Setup

1. Start the Ollama service:
   - Windows: Ollama should start automatically after installation
   - macOS: Ollama should start automatically after installation
   - Linux: Run `ollama serve` in a terminal

2. Launch Irintai:
   - If installed from source: `python irintai.py`
   - If installed with pip: `irintai`

3. Initial Configuration:
   - On first launch, the application will create necessary directories
   - Default settings will be applied

4. Install a Model:
   - Go to the "Models" tab
   - Select a model from the list (recommended for first-time: "mistral:7b-instruct")
   - Click "Install Model"
   - Wait for the download to complete

5. Start the Model:
   - With your model selected, click "Start Model"
   - Once the model is running, you can begin chatting

## Configuration

### Environment Variables

The following environment variables can be set to customize Irintai's behavior:

- `OLLAMA_MODELS`: Path to store models (can also be set in the application)
- `OLLAMA_HOME`: Ollama home directory

### Data Locations

By default, Irintai creates the following directory structure for data:

```
data/
├── models/          # AI model storage
├── logs/            # Application logs
├── vector_store/    # Vector embeddings
└── reflections/     # Session reflections
```

## Updating

If you installed from source:

```
git pull
pip install -r requirements.txt
```

If you installed with pip:

```
pip install --upgrade irintai
```

## Troubleshooting Installation

### Common Issues

1. **"Command not found" when running Ollama**
   - Ensure Ollama is properly installed
   - Check that it's in your system PATH

2. **"No module named X" errors**
   - Ensure you've installed all dependencies:
     ```
     pip install -r requirements.txt
     ```
   - Verify you're using the correct Python environment

3. **Permissions issues with model directory**
   - Ensure your user has write permissions to the model directory
   - On Linux/macOS, you might need to:
     ```
     chmod -R 755 data/models
     ```

4. **Ollama connection errors**
   - Verify Ollama is running:
     ```
     ollama list
     ```
   - If not running, start it:
     ```
     ollama serve
     ```

### Getting Help

If you encounter issues not covered here:

1. Check the application logs in `data/logs/`
2. Report issues on the GitHub repository
3. Check the Ollama documentation for model-specific issues

## Verifying Installation

After installation, you can verify that everything is set up correctly using the built-in diagnostic tools:

1. Run the basic diagnostic check:
   ```
   python diagnostics.py
   ```

2. For a more comprehensive check of all systems including plugins:
   ```
   python enhanced_diagnostics.py
   ```

These tools will check for any issues with your installation, configuration, dependencies, and plugin system. If any problems are found, they will provide guidance on how to fix them.

## Required Dependencies

Irintai Assistant requires several Python packages for full functionality, including advanced UI and plugin features. All dependencies are listed in `requirements.txt` and can be installed with:

```powershell
pip install -r requirements.txt
```

**Key dependencies include:**
- `sentence-transformers`, `torch`, `numpy` (vector and model operations)
- `psutil` (system monitoring)
- `python-docx`, `PyPDF2`, `pymupdf` (document processing)
- `pillow`, `pytesseract` (image processing and OCR)
- `customtkinter`, `ttkthemes`, `matplotlib` (UI enhancements)
- `requests`, `loguru`, `scikit-learn` (networking, logging, ML utilities)
- `pytest`, `mypy`, `black` (development/testing)

> **Note:** For OCR features, you must also install the Tesseract OCR engine (see below).

## Additional Setup for OCR Features

To use PDF/image OCR features, you must install the Tesseract OCR engine in addition to the Python packages:

- **Windows:** Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to your PATH
- **Linux:**
  ```sh
  sudo apt install tesseract-ocr
  ```
- **macOS:**
  ```sh
  brew install tesseract
  ```

## Quick Installation Steps

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/Irintai/irintai.modular.git
   cd irintai
   ```
2. **(Recommended) Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install all dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Install Ollama:**
   - Download and install from [ollama.ai](https://ollama.ai/download)
   - Ensure it is running before starting Irintai
5. **(Optional) Install Tesseract OCR engine** if you want OCR features (see above)
6. **Run the application:**
   ```powershell
   python irintai.py
   ```
