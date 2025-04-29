"""
Plugin Dependency Manager for IrintAI Assistant
Handles plugin dependencies and version requirements
"""
import os
import json
from typing import Dict, List, Any, Tuple, Set, Optional

class DependencyManager:
    """
    Manages plugin dependencies and version requirements
    """
    
    def __init__(self, logger=None):
        """
        Initialize the dependency manager
        
        Args:
            logger: Optional logger for dependency logging
        """
        self.logger = logger
        self.plugins = {}  # Plugin info by plugin_id
        self.plugin_dependencies = {}  # Dependencies by plugin_id
        
    def _log(self, message, level="INFO"):
        """Log a message if logger is available"""
        if self.logger:
            if hasattr(self.logger, 'log'):
                self.logger.log(f"[DependencyManager] {message}", level)
            else:
                print(f"[DependencyManager] {message}")
                
    def register_plugin(self, plugin_id: str, plugin_info: Dict[str, Any]) -> bool:
        """
        Register a plugin with the dependency manager
        
        Args:
            plugin_id: Plugin identifier
            plugin_info: Plugin metadata
            
        Returns:
            True if registration was successful
        """
        if not plugin_info:
            self._log(f"Failed to register plugin {plugin_id}: No plugin info provided", "ERROR")
            return False
            
        # Extract plugin information
        plugin_data = {
            'id': plugin_id,
            'name': plugin_info.get('name', plugin_id),
            'version': plugin_info.get('version', '1.0.0'),
            'compatibility': plugin_info.get('compatibility', '0.0.0'),
            'dependencies': plugin_info.get('dependencies', [])
        }
        
        # Register the plugin
        self.plugins[plugin_id] = plugin_data
        
        # Process dependencies
        self._process_dependencies(plugin_id, plugin_data['dependencies'])
        
        self._log(f"Registered plugin {plugin_id} v{plugin_data['version']}")
        return True
        
    def unregister_plugin(self, plugin_id: str) -> bool:
        """
        Unregister a plugin from the dependency manager
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if unregistration was successful
        """
        if plugin_id not in self.plugins:
            return False
            
        # Remove plugin
        del self.plugins[plugin_id]
        
        # Remove dependencies
        if plugin_id in self.plugin_dependencies:
            del self.plugin_dependencies[plugin_id]
            
        # Remove this plugin as a dependency for other plugins
        for dependencies in self.plugin_dependencies.values():
            dependencies.discard(plugin_id)
            
        self._log(f"Unregistered plugin {plugin_id}")
        return True
        
    def _process_dependencies(self, plugin_id: str, dependencies: List[str]) -> None:
        """
        Process plugin dependencies
        
        Args:
            plugin_id: Plugin identifier
            dependencies: List of dependency strings
        """
        if not dependencies:
            self.plugin_dependencies[plugin_id] = set()
            return
            
        # Parse dependencies
        dep_set = set()
        for dep in dependencies:
            # Dependencies can be specified as "plugin_id" or "plugin_id>=1.0.0"
            parts = dep.split('>=')
            if len(parts) == 1:
                dep_id = parts[0].strip()
                dep_set.add(dep_id)
            else:
                dep_id = parts[0].strip()
                # We could store version requirements here if needed
                dep_set.add(dep_id)
                
        self.plugin_dependencies[plugin_id] = dep_set
        
    def check_dependencies(self, plugin_id: str, active_plugins: List[str]) -> Tuple[bool, List[str]]:
        """
        Check if all dependencies for a plugin are satisfied
        
        Args:
            plugin_id: Plugin identifier
            active_plugins: List of currently active plugin IDs
            
        Returns:
            Tuple of (dependencies_met, missing_dependencies)
        """
        if plugin_id not in self.plugin_dependencies:
            return True, []
            
        dependencies = self.plugin_dependencies[plugin_id]
        if not dependencies:
            return True, []
            
        # Check if all dependencies are in active plugins
        active_set = set(active_plugins)
        missing = dependencies - active_set
        
        if missing:
            return False, list(missing)
        return True, []
        
    def get_plugin_dependents(self, plugin_id: str) -> List[str]:
        """
        Get plugins that depend on the given plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            List of plugin IDs that depend on the given plugin
        """
        dependents = []
        for pid, dependencies in self.plugin_dependencies.items():
            if plugin_id in dependencies:
                dependents.append(pid)
                
        return dependents
        
    def get_activation_order(self, plugin_ids: List[str]) -> List[str]:
        """
        Get the order in which plugins should be activated
        
        Args:
            plugin_ids: List of plugin IDs to activate
            
        Returns:
            Ordered list of plugin IDs
        """
        # Build dependency graph
        graph = {}
        for pid in plugin_ids:
            if pid in self.plugin_dependencies:
                # Only include dependencies that are in the list of plugins to activate
                deps = [d for d in self.plugin_dependencies[pid] if d in plugin_ids]
                graph[pid] = deps
            else:
                graph[pid] = []
                
        # Topological sort
        result = []
        visited = set()
        temp_mark = set()
        
        def visit(node):
            if node in temp_mark:
                # Circular dependency
                self._log(f"Circular dependency detected for plugin {node}", "WARNING")
                return
                
            if node not in visited:
                temp_mark.add(node)
                
                # Visit dependencies first
                for dep in graph.get(node, []):
                    visit(dep)
                    
                temp_mark.discard(node)
                visited.add(node)
                result.append(node)
                
        # Visit all nodes
        for pid in graph:
            if pid not in visited:
                visit(pid)
                
        # Reverse to get activation order (dependencies first)
        return list(reversed(result))
        
    def get_deactivation_order(self, plugin_ids: List[str]) -> List[str]:
        """
        Get the order in which plugins should be deactivated
        
        Args:
            plugin_ids: List of plugin IDs to deactivate
            
        Returns:
            Ordered list of plugin IDs
        """
        # For deactivation, we want the reverse of the activation order
        # (dependents before dependencies)
        activation_order = self.get_activation_order(plugin_ids)
        return list(reversed(activation_order))
        
    def verify_compatibility(self, plugin_id: str, core_version: str) -> bool:
        """
        Verify if a plugin is compatible with the core
        
        Args:
            plugin_id: Plugin identifier
            core_version: Core system version
            
        Returns:
            True if compatible
        """
        if plugin_id not in self.plugins:
            return False
            
        plugin_data = self.plugins[plugin_id]
        required_version = plugin_data.get('compatibility', '0.0.0')
        
        # Simple version comparison
        core_parts = self._parse_version(core_version)
        required_parts = self._parse_version(required_version)
        
        # Core version must be >= required version
        for i in range(max(len(core_parts), len(required_parts))):
            core_part = core_parts[i] if i < len(core_parts) else 0
            required_part = required_parts[i] if i < len(required_parts) else 0
            
            if core_part > required_part:
                return True
            if core_part < required_part:
                return False
                
        return True
        
    def _parse_version(self, version_str: str) -> List[int]:
        """
        Parse a version string into parts
        
        Args:
            version_str: Version string (e.g., "1.2.3")
            
        Returns:
            List of version parts
        """
        try:
            parts = version_str.split('.')
            return [int(p) for p in parts]
        except ValueError:
            self._log(f"Invalid version format: {version_str}", "ERROR")
            return [0, 0, 0]
            
    def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        """
        Get information about a plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Plugin information dictionary
        """
        return self.plugins.get(plugin_id, {})
        
    def get_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all plugins
        
        Returns:
            Dictionary of plugin information by plugin ID
        """
        return self.plugins.copy()
        
    def get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """
        Get dependencies for a plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            List of dependency plugin IDs
        """
        if plugin_id not in self.plugin_dependencies:
            return []
        return list(self.plugin_dependencies[plugin_id])
        
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get the complete dependency graph
        
        Returns:
            Dictionary of plugin IDs to their dependencies
        """
        graph = {}
        for plugin_id, deps in self.plugin_dependencies.items():
            graph[plugin_id] = list(deps)
        return graph