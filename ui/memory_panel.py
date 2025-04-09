"""
Memory panel UI component for the Irintai assistant
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
from typing import Callable, Dict, List, Any, Optional

class MemoryPanel:
    """Memory management panel for vector embeddings and knowledge retrieval"""
    
    def __init__(self, parent, memory_system, file_ops, logger: Callable, chat_engine):
        """
        Initialize the memory panel
        
        Args:
            parent: Parent widget
            memory_system: MemorySystem instance
            file_ops: FileOps instance
            logger: Logging function
            chat_engine: ChatEngine instance
        """
        self.parent = parent
        self.memory_system = memory_system
        self.file_ops = file_ops
        self.log = logger
        self.chat_engine = chat_engine
        
        # Create the main frame
        self.frame = ttk.Frame(parent)
        
        # Initialize UI components
        self.initialize_ui()
        
        # Load memory stats
        self.refresh_stats()
        
    def initialize_ui(self):
        """Initialize the UI components"""
        # Create memory management section
        self.create_memory_management()
        
        # Create memory search section
        self.create_memory_search()
        
        # Create indexed documents section
        self.create_documents_section()
        
    def create_memory_management(self):
        """Create the memory management section"""
        mgmt_frame = ttk.LabelFrame(self.frame, text="Memory Management")
        mgmt_frame.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)
        
        # Load files section
        load_frame = ttk.Frame(mgmt_frame)
        load_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            load_frame,
            text="Load Files",
            command=self.load_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            load_frame,
            text="Load Folder",
            command=self.load_folder
        ).pack(side=tk.LEFT, padx=5)
        
        # Memory stats section
        stats_frame = ttk.Frame(mgmt_frame)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(stats_frame, text="Document Count:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.doc_count_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.doc_count_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Last Updated:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.last_updated_var = tk.StringVar(value="Never")
        ttk.Label(stats_frame, textvariable=self.last_updated_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Index Path:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.index_path_var = tk.StringVar(value=self.memory_system.index_path)
        ttk.Label(stats_frame, textvariable=self.index_path_var, foreground="blue").grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Action buttons
        action_frame = ttk.Frame(mgmt_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            action_frame,
            text="Clear Index",
            command=self.clear_index
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Save Index",
            command=self.save_index
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Refresh Stats",
            command=self.refresh_stats
        ).pack(side=tk.LEFT, padx=5)
        
        # Memory mode section
        mode_frame = ttk.Frame(mgmt_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(mode_frame, text="Memory Mode:").pack(side=tk.LEFT)
        
        self.memory_mode_var = tk.StringVar(value=self.chat_engine.memory_mode)
        memory_modes = ["Off", "Manual", "Auto", "Background"]
        
        mode_dropdown = ttk.Combobox(
            mode_frame,
            textvariable=self.memory_mode_var,
            values=memory_modes,
            state="readonly",
            width=15
        )
        mode_dropdown.pack(side=tk.LEFT, padx=5)
        mode_dropdown.bind("<<ComboboxSelected>>", self.on_memory_mode_changed)
        
        # Add mode description
        self.mode_desc_var = tk.StringVar(value=self._get_mode_description("Off"))
        ttk.Label(mode_frame, textvariable=self.mode_desc_var, font=("Helvetica", 9, "italic")).pack(side=tk.LEFT, padx=20)
        
    def create_memory_search(self):
        """Create the memory search section"""
        search_frame = ttk.LabelFrame(self.frame, text="Memory Search")
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Search input section
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Query:").pack(side=tk.LEFT)
        
        self.search_entry = ttk.Entry(input_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<Return>", self.search_memory)
        
        ttk.Button(
            input_frame,
            text="Search",
            command=self.search_memory
        ).pack(side=tk.LEFT, padx=5)
        
        # Search options
        options_frame = ttk.Frame(search_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(options_frame, text="Results:").pack(side=tk.LEFT)
        
        self.results_count_var = tk.StringVar(value="5")
        results_spinbox = ttk.Spinbox(
            options_frame,
            from_=1,
            to=20,
            width=5,
            textvariable=self.results_count_var
        )
        results_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Search results section
        results_frame = ttk.Frame(search_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrolled text for results
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            height=10,
            font=("Helvetica", 9)
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags
        self.results_text.tag_configure(
            "heading",
            font=("Helvetica", 10, "bold"),
            foreground="#000080"
        )
        self.results_text.tag_configure(
            "source",
            font=("Helvetica", 9, "italic"),
            foreground="#800000"
        )
        self.results_text.tag_configure(
            "score",
            font=("Helvetica", 9),
            foreground="#008000"
        )
        self.results_text.tag_configure(
            "content",
            font=("Helvetica", 9)
        )
        
    def create_documents_section(self):
        """Create the indexed documents section"""
        docs_frame = ttk.LabelFrame(self.frame, text="Indexed Documents")
        docs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a tree view for documents
        columns = ("Source", "Type", "Chunks", "Last Updated")
        self.docs_tree = ttk.Treeview(
            docs_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.docs_tree.heading("Source", text="Document")
        self.docs_tree.heading("Type", text="Type")
        self.docs_tree.heading("Chunks", text="Chunks")
        self.docs_tree.heading("Last Updated", text="Last Updated")
        
        self.docs_tree.column("Source", width=250, anchor=tk.W)
        self.docs_tree.column("Type", width=80, anchor=tk.CENTER)
        self.docs_tree.column("Chunks", width=60, anchor=tk.CENTER)
        self.docs_tree.column("Last Updated", width=150, anchor=tk.CENTER)
        
        # Add scrollbar
        docs_scrollbar = ttk.Scrollbar(docs_frame, orient="vertical", command=self.docs_tree.yview)
        self.docs_tree.configure(yscrollcommand=docs_scrollbar.set)
        
        # Pack the tree and scrollbar
        self.docs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        docs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.docs_tree.bind("<<TreeviewSelect>>", self.on_document_selected)
        
        # Create document preview frame
        preview_frame = ttk.LabelFrame(self.frame, text="Document Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create preview text
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            wrap=tk.WORD,
            height=6,
            font=("Helvetica", 9)
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Add Preview/Remove buttons
        preview_buttons = ttk.Frame(preview_frame)
        preview_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            preview_buttons,
            text="Open Document",
            command=self.open_selected_document
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            preview_buttons,
            text="Remove from Index",
            command=self.remove_selected_document
        ).pack(side=tk.LEFT, padx=5)
        
    def refresh_stats(self):
        """Refresh memory statistics"""
        # Get stats from memory system
        stats = self.memory_system.get_stats()
        
        # Update UI
        self.doc_count_var.set(str(stats["documents_count"]))
        self.last_updated_var.set(stats["last_updated"] or "Never")
        self.index_path_var.set(stats["index_path"])
        
        # Update document tree
        self._update_document_tree(stats)
        
    def _update_document_tree(self, stats):
        """
        Update the document tree with current index contents
        
        Args:
            stats: Memory system statistics
        """
        # Clear the current tree
        for item in self.docs_tree.get_children():
            self.docs_tree.delete(item)
            
        # Group documents by source
        sources = {}
        for doc in self.memory_system.documents:
            source = doc.get("source", "Unknown")
            file_type = os.path.splitext(source)[1] if "." in source else "Unknown"
            timestamp = doc.get("timestamp", "Unknown")
            
            if source in sources:
                sources[source]["count"] += 1
                # Keep the most recent timestamp
                if timestamp > sources[source]["timestamp"]:
                    sources[source]["timestamp"] = timestamp
            else:
                sources[source] = {
                    "type": file_type,
                    "count": 1,
                    "timestamp": timestamp
                }
                
        # Add to tree
        for source, info in sources.items():
            self.docs_tree.insert(
                "",
                tk.END,
                values=(
                    source,
                    info["type"],
                    info["count"],
                    info["timestamp"]
                )
            )
            
    def on_document_selected(self, event):
        """Handle document selection in tree"""
        selection = self.docs_tree.selection()
        if not selection:
            return
            
        # Get document info
        item = selection[0]
        values = self.docs_tree.item(item, "values")
        source = values[0]
        
        # Find all chunks for this source
        chunks = []
        for doc in self.memory_system.documents:
            if doc.get("source") == source:
                chunks.append(doc)
                
        if not chunks:
            return
            
        # Take the first chunk as preview
        preview = chunks[0].get("text", "")
        
        # Limit preview length
        if len(preview) > 1000:
            preview = preview[:1000] + "..."
            
        # Update preview text
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, preview)
        
    def load_files(self):
        """Load files into memory"""
        # Get list of supported extensions
        extensions = self.file_ops.get_supported_extensions()
        
        # Create file type string for dialog
        file_types = [("Supported Files", " ".join(f"*{ext}" for ext in extensions))]
        for ext in extensions:
            content_types = self.file_ops.get_content_types()
            desc = content_types.get(ext, ext[1:].upper() + " Files")
            file_types.append((desc, f"*{ext}"))
        
        # Open file dialog
        files = filedialog.askopenfilenames(
            title="Select files to load",
            filetypes=file_types
        )
        
        if not files:
            return
            
        # Show progress dialog
        progress_window = tk.Toplevel(self.frame)
        progress_window.title("Loading Files")
        progress_window.geometry("300x150")
        progress_window.transient(self.frame)
        progress_window.grab_set()
        
        ttk.Label(
            progress_window,
            text="Loading files into memory...",
            font=("Helvetica", 10, "bold")
        ).pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window,
            variable=progress_var,
            maximum=len(files)
        )
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_var = tk.StringVar(value="Starting...")
        status_label = ttk.Label(
            progress_window,
            textvariable=status_var
        )
        status_label.pack(pady=10)
        
        # Load files in a separate thread
        def load_thread():
            for i, file_path in enumerate(files):
                # Update progress
                progress_var.set(i)
                filename = os.path.basename(file_path)
                status_var.set(f"Loading {filename}...")
                progress_window.update()
                
                # Read the file
                success, content = self.file_ops.read_file(file_path)
                
                if success:
                    # Add to memory system
                    self.memory_system.add_file_to_index(file_path, content)
                    self.log(f"[Loaded] {filename}")
                else:
                    self.log(f"[Error] Failed to load {file_path}")
                    
            # Finish up
            progress_var.set(len(files))
            status_var.set("Complete")
            progress_window.update()
            
            # Save the index
            self.memory_system.save_index()
            
            # Refresh stats
            self.refresh_stats()
            
            # Close the progress window after a short delay
            progress_window.after(1000, progress_window.destroy)
            
            # Show confirmation
            messagebox.showinfo(
                "Files Loaded", 
                f"Successfully loaded {len(files)} files into memory."
            )
            
        threading.Thread(target=load_thread, daemon=True).start()
        
    def load_folder(self):
        """Load all files from a folder into memory"""
        # Open folder dialog
        folder = filedialog.askdirectory(
            title="Select folder to load"
        )
        
        if not folder:
            return
            
        # Get list of supported extensions
        extensions = self.file_ops.get_supported_extensions()
        
        # Find all supported files in the folder
        files = []
        for ext in extensions:
            files.extend(self.file_ops.get_files_by_type(folder, ext))
            
        if not files:
            messagebox.showinfo(
                "No Files Found",
                f"No supported files found in {folder}"
            )
            return
            
        # Confirm loading
        result = messagebox.askyesno(
            "Load Files",
            f"Found {len(files)} supported files in {folder}. Load them all?",
            icon=messagebox.QUESTION
        )
        
        if not result:
            return
            
        # Show progress dialog
        progress_window = tk.Toplevel(self.frame)
        progress_window.title("Loading Folder")
        progress_window.geometry("300x150")
        progress_window.transient(self.frame)
        progress_window.grab_set()
        
        ttk.Label(
            progress_window,
            text="Loading files from folder...",
            font=("Helvetica", 10, "bold")
        ).pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window,
            variable=progress_var,
            maximum=len(files)
        )
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_var = tk.StringVar(value="Starting...")
        status_label = ttk.Label(
            progress_window,
            textvariable=status_var
        )
        status_label.pack(pady=10)
        
        # Load files in a separate thread
        def load_thread():
            for i, file_path in enumerate(files):
                # Update progress
                progress_var.set(i)
                filename = os.path.basename(file_path)
                status_var.set(f"Loading {filename}...")
                progress_window.update()
                
                # Read the file
                success, content = self.file_ops.read_file(file_path)
                
                if success:
                    # Add to memory system
                    self.memory_system.add_file_to_index(file_path, content)
                    self.log(f"[Loaded] {filename}")
                else:
                    self.log(f"[Error] Failed to load {file_path}")
                    
            # Finish up
            progress_var.set(len(files))
            status_var.set("Complete")
            progress_window.update()
            
            # Save the index
            self.memory_system.save_index()
            
            # Refresh stats
            self.refresh_stats()
            
            # Close the progress window after a short delay
            progress_window.after(1000, progress_window.destroy)
            
            # Show confirmation
            messagebox.showinfo(
                "Folder Loaded", 
                f"Successfully loaded {len(files)} files from {folder}."
            )
            
        threading.Thread(target=load_thread, daemon=True).start()
        
    def clear_index(self):
        """Clear the memory index"""
        # Confirm action
        result = messagebox.askyesno(
            "Clear Index",
            "Are you sure you want to clear the entire memory index? This cannot be undone.",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
            
        # Clear the index
        success = self.memory_system.clear_index()
        
        if success:
            # Refresh stats
            self.refresh_stats()
            
            # Clear preview
            self.preview_text.delete(1.0, tk.END)
            
            # Show confirmation
            messagebox.showinfo(
                "Index Cleared",
                "Memory index has been cleared."
            )
        else:
            messagebox.showerror(
                "Error",
                "Failed to clear memory index."
            )
            
    def save_index(self):
        """Save the memory index"""
        # Save the index
        success = self.memory_system.save_index()
        
        if success:
            # Show confirmation
            messagebox.showinfo(
                "Index Saved",
                f"Memory index has been saved to {self.memory_system.index_path}"
            )
        else:
            messagebox.showerror(
                "Error",
                "Failed to save memory index."
            )
            
    def on_memory_mode_changed(self, event):
        """Handle memory mode changes"""
        mode = self.memory_mode_var.get()
        
        # Update chat engine
        self.chat_engine.set_memory_mode(mode)
        
        # Update description
        self.mode_desc_var.set(self._get_mode_description(mode))
        
    def _get_mode_description(self, mode):
        """
        Get description for a memory mode
        
        Args:
            mode: Memory mode
            
        Returns:
            Description text
        """
        descriptions = {
            "Off": "Memory not used for responses",
            "Manual": "Manual search only",
            "Auto": "Automatically adds context to prompts",
            "Background": "Silently adds context to all prompts"
        }
        
        return descriptions.get(mode, "")
        
    def search_memory(self, event=None):
        """Search the memory index"""
        query = self.search_entry.get().strip()
        if not query:
            return
            
        # Get result count
        try:
            count = int(self.results_count_var.get())
        except ValueError:
            count = 5
            
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Searching for: {query}\n\n", "heading")
        
        # Perform search
        results = self.memory_system.search(query, top_k=count)
        
        if not results:
            self.results_text.insert(tk.END, "No results found.\n", "content")
            return
            
        # Display results
        for i, result in enumerate(results):
            source = result.get("source", "Unknown")
            score = result.get("score", 0.0)
            text = result.get("text", "")
            
            # Limit text length
            if len(text) > 300:
                text = text[:300] + "..."
                
            # Add result header
            self.results_text.insert(tk.END, f"Result {i+1}: ", "heading")
            self.results_text.insert(tk.END, f"{source}\n", "source")
            self.results_text.insert(tk.END, f"Relevance: {score:.2f}\n", "score")
            self.results_text.insert(tk.END, f"{text}\n\n", "content")
            
    def open_selected_document(self):
        """Open the selected document"""
        selection = self.docs_tree.selection()
        if not selection:
            return
            
        # Get document info
        item = selection[0]
        values = self.docs_tree.item(item, "values")
        source = values[0]
        
        # Find path for this source
        path = None
        for doc in self.memory_system.documents:
            if doc.get("source") == source and "path" in doc:
                path = doc["path"]
                break
                
        if not path or not os.path.exists(path):
            messagebox.showerror(
                "Error",
                f"Cannot find original file for {source}"
            )
            return
            
        # Open the file using system default application
        import subprocess
        import sys
        import os
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(path)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', path])
                
            self.log(f"[Opened] {path}")
        except Exception as e:
            self.log(f"[Error] Cannot open file: {e}")
            messagebox.showerror("Error", f"Cannot open file: {e}")
            
    def remove_selected_document(self):
        """Remove the selected document from the index"""
        selection = self.docs_tree.selection()
        if not selection:
            return
            
        # Get document info
        item = selection[0]
        values = self.docs_tree.item(item, "values")
        source = values[0]
        
        # Confirm removal
        result = messagebox.askyesno(
            "Remove Document",
            f"Are you sure you want to remove '{source}' from the memory index?",
            icon=messagebox.QUESTION
        )
        
        if not result:
            return
            
        # Remove all documents with this source
        removed = 0
        indices_to_remove = []
        
        # Find indices to remove
        for i, doc in enumerate(self.memory_system.documents):
            if doc.get("source") == source:
                indices_to_remove.append(i)
                removed += 1
                
        # Remove from highest index to lowest to avoid shifting issues
        for idx in sorted(indices_to_remove, reverse=True):
            del self.memory_system.documents[idx]
            del self.memory_system.index[idx]
            
        # Save the index
        self.memory_system.save_index()
        
        # Refresh stats
        self.refresh_stats()
        
        # Clear preview
        self.preview_text.delete(1.0, tk.END)
        
        # Show confirmation
        messagebox.showinfo(
            "Document Removed",
            f"Removed {removed} chunks from '{source}' in the memory index."
        )
        
import os  # Import needed for path operations