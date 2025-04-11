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
from typing import Optional, List, Dict, Any, Callable, Set, Union

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
        self.max_size_mb = max_size_mb
        self.backup_count = backup_count
        self.plugin_loggers = {}  # Store plugin-specific loggers
        
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
        
        # Set up plugins directory
        self.plugins_log_dir = os.path.join(log_dir, "plugins")
        os.makedirs(self.plugins_log_dir, exist_ok=True)
        
        # Set up event listeners for log events
        self.log_listeners = {}
        
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
    
    def log(self, msg: str, level: str = "INFO", plugin_id: str = None, 
            emit_event: bool = True, tags: List[str] = None) -> None:
        """
        Log a message
        
        Args:
            msg: Message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            plugin_id: Optional plugin identifier for plugin-specific logs
            emit_event: Whether to emit a log event for listeners
            tags: Optional list of tags for log categorization
        """
        try:
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "level": level,
                "message": msg,
                "plugin_id": plugin_id,
                "tags": tags or []
            }
            
            # Format message with plugin identifier if provided
            formatted_msg = msg
            if plugin_id:
                formatted_msg = f"[Plugin: {plugin_id}] {msg}"
                
                # Log to plugin-specific logger if available
                plugin_logger = self.get_plugin_logger(plugin_id)
                if plugin_logger:
                    self._log_with_level(plugin_logger, level, msg)

            # Log to main logger
            self._log_with_level(self.logger, level, formatted_msg)
                
            # Add to console lines
            self.console_lines.append(formatted_msg)
            
            # Trim console lines if too many
            if len(self.console_lines) > self.max_console_lines:
                self.console_lines = self.console_lines[-self.max_console_lines:]
                
            # Update console if callback provided
            if self.console_callback:
                self.console_callback(formatted_msg)
                
            # Emit log event for listeners
            if emit_event:
                self._emit_log_event(log_entry)
                
        except Exception as e:
            # Fallback to basic print if logging fails
            print(f"Logging error: {e}")
            print(msg)
    
    def _log_with_level(self, logger, level: str, msg: str) -> None:
        """Log a message with the specified level to the given logger"""
        if level == "DEBUG" or "[DEBUG]" in msg:
            logger.debug(msg)
        elif level == "INFO" or "[INFO]" in msg:
            logger.info(msg)
        elif level == "WARNING" or "[Warning]" in msg or "[WARNING]" in msg:
            logger.warning(msg)
        elif level == "ERROR" or "[Error]" in msg or "[ERROR]" in msg:
            logger.error(msg)
        elif level == "CRITICAL" or "[CRITICAL]" in msg:
            logger.critical(msg)
        else:
            logger.info(msg)
            
    def _emit_log_event(self, log_entry: Dict[str, Any]) -> None:
        """Emit a log event to registered listeners"""
        level = log_entry['level']
        plugin_id = log_entry.get('plugin_id')
        
        # Event keys to check
        event_keys = [
            "log",                       # All logs
            f"log.{level.lower()}",      # Logs of specific level
        ]
        
        # Add plugin-specific event keys if plugin_id is provided
        if plugin_id:
            event_keys.append(f"log.plugin.{plugin_id}")
            event_keys.append(f"log.plugin.{plugin_id}.{level.lower()}")
        
        # Notify listeners
        for key in event_keys:
            if key in self.log_listeners:
                for listener in self.log_listeners[key]:
                    try:
                        listener(log_entry)
                    except Exception as e:
                        # Don't use self.log here to avoid infinite recursion
                        print(f"Error in log listener: {e}")
    
    def register_log_listener(self, event_key: str, callback: Callable) -> None:
        """
        Register a listener for log events
        
        Args:
            event_key: Event key to listen for 
                       ("log", "log.info", "log.error", "log.plugin.{plugin_id}", etc.)
            callback: Function to call when event occurs
        """
        if event_key not in self.log_listeners:
            self.log_listeners[event_key] = set()
        
        self.log_listeners[event_key].add(callback)
        
    def unregister_log_listener(self, event_key: str, callback: Callable) -> None:
        """
        Unregister a listener for log events
        
        Args:
            event_key: Event key the listener was registered for
            callback: Function to unregister
        """
        if event_key in self.log_listeners and callback in self.log_listeners[event_key]:
            self.log_listeners[event_key].remove(callback)
            
    def get_plugin_logger(self, plugin_id: str) -> Optional[logging.Logger]:
        """
        Get or create a logger for a specific plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Logger instance for the plugin
        """
        if plugin_id in self.plugin_loggers:
            return self.plugin_loggers[plugin_id]
            
        try:
            # Create plugin-specific log directory
            plugin_log_dir = os.path.join(self.plugins_log_dir, plugin_id)
            os.makedirs(plugin_log_dir, exist_ok=True)
            
            # Create log file for the plugin
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(plugin_log_dir, f"{plugin_id}_{timestamp}.log")
            
            # Create rotating file handler
            handler = RotatingFileHandler(
                log_file, 
                maxBytes=self.max_size_mb*1024*1024,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            
            # Configure formatter
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            # Create logger
            logger = logging.getLogger(f'irintai.plugin.{plugin_id}')
            logger.setLevel(logging.DEBUG)
            
            # Remove any existing handlers
            for hdlr in logger.handlers:
                logger.removeHandler(hdlr)
                
            logger.addHandler(handler)
            
            # Store logger in plugin_loggers
            self.plugin_loggers[plugin_id] = logger
            
            # Create latest log symlink/copy for the plugin
            latest_log = os.path.join(plugin_log_dir, f"{plugin_id}_latest.log")
            
            if os.name == 'nt':
                # For Windows, copy the file
                shutil.copy2(log_file, latest_log)
            else:
                # For Unix-like systems, create symlink
                if os.path.exists(latest_log):
                    os.remove(latest_log)
                os.symlink(log_file, latest_log)
            
            return logger
        except Exception as e:
            self.error(f"Failed to create plugin logger for {plugin_id}: {e}")
            return None
            
    def debug(self, msg: str, plugin_id: str = None, tags: List[str] = None) -> None:
        """Log a debug message"""
        self.log(msg, "DEBUG", plugin_id, tags=tags)
        
    def info(self, msg: str, plugin_id: str = None, tags: List[str] = None) -> None:
        """Log an info message"""
        self.log(msg, "INFO", plugin_id, tags=tags)
        
    def warning(self, msg: str, plugin_id: str = None, tags: List[str] = None) -> None:
        """Log a warning message"""
        self.log(msg, "WARNING", plugin_id, tags=tags)
        
    def error(self, msg: str, plugin_id: str = None, tags: List[str] = None) -> None:
        """Log an error message"""
        self.log(msg, "ERROR", plugin_id, tags=tags)
        
    def critical(self, msg: str, plugin_id: str = None, tags: List[str] = None) -> None:
        """Log a critical message"""
        self.log(msg, "CRITICAL", plugin_id, tags=tags)
    
    def plugin_log(self, plugin_id: str, msg: str, level: str = "INFO", tags: List[str] = None) -> None:
        """
        Log a message for a specific plugin
        
        Args:
            plugin_id: Plugin identifier
            msg: Message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            tags: Optional list of tags for log categorization
        """
        self.log(msg, level, plugin_id, tags=tags)
    
    def get_console_lines(self, filter_type: str = None, plugin_id: str = None, 
                          limit: int = None, tags: List[str] = None) -> List[str]:
        """
        Get console lines with optional filtering
        
        Args:
            filter_type: Optional filter (User, Model, Error, Warning, etc.)
            plugin_id: Optional plugin ID to filter by
            limit: Optional limit on number of lines
            tags: Optional list of tags to filter by
            
        Returns:
            List of filtered console lines
        """
        filtered_lines = []
        
        # Apply basic filter
        if not filter_type or filter_type == "All":
            filtered_lines = self.console_lines.copy()
        else:
            for line in self.console_lines:
                if filter_type == "User" and (line.startswith("> ") or "[User]" in line):
                    filtered_lines.append(line)
                elif filter_type == "Model" and "[Assistant]" in line:
                    filtered_lines.append(line)
                elif filter_type == "Error" and ("[Error]" in line or "[ERROR]" in line):
                    filtered_lines.append(line)
                elif filter_type == "Warning" and ("[Warning]" in line or "[WARNING]" in line):
                    filtered_lines.append(line)
                    
        # Apply plugin filter
        if plugin_id:
            plugin_marker = f"[Plugin: {plugin_id}]"
            filtered_lines = [line for line in filtered_lines if plugin_marker in line]
            
        # Apply tag filter (not actually implemented in console_lines storage yet)
        # This would require changing how we store console lines to include metadata
                
        # Apply limit
        if limit and len(filtered_lines) > limit:
            filtered_lines = filtered_lines[-limit:]
                
        return filtered_lines
    
    def save_console_log(self, filename: Optional[str] = None, 
                         filter_type: str = None, plugin_id: str = None) -> str:
        """
        Save current console log to a file
        
        Args:
            filename: Optional filename to save to
            filter_type: Optional filter (User, Model, Error, Warning, etc.)
            plugin_id: Optional plugin ID to filter by
            
        Returns:
            Path to the saved file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = "irintai_console"
            if plugin_id:
                prefix = f"irintai_plugin_{plugin_id}"
            filename = f"{prefix}_{timestamp}.log"
            
        try:
            # Get filtered lines
            lines = self.get_console_lines(filter_type, plugin_id)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== Irintai Console Log - {datetime.datetime.now()} ===\n\n")
                if plugin_id:
                    f.write(f"Plugin: {plugin_id}\n\n")
                if filter_type and filter_type != "All":
                    f.write(f"Filter: {filter_type}\n\n")
                    
                for line in lines:
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
        
    def get_plugin_logs(self, plugin_id: str, limit: int = None) -> List[str]:
        """
        Get logs for a specific plugin
        
        Args:
            plugin_id: Plugin identifier
            limit: Optional limit on number of lines
            
        Returns:
            List of log lines for the plugin
        """
        return self.get_console_lines(plugin_id=plugin_id, limit=limit)
        
    def export_plugin_logs(self, plugin_id: str) -> str:
        """
        Export logs for a specific plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Path to the exported log file
        """
        # Create export directory if it doesn't exist
        export_dir = os.path.join(self.log_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        # Create export filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = os.path.join(export_dir, f"{plugin_id}_logs_{timestamp}.log")
        
        # Get plugin-specific log file if it exists
        plugin_log_dir = os.path.join(self.plugins_log_dir, plugin_id)
        latest_log = os.path.join(plugin_log_dir, f"{plugin_id}_latest.log")
        
        if os.path.exists(latest_log):
            # Copy the plugin log file
            shutil.copy2(latest_log, export_file)
        else:
            # Extract plugin logs from main log
            self.save_console_log(export_file, plugin_id=plugin_id)
            
        return export_file
        
    def create_plugin_logger(self, plugin_id: str) -> 'PluginLogger':
        """
        Create a logger interface for a plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            PluginLogger instance
        """
        return PluginLogger(self, plugin_id)
        

class PluginLogger:
    def __init__(self, main_logger, plugin_id):
        self.main_logger = main_logger
        self.plugin_id = plugin_id
        
    def log(self, message, level="INFO"):
        self.main_logger.log(f"[Plugin: {self.plugin_id}] {message}", level)