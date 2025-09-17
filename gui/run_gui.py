#!/usr/bin/env python3
"""
Arduino Control Center - Startup Script
Simplified launcher that handles path setup automatically.
"""
import sys
import os

def main():
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Add src to path
    src_path = os.path.join(script_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    print("Starting Arduino Control Center v2.0...")
    print("Multi-Tab Interface: FlightSequencer | GpsAutopilot | Device Testing")
    print("=" * 60)
    
    try:
        # Test tkinter availability
        import tkinter
        print("✓ tkinter available")
        
        # Test pyserial availability  
        try:
            import serial
            print("✓ pyserial available")
        except ImportError:
            print("⚠ pyserial not found - serial communication will not work")
            print("Install with: pip install pyserial")
        
        print()
        
        from gui.multi_tab_gui import ArduinoControlCenter
        app = ArduinoControlCenter()
        app.run()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("\nPlease ensure all required dependencies are installed:")
        print("- tkinter (usually included with Python)")
        print("- pyserial (pip install pyserial)")
        sys.exit(1)
    except Exception as e:
        print(f"Application Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()