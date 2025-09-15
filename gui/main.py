"""
Flight Control GUI - Main Entry Point
Phase 1: Simple Serial Monitor

Simple serial passthrough monitor for FlightSequencer.
Displays serial traffic and allows sending commands.

Usage:
    python main.py --port COM4
    python main.py -p /dev/ttyUSB0

    Or set environment variable:
    set ARDUINO_PORT=COM4
    python main.py
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli.simple_console import main as console_main


def main():
    """Main application entry point."""
    print("Flight Control GUI - Phase 1: Simple Serial Monitor")
    print("Starting serial monitor...")
    print()

    console_main()


if __name__ == '__main__':
    main()