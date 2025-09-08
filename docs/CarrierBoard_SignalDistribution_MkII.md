# Signal Distribution Mk II Carrier Board

## Overview

The Signal Distribution Mk II is a custom carrier board designed for the Adafruit Qt Py SAMD21 autopilot system. It provides power distribution, signal routing, and connector breakouts for a complete flight control system.

## Board Features

### Power System
- **VBEC Power Rail**: Distributes 5V power from ESC BEC to all peripherals
- **Reverse Protection**: 1N4007 diode prevents reverse polarity damage
- **Ground Plane**: Common ground for all components
- **No Onboard Regulation**: Requires external 5V BEC (from ESC)

### Connectors

#### Qt Py Socket (JP1)
- **Type**: 7-pin castellated holes
- **Purpose**: Mounts Adafruit Qt Py SAMD21 module
- **Signals**: All Qt Py pins pass through to board

#### Servo Channel (CH1)  
- **Type**: 3-pin header (2.54mm pitch)
- **Pinout**: 
  - Pin 1: VBEC (5V from ESC)
  - Pin 2: Signal (Qt Py A3/D3)
  - Pin 3: GND
- **Use**: Flight control servo connection

#### Motor ESC (ESC0)
- **Type**: 3-pin header (2.54mm pitch)  
- **Pinout**:
  - Pin 1: VBEC (5V BEC output from ESC)
  - Pin 2: Signal (Qt Py A2/D2)
  - Pin 3: GND
- **Use**: Motor ESC with BEC connection

#### GPS Module (GPS0)
- **Type**: 3-pin header (2.54mm pitch)
- **Pinout**:
  - Pin 1: VBEC (5V power)
  - Pin 2: GPS-TX (connects to Qt Py RX pin)
  - Pin 3: GND
- **Use**: UART GPS module connection

#### Expansion (JP2)
- **Type**: 7-pin castellated holes
- **Purpose**: Additional I/O breakout
- **Signals**: Mirror of Qt Py pins

#### Push Button (U$1)
- **Type**: EVQ-11GO7KPB2 tactile switch
- **Connection**: Qt Py A0/D0 with pull-up
- **Purpose**: Auxiliary system start/user input

## Pin Mapping

### Qt Py to Carrier Board Connections
```
Qt Py Pin    | Carrier Function     | Connector
-------------|----------------------|----------
A3 (D3)      | Servo PWM            | CH1 pin 2
A2 (D2)      | Motor ESC PWM        | ESC0 pin 2
A0 (D0)      | Auxiliary Button     | U$1
TX (D6)      | GPS RX               | GPS0 pin 2
RX (D7)      | GPS TX               | NC
SDA (D4)     | I2C Data             | Available on JP2
SCL (D5)     | I2C Clock            | Available on JP2
D8,D9,D10    | SPI/Expansion        | Available on JP2
```

## Power Requirements

### ESC with BEC Specifications
**REQUIRED**: Motor ESC must have built-in BEC (Battery Eliminator Circuit)

#### Power Output Requirements:
- **Voltage**: 5V regulated
- **Current**: 2-3A minimum capacity
- **Load**: Powers Qt Py + GPS + Servo(s)

#### Power Distribution:
- ESC BEC → ESC0 connector pin 1 (VBEC)
- VBEC rail powers:
  - Qt Py module (via JP1)
  - GPS module (via GPS0 pin 1)  
  - Servo(s) (via CH1 pin 1)
  - Additional loads on JP2

### Recommended ESC Types
- **Castle Creations Phoenix** series (integrated BEC)
- **Hobbywing SkyWalker** series (built-in BEC) 
- **Turnigy Plush** ESCs with BEC
- **Any hobby ESC** with 5V BEC rated for motor requirements

### Power Budget Calculation
```
Qt Py SAMD21:     ~100mA
GPS Module:       ~30-50mA  
Standard Servo:   ~500-800mA (under load)
Margin:           ~500mA
Total Required:   ~2-3A BEC capacity
```

## Signal Compatibility

### PWM Outputs
- **Servo Control**: 50Hz PWM, 900-2100µs pulse width (Qt Py A3)
- **Motor ESC**: 50Hz PWM, 1000-2000µs pulse width (Qt Py A2)
- **Arduino Servo Library**: Compatible with both channels

### Communication
- **GPS**: 9600 baud UART (GPS TX → Qt Py RX on pin D7)
- **Ground Station**: USB CDC via Qt Py native USB
- **I2C**: Available for IMU/sensors on SDA/SCL pins

## Board Layout Notes

- **Compact Design**: Optimized for small aircraft integration
- **Castellated Holes**: Allow board-to-board soldering if needed
- **Standard Headers**: 2.54mm pitch for easy servo/component connections
- **Reverse Protection**: Diode protects against power connection mistakes

## Integration Recommendations

1. **Mount Qt Py** on JP1 socket (castellated holes)
2. **Connect ESC** with BEC to ESC0 connector
3. **Connect servo** to CH1 connector  
4. **Connect GPS** module to GPS0 connector
5. **Verify 5V BEC** output before powering system
6. **Test button function** for auxiliary control

This carrier board design provides a clean, integrated solution for Qt Py-based flight control systems with proper power distribution and signal routing.