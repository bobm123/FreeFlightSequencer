"""
Test script for responsive layout improvements.
Tests both Tkinter and Kivy GUIs without requiring Arduino connection.
"""
import sys
import os

def test_tkinter_gui():
    """Test Tkinter GUI responsive layout."""
    print("=" * 60)
    print("Testing Tkinter GUI Responsive Layout")
    print("=" * 60)

    try:
        # Add gui directory to path
        gui_dir = os.path.dirname(os.path.abspath(__file__))
        if gui_dir not in sys.path:
            sys.path.insert(0, gui_dir)

        from src.gui.multi_tab_gui import FlightCodeManager

        print("[OK] Tkinter GUI imports successful")
        print("\nStarting Tkinter GUI...")
        print("Try resizing the window to test responsive behavior:")
        print("  - Narrow window: buttons stack vertically")
        print("  - Tall window: panels stack vertically (mobile mode)")
        print("  - Wide window: panels side-by-side (desktop mode)")
        print("  - Serial monitor < 320px wide: auto-stacks (< 40 chars)")
        print("\nWatch console for layout transition messages!")
        print("Close the window to continue...")

        app = FlightCodeManager()
        app.run()

        print("[OK] Tkinter GUI test completed")
        return True

    except Exception as e:
        print(f"[FAIL] Tkinter GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kivy_gui():
    """Test Kivy mobile GUI."""
    print("\n" + "=" * 60)
    print("Testing Kivy Mobile GUI")
    print("=" * 60)

    try:
        # Check if Kivy is installed
        try:
            import kivy
            print(f"[OK] Kivy version: {kivy.__version__}")
        except ImportError:
            print("[SKIP] Kivy not installed")
            print("To install: pip install kivy")
            return None

        # Add mobile_gui directory to path
        mobile_gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mobile_gui')
        if mobile_gui_dir not in sys.path:
            sys.path.insert(0, mobile_gui_dir)

        from main import FlightCodeManagerApp

        print("[OK] Kivy GUI imports successful")
        print("\nStarting Kivy Mobile GUI...")
        print("Window simulates 10-inch tablet (800x1280)")
        print("Try rotating/resizing to test touch-optimized layout")
        print("\nClose the window to finish...")

        app = FlightCodeManagerApp()
        app.run()

        print("[OK] Kivy GUI test completed")
        return True

    except Exception as e:
        print(f"[FAIL] Kivy GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all GUI tests."""
    print("FreeFlightSequencer GUI Responsive Layout Test")
    print("=" * 60)

    results = {}

    # Test Tkinter GUI
    results['tkinter'] = test_tkinter_gui()

    # Ask if user wants to test Kivy
    print("\n" + "=" * 60)
    response = input("Test Kivy mobile GUI? (y/n): ").strip().lower()

    if response == 'y':
        results['kivy'] = test_kivy_gui()
    else:
        print("[SKIP] Kivy GUI test skipped by user")
        results['kivy'] = None

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for gui_type, result in results.items():
        if result is True:
            status = "[PASS]"
        elif result is False:
            status = "[FAIL]"
        else:
            status = "[SKIP]"
        print(f"{status} {gui_type.upper()} GUI")

    print("\nLayout improvements applied:")
    print("  [X] Tkinter: Grid-based layout without widget destruction")
    print("  [X] Tkinter: DPI scaling support")
    print("  [X] Kivy: Touch-native responsive design")
    print("  [X] Kivy: Cross-platform mobile support")


if __name__ == '__main__':
    main()
