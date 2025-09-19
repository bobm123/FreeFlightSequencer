"""
Serial Monitor Widget - Reusable serial output display widget.
Provides consistent serial monitoring interface across tabs.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time


class SerialMonitorWidget:
    """Reusable serial monitor display widget."""
    
    def __init__(self, parent, title="Serial Monitor", show_timestamp=True, 
                 max_lines=1000, show_command_input=True):
        self.parent = parent
        self.title = title
        self.show_timestamp = show_timestamp
        self.max_lines = max_lines
        self.show_command_input = show_command_input
        self.line_count = 0
        self.send_callback = None
        
        # Create the serial monitor frame
        self.frame = ttk.LabelFrame(parent, text=title)
        self._create_widgets()
        
    def _create_widgets(self):
        """Create serial monitor widgets."""
        # Serial output display
        self.output = scrolledtext.ScrolledText(
            self.frame, 
            height=20, 
            width=60, 
            state='disabled',
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.output.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configure text tags for colored output
        self.output.tag_configure("timestamp", foreground="gray")
        self.output.tag_configure("sent", foreground="blue")
        self.output.tag_configure("received", foreground="black") 
        self.output.tag_configure("error", foreground="red")
        self.output.tag_configure("warning", foreground="orange")
        self.output.tag_configure("success", foreground="green")
        
        if self.show_command_input:
            # Command input frame
            cmd_frame = ttk.Frame(self.frame)
            cmd_frame.pack(fill='x', padx=5, pady=5)
            
            ttk.Label(cmd_frame, text="Command:").pack(side='left')
            self.command_var = tk.StringVar()
            cmd_entry = ttk.Entry(cmd_frame, textvariable=self.command_var)
            cmd_entry.pack(side='left', fill='x', expand=True, padx=5)
            cmd_entry.bind('<Return>', self._send_command)
            
            ttk.Button(cmd_frame, text="Send", command=self._send_command).pack(side='right')
            
            # Quick command buttons frame
            quick_frame = ttk.Frame(self.frame)
            quick_frame.pack(fill='x', padx=5, pady=2)
            
            # Common commands
            ttk.Button(quick_frame, text="?", width=3, 
                      command=lambda: self._quick_send("?")).pack(side='left', padx=1)
            ttk.Button(quick_frame, text="G", width=3,
                      command=lambda: self._quick_send("G")).pack(side='left', padx=1)
            ttk.Button(quick_frame, text="Clear", 
                      command=self.clear).pack(side='right', padx=1)
                      
    def set_send_callback(self, callback):
        """Set callback function for sending commands."""
        self.send_callback = callback
        
    def _send_command(self, event=None):
        """Send command via callback."""
        command = self.command_var.get().strip()
        if command and self.send_callback:
            self.send_callback(command)
            self.log_sent(command)
            self.command_var.set("")
            
    def _quick_send(self, command):
        """Send a quick command."""
        if self.send_callback:
            self.send_callback(command)
            self.log_sent(command)
            
    def log_message(self, text, tag="received"):
        """Add message to serial output with optional tag."""
        def update_display():
            self.output.config(state='normal')
            
            # Add timestamp if enabled
            if self.show_timestamp:
                timestamp = time.strftime("[%H:%M:%S] ")
                self.output.insert(tk.END, timestamp, "timestamp")
                
            # Add the message
            self.output.insert(tk.END, text, tag)
            if not text.endswith('\n'):
                self.output.insert(tk.END, '\n', tag)
                
            # Limit number of lines
            self.line_count += 1
            if self.line_count > self.max_lines:
                # Remove oldest lines
                lines_to_remove = self.line_count - self.max_lines
                for _ in range(lines_to_remove):
                    self.output.delete(1.0, "2.0")
                self.line_count = self.max_lines
                
            self.output.see(tk.END)
            self.output.config(state='disabled')
            
        # Use after() for thread safety
        self.parent.after(0, update_display)
        
    def log_sent(self, command):
        """Log sent command."""
        self.log_message(f"Sent: {command}", "sent")
        
    def log_received(self, data):
        """Log received data."""
        self.log_message(data, "received")
        
    def log_error(self, message):
        """Log error message."""
        self.log_message(f"ERROR: {message}", "error")
        
    def log_warning(self, message):
        """Log warning message.""" 
        self.log_message(f"WARNING: {message}", "warning")
        
    def log_success(self, message):
        """Log success message."""
        self.log_message(f"SUCCESS: {message}", "success")
        
    def clear(self):
        """Clear the serial output display."""
        self.output.config(state='normal')
        self.output.delete(1.0, tk.END)
        self.output.config(state='disabled')
        self.line_count = 0
        
    def pack(self, **kwargs):
        """Pack the serial monitor frame."""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the serial monitor frame."""
        self.frame.grid(**kwargs)
        
    def get_frame(self):
        """Get the main frame widget."""
        return self.frame