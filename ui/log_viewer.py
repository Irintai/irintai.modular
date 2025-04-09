"""
Log viewer UI component for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import time
import threading
from typing import Optional, Callable, List, Dict, Any

class LogViewer:
    """Enhanced log viewer with filtering and auto-refresh capabilities"""
    
    def __init__(self, parent, logger):
        """
        Initialize the log viewer
        
        Args:
            parent: Parent widget
            logger: IrintaiLogger instance
        """
        self.parent = parent
        self.logger = logger
        
        # Create top-level window
        self.window = tk.Toplevel(parent)
        self.window.title("Irintai Log Viewer")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        
        # Set up auto-refresh
        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval = 2000  # 2 seconds
        
        # Initialize UI components
        self.initialize_ui()
        
        # Initial log display
        self.update_log_display()
        
        # Start auto-refresh if enabled
        self.schedule_refresh()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def initialize_ui(self):
        """Initialize the UI components"""
        # Create control frame
        self.create_control_frame()
        
        # Create log display
        self.create_log_display()
        
        # Create status bar
        self.create_status_bar()
        
    def create_control_frame(self):
        """Create the control frame with filters and buttons"""
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add auto-refresh toggle
        ttk.Checkbutton(
            control_frame, 
            text="Auto-refresh", 
            variable=self.auto_refresh
        ).pack(side=tk.LEFT)
        
        # Add refresh interval options
        ttk.Label(control_frame, text="Interval:").pack(side=tk.LEFT, padx=(10, 0))
        
        self.interval_var = tk.StringVar(value="2s")
        interval_dropdown = ttk.Combobox(
            control_frame,
            textvariable=self.interval_var,
            values=["1s", "2s", "5s", "10s"],
            state="readonly",
            width=5
        )
        interval_dropdown.pack(side=tk.LEFT, padx=5)
        interval_dropdown.bind("<<ComboboxSelected>>", self.on_interval_changed)
        
        # Add filter options
        ttk.Label(control_frame, text="Filter:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.filter_var = tk.StringVar(value="All")
        filter_dropdown = ttk.Combobox(
            control_frame,
            textvariable=self.filter_var,
            values=["All", "Error", "Warning", "Info", "User", "Assistant", "Model", "System"],
            state="readonly",
            width=10
        )
        filter_dropdown.pack(side=tk.LEFT, padx=5)
        filter_dropdown.bind("<<ComboboxSelected>>", self.update_log_display)
        
        # Search input
        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            control_frame,
            textvariable=self.search_var,
            width=15
        )
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", self.update_log_display)
        
        ttk.Button(
            control_frame,
            text="Search",
            command=self.update_log_display
        ).pack(side=tk.LEFT, padx=5)
        
        # Add buttons on the right
        ttk.Button(
            control_frame, 
            text="Refresh Now", 
            command=self.update_log_display
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Clear Viewer", 
            command=self.clear_display
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Save Logs", 
            command=self.save_logs
        ).pack(side=tk.RIGHT, padx=5)
        
    def create_log_display(self):
        """Create the log display area"""
        # Create scrolled text widget
        self.log_display = scrolledtext.ScrolledText(
            self.window, 
            wrap=tk.WORD, 
            font=("Courier New", 10)
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for different message types
        self.log_display.tag_configure("error", foreground="red")
        self.log_display.tag_configure("warning", foreground="orange")
        self.log_display.tag_configure("info", foreground="blue")
        self.log_display.tag_configure("http", foreground="purple")
        self.log_display.tag_configure("model", foreground="green")
        self.log_display.tag_configure("assistant", foreground="purple")
        self.log_display.tag_configure("user", foreground="darkblue")
        self.log_display.tag_configure("system", foreground="darkgreen")
        self.log_display.tag_configure("timestamp", foreground="gray")
        self.log_display.tag_configure("highlight", background="yellow")
        
    def create_status_bar(self):
        """Create the status bar"""
        self.status_var = tk.StringVar(value="Log Viewer Ready")
        
        self.status_bar = ttk.Label(
            self.window, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def update_log_display(self, event=None):
        """Update the log display with filtered content"""
        try:
            # Save current position
            current_pos = self.log_display.yview()
            
            # Get filters
            filter_type = self.filter_var.get()
            search_text = self.search_var.get().lower()
            
            # Get log content
            if hasattr(self.logger, 'get_console_lines'):
                # Use logger's filtering if available
                if filter_type == "All":
                    lines = self.logger.get_console_lines()
                else:
                    lines = self.logger.get_console_lines(filter_type)
            else:
                # Fallback to reading the log file
                try:
                    with open(self.logger.latest_log_file, "r", encoding="utf-8", errors='replace') as log_file:
                        lines = log_file.readlines()
                except Exception as e:
                    lines = [f"Error reading log file: {e}"]
            
            # Apply search filter if needed
            if search_text:
                filtered_lines = []
                for line in lines:
                    if search_text in line.lower():
                        filtered_lines.append(line)
                lines = filtered_lines
            
            # Clear and insert new content
            self.log_display.delete(1.0, tk.END)
            
            # Apply tags while inserting
            for line in lines:
                if not isinstance(line, str):
                    line = str(line)
                    
                if "[Error]" in line or "ERROR" in line:
                    self.log_display.insert(tk.END, line, "error")
                elif "[Warning]" in line or "WARNING" in line:
                    self.log_display.insert(tk.END, line, "warning")
                elif "[INFO]" in line or "[Info]" in line:
                    self.log_display.insert(tk.END, line, "info")
                elif "[HTTP]" in line:
                    self.log_display.insert(tk.END, line, "http")
                elif "[Model" in line or "[Starting Model]" in line or "[Stopped Model]" in line:
                    self.log_display.insert(tk.END, line, "model")
                elif "[Assistant]" in line or "[Irintai]" in line:
                    self.log_display.insert(tk.END, line, "assistant")
                elif line.startswith("> ") or "[User]" in line:
                    self.log_display.insert(tk.END, line, "user")
                elif "[System]" in line:
                    self.log_display.insert(tk.END, line, "system")
                else:
                    self.log_display.insert(tk.END, line)
                
                # Highlight search text if present
                if search_text:
                    self.highlight_text(search_text)
            
            # Update status
            self.status_var.set(f"Log updated: {time.strftime('%H:%M:%S')} - {len(lines)} lines")
            
            # Restore view position if not at the end
            if current_pos[1] < 1.0:
                self.log_display.yview_moveto(current_pos[0])
            else:
                self.log_display.see(tk.END)  # Scroll to end if we were at the end
                
        except Exception as e:
            self.status_var.set(f"Error updating logs: {e}")
            
    def highlight_text(self, text):
        """
        Highlight all occurrences of text in the log display
        
        Args:
            text: Text to highlight
        """
        if not text:
            return
            
        # Case insensitive search
        text = text.lower()
        
        # Find all occurrences and highlight them
        start_pos = '1.0'
        while True:
            # Find next occurrence
            start_pos = self.log_display.search(
                text, 
                start_pos, 
                tk.END, 
                nocase=True
            )
            
            if not start_pos:
                break
                
            # Calculate end position
            end_pos = f"{start_pos}+{len(text)}c"
            
            # Add highlight tag
            self.log_display.tag_add("highlight", start_pos, end_pos)
            
            # Move to next position
            start_pos = end_pos
        
    def clear_display(self):
        """Clear the log display"""
        self.log_display.delete(1.0, tk.END)
        self.status_var.set("Display cleared")
        
    def save_logs(self):
        """Save displayed logs to a file"""
        # Generate default filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_filename = f"irintai_logs_{timestamp}.txt"
        
        # Open save dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=default_filename
        )
        
        if not filename:
            return
            
        try:
            # Get display content
            content = self.log_display.get(1.0, tk.END)
            
            # Save to file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== Irintai Log Export - {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
                f.write(content)
                
            self.status_var.set(f"Logs saved to {filename}")
        except Exception as e:
            self.status_var.set(f"Error saving logs: {e}")
            messagebox.showerror("Error", f"Failed to save logs: {e}")
            
    def on_interval_changed(self, event):
        """Handle refresh interval changes"""
        interval = self.interval_var.get()
        
        # Convert to milliseconds
        if interval == "1s":
            self.refresh_interval = 1000
        elif interval == "2s":
            self.refresh_interval = 2000
        elif interval == "5s":
            self.refresh_interval = 5000
        elif interval == "10s":
            self.refresh_interval = 10000
            
        # Restart refresh cycle if auto-refresh is enabled
        if self.auto_refresh.get():
            self.schedule_refresh()
            
    def schedule_refresh(self):
        """Schedule the next refresh based on current settings"""
        # Cancel any pending refresh
        if hasattr(self, 'refresh_job'):
            self.window.after_cancel(self.refresh_job)
            
        # Schedule new refresh if auto-refresh is enabled
        if self.auto_refresh.get() and self.window.winfo_exists():
            self.refresh_job = self.window.after(
                self.refresh_interval, 
                self.auto_refresh_callback
            )
            
    def auto_refresh_callback(self):
        """Callback for auto-refresh"""
        # Update the display
        self.update_log_display()
        
        # Schedule next refresh
        self.schedule_refresh()
        
    def on_close(self):
        """Handle window closing"""
        # Cancel auto-refresh
        if hasattr(self, 'refresh_job'):
            self.window.after_cancel(self.refresh_job)
            
        # Destroy window
        self.window.destroy()