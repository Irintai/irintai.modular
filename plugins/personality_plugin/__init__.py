"""
Personality Plugin for Irintai Assistant
"""
from plugins.personality_plugin.core.personality_plugin import PersonalityPlugin
from plugins.personality_plugin.ui.panel import Panel
from plugins.personality_plugin.config_handler import ConfigHandler
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import time
import json


# Export the activate_ui function at the module level
__all__ = ['IrintaiPlugin', 'activate_ui']
class IrintaiPlugin:
    """
    Plugin wrapper that integrates core functionality with UI
    
    This class implements the standard Irintai plugin interface
    and connects the core plugin with its UI representation.
    """
    
    # Forward metadata from core plugin
    METADATA = PersonalityPlugin.METADATA
    
    # Forward status constants
    STATUS = PersonalityPlugin.STATUS
    
    def __init__(
        self, 
        core_system,
        config_path=None,
        logger=None,
        **kwargs
    ):
        """
        Initialize the plugin wrapper
        
        Args:
            core_system: Reference to Irintai core system
            config_path: Path to plugin configuration
            logger: Optional logging function
            **kwargs: Additional initialization parameters
        """
        # Create core plugin instance
        self.plugin = PersonalityPlugin(
            core_system,
            config_path,
            logger,
            **kwargs
        )
        
        # UI components (initialized on demand)
        self.ui_panel = None
    
    def get_ui_panel(self, parent):
        """
        Create and return UI panel
        
        Args:
            parent: Parent widget
            
        Returns:
            UI panel frame
        """
        if self.ui_panel is None:
            # Create UI panel
            panel = Panel(parent, self.plugin)
            self.ui_panel = panel.ui_panel
        
        return self.ui_panel
    
    # Forward core methods
    def activate(self):
        """Activate the plugin"""
        return self.plugin.activate()
    
    def deactivate(self):
        """Deactivate the plugin"""
        return self.plugin.deactivate()    
    
    def update_configuration(self, **kwargs):
        """Update plugin configuration"""
        return self.plugin.update_configuration(**kwargs)
    
    def get_status(self):
        """Get plugin status"""
        return self.plugin.get_status()
        
    def get_config_schema(self):
        """
        Get configuration schema for the plugin settings UI
        
        Returns:
            Dictionary with configuration schema
        """
        # Return a fixed schema that maps to the plugin's configuration
        return {
            "active_profile": {
                "type": "choice",
                "label": "Active Profile",
                "description": "The personality profile to use for conversations",
                "options": self.plugin.get_available_profiles(),
                "default": self.plugin.get_active_profile_name() or ""
            },
            "auto_remember": {
                "type": "boolean",
                "label": "Remember Personality",
                "description": "Store personality attributes in memory for context-aware responses",
                "default": True
            }
        }
    
    def get_configuration(self):
        """
        Get current plugin configuration
        
        Returns:
            Dictionary with current configuration values
        """
        return {
            "active_profile": self.plugin.get_active_profile_name(),
            "auto_remember": self.plugin.get_auto_remember_setting()
        }
    
    def on_config_changed(self, new_config):
        """
        Handle configuration changes from the plugin settings panel
        
        Args:
            new_config: New configuration values
            
        Returns:
            True if configuration was applied successfully
        """
        # Apply the new configuration
        try:
            # Update active profile if specified
            if "active_profile" in new_config and new_config["active_profile"]:
                profile_name = new_config["active_profile"]
                if profile_name in self.plugin.get_available_profiles():
                    self.plugin.set_active_profile(profile_name)
            
            # Update auto remember setting if specified
            if "auto_remember" in new_config:
                self.plugin.set_auto_remember(new_config["auto_remember"])
                
            # Save settings
            return self.plugin.update_configuration(**new_config)
        except Exception as e:
            if hasattr(self, 'plugin') and hasattr(self.plugin, '_logger'):
                self.plugin._logger(f"Error applying configuration changes: {e}", "ERROR")
            return False    # Module-level UI activation function
    def activate_ui(container):
            """
            Create and activate UI for the plugin when loaded by the plugin manager
            
            Args:
                container: UI container to place panel in
                
            Returns:
                The activated UI panel
            """
from plugins.personality_plugin.ui import activate_ui as ui_activator
            return ui_activator(container)

    # Add these methods to the IrintaiPlugin class to complete the implementation:

    def get_active_profile_name(self):
        """
        Get the name of the currently active profile
        
        Returns:
            Name of active profile or None
        """
        return self.plugin.get_active_profile_name()

    def get_active_profile(self):
        """
        Get the currently active profile data
        
        Returns:
            Active profile data dictionary or None
        """
        return self.plugin.get_active_profile()

    def set_active_profile(self, profile_name):
        """
        Set the active profile by name
        
        Args:
            profile_name: Name of profile to activate
            
        Returns:
            Success flag
        """
        return self.plugin.set_active_profile(profile_name)

    def get_available_profiles(self):
        """
        Get a list of all available profile names
        
        Returns:
            List of profile names
        """
        return self.plugin.get_available_profiles()

    def get_profile(self, profile_name):
        """
        Get a specific profile by name
        
        Args:
            profile_name: Name of profile to retrieve
            
        Returns:
            Profile data dictionary or None
        """
        return self.plugin.get_profile(profile_name)

    def create_profile(self, profile_data):
        """
        Create a new profile
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            Success flag
        """
        return self.plugin.create_profile(profile_data)

    def update_profile(self, profile_name, profile_data):
        """
        Update an existing profile
        
        Args:
            profile_name: Name of profile to update
            profile_data: New profile data
            
        Returns:
            Success flag
        """
        return self.plugin.update_profile(profile_name, profile_data)

    def delete_profile(self, profile_name):
        """
        Delete a profile
        
        Args:
            profile_name: Name of profile to delete
            
        Returns:
            Success flag
        """
        return self.plugin.delete_profile(profile_name)

    def import_profile_from_file(self, file_path):
        """
        Import a profile from a JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Success flag
        """
        return self.plugin.import_profile_from_file(file_path)

    def export_profile_to_file(self, profile_name, file_path):
        """
        Export a profile to a JSON file
        
        Args:
            profile_name: Name of profile to export
            file_path: Path to save JSON file
            
        Returns:
            Success flag
        """
        return self.plugin.export_profile_to_file(profile_name, file_path)

    def analyze_message_style(self, message):
        """
        Analyze a message to determine its style characteristics
        
        Args:
            message: Message to analyze
            
        Returns:
            Dictionary of style characteristics with scores
        """
        return self.plugin.analyze_message_style(message)

    # Plugin instantiation function
    def get_plugin_instance(core_system, config_path=None, logger=None, **kwargs):
        """
        Create a plugin instance
        
        Args:
            core_system: Irintai core system
            config_path: Optional configuration path
            logger: Optional logger function
            **kwargs: Additional parameters
            
        Returns:
            Plugin instance
        """
        # Import the bridge
from plugins.personality_plugin.bridge import PersonalityBridge
        
        # Apply compatibility bridge
        bridge = PersonalityBridge(core_system)
        bridge.ensure_compatibility()
        
        # Create and return plugin instance
        return IrintaiPlugin(core_system, config_path, logger, **kwargs)

    # In plugins/personality_plugin/__init__.py

    def get_chat_ui_extension(self, chat_panel):
        """
        Get UI extension for the chat panel
        
        Args:
            chat_panel: Reference to the chat panel
            
        Returns:
            Extension specification
        """
        # Create container frame for our controls
        container = ttk.Frame(chat_panel.frame)
        
        # Create personality controls
        self._create_personality_controls(container, chat_panel)
        
        # Register message hook for style transformation
        chat_panel.register_message_hook("personality_plugin", self._message_hook)
        
        # Return extension specification
        return {
            "location": "top_bar",
            "title": "Personality",
            "components": [container],
        }

    def _create_personality_controls(self, container, chat_panel):
        """Create personality plugin controls"""
        # First row - active profile selection
        profile_frame = ttk.Frame(container)
        profile_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(profile_frame, text="Active Profile:").pack(side=tk.LEFT)
        
        # Get available profiles
        profiles = self.plugin.get_available_profiles()
        active_profile = self.plugin.get_active_profile_name()
        
        # Create dropdown
        self.personality_var = tk.StringVar(value=active_profile if active_profile else "")
        self.personality_dropdown = ttk.Combobox(
            profile_frame,
            textvariable=self.personality_var,
            values=sorted(profiles),
            state="readonly",
            width=30
        )
        self.personality_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.personality_dropdown.bind("<<ComboboxSelected>>", self._on_personality_changed)
        
        # Apply button
        ttk.Button(
            profile_frame,
            text="Apply",
            command=self._apply_personality
        ).pack(side=tk.LEFT, padx=5)
        
        # Settings button
        ttk.Button(
            profile_frame,
            text="Settings",
            command=lambda: self._open_settings(chat_panel)
        ).pack(side=tk.LEFT, padx=5)
        
        # Second row - style indicators
        style_frame = ttk.Frame(container)
        style_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Create indicators for active profile's style
        style_indicators = ["formality", "creativity", "empathy", "directness"]
        self.style_indicators = {}
        
        for i, indicator in enumerate(style_indicators):
            style_frame.columnconfigure(i, weight=1)
            
            label_frame = ttk.Frame(style_frame)
            label_frame.grid(row=0, column=i, padx=5, sticky=tk.EW)
            
            ttk.Label(
                label_frame,
                text=indicator.capitalize(),
                font=("Helvetica", 8)
            ).pack(anchor=tk.CENTER)
            
            # Create indicator value
            value_var = tk.StringVar(value="0.5")
            value_label = ttk.Label(
                label_frame,
                textvariable=value_var,
                font=("Helvetica", 8, "bold")
            )
            value_label.pack(anchor=tk.CENTER)
            
            self.style_indicators[indicator] = value_var
        
        # Update indicators
        self._update_style_indicators()
        
        # Store chat_panel reference for later
        self._chat_panel = chat_panel

    def _on_personality_changed(self, event):
        """Handle personality profile selection change"""
        self._apply_personality()
        
    def _apply_personality(self):
        """Apply the selected personality profile"""
        profile_name = self.personality_var.get()
        if not profile_name:
            return
            
        # Set the active profile
        success = self.plugin.set_active_profile(profile_name)
        
        if success:
            # Update style indicators
            self._update_style_indicators()
            
            # Update system prompt with personality settings
            self._update_system_prompt()
            
            # Show confirmation in chat panel
            if hasattr(self, "_chat_panel"):
                self._chat_panel.console.insert(
                    tk.END,
                    f"[System] Personality profile set to: {profile_name}\n\n",
                    "system"
                )
                self._chat_panel.console.see(tk.END)
        
    def _update_style_indicators(self):
        """Update the style indicators based on active profile"""
        active_profile = self.plugin.get_active_profile()
        if not active_profile:
            return
            
        # Get style modifiers
        style_modifiers = active_profile.get("style_modifiers", {})
        
        # Update indicators
        for indicator, var in self.style_indicators.items():
            value = style_modifiers.get(indicator, 0.5)
            var.set(f"{value:.1f}")
            
    def _update_system_prompt(self):
        """Update system prompt to reflect personality settings"""
        if not hasattr(self, "_chat_panel"):
            return
            
        # Get bridge to handle system prompt modification
from plugins.personality_plugin.bridge import PersonalityBridge
        bridge = PersonalityBridge(self._chat_panel.parent)
        bridge.ensure_compatibility()
        
        # Get system prompt hook
        system_prompt_hook = bridge.get_system_prompt_hook()
        
        if not system_prompt_hook:
            return
            
        # Get base prompt
        base_prompt = self._chat_panel.system_prompt_var.get()
        
        # Apply personality modifications
        modified_prompt = system_prompt_hook(base_prompt, self.plugin)
        
        # Update the entry and apply
        self._chat_panel.system_prompt_var.set(modified_prompt)
        self._chat_panel.apply_system_prompt()
        
    def _open_settings(self, chat_panel):
        """Open the personality settings panel"""
        # Create a top-level window
        settings_window = tk.Toplevel(chat_panel.frame)
        settings_window.title("Personality Settings")
        settings_window.transient(chat_panel.frame)
        settings_window.grab_set()
        
        # Set size and position
        settings_window.geometry(f"600x500+{chat_panel.frame.winfo_rootx()+50}+{chat_panel.frame.winfo_rooty()+50}")
        
        # Add our UI panel
        panel = self.get_ui_panel(settings_window)
        panel.pack(fill=tk.BOTH, expand=True)
        
    def _message_hook(self, content, role):
        """
        Message hook for style transformation
        
        Args:
            content: Message content
            role: Message role (user/assistant)
            
        Returns:
            Transformed content or None
        """
        # Only modify assistant messages
        if role != "assistant":
            return None
        
        try:
            # Get active profile
            active_profile = self.plugin.get_active_profile()
            if not active_profile:
                return None
                
            # Apply style transformation
from plugins.personality_plugin.core.helpers import apply_style_transforms
            return apply_style_transforms(content, active_profile)
                
        except Exception as e:
            if hasattr(self, "_chat_panel") and self._chat_panel and hasattr(self._chat_panel, "log"):
                self._chat_panel.log(f"[Personality] Error applying style: {e}")
            return None

    # In plugins/personality_plugin/__init__.py 
    # Add this to the IrintaiPlugin class

    def get_dashboard_extension(self, dashboard):
        """
        Get dashboard extension for the plugin
        
        Args:
            dashboard: Reference to the dashboard
        
        Returns:
            Extension specification
        """
        # Create dashboard component
        dashboard_component = self._create_personality_dashboard(dashboard.plugins_tab)
        
        # Create overview widget with key statistics
        overview_frame = ttk.Frame(dashboard.plugin_overview_frame)
        
        # Add current profile indicator
        active_profile = self.plugin.get_active_profile_name() or "None"
        profile_frame = ttk.Frame(overview_frame)
        profile_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(profile_frame, text="Active Personality:").pack(side=tk.LEFT)
        self.dash_profile_var = tk.StringVar(value=active_profile)
        ttk.Label(
            profile_frame,
            textvariable=self.dash_profile_var,
            font=("Helvetica", 9, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        # Return extension specification
        return {
            "dashboard_tab": dashboard_component,
            "overview_widgets": [overview_frame],
            "stats_provider": self._provide_dashboard_stats,
            "refresh_rate": 5  # Refresh every 5 seconds
        }
        
    def _create_personality_dashboard(self, parent):
        """
        Create dashboard component for the plugin
        
        Args:
            parent: Parent widget
        
        Returns:
            Dashboard component
        """
        # Create main frame
        frame = ttk.Frame(parent)
        
        # Profile statistics section
        profile_frame = ttk.LabelFrame(frame, text="Profile Statistics")
        profile_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats_grid = ttk.Frame(profile_frame)
        stats_grid.pack(fill=tk.X, padx=5, pady=5)
        
        for i in range(2):
            stats_grid.columnconfigure(i, weight=1)
        
        # Row 1: Total profiles
        ttk.Label(stats_grid, text="Total Profiles:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.total_profiles_var = tk.StringVar(value=str(len(self.plugin.get_available_profiles())))
        ttk.Label(
            stats_grid,
            textvariable=self.total_profiles_var,
            font=("Helvetica", 9, "bold")
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Row 2: Active profile
        ttk.Label(stats_grid, text="Active Profile:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.active_profile_var = tk.StringVar(value=self.plugin.get_active_profile_name() or "None")
        ttk.Label(
            stats_grid,
            textvariable=self.active_profile_var,
            font=("Helvetica", 9, "bold")
        ).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Row 3: Messages transformed
        ttk.Label(stats_grid, text="Messages Transformed:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.messages_var = tk.StringVar(value="0")
        ttk.Label(
            stats_grid,
            textvariable=self.messages_var
        ).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Style distribution section
        style_frame = ttk.LabelFrame(frame, text="Style Distribution")
        style_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create style indicators
        style_grid = ttk.Frame(style_frame)
        style_grid.pack(fill=tk.X, padx=5, pady=5)
        
        style_dimensions = [
            "formality", "creativity", "complexity", "empathy", 
            "directness", "humor", "enthusiasm", "conciseness"
        ]
        
        # Create a grid for the style indicators (2 columns)
        self.style_progress = {}
        self.style_values = {}
        
        for i, dim in enumerate(style_dimensions):
            row = i // 2
            col = i % 2
            
            # Create frame for this dimension
            dim_frame = ttk.Frame(style_grid)
            dim_frame.grid(row=row, column=col, sticky=tk.EW, padx=5, pady=2)
            
            # Add label
            ttk.Label(
                dim_frame, 
                text=f"{dim.capitalize()}:",
                width=12
            ).pack(side=tk.LEFT)
            
            # Add value label
            value_var = tk.StringVar(value="0.5")
            self.style_values[dim] = value_var
            
            ttk.Label(
                dim_frame,
                textvariable=value_var,
                width=4
            ).pack(side=tk.LEFT)
            
            # Add progress bar
            progress = ttk.Progressbar(
                dim_frame,
                length=100,
                mode="determinate",
                maximum=100,
                value=50
            )
            progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.style_progress[dim] = progress
        
        # Profiles list section
        profiles_frame = ttk.LabelFrame(frame, text="Available Profiles")
        profiles_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create profiles listbox with scrollbar
        profiles_list_frame = ttk.Frame(profiles_frame)
        profiles_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.profiles_listbox = tk.Listbox(
            profiles_list_frame,
            height=6
        )
        self.profiles_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        profiles_scrollbar = ttk.Scrollbar(
            profiles_list_frame,
            orient=tk.VERTICAL,
            command=self.profiles_listbox.yview
        )
        profiles_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.profiles_listbox.config(yscrollcommand=profiles_scrollbar.set)
        
        # Populate profiles list
        for profile in sorted(self.plugin.get_available_profiles()):
            active = profile == self.plugin.get_active_profile_name()
            display_name = f"* {profile}" if active else profile
            self.profiles_listbox.insert(tk.END, display_name)
        
        # Define update method for the component
        def update_stats(stats):
            # Update profile counters
            if "total_profiles" in stats:
                self.total_profiles_var.set(str(stats["total_profiles"]))
                
            if "active_profile" in stats:
                self.active_profile_var.set(stats["active_profile"] or "None")
                self.dash_profile_var.set(stats["active_profile"] or "None")
                
            if "messages_transformed" in stats:
                self.messages_transformed = stats["messages_transformed"]
                self.messages_var.set(str(stats["messages_transformed"]))
            
            # Update style indicators
            if "style_modifiers" in stats:
                style_modifiers = stats["style_modifiers"]
                for dim, value in style_modifiers.items():
                    if dim in self.style_values:
                        self.style_values[dim].set(f"{value:.2f}")
                        self.style_progress[dim]["value"] = value * 100
            
            # Update profiles list
            if "profiles" in stats:
                self.profiles_listbox.delete(0, tk.END)
                active = stats.get("active_profile")
                for profile in sorted(stats["profiles"]):
                    display_name = f"* {profile}" if profile == active else profile
                    self.profiles_listbox.insert(tk.END, display_name)
        
        # Attach the update method to the frame
        frame.update_stats = update_stats
        
        # Return the component
        return frame
        
    def _provide_dashboard_stats(self):
        """
        Provide statistics for the dashboard
        
        Returns:
            Dictionary of statistics
        """
        # Get basic stats
        available_profiles = self.plugin.get_available_profiles()
        active_profile = self.plugin.get_active_profile_name()
        active_profile_data = self.plugin.get_active_profile() or {}
        
        # Get message transformation count (we'd track this in the actual plugin)
        messages_transformed = getattr(self, "messages_transformed", 0)
        
        # Get style modifiers for active profile
        style_modifiers = active_profile_data.get("style_modifiers", {})
        
        # Return statistics dictionary
        return {
            "total_profiles": len(available_profiles),
            "active_profile": active_profile,
            "messages_transformed": messages_transformed,
            "profiles": available_profiles,
            "style_modifiers": style_modifiers
        }

    # In plugins/personality_plugin/__init__.py
    # Add this to the IrintaiPlugin class

    def get_log_viewer_extensions(self):
        """
        Get extensions for the log viewer
        
        Returns:
            Dictionary of log viewer extensions
        """
        return {
            "log_filters": {
                "Personality Messages": self._filter_personality_logs,
                "Style Changes": self._filter_style_change_logs
            },
            "log_processors": {
                "highlight_personalities": self._highlight_personality_names
            },
            "log_exporters": {
                "Export Personality Logs": self._export_personality_logs
            }
        }

    def _filter_personality_logs(self, log_lines):
        """
        Filter log lines to only show personality-related entries
        
        Args:
            log_lines: List of log lines
            
        Returns:
            Filtered list of log lines
        """
        filtered_lines = []
        search_terms = ["[Personality]", "personality profile", "style modifier"]
        
        for line in log_lines:
            if any(term in line for term in search_terms):
                filtered_lines.append(line)
                
        return filtered_lines

    def _filter_style_change_logs(self, log_lines):
        """
        Filter log lines to only show style change entries
        
        Args:
            log_lines: List of log lines
            
        Returns:
            Filtered list of log lines
        """
        filtered_lines = []
        
        for line in log_lines:
            if "[Personality]" in line and "style" in line.lower():
                filtered_lines.append(line)
                
        return filtered_lines

    def _highlight_personality_names(self, log_line):
        """
        Highlight personality profile names in log lines
        
        Args:
            log_line: A single log line
            
        Returns:
            Possibly modified log line
        """
        # Skip if not personality related
        if "[Personality]" not in log_line:
            return log_line
            
        # Get available profile names
        profiles = self.plugin.get_available_profiles()
        
        # Skip if no profiles
        if not profiles:
            return log_line
            
        # Simple implementation - we can't add tags here so we'll just add markers
        for profile in profiles:
            if profile in log_line:
                # Add visual indicator by surrounding with '*'
                log_line = log_line.replace(profile, f"*{profile}*")
                
        return log_line

    def _export_personality_logs(self, log_content, parent_window):
        """
        Export personality logs to a specialized format
        
        Args:
            log_content: Full log content
            parent_window: Parent window for dialogs
            
        Returns:
            Status message for user
        """
        # Generate default filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_filename = f"personality_logs_{timestamp}.json"
        
        # Open save dialog
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile=default_filename
        )
        
        if not filename:
            return None
            
        # Extract personality-related logs
        personality_logs = []
        for line in log_content.splitlines():
            if "[Personality]" in line:
                # Parse out timestamp if present
                timestamp = None
                if line.startswith("[") and "]" in line:
                    time_str = line[1:line.find("]")]
                    try:
                        # Try to convert to timestamp
                        timestamp = time.strftime(
                            "%Y-%m-%dT%H:%M:%S", 
                            time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        )
                    except:
                        pass
                        
                # Add to logs
                personality_logs.append({
                    "timestamp": timestamp,
                    "message": line,
                    "type": "style_change" if "style" in line.lower() else "profile_change"
                })
        
        # Create report structure
        report = {
            "title": "Personality Plugin Activity Report",
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_entries": len(personality_logs),
            "entries": personality_logs
        }
        
        # Save to file
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            
            return f"Exported {len(personality_logs)} personality log entries to {filename}"
        except Exception as e:
            raise Exception(f"Failed to export personality logs: {e}")

    # In plugins/personality_plugin/__init__.py
    # Add this to the IrintaiPlugin class

    def get_memory_extensions(self):
        """
        Get extensions for the memory panel
        
        Returns:
            Dictionary of memory extensions
        """
        return {
            "importers": {
                "Personality Profile": self._import_personality_profile,
                "AI Persona Template": self._import_ai_persona
            },
            "exporters": {
                "Export All Personalities": self._export_all_personalities
            },
            "ui_extensions": [
                self._create_memory_ui_extension()
            ]
        }
        
    def _create_memory_ui_extension(self):
        """
        Create a UI extension for the memory panel
        
        Returns:
            UI widget to be added to memory panel
        """
        # Create frame for personality memory integration
        extension_frame = ttk.Frame()
        
        # Add a label
        ttk.Label(
            extension_frame,
            text="Personality Memory Integration",
            font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Add description
        ttk.Label(
            extension_frame,
            text="Store personality profiles in memory to make the AI aware of them",
            wraplength=400
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Create button frame
        button_frame = ttk.Frame(extension_frame)
        button_frame.pack(fill=tk.X)
        
        # Add buttons for memory operations
        ttk.Button(
            button_frame,
            text="Store Active Profile",
            command=self._store_active_profile_in_memory
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Store All Profiles",
            command=self._store_all_profiles_in_memory
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        return extension_frame
        
    def _import_personality_profile(self, parent_window):
        """
        Import a personality profile from file or input
        
        Args:
            parent_window: Parent window for dialogs
            
        Returns:
            Dictionary with content and source, or None if cancelled
        """
        import json
        
        # Create dialog window
        dialog = tk.Toplevel(parent_window)
        dialog.title("Import Personality Profile")
        dialog.geometry("500x400")
        dialog.transient(parent_window)
        dialog.grab_set()
        
        result_data = {"content": "", "source": ""}
        
        # Create content frame
        content_frame = ttk.Frame(dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add text input
        ttk.Label(content_frame, text="Paste JSON profile or enter description:").pack(anchor=tk.W)
        
        text_input = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            height=10
        )
        text_input.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add name field
        name_frame = ttk.Frame(content_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Profile Name:").pack(side=tk.LEFT)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Add importance slider
        importance_frame = ttk.Frame(content_frame)
        importance_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(importance_frame, text="Importance:").pack(side=tk.LEFT)
        importance_var = tk.DoubleVar(value=0.7)  # Default moderate-high importance
        importance_scale = ttk.Scale(
            importance_frame,
            from_=0.0,
            to=1.0,
            variable=importance_var,
            orient=tk.HORIZONTAL
        )
        importance_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        importance_label = ttk.Label(importance_frame, text="0.7")
        importance_label.pack(side=tk.LEFT, padx=5)
        
        # Update label when slider changes
        def update_importance_label(*args):
            importance_label.config(text=f"{importance_var.get():.1f}")
        
        importance_var.trace_add("write", update_importance_label)
        
        # Create button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Function to handle file selection
        def select_file():
            filename = filedialog.askopenfilename(
                parent=dialog,
                title="Select Personality Profile",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if not filename:
                return
                
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Try to parse as JSON to validate
                try:
                    profile_data = json.loads(content)
                    
                    # Set name from file if available
                    if "name" in profile_data and not name_var.get():
                        name_var.set(profile_data["name"])
                    else:
                        # Use filename as fallback
                        base_name = os.path.basename(filename)
                        name_var.set(os.path.splitext(base_name)[0])
                except:
                    # Not valid JSON, just use filename
                    base_name = os.path.basename(filename)
                    name_var.set(os.path.splitext(base_name)[0])
                    
                # Set content
                text_input.delete(1.0, tk.END)
                text_input.insert(tk.END, content)
                
            except Exception as e:
                messagebox.showerror("Import Error", str(e), parent=dialog)
        
        # Function to handle import action
        def do_import():
            content = text_input.get(1.0, tk.END).strip()
            name = name_var.get().strip()
            
            if not content:
                messagebox.showerror("Import Error", "No content to import", parent=dialog)
                return
                
            if not name:
                messagebox.showerror("Import Error", "Please provide a name", parent=dialog)
                return
            
            # Check if it's valid JSON
            try:
                json.loads(content)
                is_json = True
            except:
                is_json = False
            
            # Prepare source name
            source = f"Personality Profile: {name}"
            
            # Prepare metadata
            metadata = {
                "type": "personality_profile",
                "name": name,
                "format": "json" if is_json else "text",
                "importance": importance_var.get(),
                "source": "personality_plugin"
            }
            
            # Set result
            result_data["content"] = content
            result_data["source"] = source
            result_data["metadata"] = metadata
            
            # Close dialog
            dialog.destroy()
        
        # Function to handle cancel
        def do_cancel():
            result_data.clear()  # Clear result to indicate cancellation
            dialog.destroy()
        
        # Add buttons
        ttk.Button(button_frame, text="Select File", command=select_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Import", command=do_import, style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=do_cancel).pack(side=tk.RIGHT, padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        # Return result or None if cancelled
        return result_data if result_data else None
        
    def _import_ai_persona(self, parent_window):
        """
        Import an AI persona template
        
        Args:
            parent_window: Parent window for dialogs
            
        Returns:
            Dictionary with content and source, or None if cancelled
        """
        # Similar to _import_personality_profile but with different UI and template options
        # For brevity, I'll implement a simpler version here
        
        # Show input dialog
        persona_name = tk.simpledialog.askstring(
            "Import AI Persona",
            "Enter name for the AI persona:",
            parent=parent_window
        )
        
        if not persona_name:
            return None
            
        # Show template selection dialog
        templates = {
            "Helpful Assistant": "A helpful, harmless, and honest AI assistant that provides accurate and useful information.",
            "Creative Writer": "A creative AI assistant focused on storytelling and creative writing with vivid descriptions.",
            "Technical Expert": "A technically proficient AI that provides detailed and accurate information about software, programming, and technology.",
            "Empathetic Counselor": "An empathetic AI focused on understanding human emotions and providing supportive guidance.",
            "Custom": "Create a custom AI persona description"
        }
        
        template_dialog = tk.Toplevel(parent_window)
        template_dialog.title("Select AI Persona Template")
        template_dialog.geometry("400x300")
        template_dialog.transient(parent_window)
        template_dialog.grab_set()
        
        template_var = tk.StringVar()
        selected_template = [None]  # Use list to store result from inner function
        
        # Create template listbox
        ttk.Label(template_dialog, text="Select a template:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        template_list = tk.Listbox(template_dialog, height=len(templates))
        template_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Add templates to listbox
        for template in templates.keys():
            template_list.insert(tk.END, template)
        
        # Add description label
        desc_var = tk.StringVar()
        ttk.Label(template_dialog, textvariable=desc_var, wraplength=380).pack(fill=tk.X, padx=10, pady=5)
        
        # Update description when selection changes
        def on_select(event):
            selection = template_list.curselection()
            if selection:
                template_name = template_list.get(selection[0])
                desc_var.set(templates[template_name])
        
        template_list.bind("<<ListboxSelect>>", on_select)
        
        # Button functions
        def on_ok():
            selection = template_list.curselection()
            if selection:
                selected_template[0] = template_list.get(selection[0])
                template_dialog.destroy()
                
        def on_cancel():
            template_dialog.destroy()
        
        # Add buttons
        button_frame = ttk.Frame(template_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
        
        # Wait for dialog
        template_dialog.wait_window()
        
        # Check if template selected
        template_name = selected_template[0]
        if not template_name:
            return None
        
        # If custom, get description
        content = ""
        if template_name == "Custom":
            custom_desc = tk.simpledialog.askstring(
                "Custom Persona",
                "Enter custom persona description:",
                parent=parent_window
            )
            
            if not custom_desc:
                return None
                
            content = f"AI Persona: {persona_name}\n\nDescription: {custom_desc}"
        else:
            # Use template
            content = f"AI Persona: {persona_name}\n\nTemplate: {template_name}\n\nDescription: {templates[template_name]}"
        
        # Return import data
        return {
            "content": content,
            "source": f"AI Persona: {persona_name}",
            "metadata": {
                "type": "ai_persona",
                "name": persona_name,
                "template": template_name,
                "importance": 0.8,  # High importance for personas
                "source": "personality_plugin"
            }
        }
        
    def _export_all_personalities(self, memory_system, parent_window):
        """
        Export all personalities from the plugin
        
        Args:
            memory_system: Memory system instance
            parent_window: Parent window for dialogs
            
        Returns:
            Status message
        """
        # Get file path
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Export All Personality Profiles"
        )
        
        if not filename:
            return None
            
        try:
            # Get available profiles
            profiles = {}
            for profile_name in self.plugin.get_available_profiles():
                profiles[profile_name] = self.plugin.get_profile(profile_name)
            
            # Add profiles to memory system first
            for name, profile in profiles.items():
                # Convert to JSON
                import json
                content = json.dumps(profile, indent=2)
                
                # Add to memory
                memory_system.add_text_to_index(
                    content,
                    f"Personality Profile: {name}",
                    {
                        "type": "personality_profile",
                        "name": name,
                        "format": "json",
                        "importance": 0.7,
                        "source": "personality_plugin",
                        "export_operation": "bulk_export"
                    }
                )
            
            # Save to file
            with open(filename, "w", encoding="utf-8") as f:
                import json
                json.dump(profiles, f, indent=2)
                
            return f"Exported {len(profiles)} personality profiles to {filename}"
            
        except Exception as e:
            raise Exception(f"Failed to export personalities: {e}")
        
    def _store_active_profile_in_memory(self):
        """Store the active personality profile in memory system"""
        # Get active profile
        active_profile = self.plugin.get_active_profile()
        active_name = self.plugin.get_active_profile_name()
        
        if not active_profile or not active_name:
            messagebox.showinfo(
                "Store Profile",
                "No active personality profile to store"
            )
            return
            
        try:
            # Access memory system through parent reference
            if not hasattr(self.plugin.core_system, "memory_system"):
                messagebox.showerror(
                    "Store Profile",
                    "Memory system not available"
                )
                return
                
            memory_system = self.plugin.core_system.memory_system
            
            # Convert profile to JSON
            import json
            content = json.dumps(active_profile, indent=2)
            
            # Add to memory
            success = memory_system.add_text_to_index(
                content,
                f"Personality Profile: {active_name}",
                {
                    "type": "personality_profile",
                    "name": active_name,
                    "format": "json",
                    "importance": 0.7,
                    "source": "personality_plugin"
                }
            )
            
            if success:
                messagebox.showinfo(
                    "Store Profile",
                    f"Successfully stored profile '{active_name}' in memory"
                )
            else:
                messagebox.showerror(
                    "Store Profile",
                    f"Failed to store profile in memory"
                )
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def _store_all_profiles_in_memory(self):
        """Store all personality profiles in memory system"""
        # Get all profiles
        profiles = {}
        for profile_name in self.plugin.get_available_profiles():
            profiles[profile_name] = self.plugin.get_profile(profile_name)
        
        if not profiles:
            messagebox.showinfo(
                "Store Profiles",
                "No personality profiles to store"
            )
            return
            
        try:
            # Access memory system through parent reference
            if not hasattr(self.plugin.core_system, "memory_system"):
                messagebox.showerror(
                    "Store Profiles",
                    "Memory system not available"
                )
                return
                
            memory_system = self.plugin.core_system.memory_system
            
            # Add each profile
            success_count = 0
            for name, profile in profiles.items():
                # Convert to JSON
                import json
                content = json.dumps(profile, indent=2)
                
                # Add to memory
                success = memory_system.add_text_to_index(
                    content,
                    f"Personality Profile: {name}",
                    {
                        "type": "personality_profile",
                        "name": name,
                        "format": "json",
                        "importance": 0.7,
                        "source": "personality_plugin"
                    }
                )
                
                if success:
                    success_count += 1
            
            if success_count > 0:
                messagebox.showinfo(
                    "Store Profiles",
                    f"Successfully stored {success_count} profiles in memory"
                )
            else:
                messagebox.showerror(
                    "Store Profiles",
                    f"Failed to store profiles in memory"
                )
                
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # In plugins/personality_plugin/__init__.py
    # Add this to the IrintaiPlugin class

    def get_model_extensions(self):
        """
        Get extensions for the model panel
        
        Returns:
            Dictionary of model extensions
        """
        return {
            "model_configs": {
                "*": self._personality_model_config  # Apply to all models
            },
            "model_actions": {
                "optimize_for_persona": self._optimize_model_for_persona,
                "create_persona_preset": self._create_persona_preset
            },
            "ui_extensions": [
                self._create_model_ui_extension()
            ]
        }
        
    def _create_model_ui_extension(self):
        """
        Create a UI extension for the model panel
        
        Returns:
            UI widget to be added to model panel
        """
        # Create frame for personality model integration
        extension_frame = ttk.Frame()
        
        # Add a label
        ttk.Label(
            extension_frame,
            text="Personality Model Integration",
            font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Create profile selection frame
        profile_frame = ttk.Frame(extension_frame)
        profile_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(profile_frame, text="Apply personality to model:").pack(side=tk.LEFT)
        
        # Get available profiles
        profiles = self.plugin.get_available_profiles()
        active_profile = self.plugin.get_active_profile_name() or "None"
        
        # Create dropdown
        self.model_profile_var = tk.StringVar(value=active_profile)
        profile_dropdown = ttk.Combobox(
            profile_frame,
            textvariable=self.model_profile_var,
            values=["None"] + sorted(profiles),
            state="readonly",
            width=20
        )
        profile_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Apply button
        ttk.Button(
            profile_frame,
            text="Apply to Model",
            command=self._apply_personality_to_model
        ).pack(side=tk.LEFT, padx=5)
        
        return extension_frame
        
    def _personality_model_config(self, model_name, base_config):
        """
        Apply personality settings to model configuration
        
        Args:
            model_name: Model name
            base_config: Base configuration
            
        Returns:
            Updated configuration
        """
        # Get active profile
        active_profile = self.plugin.get_active_profile()
        if not active_profile:
            return base_config
        
        # Create a copy of the configuration
        config = base_config.copy()
        
        # Check if personality is enabled for this model
        personality_enabled = self.plugin.get_config().get(f"model_personality_enabled.{model_name}", False)
        if not personality_enabled:
            return config
        
        # Get style modifiers
        style_modifiers = active_profile.get("style_modifiers", {})
        
        # Adjust model parameters based on personality
        if "parameters" not in config:
            config["parameters"] = {}
        
        # Map style modifiers to model parameters
        if "temperature" in config["parameters"]:
            # Adjust temperature based on creativity and formality
            creativity = style_modifiers.get("creativity", 0.5)
            formality = style_modifiers.get("formality", 0.5)
            
            # Higher creativity -> higher temperature, higher formality -> lower temperature
            temp_multiplier = 0.8 + (creativity * 0.4) - (formality * 0.2)
            config["parameters"]["temperature"] = config["parameters"]["temperature"] * temp_multiplier
            
        if "top_p" in config["parameters"]:
            # Adjust top_p based on creativity
            creativity = style_modifiers.get("creativity", 0.5)
            
            # Higher creativity -> higher top_p
            config["parameters"]["top_p"] = 0.7 + (creativity * 0.3)
        
        # Add system prompt if possible
        if active_profile.get("system_prompt"):
            config["system_prompt"] = active_profile["system_prompt"]
        
        return config
        
    def _optimize_model_for_persona(self, model_name, model_panel):
        """
        Optimize model configuration for the current personality
        
        Args:
            model_name: Model name
            model_panel: Reference to model panel
            
        Returns:
            Status message
        """
        # Get active profile
        active_profile = self.plugin.get_active_profile()
        active_name = self.plugin.get_active_profile_name()
        
        if not active_profile or not active_name:
            return "No active personality profile to optimize for"
        
        # Enable personality for this model
        self.plugin.set_config(f"model_personality_enabled.{model_name}", True)
        
        # Get base model config
        model_manager = model_panel.model_manager
        base_config = model_manager.get_model_config(model_name)
        
        # Apply personality optimizations
        optimized_config = self._personality_model_config(model_name, base_config)
        
        # Save optimized parameters
        if "parameters" in optimized_config:
            params = optimized_config["parameters"]
            param_str = ", ".join([f"{k}={v:.2f}" for k, v in params.items()])
            
            return f"Model {model_name} optimized for {active_name} persona\nParameters: {param_str}"
        else:
            return f"Model {model_name} optimized for {active_name} persona"
        
    def _create_persona_preset(self, model_name, model_panel):
        """
        Create a preset combining model and persona settings
        
        Args:
            model_name: Model name
            model_panel: Reference to model panel
            
        Returns:
            Status message
        """
        from tkinter import simpledialog
        
        # Get active profile
        active_profile = self.plugin.get_active_profile()
        active_name = self.plugin.get_active_profile_name()
        
        if not active_profile or not active_name:
            return "No active personality profile for preset creation"
        
        # Get preset name
        preset_name = simpledialog.askstring(
            "Create Persona Preset",
            f"Enter name for the {model_name}/{active_name} preset:",
            initialvalue=f"{model_name}-{active_name}"
        )
        
        if not preset_name:
            return None
        
        # Create preset by combining model and persona
        preset = {
            "name": preset_name,
            "model": model_name,
            "persona": active_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "parameters": {}
        }
        
        # Get base model config
        model_manager = model_panel.model_manager
        base_config = model_manager.get_model_config(model_name)
        
        # Apply personality optimizations
        optimized_config = self._personality_model_config(model_name, base_config)
        
        # Copy parameters
        if "parameters" in optimized_config:
            preset["parameters"] = optimized_config["parameters"]
        
        # Store the preset
        presets = self.plugin.get_config().get("model_presets", {})
        presets[preset_name] = preset
        self.plugin.set_config("model_presets", presets)
        
        return f"Created persona preset '{preset_name}'"
        
    def _apply_personality_to_model(self):
        """Apply selected personality to the current model"""
        from tkinter import messagebox
        
        # Get selected profile
        profile_name = self.model_profile_var.get()
        
        # Find the model panel (assume it's the parent's parent)
        model_panel = self._find_model_panel()
        if not model_panel:
            messagebox.showerror("Error", "Cannot access model panel")
            return
        
        # Get selected model
        selection = model_panel.model_tree.selection()
        if not selection:
            messagebox.showinfo("No Model Selected", "Please select a model first")
            return
        
        # Get model name
        item = selection[0]
        values = model_panel.model_tree.item(item, "values")
        model_name = values[0]
        
        # Enable or disable personality for this model
        if profile_name == "None":
            self.plugin.set_config(f"model_personality_enabled.{model_name}", False)
            messagebox.showinfo("Personality Disabled", f"Personality disabled for model {model_name}")
        else:
            # Set as active profile and enable for model
            self.plugin.set_active_profile(profile_name)
            self.plugin.set_config(f"model_personality_enabled.{model_name}", True)
            
            messagebox.showinfo(
                "Personality Applied", 
                f"Applied personality '{profile_name}' to model {model_name}"
            )
        
        # Refresh model info
        model_panel.on_model_selected()
        
    def _find_model_panel(self):
        """Find the model panel instance from our extensions"""
        # Check if we're directly in the model panel
        if hasattr(self, "frame") and hasattr(self, "model_tree"):
            return self
        
        # Otherwise look for model_panel in our structure
        parent_widget = None
        
        # Loop through our widget hierarchy
        current = self
        while hasattr(current, "master") or hasattr(current, "parent"):
            parent = getattr(current, "master", None) or getattr(current, "parent", None)
            if hasattr(parent, "model_tree") and hasattr(parent, "model_manager"):
                return parent
            current = parent
        
        return None