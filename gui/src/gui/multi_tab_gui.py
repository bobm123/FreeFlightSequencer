"""
Multi-Tab GUI - Main interface for Flight Code Manager.
Unified interface supporting FlightSequencer, GpsAutopilot, and Device Testing.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import threading
import time

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from communication.simple_serial import SimpleSerialMonitor
from core.tab_manager import TabManager, ApplicationType
from widgets import ConnectionPanel
from tabs import FlightSequencerTab, GpsAutopilotTab, DeviceTestTab


class FlightCodeManager:
    """Main multi-tab GUI application for flight code management."""
    
    def __init__(self):
        # Core components
        self.serial_monitor = SimpleSerialMonitor()
        self.tab_manager = TabManager(self.serial_monitor)
        self.connected = False
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Flight Code Manager v2.0")
        self.root.geometry("1200x800")
        self.root.minsize(400, 300)  # Allow smaller minimum size for mobile

        # Configure DPI scaling for better display on high-DPI screens
        self._configure_dpi_scaling()

        # Set window icon (will be set after GUI creation for better compatibility)
        self.icon_path = None
        try:
            # Get path to bird.ico - find gui directory from current file location
            current_file = os.path.abspath(__file__)
            # From gui/src/gui/multi_tab_gui.py go up to gui/ directory
            gui_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            icon_path = os.path.join(gui_dir, "bird.ico")

            if os.path.exists(icon_path):
                self.icon_path = icon_path
            else:
                # Try alternative path (run from different directories)
                alt_icon_path = os.path.join(os.path.dirname(current_file), "..", "..", "..", "bird.ico")
                alt_icon_path = os.path.abspath(alt_icon_path)
                if os.path.exists(alt_icon_path):
                    self.icon_path = alt_icon_path

        except Exception as e:
            pass  # Continue without icon
        
        # Application state
        self.current_app = ApplicationType.UNKNOWN
        self.tabs = {}

        # Responsive layout state
        self.is_mobile_layout = False
        self.mobile_threshold_ratio = 1.2  # height/width ratio threshold for mobile layout

        # Create GUI
        self._create_widgets()
        self._setup_callbacks()

        # Set window icon after GUI is fully created
        self._set_window_icon()

        # Start periodic updates
        self._start_periodic_updates()

        # Check initial layout after a brief delay to let window settle
        self.root.after(100, self._check_initial_layout)

    def _configure_dpi_scaling(self):
        """Configure DPI scaling for better display on high-DPI screens."""
        try:
            # Get DPI from system
            dpi = self.root.winfo_fpixels('1i')

            # Calculate scaling factor (96 DPI is standard)
            scale_factor = dpi / 96.0

            # Only apply scaling if significantly different from 1.0
            if scale_factor > 1.2 or scale_factor < 0.8:
                # Apply Tk scaling
                self.root.tk.call('tk', 'scaling', scale_factor)
                print(f"[GUI] Applied DPI scaling: {scale_factor:.2f}x (DPI: {dpi:.0f})")
            else:
                print(f"[GUI] Standard DPI detected: {dpi:.0f}, no scaling applied")

        except Exception as e:
            print(f"[GUI] DPI scaling configuration failed: {e}")
            # Continue without DPI scaling if detection fails

    def _create_widgets(self):
        """Create main GUI widgets."""
        # Initialize status variables BEFORE creating tabs (tabs may reference them)
        self._initialize_status_variables()

        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Header frame with connection controls
        self._create_header(main_frame)

        # Main content area with tabs
        self._create_tab_interface(main_frame)
        
    def _create_header(self, parent):
        """Create header with connection controls and status."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 5))

        # Application detection indicator (left side)
        detect_frame = ttk.Frame(header_frame)
        detect_frame.pack(side='left')

        ttk.Label(detect_frame, text="Detected App:").pack(side='left')
        self.detected_app_var = tk.StringVar(value="None")
        self.detected_app_label = ttk.Label(detect_frame, textvariable=self.detected_app_var,
                                          font=('TkDefaultFont', 9, 'bold'))
        self.detected_app_label.pack(side='left', padx=(5, 0))

        # Connection panel (right side)
        conn_frame = ttk.Frame(header_frame)
        conn_frame.pack(side='right')

        self.connection_panel = ConnectionPanel(conn_frame, self.serial_monitor,
                                               self._on_connection_changed)
        self.connection_panel.pack()
        
    def _create_tab_interface(self, parent):
        """Create main tabbed interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True, pady=5)
        
        # Create individual tabs
        self._create_flight_sequencer_tab()
        self._create_gps_autopilot_tab() 
        self._create_device_test_tab()
        
        # Bind tab selection event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
    def _create_flight_sequencer_tab(self):
        """Create FlightSequencer tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="FlightSequencer")
        
        self.flight_sequencer_tab = FlightSequencerTab(tab_frame, self.serial_monitor, self.tab_manager, self)
        self.flight_sequencer_tab.get_frame().pack(fill='both', expand=True)
        
        self.tabs[ApplicationType.FLIGHT_SEQUENCER] = {
            'tab': self.flight_sequencer_tab,
            'index': 0
        }
        
    def _create_gps_autopilot_tab(self):
        """Create GpsAutopilot tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="GpsAutopilot")
        
        self.gps_autopilot_tab = GpsAutopilotTab(tab_frame, self.serial_monitor, self.tab_manager)
        self.gps_autopilot_tab.get_frame().pack(fill='both', expand=True)
        
        self.tabs[ApplicationType.GPS_AUTOPILOT] = {
            'tab': self.gps_autopilot_tab,
            'index': 1
        }
        
    def _create_device_test_tab(self):
        """Create DeviceTest tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Device Testing")
        
        self.device_test_tab = DeviceTestTab(tab_frame, self.serial_monitor, self.tab_manager)
        self.device_test_tab.get_frame().pack(fill='both', expand=True)
        
        self.tabs[ApplicationType.DEVICE_TEST] = {
            'tab': self.device_test_tab,
            'index': 2
        }
        
    def _initialize_status_variables(self):
        """Initialize status variables (no UI, just variables for tabs to reference)."""
        # Initialize variables that tabs may reference
        self.connection_status_var = tk.StringVar(value="Disconnected")
        self.message_count_var = tk.StringVar(value="Messages: 0")
        self.flight_phase_var = tk.StringVar(value="")
        self.flight_timer_var = tk.StringVar(value="")
        self.time_var = tk.StringVar()
        self.current_tab_var = tk.StringVar(value="")
        
    def _setup_callbacks(self):
        """Setup event callbacks.""" 
        # Tab manager callbacks
        self.tab_manager.set_detection_callback(self._on_application_detected)
        
        # Serial monitor callback
        self.serial_monitor.set_receive_callback(self._on_serial_data_received)
        
        # Window close callback
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Window resize callback for responsive layout
        self.root.bind('<Configure>', self._on_window_resize)

        # Message counter
        self.message_count = 0
        
    def _start_periodic_updates(self):
        """Start periodic update tasks."""
        self._check_connection_health()

    def _set_window_icon(self):
        """Set the window icon for Windows compatibility."""
        if not self.icon_path or not os.path.exists(self.icon_path):
            return

        try:
            # Primary method - should work on Windows
            self.root.iconbitmap(self.icon_path)
        except Exception:
            try:
                # Fallback method for Windows
                self.root.wm_iconbitmap(self.icon_path)
            except Exception:
                # If all else fails, continue without icon
                pass
        
    # Time display removed from status bar - method kept for backwards compatibility
    # def _update_time_display(self):
    #     """Update time display in status bar."""
    #     current_time = time.strftime("%H:%M:%S")
    #     self.time_var.set(current_time)
    #     self.root.after(1000, self._update_time_display)
        
    def _check_connection_health(self):
        """Periodically check connection health."""
        if self.connected:
            # Check if serial connection is still alive
            if not self.serial_monitor.is_connected:
                self._on_connection_changed(False, None)
                messagebox.showwarning("Connection Lost", 
                                     "Serial connection lost. Please reconnect.")
                                     
        self.root.after(5000, self._check_connection_health)  # Check every 5 seconds
        
    def _on_connection_changed(self, connected, port):
        """Handle connection state changes."""
        self.connected = connected

        if connected:
            self.connection_status_var.set(f"Connected to {port}")
            self.detected_app_var.set("Detecting...")

            # Reset tab manager detection state to allow fresh detection
            self.tab_manager.reset_detection()

            # Send identification query after connection
            self.root.after(2000, self.tab_manager.send_identification_query)
        else:
            self.connection_status_var.set("Disconnected")
            self.detected_app_var.set("None")
            self.current_app = ApplicationType.UNKNOWN
            self.message_count = 0
            self.message_count_var.set("Messages: 0")

            # Reset tab manager detection state
            self.tab_manager.reset_detection()

        # Notify all tabs about connection change
        for app_type, tab_info in self.tabs.items():
            tab = tab_info['tab']
            if hasattr(tab, 'handle_connection_change'):
                tab.handle_connection_change(connected)
            
    def _on_application_detected(self, app_type):
        """Handle application detection."""
        self.current_app = app_type
        self.detected_app_var.set(app_type.value)
        
        # Highlight appropriate tab
        if app_type in self.tabs:
            tab_index = self.tabs[app_type]['index']
            self.notebook.select(tab_index)
            
            # Update tab appearance to indicate detection
            self._highlight_detected_tab(tab_index)
            
    def _highlight_detected_tab(self, tab_index):
        """Highlight the detected application tab."""
        # Reset all tab styles
        for i in range(self.notebook.index('end')):
            self.notebook.tab(i, state='normal')
            
        # Highlight detected tab (if available in ttk theme)
        try:
            # This may not work on all themes
            self.notebook.tab(tab_index, state='active')
        except:
            pass  # Fallback to normal highlighting
            
    def _on_tab_changed(self, event):
        """Handle tab selection changes."""
        selected_tab = self.notebook.index('current')
        tab_names = ["FlightSequencer", "GpsAutopilot", "Device Testing"]

        if 0 <= selected_tab < len(tab_names):
            self.current_tab_var.set(f"Current: {tab_names[selected_tab]}")

            # Show/hide flight status based on selected tab
            if tab_names[selected_tab] == "FlightSequencer":
                # Update flight status if FlightSequencer tab has data
                if hasattr(self, 'flight_sequencer_tab') and self.flight_sequencer_tab:
                    params = self.flight_sequencer_tab.current_flight_params
                    timer = self.flight_sequencer_tab.current_timer
                    self.update_flight_status(params['current_phase'], timer)
            else:
                # Clear flight status for other tabs
                self.clear_flight_status()

        # If we have a known app type but user switched to different tab,
        # allow manual override
        if self.current_app != ApplicationType.UNKNOWN:
            for app_type, tab_info in self.tabs.items():
                if tab_info['index'] == selected_tab and app_type != self.current_app:
                    # User manually selected different tab
                    if messagebox.askyesno("Override Detection",
                                         f"Detected {self.current_app.value} but selected {app_type.value} tab.\\n"
                                         f"Override automatic detection?"):
                        self.tab_manager.force_application_type(app_type)
                        self.detected_app_var.set(f"{app_type.value} (Manual)")
                    break
                    
    def _on_serial_data_received(self, data):
        """Handle incoming serial data."""
        # Update message counter
        self.message_count += 1
        self.message_count_var.set(f"Messages: {self.message_count}")

        # Route data through tab manager
        self.tab_manager.route_message(data)

    def update_flight_status(self, phase=None, timer=None):
        """Update flight status in the status bar."""
        if phase is not None:
            self.flight_phase_var.set(f"Phase: {phase}")
        if timer is not None:
            self.flight_timer_var.set(f"Time: {timer}")

    def clear_flight_status(self):
        """Clear flight status from the status bar."""
        self.flight_phase_var.set("")
        self.flight_timer_var.set("")

    def _on_window_resize(self, event):
        """Handle window resize events for responsive layout."""
        # Only respond to main window resize events
        if event.widget != self.root:
            return

        # Get current window dimensions
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # Skip if dimensions are not valid (during initialization)
        if width <= 1 or height <= 1:
            return

        # Calculate aspect ratio (height/width)
        aspect_ratio = height / width

        # Determine if we should use mobile layout
        should_be_mobile = aspect_ratio > self.mobile_threshold_ratio

        # Only update layout if state changed
        if should_be_mobile != self.is_mobile_layout:
            self.is_mobile_layout = should_be_mobile
            self._update_responsive_layout()

        # Always check width-based layouts (for button stacking)
        # Use a small delay to let the window settle
        self.root.after(100, self._check_width_layouts)

    def _check_initial_layout(self):
        """Check initial layout and trigger responsive update if needed."""
        # Force a layout check
        event = type('MockEvent', (), {'widget': self.root})()
        self._on_window_resize(event)

    def _update_responsive_layout(self):
        """Update layout based on mobile/desktop state."""
        # Notify all tabs about layout change
        for app_type, tab_info in self.tabs.items():
            tab = tab_info['tab']
            if hasattr(tab, 'update_responsive_layout'):
                tab.update_responsive_layout(self.is_mobile_layout)

    def _check_width_layouts(self):
        """Check width-based layouts for all tabs."""
        # Notify all tabs to check their width-based layouts
        for app_type, tab_info in self.tabs.items():
            tab = tab_info['tab']
            if hasattr(tab, '_check_width_layout'):
                tab._check_width_layout()

    def _on_window_close(self):
        """Handle window close event."""
        try:
            if self.connected:
                self.serial_monitor.disconnect()
        except:
            pass
            
        self.root.destroy()
        
    def run(self):
        """Start the GUI application."""
        try:
            # Set window icon if available
            try:
                # Try to load icon (you would need to add an icon file)
                # self.root.iconbitmap('arduino_icon.ico')
                pass
            except:
                pass
                
            # Start main loop
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            if self.connected:
                try:
                    self.serial_monitor.disconnect()
                except:
                    pass


def main():
    """Main entry point for multi-tab GUI."""
    try:
        app = FlightCodeManager()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Application Error", f"Failed to start application:\\n{e}")


if __name__ == '__main__':
    main()