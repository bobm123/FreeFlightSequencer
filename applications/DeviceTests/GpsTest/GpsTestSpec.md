# GpsTest Specification

## Overview

The GpsTest application validates GPS module integration with the QtPY SAMD21 via Signal Distribution MkII carrier board. This test verifies NMEA sentence parsing, coordinate extraction, and GPS status monitoring for flight control applications.

## Hardware Requirements

- Adafruit QT Py SAMD21 microcontroller
- Signal Distribution MkII carrier board
- GPS module with UART output connected to GPS0 connector
- GPS antenna with clear sky view for satellite reception
- 5V BEC power supply (from ESC or bench supply)
- USB connection for serial monitoring

## GPS Hardware Connection

### Signal Distribution MkII GPS0 Connector
- **Pin 1**: VBEC (5V power to GPS module)
- **Pin 2**: GPS-TX → Qt Py RX/TX pin (D6) → Serial1 RX
- **Pin 3**: GND (common ground)

### Supported GPS Modules
- **u-blox NEO-6M/8M**: Standard hobby GPS modules
- **Adafruit Ultimate GPS**: High-sensitivity GPS breakout
- **Generic NMEA GPS**: Any GPS module outputting standard NMEA sentences at 9600 baud

## Test Objectives

### GPS Communication Validation
- Verify Serial1 communication with GPS module at 9600 baud
- Validate NMEA sentence reception and parsing
- Test GPS module power-on initialization sequence
- Confirm GPS data stream continuity and timing

### NMEA Sentence Processing
- Parse standard GPS sentences: GGA, RMC, GSA, GSV
- Extract key navigation data: latitude, longitude, altitude, speed
- Validate GPS fix status and quality indicators
- Monitor satellite count and signal strength (HDOP/VDOP)

### Coordinate System Validation
- Convert GPS coordinates to decimal degrees format
- Validate coordinate precision and accuracy
- Test coordinate boundary conditions and edge cases
- Verify altitude reporting in meters above sea level

### GPS Status Monitoring
- Track GPS fix acquisition from cold start
- Monitor fix type: No fix, 2D fix, 3D fix
- Report time-to-first-fix (TTFF) performance
- Detect GPS signal loss and recovery

## Test Sequence

### Phase 1: GPS Module Detection (0-30 seconds)
1. **Power-on Sequence**: Initialize Serial1 communication at 9600 baud
2. **Stream Detection**: Monitor for incoming NMEA sentences
3. **Baud Rate Validation**: Confirm GPS communication parameters
4. **Module Identification**: Parse GPS module type and firmware version

### Phase 2: NMEA Parsing Validation (30-120 seconds)
1. **Sentence Structure**: Validate NMEA sentence format and checksum
2. **Data Extraction**: Parse latitude, longitude, altitude, speed, heading
3. **Fix Status**: Monitor GPS fix acquisition progress
4. **Error Handling**: Test malformed sentence rejection and error recovery

### Phase 3: Navigation Data Validation (2-10 minutes)
1. **Coordinate Accuracy**: Verify coordinate stability and precision
2. **Fix Quality**: Monitor satellite count and position dilution of precision
3. **Altitude Reporting**: Validate altitude accuracy against known elevation
4. **Movement Detection**: Test speed and heading calculation accuracy

### Phase 4: Long-term Stability (10+ minutes)
1. **Data Continuity**: Verify continuous GPS data stream
2. **Signal Quality**: Monitor satellite tracking and signal strength
3. **Memory Usage**: Check for memory leaks in GPS data processing
4. **Performance Analysis**: Measure GPS update rate and processing time

## Expected Behavior

### GPS Module Initialization
- GPS module powers on within 2-3 seconds of system startup
- NMEA sentences begin streaming within 5-10 seconds
- GPS attempts satellite acquisition automatically
- Status LED provides visual feedback of GPS operation

### Satellite Acquisition
- **Cold Start**: 30-60 seconds to first 3D fix (clear sky)
- **Warm Start**: 10-20 seconds to fix restoration
- **Hot Start**: 5-10 seconds after recent power cycle
- **Indoor/Obstructed**: No fix or degraded 2D fix only

### NMEA Data Stream
- **Update Rate**: 1Hz (1 update per second) standard
- **Sentence Types**: Minimum GGA and RMC for basic navigation
- **Data Accuracy**: ±3 meters horizontal accuracy (clear sky)
- **Altitude Accuracy**: ±5 meters vertical accuracy

### Serial Output Format
- Clear coordinate display in degrees/minutes/seconds and decimal
- GPS status indicators: Fix type, satellite count, accuracy metrics
- Real-time position updates with timestamp information
- Error messages for GPS communication failures

## Pass Criteria

### Functional Requirements
1. **GPS Communication**: Successfully receive and parse NMEA sentences
2. **Data Extraction**: Extract valid latitude, longitude, altitude data
3. **Fix Acquisition**: Achieve 3D GPS fix within reasonable time
4. **Coordinate Accuracy**: Report coordinates within expected accuracy
5. **Status Monitoring**: Correctly identify GPS fix status and quality

### Performance Requirements
1. **Communication Rate**: Maintain stable 9600 baud communication
2. **Update Frequency**: Process GPS updates at 1Hz or faster
3. **Memory Usage**: Operate within Arduino memory constraints
4. **Processing Time**: Parse GPS sentences without blocking other operations
5. **Error Recovery**: Gracefully handle GPS communication errors

### Integration Requirements
1. **Power Consumption**: Operate within carrier board power budget
2. **Serial Port Usage**: Correctly use Serial1 without conflict
3. **Status Display**: Provide clear visual feedback via NeoPixel
4. **Debug Output**: Generate comprehensive serial debug information
5. **Long-term Operation**: Stable operation for extended test periods

## Failure Modes

### Hardware Issues
- **No GPS Power**: GPS module not receiving 5V power
- **Wiring Problems**: GPS-TX not connected to Qt Py RX pin
- **Antenna Issues**: GPS antenna disconnected or obstructed
- **Module Failure**: GPS module hardware malfunction

### Software Issues
- **Serial Configuration**: Incorrect Serial1 baud rate or parameters
- **Parsing Errors**: NMEA sentence parsing failures
- **Memory Issues**: Buffer overflow or memory allocation problems
- **Timing Problems**: GPS processing blocking other system functions

### Environmental Issues
- **Poor Sky View**: Indoor testing or obstructed GPS antenna
- **RF Interference**: Nearby electronics interfering with GPS reception
- **Atmospheric Conditions**: Ionospheric interference affecting accuracy
- **Location Issues**: Testing in GPS-denied environment

## GPS Data Format Reference

### Standard NMEA Sentences
```
$GPGGA - Global Positioning System Fix Data
$GPRMC - Recommended Minimum Navigation Information
$GPGSA - GPS DOP and active satellites
$GPGSV - GPS Satellites in view
```

### Sample NMEA Output
```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
```

## Test Duration

**Minimum Test Time**: 15 minutes for basic validation
**Recommended Test Time**: 30 minutes for comprehensive testing
**Extended Test**: 2+ hours for long-term stability validation

## Testing Environment

### Optimal Conditions
- **Location**: Outdoors with clear sky view
- **Weather**: Clear conditions, minimal atmospheric interference
- **Time**: Any time with adequate satellite constellation
- **Interference**: Away from RF sources and tall buildings

### Acceptable Conditions  
- **Location**: Near window with partial sky view
- **Weather**: Light cloud cover acceptable
- **Time**: Avoid GPS maintenance periods (rare)
- **Interference**: Minimal nearby electronics

### Marginal Conditions
- **Location**: Indoor testing (expect degraded performance)
- **Weather**: Heavy cloud cover or precipitation
- **Time**: During GPS satellite maintenance (check NAVCEN)
- **Interference**: Near WiFi, cellular, or other RF sources

## Success Metrics

### GPS Performance Indicators
- **Time to First Fix**: < 2 minutes (cold start, clear sky)
- **Position Accuracy**: < 5 meters CEP (95% confidence)
- **Altitude Accuracy**: < 10 meters (clear sky conditions)
- **Update Rate**: 1 Hz sustained update rate
- **Satellite Count**: 4+ satellites tracked for 3D fix

### System Integration Metrics
- **Memory Usage**: < 80% of available RAM
- **CPU Usage**: GPS processing < 20% of available cycles
- **Communication Reliability**: < 1% NMEA sentence errors
- **Power Consumption**: Within carrier board power budget
- **Long-term Stability**: No degradation over 2+ hour test