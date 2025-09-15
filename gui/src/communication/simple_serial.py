"""
Simple Serial Monitor - Pure passthrough communication.
No business logic, just serial I/O and display.
"""
import time
import threading
from typing import Optional, Callable


class SimpleSerialMonitor:
    """Simple serial monitor - just sends and receives data."""

    def __init__(self):
        self.connection = None
        self.port = None
        self.is_connected = False
        self.last_error = None
        self.receive_callback = None
        self._stop_monitoring = False
        self._monitor_thread = None

    def connect(self, port: str, baud_rate: int = 9600) -> bool:
        """Connect to serial port."""
        try:
            import serial

            if self.connection:
                self.connection.close()

            self.connection = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=0.1  # Non-blocking reads
            )

            # Wait for Arduino reset
            time.sleep(2)

            self.port = port
            self.is_connected = True
            self.last_error = None

            # Start monitoring thread
            self._stop_monitoring = False
            self._monitor_thread = threading.Thread(target=self._monitor_serial, daemon=True)
            self._monitor_thread.start()

            return True

        except Exception as e:
            self.last_error = f"Connection failed: {str(e)}"
            self.connection = None
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from serial port."""
        self._stop_monitoring = True
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None

        self.is_connected = False
        self.port = None

    def send_line(self, text: str) -> bool:
        """Send a line of text to the device."""
        if not self.is_connected or not self.connection:
            self.last_error = "Not connected"
            return False

        try:
            line = text + '\n'
            self.connection.write(line.encode('utf-8'))
            self.connection.flush()
            return True
        except Exception as e:
            self.last_error = f"Send failed: {str(e)}"
            return False

    def set_receive_callback(self, callback: Callable[[str], None]):
        """Set callback for received data."""
        self.receive_callback = callback

    def _monitor_serial(self):
        """Monitor serial port for incoming data."""
        while not self._stop_monitoring and self.is_connected:
            try:
                if self.connection and self.connection.in_waiting > 0:
                    data = self.connection.read(self.connection.in_waiting)
                    if data and self.receive_callback:
                        text = data.decode('utf-8', errors='ignore')
                        self.receive_callback(text)
                time.sleep(0.01)
            except Exception as e:
                if self.is_connected:  # Only report errors if we're supposed to be connected
                    self.last_error = f"Monitor error: {str(e)}"
                break

    def get_status(self) -> dict:
        """Get connection status."""
        return {
            'connected': self.is_connected,
            'port': self.port,
            'last_error': self.last_error
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()