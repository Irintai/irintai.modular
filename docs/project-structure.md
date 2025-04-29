d:\AI\IrintAI Assistant\
│
├── irintai.py                  # Main application entry point
│
├── core\                      # Core components
│   ├── __init__.py             # Core module initialization
│   ├── chat_engine.py          # Chat interface with language models
│   ├── config_manager.py       # Configuration management
│   ├── memory_system.py        # Vector storage and retrieval
│   ├── model_manager.py        # Handles Ollama model operations
│   ├── plugin_manager.py       # Plugin lifecycle management
│   ├── plugin_sdk.py           # SDK for plugin development
│   └── settings_manager.py     # Application settings manager
│
├── utils\                     # Utility modules
│   ├── __init__.py             # Utils module initialization
│   ├── attribute_checker.py    # Attribute error prevention
│   ├── file_ops.py             # File operations utilities
│   ├── logger.py               # Logging functionality
│   ├── plugin_dependency_manager.py # Manages plugin dependencies
│   ├── plugin_event_bus.py     # Event communication system for plugins
│   ├── runtime_patching.py     # Dynamic method/attribute patching
│   ├── system_monitor.py       # System resource monitoring
│   └── version.py              # Version information
│
├── ui\                        # User interface components
│   ├── __init__.py             # UI module initialization
│   ├── chat_panel.py           # Chat interface panel
│   ├── config_panel.py         # Configuration settings panel
│   ├── dashboard.py            # Main dashboard panel
│   ├── log_viewer.py           # Log viewing interface
│   ├── main_window.py          # Main application window
│   ├── memory_panel.py         # Memory management panel
│   ├── model_panel.py          # Model management interface
│   ├── plugin_config_panel.py  # Plugin configuration UI
│   ├── plugin_panel.py         # Plugin management interface
│   └── resource_monitor_panel.py # Resource monitoring panel
│
├── plugins\                   # Plugin directory
│   ├── personality_plugin\    # Example plugin: Personality
│   │   ├── __init__.py         # Plugin initialization
│   │   ├── bridge.py           # Integration helpers
│   │   ├── core\              # Plugin core functionality
│   │   │   ├── __init__.py     # Core module initialization
│   │   │   ├── helpers.py      # Helper functions
│   │   │   └── personality_plugin.py # Main plugin implementation
│   │   └── ui\                # Plugin UI components
│   │       ├── __init__.py     # UI module initialization
│   │       └── panel.py        # Plugin panel UI
│   │
│   ├── network_monitoring\    # Network monitoring plugin
│   │   └── core\
│   │       └── network_monitoring.py # Network monitoring 
│   │
│   └── model_training_performance\ # Model training plugin
│
├── diagnostics.py              # Basic diagnostic utility
├── enhanced_diagnostics.py     # Comprehensive system diagnostics
├── fix_plugin_manager.py       # Plugin manager repair utility
├── update_plugin_manager.py    # Updates missing plugin methods
│
├── data\                      # Data directory (created at runtime)
│   ├── logs\                   # Log files
│   ├── models\                 # Model storage
│   ├── plugins\                # Plugin data
│   │   ├── config\             # Plugin configuration
│   │   └── data\               # Plugin data storage
│   ├── reflections\            # System self-reflection data
│   └── vector_store\           # Vector embeddings storage
│
├── resources\                  # Application resources
│   └── icons\                  # Application icons
│       └── irintai_icon.ico    # Application icon
│
├── docs\                      # Documentation and guides
│   ├── API_DOCUMENTATION.md
│   ├── enhanced_pdf_extraction_api.md
│   ├── enhanced_pdf_extraction.md
│   ├── enhanced_pdf_implementation.md
│   ├── INSTALLATION.md
│   ├── Irintai Assistant.md
│   ├── plugin_api.md
│   ├── Plugin_integration.md
│   ├── project-structure.md
│   ├── README.md
│   ├── requirements.txt
│   ├── TROUBLESHOOTING.md
│   ├── USAGE_GUIDE.md
│   ├── IrintAI_Assistant_Architecture_Offline\
│   └── resources\