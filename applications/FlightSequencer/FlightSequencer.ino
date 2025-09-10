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
const unsigned short MOTOR_RUN_TIME = 10;    // 10 sec for debug, was 20
const unsigned short TOTAL_FLIGHT_TIME = 30; // 30 sec for debug, was 120
const unsigned short MOTOR_SPEED = 150;      // 150 -> 1500µs PWM pulse

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

// Function prototypes
void setLedRed();
void setLedOff(); 
void updateButtonState();
void initializeSystem();
void resetStateVariables();

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
      executeReadyState();
      break;
      
    case 2: // Armed State  
      executeArmedState();
      break;
      
    case 3: // Motor Spool State
      executeMotorSpoolState();
      break;
      
    case 4: // Motor Run State
      executeMotorRunState();
      break;
      
    case 5: // Glide State
      executeGlideState();
      break;
      
    case 6: // DT Deploy State
      executeDTDeployState();
      break;
      
    case 99: // Landing State
    default:
      executeLandingState();
      break;
  }
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
  
  Serial.print(F("[DEBUG] Button pin initial state: "));
  Serial.println(lastButtonState);
  
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

void executeReadyState() {
  // Heartbeat LED pattern (double blink, pause)
  static unsigned long lastHeartbeat = 0;
  static int heartbeatStep = 0;
  
  unsigned long currentTime = millis();
  
  switch (heartbeatStep) {
    case 0: // First blink on
      if (currentTime - lastHeartbeat >= 0) {
        setLedRed();
        lastHeartbeat = currentTime;
        heartbeatStep = 1;
      }
      break;
    case 1: // First blink off
      if (currentTime - lastHeartbeat >= 50) {
        setLedOff();
        lastHeartbeat = currentTime;
        heartbeatStep = 2;
      }
      break;
    case 2: // Brief pause
      if (currentTime - lastHeartbeat >= 100) {
        setLedRed();
        lastHeartbeat = currentTime;
        heartbeatStep = 3;
      }
      break;
    case 3: // Second blink off
      if (currentTime - lastHeartbeat >= 50) {
        setLedOff();
        lastHeartbeat = currentTime;
        heartbeatStep = 4;
      }
      break;
    case 4: // Long pause
      if (currentTime - lastHeartbeat >= 850) {
        heartbeatStep = 0;
      }
      break;
  }
  
  // Check for arming (requires long press)
  if (longPressDetected) {
    flightState = 2;
    armTime = millis();
    longPressDetected = false; // Clear the flag
    Serial.println(F("[INFO] System ARMED - short press to launch"));
  }
  
  // Clear button flags after processing
  buttonJustPressed = false;
  buttonJustReleased = false;
}

void executeArmedState() {
  // Fast LED flash
  static unsigned long lastFlash = 0;
  static bool ledState = false;
  
  unsigned long currentTime = millis();
  
  if (currentTime - lastFlash >= 100) {
    if (ledState) {
      setLedOff();
    } else {
      setLedRed();
    }
    ledState = !ledState;
    lastFlash = currentTime;
  }
  
  // Check for launch (short press, with delay after arming)
  if (buttonJustReleased && (millis() - armTime > ARM_DELAY)) {
    flightState = 3;
    startTime = millis();
    Serial.println(F("[INFO] LAUNCH! Motor spooling..."));
    
    // Reset state machine variables for new flight
    resetStateVariables();
    
    // Clear ALL button flags to prevent interference with next state
    buttonJustPressed = false;
    buttonJustReleased = false;
    longPressDetected = false;
  }
  
  // Reset button flags after processing
  buttonJustPressed = false;
  buttonJustReleased = false;
}

// State variables that need to be reset between flights
bool spoolComplete = false;
bool spoolStateEntered = false;
bool runStateEntered = false;

void resetStateVariables() {
  // Reset all state-specific variables for new flight
  spoolComplete = false;
  spoolStateEntered = false;
  runStateEntered = false;
  
  Serial.println(F("[DEBUG] State variables reset for new flight"));
}

void executeMotorSpoolState() {
  // LED on during spool
  setLedRed();
  
  if (!spoolStateEntered) {
    Serial.println(F("[DEBUG] Entered Motor Spool State"));
    spoolStateEntered = true;
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
    
    flightState = 4;
  }
}

void executeMotorRunState() {
  // LED on during motor run
  setLedRed();
  
  // Maintain motor at flight speed
  motorServo.writeMicroseconds(MOTOR_SPEED * 10);
  
  if (!runStateEntered) {
    Serial.println(F("[DEBUG] Entered Motor Run State"));
    runStateEntered = true;
  }
  
  unsigned long elapsed = millis() - startTime;
  
  // Check for emergency shutoff (any button press)
  if (buttonJustPressed) {
    motorServo.writeMicroseconds(MIN_SPEED * 10);
    Serial.println(F("[WARN] Emergency motor shutoff!"));
    flightState = 99;
    buttonJustPressed = false; // Clear the flag
    return;
  }
  
  // Check for motor run completion
  if (elapsed >= motorTimeMS) {
    motorServo.writeMicroseconds(MIN_SPEED * 10);
    Serial.println(F("[INFO] Motor run complete - entering glide phase"));
    flightState = 5;
  }
}

void executeGlideState() {
  // Slow LED blink (1 second cycle)
  static unsigned long lastBlink = 0;
  static bool ledState = false;
  
  unsigned long currentTime = millis();
  
  if (currentTime - lastBlink >= 500) {
    if (ledState) {
      setLedOff();
    } else {
      setLedRed();
    }
    ledState = !ledState;
    lastBlink = currentTime;
  }
  
  // Ensure motor stays idle
  motorServo.writeMicroseconds(MIN_SPEED * 10);
  
  unsigned long elapsed = millis() - startTime;
  
  // Check for total flight time completion
  if (elapsed >= totalFlightTimeMS) {
    Serial.println(F("[INFO] Flight time complete - deploying DT"));
    flightState = 6;
  }
}

void executeDTDeployState() {
  static bool deployed = false;
  static unsigned long deployTime = 0;
  
  // LED on during deployment
  setLedRed();
  
  // Ensure motor stays idle
  motorServo.writeMicroseconds(MIN_SPEED * 10);
  
  if (!deployed) {
    // Deploy dethermalizer
    dtServo.writeMicroseconds(DT_DEPLOY);
    Serial.println(F("[INFO] Dethermalizer DEPLOYED"));
    deployTime = millis();
    deployed = true;
  } else if (millis() - deployTime >= 2000) {
    // Hold deployment for 2 seconds, then retract
    dtServo.writeMicroseconds(DT_RETRACT);
    Serial.println(F("[INFO] Dethermalizer retracted - flight complete"));
    flightState = 99;
  }
}

void executeLandingState() {
  // Slow single blink (3 second cycle)
  static unsigned long lastBlink = 0;
  static bool ledState = false;
  
  unsigned long currentTime = millis();
  
  if (currentTime - lastBlink >= 50 && !ledState) {
    setLedRed();
    ledState = true;
    lastBlink = currentTime;
  } else if (currentTime - lastBlink >= 2950 && ledState) {
    setLedOff();
    ledState = false;
    lastBlink = currentTime;
  }
  
  // Ensure safe servo positions
  motorServo.writeMicroseconds(MIN_SPEED * 10);
  dtServo.writeMicroseconds(DT_RETRACT);
  
  // Reset logic - long press to reset
  if (longPressDetected) {
    Serial.println(F("[INFO] System RESET - ready for new flight"));
    flightState = 1;
    longPressDetected = false; // Clear the flag
  }
}

void updateButtonState() {
  bool currentState = digitalRead(BUTTON_PIN);
  
  // Simple debug output every few seconds to show current pin state and system state
  static unsigned long lastDebugTime = 0;
  if (millis() - lastDebugTime > 5000) {
    Serial.print(F("[DEBUG] Pin: "));
    Serial.print(currentState);
    Serial.print(F(", State: "));
    Serial.println(flightState);
    lastDebugTime = millis();
  }
  
  // Debounce button state
  static bool lastStableState = HIGH;
  static unsigned long lastChangeTime = 0;
  
  if (currentState != lastStableState) {
    if (millis() - lastChangeTime > DEBOUNCE_DELAY) {
      Serial.print(F("[DEBUG] Button change detected: "));
      Serial.print(lastStableState);
      Serial.print(F(" -> "));
      Serial.println(currentState);
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
    Serial.println(F("[DEBUG] Button press started"));
  }
  
  // Detect release events  
  if (!currentlyPressed && buttonCurrentlyPressed) {
    // Button just released
    buttonJustReleased = true;
    unsigned long pressDuration = millis() - buttonPressStartTime;
    
    Serial.print(F("[DEBUG] Button released after "));
    Serial.print(pressDuration);
    Serial.println(F("ms"));
    
    // Check if it was a long press
    if (pressDuration >= LONG_PRESS_TIME) {
      longPressDetected = true;
      Serial.println(F("[DEBUG] Long press detected"));
    } else {
      Serial.println(F("[DEBUG] Short press detected"));
    }
  }
  
  buttonCurrentlyPressed = currentlyPressed;
}

void setLedRed() {
  pixel.setPixelColor(0, pixel.Color(255, 0, 0)); // Bright red
  pixel.show();
}

void setLedOff() {
  pixel.setPixelColor(0, pixel.Color(0, 0, 0));   // Off
  pixel.show();
}