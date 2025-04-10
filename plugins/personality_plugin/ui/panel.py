# UI hooks for personality plugin panel
"""
UI Components for the Personality Plugin
"""
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Any, Optional

# Import the core plugin
from ..core.personality_plugin import PersonalityPlugin

class Panel:
    """UI panel for the Personality Plugin"""
    
    def __init__(self, parent: tk.Widget, plugin: PersonalityPlugin):
        """
        Initialize the UI panel
        
        Args:
            parent: Parent widget
            plugin: Reference to the core plugin instance
        """
        self.parent = parent
        self.plugin = plugin
        
        # UI state
        self.ui_panel = None
        self.profiles_listbox = None
        self.details_content = None
        self.detail_fields = {}
        self.style_sliders = {}
        self.special_rules_vars = {}
        
        # Create panel
        self.create_panel()
    
    def create_panel(self) -> ttk.Frame:
        """
        Create the UI panel
        
        Returns:
            UI panel frame
        """
        # Create main frame
        self.ui_panel = ttk.Frame(self.parent)
        
        # Create title and description
        title_frame = ttk.Frame(self.ui_panel)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            title_frame, 
            text="Personality Profiles",
            font=("Helvetica", 12, "bold")
        ).pack(side=tk.LEFT)

    def activate_ui(plugin_instance, parent_container):
        """
        Manually activate the plugin UI
        
        Args:
            plugin_instance: The plugin instance
            parent_container: Parent widget to attach UI to
        
        Returns:
            The UI panel
        """
        panel = plugin_instance.get_ui_panel(parent_container)
        panel.pack(fill=tk.BOTH, expand=True)
        return panel

    def get_ui_panel(self, parent: tk.Widget) -> ttk.Frame:
        """
        Create a UI panel for this plugin
        
        Args:
            parent: Parent widget
            
        Returns:
            UI panel frame
        """
        # Create main frame
        self.ui_panel = ttk.Frame(parent)
        
        # Create title and description
        title_frame = ttk.Frame(self.ui_panel)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            title_frame, 
            text="Personality Profiles",
            font=("Helvetica", 12, "bold")
        ).pack(side=tk.LEFT)
        
        # Create main content section
        content_frame = ttk.Frame(self.ui_panel)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Split into left (profiles list) and right (profile details) panes
        paned_window = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Profiles list on the left
        profiles_frame = ttk.LabelFrame(paned_window, text="Available Profiles")
        paned_window.add(profiles_frame, weight=1)
        
        # Create profiles listbox with scrollbar
        profiles_frame_inner = ttk.Frame(profiles_frame)
        profiles_frame_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.profiles_listbox = tk.Listbox(
            profiles_frame_inner,
            height=10,
            exportselection=0
        )
        self.profiles_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        profiles_scrollbar = ttk.Scrollbar(
            profiles_frame_inner,
            orient=tk.VERTICAL,
            command=self.profiles_listbox.yview
        )
        profiles_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.profiles_listbox.config(yscrollcommand=profiles_scrollbar.set)
        
        # Profile controls
        profiles_controls = ttk.Frame(profiles_frame)
        profiles_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            profiles_controls,
            text="Activate",
            command=self._ui_activate_profile
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            profiles_controls,
            text="New",
            command=self._ui_create_profile
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            profiles_controls,
            text="Edit",
            command=self._ui_edit_profile
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            profiles_controls,
            text="Duplicate",
            command=self._ui_duplicate_profile
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            profiles_controls,
            text="Delete",
            command=self._ui_delete_profile
        ).pack(side=tk.LEFT, padx=2)
        
        # Profile details on the right
        details_frame = ttk.LabelFrame(paned_window, text="Profile Details")
        paned_window.add(details_frame, weight=2)
        
        # Create scrollable details view
        details_canvas = tk.Canvas(details_frame)
        details_scrollbar = ttk.Scrollbar(
            details_frame,
            orient=tk.VERTICAL,
            command=details_canvas.yview
        )
        details_canvas.configure(yscrollcommand=details_scrollbar.set)
        
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        details_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.details_content = ttk.Frame(details_canvas)
        details_canvas.create_window((0, 0), window=self.details_content, anchor=tk.NW)
        
        # Configure canvas to resize with content
        def _configure_details_canvas(event):
            details_canvas.configure(scrollregion=details_canvas.bbox("all"))
        
        self.details_content.bind("<Configure>", _configure_details_canvas)
        
        # Create profile detail widgets
        self._create_profile_details_widgets()
        
        # Import/Export buttons
        export_frame = ttk.Frame(self.ui_panel)
        export_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            export_frame,
            text="Import Profile",
            command=self._ui_import_profile
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            export_frame,
            text="Export Profile",
            command=self._ui_export_profile
        ).pack(side=tk.LEFT, padx=5)
        
        # Bind profile selection event
        self.profiles_listbox.bind("<<ListboxSelect>>", self._ui_on_profile_selected)
        
        # Populate the profiles list
        self._ui_refresh_profiles_list()
        
        return self.ui_panel

    def _create_profile_details_widgets(self) -> None:
        """
        Create widgets for displaying profile details
        """
        # Clear existing widgets
        for widget in self.details_content.winfo_children():
            widget.destroy()
        
        # Create detail fields
        self.detail_fields = {}
        
        fields = [
            ("name", "Name", tk.StringVar()),
            ("description", "Description", tk.StringVar()),
            ("tags", "Tags", tk.StringVar()),
            ("author", "Author", tk.StringVar()),
            ("version", "Version", tk.StringVar()),
            ("created", "Created", tk.StringVar()),
            ("prefix", "Prefix", tk.StringVar()),
            ("suffix", "Suffix", tk.StringVar())
        ]
        
        for field_id, label_text, variable in fields:
            frame = ttk.Frame(self.details_content)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(
                frame,
                text=f"{label_text}:",
                width=10,
                anchor=tk.W
            ).pack(side=tk.LEFT)
            
            if field_id in ["description", "prefix", "suffix"]:
                entry = ttk.Entry(
                    frame,
                    textvariable=variable,
                    width=40
                )
            else:
                entry = ttk.Entry(
                    frame,
                    textvariable=variable,
                    width=20
                )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            self.detail_fields[field_id] = variable
        
        # Style Modifiers section
        ttk.Label(
            self.details_content,
            text="Style Modifiers",
            font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        self.style_sliders = {}
        
        slider_labels = {
            "formality": "Casual vs. Formal",
            "creativity": "Precise vs. Creative",
            "complexity": "Simple vs. Complex",
            "empathy": "Analytical vs. Empathetic",
            "directness": "Indirect vs. Direct"
        }
        
        for slider_id, label_text in slider_labels.items():
            frame = ttk.Frame(self.details_content)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(
                frame,
                text=f"{label_text}:",
                width=20,
                anchor=tk.W
            ).pack(side=tk.LEFT)
            
            var = tk.DoubleVar(value=0.5)
            slider = ttk.Scale(
                frame,
                from_=0.0,
                to=1.0,
                orient=tk.HORIZONTAL,
                variable=var,
                length=200
            )
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            value_label = ttk.Label(
                frame,
                width=5,
                text="0.5"
            )
            value_label.pack(side=tk.LEFT)
            
            # Update value label when slider changes
            def _update_value_label(event, label=value_label, var=var):
                label.config(text=f"{var.get():.1f}")
            
            slider.bind("<Motion>", _update_value_label)
            
            self.style_sliders[slider_id] = var
        
        # Special rules for Altruxan
        self.special_rules_vars = {}
        
        ttk.Label(
            self.details_content,
            text="Special Rules",
            font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        rules = [
            ("honor_trauma", "Honor Trauma"),
            ("recursive_framing", "Use Recursive Framing"),
            ("use_symbolic_language", "Use Symbolic Language")
        ]
        
        rules_frame = ttk.Frame(self.details_content)
        rules_frame.pack(fill=tk.X, padx=5, pady=2)
        
        for i, (rule_id, label_text) in enumerate(rules):
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(
                rules_frame,
                text=label_text,
                variable=var
            )
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2)
            
            self.special_rules_vars[rule_id] = var
    
    def _ui_refresh_profiles_list(self) -> None:
        """
        Refresh the profiles listbox
        """
        # Clear existing items
        self.profiles_listbox.delete(0, tk.END)
        
        # Get profiles
        profiles = self._config.get("profiles", {})
        active_profile = self._state.get("active_profile")
        
        # Add to listbox
        for i, name in enumerate(sorted(profiles.keys())):
            display_name = name
            if name == active_profile:
                display_name = f"* {name} (Active)"
            
            self.profiles_listbox.insert(tk.END, display_name)
            
            # Select active profile
            if name == active_profile:
                self.profiles_listbox.selection_set(i)
                self.profiles_listbox.see(i)
    
    def _ui_on_profile_selected(self, event) -> None:
        """
        Handle profile selection in the listbox
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            return
        
        # Get profile name (remove active marker if present)
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Get profile data
        profiles = self._config.get("profiles", {})
        if profile_name not in profiles:
            return
        
        profile = profiles[profile_name]
        
        # Update detail fields
        for field_id, var in self.detail_fields.items():
            value = profile.get(field_id, "")
            if field_id == "tags" and isinstance(value, list):
                value = ", ".join(value)
            var.set(value)
        
        # Update style sliders
        style_modifiers = profile.get("style_modifiers", {})
        for slider_id, var in self.style_sliders.items():
            var.set(style_modifiers.get(slider_id, 0.5))
        
        # Update special rules
        special_rules = profile.get("special_rules", {})
        for rule_id, var in self.special_rules_vars.items():
            var.set(special_rules.get(rule_id, False))
    
    def _ui_activate_profile(self) -> None:
        """
        Activate the selected profile
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a profile to activate")
            return
        
        # Get profile name (remove active marker if present)
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Set as active profile
        success = self.set_active_profile(profile_name)
        
        if success:
            messagebox.showinfo("Profile Activated", f"Profile '{profile_name}' is now active")
            self._ui_refresh_profiles_list()
        else:
            messagebox.showerror("Activation Failed", f"Failed to activate profile '{profile_name}'")
    
    def _ui_create_profile(self) -> None:
        """
        Create a new personality profile
        """
        # Create a dialog for new profile
        dialog = tk.Toplevel(self.ui_panel)
        dialog.title("Create New Profile")
        dialog.transient(self.ui_panel)
        dialog.grab_set()
        
        # Create form
        form_frame = ttk.Frame(dialog, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Profile Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=name_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=desc_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Tags (comma separated):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        tags_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=tags_var, width=30).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Author:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        author_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=author_var, width=30).grid(row=3, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        def on_create():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Invalid Name", "Profile name cannot be empty")
                return
            
            # Create profile data
            profile_data = {
                "name": name,
                "description": desc_var.get().strip(),
                "tags": [tag.strip() for tag in tags_var.get().split(",") if tag.strip()],
                "author": author_var.get().strip() or "User",
                "version": "1.0.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prefix": "",
                "suffix": "",
                "style_modifiers": {
                    "formality": 0.5,
                    "creativity": 0.5,
                    "complexity": 0.5,
                    "empathy": 0.5,
                    "directness": 0.5
                },
                "formatting": {
                    "emphasize_key_points": False,
                    "use_markdown": True,
                    "paragraph_structure": "standard"
                }
            }
            
            # Create the profile
            success = self.create_profile(profile_data)
            
            if success:
                messagebox.showinfo("Profile Created", f"Profile '{name}' created successfully")
                dialog.destroy()
                self._ui_refresh_profiles_list()
            else:
                messagebox.showerror("Creation Failed", f"Failed to create profile '{name}'")
        
        ttk.Button(button_frame, text="Create", command=on_create).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _ui_edit_profile(self) -> None:
        """
        Edit the selected profile
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a profile to edit")
            return
        
        # Get profile name (remove active marker if present)
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Get profile data
        profiles = self._config.get("profiles", {})
        if profile_name not in profiles:
            messagebox.showerror("Profile Not Found", f"Profile '{profile_name}' not found")
            return
        
        profile = profiles[profile_name]
        
        # Create dialog for editing
        dialog = tk.Toplevel(self.ui_panel)
        dialog.title(f"Edit Profile: {profile_name}")
        dialog.transient(self.ui_panel)
        dialog.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic Info tab
        basic_frame = ttk.Frame(notebook, padding=10)
        notebook.add(basic_frame, text="Basic Info")
        
        # Add basic fields
        basic_vars = {}
        
        fields = [
            ("description", "Description"),
            ("tags", "Tags (comma separated)"),
            ("author", "Author"),
            ("prefix", "Prefix"),
            ("suffix", "Suffix")
        ]
        
        for i, (field_id, label_text) in enumerate(fields):
            ttk.Label(basic_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            
            value = profile.get(field_id, "")
            if field_id == "tags" and isinstance(value, list):
                value = ", ".join(value)
                
            var = tk.StringVar(value=value)
            basic_vars[field_id] = var
            
            ttk.Entry(
                basic_frame, 
                textvariable=var, 
                width=40
            ).grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Style Modifiers tab
        style_frame = ttk.Frame(notebook, padding=10)
        notebook.add(style_frame, text="Style Modifiers")
        
        style_vars = {}
        
        slider_labels = {
            "formality": "Casual vs. Formal",
            "creativity": "Precise vs. Creative",
            "complexity": "Simple vs. Complex",
            "empathy": "Analytical vs. Empathetic",
            "directness": "Indirect vs. Direct"
        }
        
        style_modifiers = profile.get("style_modifiers", {})
        
        for i, (slider_id, label_text) in enumerate(slider_labels.items()):
            ttk.Label(style_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            
            var = tk.DoubleVar(value=style_modifiers.get(slider_id, 0.5))
            style_vars[slider_id] = var
            
            slider = ttk.Scale(
                style_frame,
                from_=0.0,
                to=1.0,
                orient=tk.HORIZONTAL,
                variable=var,
                length=200
            )
            slider.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
            
            value_label = ttk.Label(
                style_frame,
                width=5,
                text=f"{var.get():.1f}"
            )
            value_label.grid(row=i, column=2, padx=5, pady=5)
            
            # Update value label when slider changes
            def _update_label(event, label=value_label, var=var):
                label.config(text=f"{var.get():.1f}")
            
            slider.bind("<Motion>", _update_label)
        
        # Special Rules tab
        rules_frame = ttk.Frame(notebook, padding=10)
        notebook.add(rules_frame, text="Special Rules")
        
        rule_vars = {}
        
        rules = [
            ("honor_trauma", "Honor Trauma"),
            ("recursive_framing", "Use Recursive Framing"),
            ("use_symbolic_language", "Use Symbolic Language")
        ]
        
        special_rules = profile.get("special_rules", {})
        
        for i, (rule_id, label_text) in enumerate(rules):
            var = tk.BooleanVar(value=special_rules.get(rule_id, False))
            rule_vars[rule_id] = var
            
            ttk.Checkbutton(
                rules_frame,
                text=label_text,
                variable=var
            ).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        def on_save():
            # Collect updated profile data
            profile_updates = {}
            
            # Basic info
            for field_id, var in basic_vars.items():
                value = var.get().strip()
                if field_id == "tags":
                    value = [tag.strip() for tag in value.split(",") if tag.strip()]
                profile_updates[field_id] = value
            
            # Style modifiers
            style_modifiers = {}
            for slider_id, var in style_vars.items():
                style_modifiers[slider_id] = round(var.get(), 1)
            profile_updates["style_modifiers"] = style_modifiers
            
            # Special rules
            special_rules = {}
            for rule_id, var in rule_vars.items():
                special_rules[rule_id] = var.get()
            profile_updates["special_rules"] = special_rules
            
            # Add modification timestamp
            profile_updates["modified"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Update the profile
            success = self.update_profile(profile_name, profile_updates)
            
            if success:
                messagebox.showinfo("Profile Updated", f"Profile '{profile_name}' updated successfully")
                dialog.destroy()
                self._ui_refresh_profiles_list()
                
                # Refresh details if this is the currently selected profile
                selection = self.profiles_listbox.curselection()
                if selection:
                    self._ui_on_profile_selected(None)
            else:
                messagebox.showerror("Update Failed", f"Failed to update profile '{profile_name}'")
        
        ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Configure grid columns
        basic_frame.columnconfigure(1, weight=1)
        style_frame.columnconfigure(1, weight=1)
        
        # Center dialog
        dialog.update_idletasks()
        dialog.geometry(f"500x400+{dialog.winfo_screenwidth()//2-250}+{dialog.winfo_screenheight()//2-200}")
    
    def _ui_duplicate_profile(self) -> None:
        """
        Duplicate the selected profile
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a profile to duplicate")
            return
        
        # Get profile name (remove active marker if present)
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Show input dialog for new name
        new_name = tk.simpledialog.askstring(
            "Duplicate Profile",
            f"Enter a name for the duplicate of '{profile_name}':",
            parent=self.ui_panel
        )
        
        if not new_name:
            return
        
        # Duplicate the profile
        success = self.duplicate_profile(profile_name, new_name)
        
        if success:
            messagebox.showinfo("Profile Duplicated", f"Profile '{profile_name}' duplicated to '{new_name}'")
            self._ui_refresh_profiles_list()
        else:
            messagebox.showerror("Duplication Failed", f"Failed to duplicate profile '{profile_name}'")
    
    def _ui_delete_profile(self) -> None:
        """
        Delete the selected profile
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a profile to delete")
            return
        
        # Get profile name (remove active marker if present)
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the profile '{profile_name}'?",
            icon=messagebox.WARNING
        )
        
        if not confirm:
            return
        
        # Delete the profile
        success = self.delete_profile(profile_name)
        
        if success:
            messagebox.showinfo("Profile Deleted", f"Profile '{profile_name}' deleted successfully")
            self._ui_refresh_profiles_list()
        else:
            messagebox.showerror("Deletion Failed", f"Failed to delete profile '{profile_name}'")
    
    def _ui_import_profile(self) -> None:
        """
        Import a profile from JSON
        """
        # Show dialog for JSON input
        dialog = tk.Toplevel(self.ui_panel)
        dialog.title("Import Profile")
        dialog.transient(self.ui_panel)
        dialog.grab_set()
        
        # Create text area for JSON
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="Paste profile JSON:",
            font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W)
        
        json_text = scrolledtext.ScrolledText(
            frame,
            width=60,
            height=20,
            wrap=tk.WORD
        )
        json_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        def on_import():
            json_str = json_text.get("1.0", tk.END).strip()
            if not json_str:
                messagebox.showwarning("Empty JSON", "Please paste profile JSON")
                return
            
            # Import the profile
            success = self.import_profile(json_str)
            
            if success:
                messagebox.showinfo("Profile Imported", "Profile imported successfully")
                dialog.destroy()
                self._ui_refresh_profiles_list()
            else:
                messagebox.showerror("Import Failed", "Failed to import profile")
        
        ttk.Button(button_frame, text="Import", command=on_import).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        dialog.geometry(f"600x500+{dialog.winfo_screenwidth()//2-300}+{dialog.winfo_screenheight()//2-250}")
    
    def _ui_export_profile(self) -> None:
        """
        Export the selected profile to JSON
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a profile to export")
            return
        
        # Get profile name (remove active marker if present)
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Export the profile
        json_str = self.export_profile(profile_name)
        
        if json_str:
            # Show dialog with JSON
            dialog = tk.Toplevel(self.ui_panel)
            dialog.title(f"Export Profile: {profile_name}")
            dialog.transient(self.ui_panel)
            dialog.grab_set()
            
            frame = ttk.Frame(dialog, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(
                frame,
                text=f"Profile JSON for '{profile_name}':",
                font=("Helvetica", 10, "bold")
            ).pack(anchor=tk.W)
            
            json_text = scrolledtext.ScrolledText(
                frame,
                width=60,
                height=20,
                wrap=tk.WORD
            )
            json_text.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # Insert JSON
            json_text.insert("1.0", json_str)
            
            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, pady=10)
            
            def copy_to_clipboard():
                dialog.clipboard_clear()
                dialog.clipboard_append(json_str)
                messagebox.showinfo("Copied", "Profile JSON copied to clipboard")
            
            ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
            # Center dialog
            dialog.update_idletasks()
            dialog.geometry(f"600x500+{dialog.winfo_screenwidth()//2-300}+{dialog.winfo_screenheight()//2-250}")
        else:
            messagebox.showerror("Export Failed", f"Failed to export profile '{profile_name}'")
