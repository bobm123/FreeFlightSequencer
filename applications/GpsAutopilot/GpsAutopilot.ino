/*
 * GpsAutopilot.ino - GPS-Guided Autonomous Flight Controller
 *
 * GPS-based autonomous flight control system for free-flight model aircraft.
 * Maintains aircraft within 100m circular flight pattern around launch point.
 * Adapted from FreeFlight autopilot for QtPY SAMD21 with Signal Distribution MkII.
 *
 * Hardware Requirements:
 * - Adafruit QT Py SAMD21 microcontroller
 * - Signal Distribution MkII carrier board
 * - GPS module connected to UART (TX/RX pins)
 * - Motor ESC connected to ESC0 (pin A2)
 * - Roll control servo connected to CH1 (pin A3)
 * - Push button (onboard tactile switch on A0)
 * - NeoPixel LED (onboard on pin 11)
 *
 * Flight Sequence:
 * 1. Ready: GPS acquisition, heartbeat LED, wait for button press
 * 2. Armed: GPS datum captured, fast LED flash, release button to start
 * 3. Motor Spool: LED on, ramp motor to speed, launch within 3 seconds
 * 4. GPS Guided Flight: LED slow blink, autonomous circular flight pattern
 * 5. Emergency: Safety override, motor cutoff, return to manual control
 * 6. Landing: Slow blink, hold button 3+ seconds to reset
 *
 * Hardware Limitations:
 * - No IMU: Launch detection and attitude estimation not available
 * - No telemetry hardware: Real-time data transmission requires future hardware
 * - GPS-only navigation: Position and heading from GPS data only
 *
 * Original FreeFlight Authors: Professional autopilot reference implementation
 * QtPY Port: GPS-guided adaptation for Arduino platform
 */

#include <Arduino.h>
#include <Servo.h>
#include <Adafruit_NeoPixel.h>
#include <FlashStorage.h>

// Include autopilot libraries
#include "config.h"
#include "navigation.h"
#include "control.h"
#include "communications.h"
#include "math_utils.h"
#include "hardware_hal.h"

// Hardware pin definitions (QtPY SAMD21 via Signal Distribution MkII)
const int ROLL_SERVO_PIN = A3;       // Roll control servo (CH1 connector)
const int MOTOR_SERVO_PIN = A2;      // Motor ESC (ESC0 connector)
const int BUTTON_PIN = A0;           // Push button (onboard switch)
const int NEOPIXEL_PIN = 11;         // NeoPixel LED (onboard)
const int GPS_RX_PIN = 0;            // GPS TX -> QtPY RX
const int GPS_TX_PIN = 1;            // GPS RX <- QtPY TX

// Flight state enumeration (following FlightSequencer pattern)
enum FlightState {
  STATE_READY = 1,              // GPS acquisition, waiting for user
  STATE_ARMED = 2,              // Datum captured, ready for launch
  STATE_MOTOR_SPOOL = 3,        // Motor ramp-up, launch within 3 seconds
  STATE_GPS_GUIDED_FLIGHT = 4,  // Autonomous GPS-guided flight
  STATE_EMERGENCY = 98,         // Safety override mode
  STATE_LANDING = 99            // Flight complete, reset available
};

// Hardware objects
Servo rollServo;
Servo motorServo;
Adafruit_NeoPixel pixel(1, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);
// GPS uses hardware Serial1 (TX/RX pins on QtPY SAMD21)

// Flight parameters structure for FlashStorage
struct FlightParameters {
  NavigationParams_t nav;
  ControlParams_t control;
  ActuatorParams_t actuator;
  bool valid;  // Flag to check if parameters are initialized
};

// Default parameters
const FlightParameters DEFAULT_PARAMS = {
  // Navigation parameters
  {
    0.8,      // Ktrack - Track update gain from GPS (0.5-2.0)
    12.0,     // Vias_nom - Nominal airspeed (m/s) (8.0-15.0)
    2.0,      // GpsFilterTau - GPS position filter time constant (s) (1.0-5.0)
    5         // GpsUpdateHz - GPS update rate (1-10)
  },
  // Control parameters
  {
    0.05,     // Kp_orbit - Orbit proportional gain (rad/m) (0.01-0.1)
    1.0,      // Kp_trk - Track proportional gain (0.5-2.0)
    0.2,      // Ki_trk - Track integral gain (0.1-0.5)
    1.0,      // Kp_roll - Roll proportional gain (0.5-2.0)
    0.2,      // Ki_roll - Roll integral gain (0.1-0.5)
    100.0,    // OrbitRadius - Desired orbit radius (m) (50-200)
    5.0,      // LaunchDelay - Manual launch delay (s) (5-30)
    200.0     // SafetyRadius - Maximum safe distance (m) (150-300)
  },
  // Actuator parameters
  {
    1500.0,   // RollServoCenter - Center position (us) (1400-1600)
    400.0,    // RollServoRange - Total range (us) (300-600)
    90.0,     // RollServoRate - Maximum servo rate (deg/s) (60-180)
    false,    // RollServoReversed - Direction: false=Normal, true=Inverted
    1000.0,   // RollServoMinPulse - Minimum pulse width (us) (800-1200)
    2000.0,   // RollServoMaxPulse - Maximum pulse width (us) (1800-2200)
    10.0,     // RollServoDeadband - Center deadband (us) (5-20)
    10.0,     // MotorMin - Minimum motor speed (%) (0-20)
    80.0,     // MotorMax - Maximum motor speed (%) (80-100)
    1,        // nMotorType - Motor type: 0=DC, 1=ESC
    0.3,      // FailsafeRollCommand - Gentle left turn when GPS lost
    0.6,      // FailsafeMotorCommand - 60% power during failsafe
    10000,    // GpsTimeoutMs - 10 second GPS timeout
    true      // FailsafeCircleLeft - Circle left during GPS loss
  },
  true        // valid flag
};

// Current flight parameters (loaded from FlashStorage or defaults)
FlightParameters currentParams;

// FlashStorage instance
FlashStorage(flash_store, FlightParameters);

// Flight controller state
FlightState flightState = STATE_READY;
unsigned long stateStartTime = 0;
unsigned long flightStartTime = 0;

// Navigation state
NavigationState_t navState;
bool gpsValid = false;
bool datumSet = false;

// Control state
ControlState_t controlState;

// Button state management (from FlightSequencer)
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;
bool lastButtonState = HIGH;
unsigned long buttonPressStartTime = 0;
bool buttonCurrentlyPressed = false;
bool buttonJustPressed = false;
bool buttonJustReleased = false;
bool longPressDetected = false;
const unsigned long LONG_PRESS_TIME = 1500; // 1.5 seconds for long press

// Prevent immediate launch after arming
unsigned long armTime = 0;
const unsigned long ARM_DELAY = 500; // 500ms delay before launch is possible

// LED pattern types (standardized from FlightSequencer)
enum LedPattern {
  LED_OFF,
  LED_SOLID_RED,
  LED_HEARTBEAT,
  LED_FAST_FLASH,
  LED_SLOW_BLINK,
  LED_EMERGENCY_FLASH,
  LED_LANDING_BLINK,
  LED_GPS_SEARCHING
};

// GPS data flash management
static unsigned long lastGpsFlash = 0;
static bool gpsFlashActive = false;
static uint8_t currentRed = 0, currentGreen = 0, currentBlue = 0;

// Function prototypes
void initializeSystem();
void updateButtonState();
void updateLED(LedPattern pattern, unsigned long currentTime);
void triggerGpsDataFlash();
void updateGpsDataFlash(unsigned long currentTime);
void reportGpsStatus();
FlightState executeReadyState(FlightState currentState);
FlightState executeArmedState(FlightState currentState);
FlightState executeMotorSpoolState(FlightState currentState);
FlightState executeGpsGuidedFlightState(FlightState currentState);
FlightState executeEmergencyState(FlightState currentState);
FlightState executeLandingState(FlightState currentState);
void processSerialCommand();
void loadParameters();
void saveParameters();
void showParameters();
void showHelp();
void printTimestampedInfo(const __FlashStringHelper* message);

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial && millis() < 3000) {
    ; // Wait up to 3 seconds for serial connection
  }

  Serial.println(F("[INFO] GpsAutopilot starting..."));
  Serial.println(F("[INFO] GPS-guided autonomous flight controller"));

  // Load parameters from FlashStorage
  loadParameters();

  // Initialize flight timing
  flightStartTime = millis();
  stateStartTime = millis();

  // Initialize hardware
  initializeSystem();

  // Initialize autopilot libraries
  Nav_Init(&currentParams.nav);
  Control_Init(&currentParams.control);
  Coms_Init();

  // Show current parameters
  showParameters();
  Serial.println(F("[INFO] System ready - GPS acquiring, press button when ready"));
  Serial.println(F("[INFO] Send '?' for parameter commands"));
}

void loop() {
  unsigned long currentTime = millis();
  float deltaTime = (currentTime - stateStartTime) / 1000.0;

  // Process serial commands (only when not in active flight)
  if (flightState == STATE_READY || flightState == STATE_LANDING) {
    processSerialCommand();
  }

  // Update button state with press/release detection
  updateButtonState();

  // Update GPS data
  if (Serial1.available()) {
    // Process incoming GPS data
    bool dataProcessed = Nav_UpdateGPS(&navState);
    if (dataProcessed) {
      triggerGpsDataFlash(); // Blue flash when GPS data processed
    }
  }

  // Validate GPS status (should be called regularly, not just when data arrives)
  bool wasValid = gpsValid;
  gpsValid = Nav_Step(&navState, deltaTime);

  // Debug GPS state changes
  if (gpsValid != wasValid) {
    if (gpsValid) {
      Serial.println(F("[DEBUG] GPS became valid"));
    } else {
      Serial.println(F("[DEBUG] GPS became invalid"));
    }
  }

  // Update GPS data flash overlay
  updateGpsDataFlash(currentTime);

  // Execute current flight state
  switch (flightState) {
    case STATE_READY:
      flightState = executeReadyState(flightState);
      break;

    case STATE_ARMED:
      flightState = executeArmedState(flightState);
      break;

    case STATE_MOTOR_SPOOL:
      flightState = executeMotorSpoolState(flightState);
      break;

    case STATE_GPS_GUIDED_FLIGHT:
      flightState = executeGpsGuidedFlightState(flightState);
      break;

    case STATE_EMERGENCY:
      flightState = executeEmergencyState(flightState);
      break;

    case STATE_LANDING:
    default:
      flightState = executeLandingState(flightState);
      break;
  }

  // Update state timing
  if (flightState != STATE_READY) {
    stateStartTime = currentTime;
  }

  // Update communications
  Coms_Step();

  // Periodic GPS status reporting for GUI
  static unsigned long lastGpsReport = 0;
  if (currentTime - lastGpsReport > 2000) { // Every 2 seconds
    reportGpsStatus();
    lastGpsReport = currentTime;
  }

  // Small delay for system stability
  delay(20); // 50Hz main loop
}

void initializeSystem() {
  // Initialize NeoPixel
  pixel.begin();
  pixel.clear();
  pixel.show();

  // Initialize button
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // Allow button pin to stabilize
  delay(100);

  // Initialize button state
  lastButtonState = digitalRead(BUTTON_PIN);
  lastDebounceTime = millis();

  // Initialize servos
  rollServo.attach(ROLL_SERVO_PIN);
  motorServo.attach(MOTOR_SERVO_PIN);

  // Set servos to safe initial positions
  rollServo.writeMicroseconds(currentParams.actuator.RollServoCenter);  // Roll neutral
  motorServo.writeMicroseconds(1000);  // Motor idle

  // Initialize GPS
  Serial1.begin(9600);

  // Initialize hardware abstraction layer
  HAL_Init();

  Serial.println(F("[OK] Hardware initialized"));
}

FlightState executeReadyState(FlightState currentState) {
  unsigned long currentTime = millis();

  // Enhanced GPS status LED logic
  if (gpsValid && datumSet) {
    updateLED(LED_HEARTBEAT, currentTime);     // GPS ready - heartbeat
  } else if (gpsValid) {
    updateLED(LED_FAST_FLASH, currentTime);    // GPS fix but no datum - fast flash
  } else {
    updateLED(LED_GPS_SEARCHING, currentTime); // No GPS fix - orange searching pattern
  }

  // Check GPS status (with rate limiting to avoid spam)
  if (gpsValid && !datumSet) {
    static unsigned long lastGpsMessage = 0;
    if (currentTime - lastGpsMessage > 5000) {  // Only print every 5 seconds
      Serial.println(F("[INFO] GPS acquired - ready for datum capture"));
      lastGpsMessage = currentTime;
    }
  }

  // Check for arming (requires long press and GPS valid)
  if (longPressDetected && gpsValid) {
    // Capture GPS datum
    Nav_SetDatum(&navState);
    datumSet = true;
    armTime = millis();
    longPressDetected = false; // Clear the flag
    printTimestampedInfo(F("System ARMED - GPS datum captured, short press to launch"));

    // Clear button flags after processing
    buttonJustPressed = false;
    buttonJustReleased = false;
    return STATE_ARMED;
  } else if (longPressDetected && !gpsValid) {
    Serial.println(F("[WARN] Cannot arm - GPS not valid"));
    longPressDetected = false;
  }

  // Clear button flags after processing
  buttonJustPressed = false;
  buttonJustReleased = false;

  return currentState; // Stay in Ready State
}

FlightState executeArmedState(FlightState currentState) {
  unsigned long currentTime = millis();

  // Fast LED flash
  updateLED(LED_FAST_FLASH, currentTime);

  // Check for launch (short press, with delay after arming)
  if (buttonJustReleased && (millis() - armTime > ARM_DELAY)) {
    stateStartTime = millis();
    printTimestampedInfo(F("LAUNCH! Motor spooling - launch within 3 seconds"));

    // Clear ALL button flags to prevent interference with next state
    buttonJustPressed = false;
    buttonJustReleased = false;
    longPressDetected = false;

    return STATE_MOTOR_SPOOL;
  }

  // Reset button flags after processing
  buttonJustPressed = false;
  buttonJustReleased = false;

  return currentState; // Stay in Armed State
}

FlightState executeMotorSpoolState(FlightState currentState) {
  unsigned long currentTime = millis();
  unsigned long elapsed = currentTime - stateStartTime;

  // LED on during spool
  updateLED(LED_SOLID_RED, currentTime);

  // Check for emergency shutoff during spool
  if (buttonJustPressed) {
    motorServo.writeMicroseconds(1000);
    Serial.println(F("[WARN] Emergency motor shutoff during spool!"));
    buttonJustPressed = false;
    return STATE_EMERGENCY;
  }

  // Ramp motor to flight speed over 3 seconds
  float motorSpeed = currentParams.actuator.MotorMin +
                    (currentParams.actuator.MotorMax - currentParams.actuator.MotorMin) *
                    min(elapsed / 3000.0, 1.0);

  int motorPWM = 1000 + (motorSpeed / 100.0) * 1000;
  motorServo.writeMicroseconds(motorPWM);

  // Transition to GPS guided flight after 3 seconds
  if (elapsed >= 3000) {
    printTimestampedInfo(F("Motor at flight speed - GPS guided flight engaged"));
    return STATE_GPS_GUIDED_FLIGHT;
  }

  return currentState; // Stay in Motor Spool State
}

FlightState executeGpsGuidedFlightState(FlightState currentState) {
  unsigned long currentTime = millis();

  // Slow LED blink during autonomous flight
  updateLED(LED_SLOW_BLINK, currentTime);

  // Check for emergency cutoff
  if (buttonJustPressed) {
    motorServo.writeMicroseconds(1000);
    Serial.println(F("[WARN] Emergency cutoff - returning to manual control"));
    buttonJustPressed = false;
    return STATE_EMERGENCY;
  }

  // Update navigation state
  if (gpsValid) {
    Nav_Step(&navState, 0.02); // 50Hz update

    // Update control system
    Control_Step(&navState, &controlState, 0.02);

    // Apply control outputs
    float rollCommand = controlState.rollCommand;
    float motorCommand = controlState.motorCommand;

    // Convert roll command to servo position
    int rollPWM = currentParams.actuator.RollServoCenter +
                  rollCommand * currentParams.actuator.RollServoRange / 2.0;
    rollPWM = constrain(rollPWM,
                       currentParams.actuator.RollServoCenter - currentParams.actuator.RollServoRange/2,
                       currentParams.actuator.RollServoCenter + currentParams.actuator.RollServoRange/2);

    // Convert motor command to ESC signal
    int motorPWM = 1000 + motorCommand * 1000;
    motorPWM = constrain(motorPWM, 1000, 2000);

    // Apply commands
    rollServo.writeMicroseconds(rollPWM);
    motorServo.writeMicroseconds(motorPWM);

    // Check safety limits
    if (navState.rangeFromDatum > currentParams.control.SafetyRadius) {
      Serial.println(F("[WARN] Safety radius exceeded - emergency mode"));
      return STATE_EMERGENCY;
    }
  } else {
    // GPS lost - enter failsafe mode
    static unsigned long gpsLossTime = 0;
    if (gpsLossTime == 0) {
      gpsLossTime = millis();
      Serial.println(F("[WARN] GPS signal lost - entering failsafe mode"));
    }

    // Apply failsafe commands (gentle turn + reduced power)
    float failsafeRoll = currentParams.actuator.FailsafeRollCommand;
    if (!currentParams.actuator.FailsafeCircleLeft) {
      failsafeRoll = -failsafeRoll; // Reverse for right turn
    }

    // Convert failsafe roll command to servo position
    int rollPWM = currentParams.actuator.RollServoCenter +
                  failsafeRoll * currentParams.actuator.RollServoRange / 2.0;
    rollPWM = constrain(rollPWM,
                       currentParams.actuator.RollServoCenter - currentParams.actuator.RollServoRange/2,
                       currentParams.actuator.RollServoCenter + currentParams.actuator.RollServoRange/2);

    // Convert failsafe motor command to ESC signal
    int motorPWM = 1000 + currentParams.actuator.FailsafeMotorCommand * 1000;
    motorPWM = constrain(motorPWM, 1000, 2000);

    // Apply failsafe commands
    rollServo.writeMicroseconds(rollPWM);
    motorServo.writeMicroseconds(motorPWM);

    // Check GPS timeout - go to emergency if GPS lost too long
    if (millis() - gpsLossTime > currentParams.actuator.GpsTimeoutMs) {
      Serial.println(F("[WARN] GPS timeout exceeded - emergency mode"));
      gpsLossTime = 0; // Reset for next time
      return STATE_EMERGENCY;
    }

    // Reset GPS loss timer when GPS comes back
    if (gpsValid) {
      gpsLossTime = 0;
      Serial.println(F("[INFO] GPS signal recovered"));
    }
  }

  return currentState; // Stay in GPS Guided Flight State
}

FlightState executeEmergencyState(FlightState currentState) {
  unsigned long currentTime = millis();

  // Emergency LED flash pattern
  updateLED(LED_EMERGENCY_FLASH, currentTime);

  // Ensure safe servo positions
  motorServo.writeMicroseconds(1000);  // Motor idle
  rollServo.writeMicroseconds(currentParams.actuator.RollServoCenter);  // Roll neutral

  // Reset logic - long press to go to landing
  if (longPressDetected) {
    printTimestampedInfo(F("Emergency reset - entering landing state"));
    longPressDetected = false;
    return STATE_LANDING;
  }

  return currentState; // Stay in Emergency State
}

FlightState executeLandingState(FlightState currentState) {
  unsigned long currentTime = millis();

  // Landing blink pattern
  updateLED(LED_LANDING_BLINK, currentTime);

  // Ensure safe servo positions
  motorServo.writeMicroseconds(1000);  // Motor idle
  rollServo.writeMicroseconds(currentParams.actuator.RollServoCenter);  // Roll neutral

  // Reset logic - long press to reset
  if (longPressDetected) {
    printTimestampedInfo(F("System RESET - ready for new flight"));
    longPressDetected = false;
    flightStartTime = millis();
    datumSet = false;  // Clear datum for new flight
    return STATE_READY;
  }

  return currentState; // Stay in Landing State
}

// Button handling code (copied from FlightSequencer)
void updateButtonState() {
  bool currentState = digitalRead(BUTTON_PIN);

  // Debounce button state
  static bool lastStableState = HIGH;
  static unsigned long lastChangeTime = 0;

  if (currentState != lastStableState) {
    if (millis() - lastChangeTime > DEBOUNCE_DELAY) {
      lastStableState = currentState;
      lastChangeTime = millis();
    }
  }

  // Update button state flags
  bool currentlyPressed = (lastStableState == LOW); // Active low button

  // Detect press events
  if (currentlyPressed && !buttonCurrentlyPressed) {
    // Button just pressed
    buttonJustPressed = true;
    buttonPressStartTime = millis();
    Serial.println(F("[BUTTON] Button pressed"));
  }

  // Detect release events
  if (!currentlyPressed && buttonCurrentlyPressed) {
    // Button just released
    buttonJustReleased = true;
    unsigned long pressDuration = millis() - buttonPressStartTime;

    Serial.print(F("[BUTTON] Button released after "));
    Serial.print(pressDuration);
    Serial.println(F(" ms"));

    // Check if it was a long press
    if (pressDuration >= LONG_PRESS_TIME) {
      longPressDetected = true;
      Serial.println(F("[BUTTON] Long press detected"));
    } else {
      Serial.println(F("[BUTTON] Short press detected"));
    }
  }

  buttonCurrentlyPressed = currentlyPressed;
}

// LED handling code (copied from FlightSequencer)
void updateLED(LedPattern pattern, unsigned long currentTime) {
  static unsigned long lastChange = 0;
  static int step = 0;
  static bool ledState = false;

  switch (pattern) {
    case LED_OFF:
      setLEDColor(0, 0, 0);
      break;

    case LED_SOLID_RED:
      setLEDColor(255, 0, 0);
      break;

    case LED_HEARTBEAT: {
      // Double blink pattern: on(50ms) - off(100ms) - on(50ms) - off(850ms)
      switch (step) {
        case 0:
          if (currentTime - lastChange >= 0) {
            setLEDColor(255, 0, 0);
                lastChange = currentTime;
            step = 1;
          }
          break;
        case 1:
          if (currentTime - lastChange >= 50) {
            setLEDColor(0, 0, 0);
                lastChange = currentTime;
            step = 2;
          }
          break;
        case 2:
          if (currentTime - lastChange >= 100) {
            setLEDColor(255, 0, 0);
                lastChange = currentTime;
            step = 3;
          }
          break;
        case 3:
          if (currentTime - lastChange >= 50) {
            setLEDColor(0, 0, 0);
                lastChange = currentTime;
            step = 4;
          }
          break;
        case 4:
          if (currentTime - lastChange >= 850) {
            step = 0;
          }
          break;
      }
      break;
    }

    case LED_FAST_FLASH:
      // 100ms on/off cycle
      if (currentTime - lastChange >= 100) {
        if (ledState) {
          setLEDColor(0, 0, 0);
        } else {
          setLEDColor(255, 0, 0);
        }
        ledState = !ledState;
        lastChange = currentTime;
      }
      break;

    case LED_SLOW_BLINK:
      // 500ms on/off cycle
      if (currentTime - lastChange >= 500) {
        if (ledState) {
          setLEDColor(0, 0, 0);
        } else {
          setLEDColor(255, 0, 0);
        }
        ledState = !ledState;
        lastChange = currentTime;
      }
      break;

    case LED_EMERGENCY_FLASH:
      // Very fast 200ms on/off cycle for emergency
      if (currentTime - lastChange >= 200) {
        if (ledState) {
          setLEDColor(0, 0, 0);
        } else {
          setLEDColor(255, 0, 0);
        }
        ledState = !ledState;
        lastChange = currentTime;
      }
      break;

    case LED_GPS_SEARCHING:
      // Orange/yellow color with 750ms on/off cycle for GPS searching
      if (currentTime - lastChange >= 750) {
        if (ledState) {
          setLEDColor(0, 0, 0);
        } else {
          setLEDColor(255, 165, 0); // Orange color
        }
        ledState = !ledState;
        lastChange = currentTime;
      }
      break;

    case LED_LANDING_BLINK:
      // 50ms on, 2950ms off cycle
      if (!ledState && currentTime - lastChange >= 50) {
        setLEDColor(255, 0, 0);
        ledState = true;
        lastChange = currentTime;
      } else if (ledState && currentTime - lastChange >= 2950) {
        setLEDColor(0, 0, 0);
        ledState = false;
        lastChange = currentTime;
      }
      break;
  }
}

// GPS data flash functions for dual LED operation
void triggerGpsDataFlash() {
  lastGpsFlash = millis();
  gpsFlashActive = true;
}

void updateGpsDataFlash(unsigned long currentTime) {
  // Blue flash duration: 50ms on, then off
  if (gpsFlashActive) {
    if (currentTime - lastGpsFlash < 50) {
      // Add blue component to current LED color
      pixel.setPixelColor(0, pixel.Color(currentRed, currentGreen, currentBlue + 150));
      pixel.show();
    } else {
      // Flash ended, restore original color
      gpsFlashActive = false;
      pixel.setPixelColor(0, pixel.Color(currentRed, currentGreen, currentBlue));
      pixel.show();
    }
  }
}

// Helper function to set LED color and store current values
void setLEDColor(uint8_t red, uint8_t green, uint8_t blue) {
  currentRed = red;
  currentGreen = green;
  currentBlue = blue;

  // Apply GPS flash overlay if active
  uint8_t finalBlue = blue;
  if (gpsFlashActive && (millis() - lastGpsFlash < 50)) {
    finalBlue = min(255, blue + 150);
  }

  pixel.setPixelColor(0, pixel.Color(red, green, finalBlue));
  pixel.show();
}

// GPS status reporting for GUI parsing
void reportGpsStatus() {
  if (gpsValid) {
    // Report GPS fix status in format GUI expects
    Serial.print(F("Fix Status: [OK] 3D Fix, Satellites: "));
    Serial.print(5); // Placeholder - could get actual satellite count from navState
    Serial.println(F(" tracked"));

    // Report position - absolute coordinates before datum, relative after
    if (datumSet) {
      // Show relative position after datum is set
      Serial.print(F("Position: N="));
      Serial.print(navState.north, 1);
      Serial.print(F(" E="));
      Serial.print(navState.east, 1);
      Serial.print(F(" U="));
      Serial.print(navState.altitude, 1);
      Serial.println();

      Serial.print(F("Range: "));
      Serial.print(navState.rangeFromDatum, 1);
      Serial.print(F("m, Bearing: "));
      Serial.print(navState.bearingToDatum * 180.0 / PI, 0);
      Serial.println(F("deg"));
    } else {
      // Show absolute GPS coordinates before datum is set
      Serial.print(F("Position: "));
      Serial.print(navState.datumLat, 6);
      Serial.print(F("deg, "));
      Serial.print(navState.datumLon, 6);
      Serial.print(F("deg, Alt: "));
      Serial.print(navState.altitude, 1);
      Serial.println(F("m"));
    }

    // Report flight mode and navigation mode
    Serial.print(F("Flight Mode: "));
    switch(flightState) {
      case STATE_READY: Serial.println(F("READY")); break;
      case STATE_ARMED: Serial.println(F("ARMED")); break;
      case STATE_MOTOR_SPOOL: Serial.println(F("MOTOR_SPOOL")); break;
      case STATE_GPS_GUIDED_FLIGHT: Serial.println(F("AUTONOMOUS")); break;
      case STATE_EMERGENCY: Serial.println(F("EMERGENCY")); break;
      case STATE_LANDING: Serial.println(F("LANDING")); break;
      default: Serial.println(F("UNKNOWN")); break;
    }

    Serial.print(F("Nav Mode: "));
    if (datumSet) {
      Serial.println(F("GPS_ORBIT"));
    } else {
      Serial.println(F("GPS_ACQUIRE"));
    }
  } else {
    Serial.println(F("GPS: No Fix"));
  }
}

// Serial command processing (simplified from FlightSequencer)
void processSerialCommand() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();

  if (command.length() == 0) {
    return;
  }

  char cmd = command.charAt(0);

  switch (cmd) {
    case 'G': {
      // Get parameters
      showParameters();
      break;
    }

    case 'R': {
      // Reset to defaults
      currentParams = DEFAULT_PARAMS;
      saveParameters();
      Serial.println(F("[OK] Parameters reset to defaults"));
      showParameters();
      break;
    }

    case '?': {
      // Help
      showHelp();
      break;
    }

    default: {
      Serial.print(F("[ERR] Unknown command: "));
      Serial.println(cmd);
      Serial.println(F("[INFO] Send '?' for help"));
      break;
    }
  }
}

void loadParameters() {
  currentParams = flash_store.read();

  // If parameters are not valid or this is first boot, use defaults
  if (!currentParams.valid) {
    Serial.println(F("[INFO] Loading default parameters"));
    currentParams = DEFAULT_PARAMS;
    saveParameters();
  } else {
    Serial.println(F("[INFO] Parameters loaded from flash memory"));
  }
}

void saveParameters() {
  currentParams.valid = true;
  flash_store.write(currentParams);
  Serial.println(F("[OK] Parameters saved to flash memory"));
}

void showParameters() {
  Serial.println(F("[INFO] Current GpsAutopilot Parameters"));
  Serial.print(F("[INFO] Orbit Radius: "));
  Serial.print(currentParams.control.OrbitRadius);
  Serial.println(F(" meters"));
  Serial.print(F("[INFO] Safety Radius: "));
  Serial.print(currentParams.control.SafetyRadius);
  Serial.println(F(" meters"));
  Serial.print(F("[INFO] Nominal Airspeed: "));
  Serial.print(currentParams.nav.Vias_nom);
  Serial.println(F(" m/s"));
  Serial.print(F("[INFO] Servo Center: "));
  Serial.print(currentParams.actuator.RollServoCenter);
  Serial.println(F(" us"));
}

void showHelp() {
  Serial.println(F("[INFO] GpsAutopilot Commands:"));
  Serial.println(F("[INFO] G         - Get current parameters"));
  Serial.println(F("[INFO] R         - Reset to defaults"));
  Serial.println(F("[INFO] ?         - Show this help"));
  Serial.println(F("[INFO] "));
  Serial.println(F("[INFO] Flight Operation:"));
  Serial.println(F("[INFO] 1. Wait for GPS lock (heartbeat LED)"));
  Serial.println(F("[INFO] 2. Long press to arm and capture datum"));
  Serial.println(F("[INFO] 3. Short press to start motor and launch"));
  Serial.println(F("[INFO] 4. Launch aircraft within 3 seconds"));
  Serial.println(F("[INFO] 5. Button press for emergency cutoff"));
}

void printTimestampedInfo(const __FlashStringHelper* message) {
  unsigned long elapsedMs = millis() - flightStartTime;
  unsigned long totalSeconds = elapsedMs / 1000;
  unsigned long minutes = totalSeconds / 60;
  unsigned long seconds = totalSeconds % 60;

  Serial.print(F("[INFO] "));
  if (minutes < 10) Serial.print(F("0"));
  Serial.print(minutes);
  Serial.print(F(":"));
  if (seconds < 10) Serial.print(F("0"));
  Serial.print(seconds);
  Serial.print(F(" "));
  Serial.println(message);
}