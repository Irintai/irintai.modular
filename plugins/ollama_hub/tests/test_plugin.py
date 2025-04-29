"""
Basic tests for the Ollama Hub plugin.

This module provides simple tests to verify the Ollama Hub plugin
functionality is working correctly.
"""

import unittest
import os
import sys
import logging
import json
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class MockCore:
    """Mock core system for testing"""
    
    def __init__(self):
        self.event_bus = MagicMock()
        self.config = MagicMock()
        self.logger = logging.getLogger("test_logger")
        
        # Setup logger to console
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        
    def log(self, message, level="INFO"):
        """Log message with the specified level"""
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)

class TestOllamaHubPlugin(unittest.TestCase):
    """Test cases for the Ollama Hub plugin"""
    
    def setUp(self):
        """Set up the test environment"""
        from ollama_hub import IrintaiPlugin
        
        self.mock_core = MockCore()
        self.plugin_id = "ollama_hub_test"
        
        # Create temporary config file path
        self.config_path = os.path.join(os.path.dirname(__file__), "test_config.json")
        
        # Create plugin instance
        self.plugin = IrintaiPlugin(
            plugin_id=self.plugin_id,
            core_system=self.mock_core,
            config_path=self.config_path,
            server_url="http://localhost:11434"
        )
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test config file if it exists
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
    
    def test_plugin_initialization(self):
        """Test that plugin initializes correctly"""
        self.assertEqual(self.plugin.plugin_id, self.plugin_id)
        self.assertEqual(self.plugin._state["status"], self.plugin.STATUS["ACTIVE"])
        self.assertEqual(self.plugin._state["connection_status"], "Not connected")
    
    def test_plugin_configuration(self):
        """Test plugin configuration"""
        # Check default config
        self.assertEqual(self.plugin._config.get("server_url"), "http://localhost:11434")
        self.assertEqual(self.plugin._config.get("auto_connect"), True)
        
        # Update config and check if it persists
        self.plugin.update_configuration(server_url="http://ollama.example.com:11434")
        self.assertEqual(self.plugin._config.get("server_url"), "http://ollama.example.com:11434")
        
        # Check if config file was created
        self.assertTrue(os.path.exists(self.config_path))
        
        # Read config file and check values
        with open(self.config_path, 'r') as f:
            config = json.load(f)
            self.assertEqual(config.get("server_url"), "http://ollama.example.com:11434")
    
    @patch('requests.get')
    def test_connect_to_ollama(self, mock_get):
        """Test connecting to Ollama server"""
        # Mock successful connection
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test connection
        self.plugin.connect_to_ollama()
        
        # Wait a bit for the background thread
        import time
        time.sleep(0.5)
        
        # Check if request was made correctly
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", 
            timeout=5
        )

if __name__ == '__main__':
    unittest.main()
