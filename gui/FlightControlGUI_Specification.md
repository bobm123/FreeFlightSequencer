# Flight Control GUI Specification

## Overview

The Flight Control GUI is a Python-based interface application focused on **Core Communication** and **Portable Field Operation** for Arduino-based flight control systems. The primary goal is establishing reliable serial communication for parameter management, with portable laptop operation in the field taking priority over desktop data analysis features. This is NOT an integral part of the flight system - both FlightSequencer and future GPS Autopilot applications operate independently when disconnected from the GUI.

## Project Scope

### Target Applications
- **FlightSequencer**: Parameter programming and basic status monitoring
- **Device Testing**: Hardware validation and system diagnostics
- **GPS Autopilot** *(Future)*: Parameter management (specifications TBD)

### Primary Users
- **Field Operators**: Laptop-based parameter configuration during flight operations
- **Developers**: System debugging and hardware validation
- **Hobbyists**: Basic parameter setup and monitoring

## Architecture Overview

### Technology Stack - Phase 1 Core
- **Communication**: PySerial (USB/Serial) - **CRITICAL FOUNDATION**
- **Configuration**: JSON for settings persistence
- **GUI Framework**: Tkinter or PyQt5/6 for cross-platform desktop support

### Future Technologies
- **Data Processing**: Pandas for flight data analysis
- **Visualization**: Matplotlib for plotting
- **Web Interface**: Flask/FastAPI for remote access

### System Architecture
```
+-------------------+    USB/Serial     +------------------------+
|   Arduino         |<----------------->|  Python GUI App        |
|   (QtPY SAMD21)   |    9600 baud      |  (Portable Desktop)    |
+-------------------+                   +------------------------+
| FlightSequencer   |                   | Core Communication     |
| Device Tests      |                   | Parameter Config       |
| GPS Test          |                   | Portable Field Ops     |
+-------------------+                   | Basic Monitoring       |
                                        +------------------------+
```

## Functional Requirements

### Core Features - Phase 1

#### 1. Serial Communication Manager **[CRITICAL]**
- **Connection Management**: Auto-detect COM ports, connect/disconnect with status
- **Protocol Handling**: Implement existing FlightSequencer command protocol
- **Error Recovery**: Handle disconnections, timeouts, and communication failures
- **Command Validation**: Ensure proper command formatting before sending

#### 2. Flight Parameter Configuration **[ESSENTIAL]**
- **FlightSequencer Parameters**:
  - Motor run time (5-60 seconds)
  - Total flight time (30-600 seconds) 
  - Motor speed (95-200, 950-2000us PWM)
- **Parameter Validation**: Range checking and logical relationship validation
- **Default Management**: Reset to factory defaults with confirmation
- **Configuration Persistence**: Save/load parameter sets locally

#### 3. Portable Field Operation **[HIGH PRIORITY]**
- **Field-Friendly Interface**: Large buttons, clear text for outdoor laptop use
- **Quick Parameter Adjustment**: Slider controls and preset buttons
- **Connection Status**: Clear visual indicators for serial connection
- **Laptop Optimization**: Efficient operation for portable field computers

### Secondary Features - Future Phases

#### 4. Basic Monitoring *(Future)*
- **Flight Status Display**: Current flight state and elapsed time
- **Parameter Readback**: Verify settings on Arduino
- **System Health**: Basic connection and communication status

#### 5. Data Logging *(Future)*
- **Parameter Logging**: Record parameter changes with timestamps
- **Session Management**: Basic flight session tracking

#### 6. GPS Integration *(Future - Lower Priority)*
- **Position Display**: Real-time coordinates (when GPS hardware exists)
- **Autopilot Parameters**: Future integration with GPS autopilot systems

### User Interface Design

#### Field-Optimized Interface Layout
```
+------------------------------------+
| Flight Control  [*] Connected  [=] |
+------------------------------------+
|                                    |
| +- Motor Run Time ----------------+ |
| |  [  20 ] seconds               | |
| |  [5] [10] [15] [20] [30] [60]  | |
| |         [UPDATE ARDUINO]       | |
| +--------------------------------+ |
|                                    |
| +- Total Flight Time -------------+ |
| |  [ 120 ] seconds               | |
| |  [60] [90] [120] [180] [300]   | |
| |         [UPDATE ARDUINO]       | |
| +--------------------------------+ |
|                                    |
| +- Motor Speed -------------------+ |
| |  [ 150 ] (1500us)              | |
| |  [100] [125] [150] [175] [200] | |
| |         [UPDATE ARDUINO]       | |
| +--------------------------------+ |
|                                    |
| +- Quick Actions -----------------+ |
| | [GET PARAMS] [SAVE] [DEFAULTS] | |
| +--------------------------------+ |
|                                    |
| Status: Ready for flight           |
+------------------------------------+
```

### Communication Protocol

#### Serial Protocol - Phase 1 Implementation
Building on existing FlightSequencer serial commands:

**Core Commands** (Currently Implemented):
- `M <sec>` - Set motor run time
- `T <sec>` - Set total flight time
- `S <speed>` - Set motor speed
- `DR <us>` - Set DT retracted position (microseconds)
- `DD <us>` - Set DT deployed position (microseconds)
- `DW <sec>` - Set DT dwell time (seconds)
- `G` - Get current parameters
- `R` - Reset to defaults
- `D J` - Download flight data in JSON format
- `X` - Clear flight records
- `STOP` - Emergency stop
- `?` - Help

**Response Format**:
- Success: `[OK] <message>`
- Error: `[ERR] <message>`
- Info: `[INFO] <message>`

**Future Extensions** *(Phase 3+)*:
- `STATUS` - Detailed system status
- `LIVE` - Live data streaming
- `GPS` - GPS status and position

#### Data Packet Structure
```
Command Packet:  [CMD]<space>[PARAMS]<LF>
Response Packet: [STATUS]<space>[DATA]<LF>
Error Response:  [ERR]:[ERROR_MESSAGE]<LF>
```

#### Flight Data Download Protocol
```
Download Request: D J<LF>
Data Response:    [START_FLIGHT_DATA]
                  HEADER,flight_id,duration_ms,gps_available,position_count,motor_run_time,total_flight_time,motor_speed
                  GPS,timestamp_ms,flight_state,state_name,latitude,longitude
                  GPS,timestamp_ms,flight_state,state_name,latitude,longitude
                  ...
                  [END_FLIGHT_DATA]
```

**Robust CSV Parsing Implementation**:
- **Line Break Recovery**: Automatically detects and merges GPS records split across transmission boundaries
- **Coordinate Validation**: Identifies incomplete coordinate values (e.g., longitude field containing only "-")
- **Error Resilience**: Skips corrupted records while preserving valid flight data
- **Debug Preservation**: Saves problematic raw data with timestamps for analysis
- **Format Support**: Exports to JSON, CSV, and KML formats for analysis and visualization

### Technical Specifications

#### Performance Requirements - Phase 1
- **Connection Time**: < 3 seconds to establish serial connection
- **Command Response**: < 1 second for parameter updates
- **Memory Usage**: < 50MB RAM for core communication features
- **Laptop Battery**: > 3 hours continuous field operation

#### Compatibility Requirements
- **Arduino Hardware**: QtPY SAMD21 with Signal Distribution MkII
- **Python Version**: Python 3.8+ (for mobile framework compatibility)
- **Desktop Systems**: Windows 10+, macOS 10.14+, Ubuntu 18.04+ **[PRIMARY]**
- **Portable Laptops**: Optimized for field operation on battery power
- **Serial Ports**: USB Serial (COM ports on Windows, /dev/tty* on Unix)

#### Security and Safety
- **Parameter Validation**: Prevent unsafe parameter combinations
- **Connection Monitoring**: Detect communication failures immediately
- **Configuration Backup**: Automatic backup of parameter changes
- **Emergency Override**: Always allow emergency stop commands *(Future)*

## Development Phases

### Phase 1: Core Communication **[COMPLETED]**
- **Serial Communication**: Robust PySerial implementation with auto-detection ✓
- **Command Protocol**: Full implementation of existing FlightSequencer commands ✓
- **Parameter Management**: Get/set/validate all flight parameters ✓
- **Error Handling**: Comprehensive communication error recovery ✓
- **Flight Data Download**: Robust CSV parsing with line-break recovery ✓
- **Multi-Tab Interface**: Support for multiple Arduino applications ✓

**Deliverables**:
- Working serial communication library ✓
- Multi-tab GUI with FlightSequencer and GPS Autopilot support ✓
- Robust flight data download with CSV/JSON/KML export ✓
- Flight path visualization with matplotlib integration ✓
- Comprehensive error handling and debug data preservation ✓

### Phase 2: Desktop GUI with Field Operation Focus **[HIGH PRIORITY]**
- **Cross-Platform GUI**: Tkinter or PyQt implementation for Windows/macOS/Linux
- **Field-Optimized Interface**: Large buttons, clear displays for outdoor laptop use
- **Quick Configuration**: Preset buttons and slider controls
- **Connection Management**: Easy serial port selection and connection
- **Field Testing**: Validate portable operation in actual flight conditions

**Deliverables**:
- Cross-platform desktop GUI for parameter configuration
- Field operation manual for laptop use
- Portable-optimized user interface

### Phase 3: Enhanced Desktop Features *(Secondary Priority)*
- **Advanced Interface**: Enhanced desktop parameter management
- **Configuration Management**: Advanced save/load parameter sets
- **Data Logging**: Basic flight parameter logging
- **Session Management**: Flight session tracking

### Phase 4: Real-time Monitoring *(Future)*
- **Real-time Status**: Flight state monitoring during operation
- **Live Data Display**: Real-time parameter monitoring
- **Emergency Controls**: Flight abort and emergency stop

### Phase 5: GPS Integration *(Future - Lower Priority)*
- **GPS Status**: Display GPS fix and satellite information
- **Position Display**: Basic coordinate display
- **Autopilot Parameters**: Future GPS autopilot parameter management

### Phase 6: Data Analysis *(Future - Lowest Priority)*
- **Flight Data Visualization**: Post-flight data plotting
- **Performance Analysis**: Flight performance metrics
- **Export Capabilities**: Data export for external analysis

## File Structure - Phase 1

```
gui/
+-- FlightControlGUI_Specification.md     # This specification
+-- requirements.txt                       # Python dependencies
+-- README.md                             # Quick start guide
+-- main.py                               # Application entry point
+-- config/
|   +-- default_config.json              # Default application settings
|   +-- parameter_presets.json           # Common parameter combinations
+-- src/
|   +-- __init__.py
|   +-- communication/
|   |   +-- __init__.py
|   |   +-- serial_manager.py            # Core serial communication
|   |   +-- protocol.py                  # FlightSequencer protocol
|   |   +-- port_detector.py             # Auto-detect serial ports
|   +-- core/
|   |   +-- __init__.py
|   |   +-- parameter_manager.py         # Parameter validation/storage
|   |   +-- config_manager.py            # Configuration persistence
|   |   +-- validation.py                # Parameter range checking
|   +-- cli/
|       +-- __init__.py
|       +-- console_app.py               # Command-line interface
+-- tests/
|   +-- __init__.py
|   +-- test_communication.py            # Serial communication tests
|   +-- test_protocol.py                 # Protocol parsing tests
|   +-- test_parameters.py               # Parameter validation tests
+-- docs/
    +-- communication_protocol.md        # Protocol specification
    +-- field_operation_guide.md         # Mobile field operation manual
    +-- developer_guide.md               # Development setup
```

### Future File Structure Extensions
```
+-- src/
|   +-- gui/                             # Phase 2 - Desktop GUI
|   |   +-- tkinter_app.py               # Tkinter implementation
|   |   +-- qt_app.py                    # PyQt implementation
|   |   +-- parameter_panel.py           # Parameter configuration widgets
|   |   +-- status_panel.py              # Connection status display
|   +-- data/                            # Phase 3+ - Data management
|   |   +-- logger.py                    # Data logging
|   |   +-- analysis.py                  # Data analysis
|   +-- gps/                             # Phase 5 - GPS integration
|   |   +-- gps_manager.py               # GPS data handling
|   |   +-- position_display.py          # Position visualization
|   +-- mobile/                          # Phase 7+ - Mobile platforms
|       +-- kivy_app.py                  # Cross-platform mobile
|       +-- ios_app.py                   # iOS native implementation
|       +-- android_app.py               # Android native implementation
```

## Quality Assurance

### Testing Strategy - Phase 1
- **Unit Tests**: Individual component testing with pytest
- **Hardware Integration Tests**: Actual FlightSequencer communication testing
- **Protocol Tests**: Command/response validation
- **Error Recovery Tests**: Communication failure handling

### Error Handling - Phase 1
- **Serial Port Errors**: Handle port unavailable, permission denied
- **Communication Timeouts**: Retry logic with exponential backoff
- **Parameter Validation**: Clear error messages for invalid ranges
- **Connection Recovery**: Automatic reconnection attempts

### Documentation Requirements - Phase 1
- **Communication Protocol**: Complete command specification
- **Field Operation Guide**: Mobile usage instructions
- **Developer Setup**: Environment setup and testing procedures
- **API Documentation**: Core communication library documentation

## Success Criteria

### Phase 1 Success Metrics
1. **Reliable Communication**: 99%+ success rate for parameter commands
2. **Fast Connection**: < 3 seconds to establish serial connection
3. **Error Recovery**: Automatic recovery from 90%+ of communication errors
4. **Hardware Compatibility**: Works with all QtPY SAMD21 boards
5. **Cross-Platform**: Runs on Windows, macOS, and Linux

### Phase 2 Success Metrics
1. **Cross-Platform Deployment**: Working desktop apps on Windows/macOS/Linux
2. **Field Usability**: Successful parameter changes on laptop in outdoor conditions
3. **Portable Interface**: Usable on laptop screens in bright sunlight
4. **Battery Life**: > 3 hours continuous operation on laptop battery

## Future Extensions *(Lower Priority)*

### Phase 7+: Mobile Platform Support *(Future)*
- **iOS/Android Apps**: Native mobile apps for field operation
- **Touch Interface**: Tablet-optimized parameter configuration
- **Bluetooth Serial**: Wireless communication via Bluetooth adapters
- **Voice Control**: Voice commands for hands-free operation

### Advanced Desktop Features
- **Multi-Aircraft**: Manage multiple aircraft with different COM ports
- **Offline Mode**: Parameter configuration without Arduino connection
- **Advanced Logging**: Detailed flight data analysis

### Integration Opportunities *(Lowest Priority)*
- **Flight Simulator**: X-Plane/FlightGear integration
- **Competition Scoring**: Contest management integration
- **Weather Data**: Real-time weather overlay
- **Cloud Sync**: Parameter set synchronization across devices

This specification prioritizes establishing reliable communication first, followed by mobile field operation capabilities, with desktop analysis features and GPS integration as future enhancements once the core communication foundation is solid and field-tested.