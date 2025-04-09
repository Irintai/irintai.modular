"""
Enhanced logging utility for the Irintai assistant
"""
import os
import logging
import datetime
import time
import threading
import shutil
from logging.handlers import RotatingFileHandler
from typing import Optional, List, Dict, Any, Callable

class IrintaiLogger:
    """Enhanced logging with file rotation, formatting, and UI integration"""
    
    def __init__(self, 
                 log_dir: str = "data/logs",
                 latest_log_file: str = "irintai_debug.log",
                 console_callback: Optional[Callable] = None,
                 max_size_mb: int = 10,
                 backup_count: int = 5):
        """
        Initialize the logger
        
        Args:
            log_dir: Directory to store log files
            latest_log_file: Path to the latest log symlink/copy
            console_callback: Function to call for console UI updates
            max_size_mb: Maximum log file size in MB
            backup_count: Number of backup log files to keep
        """
        self.log_dir = log_dir
        self.latest_log_file = latest_log_file
        self.console_callback = console_callback
        self.console_lines = []
        self.max_console_lines = 1000
        
        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up the main debug log file with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug_log_file = f"{log_dir}/irintai_debug_{timestamp}.log"
        
        # Create rotating file handler
        handler = RotatingFileHandler(
            self.debug_log_file, 
            maxBytes=max_size_mb*1024*1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Configure formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Set up logger
        self.logger = logging.getLogger('irintai')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers to avoid duplicates
        for hdlr in self.logger.handlers:
            self.logger.removeHandler(hdlr)
            
        self.logger.addHandler(handler)
        
        # Create symlink or copy for latest log
        self._setup_latest_log_link()
        
        # Log startup message
        self.logger.info(f"=== Irintai Assistant Started ===")
        self.logger.info(f"Log file: {self.debug_log_file}")
        
    def _setup_latest_log_link(self):
        """Set up symlink or copy for the latest log file"""
        try:
            # For Windows, copy the file instead of symlink
            if os.name == 'nt':
                with open(self.debug_log_file, 'a', encoding='utf-8') as src:
                    src.write(f"Log started at {datetime.datetime.now()}\n")
                    
                # Use a file watcher in a separate thread to update the copy
                self._start_log_file_watcher()
            else:
                # For Unix-like systems, use a symlink
                if os.path.exists(self.latest_log_file):
                    os.remove(self.latest_log_file)
                os.symlink(self.debug_log_file, self.latest_log_file)
        except Exception as e:
            print(f"Warning: Could not create log symlink/copy: {e}")
    
    def _start_log_file_watcher(self):
        """Start a thread to watch the log file and update the copy periodically"""
        def watcher_thread():
            last_size = 0
            while True:
                try:
                    # Check if the source file has changed
                    current_size = os.path.getsize(self.debug_log_file)
                    if current_size > last_size:
                        # Copy the file to the latest.log location
                        shutil.copy2(self.debug_log_file, self.latest_log_file)
                        last_size = current_size
                except Exception:
                    pass  # Ignore errors in the watcher
                    
                # Sleep before checking again
                time.sleep(2)
        
        threading.Thread(target=watcher_thread, daemon=True).start()
    
    def log(self, msg: str, level: str = "INFO") -> None:
        """
        Log a message
        
        Args:
            msg: Message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            # Determine log level
            if level == "DEBUG" or "[DEBUG]" in msg:
                self.logger.debug(msg)
            elif level == "INFO" or "[INFO]" in msg:
                self.logger.info(msg)
            elif level == "WARNING" or "[Warning]" in msg or "[WARNING]" in msg:
                self.logger.warning(msg)
            elif level == "ERROR" or "[Error]" in msg or "[ERROR]" in msg:
                self.logger.error(msg)
            elif level == "CRITICAL" or "[CRITICAL]" in msg:
                self.logger.critical(msg)
            else:
                self.logger.info(msg)
                
            # Add to console lines
            self.console_lines.append(msg)
            
            # Trim console lines if too many
            if len(self.console_lines) > self.max_console_lines:
                self.console_lines = self.console_lines[-self.max_console_lines:]
                
            # Update console if callback provided
            if self.console_callback:
                self.console_callback(msg)
                
        except Exception as e:
            # Fallback to basic print if logging fails
            print(f"Logging error: {e}")
            print(msg)
    
    def debug(self, msg: str) -> None:
        """Log a debug message"""
        self.log(msg, "DEBUG")
        
    def info(self, msg: str) -> None:
        """Log an info message"""
        self.log(msg, "INFO")
        
    def warning(self, msg: str) -> None:
        """Log a warning message"""
        self.log(msg, "WARNING")
        
    def error(self, msg: str) -> None:
        """Log an error message"""
        self.log(msg, "ERROR")
        
    def critical(self, msg: str) -> None:
        """Log a critical message"""
        self.log(msg, "CRITICAL")
    
    def get_console_lines(self, filter_type: str = None) -> List[str]:
        """
        Get console lines with optional filtering
        
        Args:
            filter_type: Optional filter (User, Model, Error, Warning, etc.)
            
        Returns:
            List of filtered console lines
        """
        if not filter_type or filter_type == "All":
            return self.console_lines
            
        filtered_lines = []
        for line in self.console_lines:
            if filter_type == "User" and (line.startswith("> ") or "[User]" in line):
                filtered_lines.append(line)
            elif filter_type == "Model" and "[Assistant]" in line:
                filtered_lines.append(line)
            elif filter_type == "Error" and ("[Error]" in line or "[ERROR]" in line):
                filtered_lines.append(line)
            elif filter_type == "Warning" and ("[Warning]" in line or "[WARNING]" in line):
                filtered_lines.append(line)
                
        return filtered_lines
    
    def save_console_log(self, filename: Optional[str] = None) -> str:
        """
        Save current console log to a file
        
        Args:
            filename: Optional filename to save to
            
        Returns:
            Path to the saved file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"irintai_console_{timestamp}.log"
            
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== Irintai Console Log - {datetime.datetime.now()} ===\n\n")
                for line in self.console_lines:
                    f.write(f"{line}\n")
                    
            self.info(f"Console log saved to {filename}")
            return filename
        except Exception as e:
            self.error(f"Failed to save console log: {e}")
            return ""
    
    def clear_console(self) -> None:
        """Clear the console log"""
        self.console_lines = []
        self.info("Console log cleared")
        
    def set_console_callback(self, callback: Callable) -> None:
        """
        Set the console callback function
        
        Args:
            callback: Function to call for console updates
        """
        self.console_callback = callback