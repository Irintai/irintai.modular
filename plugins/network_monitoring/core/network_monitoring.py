"""
Network monitor plugin for IrintAI Assistant
"""
import tkinter as tk
from tkinter import ttk
import time
import threading
import psutil
import json
import os
from typing import Dict, Any, Callable, List, Optional

class IrintaiPlugin:
    def __init__(self, plugin_id, core_system):
        self.plugin_id = plugin_id
        self.core_system = core_system
        self.log = core_system.logger.log if hasattr(core_system, "logger") else print
        
        # Initialize plugin data
        self.network_stats = {
            "bytes_sent": 0,
            "bytes_recv": 0,
            "packets_sent": 0,
            "packets_recv": 0,
            "bytes_sent_per_sec": 0.0,
            "bytes_recv_per_sec": 0.0
        }
        
        # Previous values for calculating rates
        self.prev_bytes_sent = 0
        self.prev_bytes_recv = 0
        self.prev_time = time.time()
        
        # Setup monitoring thread
        self.running = False
        self.monitor_thread = None
        
        # Create UI components
        self.network_frame = None
        
    def activate(self):
        """Activate the plugin"""
        self.log(f"Network Monitor Plugin activated")
        
        # Start monitoring
        self.start_monitoring()
        
        return True
        
    def deactivate(self):
        """Deactivate the plugin"""
        # Stop monitoring thread
        self.stop_monitoring()
        
        self.log(f"Network Monitor Plugin deactivated")
        return True
        
    def get_resource_monitor_extensions(self):
        """
        Get extensions for the resource monitor panel
        
        Returns:
            Dictionary of resource monitor extensions
        """
        return {
            "metrics": {
                "network_download": self.get_download_speed,
                "network_upload": self.get_upload_speed
            },
            "ui_components": [
                self._create_network_ui()
            ]
        }
        
    def _create_network_ui(self):
        """
        Create UI for network monitoring
        
        Returns:
            UI frame component
        """
        # Create the network frame
        self.network_frame = ttk.LabelFrame(None, text="Network Monitor")
        
        # Add information labels
        info_frame = ttk.Frame(self.network_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a grid of labels
        ttk.Label(info_frame, text="Download:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.download_label = ttk.Label(info_frame, text="0.0 KB/s")
        self.download_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Upload:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.upload_label = ttk.Label(info_frame, text="0.0 KB/s")
        self.upload_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Total Received:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.total_recv_label = ttk.Label(info_frame, text="0.0 MB")
        self.total_recv_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Total Sent:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.total_sent_label = ttk.Label(info_frame, text="0.0 MB")
        self.total_sent_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Add status indicator
        status_frame = ttk.Frame(self.network_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="API Endpoints:").pack(side=tk.LEFT, padx=5)
        self.endpoint_status = ttk.Label(status_frame, text="OK", foreground="green")
        self.endpoint_status.pack(side=tk.LEFT, padx=5)
        
        # Add reset button
        ttk.Button(
            status_frame,
            text="Reset Stats",
            command=self.reset_stats
        ).pack(side=tk.RIGHT, padx=5)
        
        return self.network_frame
    
    def start_monitoring(self):
        """Start the network monitoring thread"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_thread_func, daemon=True)
        self.monitor_thread.start()
        
        self.log("Network monitoring started")
    
    def stop_monitoring(self):
        """Stop the network monitoring thread"""
        self.running = False
        
        if hasattr(self, 'monitor_thread') and self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
            
        self.log("Network monitoring stopped")
        
    def reset_stats(self):
        """Reset monitoring statistics"""
        # Get current values as new baseline
        net_stats = psutil.net_io_counters()
        self.prev_bytes_sent = net_stats.bytes_sent
        self.prev_bytes_recv = net_stats.bytes_recv
        self.prev_time = time.time()
        
        self.network_stats = {
            "bytes_sent": 0,
            "bytes_recv": 0,
            "packets_sent": 0,
            "packets_recv": 0,
            "bytes_sent_per_sec": 0.0,
            "bytes_recv_per_sec": 0.0
        }
        
        self.log("Network monitoring statistics reset")
        
    def _monitor_thread_func(self):
        """Background thread for monitoring network performance"""
        # Initialize previous values
        try:
            net_stats = psutil.net_io_counters()
            self.prev_bytes_sent = net_stats.bytes_sent
            self.prev_bytes_recv = net_stats.bytes_recv
        except Exception as e:
            self.log(f"Error initializing network monitoring: {e}")
            self.prev_bytes_sent = 0
            self.prev_bytes_recv = 0
            
        self.prev_time = time.time()
        
        while self.running:
            try:
                # Get network stats
                net_stats = psutil.net_io_counters()
                current_time = time.time()
                
                # Calculate rates
                bytes_sent = net_stats.bytes_sent
                bytes_recv = net_stats.bytes_recv
                
                # Calculate bytes per second
                time_diff = current_time - self.prev_time
                if time_diff > 0:
                    bytes_sent_per_sec = (bytes_sent - self.prev_bytes_sent) / time_diff
                    bytes_recv_per_sec = (bytes_recv - self.prev_bytes_recv) / time_diff
                else:
                    bytes_sent_per_sec = 0
                    bytes_recv_per_sec = 0
                    
                # Update stats
                self.network_stats["bytes_sent"] = bytes_sent
                self.network_stats["bytes_recv"] = bytes_recv
                self.network_stats["packets_sent"] = net_stats.packets_sent
                self.network_stats["packets_recv"] = net_stats.packets_recv
                self.network_stats["bytes_sent_per_sec"] = bytes_sent_per_sec
                self.network_stats["bytes_recv_per_sec"] = bytes_recv_per_sec
                
                # Store current values for next iteration
                self.prev_bytes_sent = bytes_sent
                self.prev_bytes_recv = bytes_recv
                self.prev_time = current_time
                
                # Update UI
                self._update_labels()
                
                # Check API endpoints periodically
                if int(current_time) % 10 == 0:  # Every 10 seconds
                    self._check_endpoints()
                    
            except Exception as e:
                self.log(f"Error in network monitoring thread: {e}")
                
            time.sleep(1.0)
    
    def _update_labels(self):
        """Update the UI labels with current stats"""
        if not hasattr(self, 'download_label') or not self.download_label:
            return
            
        # Use after() to safely update from another thread
        if hasattr(self.download_label, 'after'):
            self.download_label.after(0, lambda: self._do_update_labels())
    
    def _do_update_labels(self):
        """Update labels on the main thread"""
        try:
            # Format download/upload speeds
            download_speed = self.format_bytes_per_sec(self.network_stats["bytes_recv_per_sec"])
            upload_speed = self.format_bytes_per_sec(self.network_stats["bytes_sent_per_sec"])
            
            # Format total received/sent
            total_recv = self.format_bytes(self.network_stats["bytes_recv"])
            total_sent = self.format_bytes(self.network_stats["bytes_sent"])
            
            # Update labels
            self.download_label.config(text=download_speed)
            self.upload_label.config(text=upload_speed)
            self.total_recv_label.config(text=total_recv)
            self.total_sent_label.config(text=total_sent)
        except Exception:
            # Widget may have been destroyed
            pass
    
    def _check_endpoints(self):
        """Check API endpoints status"""
        # In a real plugin, this would check actual endpoints
        import random
        
        # Simulate endpoint check for demo
        if random.random() < 0.9:  # 90% chance to be OK
            if hasattr(self, 'endpoint_status'):
                self.endpoint_status.after(0, lambda: self.endpoint_status.config(
                    text="OK", foreground="green"))
        else:
            if hasattr(self, 'endpoint_status'):
                self.endpoint_status.after(0, lambda: self.endpoint_status.config(
                    text="Error", foreground="red"))
    
    def get_download_speed(self):
        """
        Get network download speed in KB/s
        
        Returns:
            Current download speed in KB/s
        """
        return self.network_stats["bytes_recv_per_sec"] / 1024.0
    
    def get_upload_speed(self):
        """
        Get network upload speed in KB/s
        
        Returns:
            Current upload speed in KB/s
        """
        return self.network_stats["bytes_sent_per_sec"] / 1024.0
    
    @staticmethod
    def format_bytes_per_sec(bytes_per_sec):
        """Format bytes per second into human-readable form"""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.1f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec/1024:.1f} KB/s"
        else:
            return f"{bytes_per_sec/(1024*1024):.2f} MB/s"
    
    @staticmethod
    def format_bytes(bytes_val):
        """Format bytes into human-readable form"""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val/1024:.1f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val/(1024*1024):.1f} MB"
        else:
            return f"{bytes_val/(1024*1024*1024):.2f} GB"


# Plugin metadata
plugin_info = {
    "name": "Network Monitor",
    "description": "Monitors network traffic and API endpoint status",
    "version": "1.0.0",
    "author": "Irintai",
    "url": "https://example.com/plugins/network_monitor",
    "plugin_class": IrintaiPlugin,
    "compatibility": "0.5.0",
    "tags": ["network", "monitoring", "performance"]
}