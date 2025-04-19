"""
Helper script to fix the chat window issue in chat_panel.py
"""
import re
import os

def fix_chat_panel():
    # Path to the original chat panel file
    file_path = os.path.join('ui', 'chat_panel.py')
    
    # Read the original file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the load_chat_history method
    pattern_load_history = r'def load_chat_history\(self\):[^\n]*\n\s+"""[^"]*"""\s+# Clear the console first\s+self\.console\.delete\(1\.0, tk\.END\)'
    replacement_load_history = """def load_chat_history(self):
        \"\"\"Load and display chat history\"\"\"
        # Enable text insertion
        self.console.config(state=tk.NORMAL)
        
        # Clear the console first
        self.console.delete(1.0, tk.END)"""
    
    content = re.sub(pattern_load_history, replacement_load_history, content)
    
    # Fix the apply_system_prompt method if it modifies the console
    pattern_system_prompt = r'# Show in console\s+self\.console\.insert\('
    replacement_system_prompt = """# Enable text insertion
        self.console.config(state=tk.NORMAL)
        
        # Show in console
        self.console.insert("""
    
    content = re.sub(pattern_system_prompt, replacement_system_prompt, content)
    
    # Add disable statement after console.see in apply_system_prompt
    pattern_system_see = r'self\.console\.see\(tk\.END\)'
    replacement_system_see = """self.console.see(tk.END)
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)"""
    
    content = re.sub(pattern_system_see, replacement_system_see, content)
    
    # Check for clear_console method and fix it if it exists
    pattern_clear_console = r'def clear_console\(self[^\)]*\):[^\n]*\n\s+[^#]*# Clear the console\s+self\.console\.delete\('
    replacement_clear_console = """def clear_console(self):
        \"\"\"Clear the console display\"\"\"
        # Enable text insertion
        self.console.config(state=tk.NORMAL)
        
        # Clear the console
        self.console.delete("""
    
    content = re.sub(pattern_clear_console, replacement_clear_console, content)
    
    # Add disable statement at the end of clear_console if it exists
    pattern_clear_end = r'def clear_console\([^}]+?self\.log\(["\']'
    replacement_clear_end = """def clear_console(self):
        \"\"\"Clear the console display\"\"\"
        # Enable text insertion
        self.console.config(state=tk.NORMAL)
        
        # Clear the console
        self.console.delete(1.0, tk.END)
        
        # Make console read-only again
        self.console.config(state=tk.DISABLED)
        
        self.log(\"\"\""""
    
    content = re.sub(pattern_clear_end, replacement_clear_end, content)
    
    # Save the fixed content to a new file
    backup_path = file_path + '.bak'
    os.rename(file_path, backup_path)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed chat_panel.py. Original file backed up to {backup_path}")

if __name__ == "__main__":
    fix_chat_panel()
