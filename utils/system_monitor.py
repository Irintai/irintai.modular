"""
System monitoring utilities for tracking CPU, RAM, GPU, and disk usage
"""
import os
import shutil
import subprocess
import psutil
from typing import Dict, Tuple, Any, Optional

class SystemMonitor:
    """Monitor system resources like CPU, RAM, GPU, and disk space"""
    
    def __init__(self, logger=None):
        """
        Initialize the system monitor
        
        Args:
            logger: Optional logging function
        """
        self.logger = logger
        
    def log(self, msg: str) -> None:
        """
        Log a message if logger is available
        
        Args:
            msg: Message to log
        """
        if self.logger:
            self.logger(msg)
    
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
        if system_info["cpu"]["usage_percent"] > 90:
            return True, "CPU usage is critical (>90%)"
            
        # Check RAM usage
        if system_info["ram"]["usage_percent"] > 90:
            return True, "RAM usage is critical (>90%)"
            
        # Check disk space
        if system_info["disk"]["free_gb"] < 5:
            return True, f"Low disk space: only {system_info['disk']['free_gb']} GB free"
            
        # Check GPU if available
        if system_info["gpu"]["usage_percent"] != "N/A":
            try:
                gpu_percent = int(system_info["gpu"]["usage_percent"].replace("%", ""))
                if gpu_percent > 90:
                    return True, "GPU usage is critical (>90%)"
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
        
        # Check for warning level (>70%)
        if (system_info["cpu"]["usage_percent"] > 70 or
            system_info["ram"]["usage_percent"] > 70):
            return "#fff0b3"  # Light yellow
        
        # Check GPU if available
        if system_info["gpu"]["usage_percent"] != "N/A":
            try:
                gpu_percent = int(system_info["gpu"]["usage_percent"].replace("%", ""))
                if gpu_percent > 70:
                    return "#fff0b3"  # Light yellow
            except:
                pass
                
        return "#d1f5d3"  # Light green for normal usage
