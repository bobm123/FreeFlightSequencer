"""
DeviceTest Tab - Interface for hardware validation and system diagnostics.
Provides individual device testing, system integration tests, and diagnostic tools.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import re
import time
import threading
import sys
import os
from typing import Dict, Any, List

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from widgets import SerialMonitorWidget


class DeviceTestTab:
    """Device testing and diagnostics interface."""
    
    def __init__(self, parent, serial_monitor, tab_manager):
        self.parent = parent
        self.serial_monitor = serial_monitor
        self.tab_manager = tab_manager
        
        # Test state tracking
        self.test_results = {}
        self.current_test = None
        self.test_start_time = None
        
        # Available tests
        self.available_tests = {
            'BUTTON': 'Button debouncing and press detection',
            'LED': 'NeoPixel color and brightness control',
            'GPS': 'GPS module communication and fix acquisition',
            'SERVO': 'Servo positioning and calibration',
            'ESC': 'ESC control and arming sequence',
            'ALL': 'Complete system integration test'
        }
        
        # Device status
        self.device_status = {
            'button': {'status': 'Unknown', 'last_update': 0},
            'led': {'status': 'Unknown', 'last_update': 0},
            'gps': {'status': 'Unknown', 'fix': False, 'satellites': 0, 'last_update': 0},
            'servo': {'status': 'Unknown', 'position': 0, 'last_update': 0},
            'esc': {'status': 'Unknown', 'speed': 0, 'armed': False, 'last_update': 0}
        }
        
        # Create main tab frame
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
        # Register with tab manager
        from core.tab_manager import ApplicationType
        tab_manager.register_tab(ApplicationType.DEVICE_TEST, self.handle_serial_data)
        
    def _create_widgets(self):
        """Create DeviceTest interface widgets."""
        # Create paned window for layout
        main_paned = ttk.PanedWindow(self.frame, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Test controls and status
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Serial monitor
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # Create test sections
        self._create_test_selection(left_frame)
        self._create_device_status(left_frame)
        self._create_manual_controls(left_frame)
        
        # Serial monitor
        self.serial_monitor_widget = SerialMonitorWidget(
            right_frame,
            title="Device Test Serial Monitor",
            show_timestamp=True
        )
        self.serial_monitor_widget.pack(fill='both', expand=True)
        self.serial_monitor_widget.set_send_callback(self._send_command)
        
    def _create_test_selection(self, parent):
        """Create test selection and control panel."""
        test_frame = ttk.LabelFrame(parent, text="Test Selection")
        test_frame.pack(fill='x', padx=5, pady=5)
        
        # Individual test buttons
        test_btn_frame = ttk.Frame(test_frame)
        test_btn_frame.pack(fill='x', padx=5, pady=5)
        
        # Create buttons for each test type
        self.test_buttons = {}
        row = 0
        col = 0
        for test_name, description in self.available_tests.items():
            if test_name == 'ALL':
                continue  # Handle separately
                
            btn = ttk.Button(test_btn_frame, text=f"Test {test_name}", width=12,
                           command=lambda t=test_name: self._run_test(t))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            self.test_buttons[test_name] = btn
            
            col += 1
            if col >= 3:  # 3 buttons per row
                col = 0
                row += 1
                
        # Configure column weights
        for i in range(3):
            test_btn_frame.columnconfigure(i, weight=1)
            
        # System test button
        system_frame = ttk.Frame(test_frame)
        system_frame.pack(fill='x', padx=5, pady=5)
        
        self.system_test_btn = ttk.Button(system_frame, text="RUN SYSTEM TEST", 
                                         command=lambda: self._run_test('ALL'))
        self.system_test_btn.pack(side='left', padx=2)
        
        self.stop_test_btn = ttk.Button(system_frame, text="STOP TEST", 
                                       command=self._stop_test, state='disabled')
        self.stop_test_btn.pack(side='left', padx=2)
        
        # Test duration
        ttk.Label(system_frame, text="Duration (min):").pack(side='left', padx=5)
        self.test_duration_var = tk.StringVar(value="5")
        duration_combo = ttk.Combobox(system_frame, textvariable=self.test_duration_var,
                                    values=["1", "5", "10", "30", "60"], width=6, state='readonly')
        duration_combo.pack(side='left', padx=2)
        
        # Test status
        status_frame = ttk.Frame(test_frame)
        status_frame.pack(fill='x', padx=5, pady=5)
        
        self.test_status_var = tk.StringVar(value="No test running")
        ttk.Label(status_frame, textvariable=self.test_status_var).pack(side='left')
        
        self.test_progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.test_progress.pack(side='right', padx=5)
        
    def _create_device_status(self, parent):
        """Create device status monitoring panel."""
        status_frame = ttk.LabelFrame(parent, text="Device Status")
        status_frame.pack(fill='x', padx=5, pady=5)
        
        # Create notebook for device categories
        status_notebook = ttk.Notebook(status_frame)
        status_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Input devices tab
        input_tab = ttk.Frame(status_notebook)
        status_notebook.add(input_tab, text="Inputs")
        
        # Button status
        btn_frame = ttk.LabelFrame(input_tab, text="Button")
        btn_frame.pack(fill='x', padx=5, pady=2)
        
        self.button_status_var = tk.StringVar(value="Status: Unknown")
        ttk.Label(btn_frame, textvariable=self.button_status_var).pack(side='left')
        
        self.button_state_var = tk.StringVar(value="State: Released")
        ttk.Label(btn_frame, textvariable=self.button_state_var).pack(side='right')
        
        # GPS status
        gps_frame = ttk.LabelFrame(input_tab, text="GPS")
        gps_frame.pack(fill='x', padx=5, pady=2)
        
        self.gps_status_var = tk.StringVar(value="Status: Unknown")
        ttk.Label(gps_frame, textvariable=self.gps_status_var).pack(side='left')
        
        gps_details_frame = ttk.Frame(gps_frame)
        gps_details_frame.pack(fill='x')
        
        self.gps_fix_var = tk.StringVar(value="Fix: No")
        ttk.Label(gps_details_frame, textvariable=self.gps_fix_var).pack(side='left')
        
        self.gps_sats_var = tk.StringVar(value="Sats: 0")
        ttk.Label(gps_details_frame, textvariable=self.gps_sats_var).pack(side='right')
        
        # Output devices tab
        output_tab = ttk.Frame(status_notebook)
        status_notebook.add(output_tab, text="Outputs")
        
        # LED status
        led_frame = ttk.LabelFrame(output_tab, text="NeoPixel LED")
        led_frame.pack(fill='x', padx=5, pady=2)
        
        self.led_status_var = tk.StringVar(value="Status: Unknown")
        ttk.Label(led_frame, textvariable=self.led_status_var).pack(side='left')
        
        self.led_color_var = tk.StringVar(value="Color: Off")
        ttk.Label(led_frame, textvariable=self.led_color_var).pack(side='right')
        
        # Servo status
        servo_frame = ttk.LabelFrame(output_tab, text="Servo")
        servo_frame.pack(fill='x', padx=5, pady=2)
        
        self.servo_status_var = tk.StringVar(value="Status: Unknown")
        ttk.Label(servo_frame, textvariable=self.servo_status_var).pack(side='left')
        
        self.servo_pos_var = tk.StringVar(value="Position: 0°")
        ttk.Label(servo_frame, textvariable=self.servo_pos_var).pack(side='right')
        
        # ESC status
        esc_frame = ttk.LabelFrame(output_tab, text="ESC/Motor")
        esc_frame.pack(fill='x', padx=5, pady=2)
        
        self.esc_status_var = tk.StringVar(value="Status: Unknown")
        ttk.Label(esc_frame, textvariable=self.esc_status_var).pack(side='left')
        
        esc_details_frame = ttk.Frame(esc_frame)
        esc_details_frame.pack(fill='x')
        
        self.esc_speed_var = tk.StringVar(value="Speed: 0%")
        ttk.Label(esc_details_frame, textvariable=self.esc_speed_var).pack(side='left')
        
        self.esc_armed_var = tk.StringVar(value="Armed: No")
        ttk.Label(esc_details_frame, textvariable=self.esc_armed_var).pack(side='right')
        
    def _create_manual_controls(self, parent):
        """Create manual device control panel."""
        manual_frame = ttk.LabelFrame(parent, text="Manual Controls")
        manual_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # LED control
        led_frame = ttk.LabelFrame(manual_frame, text="LED Control")
        led_frame.pack(fill='x', padx=5, pady=2)
        
        led_color_frame = ttk.Frame(led_frame)
        led_color_frame.pack(fill='x', padx=5, pady=2)
        
        color_buttons = [
            ("Red", "255,0,0"), ("Green", "0,255,0"), ("Blue", "0,0,255"),
            ("White", "255,255,255"), ("Yellow", "255,255,0"), ("Off", "0,0,0")
        ]
        
        for i, (name, rgb) in enumerate(color_buttons):
            ttk.Button(led_color_frame, text=name, width=8,
                      command=lambda c=rgb: self._set_led_color(c)).grid(row=i//3, column=i%3, padx=1, pady=1)
                      
        # Servo control
        servo_frame = ttk.LabelFrame(manual_frame, text="Servo Control")
        servo_frame.pack(fill='x', padx=5, pady=2)
        
        servo_control_frame = ttk.Frame(servo_frame)
        servo_control_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(servo_control_frame, text="Position (°):").pack(side='left')
        self.servo_pos_var_manual = tk.StringVar(value="90")
        servo_scale = ttk.Scale(servo_control_frame, from_=0, to=180, orient='horizontal',
                              variable=self.servo_pos_var_manual)
        servo_scale.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Button(servo_control_frame, text="Set", 
                  command=self._set_servo_position).pack(side='right')
                  
        # ESC control
        esc_frame = ttk.LabelFrame(manual_frame, text="ESC Control")
        esc_frame.pack(fill='x', padx=5, pady=2)
        
        esc_control_frame = ttk.Frame(esc_frame)
        esc_control_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Button(esc_control_frame, text="ARM", 
                  command=self._arm_esc).pack(side='left', padx=2)
        ttk.Button(esc_control_frame, text="DISARM", 
                  command=self._disarm_esc).pack(side='left', padx=2)
                  
        esc_speed_frame = ttk.Frame(esc_frame)
        esc_speed_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(esc_speed_frame, text="Speed (%):").pack(side='left')
        self.esc_speed_var_manual = tk.StringVar(value="0")
        esc_scale = ttk.Scale(esc_speed_frame, from_=0, to=100, orient='horizontal',
                            variable=self.esc_speed_var_manual)
        esc_scale.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Button(esc_speed_frame, text="Set", 
                  command=self._set_esc_speed).pack(side='right')
                  
    def _send_command(self, command):
        """Send command to device test application."""
        if self.serial_monitor and self.serial_monitor.is_connected:
            self.serial_monitor.send_line(command)
            self.serial_monitor_widget.log_sent(command)
        else:
            messagebox.showwarning("Not Connected", "Please connect to Arduino first")
            
    def _run_test(self, test_name):
        """Run a specific test."""
        if self.current_test:
            messagebox.showwarning("Test Running", "Stop current test before starting a new one")
            return
            
        self.current_test = test_name
        self.test_start_time = time.time()
        
        # Update UI
        self.test_status_var.set(f"Running {test_name} test...")
        self.test_progress.start()
        self.stop_test_btn.config(state='normal')
        
        # Disable test buttons
        for btn in self.test_buttons.values():
            btn.config(state='disabled')
        self.system_test_btn.config(state='disabled')
        
        # Send test command
        if test_name == 'ALL':
            duration = int(self.test_duration_var.get())
            self._send_command(f"TEST ALL {duration}")
        else:
            self._send_command(f"TEST {test_name}")
            
        self.serial_monitor_widget.log_success(f"Started {test_name} test")
        
    def _stop_test(self):
        """Stop current test."""
        if self.current_test:
            self._send_command("TEST STOP")
            self._test_completed(f"{self.current_test} test stopped by user")
            
    def _test_completed(self, result):
        """Handle test completion."""
        self.current_test = None
        self.test_start_time = None
        
        # Update UI
        self.test_status_var.set(f"Test completed: {result}")
        self.test_progress.stop()
        self.stop_test_btn.config(state='disabled')
        
        # Re-enable test buttons
        for btn in self.test_buttons.values():
            btn.config(state='normal')
        self.system_test_btn.config(state='normal')
        
    # Manual control methods
    def _set_led_color(self, rgb):
        """Set LED color manually."""
        self._send_command(f"LED COLOR {rgb}")
        
    def _set_servo_position(self):
        """Set servo position manually."""
        position = int(float(self.servo_pos_var_manual.get()))
        self._send_command(f"SERVO POS {position}")
        
    def _arm_esc(self):
        """ARM ESC."""
        if messagebox.askyesno("ARM ESC", "ARM the ESC? Motor may start spinning."):
            self._send_command("ESC ARM")
            
    def _disarm_esc(self):
        """DISARM ESC."""
        self._send_command("ESC DISARM")
        
    def _set_esc_speed(self):
        """Set ESC speed manually."""
        speed = int(float(self.esc_speed_var_manual.get()))
        if speed > 0:
            if messagebox.askyesno("Set Motor Speed", 
                                  f"Set motor speed to {speed}%? Motor will spin."):
                self._send_command(f"ESC SPEED {speed}")
        else:
            self._send_command(f"ESC SPEED {speed}")
            
    def handle_serial_data(self, data):
        """Handle incoming serial data for DeviceTest."""
        # Display in serial monitor
        self.serial_monitor_widget.log_received(data)
        
        # Parse device status updates
        self._parse_device_status(data)
        
        # Parse test results
        self._parse_test_results(data)
        
        # Update status displays
        self._update_status_displays()
        
    def _parse_device_status(self, data):
        """Parse device status information from serial data."""
        current_time = time.time()
        
        # Button status
        if re.search(r'button.*press', data, re.IGNORECASE):
            self.device_status['button']['status'] = 'Pressed'
            self.device_status['button']['last_update'] = current_time
        elif re.search(r'button.*release', data, re.IGNORECASE):
            self.device_status['button']['status'] = 'Released'
            self.device_status['button']['last_update'] = current_time
        elif re.search(r'button.*ok|pass', data, re.IGNORECASE):
            self.device_status['button']['status'] = 'OK'
            self.device_status['button']['last_update'] = current_time
            
        # GPS status
        gps_fix_match = re.search(r'gps.*fix.*?(true|false|ok|valid)', data, re.IGNORECASE)
        if gps_fix_match:
            self.device_status['gps']['fix'] = gps_fix_match.group(1).lower() in ['true', 'ok', 'valid']
            self.device_status['gps']['status'] = 'Fix OK' if self.device_status['gps']['fix'] else 'No Fix'
            self.device_status['gps']['last_update'] = current_time
            
        sat_match = re.search(r'satellite.*?(\\d+)', data, re.IGNORECASE)
        if sat_match:
            self.device_status['gps']['satellites'] = int(sat_match.group(1))
            self.device_status['gps']['last_update'] = current_time
            
        # LED status
        led_match = re.search(r'led.*color.*?(\\d+,\\d+,\\d+)', data, re.IGNORECASE)
        if led_match:
            rgb = led_match.group(1)
            if rgb == "0,0,0":
                color = "Off"
            elif rgb == "255,0,0":
                color = "Red"
            elif rgb == "0,255,0":
                color = "Green"
            elif rgb == "0,0,255":
                color = "Blue"
            elif rgb == "255,255,255":
                color = "White"
            else:
                color = f"RGB({rgb})"
            self.device_status['led']['status'] = color
            self.device_status['led']['last_update'] = current_time
            
        # Servo status
        servo_match = re.search(r'servo.*position.*?(\\d+)', data, re.IGNORECASE)
        if servo_match:
            position = int(servo_match.group(1))
            self.device_status['servo']['position'] = position
            self.device_status['servo']['status'] = f"{position}°"
            self.device_status['servo']['last_update'] = current_time
            
        # ESC status
        esc_speed_match = re.search(r'esc.*speed.*?(\\d+)', data, re.IGNORECASE)
        if esc_speed_match:
            speed = int(esc_speed_match.group(1))
            self.device_status['esc']['speed'] = speed
            self.device_status['esc']['last_update'] = current_time
            
        if re.search(r'esc.*armed', data, re.IGNORECASE):
            self.device_status['esc']['armed'] = True
            self.device_status['esc']['status'] = 'Armed'
            self.device_status['esc']['last_update'] = current_time
        elif re.search(r'esc.*disarmed', data, re.IGNORECASE):
            self.device_status['esc']['armed'] = False
            self.device_status['esc']['status'] = 'Disarmed'
            self.device_status['esc']['last_update'] = current_time
            
    def _parse_test_results(self, data):
        """Parse test result information."""
        # Test completion
        if re.search(r'test.*complete|finished', data, re.IGNORECASE):
            if self.current_test:
                self._test_completed("COMPLETED")
                
        # Test failure
        if re.search(r'test.*fail', data, re.IGNORECASE):
            if self.current_test:
                self._test_completed("FAILED")
                self.serial_monitor_widget.log_error("Test failed")
                
        # Individual test results
        test_result_match = re.search(r'(\\w+).*test.*?(pass|fail)', data, re.IGNORECASE)
        if test_result_match:
            test_name = test_result_match.group(1).upper()
            result = test_result_match.group(2).upper()
            self.test_results[test_name] = result
            
            if result == "PASS":
                self.serial_monitor_widget.log_success(f"{test_name} test PASSED")
            else:
                self.serial_monitor_widget.log_error(f"{test_name} test FAILED")
                
    def _update_status_displays(self):
        """Update all device status displays."""
        def update_displays():
            current_time = time.time()
            
            # Button status
            btn_status = self.device_status['button']
            age = current_time - btn_status['last_update'] if btn_status['last_update'] else float('inf')
            if age < 5:  # Fresh data
                self.button_status_var.set(f"Status: {btn_status['status']}")
                self.button_state_var.set(f"State: {btn_status['status']}")
            else:
                self.button_status_var.set("Status: Unknown")
                self.button_state_var.set("State: Unknown")
                
            # GPS status
            gps_status = self.device_status['gps']
            age = current_time - gps_status['last_update'] if gps_status['last_update'] else float('inf')
            if age < 10:  # GPS data can be slower
                self.gps_status_var.set(f"Status: {gps_status['status']}")
                self.gps_fix_var.set(f"Fix: {'Yes' if gps_status['fix'] else 'No'}")
                self.gps_sats_var.set(f"Sats: {gps_status['satellites']}")
            else:
                self.gps_status_var.set("Status: Unknown")
                self.gps_fix_var.set("Fix: Unknown")
                self.gps_sats_var.set("Sats: 0")
                
            # LED status
            led_status = self.device_status['led']
            age = current_time - led_status['last_update'] if led_status['last_update'] else float('inf')
            if age < 5:
                self.led_status_var.set("Status: OK")
                self.led_color_var.set(f"Color: {led_status['status']}")
            else:
                self.led_status_var.set("Status: Unknown")
                self.led_color_var.set("Color: Unknown")
                
            # Servo status
            servo_status = self.device_status['servo']
            age = current_time - servo_status['last_update'] if servo_status['last_update'] else float('inf')
            if age < 5:
                self.servo_status_var.set("Status: OK")
                self.servo_pos_var.set(f"Position: {servo_status['position']}°")
            else:
                self.servo_status_var.set("Status: Unknown")
                self.servo_pos_var.set("Position: Unknown")
                
            # ESC status
            esc_status = self.device_status['esc']
            age = current_time - esc_status['last_update'] if esc_status['last_update'] else float('inf')
            if age < 5:
                self.esc_status_var.set(f"Status: {esc_status['status']}")
                self.esc_speed_var.set(f"Speed: {esc_status['speed']}%")
                self.esc_armed_var.set(f"Armed: {'Yes' if esc_status['armed'] else 'No'}")
            else:
                self.esc_status_var.set("Status: Unknown")
                self.esc_speed_var.set("Speed: Unknown")
                self.esc_armed_var.set("Armed: Unknown")
                
        self.parent.after(0, update_displays)
        
    def get_frame(self):
        """Get the main tab frame."""
        return self.frame