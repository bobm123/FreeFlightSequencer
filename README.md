# MyArduinoProject - Flight Control Systems

## Project Overview

Advanced flight control systems for free-flight model aircraft using Arduino-compatible hardware. This project provides two complete flight control applications with a unified GUI interface for parameter management and data analysis.

## Current Applications

### 1. GPS Autopilot System **READY FOR FLIGHT TESTING**
GPS-guided autonomous flight controller maintaining aircraft within circular flight patterns around launch point.

**Key Features:**
- **Autonomous Navigation**: GPS-only positioning with 100m orbit radius control
- **6-State Flight Machine**: READY -> ARMED -> MOTOR_SPOOL -> GPS_GUIDED_FLIGHT -> EMERGENCY -> LANDING
- **Dual LED Status**: Red flight state + Blue GPS data reception overlay
- **Safety Systems**: GPS failsafe, timeout protection, emergency override
- **Real-time GUI**: Parameter control, status monitoring, position display

### 2. FlightSequencer System **PRODUCTION READY**
Enhanced E36-Timer replacement providing automated flight sequencing for electric free-flight models.

**Key Features:**
- **Automated Sequencing**: Motor run -> Glide phase -> Dethermalizer deployment
- **GPS Data Logging**: Records complete flight path when GPS module available
- **Robust Data Export**: CSV parsing with line-break recovery, JSON/CSV/KML export
- **Flight Visualization**: Real-time flight path plotting with state timeline analysis
- **Parameter Programming**: Serial interface for motor time, flight time, servo positions

## Unified GUI System **FULLY IMPLEMENTED**

Multi-tab interface providing comprehensive control and monitoring for both flight systems:

### Core Features
- **Cross-platform**: Windows, macOS, Linux support
- **Real-time Communication**: Robust serial protocol with auto-reconnection
- **Parameter Management**: Live parameter adjustment with validation
- **Data Visualization**: Flight path plotting with matplotlib integration
- **Export Capabilities**: JSON, CSV, KML formats for analysis

### Robust Data Handling
- **Error Recovery**: Handles transmission line breaks and corrupted GPS coordinates
- **Debug Preservation**: Automatically saves problematic data for analysis
- **Format Validation**: Detects and corrects incomplete coordinate values
- **Multi-format Export**: Supports JSON, CSV, and KML for external analysis

## Project Structure

```
MyArduinoProject/
├── applications/           # Arduino flight control applications
│   ├── GpsAutopilot/      # GPS-guided autonomous flight control
│   ├── FlightSequencer/   # Automated flight sequencing (E36-Timer++)
│   └── DeviceTests/       # Hardware validation and testing utilities
├── gui/                   # Python-based control interface
│   ├── src/              # GUI source code with multi-tab interface
│   ├── FlightControlGUI_Specification.md
│   └── README.md
├── hardware/             # Hardware specifications and carrier boards
├── docs/                 # Project documentation
├── CLAUDE.md            # AI coding assistant context and guidelines
├── GPS_AUTOPILOT_STATUS.md  # Detailed GPS autopilot status
└── README.md           # This file
```

## Quick Start

### Hardware Setup
- **Controller**: Adafruit QtPY SAMD21 + Signal Distribution MkII
- **Servos**: Roll control (A3), Motor ESC (A2)
- **Interface**: Button (A0), NeoPixel LED (pin 11)
- **GPS Module**: Serial1 hardware UART (optional for FlightSequencer, required for GPS Autopilot)

### Software Installation
1. **Arduino IDE**: Install with Adafruit SAMD board package
2. **Python GUI**: Requires Python 3.8+ with matplotlib, pyserial, tkinter
3. **Build System**: Each application includes Makefile for command-line compilation

### Getting Started
1. **Choose Application**: Upload either GpsAutopilot.ino or FlightSequencer.ino
2. **Launch GUI**: Run `python gui/run_gui.py` and select appropriate tab
3. **Connect Hardware**: GUI auto-detects Arduino on serial ports
4. **Configure Parameters**: Set flight parameters through GUI interface
5. **Test Flight**: Follow application-specific testing procedures

## Testing Status

### GPS Autopilot System
- **Implementation**: Complete and ready for flight testing
- **Ground Testing**: GPS acquisition, parameter control, GUI integration [OK]
- **Flight Testing**: Awaiting field validation of autonomous flight patterns

### FlightSequencer System
- **Implementation**: Complete with robust data handling [OK]
- **Field Testing**: Validated through multiple flight sessions
- **Data Analysis**: CSV parsing robustness verified with actual flight data
- **Issue Resolution**: Fixed GPS coordinate line-break parsing errors

### GUI System
- **Multi-tab Interface**: Fully functional with both applications [OK]
- **Data Export**: JSON/CSV/KML export validated [OK]
- **Error Handling**: Robust parsing with automatic error recovery [OK]
- **Visualization**: Flight path plotting and analysis tools [OK]

## Safety Features

### Both Applications
- **Emergency Override**: Button press during flight provides immediate motor cutoff
- **Parameter Validation**: Range checking prevents unsafe configurations
- **Connection Monitoring**: GUI detects and handles communication failures
- **Debug Logging**: Comprehensive error tracking and data preservation

### GPS Autopilot Specific
- **GPS Failsafe**: Configurable gentle turn when GPS signal lost
- **Safety Radius**: Automatic emergency if aircraft exceeds safe distance
- **Timeout Protection**: 10-second GPS timeout before emergency mode

### FlightSequencer Specific
- **State Machine Safety**: Emergency cutoff from any flight phase
- **DT Deployment Logic**: Dethermalizer only deploys at proper flight phase
- **Data Recovery**: Robust CSV parsing handles transmission errors

## Recent Improvements

### FlightSequencer Data Handling (Latest)
- **Fixed CSV parsing issue**: "could not convert string to float: '-'" error resolved
- **Line break recovery**: GPS coordinates split across transmission boundaries now handled
- **Coordinate validation**: Detects and corrects incomplete latitude/longitude values
- **Debug data preservation**: Problematic data automatically saved with timestamps

### GUI Enhancements
- **Multi-application support**: Single interface manages both flight systems
- **Real-time parameter sync**: GUI fields automatically update from Arduino responses
- **Export format options**: JSON, CSV, and KML formats for different analysis needs
- **Flight visualization**: Matplotlib-based plotting with state timeline analysis

## Technical Specifications

### Hardware Platform
- **Microcontroller**: Adafruit QtPY SAMD21 (32-bit ARM Cortex-M0+)
- **Carrier Board**: Signal Distribution MkII with servo/ESC connectors
- **GPS Module**: Standard NMEA-compatible GPS (9600 baud UART)
- **Power Requirements**: 5V BEC from motor ESC

### Communication Protocol
- **Serial Interface**: 9600 baud USB/UART
- **Command Format**: Text-based with validation and error handling
- **Data Download**: CSV format with JSON packaging and robust parsing
- **GUI Protocol**: Auto-discovery with connection status monitoring

### Software Stack
- **Arduino**: Standard Arduino framework with cross-platform compatibility
- **Python GUI**: Tkinter-based with matplotlib visualization
- **Data Formats**: JSON for configuration, CSV for flight data, KML for mapping
- **Build System**: Arduino IDE and command-line Makefile support

## Project Status Summary

| Component | Status | Testing | Notes |
|-----------|---------|---------|-------|
| GPS Autopilot | Complete | Ready for flight | All ground testing passed |
| FlightSequencer | Complete | Field validated | CSV parsing robustness verified |
| Multi-tab GUI | Complete | Fully functional | Handles both applications |
| Data Export | Complete | Robustness tested | JSON/CSV/KML formats |
| Flight Visualization | Complete | Matplotlib integration | Path plotting with states |
| Error Handling | Complete | Real-world tested | Handles transmission errors |

## Future Enhancements

### Near Term
- Field validation of GPS Autopilot autonomous flight
- Additional flight data analysis tools
- Enhanced visualization options

### Long Term
- Multi-aircraft management
- Advanced autopilot algorithms (thermal seeking, waypoint navigation)
- Mobile app interface for field operation

## Contributing

This project follows established coding guidelines in `CLAUDE.md`. Key principles:
- No Unicode characters in Arduino code (compatibility with embedded displays)
- Consistent error handling and parameter validation
- Comprehensive documentation and testing
- Cross-platform compatibility

## License

Open source project for model aviation community. See individual application directories for specific licensing information.

---

**Project Status**: Both flight control systems are complete and ready for operation. GUI interface provides comprehensive control and data analysis capabilities. Latest improvements include robust CSV parsing for reliable flight data recovery.

**Last Updated**: December 2024 - FlightSequencer CSV parsing robustness improvements