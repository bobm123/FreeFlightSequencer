"""
Connection Panel Widget - Reusable connection control widget.
Provides standard connection interface for all tabs.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os


class ConnectionPanel:
    """Reusable connection control panel widget."""
    
    def __init__(self, parent, serial_monitor, on_connect_callback=None):
        self.parent = parent
        self.serial_monitor = serial_monitor
        self.on_connect_callback = on_connect_callback
        self.connected = False
        
        # Create the connection frame
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
    def _create_widgets(self):
        """Create connection control widgets."""
        # Port selection
        ttk.Label(self.frame, text="Port:").pack(side='left')
        self.port_var = tk.StringVar(value=os.environ.get('ARDUINO_PORT', 'COM4'))
        port_entry = ttk.Entry(self.frame, textvariable=self.port_var, width=10)
        port_entry.pack(side='left', padx=5)
        
        # Connect button
        self.connect_btn = ttk.Button(self.frame, text="Connect", command=self._toggle_connection)
        self.connect_btn.pack(side='left', padx=5)
        
        # Status indicator
        self.status_label = ttk.Label(self.frame, text="Disconnected", foreground="red")
        self.status_label.pack(side='left', padx=10)
        
        # Auto-detect button
        self.detect_btn = ttk.Button(self.frame, text="Auto-Detect", command=self._auto_detect)
        self.detect_btn.pack(side='left', padx=5)
        
    def _toggle_connection(self):
        """Toggle serial connection."""
        if not self.connected:
            port = self.port_var.get().strip()
            if not port:
                messagebox.showerror("Error", "Please enter a port name")
                return
                
            if self.serial_monitor.connect(port):
                self.connected = True
                self.connect_btn.config(text="Disconnect")
                self.status_label.config(text=f"Connected to {port}", foreground="green")
                
                # Notify callback
                if self.on_connect_callback:
                    self.on_connect_callback(True, port)
            else:
                messagebox.showerror("Connection Error", 
                                   f"Failed to connect to {port}\\n{self.serial_monitor.last_error}")
        else:
            self.serial_monitor.disconnect()
            self.connected = False
            self.connect_btn.config(text="Connect")
            self.status_label.config(text="Disconnected", foreground="red")
            
            # Notify callback
            if self.on_connect_callback:
                self.on_connect_callback(False, None)
                
    def _auto_detect(self):
        """Auto-detect Arduino port."""
        try:
            import serial.tools.list_ports
            
            # Look for Arduino-like devices
            arduino_ports = []
            for port in serial.tools.list_ports.comports():
                # Common Arduino VID/PID patterns
                if any(keyword in (port.description or "").lower() for keyword in 
                      ['arduino', 'ch340', 'cp210', 'ftdi', 'usb serial']):
                    arduino_ports.append(port.device)
                    
            if arduino_ports:
                # Use first detected port
                self.port_var.set(arduino_ports[0])
                messagebox.showinfo("Auto-Detect", 
                                  f"Found Arduino on {arduino_ports[0]}\\n"
                                  f"Click Connect to establish connection.")
            else:
                messagebox.showwarning("Auto-Detect", 
                                     "No Arduino devices detected.\\n"
                                     "Please check connections and try manual port entry.")
        except ImportError:
            messagebox.showerror("Auto-Detect", 
                               "pyserial not available for auto-detection.\\n"
                               "Please enter port manually.")
        except Exception as e:
            messagebox.showerror("Auto-Detect Error", f"Detection failed: {e}")
            
    def pack(self, **kwargs):
        """Pack the connection panel frame."""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the connection panel frame."""
        self.frame.grid(**kwargs)
        
    def is_connected(self):
        """Check if currently connected."""
        return self.connected
        
    def get_port(self):
        """Get current port setting."""
        return self.port_var.get().strip()
        
    def set_status(self, message, color="black"):
        """Set custom status message."""
        self.status_label.config(text=message, foreground=color)