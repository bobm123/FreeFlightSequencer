"""
Tab Manager - Manages tab lifecycle and inter-tab communication.
Handles application detection and message routing between tabs.
"""
import re
import time
from typing import Optional, Dict, Callable
from enum import Enum


class ApplicationType(Enum):
    """Detected Arduino application types."""
    FLIGHT_SEQUENCER = "FlightSequencer"
    GPS_AUTOPILOT = "GpsAutopilot" 
    DEVICE_TEST = "DeviceTest"
    UNKNOWN = "Unknown"


class TabManager:
    """Manages tab lifecycle and communication routing."""
    
    def __init__(self, serial_monitor):
        self.serial_monitor = serial_monitor
        self.active_app = ApplicationType.UNKNOWN
        self.tab_handlers = {}
        self.detection_callback = None
        self.last_detection_time = 0
        self.detection_patterns = {
            ApplicationType.FLIGHT_SEQUENCER: [
                r'\[APP\] FlightSequencer',
                r'FlightSequencer.*starting',
                r'FlightSequencer.*ready',
                r'Motor Run Time.*\d+',
                r'Total Flight Time.*\d+',
                r'Phase.*COMPLETE'
            ],
            ApplicationType.GPS_AUTOPILOT: [
                r'\[APP\] GpsAutopilot',
                r'GpsAutopilot.*starting',
                r'GpsAutopilot.*initialized',
                r'GPS Status Report',
                r'Navigation.*datum.*set',
                r'Control.*autonomous.*mode',
                r'GPS.*fix.*acquired',
                r'Fix Status:.*\[OK\]',
                r'Satellites:.*\d+.*tracked',
                r'Position:.*\d+\.\d+.*deg',
                r'NMEA Sentences:.*\d+',
                r'\[GPS_RAW\]',
                r'\[GPS_PARSE\]',
                r'GPS.*ready.*for.*datum',
                r'System.*ready.*GPS.*acquiring',
                r'NAV.*Navigation.*system'
            ],
            ApplicationType.DEVICE_TEST: [
                r'\[APP\] ButtonTest',
                r'\[APP\] LedTest',
                r'\[APP\] ServoTest',
                r'\[APP\] GpsTest',
                r'\[APP\] LedButton',
                r'Device.*Test.*Suite',
                r'Running.*test.*\w+',
                r'Test.*PASS|FAIL',
                r'Hardware.*validation'
            ]
        }
        
    def register_tab(self, app_type: ApplicationType, handler: Callable):
        """Register a tab handler for an application type."""
        self.tab_handlers[app_type] = handler
        
    def set_detection_callback(self, callback: Callable):
        """Set callback for when application type is detected."""
        self.detection_callback = callback
        
    def route_message(self, message: str):
        """Route incoming serial message to appropriate tab and detect application."""
        # Always try to detect application type
        detected_app = self._detect_application(message)
        if detected_app != ApplicationType.UNKNOWN:
            if detected_app != self.active_app:
                self.active_app = detected_app
                if self.detection_callback:
                    self.detection_callback(detected_app)
                    
        # Route to all handlers (they can filter what they want)
        for app_type, handler in self.tab_handlers.items():
            try:
                handler(message)
            except Exception as e:
                print(f"Error in {app_type} handler: {e}")
                
    def _detect_application(self, message: str) -> ApplicationType:
        """Detect application type from serial message patterns."""
        # Avoid rapid re-detection
        current_time = time.time()
        if current_time - self.last_detection_time < 2.0:
            return ApplicationType.UNKNOWN
            
        for app_type, patterns in self.detection_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    self.last_detection_time = current_time
                    return app_type
                    
        return ApplicationType.UNKNOWN
        
    def send_identification_query(self):
        """Send query to identify connected application."""
        if self.serial_monitor and self.serial_monitor.is_connected:
            # Try common identification commands
            commands = ["?", "SYS ID", "STATUS", "G"]
            for cmd in commands:
                self.serial_monitor.send_line(cmd)
                time.sleep(0.1)
                
    def get_active_application(self) -> ApplicationType:
        """Get currently detected application type."""
        return self.active_app
        
    def force_application_type(self, app_type: ApplicationType):
        """Manually set application type (for testing or fallback)."""
        if app_type != self.active_app:
            self.active_app = app_type
            if self.detection_callback:
                self.detection_callback(app_type)

    def reset_detection(self):
        """Reset detection state (call on connect/disconnect)."""
        self.active_app = ApplicationType.UNKNOWN
        self.last_detection_time = 0