import os
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Any, List

from core.plugin_manager import PluginManager


class PluginManagerPanel:
    """
    Irintai Plugin Management Panel for GUI integration.

    Provides a visual interface to:
    - Load and list plugins
    - Activate or deactivate plugins
    - Reload plugins
    - Filter plugins by tag
    - View plugin metadata
    """

    def __init__(
        self,
        parent: ttk.Notebook,
        plugin_manager: PluginManager,
        logger: Optional[Callable[[str, str], None]] = None,
        core_app: Optional[Any] = None  
    ):
        self.core_app = core_app
        self.parent = parent
        self.plugin_manager = plugin_manager
        self.log = logger or print
        self.plugin_tags: List[str] = []

        self.frame = ttk.Frame(parent)
        self.parent.add(self.frame, text="Plugins")

        self._build_ui()
        self.refresh_plugin_list()

    def _build_ui(self) -> None:
        self.plugin_listbox = tk.Listbox(self.frame, width=30, height=20)
        self.plugin_listbox.grid(row=0, column=0, rowspan=6, padx=5, pady=5, sticky="ns")
        self.plugin_listbox.bind("<<ListboxSelect>>", self.display_plugin_details)

        self.details_frame = ttk.LabelFrame(self.frame, text="Plugin Details")
        self.details_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.plugin_info = tk.Text(self.details_frame, wrap="word", state="disabled")
        self.plugin_info.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        ttk.Button(self.frame, text="Load Plugins", command=self.load_plugins).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(self.frame, text="Activate Plugin", command=self.activate_selected_plugin).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(self.frame, text="Deactivate Plugin", command=self.deactivate_selected_plugin).grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(self.frame, text="Reload Plugin", command=self.reload_selected_plugin).grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(self.frame, text="Open Plugin Folder", command=self.open_plugin_folder).grid(row=5, column=1, sticky="ew", padx=5, pady=2)

        self.filter_label = ttk.Label(self.frame, text="Filter by Tag:")
        self.filter_label.grid(row=6, column=0, padx=5, pady=2, sticky="w")
        self.filter_entry = ttk.Entry(self.frame)
        self.filter_entry.grid(row=6, column=1, padx=5, pady=2, sticky="ew")
        self.filter_entry.bind("<KeyRelease>", self.apply_filter)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

    def load_plugins(self) -> None:
        self.plugin_manager.load_plugins()
        self.refresh_plugin_list()

    def refresh_plugin_list(self, filter_tag: Optional[str] = None) -> None:
        self.plugin_listbox.delete(0, tk.END)
        for plugin_name, data in self.plugin_manager.plugins.items():
            instance = data.get("instance")
            tags = getattr(instance, "tags", [])
            if filter_tag and filter_tag.lower() not in [t.lower() for t in tags]:
                continue
            status = data.get("status")  # Get status directly from the plugin data
            friendly_name = getattr(instance, "friendly_name", plugin_name.replace("_", " ").title())
            label = friendly_name
            self.plugin_listbox.insert(tk.END, label) 

    def get_selected_plugin_name(self) -> Optional[str]:
        selection = self.plugin_listbox.curselection()
        if not selection:
            return None
        full_label = self.plugin_listbox.get(selection[0])
        return full_label.split(" [")[0]

    def display_plugin_details(self, event=None) -> None:
        plugin_name = self.get_selected_plugin_name()
        if not plugin_name:
            return

        plugin_entry = self.plugin_manager.plugins.get(plugin_name)
        instance = plugin_entry.get("instance")
        status = plugin_entry.get("status")

        info_lines = [f"Plugin Name: {plugin_name}", f"Status: {status}"]

        if instance:
            description = getattr(instance, "description", "No description provided.")
            version = getattr(instance, "version", "Unknown")
            tags = getattr(instance, "tags", [])
            info_lines.append(f"Version: {version}")
            if tags:
                info_lines.append(f"Tags: {', '.join(tags)}")
            info_lines.append("")
            info_lines.append(f"Description: {description}")

        self.plugin_info.config(state="normal")
        self.plugin_info.delete("1.0", tk.END)
        self.plugin_info.insert(tk.END, "\n".join(info_lines))
        self.plugin_info.config(state="disabled")

    def activate_selected_plugin(self) -> None:
        plugin_name = self.get_selected_plugin_name()
        if plugin_name:
            success = self.plugin_manager.activate_plugin(plugin_name)
            if success:
                self.log(f"Plugin '{plugin_name}' activated.", "INFO")
                self.refresh_plugin_list()
                self.select_plugin_by_name(plugin_name)

    def deactivate_selected_plugin(self) -> None:
        plugin_name = self.get_selected_plugin_name()
        if plugin_name:
            success = self.plugin_manager.deactivate_plugin(plugin_name)
            if success:
                self.log(f"Plugin '{plugin_name}' deactivated.", "INFO")
                self.refresh_plugin_list()
                self.select_plugin_by_name(plugin_name)

    def reload_selected_plugin(self) -> None:
        plugin_name = self.get_selected_plugin_name()
        if plugin_name:
            self.plugin_manager.deactivate_plugin(plugin_name)
            self.plugin_manager.load_plugins()
            self.plugin_manager.activate_plugin(plugin_name)
            self.log(f"Plugin '{plugin_name}' reloaded.", "INFO")
            self.refresh_plugin_list()
            self.select_plugin_by_name(plugin_name)

    def select_plugin_by_name(self, plugin_name: str) -> None:
        for index in range(self.plugin_listbox.size()):
            label = self.plugin_listbox.get(index)
            if label.startswith(plugin_name + " "):
                self.plugin_listbox.selection_clear(0, tk.END)
                self.plugin_listbox.selection_set(index)
                self.plugin_listbox.activate(index)
                self.display_plugin_details()
                break

    def apply_filter(self, event=None) -> None:
        tag = self.filter_entry.get().strip()
        self.refresh_plugin_list(filter_tag=tag)

    def open_plugin_folder(self) -> None:
        try:
            path = os.path.abspath(self.plugin_manager.plugin_dir)
            os.startfile(path) if os.name == "nt" else os.system(f"open '{path}'")
        except Exception as e:
            self.log(f"[Folder Open Error] {e}", "ERROR")
