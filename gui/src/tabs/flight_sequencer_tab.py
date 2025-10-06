"""
FlightSequencer Tab - Enhanced interface for FlightSequencer control.
Refactored from original simple_gui.py with additional features.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import re
import json
import os
import sys
import csv
from datetime import datetime
from typing import Dict, Any

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from widgets import SerialMonitorWidget, ParameterPanel
from core.parameter_monitor import ParameterMonitor


class FlightSequencerTab:
    """Enhanced FlightSequencer tab with profiles and monitoring."""
    
    def __init__(self, parent, serial_monitor, tab_manager, main_gui=None):
        self.parent = parent
        self.serial_monitor = serial_monitor
        self.tab_manager = tab_manager
        self.main_gui = main_gui
        self.param_monitor = ParameterMonitor()

        # Flight data management
        self.flight_data_buffer = ""
        self.downloading_data = False
        self.last_flight_data = None

        # Single source of truth for flight parameters
        self.current_flight_params = {
            'motor_run_time': None,
            'total_flight_time': None,
            'motor_speed': None,
            'current_phase': 'UNKNOWN',
            'gps_state': 'UNKNOWN',
            'dt_retracted': None,
            'dt_deployed': None,
            'dt_dwell': None
        }

        # Flight timing
        self.flight_start_time = None
        self.current_timer = "00:00"

        # Flight history tracking
        self.flight_history = []
        self.last_recorded_phase = None

        # Create main tab frame
        self.frame = ttk.Frame(parent)

        # Configure emergency button style
        self._setup_styles()

        self._create_widgets()
        
        # Register with tab manager
        from core.tab_manager import ApplicationType
        tab_manager.register_tab(ApplicationType.FLIGHT_SEQUENCER, self.handle_serial_data)

    def _setup_styles(self):
        """Configure custom styles for the tab."""
        try:
            style = ttk.Style()
            # Create emergency button style with red background
            style.configure("Emergency.TButton",
                          background="#ff4444",
                          foreground="white",
                          font=('TkDefaultFont', 9, 'bold'))
        except Exception:
            # If style configuration fails, continue without custom styling
            pass

    def _create_widgets(self):
        """Create FlightSequencer interface widgets."""
        # Create paned window for resizable layout
        paned = ttk.PanedWindow(self.frame, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Controls and parameters
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # Right panel - Serial monitor
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        # Create control panels
        self._create_flight_controls(left_frame)
        self._create_flight_data_controls(left_frame)
        self._create_status_display(left_frame)
        
        # Serial monitor
        self.serial_monitor_widget = SerialMonitorWidget(
            right_frame, 
            title="FlightSequencer Serial Monitor",
            show_timestamp=True
        )
        self.serial_monitor_widget.pack(fill='both', expand=True)
        self.serial_monitor_widget.set_send_callback(self._send_command)
        
    def _create_flight_controls(self, parent):
        """Create flight parameter controls."""
        # Parameter controls frame
        param_frame = ttk.LabelFrame(parent, text="Flight Parameters")
        param_frame.pack(fill='x', padx=5, pady=5)
        
        # Motor Run Time
        motor_frame = ttk.Frame(param_frame)
        motor_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(motor_frame, text="Motor Run Time (sec):", width=22).pack(side='left')
        self.motor_time_var = tk.StringVar(value="")
        motor_entry = ttk.Entry(motor_frame, textvariable=self.motor_time_var, width=8)
        motor_entry.pack(side='left', padx=5)
        ttk.Button(motor_frame, text="Set", command=self._set_motor_time).pack(side='left', padx=2)

        # Total Flight Time
        flight_frame = ttk.Frame(param_frame)
        flight_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(flight_frame, text="Total Flight Time (sec):", width=22).pack(side='left')
        self.flight_time_var = tk.StringVar(value="")
        flight_entry = ttk.Entry(flight_frame, textvariable=self.flight_time_var, width=8)
        flight_entry.pack(side='left', padx=5)
        ttk.Button(flight_frame, text="Set", command=self._set_flight_time).pack(side='left', padx=2)

        # Motor Speed
        speed_frame = ttk.Frame(param_frame)
        speed_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(speed_frame, text="Motor Speed (95-200):", width=22).pack(side='left')
        self.motor_speed_var = tk.StringVar(value="")
        speed_entry = ttk.Entry(speed_frame, textvariable=self.motor_speed_var, width=8)
        speed_entry.pack(side='left', padx=5)
        ttk.Button(speed_frame, text="Set", command=self._set_motor_speed).pack(side='left', padx=2)

        # DT Retracted Position
        dt_retracted_frame = ttk.Frame(param_frame)
        dt_retracted_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(dt_retracted_frame, text="DT Retracted (us):", width=22).pack(side='left')
        self.dt_retracted_var = tk.StringVar(value="")
        dt_retracted_entry = ttk.Entry(dt_retracted_frame, textvariable=self.dt_retracted_var, width=8)
        dt_retracted_entry.pack(side='left', padx=5)
        ttk.Button(dt_retracted_frame, text="Set", command=self._set_dt_retracted).pack(side='left', padx=2)

        # DT Deployed Position
        dt_deployed_frame = ttk.Frame(param_frame)
        dt_deployed_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(dt_deployed_frame, text="DT Deployed (us):", width=22).pack(side='left')
        self.dt_deployed_var = tk.StringVar(value="")
        dt_deployed_entry = ttk.Entry(dt_deployed_frame, textvariable=self.dt_deployed_var, width=8)
        dt_deployed_entry.pack(side='left', padx=5)
        ttk.Button(dt_deployed_frame, text="Set", command=self._set_dt_deployed).pack(side='left', padx=2)

        # DT Dwell Time
        dt_dwell_frame = ttk.Frame(param_frame)
        dt_dwell_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(dt_dwell_frame, text="DT Dwell Time (sec):", width=22).pack(side='left')
        self.dt_dwell_var = tk.StringVar(value="")
        dt_dwell_entry = ttk.Entry(dt_dwell_frame, textvariable=self.dt_dwell_var, width=8)
        dt_dwell_entry.pack(side='left', padx=5)
        ttk.Button(dt_dwell_frame, text="Set", command=self._set_dt_dwell).pack(side='left', padx=2)

        # Action buttons
        action_frame = ttk.Frame(param_frame)
        action_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(action_frame, text="Get Parameters",
                  command=self._get_parameters).pack(side='left', padx=2)
        ttk.Button(action_frame, text="Reset Defaults",
                  command=self._reset_parameters).pack(side='left', padx=2)

        # Emergency Stop button - prominent red button
        ttk.Button(action_frame, text="Emergency Stop",
                  command=self._emergency_stop,
                  style="Emergency.TButton").pack(side='left', padx=10)

        # Parameter file management buttons
        ttk.Button(action_frame, text="Save Parameters",
                  command=self._save_parameters_to_file).pack(side='right', padx=2)
        ttk.Button(action_frame, text="Load Parameters",
                  command=self._load_parameters_from_file).pack(side='right', padx=2)

    def _create_flight_data_controls(self, parent):
        """Create flight data download and management controls."""
        data_frame = ttk.LabelFrame(parent, text="Flight Data Management")
        data_frame.pack(fill='x', padx=5, pady=5)

        # Flight records status
        status_frame = ttk.Frame(data_frame)
        status_frame.pack(fill='x', padx=5, pady=2)

        self.records_status_var = tk.StringVar(value="Records: Unknown")
        ttk.Label(status_frame, textvariable=self.records_status_var).pack(side='left')

        self.gps_status_var = tk.StringVar(value="GPS: Unknown")
        ttk.Label(status_frame, textvariable=self.gps_status_var).pack(side='right')

        # Download controls
        download_frame = ttk.Frame(data_frame)
        download_frame.pack(fill='x', padx=5, pady=2)

        ttk.Button(download_frame, text="Download Flight Data",
                  command=self._download_flight_data).pack(side='left', padx=2)
        ttk.Button(download_frame, text="Clear Records",
                  command=self._clear_flight_records).pack(side='left', padx=2)
        ttk.Button(download_frame, text="View Flight Path / Open File",
                  command=self._view_flight_path).pack(side='right', padx=2)

    def _create_status_display(self, parent):
        """Create flight history display."""
        history_frame = ttk.LabelFrame(parent, text="Flight History")
        history_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create scrollable text widget for flight history
        history_container = ttk.Frame(history_frame)
        history_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Text widget with scrollbar
        self.history_text = tk.Text(history_container, height=8, wrap='word',
                                   font=('Consolas', 9), state='disabled')

        history_scrollbar = ttk.Scrollbar(history_container, orient='vertical',
                                         command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=history_scrollbar.set)

        self.history_text.pack(side='left', fill='both', expand=True)
        history_scrollbar.pack(side='right', fill='y')

        # Clear history button
        clear_frame = ttk.Frame(history_frame)
        clear_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(clear_frame, text="Clear History",
                  command=self._clear_flight_history).pack(side='right')
            
    def _send_command(self, command):
        """Send command to FlightSequencer."""
        if self.serial_monitor and self.serial_monitor.is_connected:
            self.serial_monitor.send_line(command)
            self.serial_monitor_widget.log_sent(command)
        else:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            
    def _set_motor_time(self):
        """Set motor run time parameter."""
        try:
            time_val = self.motor_time_var.get().strip()
            # Validate range
            time_int = int(time_val)
            if not (1 <= time_int <= 300):
                raise ValueError("Motor time must be 1-300 seconds")
            command = f"M {time_val}"
            self._send_command(command)
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            
    def _set_flight_time(self):
        """Set total flight time parameter."""
        try:
            time_val = self.flight_time_var.get().strip()
            # Validate range
            time_int = int(time_val)
            if not (10 <= time_int <= 600):
                raise ValueError("Flight time must be 10-600 seconds")
            command = f"T {time_val}"
            self._send_command(command)
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            
    def _set_motor_speed(self):
        """Set motor speed parameter."""
        try:
            speed_val = self.motor_speed_var.get().strip()
            # Validate range
            speed_int = int(speed_val)
            if not (95 <= speed_int <= 200):
                raise ValueError("Motor speed must be 95-200")
            command = f"S {speed_val}"
            self._send_command(command)
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))

    def _set_dt_retracted(self):
        """Set DT retracted position parameter."""
        try:
            pos_val = self.dt_retracted_var.get().strip()
            # Validate range (standard servo range)
            pos_int = int(pos_val)
            if not (950 <= pos_int <= 2050):
                raise ValueError("DT retracted position must be 950-2050 microseconds")
            command = f"DR {pos_val}"
            self._send_command(command)
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))

    def _set_dt_deployed(self):
        """Set DT deployed position parameter."""
        try:
            pos_val = self.dt_deployed_var.get().strip()
            # Validate range (standard servo range)
            pos_int = int(pos_val)
            if not (950 <= pos_int <= 2050):
                raise ValueError("DT deployed position must be 950-2050 microseconds")
            command = f"DD {pos_val}"
            self._send_command(command)
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))

    def _set_dt_dwell(self):
        """Set DT dwell time parameter."""
        try:
            time_val = self.dt_dwell_var.get().strip()
            # Validate range
            time_int = int(time_val)
            if not (1 <= time_int <= 60):
                raise ValueError("DT dwell time must be 1-60 seconds")
            command = f"DW {time_val}"
            self._send_command(command)
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))

    def _get_parameters(self):
        """Get current parameters from FlightSequencer."""
        self._send_command("G")

    def _reset_parameters(self):
        """Reset parameters to defaults."""
        if messagebox.askyesno("Reset Parameters",
                              "Reset all parameters to factory defaults?"):
            self._send_command("R")
            
    def _emergency_stop(self):
        """Emergency stop command."""
        if messagebox.askyesno("Emergency Stop", 
                              "Send emergency stop command?"):
            self._send_command("STOP")
            self.serial_monitor_widget.log_error("EMERGENCY STOP SENT")
            self._add_history_entry("EMERGENCY", "Emergency stop command sent")
            
    def handle_serial_data(self, data):
        """Handle incoming serial data for FlightSequencer."""
        # Display in serial monitor
        self.serial_monitor_widget.log_received(data)

        # Update canonical parameter store from ANY Arduino response
        self._update_parameter_store(data)

        # Update GUI to reflect current parameter store
        self._sync_gui_with_parameters()

        # Handle flight data download
        self._handle_flight_data_response(data)

        # Track other significant events
        self._track_flight_events(data)

    def _track_flight_events(self, data):
        """Track significant flight events for history."""
        # Flight data events
        if "flight records downloaded" in data.lower():
            self._add_history_entry("DATA", "Flight data downloaded successfully")
        elif "flight records cleared" in data.lower():
            self._add_history_entry("DATA", "Flight records cleared")

        # Error events
        if re.search(r'\[ERROR\]', data, re.IGNORECASE):
            error_msg = data.strip()
            if len(error_msg) > 100:
                error_msg = error_msg[:97] + "..."
            self._add_history_entry("ERROR", error_msg.replace("[ERROR]", "").strip())

        # Warning events
        if re.search(r'\[WARN\]', data, re.IGNORECASE):
            warning_msg = data.strip()
            if len(warning_msg) > 100:
                warning_msg = warning_msg[:97] + "..."
            self._add_history_entry("WARNING", warning_msg.replace("[WARN]", "").strip())


    def handle_connection_change(self, connected):
        """Handle connection status changes."""
        if not connected:
            # Add disconnection event to history
            self._add_history_entry("CONNECTION", "Disconnected from Arduino")
            # Clear parameter store when disconnected
            self._clear_parameters()
        else:
            # Add connection event to history
            self._add_history_entry("CONNECTION", "Connected to Arduino")
            # On connection, automatically get current parameters and status
            self.parent.after(2500, self._get_parameters)  # Send G command after Arduino settles

    def _clear_parameters(self):
        """Clear parameter store and GUI when disconnected."""
        def clear_params():
            # Clear canonical parameter store
            self.current_flight_params = {
                'motor_run_time': None,
                'total_flight_time': None,
                'motor_speed': None,
                'current_phase': 'DISCONNECTED',
                'gps_state': 'UNKNOWN',
                'dt_retracted': None,
                'dt_deployed': None,
                'dt_dwell': None
            }

            # Clear input fields
            self.motor_time_var.set("")
            self.flight_time_var.set("")
            self.motor_speed_var.set("")
            self.dt_retracted_var.set("")
            self.dt_deployed_var.set("")
            self.dt_dwell_var.set("")

            # Reset timer
            self.current_timer = "00:00"

            # Clear main GUI status bar
            if self.main_gui:
                self.main_gui.clear_flight_status()

        self.parent.after(0, clear_params)


    def _update_parameter_store(self, data):
        """Update canonical parameter store from any Arduino response."""
        # Track parameter changes with history entries
        # Motor Run Time patterns: "[INFO] Motor Run Time: 20 seconds" or "[OK] Motor Run Time = 12 seconds"
        motor_time_match = re.search(r'Motor Run Time[:\s=]+(\d+)', data, re.IGNORECASE)
        if motor_time_match:
            new_value = int(motor_time_match.group(1))
            if self.current_flight_params['motor_run_time'] != new_value:
                if re.search(r'\[OK\]', data):  # Only log when set, not when read
                    self._add_history_entry("PARAM", f"Motor run time set to {new_value} seconds")
                self.current_flight_params['motor_run_time'] = new_value

        # Total Flight Time patterns: "[INFO] Total Flight Time: 120 seconds"
        flight_time_match = re.search(r'Total Flight Time[:\s=]+(\d+)', data, re.IGNORECASE)
        if flight_time_match:
            new_value = int(flight_time_match.group(1))
            if self.current_flight_params['total_flight_time'] != new_value:
                if re.search(r'\[OK\]', data):  # Only log when set, not when read
                    self._add_history_entry("PARAM", f"Total flight time set to {new_value} seconds")
                self.current_flight_params['total_flight_time'] = new_value

        # Motor Speed patterns: "[INFO] Motor Speed: 150 (1500us PWM)" or "[OK] Motor Speed = 135"
        motor_speed_match = re.search(r'Motor Speed[:\s=]+(\d+)', data, re.IGNORECASE)
        if motor_speed_match:
            new_value = int(motor_speed_match.group(1))
            if self.current_flight_params['motor_speed'] != new_value:
                if re.search(r'\[OK\]', data):  # Only log when set, not when read
                    self._add_history_entry("PARAM", f"Motor speed set to {new_value}")
                self.current_flight_params['motor_speed'] = new_value

        # DT Retracted patterns: "[INFO] DT Retracted: 1000us" or "[OK] DT Retracted = 1000"
        dt_retracted_match = re.search(r'DT Retracted[:\s=]+(\d+)', data, re.IGNORECASE)
        if dt_retracted_match:
            self.current_flight_params['dt_retracted'] = int(dt_retracted_match.group(1))

        # DT Deployed patterns: "[INFO] DT Deployed: 2000us" or "[OK] DT Deployed = 2000"
        dt_deployed_match = re.search(r'DT Deployed[:\s=]+(\d+)', data, re.IGNORECASE)
        if dt_deployed_match:
            self.current_flight_params['dt_deployed'] = int(dt_deployed_match.group(1))

        # DT Dwell patterns: "[INFO] DT Dwell: 5 seconds" or "[OK] DT Dwell = 5"
        dt_dwell_match = re.search(r'DT Dwell[:\s=]+(\d+)', data, re.IGNORECASE)
        if dt_dwell_match:
            self.current_flight_params['dt_dwell'] = int(dt_dwell_match.group(1))

        # Current Phase patterns: "[INFO] Current Phase: READY" or state transition messages
        phase_match = re.search(r'Current Phase:\s*([A-Z_]+)', data, re.IGNORECASE)
        new_phase = None

        if phase_match:
            new_phase = phase_match.group(1).upper()
        else:
            # State transition messages
            if re.search(r'System ready|ready for new flight', data, re.IGNORECASE):
                new_phase = 'READY'
            elif re.search(r'System ARMED', data, re.IGNORECASE):
                new_phase = 'ARMED'
            elif re.search(r'LAUNCH.*Motor|Motor spooling', data, re.IGNORECASE):
                new_phase = 'MOTOR_SPOOL'
            elif re.search(r'Motor at flight speed', data, re.IGNORECASE):
                new_phase = 'MOTOR_RUN'
            elif re.search(r'Motor.*complete.*glide', data, re.IGNORECASE):
                new_phase = 'GLIDE'
            elif re.search(r'deploying DT|Flight time complete', data, re.IGNORECASE):
                new_phase = 'DT_DEPLOY'
            elif re.search(r'Dethermalizer DEPLOYED', data, re.IGNORECASE):
                new_phase = 'DT_DEPLOYED'
            elif re.search(r'flight complete', data, re.IGNORECASE):
                new_phase = 'LANDING'

        # Track phase changes and add to history
        if new_phase and new_phase != self.last_recorded_phase:
            self.current_flight_params['current_phase'] = new_phase
            self.last_recorded_phase = new_phase

            # Add history entry for phase change
            phase_descriptions = {
                'READY': 'System ready for new flight',
                'ARMED': 'System armed, ready for launch',
                'MOTOR_SPOOL': 'Motor spooling up for launch',
                'MOTOR_RUN': 'Motor running at flight speed',
                'GLIDE': 'Motor complete, entering glide phase',
                'DT_DEPLOY': 'Deploying dethermalizer',
                'DT_DEPLOYED': 'Dethermalizer deployed',
                'LANDING': 'Flight complete, landing phase'
            }

            description = phase_descriptions.get(new_phase, f"Phase changed to {new_phase}")
            self._add_history_entry("PHASE", description)

        # GPS State patterns: "[INFO] GPS Status: Available" or "GPS Status: Not detected"
        gps_status_match = re.search(r'GPS Status:\s*([^()\n]+)', data, re.IGNORECASE)
        if gps_status_match:
            gps_status = gps_status_match.group(1).strip()
            new_gps_state = None

            if 'available' in gps_status.lower():
                new_gps_state = 'AVAILABLE'
            elif 'not detected' in gps_status.lower():
                new_gps_state = 'NOT_DETECTED'
            else:
                new_gps_state = gps_status.upper()

            # Track GPS state changes
            if new_gps_state != self.current_flight_params['gps_state']:
                gps_descriptions = {
                    'AVAILABLE': 'GPS module detected and available',
                    'NOT_DETECTED': 'GPS module not detected'
                }
                description = gps_descriptions.get(new_gps_state, f"GPS status: {new_gps_state}")
                self._add_history_entry("GPS", description)
                self.current_flight_params['gps_state'] = new_gps_state

        # Flight timing patterns: "Flight time: 45s" or "Elapsed: 01:23"
        time_match = re.search(r'(?:Flight time|Elapsed):\s*(?:(\d+)s|(\d+):(\d+))', data, re.IGNORECASE)
        if time_match:
            if time_match.group(1):  # Format: "45s"
                seconds = int(time_match.group(1))
                minutes = seconds // 60
                seconds = seconds % 60
                self.current_timer = f"{minutes:02d}:{seconds:02d}"
            elif time_match.group(2) and time_match.group(3):  # Format: "01:23"
                self.current_timer = f"{time_match.group(2)}:{time_match.group(3)}"

    def _sync_gui_with_parameters(self):
        """Update GUI fields to match canonical parameter store."""
        def update_gui():
            params = self.current_flight_params

            # Update input fields with current parameter values
            if params['motor_run_time'] is not None:
                self.motor_time_var.set(str(params['motor_run_time']))

            if params['total_flight_time'] is not None:
                self.flight_time_var.set(str(params['total_flight_time']))

            if params['motor_speed'] is not None:
                self.motor_speed_var.set(str(params['motor_speed']))

            if params['dt_retracted'] is not None:
                self.dt_retracted_var.set(str(params['dt_retracted']))

            if params['dt_deployed'] is not None:
                self.dt_deployed_var.set(str(params['dt_deployed']))

            if params['dt_dwell'] is not None:
                self.dt_dwell_var.set(str(params['dt_dwell']))

            # Update main GUI status bar with phase and timer information
            if self.main_gui:
                self.main_gui.update_flight_status(
                    phase=params['current_phase'],
                    timer=self.current_timer
                )

            # Update GPS status display
            self.gps_status_var.set(f"GPS: {params['gps_state']}")

        self.parent.after(0, update_gui)

            
    def _download_flight_data(self):
        """Download flight records from Arduino."""
        if not self.serial_monitor or not self.serial_monitor.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            return

        # Show progress dialog
        progress_window = tk.Toplevel(self.parent)
        progress_window.title("Downloading Flight Data")
        progress_window.geometry("300x100")
        progress_window.grab_set()  # Make it modal

        ttk.Label(progress_window, text="Downloading flight records...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode='indeterminate')
        progress.pack(padx=20, pady=10, fill='x')
        progress.start()

        # Start download
        self.flight_data_buffer = ""
        self.downloading_data = True
        self.progress_window = progress_window
        self._send_command("D J")  # Request JSON format

        # Set timeout for download
        self.parent.after(10000, lambda: self._download_timeout())

    def _download_timeout(self):
        """Handle download timeout."""
        if self.downloading_data:
            self.downloading_data = False
            if hasattr(self, 'progress_window'):
                self.progress_window.destroy()
            messagebox.showerror("Timeout", "Download timed out. Please try again.")

    def _clear_flight_records(self):
        """Clear flight records on Arduino."""
        if messagebox.askyesno("Clear Records",
                              "Clear all flight records from Arduino?"):
            self._send_command("X")
            self.records_status_var.set("Records: Cleared")

    def _view_flight_path(self):
        """Open flight path visualization window."""
        if not hasattr(self, 'last_flight_data') or not self.last_flight_data:
            # No current data available, offer to load from file
            response = messagebox.askyesno(
                "No Flight Data",
                "No flight data available.\n\nWould you like to open an existing flight data file?"
            )
            if response:
                self._load_flight_data_from_file()
                # Check if data was successfully loaded
                if not hasattr(self, 'last_flight_data') or not self.last_flight_data:
                    return  # User cancelled or file load failed
            else:
                return  # User chose not to load file

        self._create_flight_path_window()

    def _handle_flight_data_response(self, data):
        """Handle flight data download response."""
        if not self.downloading_data:
            # Update GPS status from help command responses
            if "GPS Status:" in data:
                if "Available" in data:
                    # Extract position count
                    import re
                    match = re.search(r'\((\d+) positions recorded\)', data)
                    if match:
                        count = match.group(1)
                        self.gps_status_var.set(f"GPS: Available")
                        self.records_status_var.set(f"Records: {count} positions")
                    else:
                        self.gps_status_var.set("GPS: Available")
                elif "Not detected" in data:
                    self.gps_status_var.set("GPS: Not detected")
                    self.records_status_var.set("Records: N/A (No GPS)")
            return

        # Check for "no data available" response - cancel download immediately
        if "No flight records available" in data:
            self.downloading_data = False
            if hasattr(self, 'progress_window'):
                self.progress_window.destroy()

            # Show appropriate message based on reason
            if "GPS not available" in data:
                messagebox.showinfo("No Data", "No flight records available:\nGPS module not detected.")
                self.records_status_var.set("Records: N/A (No GPS)")
            elif "GPS detected but no positions recorded" in data:
                messagebox.showinfo("No Data", "No flight records available:\nGPS detected but no flight data recorded yet.")
                self.records_status_var.set("Records: 0 positions")
            else:
                messagebox.showinfo("No Data", "No flight records available.")
                self.records_status_var.set("Records: None")
            return

        # Collect data until END marker
        self.flight_data_buffer += data + "\n"

        if "[END_FLIGHT_DATA]" in data:
            self.downloading_data = False
            if hasattr(self, 'progress_window'):
                self.progress_window.destroy()
            self._process_downloaded_data()

    def _process_downloaded_data(self):
        """Process and save downloaded flight data."""
        try:
            # Parse CSV format from buffer - handle line breaks within records
            raw_data = self.flight_data_buffer.strip()

            # Remove carriage returns and normalize line endings
            raw_data = raw_data.replace('\r\n', '\n').replace('\r', '\n')

            # Reassemble any records that were split across lines
            # Look for incomplete GPS records and join them with the next line
            lines = raw_data.split('\n')
            processed_lines = []
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                # Skip empty lines and control markers
                if not line or line.startswith('[') or line.startswith('DEBUG'):
                    i += 1
                    continue

                # Check if this is an incomplete GPS record
                if line.startswith('GPS,'):
                    parts = line.split(',')

                    # GPS records need 6 parts: GPS,timestamp,state,state_name,lat,lon
                    # Also check if lat/lon fields look incomplete (contain only minus sign)
                    is_incomplete = False

                    if len(parts) < 6:
                        is_incomplete = True
                    elif len(parts) >= 6:
                        # Check if latitude or longitude fields are incomplete
                        lat_field = parts[4] if len(parts) > 4 else ""
                        lon_field = parts[5] if len(parts) > 5 else ""

                        # Check for incomplete coordinate values (just a minus sign or empty)
                        if lat_field in ["-", ""] or lon_field in ["-", ""]:
                            is_incomplete = True

                    if is_incomplete:
                        # This GPS record is incomplete, try to merge with next line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            # Merge the lines
                            merged_line = line + next_line
                            processed_lines.append(merged_line)
                            i += 2  # Skip both current and next line
                        else:
                            # Last line, can't merge
                            processed_lines.append(line)
                            i += 1
                    else:
                        # Complete GPS record
                        processed_lines.append(line)
                        i += 1
                else:
                    # Non-GPS line (HEADER, etc.)
                    processed_lines.append(line)
                    i += 1

            flight_header = None
            gps_records = []

            for line in processed_lines:
                if line.startswith('HEADER,'):
                    # Parse header: HEADER,flight_id,duration_ms,gps_available,position_count,motor_run_time,total_flight_time,motor_speed
                    parts = line.split(',')
                    if len(parts) >= 8:
                        flight_header = {
                            'flight_id': parts[1],
                            'duration_ms': int(parts[2]),
                            'gps_available': parts[3] == 'true',
                            'position_count': int(parts[4]),
                            'parameters': {
                                'motor_run_time': int(parts[5]),
                                'total_flight_time': int(parts[6]),
                                'motor_speed': int(parts[7])
                            }
                        }
                elif line.startswith('GPS,'):
                    # Parse GPS record: GPS,timestamp_ms,flight_state,state_name,latitude,longitude,altitude
                    parts = line.split(',')
                    if len(parts) >= 7:
                        try:
                            altitude_val = float(parts[6])
                            gps_records.append({
                                'timestamp_ms': int(parts[1]),
                                'flight_state': int(parts[2]),
                                'state_name': parts[3],
                                'latitude': float(parts[4]),
                                'longitude': float(parts[5]),
                                'altitude': altitude_val
                            })
                            # Debug: Print first few altitude values to help diagnose
                            if len(gps_records) <= 3:
                                print(f"[DEBUG] GPS record {len(gps_records)}: Alt={altitude_val}m, Raw parts: {parts[:7]}")
                        except (ValueError, IndexError) as e:
                            # Handle parsing errors gracefully
                            continue
                    elif len(parts) >= 6:
                        # Fallback for older format without altitude
                        try:
                            gps_records.append({
                                'timestamp_ms': int(parts[1]),
                                'flight_state': int(parts[2]),
                                'state_name': parts[3],
                                'latitude': float(parts[4]),
                                'longitude': float(parts[5]),
                                'altitude': 0.0  # Default altitude if not available
                            })
                        except ValueError as ve:
                            # Log problematic GPS record but continue processing
                            print(f"Skipping malformed GPS record: {line} - Error: {ve}")
                            continue

            if flight_header and gps_records:
                # Create flight data structure
                flight_data = {
                    'flight_header': flight_header,
                    'position_records': gps_records
                }

                self.last_flight_data = flight_data

                # Save to file in ./flightdata directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"flight_data_{timestamp}.json"

                # Create flightdata directory if it doesn't exist
                flightdata_dir = os.path.join(os.getcwd(), "flightdata")
                os.makedirs(flightdata_dir, exist_ok=True)

                try:
                    # Combine directory and filename for initialfile
                    initial_file_path = os.path.join(flightdata_dir, filename)

                    file_path = filedialog.asksaveasfilename(
                        defaultextension=".json",
                        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                        initialfile=initial_file_path,
                        parent=self.parent,
                        title="Save Flight Data"
                    )

                    if file_path:
                        # User selected a file location
                        with open(file_path, 'w') as f:
                            json.dump(flight_data, f, indent=2)
                        # File saved successfully - no message needed
                    else:
                        # User cancelled - don't save anything
                        return

                except Exception as dialog_error:
                    # Fallback: save to flightdata directory with timestamp
                    fallback_path = os.path.join(flightdata_dir, filename)
                    with open(fallback_path, 'w') as f:
                        json.dump(flight_data, f, indent=2)
                    messagebox.showinfo("Success", f"Flight data saved to:\n{fallback_path}\n\n(File dialog error: {str(dialog_error)})")

                # Update status
                position_count = len(gps_records)
                self.records_status_var.set(f"Records: {position_count} positions")
                if position_count > 0:
                    self.gps_status_var.set("GPS: Data downloaded")
            else:
                messagebox.showwarning("No Data", "No valid flight data found in Arduino response")

        except Exception as e:
            # Save the problematic data for debugging
            debug_file = f"debug_csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(debug_file, 'w') as f:
                f.write("Raw buffer:\n")
                f.write(repr(self.flight_data_buffer))
                f.write(f"\n\nParse Error: {str(e)}")

            messagebox.showerror("Parse Error", f"Failed to process flight data:\n{str(e)}\n\nDebug data saved to: {debug_file}")

    def _create_flight_path_window(self):
        """Create flight path visualization window."""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            import numpy as np
        except ImportError:
            messagebox.showerror("Missing Package",
                               "matplotlib is required for flight path visualization.\n"
                               "Install with: pip install matplotlib")
            return

        # Create visualization window
        viz_window = tk.Toplevel(self.parent)
        viz_window.title("Flight Path Visualization")
        viz_window.geometry("900x700")

        # Create File menu
        menubar = tk.Menu(viz_window)
        viz_window.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Plot as PNG", command=lambda: self._save_plot_as_png())
        file_menu.add_command(label="Save Plot as PDF", command=lambda: self._save_plot_as_pdf())
        file_menu.add_separator()
        file_menu.add_command(label="Export CSV", command=lambda: self._export_csv())
        file_menu.add_command(label="Export KML", command=lambda: self._export_kml())
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=viz_window.destroy)

        # Store figure reference for saving
        self.current_figure = None
        self.current_viz_window = viz_window

        # Create matplotlib figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # Parse flight data
        positions = self.last_flight_data.get('position_records', [])
        if not positions:
            ttk.Label(viz_window, text="No position data available").pack()
            return

        # Extract data arrays
        times = [p['timestamp_ms'] / 1000.0 for p in positions]  # Convert to seconds
        lats = [p['latitude'] for p in positions]
        lons = [p['longitude'] for p in positions]
        alts = [p.get('altitude', 0.0) for p in positions]  # Get altitude with fallback
        states = [p['flight_state'] for p in positions]
        state_names = [p['state_name'] for p in positions]

        # Debug: Print altitude statistics
        if alts:
            min_alt, max_alt = min(alts), max(alts)
            avg_alt = sum(alts) / len(alts)
            non_zero_alts = [a for a in alts if a != 0.0]
            print(f"[DEBUG] Altitude data: {len(positions)} points, Range: {min_alt:.1f}-{max_alt:.1f}m, Avg: {avg_alt:.1f}m, Non-zero: {len(non_zero_alts)}")
            if len(non_zero_alts) > 0:
                print(f"[DEBUG] First 5 altitudes: {alts[:5]}")
            else:
                print(f"[DEBUG] WARNING: All altitude values are zero! Check GPS data source.")

        # Plot 1: Flight path map
        scatter = ax1.scatter(lons, lats, c=times, cmap='viridis', s=50)
        ax1.plot(lons, lats, 'b-', alpha=0.6, linewidth=2)
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')
        ax1.set_title('GPS Flight Path')
        ax1.grid(True, alpha=0.3)

        # Add colorbar for time
        plt.colorbar(scatter, ax=ax1, label='Time (seconds)')

        # Add state markers
        state_colors = {3: 'red', 4: 'orange', 5: 'green', 6: 'purple', 7: 'brown'}
        state_labels = {3: 'Spool', 4: 'Motor', 5: 'Glide', 6: 'DT Deploy', 7: 'Post-DT'}

        for state in state_colors:
            state_positions = [(lon, lat) for lon, lat, s in zip(lons, lats, states) if s == state]
            if state_positions:
                state_lons, state_lats = zip(*state_positions)
                ax1.scatter(state_lons, state_lats, c=state_colors[state],
                           s=100, alpha=0.7, marker='s', label=state_labels[state])

        ax1.legend()

        # Plot 2: Altitude over time
        ax2.plot(times, alts, 'g-', linewidth=2, marker='o', markersize=4)
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Altitude (meters)')
        ax2.set_title('Altitude Over Time')
        ax2.grid(True, alpha=0.3)

        # Add state background colors to altitude plot
        state_colors = {3: 'red', 4: 'orange', 5: 'lightgreen', 6: 'purple', 7: 'lightblue'}
        current_state = None
        state_start_time = None

        for i, (time, state) in enumerate(zip(times, states)):
            if state != current_state:
                if current_state is not None and current_state in state_colors:
                    # Fill previous state period
                    ax2.axvspan(state_start_time, time, alpha=0.2, color=state_colors[current_state])
                current_state = state
                state_start_time = time

        # Fill last state period
        if current_state is not None and current_state in state_colors and times:
            ax2.axvspan(state_start_time, times[-1], alpha=0.2, color=state_colors[current_state])

        # Add legend for state colors
        state_labels = {3: 'Motor Spool', 4: 'Motor Run', 5: 'Glide', 6: 'DT Deploy', 7: 'Post-DT'}
        legend_elements = [plt.Rectangle((0,0),1,1, facecolor=state_colors[s], alpha=0.2, label=state_labels[s])
                          for s in state_colors if s in states]
        if legend_elements:
            ax2.legend(handles=legend_elements, loc='upper right')

        plt.tight_layout()

        # Store figure reference for saving
        self.current_figure = fig

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, viz_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        # Add toolbar for zooming and panning
        toolbar = NavigationToolbar2Tk(canvas, viz_window)
        toolbar.update()

        # Add export button frame
        export_frame = ttk.Frame(viz_window)
        export_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(export_frame, text="Export CSV",
                  command=lambda: self._export_csv()).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Export KML",
                  command=lambda: self._export_kml()).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Close",
                  command=viz_window.destroy).pack(side='right', padx=5)

    def _export_csv(self):
        """Export flight data to CSV format."""
        if not hasattr(self, 'last_flight_data') or not self.last_flight_data:
            messagebox.showwarning("No Data", "No flight data to export")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flight_path_{timestamp}.csv"

        # Create flightdata directory if it doesn't exist
        flightdata_dir = os.path.join(os.getcwd(), "flightdata")
        os.makedirs(flightdata_dir, exist_ok=True)

        # Combine directory and filename for initialfile
        initial_file_path = os.path.join(flightdata_dir, filename)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=initial_file_path,
            parent=self.parent,
            title="Export Flight Path as CSV"
        )

        if file_path:
            positions = self.last_flight_data.get('position_records', [])

            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Time_Seconds', 'Flight_State', 'State_Name',
                               'Latitude', 'Longitude', 'Altitude_Meters'])

                for pos in positions:
                    writer.writerow([
                        pos['timestamp_ms'] / 1000.0,
                        pos['flight_state'],
                        pos['state_name'],
                        pos['latitude'],
                        pos['longitude'],
                        pos.get('altitude', 0.0)
                    ])

            # CSV exported successfully - no message needed
            pass
        # User cancelled - no message needed

    def _export_kml(self):
        """Export flight path to KML for Google Earth."""
        if not hasattr(self, 'last_flight_data') or not self.last_flight_data:
            messagebox.showwarning("No Data", "No flight data to export")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flight_path_{timestamp}.kml"

        # Create flightdata directory if it doesn't exist
        flightdata_dir = os.path.join(os.getcwd(), "flightdata")
        os.makedirs(flightdata_dir, exist_ok=True)

        # Combine directory and filename for initialfile
        initial_file_path = os.path.join(flightdata_dir, filename)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".kml",
            filetypes=[("KML files", "*.kml"), ("All files", "*.*")],
            initialfile=initial_file_path,
            parent=self.parent,
            title="Export Flight Path as KML"
        )

        if file_path:
            positions = self.last_flight_data.get('position_records', [])

            kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Flight Path {timestamp}</name>
    <description>FlightSequencer GPS Track</description>

    <Style id="flightPath">
      <LineStyle>
        <color>ff0000ff</color>
        <width>3</width>
      </LineStyle>
    </Style>

    <Placemark>
      <name>Flight Path</name>
      <styleUrl>#flightPath</styleUrl>
      <LineString>
        <coordinates>
"""

            for pos in positions:
                alt = pos.get('altitude', 0.0)
                kml_content += f"          {pos['longitude']},{pos['latitude']},{alt}\n"

            kml_content += """        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""

            with open(file_path, 'w') as f:
                f.write(kml_content)

            messagebox.showinfo("Success", f"KML exported to:\n{file_path}")
        else:
            messagebox.showinfo("Cancelled", "KML export cancelled by user.")

    def _save_plot_as_png(self):
        """Save the current plot as PNG."""
        if not hasattr(self, 'current_figure') or self.current_figure is None:
            messagebox.showwarning("No Plot", "No plot available to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flight_plot_{timestamp}.png"

        # Create flightdata directory if it doesn't exist
        flightdata_dir = os.path.join(os.getcwd(), "flightdata")
        os.makedirs(flightdata_dir, exist_ok=True)
        initial_file_path = os.path.join(flightdata_dir, filename)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile=initial_file_path,
            parent=self.current_viz_window,
            title="Save Plot as PNG"
        )

        if file_path:
            try:
                self.current_figure.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save plot:\n{str(e)}")

    def _save_plot_as_pdf(self):
        """Save the current plot as PDF."""
        if not hasattr(self, 'current_figure') or self.current_figure is None:
            messagebox.showwarning("No Plot", "No plot available to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flight_plot_{timestamp}.pdf"

        # Create flightdata directory if it doesn't exist
        flightdata_dir = os.path.join(os.getcwd(), "flightdata")
        os.makedirs(flightdata_dir, exist_ok=True)
        initial_file_path = os.path.join(flightdata_dir, filename)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=initial_file_path,
            parent=self.current_viz_window,
            title="Save Plot as PDF"
        )

        if file_path:
            try:
                self.current_figure.savefig(file_path, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save plot:\n{str(e)}")

    def _load_flight_data_from_file(self):
        """Load flight data from an existing JSON file."""
        # Create flightdata directory reference for initial directory
        flightdata_dir = os.path.join(os.getcwd(), "flightdata")
        initial_dir = flightdata_dir if os.path.exists(flightdata_dir) else os.getcwd()

        file_path = filedialog.askopenfilename(
            title="Open Flight Data File",
            initialdir=initial_dir,
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return  # User cancelled

        try:
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)

            # Validate that this is flight data (has required structure)
            if not isinstance(loaded_data, dict):
                raise ValueError("File does not contain valid flight data structure")

            if 'flight_header' not in loaded_data or 'position_records' not in loaded_data:
                raise ValueError("File does not contain required flight data fields (flight_header, position_records)")

            # Validate position records structure
            position_records = loaded_data.get('position_records', [])
            if not isinstance(position_records, list):
                raise ValueError("Position records must be a list")

            # Check if we have any position records
            if not position_records:
                raise ValueError("No GPS position records found in file")

            # Validate sample record structure
            sample_record = position_records[0]
            required_fields = ['timestamp_ms', 'flight_state', 'state_name', 'latitude', 'longitude']
            missing_fields = [field for field in required_fields if field not in sample_record]
            if missing_fields:
                raise ValueError(f"GPS records missing required fields: {', '.join(missing_fields)}")

            # Data is valid, store it
            self.last_flight_data = loaded_data

            # Update UI to show loaded data info
            flight_header = loaded_data.get('flight_header', {})
            record_count = len(position_records)

            # Show success message with file info
            file_name = os.path.basename(file_path)
            messagebox.showinfo(
                "Flight Data Loaded",
                f"Successfully loaded flight data from:\n{file_name}\n\n"
                f"Records: {record_count} GPS positions\n"
                f"Duration: {position_records[-1]['timestamp_ms'] / 1000.0:.1f} seconds"
            )

        except json.JSONDecodeError as e:
            messagebox.showerror(
                "Invalid File Format",
                f"The selected file is not valid JSON:\n{str(e)}"
            )
        except ValueError as e:
            messagebox.showerror(
                "Invalid Flight Data",
                f"The selected file does not contain valid flight data:\n{str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error Loading File",
                f"Failed to load flight data file:\n{str(e)}"
            )

    def _save_parameters_to_file(self):
        """Save current flight parameters to a JSON file."""
        try:
            # Collect current parameters from the GUI fields
            params = {
                'motor_run_time': self.motor_time_var.get().strip() or None,
                'total_flight_time': self.flight_time_var.get().strip() or None,
                'motor_speed': self.motor_speed_var.get().strip() or None,
                'dt_retracted': self.dt_retracted_var.get().strip() or None,
                'dt_deployed': self.dt_deployed_var.get().strip() or None,
                'dt_dwell': self.dt_dwell_var.get().strip() or None,
                'saved_timestamp': datetime.now().isoformat(),
                'application': 'FlightSequencer'
            }

            # Filter out None values for cleaner JSON
            params = {k: v for k, v in params.items() if v is not None}

            # Create parameters directory if it doesn't exist
            params_dir = os.path.join(os.getcwd(), "parameters")
            os.makedirs(params_dir, exist_ok=True)

            # Default filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"FlightSequencer_params_{timestamp}.json"
            initial_file_path = os.path.join(params_dir, default_filename)

            # Ask user for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=initial_file_path,
                parent=self.parent,
                title="Save Flight Parameters"
            )

            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(params, f, indent=2)
                messagebox.showinfo("Success", f"Parameters saved to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save parameters:\n{str(e)}")

    def _load_parameters_from_file(self):
        """Load flight parameters from a JSON file."""
        try:
            # Look in parameters directory first
            params_dir = os.path.join(os.getcwd(), "parameters")

            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=params_dir if os.path.exists(params_dir) else os.getcwd(),
                parent=self.parent,
                title="Load Flight Parameters"
            )

            if file_path:
                with open(file_path, 'r') as f:
                    params = json.load(f)

                # Validate that this is a FlightSequencer parameter file
                if params.get('application') != 'FlightSequencer':
                    if not messagebox.askyesno("Warning",
                        "This file may not be FlightSequencer parameters.\nLoad anyway?"):
                        return

                # Load parameters into GUI fields
                if 'motor_run_time' in params:
                    self.motor_time_var.set(str(params['motor_run_time']))
                if 'total_flight_time' in params:
                    self.flight_time_var.set(str(params['total_flight_time']))
                if 'motor_speed' in params:
                    self.motor_speed_var.set(str(params['motor_speed']))
                if 'dt_retracted' in params:
                    self.dt_retracted_var.set(str(params['dt_retracted']))
                if 'dt_deployed' in params:
                    self.dt_deployed_var.set(str(params['dt_deployed']))
                if 'dt_dwell' in params:
                    self.dt_dwell_var.set(str(params['dt_dwell']))

                # Show success message with loaded parameters count
                param_count = len([k for k in params.keys() if k not in ['saved_timestamp', 'application']])
                messagebox.showinfo("Success",
                    f"Loaded {param_count} parameters from:\n{os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load parameters:\n{str(e)}")

    def _add_history_entry(self, event_type, description):
        """Add an entry to the flight history."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {event_type}: {description}"

        # Store in history list
        self.flight_history.append(entry)

        # Update the text widget
        def update_history():
            self.history_text.config(state='normal')
            self.history_text.insert('end', entry + '\n')
            self.history_text.config(state='disabled')
            self.history_text.see('end')  # Auto-scroll to bottom

        self.parent.after(0, update_history)

    def _clear_flight_history(self):
        """Clear the flight history display."""
        self.flight_history.clear()
        self.last_recorded_phase = None

        def clear_history():
            self.history_text.config(state='normal')
            self.history_text.delete('1.0', 'end')
            self.history_text.config(state='disabled')

        self.parent.after(0, clear_history)

    def get_frame(self):
        """Get the main tab frame."""
        return self.frame