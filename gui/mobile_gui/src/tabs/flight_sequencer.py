"""
FlightSequencer Tab for Kivy Mobile GUI
Touch-optimized parameter controls and monitoring
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty
from kivy.metrics import dp
import re


class ParameterRow(BoxLayout):
    """Single parameter input row with label, entry, and set button."""

    label_text = StringProperty('')
    value_text = StringProperty('')

    def __init__(self, label, width_hint=0.5, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = dp(5)
        self.spacing = dp(10)

        self.callback = callback

        # Label
        lbl = Label(
            text=label,
            size_hint_x=width_hint,
            halign='left',
            valign='middle'
        )
        lbl.bind(size=lbl.setter('text_size'))  # Enable text wrapping
        self.add_widget(lbl)

        # Text input
        self.text_input = TextInput(
            text='',
            size_hint_x=0.3,
            multiline=False,
            input_filter='float',
            font_size=dp(16)
        )
        self.add_widget(self.text_input)

        # Set button
        btn = Button(
            text='Set',
            size_hint_x=0.2,
            on_press=self._on_set_pressed
        )
        self.add_widget(btn)

    def _on_set_pressed(self, instance):
        """Handle Set button press."""
        if self.callback:
            self.callback(self.text_input.text)

    def set_value(self, value):
        """Update the displayed value."""
        self.text_input.text = str(value)


class FlightSequencerTab(BoxLayout):
    """Main FlightSequencer control tab."""

    # Flight parameters (for data binding)
    motor_time = NumericProperty(0)
    flight_time = NumericProperty(0)
    motor_speed = NumericProperty(0)
    current_phase = StringProperty('UNKNOWN')

    def __init__(self, serial_monitor, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)

        self.serial_monitor = serial_monitor
        serial_monitor.add_receive_callback(self.handle_serial_data)

        # Parameter store (single source of truth)
        self.flight_params = {
            'motor_run_time': None,
            'total_flight_time': None,
            'motor_speed': None,
            'dt_retracted': None,
            'dt_deployed': None,
            'dt_dwell': None,
            'current_phase': 'UNKNOWN'
        }

        self._create_widgets()

    def _create_widgets(self):
        """Create the tab UI."""
        # Connection status bar
        self.status_label = Label(
            text='Status: Disconnected',
            size_hint_y=None,
            height=dp(40),
            color=(1, 0.5, 0, 1)  # Orange
        )
        self.add_widget(self.status_label)

        # Scrollable parameter area
        scroll_view = ScrollView(size_hint=(1, 0.6))
        param_container = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None,
            padding=dp(10)
        )
        param_container.bind(minimum_height=param_container.setter('height'))

        # Parameter rows
        self.motor_time_row = ParameterRow(
            'Motor Run Time (sec):',
            callback=self._set_motor_time
        )
        param_container.add_widget(self.motor_time_row)

        self.flight_time_row = ParameterRow(
            'Total Flight Time (sec):',
            callback=self._set_flight_time
        )
        param_container.add_widget(self.flight_time_row)

        self.motor_speed_row = ParameterRow(
            'Motor Speed (95-200):',
            callback=self._set_motor_speed
        )
        param_container.add_widget(self.motor_speed_row)

        self.dt_retracted_row = ParameterRow(
            'DT Retracted (us):',
            callback=self._set_dt_retracted
        )
        param_container.add_widget(self.dt_retracted_row)

        self.dt_deployed_row = ParameterRow(
            'DT Deployed (us):',
            callback=self._set_dt_deployed
        )
        param_container.add_widget(self.dt_deployed_row)

        self.dt_dwell_row = ParameterRow(
            'DT Dwell Time (sec):',
            callback=self._set_dt_dwell
        )
        param_container.add_widget(self.dt_dwell_row)

        scroll_view.add_widget(param_container)
        self.add_widget(scroll_view)

        # Action buttons
        button_grid = GridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(120),
            padding=dp(5)
        )

        get_btn = Button(text='Get Parameters', on_press=lambda x: self._get_parameters())
        button_grid.add_widget(get_btn)

        reset_btn = Button(text='Reset Defaults', on_press=lambda x: self._reset_parameters())
        button_grid.add_widget(reset_btn)

        download_btn = Button(text='Download Data', on_press=lambda x: self._download_data())
        button_grid.add_widget(download_btn)

        emergency_btn = Button(
            text='EMERGENCY STOP',
            background_color=(0.7, 0, 0, 1),  # Red
            on_press=lambda x: self._emergency_stop()
        )
        button_grid.add_widget(emergency_btn)

        self.add_widget(button_grid)

        # Flight status display
        self.phase_label = Label(
            text='Phase: UNKNOWN',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            bold=True
        )
        self.add_widget(self.phase_label)

    def _send_command(self, command):
        """Send command to Arduino."""
        if self.serial_monitor.is_connected:
            self.serial_monitor.send_line(command)
            print(f"[FlightSequencer] Sent: {command}")
        else:
            self.status_label.text = 'Status: Not Connected'

    def _set_motor_time(self, value):
        """Set motor run time."""
        try:
            time_int = int(float(value))
            if 1 <= time_int <= 300:
                self._send_command(f"M {time_int}")
            else:
                self.status_label.text = 'Error: Motor time must be 1-300 sec'
        except ValueError:
            self.status_label.text = 'Error: Invalid motor time value'

    def _set_flight_time(self, value):
        """Set total flight time."""
        try:
            time_int = int(float(value))
            if 10 <= time_int <= 600:
                self._send_command(f"T {time_int}")
            else:
                self.status_label.text = 'Error: Flight time must be 10-600 sec'
        except ValueError:
            self.status_label.text = 'Error: Invalid flight time value'

    def _set_motor_speed(self, value):
        """Set motor speed."""
        try:
            speed_int = int(float(value))
            if 95 <= speed_int <= 200:
                self._send_command(f"S {speed_int}")
            else:
                self.status_label.text = 'Error: Motor speed must be 95-200'
        except ValueError:
            self.status_label.text = 'Error: Invalid motor speed value'

    def _set_dt_retracted(self, value):
        """Set DT retracted position."""
        try:
            pos_int = int(float(value))
            if 950 <= pos_int <= 2050:
                self._send_command(f"DR {pos_int}")
            else:
                self.status_label.text = 'Error: DT retracted must be 950-2050 us'
        except ValueError:
            self.status_label.text = 'Error: Invalid DT retracted value'

    def _set_dt_deployed(self, value):
        """Set DT deployed position."""
        try:
            pos_int = int(float(value))
            if 950 <= pos_int <= 2050:
                self._send_command(f"DD {pos_int}")
            else:
                self.status_label.text = 'Error: DT deployed must be 950-2050 us'
        except ValueError:
            self.status_label.text = 'Error: Invalid DT deployed value'

    def _set_dt_dwell(self, value):
        """Set DT dwell time."""
        try:
            time_int = int(float(value))
            if 1 <= time_int <= 60:
                self._send_command(f"DW {time_int}")
            else:
                self.status_label.text = 'Error: DT dwell must be 1-60 sec'
        except ValueError:
            self.status_label.text = 'Error: Invalid DT dwell value'

    def _get_parameters(self):
        """Get current parameters."""
        self._send_command("G")

    def _reset_parameters(self):
        """Reset parameters to defaults."""
        self._send_command("R")

    def _download_data(self):
        """Download flight data."""
        self._send_command("D J")
        self.status_label.text = 'Status: Downloading flight data...'

    def _emergency_stop(self):
        """Send emergency stop."""
        self._send_command("STOP")
        self.status_label.text = 'Status: EMERGENCY STOP SENT'

    def handle_serial_data(self, data):
        """Handle incoming serial data."""
        # Parse parameter updates
        self._parse_parameters(data)

        # Update GUI with current parameters
        self._sync_gui()

    def _parse_parameters(self, data):
        """Parse parameters from Arduino response."""
        # Motor run time
        motor_match = re.search(r'Motor Run Time[:\s=]+(\d+)', data, re.IGNORECASE)
        if motor_match:
            self.flight_params['motor_run_time'] = int(motor_match.group(1))

        # Flight time
        flight_match = re.search(r'Total Flight Time[:\s=]+(\d+)', data, re.IGNORECASE)
        if flight_match:
            self.flight_params['total_flight_time'] = int(flight_match.group(1))

        # Motor speed
        speed_match = re.search(r'Motor Speed[:\s=]+(\d+)', data, re.IGNORECASE)
        if speed_match:
            self.flight_params['motor_speed'] = int(speed_match.group(1))

        # DT parameters
        dt_ret_match = re.search(r'DT Retracted[:\s=]+(\d+)', data, re.IGNORECASE)
        if dt_ret_match:
            self.flight_params['dt_retracted'] = int(dt_ret_match.group(1))

        dt_dep_match = re.search(r'DT Deployed[:\s=]+(\d+)', data, re.IGNORECASE)
        if dt_dep_match:
            self.flight_params['dt_deployed'] = int(dt_dep_match.group(1))

        dt_dwell_match = re.search(r'DT Dwell[:\s=]+(\d+)', data, re.IGNORECASE)
        if dt_dwell_match:
            self.flight_params['dt_dwell'] = int(dt_dwell_match.group(1))

        # Phase detection
        if re.search(r'READY', data, re.IGNORECASE):
            self.flight_params['current_phase'] = 'READY'
        elif re.search(r'ARMED', data, re.IGNORECASE):
            self.flight_params['current_phase'] = 'ARMED'
        elif re.search(r'MOTOR', data, re.IGNORECASE):
            self.flight_params['current_phase'] = 'MOTOR_RUN'
        elif re.search(r'GLIDE', data, re.IGNORECASE):
            self.flight_params['current_phase'] = 'GLIDE'
        elif re.search(r'DT_DEPLOY', data, re.IGNORECASE):
            self.flight_params['current_phase'] = 'DT_DEPLOY'

    def _sync_gui(self):
        """Update GUI fields with current parameters."""
        params = self.flight_params

        if params['motor_run_time'] is not None:
            self.motor_time_row.set_value(params['motor_run_time'])

        if params['total_flight_time'] is not None:
            self.flight_time_row.set_value(params['total_flight_time'])

        if params['motor_speed'] is not None:
            self.motor_speed_row.set_value(params['motor_speed'])

        if params['dt_retracted'] is not None:
            self.dt_retracted_row.set_value(params['dt_retracted'])

        if params['dt_deployed'] is not None:
            self.dt_deployed_row.set_value(params['dt_deployed'])

        if params['dt_dwell'] is not None:
            self.dt_dwell_row.set_value(params['dt_dwell'])

        # Update phase display
        self.phase_label.text = f"Phase: {params['current_phase']}"

        # Update connection status
        if self.serial_monitor.is_connected:
            self.status_label.text = 'Status: Connected'
