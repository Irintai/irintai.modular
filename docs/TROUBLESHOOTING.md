# Irintai Assistant Troubleshooting Guide

This guide provides comprehensive information about diagnosing and fixing issues with your Irintai Assistant installation.

## Diagnostic Tools

Irintai Assistant includes built-in diagnostic tools that can help identify and fix common issues:

### Basic Diagnostics

Run this tool to perform a basic system check:

```powershell
cd "D:\AI\IrintAI Assistant"
python diagnostics\enhanced_diagnostics.py --basic
```

This will check for:
- Required dependencies
- Configuration file validity
- Plugin structure
- Basic file structure integrity
- Python environment compatibility

### Enhanced Diagnostics

For a more comprehensive analysis, use the enhanced diagnostics tool:

```powershell
cd "D:\AI\IrintAI Assistant"
python diagnostics\enhanced_diagnostics.py
```

This advanced tool performs thorough checks including:
- Plugin manager interface validation
- Missing method detection
- Runtime attribute error prevention
- Interface consistency across components
- Log analysis with error pattern detection
- Configuration validation
- Thread safety validation

The enhanced diagnostics will generate a report file (`irintai_diagnostic_report.txt`) that summarizes all findings and provides recommended actions.

### Auto-Repair Tools

The following tools can automatically fix common issues:

1. **Plugin Manager Repair**:
   ```powershell
   python diagnostics\fix_plugin_manager.py
   ```
   Fixes missing methods in the plugin manager, particularly the `set_error_handler` method.

2. **Runtime Attribute Patching**:
   The system includes a runtime patching utility that prevents attribute errors by dynamically adding missing methods when the application starts.

## Common Issues and Solutions

### Application Crashes on Startup

**Symptoms**: Application immediately crashes or shows an error dialog

**Potential Solutions**:
1. Run enhanced diagnostics to identify the root cause: 
   ```powershell
   python diagnostics\enhanced_diagnostics.py
   ```
2. Check for missing plugin methods and other issues in the generated diagnostic report
3. Run the plugin manager repair tool:
   ```powershell
   python diagnostics\fix_plugin_manager.py
   ```
4. Verify your Python version is 3.10 or higher (3.8 minimum, but 3.10+ recommended)
5. Check Python environment dependencies:
   ```powershell
   pip install -r docs\requirements.txt
   ```

### Plugin Loading Failures

**Symptoms**: Plugins fail to load or show error messages in the logs

**Potential Solutions**:
1. Check the plugin structure with:
   ```powershell
   python diagnostics\enhanced_diagnostics.py --plugins-only
   ```
2. Verify that each plugin directory has a valid `manifest.json` file
3. Confirm all plugin dependencies are installed:
   ```powershell
   python diagnostics\plugin_dependency_checker.py plugin_name
   ```
4. Check the logs in `data/logs/` for specific error messages
5. Try to reload the plugin from the Plugin Panel interface:
   - Go to the "Plugins" tab
   - Select the problematic plugin
   - Click "Reload"

### Threading Errors

**Symptoms**: Errors like "RuntimeError: main thread is not in main loop" appear in logs

**Potential Solutions**:
1. These errors typically occur when background threads try to update the UI after the main application has closed
2. The runtime patching system should handle most of these automatically
3. For custom plugins, ensure thread safety by checking if UI elements still exist before updating them
4. Use the `root.after()` method to schedule UI updates from background threads:
   ```python
   # Instead of directly updating a widget from a thread
   # widget.config(text="New text")  # Wrong!
   
   # Do this instead
   root.after(0, lambda: widget.config(text="New text"))  # Correct!
   ```
5. Check if errors persist after running:
   ```powershell
   python diagnostics\enhanced_diagnostics.py --fix-threading
   ```

### Memory System Issues

**Symptoms**: Memory lookups fail or return unexpected results

**Potential Solutions**:
1. Verify that document embeddings were successfully created
2. Check if the vector store index file exists and is not corrupted
3. Ensure the memory mode is properly set in the configuration
4. Try re-indexing your documents

## Dependency Issues and Missing Features

If you encounter errors such as missing UI panels, plugin features not loading, or import errors like `ModuleNotFoundError` for packages such as `customtkinter`, `pymupdf`, or `pytesseract`, follow these steps:

1. **Install All Required Dependencies**
   - Always use the main `requirements.txt` in the project root:
     ```powershell
     pip install -r requirements.txt
     ```
   - This ensures all core, UI, and plugin dependencies are installed (including `customtkinter`, `pymupdf`, `pytesseract`, `pillow`, etc.).

2. **OCR Features**
   - For PDF/image OCR, you must also install the Tesseract OCR engine (not just the Python packages):
     - **Windows**: Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
     - **Linux**: `sudo apt install tesseract-ocr`
     - **macOS**: `brew install tesseract`
   - After installing, ensure the Tesseract binary is in your system PATH.

3. **Plugin-Specific Issues**
   - Some plugins require extra dependencies (e.g., `customtkinter` for Ollama Hub). These are now included in the main `requirements.txt`.
   - If a plugin fails to load due to a missing dependency, re-run the install command above.

4. **Verifying Installation**
   - Run the enhanced diagnostics tool to check for missing dependencies:
     ```powershell
     python diagnostics\enhanced_diagnostics.py --basic
     ```
   - Review the output for any missing or incompatible packages.

5. **General Tips**
   - Always activate your virtual environment (if used) before installing or running the application.
   - If you update `requirements.txt`, re-run the install command.
   - For persistent issues, check the logs in `data/logs/` and the generated diagnostic report.

## Log Analysis

Log files contain valuable information for troubleshooting:

1. **Location**: All logs are stored in the `data/logs/` directory
2. **Naming**: Log files use the format `irintai_debug_YYYYMMDD_HHMMSS.log`
3. **Viewing**: 
   - Use the built-in log viewer in the UI
   - Open logs with any text editor
   - Monitor logs in real-time with:
     ```powershell
     Get-Content -Path ".\data\logs\irintai_debug.log" -Wait
     ```

4. **Key errors to look for**:
   - AttributeError: Indicates missing methods or properties
   - ImportError: Suggests missing dependencies
   - RuntimeError: Often related to threading issues

## Getting Help

If the diagnostic tools and this guide don't resolve your issue:

1. Check the project documentation for updates
2. Look for similar issues in the project repository
3. Submit a detailed bug report including:
   - The diagnostic report
   - Relevant log files
   - Steps to reproduce the issue
   - Your system configuration
