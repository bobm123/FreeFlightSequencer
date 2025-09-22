/*
 * FlightSequencer.ino - E36 Flight Timer for QtPY SAMD21
 * 
 * Automated flight control system for electric free-flight model aircraft.
 * Ported from ATTiny85 E36-Timer to QtPY SAMD21 with Signal Distribution MkII.
 * 
 * Hardware Requirements:
 * - Adafruit QT Py SAMD21 microcontroller
 * - Signal Distribution MkII carrier board
 * - Motor ESC with BEC connected to ESC0 (pin A2)
 * - Dethermalizer servo connected to CH1 (pin A3)
 * - Push button (onboard tactile switch on A0)
 * - NeoPixel LED (onboard on pin 11)
 * 
 * Flight Sequence:
 * 1. Ready: Heartbeat LED, wait for button press
 * 2. Armed: Fast LED flash, release button to start
 * 3. Motor Spool: LED on, ramp motor to speed  
 * 4. Motor Run: LED on, motor at speed for 20 seconds
 * 5. Glide: LED slow blink, motor off until 120 seconds total
 * 6. DT Deploy: Deploy dethermalizer servo
 * 7. Landing: Slow blink, hold button 3+ seconds to reset
 * 
 * Original Authors: Stew Meyers (PicAXE), Bob Marchese (ATTiny85)
 * QtPY Port: Phase 2 with serial parameter programming
 */

#include <Arduino.h>
#include <Servo.h>
#include <Adafruit_NeoPixel.h>
#include <FlashStorage.h>

// Hardware pin definitions (QtPY SAMD21 via Signal Distribution MkII)
const int DT_SERVO_PIN = A3;         // Dethermalizer servo (CH1 connector)
const int MOTOR_SERVO_PIN = A2;      // Motor ESC (ESC0 connector)
const int BUTTON_PIN = A0;           // Push button (onboard switch)
const int NEOPIXEL_PIN = 11;         // NeoPixel LED (onboard)

// Servo objects
Servo dtServo;
Servo motorServo;

// NeoPixel LED
Adafruit_NeoPixel pixel(1, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// GPS position recording structure
struct GPSPosition {
  float latitude;
  float longitude;
  unsigned long timestamp;  // Flight time in milliseconds
  int flightState;
  bool valid;
};

// Flight parameter structure for FlashStorage
struct FlightParameters {
  unsigned short motorRunTime;
  unsigned short totalFlightTime;
  unsigned short motorSpeed;
  unsigned short dtRetracted;  // DT retracted position (microseconds)
  unsigned short dtDeployed;   // DT deployed position (microseconds)
  unsigned short dtDwell;      // DT dwell time (seconds)
  bool valid;  // Flag to check if parameters are initialized
};

// Default parameters
const FlightParameters DEFAULT_PARAMS = {
  20,     // Motor run time (seconds)
  120,    // Total flight time (seconds)
  150,    // Motor speed (150 -> 1500us PWM)
  1000,   // DT retracted position (1000us)
  2000,   // DT deployed position (2000us)
  2,      // DT dwell time (2 seconds)
  true    // Valid flag
};

// Current flight parameters (loaded from FlashStorage or defaults)
FlightParameters currentParams;

// GPS tracking variables
bool gpsAvailable = false;
bool gpsInitialized = false;
float currentLat = 0.0;
float currentLon = 0.0;
int gpsQuality = 0;
int satelliteCount = 0;

// Position storage (limited by SAMD21 memory)
// Motor(10s) + Glide(90s) + Post-DT(60s) = 160 positions at 1Hz
const int MAX_GPS_POSITIONS = 180;
GPSPosition flightPath[MAX_GPS_POSITIONS];
int positionCount = 0;
unsigned long lastGPSRecord = 0;
const unsigned long GPS_RECORD_INTERVAL = 1000; // Record GPS every 1 second

// Post-DT GPS recording
unsigned long dtDeployTime = 0;
const unsigned long POST_DT_RECORD_TIME = 60000; // Record for 60 seconds after DT deployment

// FlashStorage instance
FlashStorage(flash_store, FlightParameters);

// Parameter validation ranges
const unsigned short MIN_MOTOR_TIME = 5;
const unsigned short MAX_MOTOR_TIME = 60;
const unsigned short MIN_TOTAL_TIME = 30;
const unsigned short MAX_TOTAL_TIME = 600;
const unsigned short MIN_MOTOR_SPEED = 95;
const unsigned short MAX_MOTOR_SPEED = 200;

// Servo control constants
const int MIN_SPEED = 95;            // 95 -> 950us pulse (motor idle)
const int MAX_SPEED = 200;           // 200 -> 2000us pulse (motor max)
const int DT_RETRACT = 1000;         // 1000us pulse (dethermalizer retracted)
const int DT_DEPLOY = 2000;          // 2000us pulse (dethermalizer deployed)

// Flight timing variables
unsigned long startTime;
unsigned long motorTimeMS;
unsigned long totalFlightTimeMS;
unsigned long flightStartTime;  // Time when flight sequence begins (for timestamp reset)

// Flight controller state
int flightState = 1;                 // Start in Ready state
int resetDelay = 0;
bool buttonPressed = false;

// Button state management
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;
bool lastButtonState = HIGH;

// Button press timing
unsigned long buttonPressStartTime = 0;
bool buttonCurrentlyPressed = false;
bool buttonJustPressed = false;
bool buttonJustReleased = false;
bool longPressDetected = false;
const unsigned long LONG_PRESS_TIME = 1500; // 1.5 seconds for long press

// Prevent immediate launch after arming
unsigned long armTime = 0;
const unsigned long ARM_DELAY = 500; // 500ms delay before launch is possible

// LED pattern types
enum LedPattern {
  LED_OFF,
  LED_SOLID_RED,
  LED_HEARTBEAT,
  LED_FAST_FLASH,
  LED_SLOW_BLINK,
  LED_LANDING_BLINK
};

// Function prototypes
void updateLED(LedPattern pattern, unsigned long currentTime);
void updateButtonState();
void initializeSystem();
void resetStateVariables();
int executeReadyState(int currentState);
int executeArmedState(int currentState);
int executeMotorSpoolState(int currentState);
int executeMotorRunState(int currentState);
int executeGlideState(int currentState);
int executeDTDeployState(int currentState);
int executeLandingState(int currentState);

// GPS function prototypes
void detectGPS();
void processGPSData();
bool parseNMEASentence(String sentence);
void recordPosition();
void clearFlightRecords();
void downloadFlightRecords();
const char* getStateName(int state);

// Serial parameter programming functions
void loadParameters();
void saveParameters();
void resetToDefaults();
bool validateParameters(unsigned short motorTime, unsigned short totalTime, unsigned short motorSpeed,
                       unsigned short dtRetracted, unsigned short dtDeployed, unsigned short dtDwell);
void processSerialCommand();
void showParameters();
void showHelp();

// Timestamp utility function
void printTimestampedInfo(const __FlashStringHelper* message);

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial && millis() < 3000) {
    ; // Wait up to 3 seconds for serial connection
  }
  
  Serial.println(F("[INFO] FlightSequencer starting..."));
  Serial.println(F("[INFO] Phase 2: Serial parameter programming"));
  
  // Load parameters from FlashStorage
  loadParameters();

  // Initialize flight timing
  flightStartTime = millis();

  // Detect and initialize GPS
  detectGPS();

  // Initialize hardware
  initializeSystem();
  
  // Show current parameters
  showParameters();
  Serial.println(F("[INFO] System ready - press button to arm"));
  Serial.println(F("[INFO] Send '?' for parameter commands"));
}

void loop() {
  // Process serial commands (only when not in active flight)
  if (flightState == 1 || flightState == 99) {  // Ready or Landing state
    processSerialCommand();
  }

  // Process GPS data (non-blocking)
  processGPSData();

  // Update button state with press/release detection
  updateButtonState();
  
  // Execute current flight state
  switch (flightState) {
    case 1: // Ready State
      flightState = executeReadyState(flightState);
      break;
      
    case 2: // Armed State  
      flightState = executeArmedState(flightState);
      break;
      
    case 3: // Motor Spool State
      flightState = executeMotorSpoolState(flightState);
      break;
      
    case 4: // Motor Run State
      flightState = executeMotorRunState(flightState);
      break;
      
    case 5: // Glide State
      flightState = executeGlideState(flightState);
      break;
      
    case 6: // DT Deploy State
      flightState = executeDTDeployState(flightState);
      break;
      
    case 99: // Landing State
    default:
      flightState = executeLandingState(flightState);
      break;
  }

  //DEBUG - Show state transitions
  //static int lastReportedState = -1;
  //if (flightState != lastReportedState) {
  //  Serial.print(F("[DEBUG] State transition: "));
  //  Serial.print(lastReportedState);
  //  Serial.print(F(" -> "));
  //  Serial.println(flightState);
  //  lastReportedState = flightState;
  //}
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
  
  // Serial.print(F("[DEBUG] Button pin initial state: "));
  // Serial.println(lastButtonState);
  
  // Initialize servos
  dtServo.attach(DT_SERVO_PIN);
  motorServo.attach(MOTOR_SERVO_PIN);
  
  // Set servos to safe initial positions
  dtServo.writeMicroseconds(currentParams.dtRetracted);  // DT retracted
  motorServo.writeMicroseconds(MIN_SPEED * 10);          // Motor idle
  
  // Calculate flight timing from current parameters
  motorTimeMS = currentParams.motorRunTime * 1000UL;
  totalFlightTimeMS = currentParams.totalFlightTime * 1000UL;
  
  // Parameters will be displayed by showParameters() in setup()
}

int executeReadyState(int currentState) {
  unsigned long currentTime = millis();
  
  // Heartbeat LED pattern
  updateLED(LED_HEARTBEAT, currentTime);
  
  // Check for arming (requires long press)
  if (longPressDetected) {
    armTime = millis();
    longPressDetected = false; // Clear the flag
    printTimestampedInfo(F("System ARMED - short press to launch"));
    
    // Clear button flags after processing
    buttonJustPressed = false;
    buttonJustReleased = false;
    return 2; // Transition to Armed State
  }
  
  // Clear button flags after processing
  buttonJustPressed = false;
  buttonJustReleased = false;
  
  return currentState; // Stay in Ready State
}

int executeArmedState(int currentState) {
  unsigned long currentTime = millis();
  
  // Fast LED flash
  updateLED(LED_FAST_FLASH, currentTime);
  
  // Check for launch (short press, with delay after arming)
  if (buttonJustReleased && (millis() - armTime > ARM_DELAY)) {
    startTime = millis();
    printTimestampedInfo(F("LAUNCH! Motor spooling..."));
    
    // Reset state machine variables for new flight
    resetStateVariables();
    
    // Clear ALL button flags to prevent interference with next state
    buttonJustPressed = false;
    buttonJustReleased = false;
    longPressDetected = false;
    
    return 3; // Transition to Motor Spool State
  }
  
  // Reset button flags after processing
  buttonJustPressed = false;
  buttonJustReleased = false;
  
  return currentState; // Stay in Armed State
}

// State variables that need to be reset between flights
bool spoolComplete = false;
bool spoolStateEntered = false;
bool runStateEntered = false;
bool dtDeployed = false;

void resetStateVariables() {
  // Reset all state-specific variables for new flight
  spoolComplete = false;
  spoolStateEntered = false;
  runStateEntered = false;
  dtDeployed = false;

  // Clear GPS flight path for new flight
  positionCount = 0;
  lastGPSRecord = 0;
  dtDeployTime = 0;

  // Serial.println(F("[DEBUG] State variables reset for new flight"));
}

int executeMotorSpoolState(int currentState) {
  unsigned long currentTime = millis();
  
  // LED on during spool
  updateLED(LED_SOLID_RED, currentTime);
  
  if (!spoolStateEntered) {
    // Serial.println(F("[DEBUG] Entered Motor Spool State"));
    spoolStateEntered = true;
  }
  
  // Check for emergency shutoff during spool
  if (buttonJustPressed) {
    motorServo.writeMicroseconds(MIN_SPEED * 10);
    Serial.println(F("[WARN] Emergency motor shutoff during spool!"));
    buttonJustPressed = false;
    return 99; // Transition to Landing State
  }
  
  if (!spoolComplete) {
    for (int speed = MIN_SPEED; speed <= currentParams.motorSpeed; speed += 5) {
      motorServo.writeMicroseconds(speed * 10);
      delay(50); // Small delay for smooth ramp
    }
    
    // Ensure final speed is set
    motorServo.writeMicroseconds(currentParams.motorSpeed * 10);
    spoolComplete = true;
    
    // Use custom formatting for motor speed message to include PWM value
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
    Serial.print(F(" Motor at flight speed: "));
    Serial.print(currentParams.motorSpeed * 10);
    Serial.println(F("us"));
    
    return 4; // Transition to Motor Run State
  }
  
  return currentState; // Stay in Motor Spool State
}

int executeMotorRunState(int currentState) {
  unsigned long currentTime = millis();
  
  // LED on during motor run
  updateLED(LED_SOLID_RED, currentTime);
  
  // Maintain motor at flight speed
  motorServo.writeMicroseconds(currentParams.motorSpeed * 10);
  
  if (!runStateEntered) {
    // Serial.println(F("[DEBUG] Entered Motor Run State"));
    runStateEntered = true;
  }
  
  unsigned long elapsed = millis() - startTime;
  
  // Check for emergency shutoff (any button press)
  if (buttonJustPressed) {
    motorServo.writeMicroseconds(MIN_SPEED * 10);
    Serial.println(F("[WARN] Emergency motor shutoff!"));
    buttonJustPressed = false; // Clear the flag
    return 99; // Transition to Landing State
  }
  
  // Check for motor run completion
  if (elapsed >= motorTimeMS) {
    motorServo.writeMicroseconds(MIN_SPEED * 10);
    printTimestampedInfo(F("Motor run complete - entering glide phase"));
    return 5; // Transition to Glide State
  }
  
  return currentState; // Stay in Motor Run State
}

int executeGlideState(int currentState) {
  unsigned long currentTime = millis();
  
  // Slow LED blink (1 second cycle)
  updateLED(LED_SLOW_BLINK, currentTime);
  
  // Ensure motor stays idle
  motorServo.writeMicroseconds(MIN_SPEED * 10);
  
  // Check for emergency cutoff during glide (abort flight, no DT deployment)
  if (buttonJustPressed) {
    Serial.println(F("[WARN] Flight aborted during glide phase!"));
    buttonJustPressed = false;
    return 99; // Transition to Landing State
  }
  
  unsigned long elapsed = millis() - startTime;
  
  // Check for total flight time completion
  if (elapsed >= totalFlightTimeMS) {
    printTimestampedInfo(F("Flight time complete - deploying DT"));
    return 6; // Transition to DT Deploy State
  }
  
  return currentState; // Stay in Glide State
}

int executeDTDeployState(int currentState) {
  static unsigned long deployTime = 0;
  unsigned long currentTime = millis();

  // Landing blink pattern (50ms on, 2950ms off)
  updateLED(LED_LANDING_BLINK, currentTime);

  // Ensure motor stays idle
  motorServo.writeMicroseconds(MIN_SPEED * 10);

  // Check for long press to reset
  if (longPressDetected) {
    dtServo.writeMicroseconds(currentParams.dtRetracted); // Retract DT servo
    printTimestampedInfo(F("Manual DT retraction - flight complete"));
    longPressDetected = false; // Clear the flag
    return 99; // Transition to Landing State
  }

  if (!dtDeployed) {
    // Deploy dethermalizer
    dtServo.writeMicroseconds(currentParams.dtDeployed);
    printTimestampedInfo(F("Dethermalizer DEPLOYED"));
    deployTime = millis();
    dtDeployTime = millis(); // Record DT deployment time for GPS tracking
    dtDeployed = true;
  } else if (millis() - deployTime >= (currentParams.dtDwell * 1000UL)) {
    // Hold deployment for configured dwell time, then retract
    dtServo.writeMicroseconds(currentParams.dtRetracted);
    printTimestampedInfo(F("Dethermalizer retracted - flight complete"));
    return 99; // Transition to Landing State
  }

  return currentState; // Stay in DT Deploy State
}

int executeLandingState(int currentState) {
  unsigned long currentTime = millis();
  
  // Landing blink pattern (50ms on, 2950ms off)
  updateLED(LED_LANDING_BLINK, currentTime);
  
  // Ensure safe servo positions
  motorServo.writeMicroseconds(MIN_SPEED * 10);
  dtServo.writeMicroseconds(currentParams.dtRetracted);
  
  // Reset logic - long press to reset
  if (longPressDetected) {
    printTimestampedInfo(F("System RESET - ready for new flight"));
    longPressDetected = false; // Clear the flag
    flightStartTime = millis(); // Reset flight timing for new flight
    return 1; // Transition to Ready State
  }
  
  return currentState; // Stay in Landing State
}

void updateButtonState() {
  bool currentState = digitalRead(BUTTON_PIN);
  
  // Debug output disabled for production
  // static unsigned long lastDebugTime = 0;
  // if (millis() - lastDebugTime > 5000) {
  //   Serial.print(F("[DEBUG] Pin: "));
  //   Serial.print(currentState);
  //   Serial.print(F(", State: "));
  //   Serial.println(flightState);
  //   lastDebugTime = millis();
  // }
  
  // Debounce button state
  static bool lastStableState = HIGH;
  static unsigned long lastChangeTime = 0;
  
  if (currentState != lastStableState) {
    if (millis() - lastChangeTime > DEBOUNCE_DELAY) {
      // Debug output disabled for production
      // Serial.print(F("[DEBUG] Button change detected: "));
      // Serial.print(lastStableState);
      // Serial.print(F(" -> "));
      // Serial.println(currentState);
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
    // Serial.println(F("[DEBUG] Button press started"));
  }
  
  // Detect release events  
  if (!currentlyPressed && buttonCurrentlyPressed) {
    // Button just released
    buttonJustReleased = true;
    unsigned long pressDuration = millis() - buttonPressStartTime;
    
    // Serial.print(F("[DEBUG] Button released after "));
    // Serial.print(pressDuration);
    // Serial.println(F("ms"));
    
    // Check if it was a long press
    if (pressDuration >= LONG_PRESS_TIME) {
      longPressDetected = true;
      // Serial.println(F("[DEBUG] Long press detected"));
    } else {
      // Serial.println(F("[DEBUG] Short press detected"));
    }
  }
  
  buttonCurrentlyPressed = currentlyPressed;
}

void updateLED(LedPattern pattern, unsigned long currentTime) {
  static unsigned long lastChange = 0;
  static int step = 0;
  static bool ledState = false;
  
  switch (pattern) {
    case LED_OFF:
      pixel.setPixelColor(0, pixel.Color(0, 0, 0));   // Off
      pixel.show();
      break;
      
    case LED_SOLID_RED:
      pixel.setPixelColor(0, pixel.Color(255, 0, 0)); // Bright red
      pixel.show();
      break;
      
    case LED_HEARTBEAT: {
      // Double blink pattern: on(50ms) - off(100ms) - on(50ms) - off(850ms)
      switch (step) {
        case 0: // First blink on
          if (currentTime - lastChange >= 0) {
            pixel.setPixelColor(0, pixel.Color(255, 0, 0));
            pixel.show();
            lastChange = currentTime;
            step = 1;
          }
          break;
        case 1: // First blink off
          if (currentTime - lastChange >= 50) {
            pixel.setPixelColor(0, pixel.Color(0, 0, 0));
            pixel.show();
            lastChange = currentTime;
            step = 2;
          }
          break;
        case 2: // Brief pause
          if (currentTime - lastChange >= 100) {
            pixel.setPixelColor(0, pixel.Color(255, 0, 0));
            pixel.show();
            lastChange = currentTime;
            step = 3;
          }
          break;
        case 3: // Second blink off
          if (currentTime - lastChange >= 50) {
            pixel.setPixelColor(0, pixel.Color(0, 0, 0));
            pixel.show();
            lastChange = currentTime;
            step = 4;
          }
          break;
        case 4: // Long pause
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
          pixel.setPixelColor(0, pixel.Color(0, 0, 0));
        } else {
          pixel.setPixelColor(0, pixel.Color(255, 0, 0));
        }
        pixel.show();
        ledState = !ledState;
        lastChange = currentTime;
      }
      break;
      
    case LED_SLOW_BLINK:
      // 500ms on/off cycle
      if (currentTime - lastChange >= 500) {
        if (ledState) {
          pixel.setPixelColor(0, pixel.Color(0, 0, 0));
        } else {
          pixel.setPixelColor(0, pixel.Color(255, 0, 0));
        }
        pixel.show();
        ledState = !ledState;
        lastChange = currentTime;
      }
      break;
      
    case LED_LANDING_BLINK:
      // 50ms on, 2950ms off cycle (3 second total)
      if (!ledState && currentTime - lastChange >= 50) {
        pixel.setPixelColor(0, pixel.Color(255, 0, 0));
        pixel.show();
        ledState = true;
        lastChange = currentTime;
      } else if (ledState && currentTime - lastChange >= 2950) {
        pixel.setPixelColor(0, pixel.Color(0, 0, 0));
        pixel.show();
        ledState = false;
        lastChange = currentTime;
      }
      break;
  }
}

// Serial parameter programming functions

// Timestamp utility function
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

void loadParameters() {
  currentParams = flash_store.read();
  
  // If parameters are not valid or this is first boot, use defaults
  if (!currentParams.valid ||
      !validateParameters(currentParams.motorRunTime,
                         currentParams.totalFlightTime,
                         currentParams.motorSpeed,
                         currentParams.dtRetracted,
                         currentParams.dtDeployed,
                         currentParams.dtDwell)) {
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

void resetToDefaults() {
  currentParams = DEFAULT_PARAMS;
  saveParameters();
  
  // Recalculate timing variables
  motorTimeMS = currentParams.motorRunTime * 1000UL;
  totalFlightTimeMS = currentParams.totalFlightTime * 1000UL;
  
  Serial.println(F("[OK] Parameters reset to defaults"));
  showParameters();
}

bool validateParameters(unsigned short motorTime, unsigned short totalTime, unsigned short motorSpeed,
                       unsigned short dtRetracted, unsigned short dtDeployed, unsigned short dtDwell) {
  // Check individual parameter ranges
  if (motorTime < MIN_MOTOR_TIME || motorTime > MAX_MOTOR_TIME) {
    return false;
  }
  if (totalTime < MIN_TOTAL_TIME || totalTime > MAX_TOTAL_TIME) {
    return false;
  }
  if (motorSpeed < MIN_MOTOR_SPEED || motorSpeed > MAX_MOTOR_SPEED) {
    return false;
  }
  if (dtRetracted < 950 || dtRetracted > 2050) {
    return false;
  }
  if (dtDeployed < 950 || dtDeployed > 2050) {
    return false;
  }
  if (dtDwell < 1 || dtDwell > 60) {
    return false;
  }

  // Check logical relationship: motor time must be less than total time with margin
  if (motorTime >= totalTime - 5) {
    return false;
  }

  return true;
}

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
    case 'M': {
      // Motor run time
      if (command.length() < 3) {
        Serial.println(F("[ERR] Format: M <seconds>"));
        return;
      }
      
      int value = command.substring(2).toInt();
      if (value < MIN_MOTOR_TIME || value > MAX_MOTOR_TIME) {
        Serial.print(F("[ERR] Motor time out of range ("));
        Serial.print(MIN_MOTOR_TIME);
        Serial.print(F("-"));
        Serial.print(MAX_MOTOR_TIME);
        Serial.println(F(" seconds)"));
        return;
      }
      
      if (value >= currentParams.totalFlightTime - 5) {
        Serial.println(F("[ERR] Motor time must be < total time - 5 sec"));
        return;
      }
      
      currentParams.motorRunTime = value;
      motorTimeMS = value * 1000UL;
      saveParameters();
      
      Serial.print(F("[OK] Motor Run Time = "));
      Serial.print(value);
      Serial.println(F(" seconds"));
      break;
    }
    
    case 'T': {
      // Total flight time
      if (command.length() < 3) {
        Serial.println(F("[ERR] Format: T <seconds>"));
        return;
      }
      
      int value = command.substring(2).toInt();
      if (value < MIN_TOTAL_TIME || value > MAX_TOTAL_TIME) {
        Serial.print(F("[ERR] Total time out of range ("));
        Serial.print(MIN_TOTAL_TIME);
        Serial.print(F("-"));
        Serial.print(MAX_TOTAL_TIME);
        Serial.println(F(" seconds)"));
        return;
      }
      
      if (value <= currentParams.motorRunTime + 5) {
        Serial.println(F("[ERR] Total time must be >= motor time + 5 sec"));
        return;
      }
      
      currentParams.totalFlightTime = value;
      totalFlightTimeMS = value * 1000UL;
      saveParameters();
      
      Serial.print(F("[OK] Total Flight Time = "));
      Serial.print(value);
      Serial.println(F(" seconds"));
      break;
    }
    
    case 'S': {
      // Motor speed
      if (command.length() < 3) {
        Serial.println(F("[ERR] Format: S <speed>"));
        return;
      }
      
      int value = command.substring(2).toInt();
      if (value < MIN_MOTOR_SPEED || value > MAX_MOTOR_SPEED) {
        Serial.print(F("[ERR] Motor speed out of range ("));
        Serial.print(MIN_MOTOR_SPEED);
        Serial.print(F("-"));
        Serial.print(MAX_MOTOR_SPEED);
        Serial.println(F(")"));
        return;
      }
      
      currentParams.motorSpeed = value;
      saveParameters();
      
      Serial.print(F("[OK] Motor Speed = "));
      Serial.print(value);
      Serial.print(F(" ("));
      Serial.print(value * 10);
      Serial.println(F("us PWM)"));
      break;
    }
    
    case 'G': {
      // Get parameters
      showParameters();
      break;
    }
    
    case 'R': {
      // Reset to defaults
      resetToDefaults();
      break;
    }

    case 'D': {
      // Handle DT commands (DR, DD, DW) or Download (D)
      if (command.length() >= 3 && command.substring(0, 2) == "DR") {
        // DT Retracted position
        if (command.length() < 4) {
          Serial.println(F("[ERR] Format: DR <microseconds>"));
          return;
        }

        int value = command.substring(3).toInt();
        if (value < 950 || value > 2050) {
          Serial.println(F("[ERR] DT retracted position out of range (950-2050)"));
          return;
        }

        currentParams.dtRetracted = value;
        saveParameters();

        Serial.print(F("[OK] DT Retracted = "));
        Serial.print(value);
        Serial.println(F("us"));

      } else if (command.length() >= 3 && command.substring(0, 2) == "DD") {
        // DT Deployed position
        if (command.length() < 4) {
          Serial.println(F("[ERR] Format: DD <microseconds>"));
          return;
        }

        int value = command.substring(3).toInt();
        if (value < 950 || value > 2050) {
          Serial.println(F("[ERR] DT deployed position out of range (950-2050)"));
          return;
        }

        currentParams.dtDeployed = value;
        saveParameters();

        Serial.print(F("[OK] DT Deployed = "));
        Serial.print(value);
        Serial.println(F("us"));

      } else if (command.length() >= 3 && command.substring(0, 2) == "DW") {
        // DT Dwell time
        if (command.length() < 4) {
          Serial.println(F("[ERR] Format: DW <seconds>"));
          return;
        }

        int value = command.substring(3).toInt();
        if (value < 1 || value > 60) {
          Serial.println(F("[ERR] DT dwell time out of range (1-60)"));
          return;
        }

        currentParams.dtDwell = value;
        saveParameters();

        Serial.print(F("[OK] DT Dwell = "));
        Serial.print(value);
        Serial.println(F(" seconds"));

      } else {
        // Download flight records
        downloadFlightRecords();
      }
      break;
    }

    case 'X': {
      // Clear flight records
      clearFlightRecords();
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

void showParameters() {
  Serial.println(F("[INFO] Current Parameters"));
  Serial.print(F("[INFO] Motor Run Time: "));
  Serial.print(currentParams.motorRunTime);
  Serial.println(F(" seconds"));
  Serial.print(F("[INFO] Total Flight Time: "));
  Serial.print(currentParams.totalFlightTime);
  Serial.println(F(" seconds"));
  Serial.print(F("[INFO] Motor Speed: "));
  Serial.print(currentParams.motorSpeed);
  Serial.print(F(" ("));
  Serial.print(currentParams.motorSpeed * 10);
  Serial.println(F("us PWM)"));
  Serial.print(F("[INFO] Current Phase: "));
  Serial.println(getStateName(flightState));
  Serial.print(F("[INFO] GPS Status: "));
  if (gpsAvailable) {
    Serial.print(F("Available ("));
    Serial.print(positionCount);
    Serial.println(F(" positions recorded)"));
  } else {
    Serial.println(F("Not detected"));
  }
  Serial.print(F("[INFO] DT Retracted: "));
  Serial.print(currentParams.dtRetracted);
  Serial.println(F("us"));
  Serial.print(F("[INFO] DT Deployed: "));
  Serial.print(currentParams.dtDeployed);
  Serial.println(F("us"));
  Serial.print(F("[INFO] DT Dwell: "));
  Serial.print(currentParams.dtDwell);
  Serial.println(F(" seconds"));
}

void showHelp() {
  Serial.println(F("[INFO] FlightSequencer Parameter Commands:"));
  Serial.print(F("[INFO] M <sec>   - Set motor run time ("));
  Serial.print(MIN_MOTOR_TIME);
  Serial.print(F("-"));
  Serial.print(MAX_MOTOR_TIME);
  Serial.println(F(")"));
  Serial.print(F("[INFO] T <sec>   - Set total flight time ("));
  Serial.print(MIN_TOTAL_TIME);
  Serial.print(F("-"));
  Serial.print(MAX_TOTAL_TIME);
  Serial.println(F(")"));
  Serial.print(F("[INFO] S <speed> - Set motor speed ("));
  Serial.print(MIN_MOTOR_SPEED);
  Serial.print(F("-"));
  Serial.print(MAX_MOTOR_SPEED);
  Serial.println(F(")"));
  Serial.println(F("[INFO] DR <us>   - Set DT retracted position (950-2050)"));
  Serial.println(F("[INFO] DD <us>   - Set DT deployed position (950-2050)"));
  Serial.println(F("[INFO] DW <sec>  - Set DT dwell time (1-60)"));
  Serial.println(F("[INFO] G         - Get current parameters"));
  Serial.println(F("[INFO] R         - Reset to defaults"));
  Serial.println(F("[INFO] D         - Download flight records"));
  Serial.println(F("[INFO] X         - Clear flight records"));
  Serial.println(F("[INFO] ?         - Show this help"));
  if (gpsAvailable) {
    Serial.print(F("[INFO] GPS Status: Available ("));
    Serial.print(positionCount);
    Serial.println(F(" positions recorded)"));
  } else {
    Serial.println(F("[INFO] GPS Status: Not detected"));
  }
}

// GPS Functions

void detectGPS() {
  Serial1.begin(9600);
  delay(100);

  Serial.println(F("[INFO] Detecting GPS module..."));

  unsigned long startTime = millis();
  while (millis() - startTime < 2000) {  // 2 second detection window
    if (Serial1.available()) {
      String line = Serial1.readStringUntil('\n');
      if (line.startsWith("$GN") || line.startsWith("$GP")) {
        gpsAvailable = true;
        Serial.println(F("[INFO] GPS module detected on Serial1"));
        return;
      }
    }
  }
  Serial.println(F("[INFO] No GPS detected - continuing without GPS"));
}

void processGPSData() {
  if (!gpsAvailable || !Serial1.available()) return;

  String sentence = Serial1.readStringUntil('\n');
  if (sentence.startsWith("$GNGGA") || sentence.startsWith("$GPGGA")) {
    if (parseNMEASentence(sentence)) {
      // Record position during active flight states with timing interval
      bool shouldRecord = false;

      // Record during active flight phases (Motor Spool through DT Deploy)
      if ((flightState >= 3 && flightState <= 6) &&
          (millis() - lastGPSRecord > GPS_RECORD_INTERVAL)) {
        shouldRecord = true;
      }

      // Continue recording for 1 minute after DT deployment (Landing state)
      if (flightState == 99 && dtDeployTime > 0 &&
          (millis() - dtDeployTime < POST_DT_RECORD_TIME) &&
          (millis() - lastGPSRecord > GPS_RECORD_INTERVAL)) {
        shouldRecord = true;
      }

      if (shouldRecord) {
        recordPosition();
        lastGPSRecord = millis();
      }
    }
  }
}

bool parseNMEASentence(String sentence) {
  // Parse NMEA GGA sentence: $GPGGA,time,lat,N/S,lon,E/W,quality,satellites,hdop,alt,M,geoid,M,age,station*checksum
  int commaCount = 0;
  int startPos = 0;
  int endPos = 0;
  String fields[15];

  // Split sentence by commas
  for (int i = 0; i < sentence.length() && commaCount < 15; i++) {
    if (sentence.charAt(i) == ',' || i == sentence.length() - 1) {
      endPos = (sentence.charAt(i) == ',') ? i : i + 1;
      fields[commaCount] = sentence.substring(startPos, endPos);
      startPos = endPos + 1;
      commaCount++;
    }
  }

  if (commaCount < 6) return false;

  // Extract GPS quality and satellite count
  gpsQuality = fields[6].toInt();
  satelliteCount = fields[7].toInt();

  if (gpsQuality == 0 || fields[2].length() == 0 || fields[4].length() == 0) {
    return false; // No fix or missing data
  }

  // Parse latitude (DDMM.MMMMM format)
  String latStr = fields[2];
  if (latStr.length() >= 7) {
    float degrees = latStr.substring(0, 2).toFloat();
    float minutes = latStr.substring(2).toFloat();
    currentLat = degrees + (minutes / 60.0);
    if (fields[3] == "S") currentLat = -currentLat;
  }

  // Parse longitude (DDDMM.MMMMM format)
  String lonStr = fields[4];
  if (lonStr.length() >= 8) {
    float degrees = lonStr.substring(0, 3).toFloat();
    float minutes = lonStr.substring(3).toFloat();
    currentLon = degrees + (minutes / 60.0);
    if (fields[5] == "W") currentLon = -currentLon;
  }

  return true;
}

void recordPosition() {
  if (positionCount >= MAX_GPS_POSITIONS) return;

  unsigned long flightElapsed = millis() - startTime;

  flightPath[positionCount].latitude = currentLat;
  flightPath[positionCount].longitude = currentLon;
  flightPath[positionCount].timestamp = flightElapsed;

  // Use special state code for post-DT recording period
  if (flightState == 99 && dtDeployTime > 0 &&
      (millis() - dtDeployTime < POST_DT_RECORD_TIME)) {
    flightPath[positionCount].flightState = 7; // POST_DT_DESCENT
  } else {
    flightPath[positionCount].flightState = flightState;
  }

  flightPath[positionCount].valid = true;

  positionCount++;
}

void clearFlightRecords() {
  positionCount = 0;
  Serial.print(F("[OK] Flight records cleared ("));
  Serial.print(MAX_GPS_POSITIONS);
  Serial.println(F(" positions available)"));
}

void downloadFlightRecords() {
  if (positionCount == 0) {
    Serial.println(F("[INFO] No flight records available"));
    if (gpsAvailable) {
      Serial.println(F("[INFO] GPS detected but no positions recorded"));
    } else {
      Serial.println(F("[INFO] GPS not available"));
    }
    return;
  }

  Serial.println(F("[START_FLIGHT_DATA]"));

  // Send flight header first
  Serial.print(F("HEADER,F_"));
  Serial.print(millis());
  Serial.print(F(","));
  Serial.print(millis() - flightStartTime);
  Serial.print(F(",true,"));
  Serial.print(positionCount);
  Serial.print(F(","));
  Serial.print(currentParams.motorRunTime);
  Serial.print(F(","));
  Serial.print(currentParams.totalFlightTime);
  Serial.print(F(","));
  Serial.println(currentParams.motorSpeed);

  // Send GPS data records
  for (int i = 0; i < positionCount; i++) {
    Serial.print(F("GPS,"));
    Serial.print(flightPath[i].timestamp);
    Serial.print(F(","));
    Serial.print(flightPath[i].flightState);
    Serial.print(F(","));
    Serial.print(getStateName(flightPath[i].flightState));
    Serial.print(F(","));
    Serial.print(flightPath[i].latitude, 6);
    Serial.print(F(","));
    Serial.println(flightPath[i].longitude, 6);

    // Small delay every 10 records to prevent buffer overflow
    if (i % 10 == 9) {
      delay(20);
    }
  }

  Serial.println(F("[END_FLIGHT_DATA]"));
  Serial.print(F("[INFO] Downloaded "));
  Serial.print(positionCount);
  Serial.println(F(" GPS positions in CSV format"));
}

const char* getStateName(int state) {
  switch (state) {
    case 1: return "READY";
    case 2: return "ARMED";
    case 3: return "MOTOR_SPOOL";
    case 4: return "MOTOR_RUN";
    case 5: return "GLIDE";
    case 6: return "DT_DEPLOY";
    case 7: return "POST_DT_DESCENT";
    case 99: return "LANDING";
    default: return "UNKNOWN";
  }
}