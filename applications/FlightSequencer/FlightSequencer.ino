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
 * QtPY Port: Phase 1 with hardcoded parameters
 */

#include <Arduino.h>
#include <Servo.h>
#include <Adafruit_NeoPixel.h>

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

// Hardcoded flight parameters (Phase 1)
const unsigned short MOTOR_RUN_TIME = 8;    // 8 sec for debug, was 20
const unsigned short TOTAL_FLIGHT_TIME = 30; // 30 sec for debug, was 120
const unsigned short MOTOR_SPEED = 130;      // 130 -> 1300µs PWM pulse

// Servo control constants
const int MIN_SPEED = 95;            // 95 -> 950µs pulse (motor idle)
const int MAX_SPEED = 200;           // 200 -> 2000µs pulse (motor max)
const int DT_RETRACT = 1000;         // 1000µs pulse (dethermalizer retracted)
const int DT_DEPLOY = 2000;          // 2000µs pulse (dethermalizer deployed)

// Flight timing variables
unsigned long startTime;
unsigned long motorTimeMS;
unsigned long totalFlightTimeMS;

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

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial && millis() < 3000) {
    ; // Wait up to 3 seconds for serial connection
  }
  
  Serial.println(F("[INFO] FlightSequencer starting..."));
  Serial.println(F("[INFO] Phase 1: Hardcoded parameters"));
  
  // Initialize hardware
  initializeSystem();
  
  Serial.println(F("[INFO] System ready - press button to arm"));
}

void loop() {
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
  dtServo.writeMicroseconds(DT_RETRACT);        // DT retracted
  motorServo.writeMicroseconds(MIN_SPEED * 10); // Motor idle
  
  // Calculate flight timing
  motorTimeMS = MOTOR_RUN_TIME * 1000UL;
  totalFlightTimeMS = TOTAL_FLIGHT_TIME * 1000UL;
  
  Serial.print(F("[INFO] Motor run time: "));
  Serial.print(MOTOR_RUN_TIME);
  Serial.println(F(" seconds"));
  Serial.print(F("[INFO] Total flight time: "));
  Serial.print(TOTAL_FLIGHT_TIME);
  Serial.println(F(" seconds"));
  Serial.print(F("[INFO] Motor speed: "));
  Serial.print(MOTOR_SPEED * 10);
  Serial.println(F("µs PWM"));
}

int executeReadyState(int currentState) {
  unsigned long currentTime = millis();
  
  // Heartbeat LED pattern
  updateLED(LED_HEARTBEAT, currentTime);
  
  // Check for arming (requires long press)
  if (longPressDetected) {
    armTime = millis();
    longPressDetected = false; // Clear the flag
    Serial.println(F("[INFO] System ARMED - short press to launch"));
    
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
    Serial.println(F("[INFO] LAUNCH! Motor spooling..."));
    
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
    for (int speed = MIN_SPEED; speed <= MOTOR_SPEED; speed += 5) {
      motorServo.writeMicroseconds(speed * 10);
      delay(50); // Small delay for smooth ramp
    }
    
    // Ensure final speed is set
    motorServo.writeMicroseconds(MOTOR_SPEED * 10);
    spoolComplete = true;
    
    Serial.print(F("[INFO] Motor at flight speed: "));
    Serial.print(MOTOR_SPEED * 10);
    Serial.println(F("µs"));
    
    return 4; // Transition to Motor Run State
  }
  
  return currentState; // Stay in Motor Spool State
}

int executeMotorRunState(int currentState) {
  unsigned long currentTime = millis();
  
  // LED on during motor run
  updateLED(LED_SOLID_RED, currentTime);
  
  // Maintain motor at flight speed
  motorServo.writeMicroseconds(MOTOR_SPEED * 10);
  
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
    Serial.println(F("[INFO] Motor run complete - entering glide phase"));
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
    Serial.println(F("[INFO] Flight time complete - deploying DT"));
    return 6; // Transition to DT Deploy State
  }
  
  return currentState; // Stay in Glide State
}

int executeDTDeployState(int currentState) {
  static unsigned long deployTime = 0;
  unsigned long currentTime = millis();
  
  // LED on during deployment
  updateLED(LED_SOLID_RED, currentTime);
  
  // Ensure motor stays idle
  motorServo.writeMicroseconds(MIN_SPEED * 10);
  
  if (!dtDeployed) {
    // Deploy dethermalizer
    dtServo.writeMicroseconds(DT_DEPLOY);
    Serial.println(F("[INFO] Dethermalizer DEPLOYED"));
    deployTime = millis();
    dtDeployed = true;
  } else if (millis() - deployTime >= 2000) {
    // Hold deployment for 2 seconds, then retract
    dtServo.writeMicroseconds(DT_RETRACT);
    Serial.println(F("[INFO] Dethermalizer retracted - flight complete"));
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
  dtServo.writeMicroseconds(DT_RETRACT);
  
  // Reset logic - long press to reset
  if (longPressDetected) {
    Serial.println(F("[INFO] System RESET - ready for new flight"));
    longPressDetected = false; // Clear the flag
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