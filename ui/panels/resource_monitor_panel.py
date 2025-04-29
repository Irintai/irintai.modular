"""
Resource monitor panel for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from typing import Dict, List, Any, Callable, Optional
import math
import psutil
import random
import datetime

class ResourceMonitorPanel:
    """Panel for monitoring system resources"""
    
    def __init__(self, master, logger=None, system_monitor=None):
        """
        Initialize the resource monitor panel
        
        Args:
            master: Parent widget
            logger: Optional logging function
            system_monitor: Optional SystemMonitor instance
        """
        self.master = master
        self.logger = logger
        self.system_monitor = system_monitor
        
        # Create the main frame
        self.frame = ttk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Data for plots
        self.data_points = 60  # 1 minute of data at 1 second intervals
        self.time_data = list(range(self.data_points))
        self.cpu_data = [0] * self.data_points
        self.ram_data = [0] * self.data_points
        self.gpu_data = [0] * self.data_points
        
        # Custom metrics data
        self.custom_metrics = {}
        
        # Animation running flag
        self.running = False
        
        # Create UI components
        self.create_ui()
        
        # Start the update timer
        self.start_monitoring()
        
    def log(self, message, level="INFO"):
        """Log a message if logger is available"""
        if self.logger:
            self.logger(f"[ResourceMonitor] {message}", level)
        
    def create_ui(self):
        """Create the UI components"""
        # Create top frame for current values
        self.top_frame = ttk.Frame(self.frame)
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Current usage labels
        ttk.Label(self.top_frame, text="Current Usage:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.cpu_label = ttk.Label(self.top_frame, text="CPU: 0%")
        self.cpu_label.grid(row=0, column=1, padx=10, pady=5)
        
        self.ram_label = ttk.Label(self.top_frame, text="RAM: 0%")
        self.ram_label.grid(row=0, column=2, padx=10, pady=5)
        
        self.gpu_label = ttk.Label(self.top_frame, text="GPU: N/A")
        self.gpu_label.grid(row=0, column=3, padx=10, pady=5)
        
        self.disk_label = ttk.Label(self.top_frame, text="Disk: 0%")
        self.disk_label.grid(row=0, column=4, padx=10, pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create system tab
        self.system_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.system_tab, text="System")
        
        # Create processes tab
        self.processes_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.processes_tab, text="Processes")
        
        # Create plugins tab
        self.plugins_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.plugins_tab, text="Plugin Metrics")
        
        # Create graph tab
        self.graph_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_tab, text="Graphs")
        
        # Initialize tabs
        self.init_system_tab()
        self.init_processes_tab()
        self.init_plugins_tab()
        self.init_graph_tab()
        
        # Create bottom frame for controls
        self.bottom_frame = ttk.Frame(self.frame)
        self.bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Refresh button
        self.refresh_button = ttk.Button(self.bottom_frame, text="Refresh", command=self.refresh)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Export button
        self.export_button = ttk.Button(self.bottom_frame, text="Export", command=self.export_metrics)
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Update interval
        ttk.Label(self.bottom_frame, text="Update interval:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.interval_var = tk.StringVar(value="1")
        interval_combobox = ttk.Combobox(self.bottom_frame, textvariable=self.interval_var, 
                                        values=["1", "2", "5", "10"], width=5, state="readonly")
        interval_combobox.pack(side=tk.LEFT)
        ttk.Label(self.bottom_frame, text="seconds").pack(side=tk.LEFT, padx=5)
        
        # Bind interval change
        interval_combobox.bind("<<ComboboxSelected>>", self.on_interval_changed)
        
    def init_system_tab(self):
        """Initialize the system tab"""
        # Create frame for system metrics
        self.system_frame = ttk.Frame(self.system_tab)
        self.system_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create detailed system info display
        self.system_tree = ttk.Treeview(self.system_frame, columns=("1", "2"), show="tree")
        self.system_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.system_frame, orient=tk.VERTICAL, command=self.system_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.system_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.system_tree.column("#0", width=200, minwidth=150)
        self.system_tree.column("1", width=150, minwidth=100)
        self.system_tree.column("2", width=250, minwidth=150)
        
        # Add root items
        self.cpu_item = self.system_tree.insert("", "end", text="CPU", open=True)
        self.ram_item = self.system_tree.insert("", "end", text="Memory", open=True)
        self.gpu_item = self.system_tree.insert("", "end", text="GPU", open=True)
        self.disk_item = self.system_tree.insert("", "end", text="Disk", open=True)
        
    def init_processes_tab(self):
        """Initialize the processes tab"""
        # Create frame for processes
        self.processes_frame = ttk.Frame(self.processes_tab)
        self.processes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create processes treeview
        columns = ("PID", "Name", "CPU", "Memory", "Status", "Plugin")
        self.processes_tree = ttk.Treeview(self.processes_frame, columns=columns, show="headings")
        self.processes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.processes_frame, orient=tk.VERTICAL, command=self.processes_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.processes_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure columns
        widths = [70, 150, 70, 100, 100, 120]
        for i, col in enumerate(columns):
            self.processes_tree.heading(col, text=col, command=lambda c=col: self.sort_processes_tree(c))
            self.processes_tree.column(col, width=widths[i])
            
    def init_plugins_tab(self):
        """Initialize the plugins tab"""
        # Create frame for plugin metrics
        self.plugins_frame = ttk.Frame(self.plugins_tab)
        self.plugins_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create plugin selection frame
        self.plugin_select_frame = ttk.Frame(self.plugins_frame)
        self.plugin_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.plugin_select_frame, text="Plugin Filter:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Plugin filter dropdown
        self.plugin_filter_var = tk.StringVar(value="All Plugins")
        self.plugin_filter_combo = ttk.Combobox(self.plugin_select_frame, textvariable=self.plugin_filter_var, 
                                               state="readonly", width=30)
        self.plugin_filter_combo.pack(side=tk.LEFT, padx=5)
        
        # Bind selection event
        self.plugin_filter_combo.bind("<<ComboboxSelected>>", self.on_plugin_filter_changed)
        
        # Refresh plugin list button
        ttk.Button(self.plugin_select_frame, text="Refresh", 
                  command=self.refresh_plugin_list).pack(side=tk.LEFT, padx=5)
        
        # Add to Graph button
        ttk.Button(self.plugin_select_frame, text="Add to Graph", 
                  command=self.add_selected_metric_to_graph).pack(side=tk.RIGHT, padx=5)
        
        # Create plugin metrics treeview with grouping
        self.plugins_tree = ttk.Treeview(self.plugins_frame, columns=("Value", "Format", "Description"), 
                                       show="tree headings")
        self.plugins_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.plugins_frame, orient=tk.VERTICAL, command=self.plugins_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.plugins_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.plugins_tree.heading("#0", text="Metric")
        self.plugins_tree.heading("Value", text="Value")
        self.plugins_tree.heading("Format", text="Format")
        self.plugins_tree.heading("Description", text="Description")
        
        self.plugins_tree.column("#0", width=200, minwidth=150)
        self.plugins_tree.column("Value", width=120, minwidth=80)
        self.plugins_tree.column("Format", width=80, minwidth=60)
        self.plugins_tree.column("Description", width=300, minwidth=150)
        
        # Create right-click menu
        self.plugin_metrics_menu = tk.Menu(self.plugins_tree, tearoff=0)
        self.plugin_metrics_menu.add_command(label="Add to Graph", command=self.add_selected_metric_to_graph)
        self.plugin_metrics_menu.add_command(label="Remove from Graph", command=self.remove_selected_metric_from_graph)
        self.plugin_metrics_menu.add_separator()
        self.plugin_metrics_menu.add_command(label="Show Details", command=self.show_metric_details)
        
        # Bind right-click
        self.plugins_tree.bind("<Button-3>", self.show_plugins_tree_menu)
        
        # Initialize plugin list and colors
        self.plugin_colors = {}
        self.refresh_plugin_list()
        
    def init_graph_tab(self):
        """Initialize the graph tab"""
        # Create frame for graphs
        self.graph_frame = ttk.Frame(self.graph_tab)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        
        # Create subplot for CPU and RAM
        self.subplot = self.figure.add_subplot(111)
        self.subplot.set_title("Resource Usage Over Time")
        self.subplot.set_xlabel("Time (seconds)")
        self.subplot.set_ylabel("Usage (%)")
        self.subplot.set_ylim(0, 100)
        
        # Create lines for CPU, RAM, and GPU
        self.cpu_line, = self.subplot.plot(self.time_data, self.cpu_data, 'b-', label="CPU")
        self.ram_line, = self.subplot.plot(self.time_data, self.ram_data, 'g-', label="RAM")
        self.gpu_line, = self.subplot.plot(self.time_data, self.gpu_data, 'r-', label="GPU")
        
        # Add legend
        self.subplot.legend()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Add custom metrics selection frame
        self.metrics_frame = ttk.LabelFrame(self.graph_frame, text="Metrics Visibility")
        self.metrics_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Create left frame for system metrics
        system_frame = ttk.Frame(self.metrics_frame)
        system_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(system_frame, text="System Metrics:").pack(anchor=tk.W)
        
        # Create checkbox variables
        self.show_cpu_var = tk.BooleanVar(value=True)
        self.show_ram_var = tk.BooleanVar(value=True)
        self.show_gpu_var = tk.BooleanVar(value=True)
        
        # Add checkboxes
        ttk.Checkbutton(system_frame, text="CPU", variable=self.show_cpu_var, 
                       command=self.update_graph_visibility).pack(anchor=tk.W)
        ttk.Checkbutton(system_frame, text="RAM", variable=self.show_ram_var, 
                       command=self.update_graph_visibility).pack(anchor=tk.W)
        ttk.Checkbutton(system_frame, text="GPU", variable=self.show_gpu_var, 
                       command=self.update_graph_visibility).pack(anchor=tk.W)
        
        # Create right frame for plugin metrics
        self.plugin_metrics_frame = ttk.Frame(self.metrics_frame)
        self.plugin_metrics_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        ttk.Label(self.plugin_metrics_frame, text="Plugin Metrics:").pack(anchor=tk.W)
        
        # Scrollable frame for plugin metric checkboxes
        self.plugin_checkboxes_canvas = tk.Canvas(self.plugin_metrics_frame, height=100)
        self.plugin_checkboxes_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.plugin_metrics_frame, orient=tk.VERTICAL, command=self.plugin_checkboxes_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.plugin_checkboxes_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.plugin_checkboxes_frame = ttk.Frame(self.plugin_checkboxes_canvas)
        self.plugin_checkboxes_canvas.create_window((0, 0), window=self.plugin_checkboxes_frame, anchor=tk.NW)
        
        self.plugin_checkboxes_frame.bind("<Configure>", self._on_frame_configure)
        
        # Dictionary to store custom metrics visibility variables
        self.metric_visibility_vars = {}
        
        # Add buttons
        button_frame = ttk.Frame(self.metrics_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        ttk.Button(button_frame, text="Show All", command=self.show_all_metrics).pack(pady=2)
        ttk.Button(button_frame, text="Hide All", command=self.hide_all_metrics).pack(pady=2)
        ttk.Button(button_frame, text="Remove All", command=self.remove_all_custom_metrics).pack(pady=2)
        
    def _on_frame_configure(self, event):
        """Handle frame configuration event for scrolling"""
        self.plugin_checkboxes_canvas.configure(scrollregion=self.plugin_checkboxes_canvas.bbox("all"))
        
    def show_all_metrics(self):
        """Show all metrics on the graph"""
        # System metrics
        self.show_cpu_var.set(True)
        self.show_ram_var.set(True)
        self.show_gpu_var.set(True)
        
        # Plugin metrics
        for var in self.metric_visibility_vars.values():
            var.set(True)
            
        self.update_graph_visibility()
        
    def hide_all_metrics(self):
        """Hide all metrics on the graph"""
        # System metrics
        self.show_cpu_var.set(False)
        self.show_ram_var.set(False)
        self.show_gpu_var.set(False)
        
        # Plugin metrics
        for var in self.metric_visibility_vars.values():
            var.set(False)
            
        self.update_graph_visibility()
        
    def update_graph_visibility(self):
        """Update the visibility of graph lines based on checkboxes"""
        self.cpu_line.set_visible(self.show_cpu_var.get())
        self.ram_line.set_visible(self.show_ram_var.get())
        self.gpu_line.set_visible(self.show_gpu_var.get())
        
        # Update custom metrics visibility
        for metric_id, info in self.custom_metrics.items():
            if metric_id in self.metric_visibility_vars:
                visible = self.metric_visibility_vars[metric_id].get()
                info["visible"] = visible
                if info["line"]:
                    info["line"].set_visible(visible)
        
        self.canvas.draw()
        
    def start_monitoring(self):
        """Start the monitoring updates"""
        if self.running:
            return
            
        self.running = True
        
        # Start update timer
        self.update_interval = int(self.interval_var.get()) * 1000  # Convert to milliseconds
        self.update_timer_id = self.frame.after(self.update_interval, self.update_metrics)
        
        self.log("Started resource monitoring")
        
    def stop_monitoring(self):
        """Stop the monitoring updates"""
        if not self.running:
            return
            
        self.running = False
        
        # Cancel the timer
        if hasattr(self, 'update_timer_id'):
            self.frame.after_cancel(self.update_timer_id)
            
        self.log("Stopped resource monitoring")
        
    def on_interval_changed(self, event=None):
        """Handle update interval change"""
        # Restart monitoring with new interval
        self.stop_monitoring()
        self.start_monitoring()
        
    def update_metrics(self):
        """Update resource metrics display"""
        if not self.running:
            return
            
        try:
            if self.system_monitor:
                # Get system info
                system_info = self.system_monitor.get_system_info()
                
                # Update top labels
                cpu_usage = system_info["cpu"]["usage_percent"]
                self.cpu_label.config(text=f"CPU: {cpu_usage:.1f}%")
                
                ram_usage = system_info["ram"]["usage_percent"]
                self.ram_label.config(text=f"RAM: {ram_usage:.1f}%")
                
                gpu_usage = system_info["gpu"]["usage_percent"]
                self.gpu_label.config(text=f"GPU: {gpu_usage}")
                
                disk_usage = system_info["disk"]["usage_percent"]
                self.disk_label.config(text=f"Disk: {disk_usage:.1f}%")
                
                # Update graph data
                self.cpu_data.append(cpu_usage)
                self.cpu_data.pop(0)
                
                self.ram_data.append(ram_usage)
                self.ram_data.pop(0)
                
                try:
                    if gpu_usage != "N/A":
                        gpu_value = float(gpu_usage.replace("%", ""))
                    else:
                        gpu_value = 0
                except:
                    gpu_value = 0
                    
                self.gpu_data.append(gpu_value)
                self.gpu_data.pop(0)
                
                # Update custom metrics
                self.update_custom_metrics_data()
                
                # Update graph lines
                self.cpu_line.set_ydata(self.cpu_data)
                self.ram_line.set_ydata(self.ram_data)
                self.gpu_line.set_ydata(self.gpu_data)
                
                for key, info in self.custom_metrics.items():
                    if info["line"]:
                        info["line"].set_ydata(info["data"])
                
                # Draw the canvas
                self.canvas.draw_idle()
                
                # Update system tab details
                self.update_system_details(system_info)
                
                # Update processes tab
                self.update_processes()
                
                # Update plugin metrics tab
                self.update_plugin_metrics()
                
            else:
                # No system monitor available
                self.cpu_label.config(text="CPU: N/A")
                self.ram_label.config(text="RAM: N/A")
                self.gpu_label.config(text="GPU: N/A")
                self.disk_label.config(text="Disk: N/A")
                
        except Exception as e:
            self.log(f"Error updating metrics: {e}", "ERROR")
            
        finally:
            # Schedule next update
            self.update_timer_id = self.frame.after(self.update_interval, self.update_metrics)
    
    def update_custom_metrics_data(self):
        """Update data for custom metrics"""
        if not self.system_monitor or not self.custom_metrics:
            return
            
        try:
            # Get custom metrics
            metrics = getattr(self.system_monitor, "get_all_metrics", lambda: {"custom": {}})()
            
            if "custom" not in metrics:
                return
                
            # Update each custom metric
            for key, info in self.custom_metrics.items():
                if key in metrics["custom"]:
                    metric = metrics["custom"][key]
                    value = metric["value"]
                    
                    # Convert to percentage for the graph if needed
                    if metric["metadata"]["format"] == "percentage":
                        # Already a percentage, use directly
                        graph_value = float(value)
                    elif metric["metadata"]["format"] == "numeric":
                        # Scale numeric values to fit in the graph (0-100)
                        # We need to estimate a reasonable scale
                        if hasattr(self, "_metric_max_values"):
                            # Update max value if needed
                            if key not in self._metric_max_values or value > self._metric_max_values[key]:
                                self._metric_max_values[key] = max(1.0, value * 1.1)  # Add 10% margin
                        else:
                            # Initialize max values dictionary
                            self._metric_max_values = {key: max(1.0, value * 1.1)}
                            
                        # Scale to 0-100 based on max value seen so far
                        max_value = self._metric_max_values[key]
                        graph_value = (value / max_value) * 100
                        graph_value = min(100, graph_value)  # Cap at 100%
                    else:
                        # For text metrics, just use 50% as a visual indicator
                        graph_value = 50
                        
                    # Update data
                    info["data"].append(graph_value)
                    info["data"].pop(0)
                else:
                    # Metric not available, add 0
                    info["data"].append(0)
                    info["data"].pop(0)
                    
        except Exception as e:
            self.log(f"Error updating custom metrics data: {e}", "ERROR")
            
    def update_system_details(self, system_info: Dict[str, Any]):
        """
        Update the system details treeview
        
        Args:
            system_info: System information dictionary
        """
        # Clear existing items
        for item in self.system_tree.get_children(self.cpu_item):
            self.system_tree.delete(item)
        for item in self.system_tree.get_children(self.ram_item):
            self.system_tree.delete(item)
        for item in self.system_tree.get_children(self.gpu_item):
            self.system_tree.delete(item)
        for item in self.system_tree.get_children(self.disk_item):
            self.system_tree.delete(item)
            
        # Add CPU info
        cpu_usage = system_info["cpu"]["usage_percent"]
        self.system_tree.insert(self.cpu_item, "end", values=("Usage", f"{cpu_usage:.1f}%"))
        
        # Get additional CPU info from psutil if available
        try:
            cpu_count = psutil.cpu_count(logical=False)
            logical_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            self.system_tree.insert(self.cpu_item, "end", values=("Physical cores", str(cpu_count)))
            self.system_tree.insert(self.cpu_item, "end", values=("Logical cores", str(logical_count)))
            
            if cpu_freq:
                self.system_tree.insert(self.cpu_item, "end", 
                                     values=("Current frequency", f"{cpu_freq.current:.0f} MHz"))
                if hasattr(cpu_freq, "min") and cpu_freq.min:
                    self.system_tree.insert(self.cpu_item, "end", 
                                         values=("Min frequency", f"{cpu_freq.min:.0f} MHz"))
                if hasattr(cpu_freq, "max") and cpu_freq.max:
                    self.system_tree.insert(self.cpu_item, "end", 
                                         values=("Max frequency", f"{cpu_freq.max:.0f} MHz"))
        except:
            pass
            
        # Add RAM info
        ram_percent = system_info["ram"]["usage_percent"]
        ram_used = system_info["ram"]["used_gb"]
        ram_total = system_info["ram"]["total_gb"]
        
        self.system_tree.insert(self.ram_item, "end", values=("Usage", f"{ram_percent:.1f}%"))
        self.system_tree.insert(self.ram_item, "end", values=("Used", f"{ram_used:.2f} GB"))
        self.system_tree.insert(self.ram_item, "end", values=("Total", f"{ram_total:.2f} GB"))
        self.system_tree.insert(self.ram_item, "end", values=("Free", f"{ram_total - ram_used:.2f} GB"))
        
        # Get additional memory info from psutil if available
        try:
            swap = psutil.swap_memory()
            self.system_tree.insert(self.ram_item, "end", values=("Swap usage", f"{swap.percent:.1f}%"))
            self.system_tree.insert(self.ram_item, "end", values=("Swap used", f"{swap.used / (1024**3):.2f} GB"))
            self.system_tree.insert(self.ram_item, "end", values=("Swap total", f"{swap.total / (1024**3):.2f} GB"))
        except:
            pass
            
        # Add GPU info
        gpu_usage = system_info["gpu"]["usage_percent"]
        gpu_memory = system_info["gpu"]["memory"]
        
        self.system_tree.insert(self.gpu_item, "end", values=("Usage", str(gpu_usage)))
        self.system_tree.insert(self.gpu_item, "end", values=("Memory", str(gpu_memory)))
        
        # Add additional GPU info from nvidia-smi if available
        try:
            if hasattr(self.system_monitor, 'get_gpu_info'):
                gpu_info = self.system_monitor.get_gpu_info()
                if gpu_info:
                    for key, value in gpu_info.items():
                        if key not in ["usage_percent", "memory"]:
                            self.system_tree.insert(self.gpu_item, "end", values=(key.replace("_", " ").title(), str(value)))
        except:
            pass
            
        # Add Disk info
        disk_percent = system_info["disk"]["usage_percent"]
        disk_free = system_info["disk"]["free_gb"]
        disk_total = system_info["disk"]["total_gb"]
        
        self.system_tree.insert(self.disk_item, "end", values=("Usage", f"{disk_percent:.1f}%"))
        self.system_tree.insert(self.disk_item, "end", values=("Free", f"{disk_free:.2f} GB"))
        self.system_tree.insert(self.disk_item, "end", values=("Total", f"{disk_total:.2f} GB"))
        self.system_tree.insert(self.disk_item, "end", values=("Used", f"{disk_total - disk_free:.2f} GB"))
        
    def update_processes(self):
        """Update the processes tab with monitored process information"""
        if not self.system_monitor:
            return
            
        try:
            # Clear existing items
            for item in self.processes_tree.get_children():
                self.processes_tree.delete(item)
                
            # Get process metrics if available
            metrics = getattr(self.system_monitor, "get_all_metrics", lambda: {"processes": {}})()
            
            if "processes" not in metrics:
                return
                
            # Add each monitored process
            for key, process in metrics["processes"].items():
                info = process["info"]
                metrics = process["metrics"]
                
                if "error" in metrics:
                    # Process is not running or has an error
                    self.processes_tree.insert("", "end", values=(
                        info["process_id"],
                        info["name"],
                        "N/A",
                        "N/A",
                        "Error",
                        info["plugin_id"]
                    ))
                else:
                    # Process is running
                    self.processes_tree.insert("", "end", values=(
                        info["process_id"],
                        info["name"],
                        f"{metrics['cpu_percent']:.1f}%",
                        f"{metrics['memory_rss']:.1f} MB",
                        metrics['status'],
                        info["plugin_id"]
                    ))
        except Exception as e:
            self.log(f"Error updating process list: {e}", "ERROR")
            
    def refresh_plugin_list(self):
        """Refresh the list of plugins in the filter dropdown"""
        if not self.system_monitor:
            return
            
        try:
            # Get metrics if available
            metrics = getattr(self.system_monitor, "get_all_metrics", lambda: {"custom": {}})()
            
            if "custom" not in metrics:
                return
                
            # Get unique plugin IDs
            plugin_ids = set()
            for key, metric in metrics["custom"].items():
                plugin_ids.add(metric["plugin_id"])
                
            # Update combobox values
            values = ["All Plugins"] + sorted(list(plugin_ids))
            self.plugin_filter_combo["values"] = values
            
            # Assign colors to plugins if not already assigned
            for plugin_id in plugin_ids:
                if plugin_id not in self.plugin_colors:
                    self.plugin_colors[plugin_id] = self.get_random_color()
                    
        except Exception as e:
            self.log(f"Error refreshing plugin list: {e}", "ERROR")
            
    def get_random_color(self):
        """Generate a random color that is distinct from existing colors"""
        # List of distinct colors that work well on graphs
        colors = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
            "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5"
        ]
        
        # If we've used all colors, generate a random one
        if len(self.plugin_colors) >= len(colors):
            while True:
                # Generate a bright, distinguishable color
                r = random.randint(0, 200)  # Not too dark
                g = random.randint(0, 200)
                b = random.randint(0, 200)
                
                # Ensure some brightness
                if r + g + b < 250:  # Avoid too dark colors
                    continue
                    
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Check if this color is too similar to existing ones
                if color not in self.plugin_colors.values():
                    return color
        else:
            # Use a pre-defined color
            used_colors = set(self.plugin_colors.values())
            for color in colors:
                if color not in used_colors:
                    return color
                    
            # Fallback
            return "#000000"
            
    def on_plugin_filter_changed(self, event=None):
        """Handle plugin filter change"""
        self.update_plugin_metrics()
        
    def update_plugin_metrics(self):
        """Update the plugin metrics tab with custom metrics"""
        if not self.system_monitor:
            return
            
        try:
            # Clear existing items
            for item in self.plugins_tree.get_children():
                self.plugins_tree.delete(item)
                
            # Get custom metrics if available
            metrics = getattr(self.system_monitor, "get_all_metrics", lambda: {"custom": {}})()
            
            if "custom" not in metrics:
                return
                
            # Get selected plugin filter
            plugin_filter = self.plugin_filter_var.get()
            
            # Group metrics by plugin
            plugin_metrics = {}
            for key, metric in metrics["custom"].items():
                plugin_id = metric["plugin_id"]
                
                # Apply filter
                if plugin_filter != "All Plugins" and plugin_filter != plugin_id:
                    continue
                    
                if plugin_id not in plugin_metrics:
                    plugin_metrics[plugin_id] = []
                    
                plugin_metrics[plugin_id].append((key, metric))
                
            # Add each plugin group
            for plugin_id, metrics_list in sorted(plugin_metrics.items()):
                # Create plugin node
                plugin_node = self.plugins_tree.insert("", "end", text=plugin_id, open=True, 
                                                   tags=("plugin",))
                
                # Add each metric
                for key, metric in sorted(metrics_list):
                    metadata = metric["metadata"]
                    
                    # Format the value
                    value = metric["value"]
                    if metadata["format"] == "percentage":
                        formatted_value = f"{value:.1f}%"
                    elif metadata["format"] == "numeric":
                        formatted_value = f"{value:.2f} {metadata.get('unit', '')}"
                    else:
                        formatted_value = str(value)
                        
                    # Get metric name and ID
                    metric_name = metadata["name"]
                    metric_id = key.split(":", 1)[1] if ":" in key else key
                    
                    # Add to tree
                    self.plugins_tree.insert(plugin_node, "end", text=metric_name, 
                                          values=(formatted_value, metadata["format"], metadata["description"]),
                                          tags=(plugin_id, metric_id, key))
                    
        except Exception as e:
            self.log(f"Error updating plugin metrics: {e}", "ERROR")
            
    def show_plugins_tree_menu(self, event):
        """Show context menu for plugin metrics tree"""
        # Select row under mouse
        iid = self.plugins_tree.identify_row(event.y)
        if iid:
            # Select this item
            self.plugins_tree.selection_set(iid)
            
            # Get item tags to check if it's a metric or plugin
            tags = self.plugins_tree.item(iid, "tags")
            
            if tags and len(tags) > 2:  # It's a metric item
                self.plugin_metrics_menu.entryconfigure("Add to Graph", state="normal")
                self.plugin_metrics_menu.entryconfigure("Remove from Graph", state="normal")
                self.plugin_metrics_menu.entryconfigure("Show Details", state="normal")
            else:
                # It's a plugin header
                self.plugin_metrics_menu.entryconfigure("Add to Graph", state="disabled")
                self.plugin_metrics_menu.entryconfigure("Remove from Graph", state="disabled")
                self.plugin_metrics_menu.entryconfigure("Show Details", state="disabled")
                
            # Show the menu
            self.plugin_metrics_menu.post(event.x_root, event.y_root)
            
    def add_selected_metric_to_graph(self):
        """Add the selected metric to the graph"""
        selection = self.plugins_tree.selection()
        if not selection:
            return
            
        # Get the selected item
        item_id = selection[0]
        tags = self.plugins_tree.item(item_id, "tags")
        
        if not tags or len(tags) < 3:
            # Not a metric item
            return
            
        plugin_id, metric_id, key = tags
        
        # Get the metric name for the graph label
        metric_name = self.plugins_tree.item(item_id, "text")
        
        # Add to graph
        self.add_custom_metric_to_graph(key, metric_name, color=self.plugin_colors.get(plugin_id))
        
        # Show the graph tab
        self.notebook.select(self.graph_tab)
        
        self.log(f"Added metric {metric_name} from plugin {plugin_id} to graph")
        
    def remove_selected_metric_from_graph(self):
        """Remove the selected metric from the graph"""
        selection = self.plugins_tree.selection()
        if not selection:
            return
            
        # Get the selected item
        item_id = selection[0]
        tags = self.plugins_tree.item(item_id, "tags")
        
        if not tags or len(tags) < 3:
            # Not a metric item
            return
            
        plugin_id, metric_id, key = tags
        
        # Remove from graph
        self.remove_custom_metric_from_graph(key)
        
    def show_metric_details(self):
        """Show details for the selected metric"""
        selection = self.plugins_tree.selection()
        if not selection:
            return
            
        # Get the selected item
        item_id = selection[0]
        tags = self.plugins_tree.item(item_id, "tags")
        
        if not tags or len(tags) < 3:
            # Not a metric item
            return
            
        plugin_id, metric_id, key = tags
        
        # Get custom metrics
        metrics = getattr(self.system_monitor, "get_all_metrics", lambda: {"custom": {}})()
        
        if "custom" not in metrics or key not in metrics["custom"]:
            return
            
        metric = metrics["custom"][key]
        metadata = metric["metadata"]
        
        # Create details dialog
        dialog = tk.Toplevel()
        dialog.title(f"Metric Details: {metadata['name']}")
        dialog.geometry("400x300")
        dialog.transient(self.master)
        dialog.grab_set()
        
        # Add details
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add metric information
        ttk.Label(frame, text=metadata['name'], font=("", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(frame, text="Plugin:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame, text=plugin_id).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(frame, text="Metric ID:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame, text=metric_id).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(frame, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=2)
        desc_label = ttk.Label(frame, text=metadata['description'], wraplength=250)
        desc_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(frame, text="Format:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame, text=metadata['format']).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        if 'unit' in metadata:
            ttk.Label(frame, text="Unit:").grid(row=5, column=0, sticky=tk.W, pady=2)
            ttk.Label(frame, text=metadata['unit']).grid(row=5, column=1, sticky=tk.W, pady=2)
            
        ttk.Label(frame, text="Current Value:").grid(row=6, column=0, sticky=tk.W, pady=2)
        
        # Format the value
        value = metric["value"]
        if metadata["format"] == "percentage":
            formatted_value = f"{value:.1f}%"
        elif metadata["format"] == "numeric":
            formatted_value = f"{value:.2f} {metadata.get('unit', '')}"
        else:
            formatted_value = str(value)
            
        ttk.Label(frame, text=formatted_value).grid(row=6, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(frame, text="Last Updated:").grid(row=7, column=0, sticky=tk.W, pady=2)
        update_time = datetime.datetime.fromtimestamp(metric["timestamp"]).strftime("%H:%M:%S")
        ttk.Label(frame, text=update_time).grid(row=7, column=1, sticky=tk.W, pady=2)
        
        # Add buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(20, 0), sticky=tk.E)
        
        ttk.Button(button_frame, text="Add to Graph", 
                  command=lambda: self.add_custom_metric_to_graph(key, metadata['name'], 
                                                              color=self.plugin_colors.get(plugin_id))).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def add_custom_metric_to_graph(self, metric_key: str, display_name: str = None, 
                                 color: str = None, visible: bool = True):
        """
        Add a custom metric to the graph
        
        Args:
            metric_key: Metric key (used for fetching data)
            display_name: Display name for the metric in the legend
            color: Optional color for the metric line
            visible: Initial visibility of the metric line
        """
        if not display_name:
            display_name = metric_key.split(":", 1)[1] if ":" in metric_key else metric_key
            
        if metric_key in self.custom_metrics:
            # Metric already exists, just make it visible if needed
            if visible and metric_key in self.metric_visibility_vars:
                self.metric_visibility_vars[metric_key].set(True)
                self.update_graph_visibility()
            return
            
        # Initialize data for the custom metric
        self.custom_metrics[metric_key] = {
            "data": [0] * self.data_points,
            "line": None,
            "color": color,
            "visible": visible,
            "display_name": display_name,
            "metric_key": metric_key
        }
        
        # Add the metric line to the graph
        if hasattr(self, 'subplot') and self.subplot:
            if color:
                self.custom_metrics[metric_key]["line"], = self.subplot.plot(
                    self.time_data, 
                    self.custom_metrics[metric_key]["data"], 
                    color=color, 
                    label=display_name,
                    visible=visible
                )
            else:
                self.custom_metrics[metric_key]["line"], = self.subplot.plot(
                    self.time_data, 
                    self.custom_metrics[metric_key]["data"], 
                    label=display_name,
                    visible=visible
                )
            
            # Update legend
            self.subplot.legend()
            self.canvas.draw()
            
        # Add checkbox for visibility control
        if hasattr(self, 'plugin_checkboxes_frame') and self.plugin_checkboxes_frame:
            var = tk.BooleanVar(value=visible)
            self.metric_visibility_vars[metric_key] = var
            
            # Create frame for checkbox and remove button
            metric_frame = ttk.Frame(self.plugin_checkboxes_frame)
            metric_frame.pack(fill=tk.X, padx=2, pady=1)
            
            # Add color indicator
            if color:
                color_indicator = tk.Label(metric_frame, text="   ", bg=color, relief=tk.RIDGE)
                color_indicator.pack(side=tk.LEFT, padx=(0, 5))
            
            # Add checkbox
            cb = ttk.Checkbutton(
                metric_frame, 
                text=display_name, 
                variable=var,
                command=self.update_graph_visibility
            )
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Add remove button
            remove_btn = ttk.Button(
                metric_frame, 
                text="X", 
                width=2,
                command=lambda key=metric_key: self.remove_custom_metric_from_graph(key)
            )
            remove_btn.pack(side=tk.RIGHT)
            
    def remove_custom_metric_from_graph(self, metric_key: str):
        """
        Remove a custom metric from the graph
        
        Args:
            metric_key: Metric key
        """
        if metric_key not in self.custom_metrics:
            return  # Metric not found
            
        # Remove the metric line from the graph
        info = self.custom_metrics[metric_key]
        line = info["line"]
        if line:
            line.remove()
            
        # Remove from custom metrics
        del self.custom_metrics[metric_key]
        
        # Remove checkbox
        if metric_key in self.metric_visibility_vars:
            # Find and destroy the frame containing this metric's checkbox
            for widget in self.plugin_checkboxes_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Checkbutton) and child.cget("text") == info["display_name"]:
                        widget.destroy()
                        break
            
            # Remove from variables
            del self.metric_visibility_vars[metric_key]
        
        # Redraw the graph
        self.subplot.legend()
        self.canvas.draw()
        
    def remove_all_custom_metrics(self):
        """Remove all custom metrics from the graph"""
        # Ask for confirmation
        if messagebox.askyesno("Remove Custom Metrics", "Are you sure you want to remove all custom metrics?"):
            # Get keys first to avoid modifying dict during iteration
            keys = list(self.custom_metrics.keys())
            for key in keys:
                self.remove_custom_metric_from_graph(key)
                
    def export_metrics(self):
        """Export metrics to a file"""
        import tkinter.filedialog as filedialog
        import datetime
        
        if not self.system_monitor:
            return
            
        # Get file path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"resource_metrics_{timestamp}.txt"
        
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Determine format based on extension
            if file_path.lower().endswith(".json"):
                export_format = "json"
            else:
                export_format = "text"
                
            # Export metrics
            if hasattr(self.system_monitor, "export_metrics"):
                metrics_str = self.system_monitor.export_metrics(export_format)
            else:
                # Fallback if export_metrics is not available
                metrics = self.system_monitor.get_all_metrics()
                if export_format == "json":
                    import json
                    metrics_str = json.dumps(metrics, default=str, indent=2)
                else:
                    metrics_str = str(metrics)
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(metrics_str)
                
            # Show success message
            import tkinter.messagebox as messagebox
            messagebox.showinfo("Export Complete", f"Metrics exported to {file_path}")
            
        except Exception as e:
            self.log(f"Error exporting metrics: {e}", "ERROR")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Export Error", f"Failed to export metrics: {e}")
            
    def add_custom_metric_to_graph(self, metric_key: str, display_name: str = None, 
                                 color: str = None, visible: bool = True):
        """
        Add a custom metric to the graph
        
        Args:
            metric_key: Metric key (used for fetching data)
            display_name: Display name for the metric in the legend
            color: Optional color for the metric line
            visible: Initial visibility of the metric line
        """
        if not display_name:
            display_name = metric_key.split(":", 1)[1] if ":" in metric_key else metric_key
            
        if metric_key in self.custom_metrics:
            # Metric already exists, just make it visible if needed
            if visible and metric_key in self.metric_visibility_vars:
                self.metric_visibility_vars[metric_key].set(True)
                self.update_graph_visibility()
            return
            
        # Initialize data for the custom metric
        self.custom_metrics[metric_key] = {
            "data": [0] * self.data_points,
            "line": None,
            "color": color,
            "visible": visible,
            "display_name": display_name,
            "metric_key": metric_key
        }
        
        # Add the metric line to the graph
        if hasattr(self, 'subplot') and self.subplot:
            if color:
                self.custom_metrics[metric_key]["line"], = self.subplot.plot(
                    self.time_data, 
                    self.custom_metrics[metric_key]["data"], 
                    color=color, 
                    label=display_name,
                    visible=visible
                )
            else:
                self.custom_metrics[metric_key]["line"], = self.subplot.plot(
                    self.time_data, 
                    self.custom_metrics[metric_key]["data"], 
                    label=display_name,
                    visible=visible
                )
            
            # Update legend
            self.subplot.legend()
            self.canvas.draw()
            
        # Add checkbox for visibility control
        if hasattr(self, 'plugin_checkboxes_frame') and self.plugin_checkboxes_frame:
            var = tk.BooleanVar(value=visible)
            self.metric_visibility_vars[metric_key] = var
            
            # Create frame for checkbox and remove button
            metric_frame = ttk.Frame(self.plugin_checkboxes_frame)
            metric_frame.pack(fill=tk.X, padx=2, pady=1)
            
            # Add color indicator
            if color:
                color_indicator = tk.Label(metric_frame, text="   ", bg=color, relief=tk.RIDGE)
                color_indicator.pack(side=tk.LEFT, padx=(0, 5))
            
            # Add checkbox
            cb = ttk.Checkbutton(
                metric_frame, 
                text=display_name, 
                variable=var,
                command=self.update_graph_visibility
            )
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Add remove button
            remove_btn = ttk.Button(
                metric_frame, 
                text="X", 
                width=2,
                command=lambda key=metric_key: self.remove_custom_metric_from_graph(key)
            )
            remove_btn.pack(side=tk.RIGHT)
            
    def remove_custom_metric_from_graph(self, metric_key: str):
        """
        Remove a custom metric from the graph
        
        Args:
            metric_key: Metric key
        """
        if metric_key not in self.custom_metrics:
            return  # Metric not found
            
        # Remove the metric line from the graph
        info = self.custom_metrics[metric_key]
        line = info["line"]
        if line:
            line.remove()
            
        # Remove from custom metrics
        del self.custom_metrics[metric_key]
        
        # Remove checkbox
        if metric_key in self.metric_visibility_vars:
            # Find and destroy the frame containing this metric's checkbox
            for widget in self.plugin_checkboxes_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Checkbutton) and child.cget("text") == info["display_name"]:
                        widget.destroy()
                        break
            
            # Remove from variables
            del self.metric_visibility_vars[metric_key]
        
        # Redraw the graph
        self.subplot.legend()
        self.canvas.draw()
        
    def remove_all_custom_metrics(self):
        """Remove all custom metrics from the graph"""
        # Ask for confirmation
        if messagebox.askyesno("Remove Custom Metrics", "Are you sure you want to remove all custom metrics?"):
            # Get keys first to avoid modifying dict during iteration
            keys = list(self.custom_metrics.keys())
            for key in keys:
                self.remove_custom_metric_from_graph(key)
                
    def export_metrics(self):
        """Export metrics to a file"""
        import tkinter.filedialog as filedialog
        import datetime
        
        if not self.system_monitor:
            return
            
        # Get file path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"resource_metrics_{timestamp}.txt"
        
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Determine format based on extension
            if file_path.lower().endswith(".json"):
                export_format = "json"
            else:
                export_format = "text"
                
            # Export metrics
            if hasattr(self.system_monitor, "export_metrics"):
                metrics_str = self.system_monitor.export_metrics(export_format)
            else:
                # Fallback if export_metrics is not available
                metrics = self.system_monitor.get_all_metrics()
                if export_format == "json":
                    import json
                    metrics_str = json.dumps(metrics, default=str, indent=2)
                else:
                    metrics_str = str(metrics)
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(metrics_str)
                
            # Show success message
            import tkinter.messagebox as messagebox
            messagebox.showinfo("Export Complete", f"Metrics exported to {file_path}")
            
        except Exception as e:
            self.log(f"Error exporting metrics: {e}", "ERROR")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Export Error", f"Failed to export metrics: {e}")
            
    def add_custom_metric_to_graph(self, metric_key: str, display_name: str = None, 
                                 color: str = None, visible: bool = True):
        """
        Add a custom metric to the graph
        
        Args:
            metric_key: Metric key (used for fetching data)
            display_name: Display name for the metric in the legend
            color: Optional color for the metric line
            visible: Initial visibility of the metric line
        """
        if not display_name:
            display_name = metric_key.split(":", 1)[1] if ":" in metric_key else metric_key
            
        if metric_key in self.custom_metrics:
            # Metric already exists, just make it visible if needed
            if visible and metric_key in self.metric_visibility_vars:
                self.metric_visibility_vars[metric_key].set(True)
                self.update_graph_visibility()
            return
            
        # Initialize data for the custom metric
        self.custom_metrics[metric_key] = {
            "data": [0] * self.data_points,
            "line": None,
            "color": color,
            "visible": visible,
            "display_name": display_name,
            "metric_key": metric_key
        }
        
        # Add the metric line to the graph
        if hasattr(self, 'subplot') and self.subplot:
            if color:
                self.custom_metrics[metric_key]["line"], = self.subplot.plot(
                    self.time_data, 
                    self.custom_metrics[metric_key]["data"], 
                    color=color, 
                    label=display_name,
                    visible=visible
                )
            else:
                self.custom_metrics[metric_key]["line"], = self.subplot.plot(
                    self.time_data, 
                    self.custom_metrics[metric_key]["data"], 
                    label=display_name,
                    visible=visible
                )
            
            # Update legend
            self.subplot.legend()
            self.canvas.draw()
            
        # Add checkbox for visibility control
        if hasattr(self, 'plugin_checkboxes_frame') and self.plugin_checkboxes_frame:
            var = tk.BooleanVar(value=visible)
            self.metric_visibility_vars[metric_key] = var
            
            # Create frame for checkbox and remove button
            metric_frame = ttk.Frame(self.plugin_checkboxes_frame)
            metric_frame.pack(fill=tk.X, padx=2, pady=1)
            
            # Add color indicator
            if color:
                color_indicator = tk.Label(metric_frame, text="   ", bg=color, relief=tk.RIDGE)
                color_indicator.pack(side=tk.LEFT, padx=(0, 5))
            
            # Add checkbox
            cb = ttk.Checkbutton(
                metric_frame, 
                text=display_name, 
                variable=var,
                command=self.update_graph_visibility
            )
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Add remove button
            remove_btn = ttk.Button(
                metric_frame, 
                text="X", 
                width=2,
                command=lambda key=metric_key: self.remove_custom_metric_from_graph(key)
            )
            remove_btn.pack(side=tk.RIGHT)
            
    def remove_custom_metric_from_graph(self, metric_key: str):
        """
        Remove a custom metric from the graph
        
        Args:
            metric_key: Metric key
        """
        if metric_key not in self.custom_metrics:
            return  # Metric not found
            
        # Remove the metric line from the graph
        info = self.custom_metrics[metric_key]
        line = info["line"]
        if line:
            line.remove()
            
        # Remove from custom metrics
        del self.custom_metrics[metric_key]
        
        # Remove checkbox
        if metric_key in self.metric_visibility_vars:
            # Find and destroy the frame containing this metric's checkbox
            for widget in self.plugin_checkboxes_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Checkbutton) and child.cget("text") == info["display_name"]:
                        widget.destroy()
                        break
            
            # Remove from variables
            del self.metric_visibility_vars[metric_key]
        
        # Redraw the graph
        self.subplot.legend()
        self.canvas.draw()
        
    def remove_all_custom_metrics(self):
        """Remove all custom metrics from the graph"""
        # Ask for confirmation
        if messagebox.askyesno("Remove Custom Metrics", "Are you sure you want to remove all custom metrics?"):
            # Get keys first to avoid modifying dict during iteration
            keys = list(self.custom_metrics.keys())
            for key in keys:
                self.remove_custom_metric_from_graph(key)
                
    def update_custom_metrics_data(self):
        """Update data for custom metrics"""
        if not self.system_monitor or not self.custom_metrics:
            return
            
        try:
            # Get custom metrics
            metrics = getattr(self.system_monitor, "get_all_metrics", lambda: {"custom": {}})()
            
            if "custom" not in metrics:
                return
                
            # Update each custom metric
            for key, info in self.custom_metrics.items():
                if key in metrics["custom"]:
                    metric = metrics["custom"][key]
                    value = metric["value"]
                    
                    # Convert to percentage for the graph if needed
                    if metric["metadata"]["format"] == "percentage":
                        # Already a percentage, use directly
                        graph_value = float(value)
                    elif metric["metadata"]["format"] == "numeric":
                        # Scale numeric values to fit in the graph (0-100)
                        # We need to estimate a reasonable scale
                        if hasattr(self, "_metric_max_values"):
                            # Update max value if needed
                            if key not in self._metric_max_values or value > self._metric_max_values[key]:
                                self._metric_max_values[key] = max(1.0, value * 1.1)  # Add 10% margin
                        else:
                            # Initialize max values dictionary
                            self._metric_max_values = {key: max(1.0, value * 1.1)}
                            
                        # Scale to 0-100 based on max value seen so far
                        max_value = self._metric_max_values[key]
                        graph_value = (value / max_value) * 100
                        graph_value = min(100, graph_value)  # Cap at 100%
                    else:
                        # For text metrics, just use 50% as a visual indicator
                        graph_value = 50
                        
                    # Update data
                    info["data"].append(graph_value)
                    info["data"].pop(0)
                else:
                    # Metric not available, add 0
                    info["data"].append(0)
                    info["data"].pop(0)
                    
        except Exception as e:
            self.log(f"Error updating custom metrics data: {e}", "ERROR")

    def refresh(self): # <<< ADD THIS METHOD
        """Manually refresh the displayed metrics."""
        self.log("Manual refresh triggered")
        # Stop the automatic timer temporarily to avoid race conditions
        is_running = self.running
        if is_running:
            self.stop_monitoring()

        # Force an immediate update of metrics
        # We can call the logic from update_metrics directly here
        # Or, if update_metrics is complex, extract the core update logic
        # into a helper method called by both refresh() and update_metrics().
        # For simplicity, let's reuse the update_metrics core logic:
        try:
            if self.system_monitor:
                # Get system info
                system_info = self.system_monitor.get_system_info()

                # Update top labels
                cpu_usage = system_info["cpu"]["usage_percent"]
                self.cpu_label.config(text=f"CPU: {cpu_usage:.1f}%")

                ram_usage = system_info["ram"]["usage_percent"]
                self.ram_label.config(text=f"RAM: {ram_usage:.1f}%")

                gpu_usage = system_info["gpu"]["usage_percent"]
                self.gpu_label.config(text=f"GPU: {gpu_usage}")

                disk_usage = system_info["disk"]["usage_percent"]
                self.disk_label.config(text=f"Disk: {disk_usage:.1f}%")

                # Update system tab details
                self.update_system_details(system_info)

                # Update processes tab
                self.update_processes()

                # Update plugin metrics tab
                self.update_plugin_metrics()

                # Note: We don't update the graph data here, as refresh
                #       is usually for the static displays, not the time-series graph.
                #       If graph update is desired, uncomment graph update lines from
                #       update_metrics here.

            else:
                # Handle case where system_monitor is not available
                 self.log("System monitor not available for refresh.", "WARNING")


        except Exception as e:
            self.log(f"Error during manual refresh: {e}", "ERROR")

        # Restart the automatic timer if it was running
        if is_running:
            self.start_monitoring()


    def update_metrics(self):
        """Update resource metrics display"""
        if not self.running:
            return

        try:
            if self.system_monitor:
                # Get system info
                system_info = self.system_monitor.get_system_info()

                # Update top labels
                cpu_usage = system_info["cpu"]["usage_percent"]
                self.cpu_label.config(text=f"CPU: {cpu_usage:.1f}%")

                ram_usage = system_info["ram"]["usage_percent"]
                self.ram_label.config(text=f"RAM: {ram_usage:.1f}%")

                gpu_usage = system_info["gpu"]["usage_percent"]
                self.gpu_label.config(text=f"GPU: {gpu_usage}")

                disk_usage = system_info["disk"]["usage_percent"]
                self.disk_label.config(text=f"Disk: {disk_usage:.1f}%")

                # Update graph data
                self.cpu_data.append(cpu_usage)
                self.cpu_data.pop(0)

                self.ram_data.append(ram_usage)
                self.ram_data.pop(0)

                try:
                    if gpu_usage != "N/A":
                        gpu_value = float(gpu_usage.replace("%", ""))
                    else:
                        gpu_value = 0
                except:
                    gpu_value = 0

                self.gpu_data.append(gpu_value)
                self.gpu_data.pop(0)

                # Update custom metrics
                self.update_custom_metrics_data()

                # Update graph lines
                self.cpu_line.set_ydata(self.cpu_data)
                self.ram_line.set_ydata(self.ram_data)
                self.gpu_line.set_ydata(self.gpu_data)

                for key, info in self.custom_metrics.items():
                    if info["line"]:
                        info["line"].set_ydata(info["data"])

                # Draw the canvas
                self.canvas.draw_idle()

                # Update system tab details
                self.update_system_details(system_info)

                # Update processes tab
                self.update_processes()

                # Update plugin metrics tab
                self.update_plugin_metrics()

            else:
                # No system monitor available
                self.cpu_label.config(text="CPU: N/A")
                self.ram_label.config(text="RAM: N/A")
                self.gpu_label.config(text="GPU: N/A")
                self.disk_label.config(text="Disk: N/A")

        except Exception as e:
            self.log(f"Error updating metrics: {e}", "ERROR")

        finally:
            # Schedule next update only if still running
            if self.running:
                self.update_timer_id = self.frame.after(self.update_interval, self.update_metrics)

    def update_system_details(self, system_info: Dict[str, Any]):
        """
        Update the system details treeview
        
        Args:
            system_info: System information dictionary
        """
        # Clear existing items
        for item in self.system_tree.get_children(self.cpu_item):
            self.system_tree.delete(item)
        for item in self.system_tree.get_children(self.ram_item):
            self.system_tree.delete(item)
        for item in self.system_tree.get_children(self.gpu_item):
            self.system_tree.delete(item)
        for item in self.system_tree.get_children(self.disk_item):
            self.system_tree.delete(item)
            
        # Add CPU info
        cpu_usage = system_info["cpu"]["usage_percent"]
        self.system_tree.insert(self.cpu_item, "end", values=("Usage", f"{cpu_usage:.1f}%"))
        
        # Get additional CPU info from psutil if available
        try:
            cpu_count = psutil.cpu_count(logical=False)
            logical_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            self.system_tree.insert(self.cpu_item, "end", values=("Physical cores", str(cpu_count)))
            self.system_tree.insert(self.cpu_item, "end", values=("Logical cores", str(logical_count)))
            
            if cpu_freq:
                self.system_tree.insert(self.cpu_item, "end", 
                                     values=("Current frequency", f"{cpu_freq.current:.0f} MHz"))
                if hasattr(cpu_freq, "min") and cpu_freq.min:
                    self.system_tree.insert(self.cpu_item, "end", 
                                         values=("Min frequency", f"{cpu_freq.min:.0f} MHz"))
                if hasattr(cpu_freq, "max") and cpu_freq.max:
                    self.system_tree.insert(self.cpu_item, "end", 
                                         values=("Max frequency", f"{cpu_freq.max:.0f} MHz"))
        except:
            pass
            
        # Add RAM info
        ram_percent = system_info["ram"]["usage_percent"]
        ram_used = system_info["ram"]["used_gb"]
        ram_total = system_info["ram"]["total_gb"]
        
        self.system_tree.insert(self.ram_item, "end", values=("Usage", f"{ram_percent:.1f}%"))
        self.system_tree.insert(self.ram_item, "end", values=("Used", f"{ram_used:.2f} GB"))
        self.system_tree.insert(self.ram_item, "end", values=("Total", f"{ram_total:.2f} GB"))
        self.system_tree.insert(self.ram_item, "end", values=("Free", f"{ram_total - ram_used:.2f} GB"))
        
        # Get additional memory info from psutil if available
        try:
            swap = psutil.swap_memory()
            self.system_tree.insert(self.ram_item, "end", values=("Swap usage", f"{swap.percent:.1f}%"))
            self.system_tree.insert(self.ram_item, "end", values=("Swap used", f"{swap.used / (1024**3):.2f} GB"))
            self.system_tree.insert(self.ram_item, "end", values=("Swap total", f"{swap.total / (1024**3):.2f} GB"))
        except:
            pass
            
        # Add GPU info
        gpu_usage = system_info["gpu"]["usage_percent"]
        gpu_memory = system_info["gpu"]["memory"]
        
        self.system_tree.insert(self.gpu_item, "end", values=("Usage", str(gpu_usage)))
        self.system_tree.insert(self.gpu_item, "end", values=("Memory", str(gpu_memory)))
        
        # Add additional GPU info from nvidia-smi if available
        try:
            if hasattr(self.system_monitor, 'get_gpu_info'):
                gpu_info = self.system_monitor.get_gpu_info()
                if gpu_info:
                    for key, value in gpu_info.items():
                        if key not in ["usage_percent", "memory"]:
                            self.system_tree.insert(self.gpu_item, "end", values=(key.replace("_", " ").title(), str(value)))
        except:
            pass
            
        # Add Disk info
        disk_percent = system_info["disk"]["usage_percent"]
        disk_free = system_info["disk"]["free_gb"]
        disk_total = system_info["disk"]["total_gb"]
        
        self.system_tree.insert(self.disk_item, "end", values=("Usage", f"{disk_percent:.1f}%"))
        self.system_tree.insert(self.disk_item, "end", values=("Free", f"{disk_free:.2f} GB"))
        self.system_tree.insert(self.disk_item, "end", values=("Total", f"{disk_total:.2f} GB"))
        self.system_tree.insert(self.disk_item, "end", values=("Used", f"{disk_total - disk_free:.2f} GB"))