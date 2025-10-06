"""
Multi-Tab Arduino Control GUI Application Entry Point.
Unified interface for FlightSequencer, GpsAutopilot, and Device Testing.

Usage:
    python gui_main.py

Set ARDUINO_PORT environment variable or enter port in GUI.
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.multi_tab_gui import main as gui_main


def main():
    """Main application entry point."""
    print("Starting Flight Code Manager...")
    gui_main()


if __name__ == '__main__':
    main()