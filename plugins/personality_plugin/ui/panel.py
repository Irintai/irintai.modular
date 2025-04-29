# UI hooks for personality plugin panel
"""
UI Components for the Personality Plugin
"""
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Any, Optional

# Import the core plugin
from plugins.personality_plugin.core.personality_plugin import PersonalityPlugin

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
        
        # Populate the profiles list
        self._ui_refresh_profiles_list()
        
        return self.ui_panel

    def _create_profile_details_widgets(self):
        """
        Create widgets for displaying profile details
        """
        # Create frames for different sections
        basic_info_frame = ttk.LabelFrame(self.details_content, text="Basic Information")
        basic_info_frame.pack(fill=tk.X, padx=5, pady=5, anchor=tk.N)
        
        style_frame = ttk.LabelFrame(self.details_content, text="Style Modifiers")
        style_frame.pack(fill=tk.X, padx=5, pady=5, anchor=tk.N)
        
        formatting_frame = ttk.LabelFrame(self.details_content, text="Formatting Options")
        formatting_frame.pack(fill=tk.X, padx=5, pady=5, anchor=tk.N)
        
        # Basic information fields
        basic_fields = [
            ("name", "Name", 30),
            ("description", "Description", 50),
            ("tags", "Tags", 30),
            ("author", "Author", 20),
            ("version", "Version", 10),
        ]
        
        for i, (field_id, label_text, width) in enumerate(basic_fields):
            field_frame = ttk.Frame(basic_info_frame)
            field_frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(field_frame, text=f"{label_text}:", width=10).pack(side=tk.LEFT)
            
            # Use Entry for most fields, Text for description
            if field_id == "description":
                var = tk.StringVar()
                entry = ttk.Entry(field_frame, width=width, textvariable=var)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.detail_fields[field_id] = var
            else:
                var = tk.StringVar()
                entry = ttk.Entry(field_frame, width=width, textvariable=var)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.detail_fields[field_id] = var
        
        # Prefix/suffix fields
        adv_fields = [
            ("prefix", "Prefix:", 50),
            ("suffix", "Suffix:", 50),
        ]
        
        for field_id, label_text, width in adv_fields:
            field_frame = ttk.Frame(basic_info_frame)
            field_frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(field_frame, text=label_text, width=10).pack(side=tk.LEFT)
            
            var = tk.StringVar()
            entry = ttk.Entry(field_frame, width=width, textvariable=var)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.detail_fields[field_id] = var
        
        # Style modifier sliders
        style_grid = ttk.Frame(style_frame)
        style_grid.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        style_modifiers = [
            ("formality", "Formal", "Casual"),
            ("creativity", "Creative", "Factual"),
            ("complexity", "Complex", "Simple"),
            ("empathy", "Empathetic", "Objective"),
            ("directness", "Direct", "Diplomatic"),
            ("humor", "Humorous", "Serious"),
            ("enthusiasm", "Enthusiastic", "Reserved"),
            ("conciseness", "Concise", "Detailed")
        ]
        
        # Create grid layout
        for i, (mod_id, left_label, right_label) in enumerate(style_modifiers):
            row = i // 2
            col = (i % 2) * 3
            
            # Left label
            ttk.Label(style_grid, text=left_label).grid(row=row, column=col, padx=5, pady=2, sticky=tk.E)
            
            # Slider
            var = tk.DoubleVar(value=0.5)
            slider = ttk.Scale(
                style_grid,
                from_=0.0,
                to=1.0,
                orient=tk.HORIZONTAL,
                length=100,
                variable=var
            )
            slider.grid(row=row, column=col+1, padx=5, pady=2)
            self.style_sliders[mod_id] = var
            
            # Right label
            ttk.Label(style_grid, text=right_label).grid(row=row, column=col+2, padx=5, pady=2, sticky=tk.W)
        
        # Formatting options
        formatting_options = [
            ("emphasize_key_points", "Emphasize key points"),
            ("use_markdown", "Use Markdown formatting"),
        ]
        
        for i, (option_id, label) in enumerate(formatting_options):
            var = tk.BooleanVar(value=False)
            checkbox = ttk.Checkbutton(
                formatting_frame,
                text=label,
                variable=var
            )
            checkbox.pack(anchor=tk.W, padx=5, pady=2)
            self.special_rules_vars[option_id] = var
        
        # Paragraph structure option
        para_frame = ttk.Frame(formatting_frame)
        para_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(para_frame, text="Paragraph structure:").pack(side=tk.LEFT, padx=5)
        
        para_var = tk.StringVar(value="standard")
        para_combo = ttk.Combobox(
            para_frame,
            textvariable=para_var,
            values=["standard", "concise", "detailed", "academic"]
        )
        para_combo.pack(side=tk.LEFT, padx=5)
        self.special_rules_vars["paragraph_structure"] = para_var
        
        # Add handlers
        self.profiles_listbox.bind('<<ListboxSelect>>', self._ui_on_profile_selected)

    def _ui_refresh_profiles_list(self) -> None:
        """
        Refresh the profiles listbox
        """
        # Clear existing items
        self.profiles_listbox.delete(0, tk.END)
        
        # Get profiles from the plugin
        profiles = self.plugin.get_available_profiles()
        active_profile = self.plugin.get_active_profile_name()
        
        # Add to listbox
        for i, name in enumerate(sorted(profiles)):
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
        
        # Get profile data from plugin
        profile = self.plugin.get_profile(profile_name)
        if not profile:
            return
        
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
        
        # Get profile name
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Activate using plugin method
        success = self.plugin.set_active_profile(profile_name)
        
        if success:
            messagebox.showinfo("Profile Activated", f"Profile '{profile_name}' is now active")
            self._ui_refresh_profiles_list()
        else:
            messagebox.showerror("Activation Failed", f"Failed to activate profile '{profile_name}'")
    
    def _ui_create_profile(self) -> None:
        """
        Create a new profile
        """
        # Show dialog for creating new profile
        dialog = tk.Toplevel(self.ui_panel)
        dialog.title("Create New Profile")
        dialog.transient(self.ui_panel)
        dialog.grab_set()
        
        # Create form for basic profile info
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Name:", width=10).pack(side=tk.LEFT)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, width=30, textvariable=name_var)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Description field
        desc_frame = ttk.Frame(frame)
        desc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(desc_frame, text="Description:", width=10).pack(side=tk.LEFT)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(desc_frame, width=40, textvariable=desc_var)
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Template selection
        template_frame = ttk.Frame(frame)
        template_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(template_frame, text="Template:").pack(side=tk.LEFT, padx=5)
        
        templates = ["Empty", "Standard", "Formal", "Casual", "Technical", "Creative"]
        template_var = tk.StringVar(value="Empty")
        template_combo = ttk.Combobox(
            template_frame,
            textvariable=template_var,
            values=templates
        )
        template_combo.pack(side=tk.LEFT, padx=5)
        
        # Description 
        ttk.Label(
            frame,
            text="You can edit all profile details after creating it.",
            font=("Helvetica", 9, "italic")
        ).pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def on_create():
            name = name_var.get().strip()
            description = desc_var.get().strip()
            template = template_var.get()
            
            if not name:
                messagebox.showwarning("Missing Name", "Please enter a profile name")
                return
                
            if name in self.plugin.get_available_profiles():
                messagebox.showerror("Name Exists", f"A profile named '{name}' already exists")
                return
            
            # Create profile
            if template == "Empty":
                # Create empty profile
                from plugins.personality_plugin.core import create_empty_profile
                profile_data = create_empty_profile(name)
                profile_data["description"] = description
            else:
                # Use selected template
                template_profile = self.plugin.get_profile(template) 
                if not template_profile:
                    # Fallback to empty profile
                    from plugins.personality_plugin.core import create_empty_profile
                    profile_data = create_empty_profile(name)
                else:
                    # Clone template
                    profile_data = template_profile.copy()
                    profile_data["name"] = name
                    
                profile_data["description"] = description
            
            # Create new profile
            success = self.plugin.create_profile(profile_data)
            
            if success:
                messagebox.showinfo("Profile Created", f"Profile '{name}' created successfully")
                dialog.destroy()
                self._ui_refresh_profiles_list()
                
                # Select the new profile
                profiles = sorted(self.plugin.get_available_profiles())
                try:
                    idx = profiles.index(name)
                    self.profiles_listbox.selection_set(idx)
                    self.profiles_listbox.see(idx)
                    self._ui_on_profile_selected(None)
                except ValueError:
                    pass
            else:
                messagebox.showerror("Creation Failed", f"Failed to create profile '{name}'")
        
        ttk.Button(button_frame, text="Create", command=on_create).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Center dialog and focus name field
        dialog.update_idletasks()
        dialog.geometry(f"400x250+{dialog.winfo_screenwidth()//2-200}+{dialog.winfo_screenheight()//2-125}")
        name_entry.focus_set()

    def _ui_edit_profile(self) -> None:
        """
        Edit the selected profile
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a profile to edit")
            return
        
        # Get profile name
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
            
        # Get current profile data
        profile = self.plugin.get_profile(profile_name)
        if not profile:
            messagebox.showerror("Profile Not Found", f"Profile '{profile_name}' not found")
            return
        
        # Create dialog for editing
        dialog = tk.Toplevel(self.ui_panel)
        dialog.title(f"Edit Profile: {profile_name}")
        dialog.transient(self.ui_panel)
        dialog.grab_set()
        
        # Use notebook for tabs
        import tkinter.ttk as ttk
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic info tab
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Basic Info")
        
        # Style tab
        style_tab = ttk.Frame(notebook)
        notebook.add(style_tab, text="Style")
        
        # Formatting tab
        format_tab = ttk.Frame(notebook)
        notebook.add(format_tab, text="Formatting")
        
        # --- Basic info tab ---
        basic_fields = [
            ("name", "Name:", profile.get("name", "")),
            ("description", "Description:", profile.get("description", "")),
            ("tags", "Tags:", ", ".join(profile.get("tags", []))),
            ("author", "Author:", profile.get("author", "")),
            ("version", "Version:", profile.get("version", "1.0.0")),
        ]
        
        basic_vars = {}
        for i, (field_id, label_text, value) in enumerate(basic_fields):
            field_frame = ttk.Frame(basic_tab)
            field_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(field_frame, text=label_text, width=12).pack(side=tk.LEFT)
            
            var = tk.StringVar(value=value)
            basic_vars[field_id] = var
            
            if field_id == "description":
                entry = ttk.Entry(field_frame, width=50, textvariable=var)
            else:
                entry = ttk.Entry(field_frame, width=30, textvariable=var)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Prefix/suffix
        prefix_frame = ttk.Frame(basic_tab)
        prefix_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(prefix_frame, text="Prefix:", width=12).pack(side=tk.LEFT)
        prefix_var = tk.StringVar(value=profile.get("prefix", ""))
        basic_vars["prefix"] = prefix_var
        ttk.Entry(prefix_frame, width=50, textvariable=prefix_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        suffix_frame = ttk.Frame(basic_tab)
        suffix_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(suffix_frame, text="Suffix:", width=12).pack(side=tk.LEFT)
        suffix_var = tk.StringVar(value=profile.get("suffix", ""))
        basic_vars["suffix"] = suffix_var
        ttk.Entry(suffix_frame, width=50, textvariable=suffix_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # --- Style tab ---
        style_vars = {}
        style_modifiers = profile.get("style_modifiers", {})
        
        style_pairs = [
            ("formality", "Formal", "Casual"),
            ("creativity", "Creative", "Factual"),
            ("complexity", "Complex", "Simple"),
            ("empathy", "Empathetic", "Objective"),
            ("directness", "Direct", "Diplomatic"),
            ("humor", "Humorous", "Serious"),
            ("enthusiasm", "Enthusiastic", "Reserved"),
            ("conciseness", "Concise", "Detailed")
        ]
        
        # Create sliders in a grid
        for i, (mod_id, left_label, right_label) in enumerate(style_pairs):
            row = i // 2
            col = (i % 2) * 3
            
            # Left label
            ttk.Label(style_tab, text=left_label).grid(row=row, column=col, padx=5, pady=10, sticky=tk.E)
            
            # Slider
            var = tk.DoubleVar(value=style_modifiers.get(mod_id, 0.5))
            style_vars[mod_id] = var
            
            slider = ttk.Scale(
                style_tab,
                from_=0.0,
                to=1.0,
                orient=tk.HORIZONTAL,
                length=100,
                variable=var
            )
            slider.grid(row=row, column=col+1, padx=5, pady=10)
            
            # Right label
            ttk.Label(style_tab, text=right_label).grid(row=row, column=col+2, padx=5, pady=10, sticky=tk.W)
        
        # --- Formatting tab ---
        format_vars = {}
        formatting = profile.get("formatting", {})
        
        # Checkboxes for boolean options
        format_bools = [
            ("emphasize_key_points", "Emphasize key points", 
             formatting.get("emphasize_key_points", False)),
            ("use_markdown", "Use Markdown formatting", 
             formatting.get("use_markdown", True)),
        ]
        
        for i, (option_id, label, value) in enumerate(format_bools):
            var = tk.BooleanVar(value=value)
            format_vars[option_id] = var
            
            checkbox = ttk.Checkbutton(
                format_tab,
                text=label,
                variable=var
            )
            checkbox.pack(anchor=tk.W, padx=10, pady=5)
        
        # Paragraph structure dropdown
        para_frame = ttk.Frame(format_tab)
        para_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(para_frame, text="Paragraph structure:").pack(side=tk.LEFT, padx=5)
        
        para_var = tk.StringVar(value=formatting.get("paragraph_structure", "standard"))
        format_vars["paragraph_structure"] = para_var
        
        para_combo = ttk.Combobox(
            para_frame,
            textvariable=para_var,
            values=["standard", "concise", "detailed", "academic"]
        )
        para_combo.pack(side=tk.LEFT, padx=5)
        
        # --- Buttons at bottom ---
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_save():
            # Collect values
            updated_profile = profile.copy()
            
            # Update basic fields
            for field_id, var in basic_vars.items():
                if field_id == "tags":
                    # Convert comma-separated string to list
                    tags_str = var.get().strip()
                    if tags_str:
                        updated_profile["tags"] = [t.strip() for t in tags_str.split(",")]
                    else:
                        updated_profile["tags"] = []
                else:
                    updated_profile[field_id] = var.get()
            
            # Update style modifiers
            style_mods = updated_profile.get("style_modifiers", {})
            for mod_id, var in style_vars.items():
                style_mods[mod_id] = var.get()
            updated_profile["style_modifiers"] = style_mods
            
            # Update formatting
            format_opts = updated_profile.get("formatting", {})
            for opt_id, var in format_vars.items():
                format_opts[opt_id] = var.get()
            updated_profile["formatting"] = format_opts
            
            # Save profile
            success = self.plugin.update_profile(profile_name, updated_profile)
            
            if success:
                messagebox.showinfo("Profile Updated", f"Profile '{profile_name}' updated successfully")
                dialog.destroy()
                self._ui_refresh_profiles_list()
            else:
                messagebox.showerror("Update Failed", f"Failed to update profile '{profile_name}'")
        
        ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        dialog.geometry(f"600x400+{dialog.winfo_screenwidth()//2-300}+{dialog.winfo_screenheight()//2-200}")

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
        
        # Get profile name
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Check if this is the active profile
        active_profile = self.plugin.get_active_profile_name()
        if profile_name == active_profile:
            messagebox.showerror(
                "Cannot Delete", 
                f"Cannot delete the active profile. Please activate a different profile first."
            )
            return
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete the profile '{profile_name}'?\nThis cannot be undone.",
            icon=messagebox.WARNING
        )
        
        if not confirm:
            return
        
        # Delete the profile
        success = self.plugin.delete_profile(profile_name)
        
        if success:
            messagebox.showinfo("Profile Deleted", f"Profile '{profile_name}' has been deleted")
            self._ui_refresh_profiles_list()
        else:
            messagebox.showerror("Delete Failed", f"Failed to delete profile '{profile_name}'")
    
    def _ui_import_profile(self) -> None:
        """
        Import a profile from JSON or file
        """
        # Ask user if they want to import from file or paste JSON
        import_options = ["Import from file", "Paste JSON"]
        choice = messagebox.askquestion(
            "Import Method",
            "Do you want to import from a file?",
            type=messagebox.YESNOCANCEL
        )
        
        if choice == "yes":
            # Import from file
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Select Profile File",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Use plugin's import method
            success = self.plugin.import_profile_from_file(file_path)
            
            if success:
                messagebox.showinfo("Profile Imported", f"Profile imported successfully from {file_path}")
                self._ui_refresh_profiles_list()
            else:
                messagebox.showerror("Import Failed", f"Failed to import profile from {file_path}")
                
        elif choice == "no":
            # Import from pasted JSON
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
                import json
                json_str = json_text.get("1.0", tk.END).strip()
                if not json_str:
                    messagebox.showwarning("Empty JSON", "Please paste profile JSON")
                    return
                
                try:
                    # Parse JSON to verify format
                    profile_data = json.loads(json_str)
                    
                    # Get profile name
                    profile_name = profile_data.get("name")
                    if not profile_name:
                        messagebox.showerror("Invalid Profile", "Profile must have a name")
                        return
                        
                    # Check if profile already exists
                    if profile_name in self.plugin.get_available_profiles():
                        confirm = messagebox.askyesno(
                            "Profile Exists",
                            f"A profile named '{profile_name}' already exists. Overwrite?",
                            icon=messagebox.WARNING
                        )
                        
                        if not confirm:
                            return
                
                    # Create or update the profile
                    success = self._save_profile_changes(profile_name, profile_data)
                    
                    if success:
                        messagebox.showinfo("Profile Imported", f"Profile '{profile_name}' imported successfully")
                        dialog.destroy()
                        self._ui_refresh_profiles_list()
                    else:
                        messagebox.showerror("Import Failed", f"Failed to import profile '{profile_name}'")
                        
                except json.JSONDecodeError:
                    messagebox.showerror("Invalid JSON", "The provided text is not valid JSON")
                    
                except Exception as e:
                    messagebox.showerror("Import Error", f"Error importing profile: {e}")
            
            ttk.Button(button_frame, text="Import", command=on_import).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
            # Center dialog
            dialog.update_idletasks()
            dialog.geometry(f"600x500+{dialog.winfo_screenwidth()//2-300}+{dialog.winfo_screenheight()//2-250}")

    def _ui_export_profile(self) -> None:
        """
        Export the selected profile to JSON or file
        """
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a profile to export")
            return
        
        # Get profile name
        display_name = self.profiles_listbox.get(selection[0])
        if display_name.startswith("* "):
            profile_name = display_name[2:].split(" (Active)")[0]
        else:
            profile_name = display_name
        
        # Get profile data
        profile = self.plugin.get_profile(profile_name)
        if not profile:
            messagebox.showerror("Profile Not Found", f"Profile '{profile_name}' not found")
            return
        
        # Ask user if they want to export to file or view JSON
        export_options = ["Export to file", "View JSON"]
        choice = messagebox.askquestion(
            "Export Method",
            "Do you want to export to a file?",
            type=messagebox.YESNOCANCEL
        )
        
        if choice == "yes":
            # Export to file
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="Save Profile",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                initialfile=f"{profile_name}.json"
            )
            
            if not file_path:
                return
                
            # Use plugin's export method
            success = self.plugin.export_profile_to_file(profile_name, file_path)
            
            if success:
                messagebox.showinfo("Profile Exported", f"Profile exported to {file_path}")
            else:
                messagebox.showerror("Export Failed", f"Failed to export profile to {file_path}")
                
        elif choice == "no":
            # Display JSON in dialog
            import json
            
            # Format JSON for display
            json_str = json.dumps(profile, indent=2)
            
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
    
    def activate_ui(self, parent_container):
        """
        Activate the plugin UI
        
        Args:
            parent_container: Parent widget to attach UI to
        
        Returns:
            The UI panel
        """
        panel = self.get_ui_panel(parent_container)
        panel.pack(fill=tk.BOTH, expand=True)
        return panel
    
    def _save_profile_changes(self, profile_name, profile_data):
        """
        Save changes to a profile
        
        Args:
            profile_name: Name of the profile to update
            profile_data: New profile data
            
        Returns:
            Success flag
        """
        if profile_name in self.plugin.get_available_profiles():
            # Update existing profile
            return self.plugin.update_profile(profile_name, profile_data)
        else:
            # Create new profile
            return self.plugin.create_profile(profile_name, profile_data)