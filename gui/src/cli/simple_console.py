"""
Simple Serial Console - Pure serial monitor with parameter display.
No business logic, just serial I/O passthrough with optional parameter monitoring.
"""
import sys
import os
import argparse
import threading

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.communication.simple_serial import SimpleSerialMonitor
from src.core.parameter_monitor import ParameterMonitor


class SimpleSerialConsole:
    """Simple serial monitor console."""

    def __init__(self):
        self.serial_monitor = SimpleSerialMonitor()
        self.param_monitor = ParameterMonitor()
        self.connected = False
        self._input_thread = None
        self._stop_input = False

    def run(self, port=None):
        """Main application loop."""
        print("FlightSequencer Serial Monitor v1.0")
        print("Simple passthrough communication")
        print("=" * 50)

        try:
            if not self._connect(port):
                print("Failed to connect. Exiting.")
                return

            print("Connected! Type commands to send to Arduino.")
            print("Commands: 'status' for connection info, 'params' for current parameters, 'quit' to exit")
            print("-" * 60)

            # Set up serial data callback
            self.serial_monitor.set_receive_callback(self._handle_received_data)

            # Start input thread
            self._stop_input = False
            self._input_thread = threading.Thread(target=self._input_loop, daemon=True)
            self._input_thread.start()

            # Keep main thread alive
            try:
                while self.connected:
                    import time
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nShutting down...")

        finally:
            self._stop_input = True
            if self.connected:
                self.serial_monitor.disconnect()
                print("Disconnected.")

    def _connect(self, port=None) -> bool:
        """Connect to Arduino."""
        if not port:
            port = os.environ.get('ARDUINO_PORT')

        if not port:
            print("No port specified!")
            print("Use: --port COM4 or set ARDUINO_PORT=COM4")
            return False

        print(f"Connecting to {port}...")
        if self.serial_monitor.connect(port):
            print(f"Connected to {port}")
            self.connected = True
            return True
        else:
            print(f"Failed: {self.serial_monitor.last_error}")
            return False

    def _handle_received_data(self, data: str):
        """Handle data received from serial port."""
        # Display received data immediately
        sys.stdout.write(data)
        sys.stdout.flush()

        # Update parameter monitor
        self.param_monitor.process_serial_data(data)

    def _input_loop(self):
        """Handle user input in separate thread."""
        while not self._stop_input and self.connected:
            try:
                user_input = input().strip()

                if user_input.lower() == 'quit':
                    self.connected = False
                    break
                elif user_input.lower() == 'status':
                    self._show_status()
                elif user_input.lower() == 'params':
                    self._show_parameters()
                elif user_input:
                    # Send to Arduino
                    if not self.serial_monitor.send_line(user_input):
                        print(f"Send failed: {self.serial_monitor.last_error}")

            except (EOFError, KeyboardInterrupt):
                self.connected = False
                break

    def _show_status(self):
        """Show connection status."""
        status = self.serial_monitor.get_status()
        print(f"\n--- STATUS ---")
        print(f"Connected: {status['connected']}")
        print(f"Port: {status['port']}")
        if status['last_error']:
            print(f"Last Error: {status['last_error']}")
        print()

    def _show_parameters(self):
        """Show current parameters as observed from serial traffic."""
        params = self.param_monitor.get_parameters()
        print(f"\n--- OBSERVED PARAMETERS ---")
        if not params:
            print("No parameters observed yet (send 'G' to Arduino)")
        else:
            if 'motor_run_time' in params:
                print(f"Motor Run Time: {params['motor_run_time']} seconds")
            if 'total_flight_time' in params:
                print(f"Total Flight Time: {params['total_flight_time']} seconds")
            if 'motor_speed' in params:
                speed = params['motor_speed']
                print(f"Motor Speed: {speed} ({speed * 10}µs PWM)")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Simple FlightSequencer Serial Monitor')
    parser.add_argument('--port', '-p',
                       help='Serial port (e.g., COM4) or use ARDUINO_PORT environment variable')

    args = parser.parse_args()

    app = SimpleSerialConsole()
    app.run(args.port)


if __name__ == '__main__':
    main()