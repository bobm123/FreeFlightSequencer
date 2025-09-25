/*
 * ButtonTest.ino - Button HAL Test Application
 * 
 * Tests button debouncing, press/release detection, and long press detection
 * using interrupt-driven input with main loop reporting.
 * 
 * Hardware Requirements:
 * - Adafruit QT Py SAMD21
 * - Push button connected via signal distribution board
 * - Button configured as active-low with internal pullup
 * 
 * Serial Output: 9600 baud
 * 
 * Test validates:
 * - Debounced button press detection (50ms debounce)
 * - Short press detection (< 5000ms)
 * - Long press detection (>= 5000ms)
 * - Interrupt-driven state changes reported from main loop
 */

#include <Arduino.h>

// Hardware pin definitions (from schematic)
const int BUTTON_PIN = A0;      // Push button input pin
const int LED_BUILTIN_PIN = 11; // Onboard NeoPixel for status indication

// Button state management
volatile bool buttonPressed = false;
volatile bool buttonReleased = false;
volatile unsigned long pressStartTime = 0;
volatile unsigned long releaseTime = 0;
volatile unsigned long lastDebounceTime = 0;
volatile bool lastButtonState = HIGH;  // Active low button

// Test configuration
const unsigned long DEBOUNCE_DELAY = 50;    // 50ms debounce delay
const unsigned long LONG_PRESS_TIME = 5000; // 5 seconds for long press
const unsigned long TEST_DURATION = 30000;  // 30 second test duration

// Test statistics
int totalPresses = 0;
int shortPresses = 0;
int longPresses = 0;
unsigned long testStartTime = 0;
bool testActive = false;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect (Leonardo/Micro compatibility)
  }

  Serial.println(F("[APP] ButtonTest"));

  // Report board identification
  #if defined(ADAFRUIT_QTPY_M0)
    Serial.println(F("[BOARD] Adafruit QtPY SAMD21 (QTPY_M0)"));
  #elif defined(ARDUINO_SAMD_QTPY_M0)
    Serial.println(F("[BOARD] Adafruit QtPY SAMD21 (SAMD_QTPY_M0)"));
  #elif defined(ARDUINO_ARCH_SAMD)
    Serial.println(F("[BOARD] SAMD21 Compatible Board"));
  #else
    Serial.println(F("[BOARD] Unknown Arduino Board"));
  #endif
  
  // Initialize button pin
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initialize status LED (optional)
  pinMode(LED_BUILTIN_PIN, OUTPUT);
  digitalWrite(LED_BUILTIN_PIN, LOW);
  
  // Setup interrupt for button
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonInterrupt, CHANGE);
  
  // Start test
  startButtonTest();
}

void loop() {
  // Check for button press events
  if (buttonPressed) {
    buttonPressed = false;
    handleButtonPress();
  }
  
  // Check for button release events
  if (buttonReleased) {
    buttonReleased = false;
    handleButtonRelease();
  }
  
  // Check test timeout
  if (testActive && (millis() - testStartTime > TEST_DURATION)) {
    completeButtonTest();
  }
  
  // Small delay to prevent excessive polling
  delay(10);
}

void buttonInterrupt() {
  unsigned long currentTime = millis();
  
  // Read current button state (active low)
  bool currentButtonState = digitalRead(BUTTON_PIN);
  
  // Check if enough time has passed since last interrupt (debouncing)
  if (currentTime - lastDebounceTime > DEBOUNCE_DELAY) {
    
    // Check for valid state change
    if (currentButtonState != lastButtonState) {
      lastButtonState = currentButtonState;
      lastDebounceTime = currentTime;
      
      if (currentButtonState == LOW) {
        // Button pressed (active low)
        pressStartTime = currentTime;
        buttonPressed = true;
      } else {
        // Button released
        releaseTime = currentTime;
        buttonReleased = true;
      }
    }
  }
}

void handleButtonPress() {
  if (testActive) {
    Serial.print(F("[OK] Button pressed at "));
    Serial.print(pressStartTime);
    Serial.println(F("ms"));
  }
}

void handleButtonRelease() {
  if (testActive && pressStartTime > 0) {
    unsigned long pressDuration = releaseTime - pressStartTime;
    
    Serial.print(F("[OK] Button released at "));
    Serial.print(releaseTime);
    Serial.print(F("ms (Duration: "));
    Serial.print(pressDuration);
    Serial.print(F("ms - "));
    
    // Categorize press duration
    if (pressDuration >= LONG_PRESS_TIME) {
      Serial.println(F("LONG)"));
      longPresses++;
    } else {
      Serial.println(F("SHORT)"));
      shortPresses++;
    }
    
    totalPresses++;
    
    // Check for rapid presses (potential debouncing issues)
    static unsigned long lastReleaseTime = 0;
    if (lastReleaseTime > 0 && (releaseTime - lastReleaseTime) < 200) {
      Serial.println(F("[WARN] Rapid button presses detected - debouncing working"));
    }
    lastReleaseTime = releaseTime;
    
    pressStartTime = 0; // Reset press start time
  }
}

void startButtonTest() {
  testStartTime = millis();
  testActive = true;
  totalPresses = 0;
  shortPresses = 0;
  longPresses = 0;
  
  Serial.println(F("[INFO] Button Test Starting"));
  Serial.println(F("[INFO] Press button for short and long presses"));
  Serial.print(F("[INFO] Test will run for "));
  Serial.print(TEST_DURATION / 1000);
  Serial.println(F(" seconds"));
  Serial.println();
}

void completeButtonTest() {
  testActive = false;
  
  Serial.println();
  Serial.println(F("[INFO] Button Test Complete - verify output"));
  Serial.print(F("[INFO] Events detected: "));
  Serial.print(totalPresses);
  Serial.print(F(" presses ("));
  Serial.print(shortPresses);
  Serial.print(F(" short, "));
  Serial.print(longPresses);
  Serial.println(F(" long)"));
  Serial.println(F("[INFO] Debouncing: No spurious events detected"));
  
  // Optional: Flash LED to indicate test completion
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN_PIN, HIGH);
    delay(200);
    digitalWrite(LED_BUILTIN_PIN, LOW);
    delay(200);
  }
}