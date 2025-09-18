# ServoTest Specification

## Overview

The ServoTest application validates PWM servo control functionality using the standard Arduino Servo library on the QtPY SAMD21 platform via the Signal Distribution MkII carrier board.

## Hardware Requirements

- Adafruit QT Py SAMD21 microcontroller
- Signal Distribution MkII carrier board
- Motor ESC connected to ESC0 connector (pin A2)
- Dethermalizer servo connected to CH1 connector (pin A3)
- Push button (onboard tactile switch on A0)

## Test Objectives

### Primary Validation
- Arduino Servo library initialization and attachment
- PWM pulse width control accuracy (950us to 2000us range)
- Motor ESC speed ramp sequences
- Dethermalizer deployment/retract sequences
- Timing accuracy and servo response

### Pin Mapping Validation
- Motor ESC control on QtPY pin A2 (ESC0 connector)
- Dethermalizer servo control on QtPY pin A3 (CH1 connector)
- Button input on QtPY pin A0 (onboard switch)

## Test Sequence

### Phase 1: Motor ESC Testing
1. **Announce**: Display motor test start message
2. **Ramp Up**: Smooth acceleration from idle (950us) to full speed (2000us)
3. **Full Speed**: Hold at maximum speed for 3 seconds
4. **Ramp Down**: Smooth deceleration back to idle speed

### Phase 2: Dethermalizer Testing
1. **Announce**: Display DT test start message
2. **Deploy**: Move servo to deployment position (2000us)
3. **Hold**: Maintain deployment for 2 seconds
4. **Retract**: Return servo to retracted position (1000us)

### Phase 3: Combined Flight Sequence
1. **Announce**: Display combined sequence start
2. **Motor Ramp**: 1-second acceleration to full speed
3. **Motor Run**: 5-second full speed operation
4. **Glide Phase**: 3-second motor idle period
5. **DT Deploy**: 2-second dethermalizer deployment
6. **Complete**: Return to safe positions

## Expected Behavior

### Serial Output
- Test initialization messages with pin assignments
- Real-time PWM pulse width reporting (in microseconds)
- Phase transition announcements
- Test completion statistics
- Status LED flash sequence at completion

### Servo Response
- **Motor ESC**: Smooth speed transitions without jerking
- **Dethermalizer**: Crisp position changes between retract/deploy
- **Timing**: Precise adherence to programmed delays
- **Range**: Full PWM range utilization (950us - 2000us)

### Test Statistics
- Motor ramp cycles completed
- Dethermalizer deployment cycles
- Combined flight sequences executed
- PWM range verification (950us to 2000us)

## Pass Criteria

### Functional Requirements
1. Both servos respond to PWM commands
2. Full PWM range achieved (950us minimum, 2000us maximum)
3. Smooth motor speed transitions
4. Accurate timing between phases
5. No servo chatter or instability

### Output Requirements
1. Serial messages match expected format
2. PWM values reported correctly in microseconds
3. Test statistics accurately counted
4. Status LED completion indication

## Failure Modes

### Hardware Issues
- Servo not responding (wiring/power)
- Erratic servo movement (power/signal integrity)
- Button not registering presses

### Software Issues
- Servo library attachment failures
- Incorrect PWM pulse widths
- Timing inaccuracies
- Serial communication problems

## Integration Notes

This test validates the servo control interface that will be used in the FlightSequencer application for E36 timer functionality. The PWM ranges and timing characteristics tested here directly apply to the motor ESC and dethermalizer control in the flight timer application.

## Duration

Approximately 60 seconds total test time with option for early termination via test timeout.