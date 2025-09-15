"""
Simple GUI for FlightSequencer Serial Monitor.
Basic parameter configuration with serial output display.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.communication.simple_serial import SimpleSerialMonitor
from src.core.parameter_monitor import ParameterMonitor


class FlightSequencerGUI:
    """Simple GUI for FlightSequencer parameter configuration and monitoring."""

    def __init__(self):
        self.serial_monitor = SimpleSerialMonitor()
        self.param_monitor = ParameterMonitor()
        self.connected = False

        # Create main window
        self.root = tk.Tk()
        self.root.title("FlightSequencer Control")
        self.root.geometry("800x600")

        # Create GUI elements
        self._create_widgets()

        # Set up serial callback
        self.serial_monitor.set_receive_callback(self._handle_serial_data)

    def _create_widgets(self):
        """Create and layout GUI widgets."""

        # Connection frame
        conn_frame = ttk.Frame(self.root)
        conn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(conn_frame, text="Port:").pack(side='left')
        self.port_var = tk.StringVar(value=os.environ.get('ARDUINO_PORT', 'COM4'))
        port_entry = ttk.Entry(conn_frame, textvariable=self.port_var, width=10)
        port_entry.pack(side='left', padx=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self._toggle_connection)
        self.connect_btn.pack(side='left', padx=5)

        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side='left', padx=10)

        # Main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Left panel - Parameter Controls
        self._create_parameter_panel(main_frame)

        # Right panel - Serial Monitor
        self._create_serial_panel(main_frame)

    def _create_parameter_panel(self, parent):
        """Create parameter configuration panel."""
        param_frame = ttk.LabelFrame(parent, text="Flight Parameters")
        param_frame.pack(side='left', fill='y', padx=(0, 5))

        # Motor Run Time
        ttk.Label(param_frame, text="Motor Run Time (sec):").pack(anchor='w', padx=5, pady=2)
        self.motor_time_var = tk.StringVar(value="20")
        motor_frame = ttk.Frame(param_frame)
        motor_frame.pack(fill='x', padx=5, pady=2)
        ttk.Entry(motor_frame, textvariable=self.motor_time_var, width=10).pack(side='left')
        ttk.Button(motor_frame, text="Set", command=self._set_motor_time).pack(side='left', padx=2)

        # Total Flight Time
        ttk.Label(param_frame, text="Total Flight Time (sec):").pack(anchor='w', padx=5, pady=2)
        self.flight_time_var = tk.StringVar(value="120")
        flight_frame = ttk.Frame(param_frame)
        flight_frame.pack(fill='x', padx=5, pady=2)
        ttk.Entry(flight_frame, textvariable=self.flight_time_var, width=10).pack(side='left')
        ttk.Button(flight_frame, text="Set", command=self._set_flight_time).pack(side='left', padx=2)

        # Motor Speed
        ttk.Label(param_frame, text="Motor Speed (95-200):").pack(anchor='w', padx=5, pady=2)
        self.motor_speed_var = tk.StringVar(value="150")
        speed_frame = ttk.Frame(param_frame)
        speed_frame.pack(fill='x', padx=5, pady=2)
        ttk.Entry(speed_frame, textvariable=self.motor_speed_var, width=10).pack(side='left')
        ttk.Button(speed_frame, text="Set", command=self._set_motor_speed).pack(side='left', padx=2)

        # Action buttons
        ttk.Separator(param_frame, orient='horizontal').pack(fill='x', padx=5, pady=10)

        ttk.Button(param_frame, text="Get Parameters", command=self._get_parameters).pack(fill='x', padx=5, pady=2)
        ttk.Button(param_frame, text="Reset to Defaults", command=self._reset_parameters).pack(fill='x', padx=5, pady=2)

        # Current parameters display
        ttk.Separator(param_frame, orient='horizontal').pack(fill='x', padx=5, pady=10)
        ttk.Label(param_frame, text="Current Parameters:", font=('TkDefaultFont', 9, 'bold')).pack(anchor='w', padx=5)

        self.current_params_text = tk.Text(param_frame, height=6, width=25, state='disabled')
        self.current_params_text.pack(fill='x', padx=5, pady=2)

    def _create_serial_panel(self, parent):
        """Create serial monitor panel."""
        serial_frame = ttk.LabelFrame(parent, text="Serial Monitor")
        serial_frame.pack(side='right', fill='both', expand=True)

        # Serial output display
        self.serial_output = scrolledtext.ScrolledText(serial_frame, height=25, width=50, state='disabled')
        self.serial_output.pack(fill='both', expand=True, padx=5, pady=5)

        # Command input
        cmd_frame = ttk.Frame(serial_frame)
        cmd_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(cmd_frame, text="Command:").pack(side='left')
        self.command_var = tk.StringVar()
        cmd_entry = ttk.Entry(cmd_frame, textvariable=self.command_var)
        cmd_entry.pack(side='left', fill='x', expand=True, padx=5)
        cmd_entry.bind('<Return>', self._send_command)

        ttk.Button(cmd_frame, text="Send", command=self._send_command).pack(side='right')

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
                self._log_to_serial(f"Connected to {port}\n")
            else:
                messagebox.showerror("Connection Error",
                                   f"Failed to connect to {port}\n{self.serial_monitor.last_error}")
        else:
            self.serial_monitor.disconnect()
            self.connected = False
            self.connect_btn.config(text="Connect")
            self.status_label.config(text="Disconnected", foreground="red")
            self._log_to_serial("Disconnected\n")

    def _handle_serial_data(self, data):
        """Handle data received from serial port."""
        # Update parameter monitor
        self.param_monitor.process_serial_data(data)

        # Display in serial monitor
        self._log_to_serial(data)

        # Update current parameters display
        self._update_current_params()

    def _log_to_serial(self, text):
        """Add text to serial output display."""
        def update_display():
            self.serial_output.config(state='normal')
            self.serial_output.insert(tk.END, text)
            self.serial_output.see(tk.END)
            self.serial_output.config(state='disabled')

        # Use after() to update GUI from any thread
        self.root.after(0, update_display)

    def _update_current_params(self):
        """Update the current parameters display."""
        def update_params():
            params = self.param_monitor.get_parameters()

            self.current_params_text.config(state='normal')
            self.current_params_text.delete(1.0, tk.END)

            if params:
                if 'motor_run_time' in params:
                    self.current_params_text.insert(tk.END, f"Motor Time: {params['motor_run_time']}s\n")
                if 'total_flight_time' in params:
                    self.current_params_text.insert(tk.END, f"Flight Time: {params['total_flight_time']}s\n")
                if 'motor_speed' in params:
                    speed = params['motor_speed']
                    self.current_params_text.insert(tk.END, f"Motor Speed: {speed}\n({speed * 10}µs PWM)\n")
            else:
                self.current_params_text.insert(tk.END, "No parameters\nreceived yet")

            self.current_params_text.config(state='disabled')

        self.root.after(0, update_params)

    def _set_motor_time(self):
        """Set motor run time."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            return

        try:
            time_val = self.motor_time_var.get().strip()
            command = f"M {time_val}"
            self.serial_monitor.send_line(command)
            self._log_to_serial(f"Sent: {command}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {e}")

    def _set_flight_time(self):
        """Set total flight time."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            return

        try:
            time_val = self.flight_time_var.get().strip()
            command = f"T {time_val}"
            self.serial_monitor.send_line(command)
            self._log_to_serial(f"Sent: {command}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {e}")

    def _set_motor_speed(self):
        """Set motor speed."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            return

        try:
            speed_val = self.motor_speed_var.get().strip()
            command = f"S {speed_val}"
            self.serial_monitor.send_line(command)
            self._log_to_serial(f"Sent: {command}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {e}")

    def _get_parameters(self):
        """Get current parameters from Arduino."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            return

        self.serial_monitor.send_line("G")
        self._log_to_serial("Sent: G\n")

    def _reset_parameters(self):
        """Reset parameters to defaults."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            return

        if messagebox.askyesno("Reset Parameters", "Reset all parameters to factory defaults?"):
            self.serial_monitor.send_line("R")
            self._log_to_serial("Sent: R\n")

    def _send_command(self, event=None):
        """Send custom command to Arduino."""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            return

        command = self.command_var.get().strip()
        if command:
            self.serial_monitor.send_line(command)
            self._log_to_serial(f"Sent: {command}\n")
            self.command_var.set("")

    def run(self):
        """Start the GUI application."""
        try:
            self.root.mainloop()
        finally:
            if self.connected:
                self.serial_monitor.disconnect()


def main():
    """Main entry point for GUI application."""
    app = FlightSequencerGUI()
    app.run()


if __name__ == '__main__':
    main()