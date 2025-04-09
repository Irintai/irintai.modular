"""
File operations utilities for the Irintai assistant
"""
import os
import json
import shutil
import subprocess
import sys
from typing import Dict, List, Any, Optional, Tuple, Set

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.py', '.txt', '.md', '.pdf', '.docx', '.json', '.sty']

class FileOps:
    """File operations utilities for loading, saving, and managing files"""
    
    def __init__(self, logger=None):
        """
        Initialize the file operations utility
        
        Args:
            logger: Optional logging function
        """
        self.logger = logger
        self.content_cache = {}
        
    def log(self, msg: str) -> None:
        """
        Log a message if logger is available
        
        Args:
            msg: Message to log
        """
        if self.logger:
            self.logger(msg)
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> Tuple[bool, str]:
        """
        Read a file and return its content
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            Tuple containing success flag and file content
        """
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
                
            # Cache the content for later use
            self.content_cache[file_path] = content
            
            return True, content
        except Exception as e:
            self.log(f"[File Error] Failed to read {file_path}: {e}")
            return False, f"Error: {str(e)}"
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        Write content to a file
        
        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding
            
        Returns:
            True if file written successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
                
            # Update the cache
            self.content_cache[file_path] = content
            
            self.log(f"[File] Wrote to {file_path}")
            return True
        except Exception as e:
            self.log(f"[File Error] Failed to write to {file_path}: {e}")
            return False
    
    def append_to_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        Append content to a file
        
        Args:
            file_path: Path to the file
            content: Content to append
            encoding: File encoding
            
        Returns:
            True if content appended successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
                
            # Update the cache if it exists
            if file_path in self.content_cache:
                self.content_cache[file_path] += content
                
            self.log(f"[File] Appended to {file_path}")
            return True
        except Exception as e:
            self.log(f"[File Error] Failed to append to {file_path}: {e}")
            return False
    
    def list_files(self, directory: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        List files in a directory with optional extension filtering
        
        Args:
            directory: Directory to list files from
            extensions: Optional list of file extensions to filter by
            
        Returns:
            List of file paths
        """
        try:
            files = []
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if extensions:
                        if any(filename.endswith(ext) for ext in extensions):
                            files.append(file_path)
                    else:
                        files.append(file_path)
                        
            return files
        except Exception as e:
            self.log(f"[File Error] Failed to list files in {directory}: {e}")
            return []
    
    def load_json(self, file_path: str) -> Tuple[bool, Any]:
        """
        Load a JSON file
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple containing success flag and loaded data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return True, data
        except Exception as e:
            self.log(f"[JSON Error] Failed to load {file_path}: {e}")
            return False, None
    
    def save_json(self, file_path: str, data: Any, indent: int = 2) -> bool:
        """
        Save data to a JSON file
        
        Args:
            file_path: Path to the JSON file
            data: Data to save
            indent: JSON indentation
            
        Returns:
            True if data saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent)
                
            self.log(f"[JSON] Saved to {file_path}")
            return True
        except Exception as e:
            self.log(f"[JSON Error] Failed to save to {file_path}: {e}")
            return False
    
    def copy_file(self, source: str, destination: str) -> bool:
        """
        Copy a file
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if file copied successfully, False otherwise
        """
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
            
            shutil.copy2(source, destination)
            
            self.log(f"[File] Copied {source} to {destination}")
            return True
        except Exception as e:
            self.log(f"[File Error] Failed to copy {source} to {destination}: {e}")
            return False
    
    def move_file(self, source: str, destination: str) -> bool:
        """
        Move a file
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if file moved successfully, False otherwise
        """
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
            
            shutil.move(source, destination)
            
            # Update cache if needed
            if source in self.content_cache:
                self.content_cache[destination] = self.content_cache[source]
                del self.content_cache[source]
                
            self.log(f"[File] Moved {source} to {destination}")
            return True
        except Exception as e:
            self.log(f"[File Error] Failed to move {source} to {destination}: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file deleted successfully, False otherwise
        """
        try:
            os.remove(file_path)
            
            # Remove from cache if present
            if file_path in self.content_cache:
                del self.content_cache[file_path]
                
            self.log(f"[File] Deleted {file_path}")
            return True
        except Exception as e:
            self.log(f"[File Error] Failed to delete {file_path}: {e}")
            return False
    
    def ensure_dir(self, directory: str) -> bool:
        """
        Ensure a directory exists
        
        Args:
            directory: Directory path
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            self.log(f"[Directory Error] Failed to create {directory}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            stats = os.stat(file_path)
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "extension": os.path.splitext(file_path)[1],
                "size": stats.st_size,
                "created": stats.st_ctime,
                "modified": stats.st_mtime,
                "exists": True
            }
        except Exception as e:
            self.log(f"[File Error] Failed to get info for {file_path}: {e}")
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "extension": os.path.splitext(file_path)[1],
                "exists": False,
                "error": str(e)
            }
    
    def open_folder(self, folder_path: str) -> bool:
        """
        Open a folder in the file explorer
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            True if folder opened successfully, False otherwise
        """
        try:
            if not os.path.exists(folder_path):
                self.ensure_dir(folder_path)
            
            # Open folder based on OS
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', folder_path])
                
            self.log(f"[Folder] Opened {folder_path}")
            return True
        except Exception as e:
            self.log(f"[Folder Error] Failed to open {folder_path}: {e}")
            return False
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions
        
        Returns:
            List of supported extensions
        """
        return SUPPORTED_EXTENSIONS
    
    def add_supported_extension(self, extension: str) -> None:
        """
        Add a file extension to the supported list
        
        Args:
            extension: File extension to add (including the dot)
        """
        global SUPPORTED_EXTENSIONS
        if extension not in SUPPORTED_EXTENSIONS:
            SUPPORTED_EXTENSIONS.append(extension)
            
    def get_content_types(self) -> Dict[str, str]:
        """
        Get a mapping of file extensions to content types
        
        Returns:
            Dictionary mapping file extensions to content types
        """
        return {
            '.py': 'Python Source',
            '.txt': 'Text File',
            '.md': 'Markdown',
            '.pdf': 'PDF Document',
            '.docx': 'Word Document',
            '.json': 'JSON Data',
            '.sty': 'LaTeX Style',
            '.csv': 'CSV Data',
            '.html': 'HTML Document',
            '.css': 'CSS Stylesheet',
            '.js': 'JavaScript',
            '.xml': 'XML Document',
            '.yaml': 'YAML Data',
            '.yml': 'YAML Data',
            '.ini': 'Configuration File',
            '.cfg': 'Configuration File',
            '.log': 'Log File'
        }
        
    def get_file_extension(self, file_path: str) -> str:
        """
        Get the extension of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            File extension
        """
        return os.path.splitext(file_path)[1].lower()
        
    def get_files_by_type(self, directory: str, extension: str) -> List[str]:
        """
        Get all files of a specific type in a directory
        
        Args:
            directory: Directory to search
            extension: File extension to filter by
            
        Returns:
            List of file paths
        """
        return self.list_files(directory, [extension])
        
    def get_file_tree(self, directory: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Get a tree representation of files in a directory
        
        Args:
            directory: Directory to scan
            max_depth: Maximum directory depth to scan
            
        Returns:
            Dictionary representing the file tree
        """
        def scan_dir(path: str, current_depth: int) -> Dict[str, Any]:
            if current_depth > max_depth:
                return {"name": os.path.basename(path), "type": "directory", "truncated": True}
                
            result = {
                "name": os.path.basename(path),
                "path": path,
                "type": "directory",
                "children": []
            }
            
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        result["children"].append(scan_dir(item_path, current_depth + 1))
                    else:
                        result["children"].append({
                            "name": item,
                            "path": item_path,
                            "type": "file",
                            "extension": self.get_file_extension(item)
                        })
            except Exception as e:
                self.log(f"[File Tree Error] Failed to scan {path}: {e}")
                result["error"] = str(e)
                
            return result
            
        return scan_dir(directory, 1)
        
    def search_files(self, directory: str, search_term: str, extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for files containing a specific term
        
        Args:
            directory: Directory to search
            search_term: Term to search for
            extensions: Optional list of file extensions to filter by
            
        Returns:
            List of dictionaries with file information and matches
        """
        results = []
        files = self.list_files(directory, extensions)
        
        for file_path in files:
            try:
                success, content = self.read_file(file_path)
                if success and search_term.lower() in content.lower():
                    # Count occurrences
                    count = content.lower().count(search_term.lower())
                    
                    # Get some context around matches
                    context = []
                    content_lower = content.lower()
                    search_lower = search_term.lower()
                    
                    start = 0
                    while True:
                        pos = content_lower.find(search_lower, start)
                        if pos == -1:
                            break
                            
                        # Get context (50 chars before and after)
                        ctx_start = max(0, pos - 50)
                        ctx_end = min(len(content), pos + len(search_term) + 50)
                        context_str = content[ctx_start:ctx_end]
                        
                        # Highlight the match
                        match_start = max(0, pos - ctx_start)
                        match_end = match_start + len(search_term)
                        
                        context.append({
                            "before": context_str[:match_start],
                            "match": context_str[match_start:match_end],
                            "after": context_str[match_end:]
                        })
                        
                        start = pos + len(search_term)
                        
                        # Limit to 5 contexts
                        if len(context) >= 5:
                            break
                    
                    results.append({
                        "path": file_path,
                        "name": os.path.basename(file_path),
                        "extension": self.get_file_extension(file_path),
                        "count": count,
                        "context": context
                    })
            except Exception as e:
                self.log(f"[Search Error] Failed to search {file_path}: {e}")
                
        return results