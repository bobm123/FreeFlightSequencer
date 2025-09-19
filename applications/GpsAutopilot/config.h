/*
 * config.h - GpsAutopilot Configuration Parameters
 *
 * Configuration structures and default parameters for the GpsAutopilot system.
 * Based on FreeFlight autopilot parameter organization.
 *
 * Hardware Limitations:
 * - QtPY SAMD21 + SignalDistribution MkII
 * - No IMU hardware available
 * - GPS-only navigation
 * - No real-time telemetry hardware
 */

#ifndef CONFIG_H
#define CONFIG_H

// Navigation parameters structure
typedef struct {
    float Ktrack;         // Track update gain from GPS (0.5-2.0)
    float Vias_nom;       // Nominal airspeed (m/s) (8.0-15.0)
    float GpsFilterTau;   // GPS position filter time constant (s) (1.0-5.0)
    uint32_t GpsUpdateHz; // GPS update rate (1-10)
} NavigationParams_t;

// Control parameters structure
typedef struct {
    float Kp_orbit;       // Orbit proportional gain (rad/m) (0.01-0.1)
    float Kp_trk;         // Track proportional gain (0.5-2.0)
    float Ki_trk;         // Track integral gain (0.1-0.5)
    float Kp_roll;        // Roll proportional gain (0.5-2.0)
    float Ki_roll;        // Roll integral gain (0.1-0.5)
    float OrbitRadius;    // Desired orbit radius (m) (50-200)
    float LaunchDelay;    // Manual launch delay (s) (5-30)
    float SafetyRadius;   // Maximum safe distance (m) (150-300)
} ControlParams_t;

// Actuator parameters structure
typedef struct {
    // Roll servo configuration
    float RollServoCenter;     // Center position (us) (1400-1600)
    float RollServoRange;      // Total range (us) (300-600)
    float RollServoRate;       // Maximum servo rate (deg/s) (60-180)
    bool RollServoReversed;    // Direction: false=Normal, true=Inverted
    float RollServoMinPulse;   // Minimum pulse width (us) (800-1200)
    float RollServoMaxPulse;   // Maximum pulse width (us) (1800-2200)
    float RollServoDeadband;   // Center deadband (us) (5-20)

    // Motor configuration
    float MotorMin;            // Minimum motor speed (%) (0-20)
    float MotorMax;            // Maximum motor speed (%) (80-100)
    uint32_t nMotorType;       // Motor type: 0=DC, 1=ESC

    // GPS Failsafe settings
    float FailsafeRollCommand; // Roll command when GPS lost (-1.0 to +1.0)
    float FailsafeMotorCommand; // Motor command when GPS lost (0.0 to 1.0)
    uint32_t GpsTimeoutMs;     // GPS timeout before failsafe (ms) (5000-30000)
    bool FailsafeCircleLeft;   // Circle direction: true=Left, false=Right
} ActuatorParams_t;

// Navigation state structure
typedef struct {
    // Position relative to datum (meters)
    float north;          // North displacement from datum
    float east;           // East displacement from datum
    float altitude;       // Altitude above datum

    // GPS-derived motion
    float groundSpeed;    // Ground speed (m/s)
    float groundTrack;    // Ground track angle (radians)
    float heading;        // Current heading (radians)

    // Datum information
    double datumLat;      // Datum latitude (degrees)
    double datumLon;      // Datum longitude (degrees)
    float datumAlt;       // Datum altitude (meters)

    // Range and bearing to datum
    float rangeFromDatum; // Distance from datum (meters)
    float bearingToDatum; // Bearing to datum (radians)

    // Status flags
    bool gpsValid;        // GPS fix status
    bool datumSet;        // Datum captured status
    uint32_t lastGpsUpdate; // Last GPS update time (ms)
} NavigationState_t;

// Control state structure
typedef struct {
    // Control commands
    float rollCommand;    // Roll command (-1.0 to +1.0)
    float motorCommand;   // Motor command (0.0 to 1.0)

    // Control errors
    float rangeError;     // Distance error from desired orbit
    float trackError;     // Track angle error
    float rollError;      // Roll angle error

    // Integral terms
    float trackIntegral;  // Track error integral
    float rollIntegral;   // Roll error integral

    // Desired values
    float desiredTrack;   // Desired ground track angle
    float desiredRange;   // Desired range from datum

    // Control loop status
    bool autonomousMode;  // Autonomous control active
    uint32_t lastUpdate; // Last control update time (ms)
} ControlState_t;

// System constants (only define if not already defined by Arduino core)
#ifndef PI
#define PI 3.14159265358979323846
#endif
#ifndef RAD_TO_DEG
#define RAD_TO_DEG (180.0 / PI)
#endif
#ifndef DEG_TO_RAD
#define DEG_TO_RAD (PI / 180.0)
#endif

// Earth constants for GPS calculations
#define EARTH_RADIUS_M 6371000.0  // Earth radius in meters
#define METERS_PER_DEGREE_LAT 111320.0  // Approximate meters per degree latitude

// Control loop timing
#define CONTROL_LOOP_HZ 50        // 50Hz control loop
#define CONTROL_LOOP_DT (1.0/CONTROL_LOOP_HZ)

// GPS timeout and validation
#define GPS_TIMEOUT_MS 5000       // GPS timeout (5 seconds)
#define GPS_MIN_SATELLITES 4      // Minimum satellites for valid fix
#define GPS_MAX_HDOP 3.0         // Maximum horizontal dilution of precision

// Safety limits
#define MAX_ROLL_COMMAND 1.0      // Maximum roll command
#define MAX_MOTOR_COMMAND 1.0     // Maximum motor command
#define MIN_ALTITUDE_AGL 10.0     // Minimum altitude above ground level (m)
#define MAX_ALTITUDE_AGL 200.0    // Maximum altitude above ground level (m)

// Servo limits (microseconds)
#define SERVO_MIN_PULSE 1000      // Minimum servo pulse width
#define SERVO_MAX_PULSE 2000      // Maximum servo pulse width
#define SERVO_CENTER_PULSE 1500   // Center servo pulse width

// Motor limits (microseconds for ESC)
#define MOTOR_MIN_PULSE 1000      // Motor idle pulse width
#define MOTOR_MAX_PULSE 2000      // Motor full power pulse width

// Parameter validation macros
#define VALIDATE_RANGE(val, min, max) ((val) < (min) ? (min) : ((val) > (max) ? (max) : (val)))

// Debug and logging options
//#define DEBUG_NAVIGATION        // Enable navigation debug output
//#define DEBUG_CONTROL           // Enable control debug output
//#define DEBUG_GPS               // Enable GPS debug output
//#define LOG_FLIGHT_DATA         // Enable flight data logging

#endif // CONFIG_H