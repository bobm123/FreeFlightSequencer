"""
Parameter Monitor - Passively monitors serial traffic for parameter updates.
Updates local parameter view based on what it sees, no validation or business logic.
"""
import re
from typing import Dict, Any, Optional


class ParameterMonitor:
    """Passively monitors serial traffic and tracks current parameters."""

    def __init__(self):
        self.current_parameters = {}
        self.buffer = ""  # Buffer for incomplete lines

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

    def _check_for_parameters(self, line: str):
        """Check a line for parameter information and update local view."""
        # Look for parameter patterns - just monitor what we see
        patterns = {
            'motor_run_time': r'Motor Run Time.*?(\d+)',
            'total_flight_time': r'Total Flight Time.*?(\d+)',
            'motor_speed': r'Motor Speed.*?(\d+)'
        }

        for param_name, pattern in patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    value = int(match.group(1))
                    self.current_parameters[param_name] = value
                except ValueError:
                    pass

    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values as observed from serial traffic."""
        return self.current_parameters.copy()

    def clear_parameters(self):
        """Clear parameter cache."""
        self.current_parameters.clear()
        self.buffer = ""