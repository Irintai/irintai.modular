import os
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Any

from core.plugin_manager import PluginManager


class PluginManagerPanel:
    """
    Irintai Plugin Management Panel for GUI integration.

    Provides a visual interface to:
    - Load and list plugins
    - Activate or deactivate plugins
    - View plugin metadata
    - Promote low-friction dev with instant feedback
    """

    def __init__(
        self,
        parent: ttk.Notebook,
        plugin_manager: PluginManager,
        logger: Optional[Callable[[str, str], None]] = None
    ):
        """
        Initialize the plugin panel

        Args:
            parent: ttk.Notebook instance (main UI tab container)
            plugin_manager: PluginManager instance
            logger: Optional logging function
        """
        self.parent = parent
        self.plugin_manager = plugin_manager
        self.log = logger or print

        self.frame = ttk.Frame(parent)
        self.parent.add(self.frame, text="Plugins")

        self._build_ui()
        self.refresh_plugin_list()

    def _build_ui(self) -> None:
        """
        Construct all UI widgets for the plugin panel
        """
        # Plugin List
        self.plugin_listbox = tk.Listbox(self.frame, width=30, height=20)
        self.plugin_listbox.grid(row=0, column=0, rowspan=5, padx=5, pady=5, sticky="ns")
        self.plugin_listbox.bind("<<ListboxSelect>>", self.display_plugin_details)

        # Plugin Info Frame
        self.details_frame = ttk.LabelFrame(self.frame, text="Plugin Details")
        self.details_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.plugin_info = tk.Text(self.details_frame, height=12, width=50, wrap="word", state="disabled")
        self.plugin_info.pack(padx=5, pady=5)

        # Buttons
        ttk.Button(self.frame, text="Load Plugins", command=self.load_plugins).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(self.frame, text="Activate Plugin", command=self.activate_selected_plugin).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(self.frame, text="Deactivate Plugin", command=self.deactivate_selected_plugin).grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(self.frame, text="Open Plugin Folder", command=self.open_plugin_folder).grid(row=4, column=1, sticky="ew", padx=5, pady=2)

        # Resize rules
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

    def load_plugins(self) -> None:
        """
        Trigger plugin loading from disk
        """
        self.plugin_manager.load_plugins()
        self.refresh_plugin_list()

    def refresh_plugin_list(self) -> None:
        """
        Populate listbox with available plugins
        """
        self.plugin_listbox.delete(0, tk.END)
        for plugin_name in self.plugin_manager.plugins.keys():
            status = self.plugin_manager.get_plugin_status(plugin_name)
            label = f"{plugin_name} [{status}]"
            self.plugin_listbox.insert(tk.END, label)

    def get_selected_plugin_name(self) -> Optional[str]:
        """
        Extract the raw plugin name from selected listbox item
        """
        selection = self.plugin_listbox.curselection()
        if not selection:
            return None
        full_label = self.plugin_listbox.get(selection[0])
        return full_label.split(" [")[0]

    def display_plugin_details(self, event=None) -> None:
        """
        Show selected plugin's metadata in text box
        """
        plugin_name = self.get_selected_plugin_name()
        if not plugin_name:
            return

        plugin_entry = self.plugin_manager.plugins.get(plugin_name)
        instance = plugin_entry.get("instance")
        status = plugin_entry.get("status")

        info_lines = [f"Plugin Name: {plugin_name}", f"Status: {status}"]

        if instance:
            # Attempt to pull additional metadata
            description = getattr(instance, "description", "No description provided.")
            version = getattr(instance, "version", "Unknown")
            info_lines.append(f"Version: {version}")
            info_lines.append("")
            info_lines.append(f"Description:{description}")

        self.plugin_info.config(state="normal")
        self.plugin_info.delete("1.0", tk.END)
        self.plugin_info.insert(tk.END, "\n".join(info_lines))
        self.plugin_info.config(state="disabled")

    def activate_selected_plugin(self) -> None:
        """
        Activate the selected plugin
        """
        plugin_name = self.get_selected_plugin_name()
        if plugin_name:
            success = self.plugin_manager.activate_plugin(plugin_name)
            if success:
                self.log(f"Plugin '{plugin_name}' activated.", "INFO")
                self.refresh_plugin_list()
                self.display_plugin_details()

    def deactivate_selected_plugin(self) -> None:
        """
        Deactivate the selected plugin
        """
        plugin_name = self.get_selected_plugin_name()
        if plugin_name:
            success = self.plugin_manager.deactivate_plugin(plugin_name)
            if success:
                self.log(f"Plugin '{plugin_name}' deactivated.", "INFO")
                self.refresh_plugin_list()
                self.display_plugin_details()

    def open_plugin_folder(self) -> None:
        """
        Open the plugins directory using the OS file explorer
        """
        try:
            path = os.path.abspath(self.plugin_manager.plugin_dir)
            os.startfile(path) if os.name == "nt" else os.system(f"open '{path}'")
        except Exception as e:
            self.log(f"[Folder Open Error] {e}", "ERROR")
