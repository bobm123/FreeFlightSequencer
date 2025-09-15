"""
FlightSequencer GUI Application Entry Point.
Simple parameter configuration GUI with serial monitoring.

Usage:
    python gui_main.py

Set ARDUINO_PORT environment variable or enter port in GUI.
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.simple_gui import main as gui_main


def main():
    """Main application entry point."""
    print("Starting FlightSequencer GUI...")
    gui_main()


if __name__ == '__main__':
    main()