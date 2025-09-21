"""
Parameter Monitor - Enhanced multi-application parameter monitoring.
Monitors serial traffic for parameter updates from different Arduino applications.
"""
import re
from typing import Dict, Any, Optional
from enum import Enum


class ApplicationType(Enum):
    """Arduino application types."""
    FLIGHT_SEQUENCER = "FlightSequencer"
    GPS_AUTOPILOT = "GpsAutopilot"
    DEVICE_TEST = "DeviceTest"
    UNKNOWN = "Unknown"


class ParameterMonitor:
    """Enhanced parameter monitor supporting multiple applications."""

    def __init__(self):
        self.current_parameters = {}
        self.buffer = ""  # Buffer for incomplete lines
        self.app_type = ApplicationType.UNKNOWN
        
        # Parameter patterns for different applications
        self.parameter_patterns = {
            ApplicationType.FLIGHT_SEQUENCER: {
                'motor_run_time': r'Motor Run Time:\s*(\d+)\s*seconds?',
                'total_flight_time': r'Total Flight Time:\s*(\d+)\s*seconds?',
                'motor_speed': r'Motor Speed:\s*(\d+)',
                'current_phase': r'Phase.*?([A-Z_]+)',
                'flight_timer': r'Time.*?(\d+):(\d+)',
                'flights_completed': r'Flight.*?(\d+)'
            },
            ApplicationType.GPS_AUTOPILOT: {
                'orbit_radius': r'Orbit Radius.*?(\d*\.?\d+)',
                'airspeed': r'Airspeed.*?(\d*\.?\d+)',
                'gps_rate': r'GPS Rate.*?(\d+)',
                'orbit_kp': r'Orbit Kp.*?(\d*\.?\d+)',
                'track_kp': r'Track Kp.*?(\d*\.?\d+)',
                'track_ki': r'Track Ki.*?(\d*\.?\d+)',
                'roll_kp': r'Roll Kp.*?(\d*\.?\d+)',
                'nav_mode': r'Nav Mode.*?([A-Z_]+)',
                'flight_mode': r'Flight Mode.*?([A-Z_]+)',
                'gps_fix': r'GPS.*fix.*?(true|false|ok|valid)',
                'satellites': r'Satellite.*?(\d+)',
                'position_n': r'North.*?(-?\d*\.?\d+)',
                'position_e': r'East.*?(-?\d*\.?\d+)',
                'range_to_datum': r'Range.*?(\d*\.?\d+)',
                'bearing_to_datum': r'Bearing.*?(\d*\.?\d+)'
            },
            ApplicationType.DEVICE_TEST: {
                'test_status': r'Test.*?([A-Z_]+)',
                'test_result': r'(\w+).*test.*?(pass|fail)',
                'button_state': r'Button.*?(pressed|released)',
                'gps_satellites': r'GPS.*satellites.*?(\d+)',
                'servo_position': r'Servo.*position.*?(\d+)',
                'esc_speed': r'ESC.*speed.*?(\d+)',
                'esc_armed': r'ESC.*(armed|disarmed)'
            }
        }

    def set_application_type(self, app_type: ApplicationType):
        """Set the expected application type for parameter parsing."""
        if app_type != self.app_type:
            self.app_type = app_type
            # Clear parameters when switching apps
            self.current_parameters.clear()

    def process_serial_data(self, data: str):
        """Process incoming serial data and update parameters if found."""
        # Add to buffer and process complete lines
        self.buffer += data
        lines = self.buffer.split('\n')

        # Keep the last incomplete line in buffer
        self.buffer = lines[-1]

        # Process complete lines
        for line in lines[:-1]:
            line = line.strip()
            if line:
                self._check_for_parameters(line)
                self._auto_detect_app_type(line)

    def _auto_detect_app_type(self, line: str):
        """Auto-detect application type from serial output."""
        # FlightSequencer patterns
        if re.search(r'FlightSequencer|Motor Run Time|Flight Time.*complete', line, re.IGNORECASE):
            if self.app_type != ApplicationType.FLIGHT_SEQUENCER:
                self.set_application_type(ApplicationType.FLIGHT_SEQUENCER)
                
        # GpsAutopilot patterns  
        elif re.search(r'GpsAutopilot|Orbit.*Radius|Nav.*Mode|GPS.*fix', line, re.IGNORECASE):
            if self.app_type != ApplicationType.GPS_AUTOPILOT:
                self.set_application_type(ApplicationType.GPS_AUTOPILOT)
                
        # DeviceTest patterns
        elif re.search(r'Device.*Test|Running.*test|Test.*PASS|Test.*FAIL', line, re.IGNORECASE):
            if self.app_type != ApplicationType.DEVICE_TEST:
                self.set_application_type(ApplicationType.DEVICE_TEST)

    def _check_for_parameters(self, line: str):
        """Check a line for parameter information and update local view."""
        if self.app_type == ApplicationType.UNKNOWN:
            return
            
        patterns = self.parameter_patterns.get(self.app_type, {})
        
        for param_name, pattern in patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    # Handle different parameter types
                    if param_name in ['gps_fix']:
                        # Boolean parameters
                        value = match.group(1).lower() in ['true', 'ok', 'valid']
                    elif param_name in ['current_phase', 'nav_mode', 'flight_mode', 'test_status', 
                                      'button_state', 'esc_armed']:
                        # String parameters
                        value = match.group(1).upper()
                    elif param_name == 'flight_timer':
                        # Special case for timer format (mm:ss)
                        minutes, seconds = match.groups()
                        value = f"{minutes}:{seconds}"
                    elif param_name == 'test_result':
                        # Special case for test results
                        test_name = match.group(1).upper()
                        result = match.group(2).upper()
                        # Store as nested dict
                        if 'test_results' not in self.current_parameters:
                            self.current_parameters['test_results'] = {}
                        self.current_parameters['test_results'][test_name] = result
                        continue
                    elif '.' in match.group(1):
                        # Float parameters
                        value = float(match.group(1))
                    else:
                        # Integer parameters
                        value = int(match.group(1))
                        
                    self.current_parameters[param_name] = value
                except (ValueError, IndexError):
                    pass

    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values as observed from serial traffic."""
        return self.current_parameters.copy()

    def get_parameter(self, param_name: str) -> Any:
        """Get a specific parameter value."""
        return self.current_parameters.get(param_name)

    def clear_parameters(self):
        """Clear parameter cache."""
        self.current_parameters.clear()
        self.buffer = ""

    def get_application_type(self) -> ApplicationType:
        """Get currently detected application type."""
        return self.app_type