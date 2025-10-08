"""
GPS Autopilot Tab for Kivy Mobile GUI
Touch-optimized GPS navigation monitoring
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty
from kivy.metrics import dp


class GpsAutopilotTab(BoxLayout):
    """GPS Autopilot monitoring and control tab."""

    # Navigation data properties
    gps_fix = StringProperty('No Fix')
    satellites = NumericProperty(0)
    position_text = StringProperty('N=0.0 E=0.0 U=0.0')
    range_text = StringProperty('Range: 0.0m')
    bearing_text = StringProperty('Bearing: 0deg')

    def __init__(self, serial_monitor, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)

        self.serial_monitor = serial_monitor
        serial_monitor.add_receive_callback(self.handle_serial_data)

        self._create_widgets()

    def _create_widgets(self):
        """Create the GPS autopilot UI."""
        # Status header
        status_label = Label(
            text='GPS Autopilot',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(20),
            bold=True
        )
        self.add_widget(status_label)

        # GPS status display
        gps_grid = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(200),
            padding=dp(10)
        )

        self.gps_status_label = Label(text=f'GPS: {self.gps_fix}')
        gps_grid.add_widget(self.gps_status_label)

        self.sat_label = Label(text=f'Satellites: {self.satellites}')
        gps_grid.add_widget(self.sat_label)

        self.pos_label = Label(text=self.position_text, font_name='RobotoMono-Regular')
        gps_grid.add_widget(self.pos_label)

        self.range_label = Label(text=self.range_text)
        gps_grid.add_widget(self.range_label)

        self.bearing_label = Label(text=self.bearing_text)
        gps_grid.add_widget(self.bearing_label)

        self.add_widget(gps_grid)

        # Control buttons
        btn_grid = GridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(200),
            padding=dp(10)
        )

        set_datum_btn = Button(text='Set Datum', on_press=lambda x: self._set_datum())
        btn_grid.add_widget(set_datum_btn)

        clear_datum_btn = Button(text='Clear Datum', on_press=lambda x: self._clear_datum())
        btn_grid.add_widget(clear_datum_btn)

        arm_btn = Button(text='ARM', on_press=lambda x: self._arm())
        btn_grid.add_widget(arm_btn)

        disarm_btn = Button(text='DISARM', on_press=lambda x: self._disarm())
        btn_grid.add_widget(disarm_btn)

        get_params_btn = Button(text='Get Parameters', on_press=lambda x: self._get_params())
        btn_grid.add_widget(get_params_btn)

        emergency_btn = Button(
            text='EMERGENCY',
            background_color=(0.7, 0, 0, 1),
            on_press=lambda x: self._emergency()
        )
        btn_grid.add_widget(emergency_btn)

        self.add_widget(btn_grid)

    def _send_command(self, command):
        """Send command to Arduino."""
        if self.serial_monitor.is_connected:
            self.serial_monitor.send_line(command)
            print(f"[GpsAutopilot] Sent: {command}")

    def _set_datum(self):
        """Set current position as datum."""
        self._send_command("NAV SET_DATUM")

    def _clear_datum(self):
        """Clear datum."""
        self._send_command("NAV CLEAR_DATUM")

    def _arm(self):
        """Arm autopilot."""
        self._send_command("CTRL ARM")

    def _disarm(self):
        """Disarm autopilot."""
        self._send_command("CTRL DISARM")

    def _get_params(self):
        """Get all parameters."""
        self._send_command("GET ALL")

    def _emergency(self):
        """Emergency stop."""
        self._send_command("SYS EMERGENCY")

    def handle_serial_data(self, data):
        """Handle incoming serial data."""
        import re

        # Parse GPS fix
        if 'Fix OK' in data or 'fix.*true' in data.lower():
            self.gps_fix = 'Fix OK'
        elif 'No Fix' in data or 'fix.*false' in data.lower():
            self.gps_fix = 'No Fix'

        # Parse satellite count
        sat_match = re.search(r'Satellites:\s*(\d+)', data, re.IGNORECASE)
        if sat_match:
            self.satellites = int(sat_match.group(1))

        # Parse position
        pos_match = re.search(r'pos.*?n[=:]?([-+]?\d*\.?\d+).*?e[=:]?([-+]?\d*\.?\d+).*?u[=:]?([-+]?\d*\.?\d+)', data, re.IGNORECASE)
        if pos_match:
            n = float(pos_match.group(1))
            e = float(pos_match.group(2))
            u = float(pos_match.group(3))
            self.position_text = f'N={n:.1f} E={e:.1f} U={u:.1f}'

        # Parse range
        range_match = re.search(r'range.*?(\d*\.?\d+)', data, re.IGNORECASE)
        if range_match:
            range_val = float(range_match.group(1))
            self.range_text = f'Range: {range_val:.1f}m'

        # Parse bearing
        bearing_match = re.search(r'bearing.*?(\d*\.?\d+)', data, re.IGNORECASE)
        if bearing_match:
            bearing_val = float(bearing_match.group(1))
            self.bearing_text = f'Bearing: {bearing_val:.0f}deg'

        # Update labels
        self.gps_status_label.text = f'GPS: {self.gps_fix}'
        self.sat_label.text = f'Satellites: {self.satellites}'
        self.pos_label.text = self.position_text
        self.range_label.text = self.range_text
        self.bearing_label.text = self.bearing_text
