"""
IrintAI Assistant Diagnostic Suite

This module provides a comprehensive diagnostic suite for the IrintAI Assistant,
allowing users to diagnose various components of the system.
"""
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

# Add project root to sys.path to allow importing core modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.config_manager import ConfigManager
    from utils.logger import IrintaiLogger
    from diagnostics.ollama_panel_diagnostic import OllamaPanelDiagnostic
    from diagnostics.system_diagnostic import SystemDiagnostic
    from diagnostics.config_diagnostic import ConfigDiagnostic
    from diagnostics.plugin_diagnostic import PluginDiagnostic
    from diagnostics.memory_diagnostic import MemoryDiagnostic
    from diagnostics.network_diagnostic import NetworkDiagnostic
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure the script is run from the project root or the PYTHONPATH is set correctly.")
    sys.exit(1)

# Setup logger for diagnostics
logger = IrintaiLogger('diagnostic_suite', 'diagnostic_suite.log')

class DiagnosticSuite:
    """Main controller for the IrintAI Assistant diagnostic suite"""
    def __init__(self, config_path='data/config.json'):
        """Initialize the diagnostic suite with configuration"""
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.results = {}
        self.diagnostic_modules = {}
        self.initialize_modules()
        
    def initialize_modules(self):
        """Initialize all diagnostic modules"""
        # Initialize each diagnostic module
        try:
            self.diagnostic_modules['system'] = SystemDiagnostic()
            self.diagnostic_modules['config'] = ConfigDiagnostic(self.config_path)
            self.diagnostic_modules['ollama'] = OllamaPanelDiagnostic(self.config_path)
            self.diagnostic_modules['plugin'] = PluginDiagnostic(self.config_path)
            self.diagnostic_modules['memory'] = MemoryDiagnostic(self.config_path)
            self.diagnostic_modules['network'] = NetworkDiagnostic(self.config_path)
            self.diagnostic_modules['network'] = NetworkDiagnostic(self.config_path)
            logger.info("All diagnostic modules initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing diagnostic modules: {e}")
            raise
    
    def run_all_diagnostics(self):
        """Run all diagnostic modules and collect results"""
        logger.info("Starting comprehensive diagnostic suite")
        start_time = time.time()
        
        # Run each module's diagnostics
        for module_name, module in self.diagnostic_modules.items():
            try:
                logger.info(f"Running {module_name} diagnostics")
                module.run_all_checks()
                self.results[module_name] = module.results
            except Exception as e:
                logger.error(f"Error running {module_name} diagnostics: {e}")
                self.results[module_name] = {'error': str(e)}
        
        elapsed_time = time.time() - start_time
        logger.info(f"All diagnostics completed in {elapsed_time:.2f} seconds")
        return self.results
    
    def run_specific_diagnostic(self, module_name):
        """Run a specific diagnostic module"""
        if module_name not in self.diagnostic_modules:
            logger.error(f"Diagnostic module {module_name} not found")
            return False
        
        try:
            module = self.diagnostic_modules[module_name]
            module.run_all_checks()
            self.results[module_name] = module.results
            return self.results[module_name]
        except Exception as e:
            logger.error(f"Error running {module_name} diagnostics: {e}")
            self.results[module_name] = {'error': str(e)}
            return self.results[module_name]
    
    def get_summary(self):
        """Get a summary of all diagnostic results"""
        if not self.results:
            return "No diagnostics have been run yet."
            
        summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "Success",
            "module_status": {},
            "error_count": 0,
            "warning_count": 0,
            "success_count": 0
        }
        
        for module_name, results in self.results.items():
            module_status = "Success"
            error_count = 0
            warning_count = 0
            success_count = 0
            
            for check, result in results.items():
                if isinstance(result, dict) and 'status' in result:
                    status = result['status'].lower()
                    if status == 'failure':
                        module_status = "Failure"
                        error_count += 1
                        summary["error_count"] += 1
                    elif status == 'warning':
                        if module_status != "Failure":  # Don't downgrade from failure
                            module_status = "Warning"
                        warning_count += 1
                        summary["warning_count"] += 1
                    elif status == 'success':
                        success_count += 1
                        summary["success_count"] += 1
            
            summary["module_status"][module_name] = {
                "status": module_status,
                "error_count": error_count,
                "warning_count": warning_count,
                "success_count": success_count
            }
            
            # Update overall status
            if module_status == "Failure" and summary["overall_status"] != "Failure":
                summary["overall_status"] = "Failure"
            elif module_status == "Warning" and summary["overall_status"] == "Success":
                summary["overall_status"] = "Warning"
        
        return summary
    
    def export_results(self, filepath=None):
        """Export diagnostic results to a JSON file"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(project_root, 'diagnostics', f'diagnostic_results_{timestamp}.json')
        
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": self.get_summary(),
                    "detailed_results": self.results
                }, f, indent=2)
            logger.info(f"Diagnostic results exported to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error exporting diagnostic results: {e}")
            return None
    
    def print_results(self):
        """Print diagnostic results to console"""
        summary = self.get_summary()
        if isinstance(summary, str):
            print(summary)
            return
            
        print("\n===== IrintAI Assistant Diagnostic Results =====")
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Success: {summary['success_count']} | Warnings: {summary['warning_count']} | Errors: {summary['error_count']}")
        print("=" * 50)
        
        for module_name, results in self.results.items():
            module_status = summary["module_status"].get(module_name, {})
            status_str = module_status.get("status", "Unknown")
            print(f"\n--- {module_name.upper()} DIAGNOSTICS: {status_str} ---")
            
            for check, result in results.items():
                if isinstance(result, dict) and 'status' in result:
                    status = result['status']
                    message = result.get('message', 'No details')
                    print(f"[{status.upper()}] {check.replace('_', ' ').title()}")
                    print(f"  {message}")
            
        print("\n===== End of Diagnostic Report =====")


class DiagnosticGUI:
    """GUI for the IrintAI Assistant Diagnostic Suite"""
    
    def __init__(self, master):
        """Initialize the diagnostic GUI"""
        self.master = master
        master.title("IrintAI Assistant Diagnostic Suite")
        master.geometry("800x600")
        
        # Initialize diagnostic suite
        self.diagnostic_suite = DiagnosticSuite()
        
        # Set up the main notebook
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
          # Create main tabs
        self.overview_frame = ttk.Frame(self.notebook)
        self.system_frame = ttk.Frame(self.notebook)
        self.config_frame = ttk.Frame(self.notebook)
        self.ollama_frame = ttk.Frame(self.notebook)
        self.plugin_frame = ttk.Frame(self.notebook)
        self.memory_frame = ttk.Frame(self.notebook)
        self.network_frame = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.overview_frame, text="Overview")
        self.notebook.add(self.system_frame, text="System")
        self.notebook.add(self.config_frame, text="Configuration")
        self.notebook.add(self.ollama_frame, text="Ollama")
        self.notebook.add(self.plugin_frame, text="Plugins")
        self.notebook.add(self.memory_frame, text="Memory")
        self.notebook.add(self.network_frame, text="Network")
        
        # Setup overview tab
        self.setup_overview_tab()
          # Setup diagnostic module tabs
        self.setup_system_tab()
        self.setup_config_tab()
        self.setup_ollama_tab()
        self.setup_plugin_tab()
        self.setup_memory_tab()
        self.setup_network_tab()
    
    def setup_overview_tab(self):
        """Set up the overview tab"""
        # Top frame for controls
        control_frame = ttk.Frame(self.overview_frame)
        control_frame.pack(fill='x', pady=10)
        
        # Buttons
        run_all_button = ttk.Button(control_frame, text="Run All Diagnostics", 
                                   command=self.run_all_diagnostics)
        run_all_button.pack(side='left', padx=5)
        
        export_button = ttk.Button(control_frame, text="Export Results", 
                                  command=self.export_results)
        export_button.pack(side='left', padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.overview_frame, text="System Status")
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Status indicators using treeview for better formatting
        self.status_tree = ttk.Treeview(status_frame, columns=("Module", "Status", "Success", "Warnings", "Errors"),
                                       show="headings", height=6)
        self.status_tree.heading("Module", text="Module")
        self.status_tree.heading("Status", text="Status")
        self.status_tree.heading("Success", text="Success")
        self.status_tree.heading("Warnings", text="Warnings")
        self.status_tree.heading("Errors", text="Errors")
        
        self.status_tree.column("Module", width=150)
        self.status_tree.column("Status", width=100)
        self.status_tree.column("Success", width=80, anchor='center')
        self.status_tree.column("Warnings", width=80, anchor='center')
        self.status_tree.column("Errors", width=80, anchor='center')
        
        self.status_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Results text area
        results_frame = ttk.LabelFrame(self.overview_frame, text="Summary")
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.summary_text = tk.Text(results_frame, wrap='word', height=10)
        self.summary_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def setup_system_tab(self):
        """Set up the system diagnostics tab"""
        # Controls
        control_frame = ttk.Frame(self.system_frame)
        control_frame.pack(fill='x', pady=10)
        
        run_button = ttk.Button(control_frame, text="Run System Diagnostics", 
                               command=lambda: self.run_specific_diagnostic('system'))
        run_button.pack(side='left', padx=5)
        
        # Results treeview
        self.system_tree = ttk.Treeview(self.system_frame, columns=("Check", "Status", "Message"),
                                       show="headings")
        self.system_tree.heading("Check", text="Check")
        self.system_tree.heading("Status", text="Status")
        self.system_tree.heading("Message", text="Message")
        
        self.system_tree.column("Check", width=150)
        self.system_tree.column("Status", width=80)
        self.system_tree.column("Message", width=400)
        
        self.system_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def setup_config_tab(self):
        """Set up the configuration diagnostics tab"""
        # Controls
        control_frame = ttk.Frame(self.config_frame)
        control_frame.pack(fill='x', pady=10)
        
        run_button = ttk.Button(control_frame, text="Run Config Diagnostics", 
                               command=lambda: self.run_specific_diagnostic('config'))
        run_button.pack(side='left', padx=5)
        
        # Results treeview
        self.config_tree = ttk.Treeview(self.config_frame, columns=("Check", "Status", "Message"),
                                       show="headings")
        self.config_tree.heading("Check", text="Check")
        self.config_tree.heading("Status", text="Status")
        self.config_tree.heading("Message", text="Message")
        
        self.config_tree.column("Check", width=150)
        self.config_tree.column("Status", width=80)
        self.config_tree.column("Message", width=400)
        
        self.config_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def setup_ollama_tab(self):
        """Set up the Ollama diagnostics tab"""
        # Controls
        control_frame = ttk.Frame(self.ollama_frame)
        control_frame.pack(fill='x', pady=10)
        
        run_button = ttk.Button(control_frame, text="Run Ollama Diagnostics", 
                               command=lambda: self.run_specific_diagnostic('ollama'))
        run_button.pack(side='left', padx=5)
        
        # Results treeview
        self.ollama_tree = ttk.Treeview(self.ollama_frame, columns=("Check", "Status", "Message"),
                                       show="headings")
        self.ollama_tree.heading("Check", text="Check")
        self.ollama_tree.heading("Status", text="Status")
        self.ollama_tree.heading("Message", text="Message")
        
        self.ollama_tree.column("Check", width=150)
        self.ollama_tree.column("Status", width=80)
        self.ollama_tree.column("Message", width=400)
        
        self.ollama_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def setup_plugin_tab(self):
        """Set up the plugin diagnostics tab"""
        # Controls
        control_frame = ttk.Frame(self.plugin_frame)
        control_frame.pack(fill='x', pady=10)
        
        run_button = ttk.Button(control_frame, text="Run Plugin Diagnostics", 
                               command=lambda: self.run_specific_diagnostic('plugin'))
        run_button.pack(side='left', padx=5)
        
        # Results treeview
        self.plugin_tree = ttk.Treeview(self.plugin_frame, columns=("Check", "Status", "Message"),
                                       show="headings")
        self.plugin_tree.heading("Check", text="Check")
        self.plugin_tree.heading("Status", text="Status")
        self.plugin_tree.heading("Message", text="Message")
        
        self.plugin_tree.column("Check", width=150)
        self.plugin_tree.column("Status", width=80)
        self.plugin_tree.column("Message", width=400)
        
        self.plugin_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def setup_memory_tab(self):
        """Set up the memory diagnostics tab"""
        # Controls
        control_frame = ttk.Frame(self.memory_frame)
        control_frame.pack(fill='x', pady=10)
        
        run_button = ttk.Button(control_frame, text="Run Memory Diagnostics", 
                               command=lambda: self.run_specific_diagnostic('memory'))
        run_button.pack(side='left', padx=5)
        
        # Results treeview
        self.memory_tree = ttk.Treeview(self.memory_frame, columns=("Check", "Status", "Message"),
                                       show="headings")
        self.memory_tree.heading("Check", text="Check")
        self.memory_tree.heading("Status", text="Status")
        self.memory_tree.heading("Message", text="Message")
        
        self.memory_tree.column("Check", width=150)
        self.memory_tree.column("Status", width=80)
        self.memory_tree.column("Message", width=400)
        
        self.memory_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def setup_network_tab(self):
        """Set up the network diagnostics tab"""
        # Controls
        control_frame = ttk.Frame(self.network_frame)
        control_frame.pack(fill='x', pady=10)
        
        run_button = ttk.Button(control_frame, text="Run Network Diagnostics", 
                               command=lambda: self.run_specific_diagnostic('network'))
        run_button.pack(side='left', padx=5)
        
        # Results treeview
        self.network_tree = ttk.Treeview(self.network_frame, columns=("Check", "Status", "Message"),
                                       show="headings")
        self.network_tree.heading("Check", text="Check")
        self.network_tree.heading("Status", text="Status")
        self.network_tree.heading("Message", text="Message")
        
        self.network_tree.column("Check", width=150)
        self.network_tree.column("Status", width=80)
        self.network_tree.column("Message", width=400)
        
        self.network_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def run_all_diagnostics(self):
        """Run all diagnostics and update UI"""
        # Disable all buttons during diagnostic run
        for child in self.master.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state='disabled')
                
        # Update status
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, "Running diagnostics...\n")
        
        # Run diagnostics in a separate thread to avoid freezing UI
        threading.Thread(target=self._run_all_diagnostics, daemon=True).start()
    
    def _run_all_diagnostics(self):
        """Thread target for running all diagnostics"""
        try:
            # Clear previous results
            self.status_tree.delete(*self.status_tree.get_children())
            
            # Run diagnostics
            self.diagnostic_suite.run_all_diagnostics()
            
            # Update UI on the main thread
            self.master.after(0, self._update_ui_after_diagnostics)
        except Exception as e:
            # Handle exceptions
            self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
            # Re-enable buttons
            self.master.after(0, self._enable_buttons)
    
    def _update_ui_after_diagnostics(self):
        """Update UI with diagnostic results"""
        # Get summary
        summary = self.diagnostic_suite.get_summary()
        
        # Update summary text
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, f"Diagnostics completed at {summary['timestamp']}\n")
        self.summary_text.insert(tk.END, f"Overall Status: {summary['overall_status']}\n")
        self.summary_text.insert(tk.END, f"Success: {summary['success_count']} | Warnings: {summary['warning_count']} | Errors: {summary['error_count']}\n\n")
        
        # Update status tree
        self.status_tree.delete(*self.status_tree.get_children())
        for module_name, module_status in summary["module_status"].items():
            status = module_status["status"]
            success = module_status["success_count"]
            warnings = module_status["warning_count"]
            errors = module_status["error_count"]
            
            tag = "normal"
            if status == "Failure":
                tag = "error"
            elif status == "Warning":
                tag = "warning"
                
            self.status_tree.insert("", "end", values=(module_name, status, success, warnings, errors), tags=(tag,))
        
        # Setup tags for coloring
        self.status_tree.tag_configure("error", background="#FFCCCC")
        self.status_tree.tag_configure("warning", background="#FFFFCC")
          # Update module-specific tabs
        self._update_module_tab(self.system_tree, 'system')
        self._update_module_tab(self.config_tree, 'config')
        self._update_module_tab(self.ollama_tree, 'ollama')
        self._update_module_tab(self.plugin_tree, 'plugin')
        self._update_module_tab(self.memory_tree, 'memory')
        self._update_module_tab(self.network_tree, 'network')
        
        # Re-enable buttons
        self._enable_buttons()
    
    def _update_module_tab(self, tree, module_name):
        """Update a specific module's tab with results"""
        # Clear existing results
        tree.delete(*tree.get_children())
        
        # Get results for this module
        results = self.diagnostic_suite.results.get(module_name, {})
        
        # Add results to tree
        for check, result in results.items():
            if isinstance(result, dict) and 'status' in result:
                status = result['status']
                message = result.get('message', 'No details')
                
                tag = "normal"
                if status.lower() == "failure":
                    tag = "error"
                elif status.lower() == "warning":
                    tag = "warning"
                
                tree.insert("", "end", values=(check.replace('_', ' ').title(), status, message), tags=(tag,))
        
        # Setup tags for coloring
        tree.tag_configure("error", background="#FFCCCC")
        tree.tag_configure("warning", background="#FFFFCC")
    
    def _enable_buttons(self):
        """Re-enable all buttons"""
        for child in self.master.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state='normal')
    def run_specific_diagnostic(self, module_name):
        """Run a specific diagnostic module and update its tab"""
        # Get the corresponding treeview
        tree_map = {
            'system': self.system_tree,
            'config': self.config_tree,
            'ollama': self.ollama_tree,
            'plugin': self.plugin_tree,
            'memory': self.memory_tree,
            'network': self.network_tree
        }
        
        tree = tree_map.get(module_name)
        if not tree:
            messagebox.showerror("Error", f"Unknown module: {module_name}")
            return
        
        # Clear tree
        tree.delete(*tree.get_children())
        
        # Disable buttons
        for child in self.master.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state='disabled')
        
        # Run diagnostic in thread
        threading.Thread(
            target=self._run_specific_diagnostic,
            args=(module_name, tree),
            daemon=True
        ).start()
    
    def _run_specific_diagnostic(self, module_name, tree):
        """Thread target for running a specific diagnostic"""
        try:
            # Run diagnostic
            results = self.diagnostic_suite.run_specific_diagnostic(module_name)
            
            # Update UI on main thread
            self.master.after(0, lambda: self._update_specific_tab(module_name, tree, results))
        except Exception as e:
            # Handle exceptions
            self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
        finally:
            # Re-enable buttons
            self.master.after(0, self._enable_buttons)
    
    def _update_specific_tab(self, module_name, tree, results):
        """Update a specific tab with diagnostic results"""
        # Clear tree
        tree.delete(*tree.get_children())
        
        # Add results
        for check, result in results.items():
            if isinstance(result, dict) and 'status' in result:
                status = result['status']
                message = result.get('message', 'No details')
                
                tag = "normal"
                if status.lower() == "failure":
                    tag = "error"
                elif status.lower() == "warning":
                    tag = "warning"
                
                tree.insert("", "end", values=(check.replace('_', ' ').title(), status, message), tags=(tag,))
        
        # Setup tags for coloring
        tree.tag_configure("error", background="#FFCCCC")
        tree.tag_configure("warning", background="#FFFFCC")
        
        # Also update overview if it exists
        if hasattr(self, 'status_tree') and module_name in self.diagnostic_suite.results:
            self._update_overview_for_module(module_name)
    
    def _update_overview_for_module(self, module_name):
        """Update overview tab for a specific module"""
        # Get summary
        summary = self.diagnostic_suite.get_summary()
        
        # Update module in status tree
        for item in self.status_tree.get_children():
            values = self.status_tree.item(item, 'values')
            if values and values[0] == module_name:
                self.status_tree.delete(item)
                break
        
        # Add updated module status
        module_status = summary["module_status"].get(module_name, {})
        status = module_status.get("status", "Unknown")
        success = module_status.get("success_count", 0)
        warnings = module_status.get("warning_count", 0)
        errors = module_status.get("error_count", 0)
        
        tag = "normal"
        if status == "Failure":
            tag = "error"
        elif status == "Warning":
            tag = "warning"
            
        self.status_tree.insert("", "end", values=(module_name, status, success, warnings, errors), tags=(tag,))
    
    def export_results(self):
        """Export diagnostic results to file"""
        if not self.diagnostic_suite.results:
            messagebox.showinfo("Info", "No diagnostic results to export. Please run diagnostics first.")
            return
            
        filepath = self.diagnostic_suite.export_results()
        if filepath:
            messagebox.showinfo("Success", f"Diagnostic results exported to:\n{filepath}")
        else:
            messagebox.showerror("Error", "Failed to export diagnostic results")


def run_diagnostics_cli():
    """Run diagnostics in command line mode"""
    print("=== IrintAI Assistant Diagnostic Suite ===")
    config_file = os.path.join(project_root, 'data', 'config.json')
    
    # Create and run diagnostics
    suite = DiagnosticSuite(config_path=config_file)
    suite.run_all_diagnostics()
    suite.print_results()
    
    # Export results
    filepath = suite.export_results()
    if filepath:
        print(f"\nDiagnostic results exported to: {filepath}")
    
    return 0

def run_diagnostics_gui():
    """Run diagnostics in GUI mode"""
    root = tk.Tk()
    app = DiagnosticGUI(root)
    root.mainloop()
    return 0

if __name__ == "__main__":
    # Check if GUI mode requested
    import argparse
    parser = argparse.ArgumentParser(description="IrintAI Assistant Diagnostic Suite")
    parser.add_argument('--gui', action='store_true', help='Run in GUI mode')
    parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
    args = parser.parse_args()
    
    # Default to GUI mode if no arguments provided
    if not args.cli and (args.gui or len(sys.argv) == 1):
        sys.exit(run_diagnostics_gui())
    else:
        sys.exit(run_diagnostics_cli())
