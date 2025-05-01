"""
Console module for displaying application logs and messages
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import datetime
from typing import Optional
import queue
import threading
import logging

logger = logging.getLogger(__name__)

class ConsoleFrame(ttk.LabelFrame):
    """Frame containing the console output"""
    
    def __init__(self, parent, **kwargs):
        """Initialize the console frame"""
        super().__init__(parent, text="Console", **kwargs)
        self.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        # Message queue for thread safety
        self.message_queue = queue.Queue()
        
        # Create the console widget
        self.console_text = scrolledtext.ScrolledText(
            self, 
            wrap=tk.WORD, 
            height=6, 
            font=("Courier", 9),
            background="#f5f5f5"
        )
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console_text.config(state=tk.DISABLED)
        
        # Tag configurations
        self.console_text.tag_configure('info', foreground='#0066cc')
        self.console_text.tag_configure('success', foreground='#008800')
        self.console_text.tag_configure('warning', foreground='#cc7700')
        self.console_text.tag_configure('error', foreground='#cc0000')
        self.console_text.tag_configure('timestamp', foreground='#666666')
        
        # Create toolbar
        self.create_toolbar()
        
        # Start message processing
        self.process_messages()
    
    def create_toolbar(self):
        """Create the toolbar with console controls"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Clear button
        clear_button = ttk.Button(
            toolbar, text="Clear Console", command=self.clear_console
        )
        clear_button.pack(side=tk.LEFT)
        
        # Filter dropdown
        ttk.Label(toolbar, text="Show:").pack(side=tk.LEFT, padx=(10, 0))
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            toolbar, 
            textvariable=self.filter_var, 
            values=["All", "Info", "Success", "Warning", "Error"],
            width=10
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.apply_filter)
        
        # Auto-scroll checkbox
        self.autoscroll_var = tk.BooleanVar(value=True)
        autoscroll_check = ttk.Checkbutton(
            toolbar, 
            text="Auto-scroll", 
            variable=self.autoscroll_var
        )
        autoscroll_check.pack(side=tk.LEFT, padx=10)
    
    def add_message(self, message: str, level: str = 'info'):
        """
        Add a message to the console
        
        Args:
            message: The message to add
            level: Message level (info, success, warning, error)
        """
        # Put the message in the queue for thread-safe processing
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.message_queue.put((message, level, timestamp))
    
    def process_messages(self):
        """Process messages from the queue"""
        try:
            while not self.message_queue.empty():
                message, level, timestamp = self.message_queue.get_nowait()
                self._add_message_to_console(message, level, timestamp)
        except Exception as e:
            logger.error(f"Error processing console messages: {e}")
        
        # Schedule to run again
        self.after(100, self.process_messages)
    
    def _add_message_to_console(self, message: str, level: str, timestamp: str):
        """Add a message directly to the console widget"""
        self.console_text.config(state=tk.NORMAL)
        
        # Add timestamp
        self.console_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Add the message with appropriate tag
        self.console_text.insert(tk.END, f"{message}\n", level)
        
        # Auto-scroll if enabled
        if self.autoscroll_var.get():
            self.console_text.see(tk.END)
            
        self.console_text.config(state=tk.DISABLED)
    
    def clear_console(self):
        """Clear the console"""
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state=tk.DISABLED)
    
    def apply_filter(self, event=None):
        """Apply the selected filter to the console"""
        filter_value = self.filter_var.get()
        
        # Show all messages
        if filter_value == "All":
            self.console_text.tag_configure('info', elide=False)
            self.console_text.tag_configure('success', elide=False)
            self.console_text.tag_configure('warning', elide=False)
            self.console_text.tag_configure('error', elide=False)
            return
        
        # Show only selected level
        self.console_text.tag_configure('info', elide=filter_value != "Info")
        self.console_text.tag_configure('success', elide=filter_value != "Success")
        self.console_text.tag_configure('warning', elide=filter_value != "Warning")
        self.console_text.tag_configure('error', elide=filter_value != "Error")