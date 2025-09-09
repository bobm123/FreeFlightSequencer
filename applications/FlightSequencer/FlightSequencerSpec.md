# FlightSequencer Specification

## Overview

The FlightSequencer application is a port of the E36-Timer from ATTiny85 to QtPY SAMD21 platform, providing automated flight control for electric free-flight model aircraft. This Phase 1 implementation uses hardcoded parameters for core flight sequencing functionality.

## Hardware Requirements

- Adafruit QT Py SAMD21 microcontroller
- Signal Distribution MkII carrier board
- Motor ESC with BEC connected to ESC0 connector (pin A2)
- Dethermalizer servo connected to CH1 connector (pin A3)
- Push button (onboard tactile switch on A0)
- NeoPixel LED (onboard on pin 11)

## Flight Sequence Objectives

### Primary Flight Control
- Automated motor run sequence (20 second duration)
- Dethermalizer deployment (120 second total flight time)
- Single pushbutton operation for start/arm/reset
- Visual status indication via NeoPixel LED
- Safe motor and servo control

### Hardware Interface Validation
- Standard Arduino Servo library compatibility
- NeoPixel LED status indication
- Single pushbutton state management
- PWM servo control (motor ESC and dethermalizer)

## Flight State Machine

### State Sequence
1. **Ready (State 1)**: System initialization and standby
2. **Armed (State 2)**: Armed for launch, waiting for button release
3. **Motor Spool (State 3)**: Motor acceleration to flight speed
4. **Motor Run (State 4)**: Full power flight phase (20 seconds)
5. **Glide (State 5)**: Motor off glide phase (remaining time to 120 seconds total)
6. **DT Deploy (State 6)**: Dethermalizer deployment
7. **Landing (State 99)**: Flight complete, reset available

### State Transitions
- **Ready → Armed**: Button press detected
- **Armed → Motor Spool**: Button released
- **Motor Spool → Motor Run**: Motor ramp complete
- **Motor Run → Glide**: 20 second timer expires
- **Glide → DT Deploy**: 120 second total flight timer expires
- **DT Deploy → Landing**: Dethermalizer deployment complete
- **Landing → Ready**: Button held for 3+ seconds

## Hardcoded Parameters (Phase 1)

### Flight Timing
- **Motor Run Duration**: 20 seconds
- **Total Flight Duration**: 120 seconds (2 minutes)
- **Motor Speed**: 150 (1500µs PWM pulse)

### Servo Control
- **Motor Idle**: 950µs PWM pulse (MIN_SPEED = 95)
- **Motor Full**: 1500µs PWM pulse (MotSpeed = 150)
- **DT Retracted**: 1000µs PWM pulse
- **DT Deployed**: 2000µs PWM pulse

## Expected Behavior

### LED Status Patterns
- **Ready State**: Heartbeat pattern (double blink, pause)
- **Armed State**: Fast continuous blinking
- **Motor Spool**: Solid red LED
- **Motor Run**: Solid red LED
- **Glide Phase**: Slow on/off blink (1 second cycle)
- **DT Deploy**: Solid red during deployment
- **Landing**: Slow single blink (3 second cycle)

### Motor Control
- **Initialization**: Motor set to idle (950µs)
- **Spool Phase**: Smooth ramp from idle to flight speed
- **Run Phase**: Maintain constant speed (1500µs)
- **Shutdown**: Immediate return to idle speed
- **Emergency**: Button press during run stops motor

### Dethermalizer Control
- **Initialization**: Servo retracted (1000µs)
- **Flight Phase**: Remains retracted
- **Deployment**: Move to deployed position (2000µs)
- **Hold**: Maintain deployment for 2 seconds
- **Return**: Return to retracted position

## Pass Criteria

### Functional Requirements
1. Complete flight sequence execution (Ready through Landing)
2. Accurate timing (20 second motor, 120 second total)
3. Proper motor speed control and transitions
4. Reliable dethermalizer deployment
5. Correct LED status indication for each phase
6. Single button operation (press/release/hold)

### Safety Requirements
1. Motor starts at idle and returns to idle
2. Emergency motor shutoff via button press
3. Dethermalizer deploys only at proper time
4. System can be reset from Landing state
5. No spurious state transitions

### Performance Requirements
1. Motor ramp smooth without jerking
2. Timing accuracy within ±0.5 seconds
3. LED patterns clearly distinguishable
4. Button response time < 100ms
5. Servo movements crisp and reliable

## Failure Modes

### Hardware Issues
- Motor ESC not responding (check wiring/BEC power)
- Dethermalizer servo not moving (check connection/power)
- Button not responding (check carrier board connection)
- LED not functioning (check NeoPixel library/pin)

### Software Issues
- Servo library attachment failures
- Timing inaccuracies (check millis() usage)
- State machine stuck in invalid state
- Button debouncing issues

### Flight Issues
- Motor runs too long/short (timing validation)
- Dethermalizer deploys early/late (state sequence validation)
- System doesn't reset properly (button hold detection)

## Integration Notes

This application replaces the original E36-Timer functionality with these key differences:
- Single pushbutton operation (vs. dual button programming)
- NeoPixel LED status (vs. simple LED)
- Standard Arduino Servo library (vs. megaTinyCore)
- QtPY SAMD21 platform (vs. ATTiny85)
- Hardcoded parameters (vs. EEPROM storage)

## Future Enhancements (Phase 2)

Phase 2 will add parameter programming capability:
- Serial command interface for PC-based parameter adjustment
- FlashStorage for non-volatile parameter storage
- Parameter validation and default restoration
- Extended diagnostic and configuration modes

## Test Duration

Complete flight sequence: 120 seconds (2 minutes) plus initialization and reset time. Multiple test flights recommended to validate timing accuracy and system reliability.