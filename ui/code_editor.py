"""
Enhanced code editor with syntax highlighting and additional features
"""
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, font, messagebox, simpledialog
from tkinter.font import Font
from typing import Callable, Optional, Dict, List, Tuple, Any
import logging
import os

from core.component import Component

logger = logging.getLogger(__name__)

class CodeEditorFrame(ttk.LabelFrame):
    """Frame containing the code editor with enhanced features"""
    
    def __init__(self, parent, app, **kwargs):
        """Initialize the code editor frame"""
        super().__init__(parent, text="Code Editor", **kwargs)
        self.app = app
        self.current_component = None
        self.unsaved_changes = False
        
        self.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create editor with line numbers
        self.create_editor()
        
        # Create editor toolbar
        self.create_toolbar()
        
        # Create search panel (initially hidden)
        self.search_panel = SearchReplacePanel(self, self.code_text)
        
        # Setup syntax highlighting
        self.syntax_highlighter = SyntaxHighlighter(self.code_text)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
    
    def create_editor(self):
        """Create the text editor with line numbers"""
        editor_frame = ttk.Frame(self)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a custom font
        editor_font = Font(family="Courier", size=10)
        
        # Create text widget with scrollbars first
        editor_text_frame = ttk.Frame(editor_frame)
        editor_text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.code_text = scrolledtext.ScrolledText(
            editor_text_frame,
            wrap=tk.NONE,
            font=editor_font,
            undo=True,  # Enable undo/redo
            maxundo=100,  # Number of undo levels
            autoseparators=True  # Automatically add separators for undo
        )
        self.code_text.pack(fill=tk.BOTH, expand=True)
        
        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(editor_text_frame, orient=tk.HORIZONTAL, command=self.code_text.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.code_text.config(xscrollcommand=h_scrollbar.set)
        
        # Now create the line numbers widget with text_widget parameter
        self.line_numbers = LineNumbers(
            editor_frame, 
            text_widget=self.code_text,  # Pass the text widget reference
            width=30, 
            bg="#f0f0f0", 
            highlightthickness=0
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Setup change tracking
        self.code_text.bind("<<Modified>>", self.on_text_modified)
        self.code_text.bind("<Key>", self.on_key_press)
        
    def create_toolbar(self):
        """Create the editor toolbar with buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Save button
        save_button = ttk.Button(
            toolbar, text="Save", command=self.save_changes, width=10
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Find button
        find_button = ttk.Button(
            toolbar, text="Find/Replace", command=self.show_search_panel, width=15
        )
        find_button.pack(side=tk.LEFT, padx=5)
        
        # Format code button
        format_button = ttk.Button(
            toolbar, text="Format Code", command=self.format_code, width=15
        )
        format_button.pack(side=tk.LEFT, padx=5)
        
        # Tab size selector
        ttk.Label(toolbar, text="Tab Size:").pack(side=tk.LEFT, padx=(10, 0))
        self.tab_size_var = tk.StringVar(value="2")
        tab_size_combo = ttk.Combobox(
            toolbar, textvariable=self.tab_size_var, values=["2", "4", "8"], width=3
        )
        tab_size_combo.pack(side=tk.LEFT, padx=5)
        tab_size_combo.bind("<<ComboboxSelected>>", self.set_tab_size)
        
        # Status indicators on the right
        self.status_frame = ttk.Frame(toolbar)
        self.status_frame.pack(side=tk.RIGHT, padx=5)
        
        # Unsaved changes indicator
        self.unsaved_indicator = ttk.Label(self.status_frame, text="●", foreground="gray")
        self.unsaved_indicator.pack(side=tk.RIGHT, padx=5)
        
        # Component name indicator
        self.component_name_label = ttk.Label(self.status_frame, text="No component selected")
        self.component_name_label.pack(side=tk.RIGHT, padx=5)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for the editor"""
        # Ctrl+S: Save
        self.code_text.bind("<Control-s>", lambda e: self.save_changes())
        
        # Ctrl+F: Find
        self.code_text.bind("<Control-f>", lambda e: self.show_search_panel())
        
        # Ctrl+Z: Undo
        self.code_text.bind("<Control-z>", lambda e: self.code_text.edit_undo())
        
        # Ctrl+Y: Redo
        self.code_text.bind("<Control-y>", lambda e: self.code_text.edit_redo())
        
        # Tab key: Insert spaces
        self.code_text.bind("<Tab>", self.handle_tab)
        
        # Shift+Tab: Remove indent
        self.code_text.bind("<Shift-Tab>", self.handle_shift_tab)
        
        # Auto-indent after newline
        self.code_text.bind("<Return>", self.handle_return)
        
        # Auto close brackets and quotes
        for char, closing in [("(", ")"), ("[", "]"), ("{", "}"), ('"', '"'), ("'", "'")]:
            self.code_text.bind(f"<KeyPress-{char}>", lambda e, c=closing: self.auto_close_char(e, c))
    
    def show_search_panel(self):
        """Show the search and replace panel"""
        self.search_panel.show()
    
    def load_component(self, component: Component):
        """Load a component into the editor"""
        if self.unsaved_changes:
            if not messagebox.askyesno("Unsaved Changes", 
                                    "You have unsaved changes. Discard them?"):
                return False
        
        self.current_component = component
        
        # Load content
        try:
            # Try using read_content() method if it exists
            if hasattr(component, 'read_content'):
                content = component.read_content()
            # Fall back to loading content attribute directly
            elif hasattr(component, 'content'):
                content = component.content
                # If content is None, try loading from file
                if content is None and hasattr(component, 'load_content'):
                    content = component.load_content()
            # As a last resort, try reading directly from file
            else:
                with open(component.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            self.code_text.delete('1.0', tk.END)
            self.code_text.insert('1.0', content)
            self.component_name_label.config(text=component.name)
            self.set_unsaved(False)
            self.syntax_highlighter.highlight()
            return True
        except Exception as e:
            logger.error(f"Error loading component {component.name}: {e}")
            messagebox.showerror("Error", f"Failed to load component: {e}")
            return False
        
    def save_changes(self):
        """Save changes to the current component"""
        if not self.current_component:
            return False
        
        try:
            content = self.code_text.get('1.0', 'end-1c')  # Get text without final newline
            self.current_component.save_content(content)
            self.set_unsaved(False)
            self.app.set_status(f"Saved: {self.current_component.name}")
            return True
        except Exception as e:
            logger.error(f"Error saving component {self.current_component.name}: {e}")
            messagebox.showerror("Error", f"Failed to save component: {e}")
            return False
    
    def format_code(self):
        """Format the code in the editor"""
        if not self.current_component:
            return
        
        try:
            # Get current content
            content = self.code_text.get('1.0', 'end-1c')
            
            # Backup cursor position
            cursor_pos = self.code_text.index(tk.INSERT)
            
            # Try to format with external formatter if available
            # This is a placeholder - in a real implementation, you would use a proper
            # formatter like prettier. For now, we'll use a simple approach
            formatted_content = self.simple_format(content)
            
            # Update text
            self.code_text.delete('1.0', tk.END)
            self.code_text.insert('1.0', formatted_content)
            
            # Try to restore cursor position
            try:
                self.code_text.mark_set(tk.INSERT, cursor_pos)
            except:
                pass  # If position no longer exists
            
            # Update highlighting
            self.syntax_highlighter.highlight()
            
            self.set_unsaved(True)
            self.app.set_status("Code formatted")
        except Exception as e:
            logger.error(f"Error formatting code: {e}")
            messagebox.showerror("Error", f"Failed to format code: {e}")
    
    def simple_format(self, content: str) -> str:
        """Simple formatting for TSX/JSX code"""
        lines = content.split('\n')
        formatted_lines = []
        indent_level = 0
        in_multiline_comment = False
        
        for line in lines:
            # Trim trailing whitespace
            trimmed = line.rstrip()
            
            # Skip empty lines
            if not trimmed:
                formatted_lines.append('')
                continue
            
            # Handle multiline comments
            if in_multiline_comment:
                formatted_lines.append('  ' * indent_level + trimmed)
                if '*/' in trimmed:
                    in_multiline_comment = False
                continue
            
            if '/*' in trimmed and '*/' not in trimmed:
                in_multiline_comment = True
                formatted_lines.append('  ' * indent_level + trimmed)
                continue
            
            # Adjust indent for closing brackets
            if any(c in trimmed for c in [')', '}', ']', '/>']) and not trimmed.strip().startswith((')', '}', ']', '/>')): 
                if not any(trimmed.strip().startswith(c) for c in ['if', 'else', 'for', 'while', 'switch', 'function']):
                    indent_level = max(0, indent_level - 1)
            
            # Add the line with proper indentation
            formatted_lines.append('  ' * indent_level + trimmed)
            
            # Adjust indent for opening brackets
            if any(c in trimmed for c in ['(', '{', '[', '<']) and not any(c in trimmed for c in ['</', '/>']): 
                if not any(c+'>' in trimmed for c in ['<img', '<br', '<input']):
                    indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def set_unsaved(self, unsaved: bool):
        """Set the unsaved changes status and update indicator"""
        self.unsaved_changes = unsaved
        if unsaved:
            self.unsaved_indicator.config(text="●", foreground="red")
        else:
            self.unsaved_indicator.config(text="●", foreground="gray")
    
    def set_tab_size(self, event=None):
        """Set the tab size based on the dropdown selection"""
        try:
            tab_size = int(self.tab_size_var.get())
            spaces = ' ' * tab_size
            # Configure tab size in the editor
            self.code_text.config(tabs=(font.Font(font=self.code_text['font']).measure(spaces),))
        except:
            pass  # Handle invalid input
    
    def handle_tab(self, event):
        """Handle tab key press - insert spaces"""
        try:
            tab_size = int(self.tab_size_var.get())
        except:
            tab_size = 2
            
        self.code_text.insert(tk.INSERT, ' ' * tab_size)
        return 'break'  # Prevent default tab behavior
    
    def handle_shift_tab(self, event):
        """Handle shift+tab to remove indentation"""
        try:
            tab_size = int(self.tab_size_var.get())
        except:
            tab_size = 2
            
        # Get current line
        line_start = self.code_text.index(f"{tk.INSERT} linestart")
        line_text = self.code_text.get(line_start, f"{tk.INSERT} lineend")
        
        # Count leading spaces
        leading_spaces = len(line_text) - len(line_text.lstrip(' '))
        
        # Remove up to tab_size spaces from the beginning
        if leading_spaces > 0:
            spaces_to_remove = min(leading_spaces, tab_size)
            self.code_text.delete(line_start, f"{line_start}+{spaces_to_remove}c")
            
        return 'break'  # Prevent default behavior
    
    def handle_return(self, event):
        """Auto-indent after newline"""
        # Get current line
        current_line = self.code_text.get("insert linestart", "insert")
        
        # Insert newline
        self.code_text.insert(tk.INSERT, '\n')
        
        # Count leading spaces
        leading_spaces = len(current_line) - len(current_line.lstrip())
        
        # Add indent
        if leading_spaces > 0:
            self.code_text.insert(tk.INSERT, ' ' * leading_spaces)
        
        # Extra indent after opening bracket
        if current_line.rstrip().endswith(('(', '{', '[')):
            try:
                tab_size = int(self.tab_size_var.get())
            except:
                tab_size = 2
            self.code_text.insert(tk.INSERT, ' ' * tab_size)
            
        return 'break'  # Prevent default return behavior
    
    def auto_close_char(self, event, closing_char):
        """Auto-close brackets and quotes"""
        self.code_text.insert(tk.INSERT, closing_char)
        self.code_text.mark_set(tk.INSERT, f"{tk.INSERT}-1c")  # Move cursor back
        return 'break'  # Prevent default behavior
    
    def on_text_modified(self, event):
        """Handle text modified event"""
        if self.code_text.edit_modified():
            self.set_unsaved(True)
            self.code_text.edit_modified(False)  # Reset the modified flag
    
    def on_key_press(self, event):
        """Handle key press events"""
        # This is called for every key press
        # We can use it to trigger syntax highlighting with some throttling
        if hasattr(self, '_highlight_after_id'):
            self.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.after(500, self.syntax_highlighter.highlight)


class LineNumbers(tk.Canvas):
    """Canvas widget for displaying line numbers"""
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.text_widget.bind('<<Change>>', self.redraw)
        self.text_widget.bind('<Configure>', self.redraw)
        self.redraw()
    
    def redraw(self, *args):
        """Redraw the line numbers"""
        self.delete("all")
        
        # Get visible line range
        first_line = self.text_widget.index("@0,0").split('.')[0]
        last_line = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}").split('.')[0]
        
        for line_num in range(int(first_line), int(last_line) + 1):
            # Get y-coordinate of line
            y_coord = self.text_widget.dlineinfo(f"{line_num}.0")
            if y_coord:
                self.create_text(
                    2, y_coord[1], 
                    anchor="nw", 
                    text=str(line_num), 
                    fill="#606060", 
                    font=self.text_widget['font']
                )


class SearchReplacePanel(ttk.Frame):
    """Panel for search and replace functionality"""
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.search_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.matches = []
        self.current_match = -1
        
        # Search frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(search_frame, text="Find:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", self.search)
        self.search_entry.bind("<KeyRelease>", self.live_search)
        
        ttk.Button(search_frame, text="Next", command=self.next_match).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Prev", command=self.prev_match).pack(side=tk.LEFT, padx=5)
        
        # Replace frame
        replace_frame = ttk.Frame(self)
        replace_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(replace_frame, text="Replace:").pack(side=tk.LEFT)
        self.replace_entry = ttk.Entry(replace_frame, textvariable=self.replace_var)
        self.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(replace_frame, text="Replace", command=self.replace_current).pack(side=tk.LEFT, padx=5)
        ttk.Button(replace_frame, text="Replace All", command=self.replace_all).pack(side=tk.LEFT, padx=5)
        
        # Options frame
        options_frame = ttk.Frame(self)
        options_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive_var,
                       command=self.search).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(options_frame, text="")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Close button
        ttk.Button(self, text="✕", width=2, command=self.hide).pack(side=tk.RIGHT, padx=5)
    
    def show(self):
        """Show the search panel"""
        self.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        self.search_entry.focus_set()
        self.text_widget.tag_configure('search_highlight', background='yellow')
        self.text_widget.tag_configure('current_match', background='orange')
    
    def hide(self):
        """Hide the search panel"""
        self.pack_forget()
        # Remove highlights
        self.text_widget.tag_remove('search_highlight', '1.0', 'end')
        self.text_widget.tag_remove('current_match', '1.0', 'end')
    
    def live_search(self, event=None):
        """Perform search as user types"""
        if len(self.search_var.get()) >= 2:  # Only search if at least 2 chars
            self.search()
    
    def search(self, event=None):
        """Search for text in the editor"""
        search_text = self.search_var.get()
        if not search_text:
            return
        
        # Remove existing highlights
        self.text_widget.tag_remove('search_highlight', '1.0', 'end')
        self.text_widget.tag_remove('current_match', '1.0', 'end')
        
        self.matches = []
        self.current_match = -1
        
        text_content = self.text_widget.get('1.0', 'end-1c')
        
        if not self.case_sensitive_var.get():
            text_content = text_content.lower()
            search_text = search_text.lower()
        
        start_idx = 0
        while True:
            match_idx = text_content.find(search_text, start_idx)
            if match_idx == -1:
                break
            
            line_idx = text_content.count('\n', 0, match_idx)
            char_idx = match_idx - text_content.rfind('\n', 0, match_idx) - 1
            if char_idx < 0:  # Handle match at the beginning of line
                char_idx = match_idx
                if line_idx > 0:  # Adjust for all previous lines
                    for i in range(line_idx):
                        prev_newline = text_content.rfind('\n', 0, match_idx - i)
                        if prev_newline != -1:
                            match_idx = prev_newline + 1
            
            start_pos = f"{line_idx + 1}.{char_idx}"
            end_pos = f"{line_idx + 1}.{char_idx + len(search_text)}"
            
            self.matches.append((start_pos, end_pos))
            self.text_widget.tag_add('search_highlight', start_pos, end_pos)
            
            start_idx = match_idx + len(search_text)
        
        # Update status
        match_count = len(self.matches)
        self.status_label.config(text=f"{match_count} matches" if match_count else "No matches")
        
        # Go to first match if any
        if self.matches:
            self.next_match()
    
    def next_match(self):
        """Go to next match"""
        if not self.matches:
            return
            
        # Remove current highlight
        self.text_widget.tag_remove('current_match', '1.0', 'end')
        
        # Go to next match
        self.current_match = (self.current_match + 1) % len(self.matches)
        start_pos, end_pos = self.matches[self.current_match]
        
        # Highlight and scroll to match
        self.text_widget.tag_add('current_match', start_pos, end_pos)
        self.text_widget.see(start_pos)
        self.text_widget.mark_set('insert', start_pos)
        
        # Update status
        self.status_label.config(text=f"Match {self.current_match + 1} of {len(self.matches)}")
    
    def prev_match(self):
        """Go to previous match"""
        if not self.matches:
            return
            
        # Remove current highlight
        self.text_widget.tag_remove('current_match', '1.0', 'end')
        
        # Go to previous match
        self.current_match = (self.current_match - 1) % len(self.matches)
        start_pos, end_pos = self.matches[self.current_match]
        
        # Highlight and scroll to match
        self.text_widget.tag_add('current_match', start_pos, end_pos)
        self.text_widget.see(start_pos)
        self.text_widget.mark_set('insert', start_pos)
        
        # Update status
        self.status_label.config(text=f"Match {self.current_match + 1} of {len(self.matches)}")
    
    def replace_current(self):
        """Replace the current match"""
        if not self.matches or self.current_match < 0:
            return
            
        start_pos, end_pos = self.matches[self.current_match]
        self.text_widget.delete(start_pos, end_pos)
        self.text_widget.insert(start_pos, self.replace_var.get())
        
        # Update search to refresh matches
        self.search()
    
    def replace_all(self):
        """Replace all matches"""
        if not self.matches:
            return
            
        search_text = self.search_var.get()
        replace_text = self.replace_var.get()
        
        if messagebox.askyesno("Replace All", 
                           f"Replace all {len(self.matches)} occurrences of '{search_text}' with '{replace_text}'?"):
            # Replacing from end to start to avoid index problems
            for start_pos, end_pos in reversed(self.matches):
                self.text_widget.delete(start_pos, end_pos)
                self.text_widget.insert(start_pos, replace_text)
            
            # Update search
            self.search()


class SyntaxHighlighter:
    """Class for providing syntax highlighting in the code editor"""
    
    def __init__(self, text_widget):
        """Initialize the syntax highlighter"""
        self.text_widget = text_widget
        self.setup_tags()
        self.line_comment_pattern = r'//.*'
        
        # Bind events
        self.text_widget.bind('<KeyRelease>', self.highlight)
        self.text_widget.bind('<FocusIn>', self.highlight)
    
    def setup_tags(self):
        """Set up tag styles for different syntax elements"""
        # Configure tags with colors and styles
        self.text_widget.tag_configure('comment', foreground='#6A9955')
        self.text_widget.tag_configure('string', foreground='#CE9178')
        self.text_widget.tag_configure('keyword', foreground='#569CD6', font=('Courier', 10, 'bold'))
        self.text_widget.tag_configure('number', foreground='#B5CEA8')
        self.text_widget.tag_configure('jsx_tag', foreground='#D7BA7D')
        self.text_widget.tag_configure('prop', foreground='#9CDCFE')
        self.text_widget.tag_configure('react_hook', foreground='#C586C0', font=('Courier', 10, 'bold'))
    
    def clear_tags(self, start='1.0', end='end'):
        """Clear all syntax highlighting tags"""
        for tag in ['comment', 'string', 'keyword', 'number', 'jsx_tag', 'prop', 'react_hook']:
            self.text_widget.tag_remove(tag, start, end)
    
    def highlight(self, event=None):
        """Apply syntax highlighting to the text"""
        # Clear existing tags
        self.clear_tags()
        
        # Get the text content
        content = self.text_widget.get('1.0', 'end-1c')
        
        # Apply highlighting for different patterns
        self.apply_regex_highlight(content, self.line_comment_pattern, 'comment', is_multiline=True)
        self.apply_regex_highlight(content, self.block_comment_pattern, 'comment', is_multiline=True)
        self.apply_regex_highlight(content, self.string_pattern, 'string', is_multiline=True)
        self.apply_regex_highlight(content, self.jsx_tag_pattern, 'jsx_tag', is_multiline=True)
        self.apply_regex_highlight(content, self.keyword_pattern, 'keyword')
        self.apply_regex_highlight(content, self.number_pattern, 'number')
        self.apply_regex_highlight(content, self.prop_pattern, 'prop', group=1)
        self.apply_regex_highlight(content, self.react_hook_pattern, 'react_hook')
    
    def apply_regex_highlight(self, content, pattern, tag_name, group=0, is_multiline=False):
        """Apply highlighting based on regex pattern"""
        if is_multiline:
            # Use finditer for multiline patterns
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                start_idx = match.start(group) if group < len(match.groups())+1 else match.start()
                end_idx = match.end(group) if group < len(match.groups())+1 else match.end()
                
                # Convert string indices to tkinter text indices
                start_line = content.count('\n', 0, start_idx) + 1
                start_col = start_idx - content.rfind('\n', 0, start_idx) - 1
                if start_col < 0:  # Handle match at start of line
                    start_col = 0
                
                end_line = content.count('\n', 0, end_idx) + 1
                end_col = end_idx - content.rfind('\n', 0, end_idx) - 1
                if end_col < 0:  # Handle match at start of line
                    end_col = 0
                
                start_pos = f"{start_line}.{start_col}"
                end_pos = f"{end_line}.{end_col}"
                
                self.text_widget.tag_add(tag_name, start_pos, end_pos)
        else:
            # Use line-by-line approach for single-line patterns
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line_num = i + 1
                for match in re.finditer(pattern, line):
                    start_idx = match.start(group) if group < len(match.groups())+1 else match.start()
                    end_idx = match.end(group) if group < len(match.groups())+1 else match.end()
                    
                    start_pos = f"{line_num}.{start_idx}"
                    end_pos = f"{line_num}.{end_idx}"
                    
                    self.text_widget.tag_add(tag_name, start_pos, end_pos)
        self.block_comment_pattern = r'/\*.*?\*/'
        self.string_pattern = r'".*?"|\'.*?\''
        self.jsx_tag_pattern = r'<(\w+).*?>|</(\w+).*?>|<(\w+).*?/>'
        self.keyword_pattern = r'\b(import|from|export|default|const|let|var|function|class|extends|return|if|else|switch|case|for|while|do|try|catch|throw|new|this|super|async|await|static|get|set)\b'
        self.number_pattern = r'\b\d+\b|\b\d+\.\d+\b'
        self.prop_pattern = r'(\w+):'
        self.react_hook_pattern = r'\b(useState|useEffect|useContext|useReducer|useCallback|useMemo|useRef|useImperativeHandle|useLayoutEffect|useDebugValue)\b'
        
        # Bind events
        self.text_widget.bind('<KeyRelease>', self.highlight)
        self.text_widget.bind('<FocusIn>', self.highlight)
    
    def setup_tags(self):
        """Set up tag styles for different syntax elements"""
        # Configure tags with colors and styles
        self.text_widget.tag_configure('comment', foreground='#6A9955')
        self.text_widget.tag_configure('string', foreground='#CE9178')
        self.text_widget.tag_configure('keyword', foreground='#569CD6', font=('Courier', 10, 'bold'))
        self.text_widget.tag_configure('number', foreground='#B5CEA8')
        self.text_widget.tag_configure('jsx_tag', foreground='#D7BA7D')
        self.text_widget.tag_configure('prop', foreground='#9CDCFE')
    
    def clear_tags(self, start='1.0', end='end'):
        """Clear all syntax highlighting tags"""
        for tag in ['comment', 'string', 'keyword', 'number', 'jsx_tag', 'prop']:
            self.text_widget.tag_remove(tag, start, end)
    
    def highlight(self, event=None):
        """Apply syntax highlighting to the text"""
        # Clear existing tags
        self.clear_tags()
        
        # Get the text content
        content = self.text_widget.get('1.0', 'end-1c')
        
        # Apply highlighting for different patterns
        self.apply_regex_highlight(content, self.line_comment_pattern, 'comment', is_multiline=True)
        self.apply_regex_highlight(content, self.block_comment_pattern, 'comment', is_multiline=True)
        self.apply_regex_highlight(content, self.string_pattern, 'string', is_multiline=True)
        self.apply_regex_highlight(content, self.jsx_tag_pattern, 'jsx_tag', is_multiline=True)
        self.apply_regex_highlight(content, self.keyword_pattern, 'keyword')
        self.apply_regex_highlight(content, self.number_pattern, 'number')
        self.apply_regex_highlight(content, self.prop_pattern, 'prop', group=1)
    
    def apply_regex_highlight(self, content, pattern, tag_name, group=0, is_multiline=False):
        """Apply highlighting based on regex pattern"""
        if is_multiline:
            # Use finditer for multiline patterns
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                start_idx = match.start(group) if group < len(match.groups())+1 else match.start()
                end_idx = match.end(group) if group < len(match.groups())+1 else match.end()
                
                # Convert string indices to tkinter text indices
                start_line = content.count('\n', 0, start_idx) + 1
                start_col = start_idx - content.rfind('\n', 0, start_idx) - 1
                if start_col < 0:  # Handle match at start of line
                    start_col = 0
                
                end_line = content.count('\n', 0, end_idx) + 1
                end_col = end_idx - content.rfind('\n', 0, end_idx) - 1
                if end_col < 0:  # Handle match at start of line
                    end_col = 0
                
                start_pos = f"{start_line}.{start_col}"
                end_pos = f"{end_line}.{end_col}"
                
                self.text_widget.tag_add(tag_name, start_pos, end_pos)
        else:
            # Use line-by-line approach for single-line patterns
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line_num = i + 1
                for match in re.finditer(pattern, line):
                    start_idx = match.start(group) if group < len(match.groups())+1 else match.start()
                    end_idx = match.end(group) if group < len(match.groups())+1 else match.end()
                    
                    start_pos = f"{line_num}.{start_idx}"
                    end_pos = f"{line_num}.{end_idx}"
                    
                    self.text_widget.tag_add(tag_name, start_pos, end_pos)