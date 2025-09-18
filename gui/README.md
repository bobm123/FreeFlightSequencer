# Arduino Control Center v2.0

Multi-tab GUI interface for Arduino flight control applications.

## Quick Start

### Method 1: Direct Launch
```bash
python run_gui.py
```

### Method 2: Traditional Launch  
```bash
python gui_main.py
```

## Features

### Multi-Application Support
- **FlightSequencer**: Flight parameter control with profiles and real-time monitoring
- **GpsAutopilot**: GPS navigation configuration and autonomous flight control
- **Device Testing**: Hardware validation and diagnostic tools

### Key Capabilities
- **Auto-Detection**: Automatically identifies connected Arduino application
- **Real-time Monitoring**: Live parameter updates and status displays
- **Flight Profiles**: Save/load parameter sets for different aircraft
- **Safety Features**: Emergency stops and parameter validation
- **Cross-Platform**: Windows, Mac, Linux support

## Requirements

- Python 3.7+
- tkinter (usually included)
- pyserial (`pip install pyserial`)

## Application Structure

```
gui/
|-- run_gui.py              # Simplified launcher
|-- gui_main.py            # Main entry point
|-- main.py                # Console interface (legacy)
`-- src/                   # Source code modules
    |-- gui/               # Main GUI application
    |-- tabs/              # Individual tab interfaces
    |-- widgets/           # Reusable GUI components
    |-- core/              # Tab management and monitoring
    `-- communication/     # Serial communication layer
```

## Usage

1. **Connect Arduino**: Use auto-detect or manually select COM port
2. **Application Detection**: GUI automatically identifies Arduino app type
3. **Configure Parameters**: Use appropriate tab interface for your application
4. **Monitor Status**: Real-time display of flight parameters and system status
5. **Flight Operations**: Execute flights with safety monitoring and data logging

## Troubleshooting

### Import Errors
- Ensure you're running from the `gui/` directory
- Check that `pyserial` is installed: `pip install pyserial`

### Connection Issues
- Verify Arduino is connected and drivers installed
- Try auto-detect or manually select correct COM port
- Check that Arduino application is running and responsive

### Application Detection
- Wait 2-3 seconds after connection for auto-detection
- Send `?` or `G` commands to trigger detection
- Use manual tab selection if auto-detection fails

## Support

- Check project documentation in `docs/`
- Review Arduino application specifications
- Verify hardware connections per project plan