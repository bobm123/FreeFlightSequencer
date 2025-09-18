"""
FlightSequencer Tab - Enhanced interface for FlightSequencer control.
Refactored from original simple_gui.py with additional features.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re
import json
import os
import sys
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
        
    def _update_current_params(self):
        """Update the current parameters display."""
        def update_params():
            params = self.param_monitor.get_parameters()
            
            self.current_params_text.config(state='normal')
            self.current_params_text.delete(1.0, tk.END)
            
            if params:
                if 'motor_run_time' in params:
                    self.current_params_text.insert(tk.END, f"Motor Time: {params['motor_run_time']}s\\n")
                if 'total_flight_time' in params:
                    self.current_params_text.insert(tk.END, f"Flight Time: {params['total_flight_time']}s\\n")
                if 'motor_speed' in params:
                    speed = params['motor_speed']
                    self.current_params_text.insert(tk.END, f"Motor Speed: {speed}\\n")
                    self.current_params_text.insert(tk.END, f"PWM: {speed * 10}us\\n")
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
            
    def get_frame(self):
        """Get the main tab frame."""
        return self.frame