"""
Dashboard UI component for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import time
import datetime
import os
import sys
from typing import Dict, List, Any, Optional, Callable

class Dashboard:
    """Dashboard for displaying session statistics and system information"""
    
    def __init__(self, parent, chat_engine, model_manager, memory_system, system_monitor, logger: Callable):
        """
        Initialize the dashboard
        
        Args:
            parent: Parent widget
            chat_engine: ChatEngine instance
            model_manager: ModelManager instance
            memory_system: MemorySystem instance
            system_monitor: SystemMonitor instance
            logger: Logging function
        """
        self.parent = parent
        self.chat_engine = chat_engine
        self.model_manager = model_manager
        self.memory_system = memory_system
        self.system_monitor = system_monitor
        self.log = logger
        
        # Create top-level window
        self.window = tk.Toplevel(parent)
        self.window.title("Irintai Dashboard")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        
        # Initialize UI components
        self.initialize_ui()
        
        # Initialize plugin extensions
        self.initialize_plugin_extensions()
        
        # Update statistics
        self.update_statistics()
        
        # Schedule periodic updates
        self.schedule_updates()
        
    def initialize_ui(self):
        """Initialize the UI components"""
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create overview tab
        self.create_overview_tab()
        
        # Create chat statistics tab
        self.create_chat_stats_tab()
        
        # Create system information tab
        self.create_system_info_tab()
        
        # Create memory statistics tab
        self.create_memory_stats_tab()
        
        # Create status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.window, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add refresh button
        refresh_button = ttk.Button(
            self.window,
            text="Refresh Stats",
            command=self.update_statistics
        )
        refresh_button.pack(side=tk.BOTTOM, pady=5)
        
    def create_overview_tab(self):
        """Create the overview tab"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="Overview")
        
        # Add header
        ttk.Label(
            overview_frame, 
            text="Session Overview", 
            font=("Helvetica", 16, "bold")
        ).pack(pady=10)
        
        # Create stats grid
        stats_frame = ttk.Frame(overview_frame)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Configure grid columns
        for i in range(2):
            stats_frame.columnconfigure(i, weight=1)
            
        # Row 1: Total interactions
        ttk.Label(
            stats_frame, 
            text="Total Interactions:", 
            font=("Helvetica", 12)
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.total_interactions_var = tk.StringVar(value="0")
        ttk.Label(
            stats_frame, 
            textvariable=self.total_interactions_var,
            font=("Helvetica", 12, "bold"),
            foreground="blue"
        ).grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Row 2: Current model
        ttk.Label(
            stats_frame, 
            text="Current Model:", 
            font=("Helvetica", 12)
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.current_model_var = tk.StringVar(value="None")
        ttk.Label(
            stats_frame, 
            textvariable=self.current_model_var,
            font=("Helvetica", 12, "bold")
        ).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Row 3: Memory mode
        ttk.Label(
            stats_frame, 
            text="Memory Mode:", 
            font=("Helvetica", 12)
        ).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.memory_mode_var = tk.StringVar(value="Off")
        ttk.Label(
            stats_frame, 
            textvariable=self.memory_mode_var,
            font=("Helvetica", 12)
        ).grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Row 4: Vector store size
        ttk.Label(
            stats_frame, 
            text="Vector Store:", 
            font=("Helvetica", 12)
        ).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.vector_store_var = tk.StringVar(value="0 documents")
        ttk.Label(
            stats_frame, 
            textvariable=self.vector_store_var,
            font=("Helvetica", 12)
        ).grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Performance frame
        perf_frame = ttk.LabelFrame(overview_frame, text="System Performance")
        perf_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # CPU usage
        cpu_frame = ttk.Frame(perf_frame)
        cpu_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(cpu_frame, text="CPU Usage:").pack(side=tk.LEFT, padx=5)
        
        self.cpu_var = tk.StringVar(value="0%")
        ttk.Label(
            cpu_frame, 
            textvariable=self.cpu_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        self.cpu_progress = ttk.Progressbar(
            cpu_frame, 
            length=200,
            mode="determinate",
            maximum=100
        )
        self.cpu_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # RAM usage
        ram_frame = ttk.Frame(perf_frame)
        ram_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ram_frame, text="RAM Usage:").pack(side=tk.LEFT, padx=5)
        
        self.ram_var = tk.StringVar(value="0%")
        ttk.Label(
            ram_frame, 
            textvariable=self.ram_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        self.ram_progress = ttk.Progressbar(
            ram_frame, 
            length=200,
            mode="determinate",
            maximum=100
        )
        self.ram_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # GPU usage (if available)
        gpu_frame = ttk.Frame(perf_frame)
        gpu_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(gpu_frame, text="GPU Usage:").pack(side=tk.LEFT, padx=5)
        
        self.gpu_var = tk.StringVar(value="N/A")
        ttk.Label(
            gpu_frame, 
            textvariable=self.gpu_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        self.gpu_progress = ttk.Progressbar(
            gpu_frame, 
            length=200,
            mode="determinate",
            maximum=100
        )
        self.gpu_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Disk usage
        disk_frame = ttk.Frame(perf_frame)
        disk_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(disk_frame, text="Disk Space:").pack(side=tk.LEFT, padx=5)
        
        self.disk_var = tk.StringVar(value="0 GB free")
        ttk.Label(
            disk_frame, 
            textvariable=self.disk_var,
            width=15
        ).pack(side=tk.LEFT)
        
        # Recent activity section
        activity_frame = ttk.LabelFrame(overview_frame, text="Recent Activity")
        activity_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Timeline of recent messages
        self.activity_text = scrolledtext.ScrolledText(
            activity_frame,
            wrap=tk.WORD,
            height=6,
            font=("Helvetica", 9)
        )
        self.activity_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags
        self.activity_text.tag_configure("timestamp", foreground="gray", font=("Helvetica", 9, "italic"))
        self.activity_text.tag_configure("user", foreground="blue", font=("Helvetica", 9, "bold"))
        self.activity_text.tag_configure("assistant", foreground="green", font=("Helvetica", 9, "bold"))
        self.activity_text.tag_configure("system", foreground="purple", font=("Helvetica", 9, "bold"))
        
    def create_chat_stats_tab(self):
        """Create the chat statistics tab"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text="Chat Stats")
        
        # Conversation analysis
        analysis_frame = ttk.LabelFrame(chat_frame, text="Conversation Analysis")
        analysis_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Message counts
        counts_frame = ttk.Frame(analysis_frame)
        counts_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create a grid for counts
        for i in range(2):
            counts_frame.columnconfigure(i, weight=1)
            
        # Row 1: User messages
        ttk.Label(counts_frame, text="User Messages:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.user_count_var = tk.StringVar(value="0")
        ttk.Label(counts_frame, textvariable=self.user_count_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 2: Assistant messages
        ttk.Label(counts_frame, text="Assistant Responses:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.assistant_count_var = tk.StringVar(value="0")
        ttk.Label(counts_frame, textvariable=self.assistant_count_var, font=("Helvetica", 10, "bold")).grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 3: Avg response length
        ttk.Label(counts_frame, text="Avg Response Length:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.avg_length_var = tk.StringVar(value="0 chars")
        ttk.Label(counts_frame, textvariable=self.avg_length_var, font=("Helvetica", 10)).grid(row=2, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 4: Session duration
        ttk.Label(counts_frame, text="Session Duration:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.duration_var = tk.StringVar(value="0 minutes")
        ttk.Label(counts_frame, textvariable=self.duration_var, font=("Helvetica", 10)).grid(row=3, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Models used section
        models_frame = ttk.LabelFrame(chat_frame, text="Models Used")
        models_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a tree view for models
        columns = ("Model", "Responses", "Last Used")
        self.models_tree = ttk.Treeview(
            models_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=5
        )
        
        # Configure columns
        self.models_tree.heading("Model", text="Model Name")
        self.models_tree.heading("Responses", text="Responses")
        self.models_tree.heading("Last Used", text="Last Used")
        
        self.models_tree.column("Model", width=250, anchor=tk.W)
        self.models_tree.column("Responses", width=100, anchor=tk.CENTER)
        self.models_tree.column("Last Used", width=150, anchor=tk.CENTER)
        
        # Add scrollbar
        models_scrollbar = ttk.Scrollbar(models_frame, orient="vertical", command=self.models_tree.yview)
        self.models_tree.configure(yscrollcommand=models_scrollbar.set)
        
        # Pack the tree and scrollbar
        self.models_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        models_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_system_info_tab(self):
        """Create the system information tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="System Info")
        
        # System information section
        info_frame = ttk.LabelFrame(system_frame, text="System Information")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create a grid for info
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X, padx=10, pady=5)
        
        for i in range(2):
            info_grid.columnconfigure(i, weight=1)
            
        # Row 1: OS info
        ttk.Label(info_grid, text="Operating System:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.os_info_var = tk.StringVar(value="Unknown")
        ttk.Label(info_grid, textvariable=self.os_info_var).grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 2: Python version
        ttk.Label(info_grid, text="Python Version:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.python_var = tk.StringVar(value=f"Python {sys.version.split()[0]}")
        ttk.Label(info_grid, textvariable=self.python_var).grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 3: CPU info
        ttk.Label(info_grid, text="CPU:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.cpu_info_var = tk.StringVar(value="Unknown")
        ttk.Label(info_grid, textvariable=self.cpu_info_var).grid(row=2, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 4: RAM info
        ttk.Label(info_grid, text="RAM:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.ram_info_var = tk.StringVar(value="Unknown")
        ttk.Label(info_grid, textvariable=self.ram_info_var).grid(row=3, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 5: GPU info
        ttk.Label(info_grid, text="GPU:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.gpu_info_var = tk.StringVar(value="Unknown")
        ttk.Label(info_grid, textvariable=self.gpu_info_var).grid(row=4, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Path information section
        paths_frame = ttk.LabelFrame(system_frame, text="Path Information")
        paths_frame.pack(fill=tk.X, padx=10, pady=10)
        
        paths_grid = ttk.Frame(paths_frame)
        paths_grid.pack(fill=tk.X, padx=10, pady=5)
        
        for i in range(2):
            paths_grid.columnconfigure(i, weight=1)
            
        # Row 1: Model path
        ttk.Label(paths_grid, text="Model Path:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.model_path_var = tk.StringVar(value=self.model_manager.model_path)
        ttk.Label(paths_grid, textvariable=self.model_path_var).grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 2: Log path
        ttk.Label(paths_grid, text="Log Path:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.log_path_var = tk.StringVar(value="data/logs")
        ttk.Label(paths_grid, textvariable=self.log_path_var).grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 3: Vector store path
        ttk.Label(paths_grid, text="Vector Store Path:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.vector_path_var = tk.StringVar(value=self.memory_system.index_path)
        ttk.Label(paths_grid, textvariable=self.vector_path_var).grid(row=2, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Process information section
        process_frame = ttk.LabelFrame(system_frame, text="Process Information")
        process_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create process info text area
        self.process_text = scrolledtext.ScrolledText(
            process_frame,
            wrap=tk.WORD,
            height=10,
            font=("Courier New", 9)
        )
        self.process_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def create_memory_stats_tab(self):
        """Create the memory statistics tab"""
        memory_frame = ttk.Frame(self.notebook)
        self.notebook.add(memory_frame, text="Memory Stats")
        
        # Memory statistics section
        stats_frame = ttk.LabelFrame(memory_frame, text="Vector Store Statistics")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Stats grid
        grid_frame = ttk.Frame(stats_frame)
        grid_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for i in range(2):
            grid_frame.columnconfigure(i, weight=1)
            
        # Row 1: Document count
        ttk.Label(grid_frame, text="Total Documents:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.doc_count_var = tk.StringVar(value="0")
        ttk.Label(grid_frame, textvariable=self.doc_count_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 2: Unique sources
        ttk.Label(grid_frame, text="Unique Sources:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.source_count_var = tk.StringVar(value="0")
        ttk.Label(grid_frame, textvariable=self.source_count_var).grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 3: Embedding model
        ttk.Label(grid_frame, text="Embedding Model:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.embedding_model_var = tk.StringVar(value=self.memory_system.model_name)
        ttk.Label(grid_frame, textvariable=self.embedding_model_var).grid(row=2, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Row 4: Last updated
        ttk.Label(grid_frame, text="Last Updated:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        
        self.last_updated_var = tk.StringVar(value="Unknown")
        ttk.Label(grid_frame, textvariable=self.last_updated_var).grid(row=3, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Source breakdown section
        sources_frame = ttk.LabelFrame(memory_frame, text="Source Types")
        sources_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a tree view for source types
        columns = ("Type", "Count", "Percentage")
        self.sources_tree = ttk.Treeview(
            sources_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=6
        )
        
        # Configure columns
        self.sources_tree.heading("Type", text="File Type")
        self.sources_tree.heading("Count", text="Count")
        self.sources_tree.heading("Percentage", text="Percentage")
        
        self.sources_tree.column("Type", width=100, anchor=tk.W)
        self.sources_tree.column("Count", width=100, anchor=tk.CENTER)
        self.sources_tree.column("Percentage", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        sources_scrollbar = ttk.Scrollbar(sources_frame, orient="vertical", command=self.sources_tree.yview)
        self.sources_tree.configure(yscrollcommand=sources_scrollbar.set)
        
        # Pack the tree and scrollbar
        self.sources_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sources_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add recent searches section
        searches_frame = ttk.LabelFrame(memory_frame, text="Recent Memory Searches")
        searches_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create searches listbox
        self.searches_listbox = tk.Listbox(
            searches_frame,
            height=5,
            font=("Helvetica", 9)
        )
        self.searches_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        searches_scrollbar = ttk.Scrollbar(searches_frame, orient="vertical", command=self.searches_listbox.yview)
        self.searches_listbox.configure(yscrollcommand=searches_scrollbar.set)
        searches_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def update_statistics(self):
        """Update all statistics in the dashboard"""
        # Update session statistics
        self.update_session_stats()
        
        # Update system information
        self.update_system_info()
        
        # Update memory statistics
        self.update_memory_stats()
        
        # Update plugin statistics
        self.update_plugin_stats()
        
        # Update status
        self.status_var.set(f"Statistics updated at {time.strftime('%H:%M:%S')}")
        
    def update_plugin_stats(self):
        """Update statistics from plugin providers"""
        # Skip if no providers registered
        if not hasattr(self, "plugin_stats_providers") or not self.plugin_stats_providers:
            return
            
        # Call each provider and process the stats
        for plugin_id, provider in self.plugin_stats_providers.items():
            try:
                # Get statistics from plugin
                stats = provider()
                
                # Skip if no stats provided
                if not stats or not isinstance(stats, dict):
                    continue
                    
                # Update the plugin's dashboard if it has one
                if plugin_id in self.plugin_dashboards:
                    component = self.plugin_dashboards[plugin_id]["component"]
                    if hasattr(component, "update_stats") and callable(component.update_stats):
                        component.update_stats(stats)
                        
            except Exception as e:
                self.log(f"[Dashboard] Error updating stats for plugin {plugin_id}: {e}")

    def update_session_stats(self):
        """Update session statistics"""
        # Get chat history
        history = self.chat_engine.chat_history
        
        # Count messages by role
        user_count = sum(1 for msg in history if msg.get("role") == "user")
        assistant_count = sum(1 for msg in history if msg.get("role") == "assistant")
        
        # Update counts
        self.total_interactions_var.set(str(len(history)))
        self.user_count_var.set(str(user_count))
        self.assistant_count_var.set(str(assistant_count))
        
        # Get current model
        current_model = self.model_manager.current_model or "None"
        self.current_model_var.set(current_model)
        
        # Get memory mode
        memory_mode = self.chat_engine.memory_mode
        self.memory_mode_var.set(memory_mode)
        
        # Calculate average response length
        if assistant_count > 0:
            total_length = sum(len(msg.get("content", "")) for msg in history if msg.get("role") == "assistant")
            avg_length = total_length / assistant_count
            self.avg_length_var.set(f"{int(avg_length)} chars")
        else:
            self.avg_length_var.set("N/A")
            
        # Calculate session duration if timestamps are available
        if history and "timestamp" in history[0] and "timestamp" in history[-1]:
            try:
                start_time = datetime.datetime.strptime(history[0]["timestamp"], "%Y-%m-%d %H:%M:%S")
                end_time = datetime.datetime.strptime(history[-1]["timestamp"], "%Y-%m-%d %H:%M:%S")
                duration = end_time - start_time
                minutes = duration.total_seconds() / 60
                self.duration_var.set(f"{int(minutes)} minutes")
            except (ValueError, TypeError, KeyError):
                self.duration_var.set("Unknown")
        else:
            self.duration_var.set("Unknown")
            
        # Update models used tree
        self.update_models_used()
        
        # Update timeline
        self.update_timeline()
        
    def update_models_used(self):
        """Update the models used tree"""
        # Clear the current tree
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
            
        # Count responses by model
        model_counts = {}
        model_last_used = {}
        
        for msg in self.chat_engine.chat_history:
            if msg.get("role") == "assistant" and "model" in msg:
                model = msg["model"]
                model_counts[model] = model_counts.get(model, 0) + 1
                model_last_used[model] = msg.get("timestamp", "Unknown")
                
        # Add to tree
        for model, count in model_counts.items():
            last_used = model_last_used[model]
            self.models_tree.insert(
                "",
                tk.END,
                values=(model, count, last_used)
            )
            
    def update_timeline(self):
        """Update the timeline of recent activity"""
        # Clear the current timeline
        self.activity_text.delete(1.0, tk.END)
        
        # Get the most recent messages (up to 10)
        recent = self.chat_engine.chat_history[-min(10, len(self.chat_engine.chat_history)):]
        
        # Add each message to the timeline
        for msg in recent:
            role = msg.get("role", "")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            # Limit content length for display
            if len(content) > 100:
                content = content[:100] + "..."
                
            if timestamp:
                self.activity_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                
            if role == "user":
                self.activity_text.insert(tk.END, "User: ", "user")
                self.activity_text.insert(tk.END, f"{content}\n\n")
            elif role == "assistant":
                self.activity_text.insert(tk.END, "Irintai: ", "assistant")
                self.activity_text.insert(tk.END, f"{content}\n\n")
            else:
                self.activity_text.insert(tk.END, f"{role}: {content}\n\n")
                
    def update_system_info(self):
        """Update system information"""
        # Get system information
        info = self.system_monitor.get_system_info()
        
        # Update performance values
        cpu_percent = info["cpu"]["usage_percent"]
        self.cpu_var.set(f"{cpu_percent}%")
        self.cpu_progress["value"] = cpu_percent
        
        ram_percent = info["ram"]["usage_percent"]
        self.ram_var.set(f"{ram_percent}%")
        self.ram_progress["value"] = ram_percent
        
        gpu_percent = info["gpu"]["usage_percent"]
        self.gpu_var.set(gpu_percent)
        
        if gpu_percent != "N/A":
            try:
                gpu_value = int(gpu_percent.replace("%", ""))
                self.gpu_progress["value"] = gpu_value
            except (ValueError, TypeError):
                self.gpu_progress["value"] = 0
                
        # Update disk space
        free_space = info["disk"]["free_gb"]
        total_space = info["disk"]["total_gb"]
        self.disk_var.set(f"{free_space} GB free of {total_space} GB")
        
        # Get OS information
        import platform
        os_info = f"{platform.system()} {platform.release()}"
        self.os_info_var.set(os_info)
        
        # Get CPU information
        import psutil
        try:
            cpu_info = f"{psutil.cpu_count(logical=False)} cores, {psutil.cpu_count()} threads"
        except:
            cpu_info = f"{psutil.cpu_count()} logical processors"
        self.cpu_info_var.set(cpu_info)
        
        # Get RAM information
        ram_total = round(psutil.virtual_memory().total / (1024**3), 2)
        self.ram_info_var.set(f"{ram_total} GB")
        
        # Get GPU information
        gpu_info = "Not available"
        if gpu_percent != "N/A":
            gpu_info = info["gpu"]["memory"]
        self.gpu_info_var.set(gpu_info)
        
        # Update process information
        self.update_process_info()
        
    def update_process_info(self):
        """Update process information"""
        import psutil
        
        # Clear current text
        self.process_text.delete(1.0, tk.END)
        
        # Add process information for current process
        current_process = psutil.Process()
        
        # Add header
        self.process_text.insert(tk.END, "=== Irintai Process Information ===\n\n")
        
        # Process details
        pid = current_process.pid
        memory_info = current_process.memory_info()
        cpu_percent = current_process.cpu_percent()
        create_time = datetime.datetime.fromtimestamp(current_process.create_time()).strftime("%Y-%m-%d %H:%M:%S")
        
        self.process_text.insert(tk.END, f"PID: {pid}\n")
        self.process_text.insert(tk.END, f"Started: {create_time}\n")
        self.process_text.insert(tk.END, f"CPU Usage: {cpu_percent}%\n")
        self.process_text.insert(tk.END, f"Memory Usage: {memory_info.rss / (1024**2):.2f} MB\n\n")
        
        # Add Ollama process info if running
        if self.model_manager.model_process and self.model_manager.model_process.poll() is None:
            # Get PID from subprocess
            ollama_pid = self.model_manager.model_process.pid
            
            try:
                ollama_process = psutil.Process(ollama_pid)
                
                # Add header
                self.process_text.insert(tk.END, "=== Ollama Process Information ===\n\n")
                
                # Process details
                ollama_memory = ollama_process.memory_info()
                ollama_cpu = ollama_process.cpu_percent()
                ollama_create_time = datetime.datetime.fromtimestamp(ollama_process.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                
                self.process_text.insert(tk.END, f"PID: {ollama_pid}\n")
                self.process_text.insert(tk.END, f"Started: {ollama_create_time}\n")
                self.process_text.insert(tk.END, f"CPU Usage: {ollama_cpu}%\n")
                self.process_text.insert(tk.END, f"Memory Usage: {ollama_memory.rss / (1024**2):.2f} MB\n")
                
                # Get current model
                model_name = self.model_manager.current_model
                if model_name:
                    self.process_text.insert(tk.END, f"Running Model: {model_name}\n")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.process_text.insert(tk.END, "Could not access Ollama process information.\n")
                
    def update_memory_stats(self):
        """Update memory statistics"""
        # Get memory system stats
        stats = self.memory_system.get_stats()
        
        # Update document count
        doc_count = stats["documents_count"]
        self.doc_count_var.set(str(doc_count))
        self.vector_store_var.set(f"{doc_count} documents")
        
        # Update last updated
        last_updated = stats["last_updated"] or "Never"
        self.last_updated_var.set(last_updated)
        
        # Count unique sources
        sources = set()
        source_types = {}
        
        for doc in self.memory_system.documents:
            source = doc.get("source", "Unknown")
            sources.add(source)
            
            # Get file extension
            ext = os.path.splitext(source)[1].lower() if "." in source else "unknown"
            source_types[ext] = source_types.get(ext, 0) + 1
            
        # Update unique sources count
        self.source_count_var.set(str(len(sources)))
        
        # Update sources tree
        self.update_sources_tree(source_types, doc_count)
        
        # Add recent searches (placeholder - would need to track searches)
        self.searches_listbox.delete(0, tk.END)
        
    def update_sources_tree(self, source_types, total_count):
        """
        Update the sources tree with file type breakdown
        
        Args:
            source_types: Dictionary of file types and counts
            total_count: Total document count
        """
        # Clear the current tree
        for item in self.sources_tree.get_children():
            self.sources_tree.delete(item)
            
        # Add each file type
        for ext, count in source_types.items():
            # Calculate percentage
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            
            # Add to tree
            self.sources_tree.insert(
                "",
                tk.END,
                values=(ext, count, f"{percentage:.1f}%")
            )
            
    def schedule_updates(self):
        """Schedule periodic updates"""
        if self.window.winfo_exists():
            # Update system info every 5 seconds
            self.update_system_info()
            
            # Update plugin stats at their own rates
            self.update_plugin_refresh_timers()
            
            # Schedule next system refresh
            self.window.after(5000, self.schedule_updates)
            
    def update_plugin_refresh_timers(self):
        """Update plugin statistics based on their refresh rates"""
        if not hasattr(self, "plugin_extensions") or not self.plugin_extensions:
            return
            
        current_time = time.time()
        
        # Initialize last refresh time tracker if not exists
        if not hasattr(self, "last_plugin_refresh"):
            self.last_plugin_refresh = {}
            
        # Check each plugin extension
        for plugin_id, extension in self.plugin_extensions.items():
            # Get refresh rate (default to 10 seconds)
            refresh_rate = extension.get("refresh_rate", 10)
            last_refresh = self.last_plugin_refresh.get(plugin_id, 0)
            
            # If it's time to refresh this plugin's stats
            if current_time - last_refresh >= refresh_rate:
                # Update last refresh time
                self.last_plugin_refresh[plugin_id] = current_time
                
                # If plugin has a stats provider, call it
                if plugin_id in self.plugin_stats_providers:
                    try:
                        stats = self.plugin_stats_providers[plugin_id]()
                        
                        # Update dashboard component if available
                        if plugin_id in self.plugin_dashboards:
                            component = self.plugin_dashboards[plugin_id]["component"]
                            if hasattr(component, "update_stats") and callable(component.update_stats):
                                component.update_stats(stats)
                    except Exception as e:
                        self.log(f"[Dashboard] Error refreshing stats for plugin {plugin_id}: {e}")

    def initialize_plugin_extensions(self):
        """Initialize extensions for plugins in the dashboard"""
        # Dictionary of registered plugin extensions
        self.plugin_extensions = {}
        
        # Create plugins tab to contain plugin-specific dashboards
        self.create_plugins_tab()
        
        # Register with plugin manager if available
        if hasattr(self.parent, "plugin_manager"):
            plugin_manager = self.parent.plugin_manager
            
            # Register for plugin events
            plugin_manager.register_event_handler("dashboard", "plugin_activated", 
                                                 self.on_plugin_activated)
            plugin_manager.register_event_handler("dashboard", "plugin_deactivated", 
                                                 self.on_plugin_deactivated)
                                                 
            # Get all active plugins and register them
            active_plugins = plugin_manager.get_active_plugins()
            for plugin_id, plugin in active_plugins.items():
                self.register_plugin_extension(plugin_id, plugin)

    def create_plugins_tab(self):
        """Create a tab for plugin-specific dashboards"""
        # Create main plugins tab
        self.plugins_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.plugins_tab, text="Plugins")
        
        # Create notebook for plugin tabs
        self.plugins_notebook = ttk.Notebook(self.plugins_tab)
        self.plugins_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Empty message for when no plugins have dashboards
        self.no_plugins_label = ttk.Label(
            self.plugins_notebook, 
            text="No plugins with dashboard components are currently active.",
            font=("Helvetica", 10, "italic")
        )
        self.no_plugins_label.pack(pady=50)
        
        # Dictionary to track plugin dashboard components
        self.plugin_dashboards = {}
        self.plugin_stats_providers = {}

    def register_plugin_extension(self, plugin_id, plugin):
        """
        Register a plugin extension for the dashboard
        
        Args:
            plugin_id: Plugin identifier
            plugin: Plugin instance
        """
        # Skip if plugin doesn't have dashboard extension
        if not hasattr(plugin, "get_dashboard_extension"):
            return
            
        try:
            # Check if already registered
            if plugin_id in self.plugin_extensions:
                return
                
            # Get dashboard extension from plugin
            extension = plugin.get_dashboard_extension(self)
            
            if not extension or not isinstance(extension, dict):
                return
                
            # Store extension specification
            self.plugin_extensions[plugin_id] = extension
            
            # Add dashboard tab if provided
            if "dashboard_tab" in extension:
                self.add_plugin_dashboard_tab(plugin_id, extension["dashboard_tab"])
                
            # Register statistics provider if provided
            if "stats_provider" in extension and callable(extension["stats_provider"]):
                self.plugin_stats_providers[plugin_id] = extension["stats_provider"]
                
            # Register overview widgets if provided
            if "overview_widgets" in extension:
                self.add_plugin_overview_widgets(plugin_id, extension["overview_widgets"])
                
            self.log(f"[Dashboard] Registered extension for plugin: {plugin_id}")
            
        except Exception as e:
            self.log(f"[Dashboard] Error registering extension for plugin {plugin_id}: {e}")

    def unregister_plugin_extension(self, plugin_id):
        """
        Unregister a plugin extension
        
        Args:
            plugin_id: Plugin identifier
        """
        if plugin_id not in self.plugin_extensions:
            return
            
        # Remove dashboard tab if present
        if plugin_id in self.plugin_dashboards:
            self.remove_plugin_dashboard_tab(plugin_id)
            
        # Remove statistics provider if present
        if plugin_id in self.plugin_stats_providers:
            del self.plugin_stats_providers[plugin_id]
            
        # Remove from extensions dictionary
        del self.plugin_extensions[plugin_id]
        
        self.log(f"[Dashboard] Unregistered extension for plugin: {plugin_id}")

    def add_plugin_dashboard_tab(self, plugin_id, dashboard_component):
        """
        Add a plugin dashboard tab
        
        Args:
            plugin_id: Plugin identifier
            dashboard_component: Dashboard component to add
        """
        # Hide the no plugins label if it's visible
        if self.no_plugins_label.winfo_ismapped():
            self.no_plugins_label.pack_forget()
            
        # Create tab frame
        tab_frame = ttk.Frame(self.plugins_notebook)
        
        # Get plugin metadata
        plugin_manager = getattr(self.parent, "plugin_manager", None)
        plugin_name = plugin_id.capitalize()
        
        if plugin_manager:
            plugin = plugin_manager.get_plugin_instance(plugin_id)
            if plugin and hasattr(plugin, "METADATA"):
                plugin_name = plugin.METADATA.get("name", plugin_name)
        
        # Add to notebook
        self.plugins_notebook.add(tab_frame, text=plugin_name)
        
        # Add component to frame
        if isinstance(dashboard_component, tk.Widget):
            dashboard_component.pack(in_=tab_frame, fill=tk.BOTH, expand=True)
            
        # Store reference
        self.plugin_dashboards[plugin_id] = {
            "tab": tab_frame,
            "component": dashboard_component
        }

    def remove_plugin_dashboard_tab(self, plugin_id):
        """
        Remove a plugin dashboard tab
        
        Args:
            plugin_id: Plugin identifier
        """
        if plugin_id not in self.plugin_dashboards:
            return
            
        # Get tab info
        tab_info = self.plugin_dashboards[plugin_id]
        tab_frame = tab_info["tab"]
        
        # Remove from notebook
        tab_index = self.plugins_notebook.index(tab_frame)
        if tab_index is not None:
            self.plugins_notebook.forget(tab_index)
        
        # Clean up reference
        del self.plugin_dashboards[plugin_id]
        
        # Show no plugins label if no more plugin dashboards
        if not self.plugin_dashboards and not self.no_plugins_label.winfo_ismapped():
            self.no_plugins_label.pack(pady=50)

    def add_plugin_overview_widgets(self, plugin_id, widgets):
        """
        Add plugin widgets to the overview tab
        
        Args:
            plugin_id: Plugin identifier
            widgets: List of widgets to add
        """
        if not widgets or not isinstance(widgets, list):
            return
            
        # Create section for plugin widgets if not exists
        if not hasattr(self, "plugin_overview_frame"):
            # Get the overview frame (first tab)
            overview_tab = self.notebook.nametowidget(self.notebook.tabs()[0])
            
            # Create frame for plugin widgets
            self.plugin_overview_frame = ttk.LabelFrame(overview_tab, text="Plugin Statistics")
            self.plugin_overview_frame.pack(fill=tk.X, padx=20, pady=(5, 10), before=overview_tab.winfo_children()[-1])
            
        # Add widgets to section
        for widget in widgets:
            if isinstance(widget, tk.Widget):
                widget.pack(in_=self.plugin_overview_frame, fill=tk.X, padx=5, pady=2)

    def on_plugin_activated(self, plugin_id, plugin_instance):
        """
        Handle plugin activation event
        
        Args:
            plugin_id: ID of activated plugin
            plugin_instance: Plugin instance
        """
        # Register dashboard extension for newly activated plugin
        self.register_plugin_extension(plugin_id, plugin_instance)
        
        # Update dashboard with new plugin data
        self.update_statistics()

    def on_plugin_deactivated(self, plugin_id):
        """
        Handle plugin deactivation event
        
        Args:
            plugin_id: ID of deactivated plugin
        """
        # Unregister dashboard extension
        self.unregister_plugin_extension(plugin_id)
        
        # Update dashboard to remove plugin data
        self.update_statistics()

