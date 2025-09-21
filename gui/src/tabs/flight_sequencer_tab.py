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
    
    def __init__(self, parent, serial_monitor, tab_manager):
        self.parent = parent
        self.serial_monitor = serial_monitor
        self.tab_manager = tab_manager
        self.param_monitor = ParameterMonitor()

        # Flight data management
        self.flight_data_buffer = ""
        self.downloading_data = False
        self.last_flight_data = None

        # Create main tab frame
        self.frame = ttk.Frame(parent)
        
        # Flight profiles
        self.profiles = {
            "Test Flight": {"motor_time": "5", "flight_time": "30", "motor_speed": "120"},
            "Competition": {"motor_time": "20", "flight_time": "120", "motor_speed": "150"},
            "Max Duration": {"motor_time": "30", "flight_time": "300", "motor_speed": "110"}
        }
        
        self._create_widgets()
        self._load_profiles()
        
        # Register with tab manager
        from core.tab_manager import ApplicationType
        tab_manager.register_tab(ApplicationType.FLIGHT_SEQUENCER, self.handle_serial_data)
        
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
        # Profile selection frame
        profile_frame = ttk.LabelFrame(parent, text="Flight Profiles")
        profile_frame.pack(fill='x', padx=5, pady=5)
        
        # Profile dropdown
        ttk.Label(profile_frame, text="Profile:").pack(side='left', padx=5)
        self.profile_var = tk.StringVar(value="Custom")
        profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var,
                                   values=list(self.profiles.keys()) + ["Custom"],
                                   state='readonly', width=15)
        profile_combo.pack(side='left', padx=5)
        profile_combo.bind('<<ComboboxSelected>>', self._load_profile)
        
        ttk.Button(profile_frame, text="Save As...", 
                  command=self._save_custom_profile).pack(side='right', padx=5)
        
        # Parameter controls frame
        param_frame = ttk.LabelFrame(parent, text="Flight Parameters")
        param_frame.pack(fill='x', padx=5, pady=5)
        
        # Motor Run Time
        motor_frame = ttk.Frame(param_frame)
        motor_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(motor_frame, text="Motor Run Time (sec):").pack(side='left')
        self.motor_time_var = tk.StringVar(value="20")
        motor_entry = ttk.Entry(motor_frame, textvariable=self.motor_time_var, width=8)
        motor_entry.pack(side='left', padx=5)
        ttk.Button(motor_frame, text="Set", command=self._set_motor_time).pack(side='left', padx=2)
        
        # Total Flight Time
        flight_frame = ttk.Frame(param_frame)
        flight_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(flight_frame, text="Total Flight Time (sec):").pack(side='left')
        self.flight_time_var = tk.StringVar(value="120")
        flight_entry = ttk.Entry(flight_frame, textvariable=self.flight_time_var, width=8)
        flight_entry.pack(side='left', padx=5)
        ttk.Button(flight_frame, text="Set", command=self._set_flight_time).pack(side='left', padx=2)
        
        # Motor Speed
        speed_frame = ttk.Frame(param_frame)
        speed_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(speed_frame, text="Motor Speed (95-200):").pack(side='left')
        self.motor_speed_var = tk.StringVar(value="150")
        speed_entry = ttk.Entry(speed_frame, textvariable=self.motor_speed_var, width=8)
        speed_entry.pack(side='left', padx=5)
        ttk.Button(speed_frame, text="Set", command=self._set_motor_speed).pack(side='left', padx=2)
        
        # Action buttons
        action_frame = ttk.Frame(param_frame)
        action_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(action_frame, text="Get Parameters", 
                  command=self._get_parameters).pack(side='left', padx=2)
        ttk.Button(action_frame, text="Reset Defaults", 
                  command=self._reset_parameters).pack(side='left', padx=2)
        ttk.Button(action_frame, text="Emergency Stop", 
                  command=self._emergency_stop).pack(side='right', padx=2)

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
        ttk.Button(download_frame, text="View Flight Path",
                  command=self._view_flight_path).pack(side='right', padx=2)

    def _create_status_display(self, parent):
        """Create flight status display."""
        status_frame = ttk.LabelFrame(parent, text="Flight Status")
        status_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Current parameters display
        ttk.Label(status_frame, text="Current Parameters:", 
                 font=('TkDefaultFont', 9, 'bold')).pack(anchor='w', padx=5, pady=2)
        
        self.current_params_text = tk.Text(status_frame, height=8, width=30, state='disabled',
                                         font=('Consolas', 9))
        self.current_params_text.pack(fill='x', padx=5, pady=2)
        
        # Flight statistics
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill='x', padx=5, pady=5)
        
        self.flights_completed_var = tk.StringVar(value="Flights: 0")
        ttk.Label(stats_frame, textvariable=self.flights_completed_var).pack(side='left')
        
        self.current_phase_var = tk.StringVar(value="Phase: IDLE")
        ttk.Label(stats_frame, textvariable=self.current_phase_var).pack(side='right')
        
        # Timer display
        self.timer_var = tk.StringVar(value="Time: 00:00")
        timer_label = ttk.Label(status_frame, textvariable=self.timer_var, 
                              font=('Digital-7', 14, 'bold'))
        timer_label.pack(pady=5)
        
    def _load_profile(self, event=None):
        """Load selected flight profile."""
        profile_name = self.profile_var.get()
        if profile_name in self.profiles:
            profile = self.profiles[profile_name]
            self.motor_time_var.set(profile["motor_time"])
            self.flight_time_var.set(profile["flight_time"])
            self.motor_speed_var.set(profile["motor_speed"])
            
    def _save_custom_profile(self):
        """Save current settings as custom profile."""
        name = tk.simpledialog.askstring("Save Profile", "Enter profile name:")
        if name:
            self.profiles[name] = {
                "motor_time": self.motor_time_var.get(),
                "flight_time": self.flight_time_var.get(),
                "motor_speed": self.motor_speed_var.get()
            }
            self._save_profiles()
            
            # Update combo box
            profile_combo = None
            for widget in self.frame.winfo_children():
                if isinstance(widget, ttk.PanedWindow):
                    for child in widget.winfo_children():
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.LabelFrame) and "Profile" in grandchild['text']:
                                for element in grandchild.winfo_children():
                                    if isinstance(element, ttk.Combobox):
                                        element['values'] = list(self.profiles.keys()) + ["Custom"]
                                        break
                                        
    def _load_profiles(self):
        """Load flight profiles from file."""
        try:
            profiles_file = os.path.expanduser("~/.arduino_gui/flight_profiles.json")
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r') as f:
                    saved_profiles = json.load(f)
                    self.profiles.update(saved_profiles)
        except Exception as e:
            print(f"Failed to load profiles: {e}")
            
    def _save_profiles(self):
        """Save flight profiles to file."""
        try:
            config_dir = os.path.expanduser("~/.arduino_gui")
            os.makedirs(config_dir, exist_ok=True)
            profiles_file = os.path.join(config_dir, "flight_profiles.json")
            
            # Only save custom profiles (not built-in ones)
            custom_profiles = {k: v for k, v in self.profiles.items() 
                             if k not in ["Test Flight", "Competition", "Max Duration"]}
            
            with open(profiles_file, 'w') as f:
                json.dump(custom_profiles, f, indent=2)
        except Exception as e:
            print(f"Failed to save profiles: {e}")
            
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
            
    def handle_serial_data(self, data):
        """Handle incoming serial data for FlightSequencer."""
        # Update parameter monitor
        self.param_monitor.process_serial_data(data)
        
        # Display in serial monitor
        self.serial_monitor_widget.log_received(data)
        
        # Update current parameters display
        self._update_current_params()
        
        # Update flight status
        self._update_flight_status(data)

        # Handle flight data download
        self._handle_flight_data_response(data)

    def _update_current_params(self):
        """Update the current parameters display and input fields."""
        def update_params():
            params = self.param_monitor.get_parameters()

            # Update the display text widget
            self.current_params_text.config(state='normal')
            self.current_params_text.delete(1.0, tk.END)

            if params:
                # Update display
                if 'motor_run_time' in params:
                    self.current_params_text.insert(tk.END, f"Motor Time: {params['motor_run_time']}s\\n")
                    # Update input field
                    self.motor_time_var.set(str(params['motor_run_time']))

                if 'total_flight_time' in params:
                    self.current_params_text.insert(tk.END, f"Flight Time: {params['total_flight_time']}s\\n")
                    # Update input field
                    self.flight_time_var.set(str(params['total_flight_time']))

                if 'motor_speed' in params:
                    speed = params['motor_speed']
                    self.current_params_text.insert(tk.END, f"Motor Speed: {speed}\\n")
                    self.current_params_text.insert(tk.END, f"PWM: {speed * 10}us\\n")
                    # Update input field
                    self.motor_speed_var.set(str(speed))
            else:
                self.current_params_text.insert(tk.END, "No parameters\\nreceived yet")

            self.current_params_text.config(state='disabled')

        self.parent.after(0, update_params)
        
    def _update_flight_status(self, data):
        """Update flight status from serial data."""
        # Extract flight phase
        phase_match = re.search(r'Phase.*?([A-Z_]+)', data, re.IGNORECASE)
        if phase_match:
            phase = phase_match.group(1)
            self.current_phase_var.set(f"Phase: {phase}")
            
        # Extract timer information
        timer_match = re.search(r'Time.*?(\d+):(\d+)', data)
        if timer_match:
            minutes, seconds = timer_match.groups()
            self.timer_var.set(f"Time: {minutes}:{seconds}")
            
        # Extract flight count
        flight_match = re.search(r'Flight.*?(\d+)', data, re.IGNORECASE)
        if flight_match:
            count = flight_match.group(1)
            self.flights_completed_var.set(f"Flights: {count}")
            
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
            messagebox.showinfo("No Data", "No flight data available. Download flight data first.")
            return

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
            # Parse CSV format from buffer
            lines = self.flight_data_buffer.strip().split('\n')

            flight_header = None
            gps_records = []

            for line in lines:
                line = line.strip()
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
                    # Parse GPS record: GPS,timestamp_ms,flight_state,state_name,latitude,longitude
                    parts = line.split(',')
                    if len(parts) >= 6:
                        gps_records.append({
                            'timestamp_ms': int(parts[1]),
                            'flight_state': int(parts[2]),
                            'state_name': parts[3],
                            'latitude': float(parts[4]),
                            'longitude': float(parts[5])
                        })

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
            import numpy as np
        except ImportError:
            messagebox.showerror("Missing Package",
                               "matplotlib is required for flight path visualization.\n"
                               "Install with: pip install matplotlib")
            return

        # Create visualization window
        viz_window = tk.Toplevel(self.parent)
        viz_window.title("Flight Path Visualization")
        viz_window.geometry("800x600")

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
        states = [p['flight_state'] for p in positions]
        state_names = [p['state_name'] for p in positions]

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

        # Plot 2: Timeline
        ax2.plot(times, states, 'b-', linewidth=2, marker='o')
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Flight State')
        ax2.set_title('Flight State Timeline')
        ax2.grid(True, alpha=0.3)
        ax2.set_yticks([1, 2, 3, 4, 5, 6, 7, 99])
        ax2.set_yticklabels(['Ready', 'Armed', 'Spool', 'Motor', 'Glide', 'DT', 'Post-DT', 'Land'])

        plt.tight_layout()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, viz_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

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
                               'Latitude', 'Longitude'])

                for pos in positions:
                    writer.writerow([
                        pos['timestamp_ms'] / 1000.0,
                        pos['flight_state'],
                        pos['state_name'],
                        pos['latitude'],
                        pos['longitude']
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
                kml_content += f"          {pos['longitude']},{pos['latitude']},0\n"

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

    def get_frame(self):
        """Get the main tab frame."""
        return self.frame