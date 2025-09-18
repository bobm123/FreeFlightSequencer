# Target Hardware Documentation

## Overview

This document describes the target hardware platform for the Arduino C code integration project, consisting of a Signal Distribution Board with an Adafruit QT Py SAMD21 microcontroller.

## System Architecture

### Primary Target: Adafruit QT Py SAMD21 Dev Board
- **Product Page**: [https://www.adafruit.com/product/4600](https://www.adafruit.com/product/4600)
- **Microcontroller**: ATSAMD21E18 32-bit Cortex M0+
- **Clock Speed**: 48 MHz  
- **Memory**: 256KB Flash, 32KB RAM
- **Form Factor**: Xiao-compatible with castellated pads
- **USB**: Type-C connector with native USB support
- **Arduino IDE**: Fully compatible

#### Official Pinout Diagram
![Adafruit QT Py SAMD21 Pinout](../hardware/qtpy/adafruit_products_Adafruit_QT_Py_SAMD21_pinout.png)

### Signal Distribution Board (MkII)
Custom PCB that provides connections between the QT Py and external devices:
- Servo connector (CH1)
- Motor speed controller connector (ESC0) 
- GPS module connector (GPS0)
- Push button switch
- Protection diode for power management

## Pin Mapping and Connections

### QT Py SAMD21 Pinout
| Pin | Arduino | Function | Capabilities |
|-----|---------|----------|--------------|
| A0/D0 | 0 | GPIO/Analog | Analog input, Analog output (10-bit), Capacitive touch |
| A1/D1 | 1 | GPIO/Analog | Analog input, Optional AREF, Capacitive touch |
| A2/D2 | 2 | GPIO/Analog | Analog input, PWM, Capacitive touch |
| A3/D3 | 3 | GPIO/Analog | Analog input, PWM, Capacitive touch |
| SDA/D4 | 4 | I2C Data | Digital I/O, I2C, PWM |
| SCL/D5 | 5 | I2C Clock | Digital I/O, I2C, PWM |
| TX/A6/D6 | 6 | UART TX | Digital I/O, UART transmit, PWM, Capacitive touch |
| RX/A7/D7 | 7 | UART RX | Digital I/O, UART receive, PWM, Capacitive touch |
| SCK/A8/D8 | 8 | SPI Clock | Digital I/O, SPI, PWM |
| MI/A9/D9 | 9 | SPI MISO | Digital I/O, SPI, PWM |
| MO/A10/D10 | 10 | SPI MOSI | Digital I/O, SPI, PWM |
| - | 11 | NeoPixel | Built-in RGB LED |
| - | 12 | NeoPixel Power | NeoPixel power control (set low for power saving) |

### Power Pins
| Pin | Voltage | Current | Description |
|-----|---------|---------|-------------|
| 3V | 3.3V | 500mA | Regulated 3.3V output |
| 5V | 5.0V | 1A peak | USB 5V passthrough |
| GND | 0V | - | Ground reference |

## Signal Distribution Board Connections

### From KiCad Schematic Analysis

#### JP1 - QT Py Connection (7-pin castellated header)
Primary interface between QT Py and distribution board:
- Pin 1: 3.3V power
- Pin 2: Ground
- Pin 3: GPIO (likely for servo control)
- Pin 4: GPIO (likely for ESC control)  
- Pin 5: GPIO (likely for button input)
- Pin 6: TX (UART transmit for GPS)
- Pin 7: RX (UART receive from GPS)

#### GPS0 Connector (3-pin)
GPS module interface:
- Pin 1: VBEC (power)
- Pin 2: GPS-TX (GPS transmit to QT Py RX)
- Pin 3: GND

#### CH1 Connector (3-pin) - Servo
Servo motor connection:
- Pin 1: VBEC (power)
- Pin 2: PWM signal
- Pin 3: GND

#### ESC0 Connector (3-pin) - Motor Controller
Electronic Speed Controller connection:
- Pin 1: VBEC (power)
- Pin 2: PWM signal  
- Pin 3: GND

#### Push Button (U$1)
User input switch:
- Connects to GPIO pin via pullup/pulldown configuration
- Debouncing may be required in software

#### Protection Diode (D2 - 1N4007)
Power protection:
- Reverse polarity protection for VBEC supply

## Arduino IDE Configuration

### Board Selection
```
Tools > Board > Adafruit SAMD Boards > Adafruit QT Py (SAMD21)
```

### Serial Communication
- **USB Serial**: `Serial` object for debugging/communication with PC
- **Hardware Serial**: `Serial1` object on pins TX(6)/RX(7) for GPS communication

### Key Libraries Required
```cpp
// Core libraries
#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>

// SAMD-specific
#include <Adafruit_NeoPixel.h>  // For onboard LED
#include <FlashStorage.h>       // For parameter storage
```

## Peripheral Integration

### GPS Module
- **Connection**: Hardware UART (Serial1)
- **Pins**: TX(6) -> GPS RX, RX(7) <- GPS TX
- **Baud Rate**: Typically 9600 or 38400
- **Protocol**: NMEA 0183 standard

### Servo Control
- **Connection**: PWM output pin
- **Signal**: 1-2ms pulse width, 50Hz (20ms period)
- **Library**: `Servo.h` or custom PWM

### Motor Speed Controller (ESC)
- **Connection**: PWM output pin
- **Signal**: Similar to servo, but with ESC-specific calibration
- **Initialization**: May require arming sequence

### Push Button
- **Connection**: Digital input with internal pullup
- **Debouncing**: Software debouncing recommended
- **Interrupt**: Can use external interrupt for responsiveness

### Status LED (NeoPixel)
- **Pin**: Digital pin 11
- **Power Control**: Pin 12 (set low to disable for power saving)
- **Library**: `Adafruit_NeoPixel.h`

## Memory Considerations

### SAMD21 Memory Layout
- **Flash**: 256KB (program storage)
- **SRAM**: 32KB (runtime memory)
- **EEPROM**: FlashStorage emulation for parameter storage

### C Library Integration Constraints
- Keep stack usage minimal (recommend < 8KB)
- Use `PROGMEM` for large constant data
- Consider dynamic allocation carefully due to fragmentation risks
- Monitor free memory during development

### Parameter Storage
Use FlashStorage library for persistent parameter storage:
```cpp
#include <FlashStorage.h>

// Define parameter structure
typedef struct {
    float pid_gains[3];
    uint16_t servo_limits[2];
    // ... other parameters
} Parameters;

// Create storage
FlashStorage(param_storage, Parameters);
```

## Development Considerations

### Cross-Platform Compatibility
The hardware abstraction should support:
- Current target: Adafruit QT Py SAMD21
- Future targets: Other Xiao-compatible boards
- Simulation: PC-based testing environment

### Pin Assignment Flexibility
Design wrapper functions to abstract pin assignments:
```cpp
// Hardware abstraction layer
#define SERVO_PIN     A2
#define ESC_PIN       A3  
#define BUTTON_PIN    A1
#define GPS_SERIAL    Serial1
#define DEBUG_SERIAL  Serial
```

### Power Management
- Monitor current consumption, especially for battery operation
- Use sleep modes when appropriate
- Disable NeoPixel (pin 12 low) for power savings

### Testing and Validation
- Hardware-in-the-loop testing capability
- Serial monitoring for debugging
- Status LED feedback for system state indication

## Future Hardware Support

### Expandability
The modular design allows for:
- Different Xiao form-factor boards (ESP32, RP2040, etc.)
- Signal distribution board revisions
- Additional peripheral connections

### Compatibility Requirements
Any future target hardware should provide:
- Arduino IDE compatibility
- Hardware UART for GPS
- At least 2 PWM outputs (servo + ESC)
- Digital input for button
- USB serial for debugging
- Sufficient memory for C library integration (>32KB RAM recommended)