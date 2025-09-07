# LED Button Application - Product Requirements Document

## Overview
Basic hardware validation application that demonstrates GPIO input/output, debouncing, and status indication using the onboard NeoPixel LED and push button.

## Purpose
- Validate Adafruit QT Py SAMD21 hardware platform
- Establish basic Hardware Abstraction Layer (HAL) components
- Demonstrate Arduino C integration workflow
- Provide foundation for more complex applications

## Hardware Requirements
- Adafruit QT Py SAMD21 (see [TargetHardware.md](../../docs/TargetHardware.md))
- Signal Distribution Board with push button
- Onboard NeoPixel LED (pin 11)
- USB connection for serial communication

## Functional Requirements

### Button Input Processing
- Detect button press/release events from hardware push button
- Implement software debouncing (configurable, default 50ms)
- Handle button as active-low with internal pullup
- Ignore spurious signals during debounce period

### LED Status Indication  
- Control onboard NeoPixel LED for visual feedback
- Color sequence on button press: Red → Green → Blue → White → Off → Red (repeat)
- Optional: Smooth color transitions or fade effects
- Support LED power control (pin 12) for battery operation

### Serial Communication
- USB serial at 9600 baud for debug output
- Report system initialization status
- Log button events with timestamps
- Report LED color changes
- Optional: Memory usage monitoring

### System Initialization
- Initialize GPIO pins and serial communication
- Perform basic self-test
- Display startup pattern on LED
- Establish known system state

## Non-Functional Requirements

### Performance
- Button response time: < 100ms
- Serial message transmission: < 200ms from event

### Memory Constraints
- SRAM usage: < 2KB (leave headroom for future development)
- Flash usage: < 16KB

### Code Quality
- Follow [arduino-c-integration-guide.md](../../docs/arduino-c-integration-guide.md)
- Use ASCII-only serial output (see [CLAUDE.md](../../CLAUDE.md))
- Create reusable HAL components in [../../shared/hardware/](../../shared/hardware/)

## Success Criteria
- Button press reliably changes LED color
- No false button triggers during 10-minute continuous operation
- Clean serial debug output with proper formatting
- HAL components ready for reuse in Phase 2 applications

## Dependencies
- Arduino IDE with SAMD21 board support
- Adafruit NeoPixel library
- Hardware connections per signal distribution board schematic

## Deliverables
- Working Arduino sketch (led_button.ino)
- Reusable HAL components (hal_button.h/cpp, hal_neopixel.h/cpp)  
- Application-specific documentation
- Makefile for Arduino CLI builds