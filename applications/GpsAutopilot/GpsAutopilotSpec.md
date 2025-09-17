# GpsAutopilot Product Specification

## Overview

The GpsAutopilot is an Arduino-based autonomous flight control system designed to keep a free-flight model aircraft circling within a 100-meter radius around the launch point. This system builds upon the successful FlightSequencer project and adapts the professional FreeFlight C++ autopilot codebase for Arduino integration.

## Project Objectives

### Primary Objective
Develop a GPS-guided autonomous flight controller that:
- Captures launch position as datum reference point
- Maintains aircraft within 100m circular flight pattern around launch point
- Uses roll control for steering and motor speed for altitude management
- Implements safety systems with manual override capability

### Secondary Objectives
- Demonstrate successful C library integration with Arduino platform
- Establish framework for advanced autopilot features
- Provide telemetry and parameter configuration capabilities
- Enable field testing and validation of autonomous flight control

## System Architecture

### High-Level Design
The GpsAutopilot follows a modular architecture with four core libraries adapted from the FreeFlight reference implementation:

```
GpsAutopilot Application
├── Navigation Library      # GPS processing and state estimation
├── Control Library         # Flight control algorithms
├── Communications Library  # Telemetry and parameter management
├── Math Library           # Mathematical utilities and filters
└── Hardware Abstraction   # Arduino-specific hardware interfaces
```

### State Machine Design
The system operates through discrete flight phases similar to FlightSequencer but with autonomous guidance:

1. **INITIALIZATION** - Hardware setup and parameter loading
2. **ALIGNMENT** - IMU calibration and GPS acquisition
3. **DATUM_CAPTURE** - Establish launch point as reference
4. **LAUNCH_DETECT** - Detect aircraft launch via accelerometer
5. **AUTONOMOUS_FLIGHT** - GPS-guided circular flight pattern
6. **EMERGENCY** - Safety override and recovery modes

## Module Specifications

### 1. Navigation Library

**Purpose**: GPS-based position estimation and sensor fusion

**Key Components**:
- **GPS Processing**: NMEA parsing, position validation, datum management
- **State Estimation**: Position, velocity, attitude estimation from GPS + IMU
- **Coordinate Conversion**: Geodetic to local NED frame conversion
- **Sensor Fusion**: Integration of GPS, accelerometer, and gyroscope data

**Core Functions**:
```cpp
void Nav_Init(void);                        // Initialize navigation system
LPCNAVX Nav_Step(const float dT);          // Update navigation states
void Nav_SetDatum(void);                   // Capture current position as datum
int Nav_IsDatumSet(void);                  // Check if datum is established
float Nav_ComputeTurnRadius(const float Roll); // Calculate turn radius
```

**Navigation States**:
- Position relative to datum (North, East, Up) in meters
- Ground track and ground speed from GPS
- Roll and pitch attitude from IMU integration
- Range and bearing to datum point
- GPS validity and datum status flags

**Parameters**:
- IMU mounting orientation and bias calibration
- GPS update rates and validity thresholds
- Sensor fusion gains (roll from track rate, pitch from acceleration)
- Nominal airspeed for coordinated turn calculations

### 2. Control Library

**Purpose**: Autonomous flight control with circular orbit guidance

**Key Components**:
- **Orbit Controller**: Maintains circular flight pattern around datum
- **Track Controller**: Commands roll angle for desired ground track
- **Roll Controller**: Servo commands for roll attitude control
- **Throttle Controller**: Motor speed control for altitude management
- **Launch Detection**: Accelerometer-based takeoff detection
- **Safety Systems**: Emergency override and failsafe modes

**Core Functions**:
```cpp
void Control_Init(void);                           // Initialize controller
void Control_Step(LPCNAVX pX, const float dT);   // Update control outputs
void Control_LoadRiggingCmds(int bEnable, int bRight, int bMotor); // Manual override
void Control_ResetActuatorSettings(void);         // Update actuator configuration
```

**Control Loops**:
1. **Orbit Control**: Range error → commanded track angle
2. **Track Control**: Track error → commanded roll angle (with PI controller)
3. **Roll Control**: Roll error → servo deflection (with PI controller)
4. **Throttle Control**: Altitude/speed management via motor ESC

**Control Parameters**:
- Orbit radius (100m nominal)
- Proportional and integral gains for each control loop
- Servo limits and rates
- Motor/ESC configuration and limits
- Launch detection sensitivity and timing
- Safety timeouts and emergency thresholds

### 3. Communications Library

**Purpose**: Telemetry, parameter management, and ground station interface

**Key Components**:
- **Protocol Handler**: Message parsing and packet assembly
- **Parameter Management**: Non-volatile storage and real-time updates
- **Telemetry Streaming**: Real-time flight data transmission
- **Command Interface**: Ground station control and configuration
- **Bootloader Support**: Firmware update capability

**Core Functions**:
```cpp
void Coms_Init(void);                              // Initialize communications
void Coms_Step(void);                             // Process incoming/outgoing data
uint32_t Coms_SendData(uint8_t msgID, const void *pData, uint8_t nBytes); // Send telemetry
```

**Message Types**:
- Navigation parameters (sensor gains, mounting orientation)
- Control parameters (loop gains, servo limits, safety timeouts)
- Actuator parameters (servo/ESC configuration)
- Real-time telemetry (position, attitude, control commands)
- System status and diagnostic messages

**Protocol Features**:
- Packet-based communication with error detection
- Parameter upload/download with validation
- Real-time telemetry streaming
- Bootloader activation sequence
- Ground station compatibility

### 4. Math Library

**Purpose**: Mathematical utilities and signal processing functions

**Key Components**:
- **Vector Operations**: 2D/3D vector math, norms, rotations
- **Angle Mathematics**: Angle wrapping, coordinate transformations
- **Filter Functions**: Low-pass, washout, and integration filters
- **Control Utilities**: Rate limiting, deadband, saturation logic
- **Geodetic Functions**: GPS coordinate conversions and distance calculations
- **Flight Dynamics**: Coordinated turn calculations and turn radius computation

**Core Functions**:
```cpp
// Angle mathematics
float ModAngle(const float angle);                     // Wrap angle to ±π
float CoordTurn(const float TurnRate, const float Vs); // Coordinated turn bank angle

// Filtering and control
float LowPassFilter(float *pX, const float U, const float tau, const float dT);
float RateLimitf(const float desired, const float current, const float maxRate, const float dT);

// Geodetic calculations
void CalculateClatClon(double *pClat, double *pClon, const double LatDeg);
float DegreeToMeters(const double ToDeg, const double FromDeg, const double Conv);
```

**Mathematical Constants**:
- Earth gravity, WGS84 ellipsoid parameters
- Unit conversions (degrees/radians, meters/feet)
- Physical constants for flight dynamics

## Hardware Integration

### Arduino Platform Adaptations

**Target Hardware**: Adafruit QT Py SAMD21 (32-bit ARM Cortex-M0+)
- **Memory**: 256KB Flash, 32KB RAM
- **Performance**: 48MHz, sufficient for 50Hz control loop
- **Peripherals**: Hardware UART for GPS, I2C for IMU, PWM for servos

**Hardware Abstraction Layer**:
```cpp
// GPS interface
uint32_t hal_ReadGPS(uint8_t *buffer, uint32_t maxBytes);

// IMU interface  
void hal_ReadIMU(float *accel, float *gyro);

// Servo/ESC outputs
void hal_SetServoPosition(float rollCommand);    // ±1.0 normalized
void hal_SetMotorSpeed(float throttleCommand);   // 0.0-1.0 normalized

// System timing
bool hal_ClockMainLoop(float *deltaTime);       // 50Hz main loop timing
```

**Memory Optimization**:
- Use `PROGMEM` for constant data (lookup tables, strings)
- Optimize floating-point operations for ARM Cortex-M0+
- Minimize RAM usage through careful structure packing
- Selective compilation of unused features

### Sensor Integration

**GPS Module**: 
- UART interface at 9600 baud
- NMEA 0183 protocol parsing
- Position accuracy: <3m typical
- Update rate: 1-10Hz configurable

**IMU (Accelerometer + Gyroscope)**:
- I2C interface
- 3-axis accelerometer for launch detection and pitch estimation
- 3-axis gyroscope for attitude integration
- Update rate: 50Hz synchronized with control loop

**Servo Control**:
- PWM output for roll control surface
- 1000-2000μs pulse width, 50Hz update rate
- Position feedback optional

**Motor/ESC Control**:
- PWM output for motor speed control
- Support for both ESC and direct DC motor control
- Configurable through parameter system

## Flight Control Algorithms

### Circular Orbit Guidance

**Objective**: Maintain aircraft within 100m radius of launch datum

**Control Strategy**:
1. **Range Control**: Calculate distance from current position to datum
2. **Track Command**: Generate desired ground track to maintain circular orbit
3. **Roll Command**: Use coordinated turn dynamics to command bank angle
4. **Servo Output**: Convert roll command to servo deflection

**Mathematical Model**:
```
Range_Error = Current_Range - Desired_Radius
Track_Command = atan2(Position_East, Position_North) + Kp_orbit * Range_Error
Roll_Command = CoordTurn(Track_Rate_Command, Ground_Speed)
Servo_Command = Kp_roll * (Roll_Command - Estimated_Roll) + Ki_roll * Integral_Error
```

### Altitude Management

**Objective**: Maintain suitable flight altitude through motor speed control

**Control Strategy**:
- Monitor climb rate and altitude relative to datum
- Increase motor speed when losing altitude
- Reduce motor speed when climbing excessively
- Implement conservative altitude envelope

### Safety Systems

**Launch Detection**:
- Monitor X-axis acceleration for launch signature
- Arm autonomous control only after confirmed launch
- Timeout-based reset for multi-flight operation

**Emergency Override**:
- Manual servo control via rigging commands
- Motor cutoff capability
- Automatic failsafe on GPS loss or system errors

**Geofencing**:
- Hard limits on distance from datum (200m maximum)
- Automatic emergency mode if aircraft exits safe zone
- Conservative flight envelope for initial testing

## Development Approach

### Phase 1: Core Library Integration
1. **C Library Porting**: Adapt FreeFlight modules for Arduino
2. **Hardware Abstraction**: Implement Arduino-specific HAL
3. **Memory Optimization**: SAMD21 memory constraint management
4. **Basic Testing**: Unit tests for each module

### Phase 2: System Integration
1. **Module Integration**: Combine all libraries in main application
2. **Timing Validation**: Ensure real-time performance at 50Hz
3. **Parameter System**: Implement configuration and persistence
4. **Communication**: Basic telemetry and parameter interface

### Phase 3: Flight Testing
1. **Ground Testing**: Hardware-in-the-loop validation
2. **Sensor Validation**: GPS and IMU accuracy verification
3. **Control Loop Testing**: Servo response and stability
4. **Progressive Flight Testing**: Guided manual → autonomous

### Phase 4: Refinement
1. **Performance Optimization**: Control loop tuning
2. **Safety Validation**: Emergency mode testing
3. **Documentation**: Flight operations manual
4. **Production Testing**: Multiple aircraft validation

## Configuration Parameters

### Navigation Parameters
```cpp
typedef struct {
    float Kroll_trk;      // Roll update gain from track rate (0.1-1.0)
    float Kroll_r;        // Roll update gain from yaw rate (0.1-1.0)
    float Ktrack;         // Track update gain (0.5-2.0)
    float Kpitch_ax;      // Pitch update gain from acceleration (0.1-0.5)
    float Vias_nom;       // Nominal airspeed (m/s) (8.0-15.0)
    uint32_t nMounting;   // IMU mounting orientation
} NavigationParams_t;
```

### Control Parameters
```cpp
typedef struct {
    float Kp_orbit;       // Orbit proportional gain (rad/m) (0.01-0.1)
    float Kp_trk;         // Track proportional gain (0.5-2.0)
    float Ki_trk;         // Track integral gain (0.1-0.5)
    float Kp_roll;        // Roll proportional gain (0.5-2.0)
    float Ki_roll;        // Roll integral gain (0.1-0.5)
    float OrbitRadius;    // Desired orbit radius (m) (50-200)
    float LaunchAccel;    // Launch detection threshold (G) (1.5-3.0)
    float SafetyRadius;   // Maximum safe distance (m) (150-300)
} ControlParams_t;
```

### Actuator Parameters
```cpp
typedef struct {
    float ServoCenter;    // Servo center position (μs) (1400-1600)
    float ServoRange;     // Servo range (μs) (300-600)
    float ServoRate;      // Maximum servo rate (deg/s) (60-180)
    float MotorMin;       // Minimum motor speed (%) (0-20)
    float MotorMax;       // Maximum motor speed (%) (80-100)
    uint32_t nMotorType;  // Motor type: 0=DC, 1=ESC
} ActuatorParams_t;
```

## Success Criteria

### Technical Requirements
- **Control Performance**: Maintain <100m radius 90% of flight time
- **System Stability**: No oscillations or instability in control loops
- **GPS Accuracy**: Position accuracy <5m during autonomous flight
- **Real-time Performance**: Maintain 50Hz control loop without timing violations
- **Memory Usage**: <80% of available Flash and RAM resources

### Safety Requirements
- **Launch Detection**: Reliable takeoff detection within 2 seconds
- **Emergency Override**: Manual control available within 1 second
- **Geofencing**: Hard stop at 200m from datum point
- **GPS Loss**: Safe behavior during GPS signal interruption
- **Battery Monitoring**: Low voltage detection and response

### Operational Requirements
- **Parameter Configuration**: Field-adjustable parameters via ground station
- **Telemetry**: Real-time position, attitude, and control data
- **Multi-flight**: Automatic reset capability for consecutive flights
- **Weather Tolerance**: Operation in light wind conditions (<10 mph)
- **Flight Duration**: Support for 5-15 minute autonomous flights

## Risk Mitigation

### Technical Risks
- **Memory Constraints**: Progressive optimization and selective feature compilation
- **Real-time Performance**: Careful algorithm selection and timing validation
- **GPS Accuracy**: Conservative control gains and geofencing limits
- **Sensor Integration**: Extensive ground testing and calibration procedures

### Safety Risks
- **Autonomous Failure**: Multiple redundant safety systems and manual override
- **Sensor Failure**: Graceful degradation and emergency landing modes
- **Communication Loss**: Autonomous operation with conservative flight envelope
- **Aircraft Damage**: Progressive testing from simple to complex maneuvers

### Operational Risks
- **Weather Conditions**: Defined operational limits and pre-flight checks
- **Airspace Compliance**: AMA safety code compliance and FHSS radio systems
- **Flight Testing**: Staged approach with increasing complexity and safety observers

## Future Enhancements

### Advanced Navigation
- **Wind Estimation**: Airspeed vector and wind compensation
- **Waypoint Navigation**: Multi-point flight patterns beyond simple orbits
- **Terrain Following**: Altitude control based on ground elevation
- **INS Integration**: Dead reckoning during GPS outages

### Enhanced Control
- **Adaptive Control**: Self-tuning control gains based on flight performance
- **Energy Management**: Optimal altitude and speed control for flight duration
- **Formation Flight**: Multiple aircraft coordination
- **Precision Landing**: Automated approach and landing capability

### Mission Capabilities
- **Payload Integration**: Camera gimbal and sensor package support
- **Data Collection**: Autonomous mapping and surveillance missions
- **Search Patterns**: Systematic area coverage algorithms
- **Return-to-Home**: Automatic navigation back to launch point

This specification provides a comprehensive framework for developing the GpsAutopilot system, building upon proven autopilot algorithms while adapting them for Arduino hardware constraints and free-flight model aircraft applications.