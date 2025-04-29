"""
System monitoring utilities for tracking CPU, RAM, GPU, and disk usage
"""
import os
import shutil
import subprocess
import psutil
import time
import threading
import json
from typing import Dict, Tuple, Any, Optional, List, Callable, Set, Union

class SystemMonitor:
    """Monitor system resources like CPU, RAM, GPU, and disk space"""
    
    def __init__(self, logger=None, event_bus=None, config=None):
        """
        Initialize the system monitor
        
        Args:
            logger: Optional logging function
            event_bus: Optional event bus for notifications
            config: Optional configuration manager
        """
        self.logger = logger
        self.event_bus = event_bus
        self.config = config
        
        # Store custom metrics registered by plugins
        self.custom_metrics = {}
        
        # Process monitoring
        self.monitored_processes = {}
        self.process_metrics = {}
        
        # Store previous values for change detection
        self.previous_values = {}
        
        # Notification thresholds
        self.thresholds = {
            "cpu": {"warning": 70, "critical": 90},
            "ram": {"warning": 70, "critical": 90},
            "gpu": {"warning": 70, "critical": 90},
            "disk": {"warning": 80, "critical": 90},
            "vram": {"warning": 80, "critical": 90}
        }
        
        # Start monitoring thread
        self.running = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: float = 5.0):
        """
        Start the monitoring thread
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,), 
            daemon=True
        )
        self.monitor_thread.start()
        self.log("[SystemMonitor] Started monitoring thread")
        # Emit initial stats for UI
        if self.event_bus is not None:
            self.event_bus.publish("system.stats_updated", self.get_system_info())

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None
            self.log("[SystemMonitor] Stopped monitoring thread")
        
    def _monitor_loop(self, interval: float):
        """
        Main monitoring loop
        
        Args:
            interval: Monitoring interval in seconds
        """
        while self.running:
            try:
                # Get system stats
                system_stats = self.get_system_info()
                
                # Check for significant changes
                self._check_for_changes(system_stats)
                
                # Update process metrics
                self._update_process_metrics()
                
                # Update custom metrics
                self._update_custom_metrics()
                
                # Emit system stats event
                if self.event_bus is not None:
                    self.event_bus.publish("system.stats_updated", system_stats)
                    
            except Exception as e:
                self.log(f"[SystemMonitor] Error in monitoring loop: {e}", "ERROR")
                
            # Sleep until next check
            time.sleep(interval)
        
    def log(self, msg: str, level: str = "INFO") -> None:
        """
        Log a message if logger is available
        
        Args:
            msg: Message to log
            level: Log level
        """
        if self.logger:
            if hasattr(self.logger, 'log'):
                self.logger.log(msg, level)
            else:
                print(f"[{level}] {msg}")
    
    def get_gpu_stats(self) -> Tuple[str, str]:
        """
        Get NVIDIA GPU utilization and memory usage
        
        Returns:
            Tuple containing GPU utilization percentage and memory usage string
        """
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", 
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2, env=os.environ.copy()
            )
            
            if result.returncode == 0:
                usage, used, total = result.stdout.strip().split(',')
                return usage.strip() + "%", f"{used.strip()} MB / {total.strip()} MB"
            
            return "N/A", "N/A"
        except Exception as e:
            self.log(f"[System Monitor] GPU stats error: {e}")
            return "N/A", "N/A"
    
    def get_cpu_usage(self) -> float:
        """
        Get CPU usage percentage
        
        Returns:
            CPU usage percentage
        """
        try:
            return psutil.cpu_percent()
        except Exception as e:
            self.log(f"[System Monitor] CPU usage error: {e}")
            return 0.0
    
    def get_ram_usage(self) -> Tuple[float, float, float]:
        """
        Get RAM usage information
        
        Returns:
            Tuple containing RAM usage percentage, used GB, and total GB
        """
        try:
            memory = psutil.virtual_memory()
            used_gb = memory.used / (1024**3)
            total_gb = memory.total / (1024**3)
            return memory.percent, used_gb, total_gb
        except Exception as e:
            self.log(f"[System Monitor] RAM usage error: {e}")
            return 0.0, 0.0, 0.0
    
    def get_disk_space(self, path: str) -> Tuple[float, float, float]:
        """
        Get disk space for a given path
        
        Args:
            path: Path to check
            
        Returns:
            Tuple containing disk usage percentage, free GB, and total GB
        """
        try:
            # Extract the drive letter from the path
            if os.name == 'nt':  # Windows
                drive = os.path.splitdrive(path)[0]
                if drive:
                    drive = drive + "\\"
                else:
                    drive = "C:\\"  # Default to C: if no drive letter found
            else:  # Unix-like
                drive = path
                
            usage = shutil.disk_usage(drive)
            used_percent = (usage.used / usage.total) * 100
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            
            return used_percent, free_gb, total_gb
        except Exception as e:
            self.log(f"[System Monitor] Disk space error for {path}: {e}")
            return 0.0, 0.0, 0.0
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information
        
        Returns:
            Dictionary containing system information
        """
        info = {
            "cpu": {
                "usage_percent": self.get_cpu_usage()
            },
            "ram": {},
            "gpu": {},
            "disk": {}
        }
        
        # RAM info
        ram_percent, ram_used, ram_total = self.get_ram_usage()
        info["ram"] = {
            "usage_percent": ram_percent,
            "used_gb": round(ram_used, 2),
            "total_gb": round(ram_total, 2)
        }
        
        # GPU info
        gpu_percent, gpu_memory = self.get_gpu_stats()
        info["gpu"] = {
            "usage_percent": gpu_percent,
            "memory": gpu_memory
        }
        
        # Disk info for current directory
        disk_percent, disk_free, disk_total = self.get_disk_space(os.getcwd())
        info["disk"] = {
            "usage_percent": disk_percent,
            "free_gb": round(disk_free, 2),
            "total_gb": round(disk_total, 2)
        }
        
        return info
    
    def get_performance_stats(self) -> Dict[str, str]:
        """
        Get formatted performance statistics
        
        Returns:
            Dictionary with formatted performance stats
        """
        # Get CPU usage
        cpu = self.get_cpu_usage()
        
        # Get RAM usage
        ram_percent, _, _ = self.get_ram_usage()
        
        # Get GPU stats
        gpu, vram = self.get_gpu_stats()
        
        return {
            "cpu": f"{cpu}%",
            "ram": f"{ram_percent}%",
            "gpu": gpu,
            "vram": vram
        }
    
    def is_resource_critical(self) -> Tuple[bool, str]:
        """
        Check if any resource usage is at a critical level
        
        Returns:
            Tuple containing flag indicating critical status and message
        """
        system_info = self.get_system_info()
        
        # Check CPU usage
        if system_info["cpu"]["usage_percent"] > self.thresholds["cpu"]["critical"]:
            return True, f"CPU usage is critical (>{self.thresholds['cpu']['critical']}%)"
            
        # Check RAM usage
        if system_info["ram"]["usage_percent"] > self.thresholds["ram"]["critical"]:
            return True, f"RAM usage is critical (>{self.thresholds['ram']['critical']}%)"
            
        # Check disk space
        if system_info["disk"]["free_gb"] < 5:
            return True, f"Low disk space: only {system_info['disk']['free_gb']} GB free"
            
        # Check GPU if available
        if system_info["gpu"]["usage_percent"] != "N/A":
            try:
                gpu_percent = int(system_info["gpu"]["usage_percent"].replace("%", ""))
                if gpu_percent > self.thresholds["gpu"]["critical"]:
                    return True, f"GPU usage is critical (>{self.thresholds['gpu']['critical']}%)"
            except:
                pass
                
        return False, ""
    
    def get_formatted_stats(self) -> str:
        """
        Get formatted performance statistics string
        
        Returns:
            Formatted string with performance stats
        """
        stats = self.get_performance_stats()
        return f"CPU: {stats['cpu']} | RAM: {stats['ram']} | GPU: {stats['gpu']} | VRAM: {stats['vram']}"
    
    def get_bgr_color(self) -> str:
        """
        Get background color based on resource usage
        
        Returns:
            Hex color code for background
        """
        is_critical, _ = self.is_resource_critical()
        if is_critical:
            return "#ffcccc"  # Light red
            
        system_info = self.get_system_info()
        
        # Check for warning level
        warning_threshold = self.thresholds["cpu"]["warning"]
        if (system_info["cpu"]["usage_percent"] > warning_threshold or
            system_info["ram"]["usage_percent"] > warning_threshold):
            return "#fff0b3"  # Light yellow
        
        # Check GPU if available
        if system_info["gpu"]["usage_percent"] != "N/A":
            try:
                gpu_percent = int(system_info["gpu"]["usage_percent"].replace("%", ""))
                if gpu_percent > warning_threshold:
                    return "#fff0b3"  # Light yellow
            except:
                pass
                
        return "#d1f5d3"  # Light green for normal usage
        
    def register_custom_metric(self, plugin_id: str, metric_id: str, 
                              provider_func: Callable, metadata: Dict = None) -> bool:
        """
        Register a custom metric from a plugin
        
        Args:
            plugin_id: Plugin identifier
            metric_id: Metric identifier
            provider_func: Function that returns the metric value
            metadata: Optional metadata about the metric
            
        Returns:
            True if registration was successful
        """
        if not callable(provider_func):
            self.log(f"[SystemMonitor] Cannot register metric {metric_id}: provider is not callable", "ERROR")
            return False
            
        metric_key = f"{plugin_id}.{metric_id}"
        
        # Default metadata
        default_metadata = {
            "name": metric_id,
            "description": f"Custom metric: {metric_id}",
            "unit": "",
            "min": 0,
            "max": 100,
            "warning_threshold": 70,
            "critical_threshold": 90,
            "display": True,
            "category": "plugin",
            "format": "numeric"  # numeric, percentage, text
        }
        
        # Merge with provided metadata
        if metadata:
            for key, value in metadata.items():
                default_metadata[key] = value
                
        # Store the metric
        self.custom_metrics[metric_key] = {
            "provider": provider_func,
            "metadata": default_metadata,
            "plugin_id": plugin_id,
            "metric_id": metric_id,
            "last_value": None,
            "last_update": 0
        }
        
        self.log(f"[SystemMonitor] Registered custom metric: {metric_key}")
        return True
        
    def unregister_custom_metric(self, plugin_id: str, metric_id: str) -> bool:
        """
        Unregister a custom metric
        
        Args:
            plugin_id: Plugin identifier
            metric_id: Metric identifier
            
        Returns:
            True if unregistration was successful
        """
        metric_key = f"{plugin_id}.{metric_id}"
        
        if metric_key in self.custom_metrics:
            del self.custom_metrics[metric_key]
            self.log(f"[SystemMonitor] Unregistered custom metric: {metric_key}")
            return True
            
        return False
        
    def unregister_plugin_metrics(self, plugin_id: str) -> int:
        """
        Unregister all metrics for a plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Number of metrics unregistered
        """
        count = 0
        to_remove = []
        
        for metric_key, metric_info in self.custom_metrics.items():
            if metric_info["plugin_id"] == plugin_id:
                to_remove.append(metric_key)
                count += 1
                
        for metric_key in to_remove:
            del self.custom_metrics[metric_key]
            
        if count:
            self.log(f"[SystemMonitor] Unregistered {count} metrics for plugin: {plugin_id}")
            
        return count
        
    def get_custom_metric(self, plugin_id: str, metric_id: str) -> Any:
        """
        Get the current value of a custom metric
        
        Args:
            plugin_id: Plugin identifier
            metric_id: Metric identifier
            
        Returns:
            Current metric value or None if not found
        """
        metric_key = f"{plugin_id}.{metric_id}"
        
        if metric_key not in self.custom_metrics:
            return None
            
        metric = self.custom_metrics[metric_key]
        
        try:
            # Update the value
            value = metric["provider"]()
            metric["last_value"] = value
            metric["last_update"] = time.time()
            return value
        except Exception as e:
            self.log(f"[SystemMonitor] Error getting metric {metric_key}: {e}", "ERROR")
            return metric.get("last_value")
            
    def _update_custom_metrics(self):
        """Update all custom metrics"""
        for metric_key, metric in list(self.custom_metrics.items()):
            try:
                # Get new value
                value = metric["provider"]()
                
                # Check for significant change
                last_value = metric.get("last_value")
                if last_value is not None:
                    metadata = metric["metadata"]
                    
                    # Calculate the range for percentage change
                    value_range = metadata.get("max", 100) - metadata.get("min", 0)
                    
                    # If the range is very small, use absolute change
                    if value_range < 1:
                        significant_change = abs(value - last_value) >= 0.1
                    else:
                        # Check for percentage change
                        change_percent = abs((value - last_value) / value_range * 100)
                        significant_change = change_percent >= 5  # 5% change is significant
                        
                    # Check for threshold crossing
                    warning_threshold = metadata.get("warning_threshold")
                    critical_threshold = metadata.get("critical_threshold")
                    
                    crossed_warning = (warning_threshold is not None and 
                                     (last_value < warning_threshold <= value or 
                                      last_value > warning_threshold >= value))
                    
                    crossed_critical = (critical_threshold is not None and 
                                      (last_value < critical_threshold <= value or 
                                       last_value > critical_threshold >= value))
                    
                    # Emit event if significant change
                    if (significant_change or crossed_warning or crossed_critical) and self.event_bus is not None:
                        event_data = {
                            "plugin_id": metric["plugin_id"],
                            "metric_id": metric["metric_id"],
                            "value": value,
                            "previous_value": last_value,
                            "metadata": metadata,
                            "crossed_warning": crossed_warning,
                            "crossed_critical": crossed_critical
                        }
                        
                        self.event_bus.publish("system.metric_changed", event_data)
                        
                        # Also emit specific events for threshold crossings
                        if crossed_warning and self.event_bus is not None:
                            if value > warning_threshold:
                                self.event_bus.publish("system.metric_warning", event_data)
                            else:
                                self.event_bus.publish("system.metric_warning_resolved", event_data)
                                
                        if crossed_critical and self.event_bus is not None:
                            if value > critical_threshold:
                                self.event_bus.publish("system.metric_critical", event_data)
                            else:
                                self.event_bus.publish("system.metric_critical_resolved", event_data)
                
                # Update stored value
                metric["last_value"] = value
                metric["last_update"] = time.time()
                
            except Exception as e:
                self.log(f"[SystemMonitor] Error updating metric {metric_key}: {e}", "ERROR")
        
    def _check_for_changes(self, current_stats: Dict[str, Any]):
        """
        Check for significant changes in system stats
        
        Args:
            current_stats: Current system stats
        """
        if not self.previous_values:
            # First time, just store the values
            self.previous_values = self._extract_key_values(current_stats)
            return
            
        # Extract current values
        current_values = self._extract_key_values(current_stats)
        
        # Check for significant changes
        for key, value in current_values.items():
            if key not in self.previous_values:
                continue
                
            prev_value = self.previous_values[key]
            
            # Skip non-numeric values
            if not isinstance(value, (int, float)) or not isinstance(prev_value, (int, float)):
                continue
                
            # Check for significant change (5% or more)
            if abs(value - prev_value) >= 5:
                # Emit event if event bus is available
                if self.event_bus is not None:
                    event_data = {
                        "metric": key,
                        "value": value,
                        "previous_value": prev_value,
                        "change": value - prev_value
                    }
                    self.event_bus.publish("system.significant_change", event_data)
                    
                # Check for threshold crossings
                if key in self.thresholds:
                    warning = self.thresholds[key]["warning"]
                    critical = self.thresholds[key]["critical"]
                    
                    # Check warning threshold crossing
                    if (prev_value < warning <= value or 
                        prev_value > warning >= value):
                        
                        event_data = {
                            "metric": key,
                            "value": value,
                            "threshold": warning,
                            "severity": "warning",
                            "exceeded": value >= warning
                        }
                        
                        if value >= warning:
                            self.event_bus.publish("system.threshold_exceeded", event_data)
                        else:
                            self.event_bus.publish("system.threshold_resolved", event_data)
                            
                    # Check critical threshold crossing
                    if (prev_value < critical <= value or 
                        prev_value > critical >= value):
                        
                        event_data = {
                            "metric": key,
                            "value": value,
                            "threshold": critical,
                            "severity": "critical",
                            "exceeded": value >= critical
                        }
                        
                        if value >= critical:
                            self.event_bus.publish("system.threshold_exceeded", event_data)
                        else:
                            self.event_bus.publish("system.threshold_resolved", event_data)
        
        # Update previous values
        self.previous_values = current_values
    
    def _extract_key_values(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key values from system stats for change detection
        
        Args:
            stats: System stats dictionary
            
        Returns:
            Dictionary of key values
        """
        result = {}
        # Extract CPU usage
        if "cpu" in stats and "usage_percent" in stats["cpu"]:
            try:
                result["cpu"] = float(stats["cpu"]["usage_percent"])
            except Exception:
                pass
        # Extract RAM usage
        if "ram" in stats and "usage_percent" in stats["ram"]:
            try:
                result["ram"] = float(stats["ram"]["usage_percent"])
            except Exception:
                pass
        # Extract GPU usage
        if "gpu" in stats and "usage_percent" in stats["gpu"]:
            try:
                val = stats["gpu"]["usage_percent"]
                if val != "N/A":
                    result["gpu"] = int(str(val).replace("%", ""))
            except Exception:
                pass
        # Extract disk usage
        if "disk" in stats and "usage_percent" in stats["disk"]:
            try:
                result["disk"] = float(stats["disk"]["usage_percent"])
            except Exception:
                pass
        return result
        
    def register_process_monitor(self, plugin_id: str, process_id: int, 
                               name: str = None, unregister_on_exit: bool = True):
        """
        Register a process for monitoring
        
        Args:
            plugin_id: Plugin identifier
            process_id: Process ID to monitor
            name: Optional name for the process
            unregister_on_exit: Whether to unregister when process exits
            
        Returns:
            True if registration was successful
        """
        try:
            # Check if process exists
            process = psutil.Process(process_id)
            
            # Store process info
            if not name:
                name = process.name()
                
            key = f"{plugin_id}:{process_id}"
            self.monitored_processes[key] = {
                "plugin_id": plugin_id,
                "process_id": process_id,
                "name": name,
                "unregister_on_exit": unregister_on_exit,
                "start_time": time.time()
            }
            
            self.log(f"[SystemMonitor] Registered process monitor for {name} (PID: {process_id}) from plugin {plugin_id}")
            return True
        except Exception as e:
            self.log(f"[SystemMonitor] Error registering process monitor: {e}", "ERROR")
            return False
            
    def unregister_process_monitor(self, plugin_id: str, process_id: int) -> bool:
        """
        Unregister a process monitor
        
        Args:
            plugin_id: Plugin identifier
            process_id: Process ID
            
        Returns:
            True if unregistration was successful
        """
        key = f"{plugin_id}:{process_id}"
        
        if key in self.monitored_processes:
            del self.monitored_processes[key]
            
            # Clean up process metrics
            if key in self.process_metrics:
                del self.process_metrics[key]
                
            self.log(f"[SystemMonitor] Unregistered process monitor for PID {process_id} from plugin {plugin_id}")
            return True
            
        return False
        
    def unregister_plugin_processes(self, plugin_id: str) -> int:
        """
        Unregister all process monitors for a plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Number of processes unregistered
        """
        count = 0
        to_remove = []
        
        for key, info in self.monitored_processes.items():
            if info["plugin_id"] == plugin_id:
                to_remove.append(key)
                count += 1
                
        for key in to_remove:
            del self.monitored_processes[key]
            
            # Clean up process metrics
            if key in self.process_metrics:
                del self.process_metrics[key]
                
        if count:
            self.log(f"[SystemMonitor] Unregistered {count} process monitors for plugin {plugin_id}")
            
        return count
        
    def get_process_metrics(self, plugin_id: str, process_id: int) -> Dict[str, Any]:
        """
        Get metrics for a monitored process
        
        Args:
            plugin_id: Plugin identifier
            process_id: Process ID
            
        Returns:
            Dictionary of process metrics or empty dict if not found
        """
        key = f"{plugin_id}:{process_id}"
        
        if key not in self.monitored_processes:
            return {}
            
        # Return cached metrics if available
        if key in self.process_metrics:
            return self.process_metrics[key]
            
        # Get process metrics
        try:
            process = psutil.Process(process_id)
            
            with process.oneshot():
                metrics = {
                    "cpu_percent": process.cpu_percent(),
                    "memory_percent": process.memory_percent(),
                    "memory_rss": process.memory_info().rss / (1024*1024),  # MB
                    "threads": len(process.threads()),
                    "status": process.status(),
                    "running": process.is_running(),
                    "name": process.name(),
                    "command": " ".join(process.cmdline()),
                    "io": process.io_counters() if hasattr(process, 'io_counters') else None
                }
                
                # Add additional metrics for non-Windows platforms
                if os.name != 'nt':
                    metrics["open_files"] = len(process.open_files())
                    metrics["connections"] = len(process.connections())
                    
                # Cache metrics
                self.process_metrics[key] = metrics
                
                return metrics
        except Exception as e:
            # Process may have exited
            if key in self.monitored_processes and self.monitored_processes[key]["unregister_on_exit"]:
                self.unregister_process_monitor(plugin_id, process_id)
                
            return {
                "error": str(e),
                "running": False
            }
    
    def _update_process_metrics(self):
        """Update metrics for all monitored processes"""
        for key, info in list(self.monitored_processes.items()):
            plugin_id = info["plugin_id"]
            process_id = info["process_id"]
            
            # Get updated metrics
            metrics = self.get_process_metrics(plugin_id, process_id)
            
            # Check for process exit
            if not metrics.get("running", True):
                if info["unregister_on_exit"]:
                    self.unregister_process_monitor(plugin_id, process_id)
                    
                    # Emit event if event bus is available
                    if self.event_bus is not None:
                        event_data = {
                            "plugin_id": plugin_id,
                            "process_id": process_id,
                            "name": info["name"]
                        }
                        self.event_bus.publish("system.process_exited", event_data)
                        
    def get_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        Get current threshold values
        
        Returns:
            Dictionary of threshold values
        """
        return self.thresholds.copy()
        
    def set_threshold(self, metric: str, level: str, value: float) -> bool:
        """
        Set a threshold value
        
        Args:
            metric: Metric name (cpu, ram, gpu, disk, vram)
            level: Threshold level (warning, critical)
            value: Threshold value
            
        Returns:
            True if threshold was set successfully
        """
        if metric not in self.thresholds:
            return False
            
        if level not in ["warning", "critical"]:
            return False
            
        if not isinstance(value, (int, float)) or value < 0 or value > 100:
            return False
            
        # Ensure warning is less than critical
        if level == "warning" and value >= self.thresholds[metric]["critical"]:
            return False
            
        if level == "critical" and value <= self.thresholds[metric]["warning"]:
            return False
            
        self.thresholds[metric][level] = value
        return True
        
    def get_all_metrics(self, include_processes: bool = True, 
                       include_custom: bool = True) -> Dict[str, Any]:
        """
        Get all metrics (system, processes, and custom)
        
        Args:
            include_processes: Whether to include process metrics
            include_custom: Whether to include custom metrics
            
        Returns:
            Dictionary of all metrics
        """
        # Get system metrics
        metrics = {
            "system": self.get_system_info()
        }
        
        # Add process metrics
        if include_processes and self.monitored_processes:
            process_metrics = {}
            
            for key, info in self.monitored_processes.items():
                plugin_id = info["plugin_id"]
                process_id = info["process_id"]
                
                process_metrics[key] = {
                    "info": info,
                    "metrics": self.get_process_metrics(plugin_id, process_id)
                }
                
            metrics["processes"] = process_metrics
            
        # Add custom metrics
        if include_custom and self.custom_metrics:
            custom_metrics = {}
            
            for key, metric in self.custom_metrics.items():
                try:
                    value = metric["provider"]()
                    last_update = time.time()
                except Exception as e:
                    value = metric.get("last_value")
                    last_update = metric.get("last_update", 0)
                    
                custom_metrics[key] = {
                    "value": value,
                    "metadata": metric["metadata"],
                    "plugin_id": metric["plugin_id"],
                    "last_update": last_update
                }
                
            metrics["custom"] = custom_metrics
            
        return metrics
        
    def export_metrics(self, format: str = "json") -> str:
        """
        Export all metrics to a string
        
        Args:
            format: Export format (json or text)
            
        Returns:
            String representation of metrics
        """
        metrics = self.get_all_metrics()
        
        if format.lower() == "json":
            # Filter out non-serializable values
            return json.dumps(metrics, default=str, indent=2)
        else:
            # Text format
            lines = ["=== System Metrics ==="]
            
            # Add system metrics
            system = metrics["system"]
            lines.append(f"CPU: {system['cpu']['usage_percent']}%")
            lines.append(f"RAM: {system['ram']['usage_percent']}% ({system['ram']['used_gb']} GB / {system['ram']['total_gb']} GB)")
            lines.append(f"GPU: {system['gpu']['usage_percent']}")
            lines.append(f"GPU Memory: {system['gpu']['memory']}")
            lines.append(f"Disk: {system['disk']['usage_percent']}% used, {system['disk']['free_gb']} GB free / {system['disk']['total_gb']} GB total")
            
            # Add process metrics
            if "processes" in metrics:
                lines.append("\n=== Process Metrics ===")
                
                for key, process in metrics["processes"].items():
                    info = process["info"]
                    proc_metrics = process["metrics"]
                    
                    lines.append(f"\n{info['name']} (PID: {info['process_id']}) - Plugin: {info['plugin_id']}")
                    if "error" in proc_metrics:
                        lines.append(f"  Error: {proc_metrics['error']}")
                    else:
                        lines.append(f"  CPU: {proc_metrics['cpu_percent']}%")
                        lines.append(f"  Memory: {proc_metrics['memory_percent']}% ({proc_metrics['memory_rss']:.1f} MB)")
                        lines.append(f"  Status: {proc_metrics['status']}")
                        lines.append(f"  Threads: {proc_metrics['threads']}")
                        
            # Add custom metrics
            if "custom" in metrics:
                lines.append("\n=== Custom Metrics ===")
                
                for key, metric in metrics["custom"].items():
                    metadata = metric["metadata"]
                    lines.append(f"\n{metadata['name']} - Plugin: {metric['plugin_id']}")
                    lines.append(f"  Value: {metric['value']} {metadata['unit']}")
                    lines.append(f"  Description: {metadata['description']}")
                    
            return "\n".join(lines)
