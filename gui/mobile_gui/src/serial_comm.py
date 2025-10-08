"""
Mobile Serial Communication Module
Handles serial communication with Arduino for mobile platforms
"""
import threading
import queue
import time


class MobileSerialMonitor:
    """
    Serial communication manager for mobile platforms.
    Handles asynchronous serial I/O with threading.
    """

    def __init__(self):
        self.is_connected = False
        self.serial_port = None
        self.port_name = None
        self.baud_rate = 9600
        self.last_error = None

        # Threading components
        self.read_thread = None
        self.write_queue = queue.Queue()
        self.receive_callbacks = []
        self.running = False

    def connect(self, port, baud_rate=9600):
        """
        Connect to serial port.

        Args:
            port: Serial port name (e.g., '/dev/ttyUSB0' on Android)
            baud_rate: Communication baud rate

        Returns:
            bool: True if connection successful
        """
        try:
            import serial

            self.serial_port = serial.Serial(port, baud_rate, timeout=0.1)
            self.port_name = port
            self.baud_rate = baud_rate
            self.is_connected = True
            self.running = True

            # Start read thread
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

            print(f"[MobileSerial] Connected to {port} at {baud_rate} baud")
            return True

        except Exception as e:
            self.last_error = str(e)
            print(f"[MobileSerial] Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from serial port."""
        self.running = False
        self.is_connected = False

        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)

        if self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None

        print("[MobileSerial] Disconnected")

    def send_line(self, data):
        """
        Send line to serial port (async via queue).

        Args:
            data: String data to send (newline added automatically)
        """
        if not self.is_connected:
            return

        self.write_queue.put(data + '\n')

    def add_receive_callback(self, callback):
        """
        Add callback for received data.

        Args:
            callback: Function(data_string) to call when data received
        """
        self.receive_callbacks.append(callback)

    def _read_loop(self):
        """Background thread for reading serial data."""
        buffer = ""

        while self.running and self.serial_port:
            try:
                # Handle writes from queue
                while not self.write_queue.empty():
                    data = self.write_queue.get_nowait()
                    self.serial_port.write(data.encode('utf-8'))

                # Read available data
                if self.serial_port.in_waiting > 0:
                    chunk = self.serial_port.read(self.serial_port.in_waiting)
                    buffer += chunk.decode('utf-8', errors='ignore')

                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()

                        if line:
                            # Call all registered callbacks
                            for callback in self.receive_callbacks:
                                try:
                                    callback(line)
                                except Exception as e:
                                    print(f"[MobileSerial] Callback error: {e}")

                time.sleep(0.01)  # Small delay to prevent CPU spinning

            except Exception as e:
                if self.running:  # Only log if not intentionally stopping
                    print(f"[MobileSerial] Read error: {e}")
                    self.last_error = str(e)
                time.sleep(0.1)

    def get_available_ports(self):
        """
        Get list of available serial ports.

        Returns:
            list: Available port names
        """
        try:
            import serial.tools.list_ports
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return ports
        except Exception as e:
            print(f"[MobileSerial] Port enumeration error: {e}")
            return []
