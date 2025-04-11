"""
Model training monitor plugin for IrintAI Assistant
"""
import tkinter as tk
from tkinter import ttk
import time
import threading
import json
import os
from typing import Dict, Any, Callable, List, Optional

class IrintaiPlugin:
    def __init__(self, plugin_id, core_system):
        self.plugin_id = plugin_id
        self.core_system = core_system
        self.log = core_system.logger.log if hasattr(core_system, "logger") else print
        
        # Initialize plugin data
        self.model_stats = {
            "tokens_per_second": 0.0,
            "total_tokens": 0,
            "batch_size": 0,
            "model_temperature": 0.0,
            "memory_allocated": 0.0
        }
        
        # Setup monitoring thread
        self.running = False
        self.monitor_thread = None
        
        # History tracking
        self.tokens_history = []
        self.memory_history = []
        
        # Create UI components
        self.monitoring_frame = None
        self.token_label = None
        self.memory_label = None
        self.batch_label = None
        self.temperature_label = None
        
    def activate(self):
        """Activate the plugin"""
        self.log(f"Model Monitor Plugin activated")
        
        # Start monitoring if model is running
        if hasattr(self.core_system, "model_manager") and self.core_system.model_manager.is_model_running():
            self.start_monitoring()
            
        # Register for model events
        if hasattr(self.core_system, "model_manager"):
            self.core_system.model_manager.register_event_handler(
                "model_started", self.on_model_started
            )
            self.core_system.model_manager.register_event_handler(
                "model_stopped", self.on_model_stopped
            )
        
        return True
        
    def deactivate(self):
        """Deactivate the plugin"""
        # Stop monitoring thread
        self.stop_monitoring()
        
        # Unregister event handlers
        if hasattr(self.core_system, "model_manager"):
            self.core_system.model_manager.unregister_event_handler(
                "model_started", self.on_model_started
            )
            self.core_system.model_manager.unregister_event_handler(
                "model_stopped", self.on_model_stopped
            )
        
        self.log(f"Model Monitor Plugin deactivated")
        return True
        
    def get_resource_monitor_extensions(self):
        """
        Get extensions for the resource monitor panel
        
        Returns:
            Dictionary of resource monitor extensions
        """
        return {
            "metrics": {
                "tokens_per_second": self.get_tokens_per_second,
                "model_memory": self.get_model_memory_usage
            },
            "collectors": {
                "model_stats_collector": self.collect_model_stats
            },
            "ui_components": [
                self._create_monitoring_ui()
            ]
        }
        
    def _create_monitoring_ui(self):
        """
        Create UI for model monitoring
        
        Returns:
            UI frame component
        """
        # Create the monitoring frame
        self.monitoring_frame = ttk.LabelFrame(None, text="Model Performance Monitor")
        
        # Add information labels
        info_frame = ttk.Frame(self.monitoring_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a grid of labels
        ttk.Label(info_frame, text="Tokens/sec:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.token_label = ttk.Label(info_frame, text="0.0")
        self.token_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Memory:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.memory_label = ttk.Label(info_frame, text="0.0 MB")
        self.memory_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Batch Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.batch_label = ttk.Label(info_frame, text="0")
        self.batch_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Temperature:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.temperature_label = ttk.Label(info_frame, text="0.0")
        self.temperature_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Add controls
        controls_frame = ttk.Frame(self.monitoring_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add toggle button
        self.monitor_button = ttk.Button(
            controls_frame,
            text="Start Monitoring" if not self.running else "Stop Monitoring",
            command=self.toggle_monitoring
        )
        self.monitor_button.pack(side=tk.LEFT, padx=5)
        
        # Add reset button
        ttk.Button(
            controls_frame,
            text="Reset Stats",
            command=self.reset_stats
        ).pack(side=tk.LEFT, padx=5)
        
        return self.monitoring_frame
        
    def toggle_monitoring(self):
        """Toggle model monitoring on/off"""
        if self.running:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start the model monitoring thread"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_thread_func, daemon=True)
        self.monitor_thread.start()
        
        if hasattr(self, 'monitor_button'):
            self.monitor_button.config(text="Stop Monitoring")
        
        self.log("Model monitoring started")
    
    def stop_monitoring(self):
        """Stop the model monitoring thread"""
        self.running = False
        
        if hasattr(self, 'monitor_thread') and self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
            
        if hasattr(self, 'monitor_button'):
            self.monitor_button.config(text="Start Monitoring")
            
        self.log("Model monitoring stopped")
        
    def reset_stats(self):
        """Reset monitoring statistics"""
        self.model_stats = {
            "tokens_per_second": 0.0,
            "total_tokens": 0,
            "batch_size": 0,
            "model_temperature": 0.0,
            "memory_allocated": 0.0
        }
        self.tokens_history.clear()
        self.memory_history.clear()
        self.log("Model monitoring statistics reset")
        
    def _monitor_thread_func(self):
        """Background thread for monitoring model performance"""
        last_token_count = 0
        last_time = time.time()
        
        while self.running:
            try:
                # Simulate getting model statistics
                # In a real plugin, this would fetch data from the model API
                self._collect_simulated_stats()
                
                # Calculate tokens per second
                current_time = time.time()
                current_tokens = self.model_stats["total_tokens"]
                elapsed = current_time - last_time
                
                if elapsed > 0:
                    tokens_per_sec = (current_tokens - last_token_count) / elapsed
                    self.model_stats["tokens_per_second"] = tokens_per_sec
                    
                    # Add to history
                    self.tokens_history.append(tokens_per_sec)
                    if len(self.tokens_history) > 60:
                        self.tokens_history.pop(0)
                        
                    # Also track memory
                    self.memory_history.append(self.model_stats["memory_allocated"])
                    if len(self.memory_history) > 60:
                        self.memory_history.pop(0)
                    
                    # Update the UI
                    if hasattr(self, 'token_label') and self.token_label:
                        self._update_labels()
                
                last_token_count = current_tokens
                last_time = current_time
                
            except Exception as e:
                self.log(f"Error in model monitoring thread: {e}")
                
            time.sleep(1.0)
    
    def _collect_simulated_stats(self):
        """Collect simulated model stats for demonstration"""
        # In a real plugin, this would query the model API
        
        # Get current stats
        current_tokens = self.model_stats["total_tokens"]
        current_memory = self.model_stats["memory_allocated"]
        
        # Simulate processing more tokens
        import random
        new_tokens = random.randint(5, 50)
        self.model_stats["total_tokens"] = current_tokens + new_tokens
        
        # Simulate memory changes
        memory_change = random.uniform(-10, 30)
        new_memory = max(50, current_memory + memory_change)
        self.model_stats["memory_allocated"] = new_memory
        
        # Update other stats occasionally
        if random.random() < 0.1:
            self.model_stats["batch_size"] = random.randint(1, 8)
        
        if random.random() < 0.1:
            self.model_stats["model_temperature"] = round(random.uniform(0.1, 1.0), 2)
    
    def _update_labels(self):
        """Update the UI labels with current stats"""
        if not hasattr(self, 'token_label') or not self.token_label:
            return
            
        # Use after() to safely update from another thread
        if hasattr(self.token_label, 'after'):
            self.token_label.after(0, lambda: self._do_update_labels())
    
    def _do_update_labels(self):
        """Update labels on the main thread"""
        try:
            self.token_label.config(text=f"{self.model_stats['tokens_per_second']:.1f}")
            self.memory_label.config(text=f"{self.model_stats['memory_allocated']:.1f} MB")
            self.batch_label.config(text=f"{self.model_stats['batch_size']}")
            self.temperature_label.config(text=f"{self.model_stats['model_temperature']:.2f}")
        except Exception:
            # Widget may have been destroyed
            pass
    
    def get_tokens_per_second(self):
        """
        Get tokens per second metric
        
        Returns:
            Current tokens per second
        """
        return self.model_stats["tokens_per_second"]
    
    def get_model_memory_usage(self):
        """
        Get model memory usage in MB
        
        Returns:
            Current memory usage
        """
        return self.model_stats["memory_allocated"]
    
    def collect_model_stats(self, current_stats):
        """
        Collect and provide model statistics
        
        Args:
            current_stats: Current system stats
            
        Returns:
            Dictionary of model stats to add
        """
        return {
            "model_tokens_per_sec": self.model_stats["tokens_per_second"],
            "model_memory_mb": self.model_stats["memory_allocated"],
            "model_temperature": self.model_stats["model_temperature"],
            "model_batch_size": self.model_stats["batch_size"]
        }
    
    def on_model_started(self, model_name, config):
        """
        Handle model started event
        
        Args:
            model_name: Name of the started model
            config: Model configuration
        """
        self.log(f"Model started: {model_name}")
        self.reset_stats()
        self.start_monitoring()
    
    def on_model_stopped(self):
        """Handle model stopped event"""
        self.log("Model stopped")
        self.stop_monitoring()


# Plugin metadata
plugin_info = {
    "name": "Model Monitor",
    "description": "Monitors and tracks model performance metrics",
    "version": "1.0.0",
    "author": "Irintai",
    "url": "https://example.com/plugins/model_monitor",
    "plugin_class": IrintaiPlugin,
    "compatibility": "0.5.0",
    "tags": ["model", "performance", "monitoring"]
}