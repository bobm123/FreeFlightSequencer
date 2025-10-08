"""
Kivy Mobile GUI for FreeFlightSequencer
Main entry point for mobile application
"""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.metrics import dp
from kivy.core.window import Window

# Set reasonable window size for development (simulating tablet)
Window.size = (800, 1280)

from src.serial_comm import MobileSerialMonitor
from src.tabs.flight_sequencer import FlightSequencerTab
from src.tabs.gps_autopilot import GpsAutopilotTab


class ConnectionBar(BoxLayout):
    """Connection control bar widget."""

    # Properties for data binding
    port = StringProperty('COM4')
    connected = BooleanProperty(False)
    status_text = StringProperty('Disconnected')

    def __init__(self, serial_monitor, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = dp(10)
        self.spacing = dp(10)

        self.serial_monitor = serial_monitor


class FlightCodeManagerApp(App):
    """Main Kivy application for flight code management."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_monitor = MobileSerialMonitor()
        self.connected = False

    def build(self):
        """Build the main application UI."""
        # Main layout
        root_layout = BoxLayout(orientation='vertical')

        # Create tabbed panel
        tabs = TabbedPanel(do_default_tab=False)
        tabs.tab_width = dp(150)

        # FlightSequencer tab
        fs_tab = TabbedPanelItem(text='FlightSequencer')
        fs_content = FlightSequencerTab(self.serial_monitor)
        fs_tab.add_widget(fs_content)
        tabs.add_widget(fs_tab)

        # GpsAutopilot tab
        gps_tab = TabbedPanelItem(text='GPS Autopilot')
        gps_content = GpsAutopilotTab(self.serial_monitor)
        gps_tab.add_widget(gps_content)
        tabs.add_widget(gps_tab)

        # Add tabs to root layout
        root_layout.add_widget(tabs)

        return root_layout

    def on_pause(self):
        """Handle app pause (Android/iOS)."""
        return True

    def on_resume(self):
        """Handle app resume (Android/iOS)."""
        pass

    def on_stop(self):
        """Handle app shutdown."""
        if self.serial_monitor.is_connected:
            self.serial_monitor.disconnect()


if __name__ == '__main__':
    FlightCodeManagerApp().run()
