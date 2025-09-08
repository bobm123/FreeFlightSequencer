# FlightSequencer - E36 Timer Port to QtPY SAMD21

## Phase 1: Core Flight Sequencer (Hardcoded Parameters)

### Test Applications
- [x] ~~Create test application for NeoPixel interface~~ *(completed - LedTest exists)*
- [ ] Create test application for servo/PWM interface using standard Arduino Servo library

### Core Porting Tasks
- [ ] Create FlightSequencer application directory and basic structure
- [ ] Port E36-Timer main sketch to QtPY SAMD21 with hardcoded parameters
- [ ] Replace pinMode and pin definitions for QtPY SAMD21
- [ ] Update servo library include from Servo_megaTinyCore.h to standard Servo.h
- [ ] Replace digitalWrite LED calls with NeoPixel functions
- [ ] Remove second pushbutton code and programming states 95-98
- [ ] Remove all EEPROM code and use hardcoded parameters
- [ ] Create Makefile for FlightSequencer QtPY build system
- [ ] Test complete FlightSequencer functionality on QtPY hardware

### Hardcoded Parameters (Phase 1)
- **Motor Run Time**: 20 seconds
- **Total Flight Time**: 2 minutes (120 seconds)
- **Motor Speed**: 150 (1500µs PWM pulse)

### Hardware Changes
- **Single pushbutton**: Only PB1 for start/arm sequence
- **NeoPixel LED**: Replace digitalWrite LED control with red NeoPixel
- **Standard Servo**: Use Arduino Servo.h instead of Servo_megaTinyCore.h
- **QtPY pins**: Update pin definitions for SAMD21 platform

### State Machine Simplification
- Remove programming states 95-98 (dual-button parameter adjustment)
- Keep core flight states: Ready(1) → Armed(2) → Motor Spool(3) → Motor Run(4) → Glide(5) → DT Deploy(6) → Landing(99)

## Phase 2: Parameter Programming (Future)
*Deferred tasks:*
- Create test application for FlashStorage non-volatile memory interface
- Create serial command interface for parameter programming  
- Replace EEPROM calls with FlashStorage for parameter storage
- Implement parameter adjustment, storage, recall, and reset via PC serial interface

## Key Flight Sequence
1. **Ready**: Heartbeat LED pattern, wait for button press
2. **Armed**: Fast LED flash, release button to start
3. **Motor Spool**: LED on, ramp motor to speed
4. **Motor Run**: LED on, motor at full speed for 20 seconds
5. **Glide**: LED slow blink, motor off, wait for 2 minutes total
6. **DT Deploy**: Deploy dethermalizer servo
7. **Landing**: Slow blink, hold button 3+ seconds to reset