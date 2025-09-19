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

        # Rate limiting for updates
        self.last_update_time = 0
        self.update_interval = 0.1  # Limit updates to 10Hz

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

        # Servo configuration state
        self.servo_config_data = {
            'center': 1500, 'range': 400, 'direction': 'Normal',
            'updated': False
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

        # Servo configuration tab
        servo_tab = ttk.Frame(param_notebook)
        param_notebook.add(servo_tab, text="Servo")

        # Roll servo direction
        direction_frame = ttk.Frame(servo_tab)
        direction_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(direction_frame, text="Direction:").pack(side='left')
        self.servo_direction_var = tk.StringVar(value="Normal")
        direction_combo = ttk.Combobox(direction_frame, textvariable=self.servo_direction_var,
                                      values=["Normal", "Inverted"], width=10, state='readonly')
        direction_combo.pack(side='left', padx=5)
        ttk.Button(direction_frame, text="Set", command=self._set_servo_direction).pack(side='left', padx=2)

        # Roll servo center
        center_frame = ttk.Frame(servo_tab)
        center_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(center_frame, text="Center (μs):").pack(side='left')
        self.servo_center_var = tk.StringVar(value="1500")
        center_entry = ttk.Entry(center_frame, textvariable=self.servo_center_var, width=8)
        center_entry.pack(side='left', padx=5)
        ttk.Button(center_frame, text="Set", command=self._set_servo_center).pack(side='left', padx=2)

        # Roll servo range
        range_frame = ttk.Frame(servo_tab)
        range_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(range_frame, text="Range (μs):").pack(side='left')
        self.servo_range_var = tk.StringVar(value="400")
        range_entry = ttk.Entry(range_frame, textvariable=self.servo_range_var, width=8)
        range_entry.pack(side='left', padx=5)
        ttk.Button(range_frame, text="Set", command=self._set_servo_range).pack(side='left', padx=2)

        # Servo status display
        servo_status_frame = ttk.LabelFrame(servo_tab, text="Servo Status")
        servo_status_frame.pack(fill='x', padx=5, pady=5)

        # Current configuration display
        self.servo_config_var = tk.StringVar(value="Config: Center=1500μs Range=400μs Dir=Normal")
        ttk.Label(servo_status_frame, textvariable=self.servo_config_var,
                 font=('Consolas', 9)).pack(padx=5, pady=2)

        # Servo action buttons
        servo_action_frame = ttk.Frame(servo_tab)
        servo_action_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(servo_action_frame, text="Get Config",
                  command=self._get_servo_config).pack(side='left', padx=2)
        ttk.Button(servo_action_frame, text="Test Servo",
                  command=self._test_servo).pack(side='left', padx=2)
        
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
        self.bearing_var = tk.StringVar(value="Bearing: 0deg")
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
        self.roll_cmd_var = tk.StringVar(value="Roll: 0.0deg")
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

    # Servo configuration functions
    def _set_servo_direction(self):
        """Set roll servo direction."""
        direction = self.servo_direction_var.get()
        reversed_val = "1" if direction == "Inverted" else "0"
        self._send_command(f"SERVO SET DIRECTION {reversed_val}")

    def _set_servo_center(self):
        """Set roll servo center position."""
        try:
            center = float(self.servo_center_var.get())
            if not (1400 <= center <= 1600):
                raise ValueError("Center must be 1400-1600 μs")
            self._send_command(f"SERVO SET CENTER {center}")
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))

    def _set_servo_range(self):
        """Set roll servo range."""
        try:
            range_val = float(self.servo_range_var.get())
            if not (200 <= range_val <= 600):
                raise ValueError("Range must be 200-600 μs")
            self._send_command(f"SERVO SET RANGE {range_val}")
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))

    def _get_servo_config(self):
        """Get current servo configuration."""
        self._send_command("SERVO GET")

    def _test_servo(self):
        """Test servo movement."""
        if messagebox.askyesno("Test Servo",
                              "Move servo through full range? Ensure aircraft is secure."):
            self._send_command("SERVO TEST")
            
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
        try:
            # Display in serial monitor
            self.serial_monitor_widget.log_received(data)

            # Parse navigation data
            self._parse_navigation_data(data)

            # Parse control data
            self._parse_control_data(data)

            # Parse servo data
            self._parse_servo_data(data)

            # Update displays with rate limiting
            import time
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                self._update_status_displays()
                self.last_update_time = current_time
        except Exception as e:
            print(f"Error handling GPS autopilot data: {e}")
            # Still display the raw data in serial monitor even if parsing fails
            try:
                self.serial_monitor_widget.log_received(data)
            except:
                pass
        
    def _parse_navigation_data(self, data):
        """Parse navigation information from serial data."""
        try:
            # GPS fix status - check multiple formats
            gps_fix_match = re.search(r'Fix Status:.*\[OK\]|GPS.*fix.*?(true|false|ok|valid)', data, re.IGNORECASE)
            if gps_fix_match:
                if '[OK]' in data:
                    self.nav_data['gps_fix'] = True
                elif gps_fix_match.group(1):
                    self.nav_data['gps_fix'] = gps_fix_match.group(1).lower() in ['true', 'ok', 'valid']
                else:
                    self.nav_data['gps_fix'] = False

            # Satellite count
            sat_match = re.search(r'Satellites:\s*(\d+)|sat.*?(\d+)', data, re.IGNORECASE)
            if sat_match:
                # Use first group if it matches, otherwise second group
                sat_count = sat_match.group(1) if sat_match.group(1) else sat_match.group(2)
                self.nav_data['satellites'] = int(sat_count)

            # Position data (N/E/U format)
            pos_match = re.search(r'pos.*?n[=:]?([-+]?\d*\.?\d+).*?e[=:]?([-+]?\d*\.?\d+).*?u[=:]?([-+]?\d*\.?\d+)', data, re.IGNORECASE)
            if pos_match:
                self.nav_data['position_n'] = float(pos_match.group(1))
                self.nav_data['position_e'] = float(pos_match.group(2))
                self.nav_data['position_u'] = float(pos_match.group(3))

            # Range and bearing
            range_match = re.search(r'range.*?(\d*\.?\d+)', data, re.IGNORECASE)
            if range_match:
                self.nav_data['range_to_datum'] = float(range_match.group(1))

            bearing_match = re.search(r'bearing.*?(\d*\.?\d+)', data, re.IGNORECASE)
            if bearing_match:
                self.nav_data['bearing_to_datum'] = float(bearing_match.group(1))

            # Navigation mode
            nav_mode_match = re.search(r'nav.*mode.*?([A-Z_]+)', data, re.IGNORECASE)
            if nav_mode_match:
                self.nav_data['nav_mode'] = nav_mode_match.group(1).upper()
        except Exception as e:
            print(f"Error parsing navigation data: {e}")
            
    def _parse_control_data(self, data):
        """Parse control information from serial data."""
        # Flight mode
        flight_mode_match = re.search(r'flight.*mode.*?([A-Z_]+)', data, re.IGNORECASE)
        if flight_mode_match:
            self.control_data['flight_mode'] = flight_mode_match.group(1).upper()
            
        # Roll command
        roll_match = re.search(r'roll.*cmd.*?([-+]?\d*\.?\d+)', data, re.IGNORECASE)
        if roll_match:
            self.control_data['roll_command'] = float(roll_match.group(1))

        # Motor command
        motor_match = re.search(r'motor.*cmd.*?(\d*\.?\d+)', data, re.IGNORECASE)
        if motor_match:
            self.control_data['motor_command'] = float(motor_match.group(1))
            
        # Control mode (ARM/DISARM status) - store data only, update GUI later
        if re.search(r'armed', data, re.IGNORECASE):
            self.control_data['control_mode'] = 'ARMED'
        elif re.search(r'disarmed', data, re.IGNORECASE):
            self.control_data['control_mode'] = 'DISARMED'

    def _parse_servo_data(self, data):
        """Parse servo configuration information from serial data."""
        # Servo configuration responses - store data only, update GUI later
        if '[SERVO]' in data:
            # Center position
            center_match = re.search(r'center.*?(\d+\.?\d*)', data, re.IGNORECASE)
            if center_match:
                center = float(center_match.group(1))
                self.servo_config_data['center'] = int(center)

            # Range
            range_match = re.search(r'range.*?(\d+\.?\d*)', data, re.IGNORECASE)
            if range_match:
                range_val = float(range_match.group(1))
                self.servo_config_data['range'] = int(range_val)

            # Direction
            if 'inverted' in data.lower():
                self.servo_config_data['direction'] = "Inverted"
            elif 'normal' in data.lower():
                self.servo_config_data['direction'] = "Normal"

            # Set flag for GUI update
            self.servo_config_data['updated'] = True
            
    def _update_status_displays(self):
        """Update all status displays."""
        def update_displays():
            # Update ARM/DISARM button based on control mode
            if self.control_data.get('control_mode') == 'ARMED':
                self.arm_btn.config(text="DISARM")
            elif self.control_data.get('control_mode') == 'DISARMED':
                self.arm_btn.config(text="ARM")

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
            self.bearing_var.set(f"Bearing: {self.nav_data['bearing_to_datum']:.0f}deg")
            
            # Modes
            self.flight_mode_var.set(f"Mode: {self.control_data['flight_mode']}")
            self.nav_mode_var.set(f"Nav: {self.nav_data['nav_mode']}")
            
            # Control outputs
            self.roll_cmd_var.set(f"Roll: {self.control_data['roll_command']:.1f}deg")
            self.motor_cmd_var.set(f"Motor: {self.control_data['motor_command']:.0f}%")

            # Update servo configuration if changed
            if self.servo_config_data['updated']:
                self.servo_center_var.set(str(self.servo_config_data['center']))
                self.servo_range_var.set(str(self.servo_config_data['range']))
                self.servo_direction_var.set(self.servo_config_data['direction'])

                # Update servo display
                center = self.servo_config_data['center']
                range_val = self.servo_config_data['range']
                direction = self.servo_config_data['direction']
                config_text = f"Config: Center={center}μs Range={range_val}μs Dir={direction}"
                self.servo_config_var.set(config_text)

                # Reset update flag
                self.servo_config_data['updated'] = False

        self.parent.after(0, update_displays)

    def _update_servo_config_display(self):
        """Update servo configuration display (called by user input)."""
        center = self.servo_center_var.get()
        range_val = self.servo_range_var.get()
        direction = self.servo_direction_var.get()
        config_text = f"Config: Center={center}μs Range={range_val}μs Dir={direction}"
        self.servo_config_var.set(config_text)
        
    def get_frame(self):
        """Get the main tab frame."""
        return self.frame