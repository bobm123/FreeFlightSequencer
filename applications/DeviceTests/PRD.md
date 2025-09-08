# Device Test Suite - Product Requirements Document

## Overview
Comprehensive testing application that validates all connected hardware devices and provides a regression testing framework for development.

## Purpose
- Validate all peripheral devices on signal distribution board
- Create reusable test framework for ongoing development
- Extend HAL components for GPS, servo, and ESC interfaces
- Establish system integration baseline

## Hardware Requirements
- Complete signal distribution board setup (see [TargetHardware.md](../../docs/TargetHardware.md))
- GPS module connected to Hardware UART (TX/RX pins)
- Servo connected to CH1 connector
- ESC connected to ESC0 connector
- Push button and onboard NeoPixel from Phase 1

## Functional Requirements

### Hardware Device Testing
- **Button Test**: Validate debouncing, press/release detection, long press detection (>5 sec), interrupt handling
- **NeoPixel Test**: Test colors, brightness, and power control
- **Serial Test**: USB serial and Hardware UART communication validation
- **PWM Test**: Servo and ESC signal generation and verification
- **GPS Module Test**:
  - Detect GPS module presence
  - Parse basic NMEA sentences (GGA, RMC)
  - Extract position, time, and satellite count
  - Validate data integrity and checksums
- **Servo Test**:
  - Generate PWM signals (1-2ms pulse, 50Hz)
  - Test position accuracy across range
  - Validate calibration and limits
- **ESC Test**:
  - Generate ESC control signals
  - Test arming sequence and safety
  - Validate throttle response

### System Integration Testing
- All devices operational simultaneously
- Memory usage monitoring during multi-device operation
- Timing validation under load
- Extended operation stability (configurable duration)

### Test Framework
- Individual test selection via serial interface
- Complete test suite execution
- Factual output reporting for user validation
- Test results comparison with ExpectedResults.txt files
- User-validated pass/fail determination

## Test Specifications

### Test Categories
1. **Basic Hardware** (5-10 seconds each): Core GPIO and communication
2. **Device Communication** (10-30 seconds each): Data parsing and validation
3. **Integration Tests** (30-60 seconds each): Multi-device operation
4. **Stress Tests** (configurable 5-30 minutes): Long-term stability

### Testing Methodology
- Tests provide factual output without automated pass/fail decisions
- Each test includes ExpectedResults.txt file showing typical good output
- User compares serial monitor output with expected results
- User determines pass/fail based on output comparison
- This approach prevents false confidence from automated validation

## Non-Functional Requirements

### Performance
- Test execution time should be reasonable for development workflow
- Real-time monitoring without interfering with device operation
- Memory usage tracking throughout test execution

### Code Quality
- Extend shared HAL components for all devices
- Create reusable test framework in [../../shared/tests/](../../shared/tests/)
- Follow established coding guidelines and serial output standards

## Success Criteria
- All connected devices pass individual validation tests
- System operates stably with all devices active for extended periods
- Test framework ready for regression testing in later phases
- HAL components complete for GPS, servo, and ESC interfaces

## Dependencies
- Phase 1 LED/Button application completion
- All hardware devices connected per signal distribution board
- GPS module with valid NMEA output
- Servo and ESC hardware for testing

## Deliverables
- Comprehensive test suite application (DeviceTests.ino)
- Extended HAL components (hal_gps.h/cpp, hal_servo.h/cpp, hal_esc.h/cpp)
- Shared test framework components
- Test documentation and usage instructions
- Makefile for Arduino CLI builds