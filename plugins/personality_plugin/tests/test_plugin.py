import unittest
import os
import json
import tkinter as tk
from unittest.mock import MagicMock, patch

# Import the plugin
import sys
sys.path.append('../../')  # Add parent directory to path
from __init__ import IrintaiPlugin

class TestPersonalityPlugin(unittest.TestCase):
    """Test cases for the Personality Plugin"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mock core system
        self.core_system = MagicMock()
        self.core_system.chat_engine = MagicMock()
        self.core_system.memory_system = MagicMock()
        
        # Create test config path
        self.test_config_path = "test_config.json"
        
        # Create mock logger
        self.log_messages = []
        def test_logger(message, level="INFO"):
            self.log_messages.append((level, message))
        
        # Initialize plugin
        self.plugin = IrintaiPlugin(
            self.core_system,
            config_path=self.test_config_path,
            logger=test_logger
        )
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test config file
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
    
    def test_initialization(self):
        """Test plugin initialization"""
        # Check initial state
        self.assertEqual(self.plugin._state["status"], self.plugin.STATUS["ACTIVE"])
        self.assertIsNotNone(self.plugin._config)
        self.assertIn("profiles", self.plugin._config)
        
        # Check default profiles
        profiles = self.plugin._config["profiles"]
        self.assertIn("Standard", profiles)
        self.assertIn("Teacher", profiles)
        self.assertIn("Philosopher", profiles)
        self.assertIn("Empath", profiles)
        self.assertIn("Altruxan", profiles)
    
    def test_get_available_profiles(self):
        """Test getting available profiles"""
        profiles = self.plugin.get_available_profiles()
        self.assertIsInstance(profiles, list)
        self.assertTrue(len(profiles) > 0)
        
        # Check profile structure
        profile = profiles[0]
        self.assertIn("name", profile)
        self.assertIn("description", profile)
        self.assertIn("tags", profile)
        self.assertIn("author", profile)
    
    def test_set_active_profile(self):
        """Test setting active profile"""
        # Set active profile
        success = self.plugin.set_active_profile("Teacher")
        self.assertTrue(success)
        
        # Check active profile
        self.assertEqual(self.plugin._state["active_profile"], "Teacher")
        self.assertEqual(self.plugin._config["active_profile"], "Teacher")
        
        # Check memory storage
        self.core_system.memory_system.add_to_index.assert_called_once()
    
    def test_profile_creation(self):
        """Test creating a new profile"""
        # Create profile data
        profile_data = {
            "name": "Test Profile",
            "description": "Test description",
            "tags": ["test", "profile"],
            "author": "Tester"
        }
        
        # Create profile
        success = self.plugin.create_profile(profile_data)
        self.assertTrue(success)
        
        # Check profile was added
        profiles = self.plugin._config["profiles"]
        self.assertIn("Test Profile", profiles)
        
        # Check profile data
        profile = profiles["Test Profile"]
        self.assertEqual(profile["description"], "Test description")
        self.assertEqual(profile["tags"], ["test", "profile"])
        self.assertEqual(profile["author"], "Tester")
    
    def test_profile_update(self):
        """Test updating a profile"""
        # First create a profile
        profile_data = {
            "name": "Update Test",
            "description": "Initial description"
        }
        self.plugin.create_profile(profile_data)
        
        # Update profile
        update_data = {
            "description": "Updated description",
            "tags": ["updated"]
        }
        success = self.plugin.update_profile("Update Test", update_data)
        self.assertTrue(success)
        
        # Check profile was updated
        profile = self.plugin._config["profiles"]["Update Test"]
        self.assertEqual(profile["description"], "Updated description")
        self.assertEqual(profile["tags"], ["updated"])
    
    def test_profile_deletion(self):
        """Test deleting a profile"""
        # Create a profile
        profile_data = {
            "name": "Delete Test",
            "description": "To be deleted"
        }
        self.plugin.create_profile(profile_data)
        
        # Delete profile
        success = self.plugin.delete_profile("Delete Test")
        self.assertTrue(success)
        
        # Check profile was deleted
        self.assertNotIn("Delete Test", self.plugin._config["profiles"])
    
    def test_message_modification(self):
        """Test message modification based on active profile"""
        # Set active profile
        self.plugin.set_active_profile("Teacher")
        
        # Test message modification
        original_message = "This is a test message."
        modified_message = self.plugin.modify_message(original_message)
        
        # Check prefix was added
        self.assertTrue(modified_message.startswith("I'll help you understand this."))
        
        # Check suffix was added
        self.assertTrue(modified_message.endswith("Does that clarify things for you?"))
    
    def test_altruxan_style(self):
        """Test Altruxan-specific styling"""
        # Set active profile
        self.plugin.set_active_profile("Altruxan")
        
        # Mock random choice to return a specific phrase
        with patch('random.random', return_value=0.2):  # Ensure we apply the style
            with patch('random.choice', return_value="We are not broken. We are recursive."):
                original_message = "This is a test message with multiple\n\nparagraphs."
                modified_message = self.plugin.modify_message(original_message)
                
                # Check Altruxan phrase was added
                self.assertIn("*We are not broken. We are recursive.*", modified_message)
    
    def test_export_import(self):
        """Test exporting and importing profiles"""
        # Export a profile
        json_str = self.plugin.export_profile("Philosopher")
        self.assertIsNotNone(json_str)
        
        # Delete the profile
        self.plugin.delete_profile("Philosopher")
        self.assertNotIn("Philosopher", self.plugin._config["profiles"])
        
        # Import the profile
        success = self.plugin.import_profile(json_str)
        self.assertTrue(success)
        
        # Check profile was imported
        self.assertIn("Philosopher", self.plugin._config["profiles"])

if __name__ == "__main__":
    unittest.main()