# FlightSequencer - E36 Timer Port to QtPY SAMD21

## Phase 1: Core Flight Sequencer (Hardcoded Parameters)

### Test Applications
- [x] ~~Create test application for NeoPixel interface~~ *(completed - LedTest exists)*
- [x] ~~Create test application for servo/PWM interface using standard Arduino Servo library~~ *(completed - ServoTest validated)*

### Core Porting Tasks
- [x] ~~Create FlightSequencer application directory and basic structure~~ *(completed)*
- [x] ~~Port E36-Timer main sketch to QtPY SAMD21 with hardcoded parameters~~ *(completed)*
- [x] ~~Replace pinMode and pin definitions for QtPY SAMD21~~ *(completed)*
- [x] ~~Update servo library include from Servo_megaTinyCore.h to standard Servo.h~~ *(completed)*
- [x] ~~Replace digitalWrite LED calls with NeoPixel functions~~ *(completed)*
- [x] ~~Remove second pushbutton code and programming states 95-98~~ *(completed)*
- [x] ~~Remove all EEPROM code and use hardcoded parameters~~ *(completed)*
- [x] ~~Create Makefile for FlightSequencer QtPY build system~~ *(completed)*

### Phase 1 Testing [COMPLETED] ALL COMPLETE
- [x] ~~Test 1.1: Basic flight sequence operation~~ *(completed - validated complete flight sequence)*
- [x] ~~Test 1.2: Reset and run sequence again~~ *(completed - fixed static variable reset bug)*
- [x] ~~Test 1.3: Emergency cutoff from all states~~ *(completed - validated emergency cutoff in states 3, 4, 5)*

### Hardcoded Parameters (Phase 1)
- **Motor Run Time**: 10 seconds *(debug timing, was 20)*
- **Total Flight Time**: 30 seconds *(debug timing, was 120)*
- **Motor Speed**: 150 (1500us PWM pulse)

### Hardware Changes
- **Single pushbutton**: Only PB1 for start/arm sequence
- **NeoPixel LED**: Replace digitalWrite LED control with red NeoPixel
- **Standard Servo**: Use Arduino Servo.h instead of Servo_megaTinyCore.h
- **QtPY pins**: Update pin definitions for SAMD21 platform

### State Machine Simplification
- Remove programming states 95-98 (dual-button parameter adjustment)
- Keep core flight states: Ready(1) -> Armed(2) -> Motor Spool(3) -> Motor Run(4) -> Glide(5) -> DT Deploy(6) -> Landing(99)
- Emergency cutoff available in states 3, 4, and 5 (active flight phases)

## Phase 2: Parameter Programming [COMPLETED]

### Core Implementation Tasks
- [x] ~~Add FlashStorage library integration~~ *(completed)*
- [x] ~~Create FlightParameters struct for parameter storage~~ *(completed)*
- [x] ~~Replace hardcoded constants with dynamic parameter system~~ *(completed)*
- [x] ~~Implement serial command interface (M/T/S/G/R/? commands)~~ *(completed)*
- [x] ~~Add parameter validation logic~~ *(completed)*
- [x] ~~Add FlashStorage parameter persistence~~ *(completed)*
- [x] ~~Update initialization to load saved parameters~~ *(completed)*

### Serial Command Interface
- **M <sec>**: Set motor run time (5-60 seconds)
- **T <sec>**: Set total flight time (30-600 seconds) 
- **S <speed>**: Set motor speed (95-200, maps to 950-2000us PWM)
- **G**: Get current parameters
- **R**: Reset to defaults
- **?**: Show help

### Parameter Storage
- **FlashStorage**: Non-volatile parameter storage survives power cycles
- **Validation**: Range checking and logical relationship validation
- **Defaults**: 20s motor, 120s total, 150 speed (1500us PWM)
- **Safety**: Serial commands only available in Ready(1) or Landing(99) states

### Timestamp System [COMPLETED]
- **Format**: mm:ss timestamps for clear time display
- **Reset**: Timer resets to 00:00 when returning to Ready state
- **Flight Tracking**: Each flight sequence gets clean timing from 00:00

## Flight Testing Phase
*Ready for field testing:*
- [ ] Ground testing with motor ESC and servo hardware
- [ ] Bench testing of parameter programming via serial interface
- [ ] Flight testing with actual aircraft for timing validation
- [ ] Emergency cutoff testing during actual flight phases
- [ ] Parameter tuning based on flight performance data

## Key Flight Sequence
1. **Ready**: Heartbeat LED pattern, wait for long button press
2. **Armed**: Fast LED flash, short press to launch
3. **Motor Spool**: LED on, ramp motor to speed *(Emergency: Button press -> Landing)*
4. **Motor Run**: LED on, motor at full speed for 10 seconds *(Emergency: Button press -> Landing)*
5. **Glide**: LED slow blink, motor off, wait for 30 seconds total *(Emergency: Button press -> Landing, skip DT)*
6. **DT Deploy**: Deploy dethermalizer servo *(No emergency cutoff)*
7. **Landing**: Slow blink, long press to reset