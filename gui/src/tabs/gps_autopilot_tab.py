"""
GpsAutopilot Tab - Interface for GPS-guided autonomous flight control.
Provides navigation monitoring, control parameter adjustment, and flight status display.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import re
import math
import sys
import os
from typing import Dict, Any

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from widgets import SerialMonitorWidget, ParameterPanel


class GpsAutopilotTab:
    """GPS Autopilot control and monitoring interface."""
    
    def __init__(self, parent, serial_monitor, tab_manager):
        self.parent = parent
        self.serial_monitor = serial_monitor
        self.tab_manager = tab_manager
        
        # Navigation state
        self.nav_data = {
            'datum_lat': 0.0, 'datum_lon': 0.0, 'datum_alt': 0.0,
            'current_lat': 0.0, 'current_lon': 0.0, 'current_alt': 0.0,
            'position_n': 0.0, 'position_e': 0.0, 'position_u': 0.0,
            'range_to_datum': 0.0, 'bearing_to_datum': 0.0,
            'ground_speed': 0.0, 'ground_track': 0.0,
            'nav_mode': 'UNKNOWN', 'gps_fix': False, 'satellites': 0
        }
        
        # Control state
        self.control_data = {
            'flight_mode': 'IDLE', 'control_mode': 'MANUAL',
            'roll_command': 0.0, 'track_command': 0.0,
            'motor_command': 0.0, 'orbit_error': 0.0
        }
        
        # Create main tab frame
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
        # Register with tab manager
        from core.tab_manager import ApplicationType
        tab_manager.register_tab(ApplicationType.GPS_AUTOPILOT, self.handle_serial_data)
        
    def _create_widgets(self):
        """Create GpsAutopilot interface widgets."""
        # Create paned window for layout
        main_paned = ttk.PanedWindow(self.frame, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Controls and status
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Serial monitor
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # Create control sections
        self._create_navigation_controls(left_frame)
        self._create_control_parameters(left_frame)
        self._create_flight_status(left_frame)
        
        # Serial monitor
        self.serial_monitor_widget = SerialMonitorWidget(
            right_frame,
            title="GpsAutopilot Serial Monitor",
            show_timestamp=True
        )
        self.serial_monitor_widget.pack(fill='both', expand=True)
        self.serial_monitor_widget.set_send_callback(self._send_command)
        
    def _create_navigation_controls(self, parent):
        """Create navigation parameter controls."""
        nav_frame = ttk.LabelFrame(parent, text="Navigation Parameters")
        nav_frame.pack(fill='x', padx=5, pady=5)
        
        # Orbit radius
        radius_frame = ttk.Frame(nav_frame)
        radius_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(radius_frame, text="Orbit Radius (m):").pack(side='left')
        self.orbit_radius_var = tk.StringVar(value="100")
        radius_entry = ttk.Entry(radius_frame, textvariable=self.orbit_radius_var, width=8)
        radius_entry.pack(side='left', padx=5)
        ttk.Button(radius_frame, text="Set", command=self._set_orbit_radius).pack(side='left', padx=2)
        
        # Nominal airspeed
        airspeed_frame = ttk.Frame(nav_frame)
        airspeed_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(airspeed_frame, text="Airspeed (m/s):").pack(side='left')
        self.airspeed_var = tk.StringVar(value="12.0")
        airspeed_entry = ttk.Entry(airspeed_frame, textvariable=self.airspeed_var, width=8)
        airspeed_entry.pack(side='left', padx=5)
        ttk.Button(airspeed_frame, text="Set", command=self._set_airspeed).pack(side='left', padx=2)
        
        # GPS settings
        gps_frame = ttk.Frame(nav_frame)
        gps_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(gps_frame, text="GPS Update (Hz):").pack(side='left')
        self.gps_rate_var = tk.StringVar(value="5")
        gps_combo = ttk.Combobox(gps_frame, textvariable=self.gps_rate_var,
                               values=["1", "2", "5", "10"], width=6, state='readonly')
        gps_combo.pack(side='left', padx=5)
        ttk.Button(gps_frame, text="Set", command=self._set_gps_rate).pack(side='left', padx=2)
        
        # Datum controls
        datum_frame = ttk.Frame(nav_frame)
        datum_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(datum_frame, text="Set Datum", command=self._set_datum).pack(side='left', padx=2)
        ttk.Button(datum_frame, text="Clear Datum", command=self._clear_datum).pack(side='left', padx=2)
        
    def _create_control_parameters(self, parent):
        """Create control parameter adjustment."""
        control_frame = ttk.LabelFrame(parent, text="Control Parameters")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Create notebook for parameter groups
        param_notebook = ttk.Notebook(control_frame)
        param_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Orbit control tab
        orbit_tab = ttk.Frame(param_notebook)
        param_notebook.add(orbit_tab, text="Orbit")
        
        # Orbit proportional gain
        orbit_kp_frame = ttk.Frame(orbit_tab)
        orbit_kp_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(orbit_kp_frame, text="Orbit Kp:").pack(side='left')
        self.orbit_kp_var = tk.StringVar(value="0.05")
        orbit_kp_entry = ttk.Entry(orbit_kp_frame, textvariable=self.orbit_kp_var, width=8)
        orbit_kp_entry.pack(side='left', padx=5)
        ttk.Button(orbit_kp_frame, text="Set", command=self._set_orbit_kp).pack(side='left', padx=2)
        
        # Track control tab
        track_tab = ttk.Frame(param_notebook)
        param_notebook.add(track_tab, text="Track")
        
        # Track proportional gain
        track_kp_frame = ttk.Frame(track_tab)
        track_kp_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(track_kp_frame, text="Track Kp:").pack(side='left')
        self.track_kp_var = tk.StringVar(value="1.0")
        track_kp_entry = ttk.Entry(track_kp_frame, textvariable=self.track_kp_var, width=8)
        track_kp_entry.pack(side='left', padx=5)
        ttk.Button(track_kp_frame, text="Set", command=self._set_track_kp).pack(side='left', padx=2)
        
        # Track integral gain
        track_ki_frame = ttk.Frame(track_tab)
        track_ki_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(track_ki_frame, text="Track Ki:").pack(side='left')
        self.track_ki_var = tk.StringVar(value="0.2")
        track_ki_entry = ttk.Entry(track_ki_frame, textvariable=self.track_ki_var, width=8)
        track_ki_entry.pack(side='left', padx=5)
        ttk.Button(track_ki_frame, text="Set", command=self._set_track_ki).pack(side='left', padx=2)
        
        # Roll control tab
        roll_tab = ttk.Frame(param_notebook)
        param_notebook.add(roll_tab, text="Roll")
        
        # Roll proportional gain
        roll_kp_frame = ttk.Frame(roll_tab)
        roll_kp_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(roll_kp_frame, text="Roll Kp:").pack(side='left')
        self.roll_kp_var = tk.StringVar(value="1.5")
        roll_kp_entry = ttk.Entry(roll_kp_frame, textvariable=self.roll_kp_var, width=8)
        roll_kp_entry.pack(side='left', padx=5)
        ttk.Button(roll_kp_frame, text="Set", command=self._set_roll_kp).pack(side='left', padx=2)
        
        # Control action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(action_frame, text="Get All Params", 
                  command=self._get_all_parameters).pack(side='left', padx=2)
        ttk.Button(action_frame, text="Reset Defaults", 
                  command=self._reset_parameters).pack(side='left', padx=2)
        
    def _create_flight_status(self, parent):
        """Create flight status display."""
        status_frame = ttk.LabelFrame(parent, text="Flight Status")
        status_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Navigation status
        nav_status_frame = ttk.LabelFrame(status_frame, text="Navigation")
        nav_status_frame.pack(fill='x', padx=5, pady=2)
        
        # GPS status
        gps_frame = ttk.Frame(nav_status_frame)
        gps_frame.pack(fill='x', padx=5, pady=2)
        self.gps_status_var = tk.StringVar(value="GPS: No Fix")
        ttk.Label(gps_frame, textvariable=self.gps_status_var).pack(side='left')
        self.satellites_var = tk.StringVar(value="Sats: 0")
        ttk.Label(gps_frame, textvariable=self.satellites_var).pack(side='right')
        
        # Position display
        pos_frame = ttk.Frame(nav_status_frame)
        pos_frame.pack(fill='x', padx=5, pady=2)
        self.position_var = tk.StringVar(value="Pos: N=0.0 E=0.0 U=0.0")
        ttk.Label(pos_frame, textvariable=self.position_var, font=('Consolas', 9)).pack()
        
        # Range and bearing
        range_frame = ttk.Frame(nav_status_frame)
        range_frame.pack(fill='x', padx=5, pady=2)
        self.range_var = tk.StringVar(value="Range: 0.0m")
        ttk.Label(range_frame, textvariable=self.range_var).pack(side='left')
        self.bearing_var = tk.StringVar(value="Bearing: 0°")
        ttk.Label(range_frame, textvariable=self.bearing_var).pack(side='right')
        
        # Control status
        ctrl_status_frame = ttk.LabelFrame(status_frame, text="Control")
        ctrl_status_frame.pack(fill='x', padx=5, pady=2)
        
        # Flight mode
        mode_frame = ttk.Frame(ctrl_status_frame)
        mode_frame.pack(fill='x', padx=5, pady=2)
        self.flight_mode_var = tk.StringVar(value="Mode: IDLE")
        ttk.Label(mode_frame, textvariable=self.flight_mode_var).pack(side='left')
        self.nav_mode_var = tk.StringVar(value="Nav: UNKNOWN")
        ttk.Label(mode_frame, textvariable=self.nav_mode_var).pack(side='right')
        
        # Control outputs
        output_frame = ttk.Frame(ctrl_status_frame)
        output_frame.pack(fill='x', padx=5, pady=2)
        self.roll_cmd_var = tk.StringVar(value="Roll: 0.0°")
        ttk.Label(output_frame, textvariable=self.roll_cmd_var).pack(side='left')
        self.motor_cmd_var = tk.StringVar(value="Motor: 0%")
        ttk.Label(output_frame, textvariable=self.motor_cmd_var).pack(side='right')
        
        # Control buttons
        control_btn_frame = ttk.Frame(status_frame)
        control_btn_frame.pack(fill='x', padx=5, pady=5)
        
        self.arm_btn = ttk.Button(control_btn_frame, text="ARM", 
                                 command=self._toggle_arm_disarm)
        self.arm_btn.pack(side='left', padx=2)
        
        ttk.Button(control_btn_frame, text="EMERGENCY", 
                  command=self._emergency_stop).pack(side='right', padx=2)
                  
    def _send_command(self, command):
        """Send command to GpsAutopilot."""
        if self.serial_monitor and self.serial_monitor.is_connected:
            self.serial_monitor.send_line(command)
            self.serial_monitor_widget.log_sent(command)
        else:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            
    # Navigation parameter setters
    def _set_orbit_radius(self):
        """Set orbit radius parameter."""
        try:
            radius = float(self.orbit_radius_var.get())
            if not (20 <= radius <= 500):
                raise ValueError("Orbit radius must be 20-500 meters")
            self._send_command(f"NAV SET RADIUS {radius}")
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            
    def _set_airspeed(self):
        """Set nominal airspeed parameter."""
        try:
            airspeed = float(self.airspeed_var.get())
            if not (5.0 <= airspeed <= 25.0):
                raise ValueError("Airspeed must be 5.0-25.0 m/s")
            self._send_command(f"NAV SET AIRSPEED {airspeed}")
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            
    def _set_gps_rate(self):
        """Set GPS update rate."""
        rate = self.gps_rate_var.get()
        self._send_command(f"NAV SET GPS_RATE {rate}")
        
    def _set_datum(self):
        """Set current position as datum."""
        if messagebox.askyesno("Set Datum", 
                              "Set current GPS position as orbit center?"):
            self._send_command("NAV SET_DATUM")
            
    def _clear_datum(self):
        """Clear current datum."""
        if messagebox.askyesno("Clear Datum", "Clear current datum point?"):
            self._send_command("NAV CLEAR_DATUM")
            
    # Control parameter setters
    def _set_orbit_kp(self):
        """Set orbit controller proportional gain."""
        try:
            kp = float(self.orbit_kp_var.get())
            if not (0.001 <= kp <= 1.0):
                raise ValueError("Orbit Kp must be 0.001-1.0")
            self._send_command(f"CTRL SET ORBIT_KP {kp}")
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            
    def _set_track_kp(self):
        """Set track controller proportional gain."""
        try:
            kp = float(self.track_kp_var.get())
            if not (0.1 <= kp <= 10.0):
                raise ValueError("Track Kp must be 0.1-10.0")
            self._send_command(f"CTRL SET TRACK_KP {kp}")
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            
    def _set_track_ki(self):
        """Set track controller integral gain."""
        try:
            ki = float(self.track_ki_var.get())
            if not (0.0 <= ki <= 2.0):
                raise ValueError("Track Ki must be 0.0-2.0")
            self._send_command(f"CTRL SET TRACK_KI {ki}")
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            
    def _set_roll_kp(self):
        """Set roll controller proportional gain."""
        try:
            kp = float(self.roll_kp_var.get())
            if not (0.1 <= kp <= 5.0):
                raise ValueError("Roll Kp must be 0.1-5.0")
            self._send_command(f"CTRL SET ROLL_KP {kp}")
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            
    def _get_all_parameters(self):
        """Get all parameters from autopilot."""
        self._send_command("GET ALL")
        
    def _reset_parameters(self):
        """Reset all parameters to defaults."""
        if messagebox.askyesno("Reset Parameters", 
                              "Reset all parameters to factory defaults?"):
            self._send_command("RESET ALL")
            
    def _toggle_arm_disarm(self):
        """Toggle ARM/DISARM state."""
        current_text = self.arm_btn['text']
        if current_text == "ARM":
            if messagebox.askyesno("ARM Autopilot", 
                                  "Enable autonomous flight control?"):
                self._send_command("CTRL ARM")
                self.arm_btn.config(text="DISARM")
        else:
            if messagebox.askyesno("DISARM Autopilot", 
                                  "Disable autonomous flight control?"):
                self._send_command("CTRL DISARM")
                self.arm_btn.config(text="ARM")
                
    def _emergency_stop(self):
        """Emergency stop and disarm."""
        if messagebox.askyesno("EMERGENCY STOP", 
                              "Send emergency stop command?"):
            self._send_command("SYS EMERGENCY")
            self.arm_btn.config(text="ARM")
            self.serial_monitor_widget.log_error("EMERGENCY STOP SENT")
            
    def handle_serial_data(self, data):
        """Handle incoming serial data for GpsAutopilot."""
        # Display in serial monitor
        self.serial_monitor_widget.log_received(data)
        
        # Parse navigation data
        self._parse_navigation_data(data)
        
        # Parse control data
        self._parse_control_data(data)
        
        # Update displays
        self._update_status_displays()
        
    def _parse_navigation_data(self, data):
        """Parse navigation information from serial data."""
        # GPS fix status
        gps_fix_match = re.search(r'GPS.*fix.*?(true|false|ok|valid)', data, re.IGNORECASE)
        if gps_fix_match:
            self.nav_data['gps_fix'] = gps_fix_match.group(1).lower() in ['true', 'ok', 'valid']
            
        # Satellite count
        sat_match = re.search(r'sat.*?(\d+)', data, re.IGNORECASE)
        if sat_match:
            self.nav_data['satellites'] = int(sat_match.group(1))
            
        # Position data (N/E/U format)
        pos_match = re.search(r'pos.*?n[=:]?([-+]?\\d*\\.?\\d+).*?e[=:]?([-+]?\\d*\\.?\\d+).*?u[=:]?([-+]?\\d*\\.?\\d+)', data, re.IGNORECASE)
        if pos_match:
            self.nav_data['position_n'] = float(pos_match.group(1))
            self.nav_data['position_e'] = float(pos_match.group(2))
            self.nav_data['position_u'] = float(pos_match.group(3))
            
        # Range and bearing
        range_match = re.search(r'range.*?(\\d*\\.?\\d+)', data, re.IGNORECASE)
        if range_match:
            self.nav_data['range_to_datum'] = float(range_match.group(1))
            
        bearing_match = re.search(r'bearing.*?(\\d*\\.?\\d+)', data, re.IGNORECASE)
        if bearing_match:
            self.nav_data['bearing_to_datum'] = float(bearing_match.group(1))
            
        # Navigation mode
        nav_mode_match = re.search(r'nav.*mode.*?([A-Z_]+)', data, re.IGNORECASE)
        if nav_mode_match:
            self.nav_data['nav_mode'] = nav_mode_match.group(1).upper()
            
    def _parse_control_data(self, data):
        """Parse control information from serial data."""
        # Flight mode
        flight_mode_match = re.search(r'flight.*mode.*?([A-Z_]+)', data, re.IGNORECASE)
        if flight_mode_match:
            self.control_data['flight_mode'] = flight_mode_match.group(1).upper()
            
        # Roll command
        roll_match = re.search(r'roll.*cmd.*?([-+]?\\d*\\.?\\d+)', data, re.IGNORECASE)
        if roll_match:
            self.control_data['roll_command'] = float(roll_match.group(1))
            
        # Motor command
        motor_match = re.search(r'motor.*cmd.*?(\\d*\\.?\\d+)', data, re.IGNORECASE)
        if motor_match:
            self.control_data['motor_command'] = float(motor_match.group(1))
            
        # Control mode (ARM/DISARM status)
        if re.search(r'armed', data, re.IGNORECASE):
            self.control_data['control_mode'] = 'ARMED'
            self.arm_btn.config(text="DISARM")
        elif re.search(r'disarmed', data, re.IGNORECASE):
            self.control_data['control_mode'] = 'DISARMED'
            self.arm_btn.config(text="ARM")
            
    def _update_status_displays(self):
        """Update all status displays."""
        def update_displays():
            # GPS status
            if self.nav_data['gps_fix']:
                self.gps_status_var.set("GPS: Fix OK")
            else:
                self.gps_status_var.set("GPS: No Fix")
                
            self.satellites_var.set(f"Sats: {self.nav_data['satellites']}")
            
            # Position
            n = self.nav_data['position_n']
            e = self.nav_data['position_e']
            u = self.nav_data['position_u']
            self.position_var.set(f"Pos: N={n:.1f} E={e:.1f} U={u:.1f}")
            
            # Range and bearing
            self.range_var.set(f"Range: {self.nav_data['range_to_datum']:.1f}m")
            self.bearing_var.set(f"Bearing: {self.nav_data['bearing_to_datum']:.0f}°")
            
            # Modes
            self.flight_mode_var.set(f"Mode: {self.control_data['flight_mode']}")
            self.nav_mode_var.set(f"Nav: {self.nav_data['nav_mode']}")
            
            # Control outputs
            self.roll_cmd_var.set(f"Roll: {self.control_data['roll_command']:.1f}°")
            self.motor_cmd_var.set(f"Motor: {self.control_data['motor_command']:.0f}%")
            
        self.parent.after(0, update_displays)
        
    def get_frame(self):
        """Get the main tab frame."""
        return self.frame