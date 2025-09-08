/*
 * LedButton.ino - Interactive LED Button Application
 * 
 * Interactive application demonstrating button input and NeoPixel LED output
 * with debounced button handling and finite state machine design patterns.
 * 
 * Hardware Requirements:
 * - Adafruit QT Py SAMD21
 * - Push button connected to A0 (active-low with internal pullup)
 * - Onboard NeoPixel LED (pin 11)
 * 
 * Serial Output: 9600 baud
 * 
 * Features:
 * - Short press: Cycle through colors (Red → Green → Blue)
 * - Long press (1s+): Enter brightness adjustment mode
 * - Auto-return to idle after AUTO_RETURN_TIME seconds of inactivity
 * - Interrupt-driven button handling with debouncing
 */

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

// Hardware pin definitions
const int BUTTON_PIN = A0;           // Push button input pin
const int NEOPIXEL_PIN = 11;         // Onboard NeoPixel
const int NEOPIXEL_COUNT = 1;        // Single LED

// Timing configuration
const unsigned long DEBOUNCE_DELAY = 50;        // 50ms debounce delay
const unsigned long LONG_PRESS_TIME = 1000;     // 1 second for long press
const unsigned long AUTO_RETURN_TIME = 30000;   // 10 seconds auto-return to idle
const unsigned long BRIGHTNESS_ADJUST_RATE = 300; // 300ms between brightness steps

// Color definitions (RGB values)
const uint32_t COLOR_RED = 0xFF0000;
const uint32_t COLOR_GREEN = 0x00FF00;
const uint32_t COLOR_BLUE = 0x0000FF;
const uint32_t COLOR_OFF = 0x000000;

// Brightness levels (25%, 50%, 75%, 100%)
const int BRIGHTNESS_LEVELS[] = {64, 128, 192, 255};
const int NUM_BRIGHTNESS_LEVELS = 4;

// NeoPixel instance
Adafruit_NeoPixel pixel(NEOPIXEL_COUNT, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// State machine definition
enum AppState {
  STATE_IDLE,
  STATE_COLOR_CYCLE,
  STATE_BRIGHTNESS_ADJUST
};
AppState currentState = STATE_IDLE;

// Button state management
volatile bool buttonPressed = false;
volatile bool buttonReleased = false;
volatile unsigned long pressStartTime = 0;
volatile unsigned long releaseTime = 0;
volatile unsigned long lastDebounceTime = 0;
volatile bool lastButtonState = HIGH;  // Active low button
volatile bool buttonCurrentlyPressed = false;

// Application state variables
int currentColorIndex = 0;      // 0=Red, 1=Green, 2=Blue, 3=Off
int currentBrightnessIndex = 3; // Start at 100% brightness
unsigned long lastActivityTime = 0;
unsigned long lastStateChange = 0;
unsigned long brightnessAdjustTime = 0;

// Color array for cycling (removed OFF - only cycle through actual colors)
const uint32_t COLORS[] = {COLOR_RED, COLOR_GREEN, COLOR_BLUE};
const char* COLOR_NAMES[] = {"RED", "GREEN", "BLUE"};
const int NUM_COLORS = 3;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  // Initialize button pin
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initialize NeoPixel
  pixel.begin();
  pixel.setBrightness(BRIGHTNESS_LEVELS[currentBrightnessIndex]);
  pixel.clear();
  pixel.show();
  
  // Setup interrupt for button
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonInterrupt, CHANGE);
  
  // Initialize timing
  lastActivityTime = millis();
  lastStateChange = millis();
  
  Serial.println(F("[INFO] LED Button Application Starting"));
  Serial.println(F("[INFO] Short press: Cycle colors | Long press: Adjust brightness"));
  Serial.print(F("[INFO] Auto-return to idle after "));
  Serial.print(AUTO_RETURN_TIME / 1000.0, 1);
  Serial.println(F("s of inactivity"));  Serial.println();
  
  // Start in idle state
  enterState(STATE_IDLE);
}

void loop() {
  unsigned long currentTime = millis();
  
  // Handle button events
  handleButtonEvents(currentTime);
  
  // Execute current state logic
  executeCurrentState(currentTime);
  
  // Check for auto-return to idle
  checkAutoReturn(currentTime);
  
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
        buttonCurrentlyPressed = true;
        buttonPressed = true;
      } else {
        // Button released
        releaseTime = currentTime;
        buttonCurrentlyPressed = false;
        buttonReleased = true;
      }
    }
  }
}

void handleButtonEvents(unsigned long currentTime) {
  // Handle button press event
  if (buttonPressed) {
    buttonPressed = false;
    onButtonPress(currentTime);
  }
  
  // Handle button release event
  if (buttonReleased) {
    buttonReleased = false;
    onButtonRelease(currentTime);
  }
  
  // Check for long press while button is held
  if (buttonCurrentlyPressed && 
      currentState != STATE_BRIGHTNESS_ADJUST &&
      (currentTime - pressStartTime) >= LONG_PRESS_TIME) {
    onLongPress(currentTime);
  }
}

void onButtonPress(unsigned long currentTime) {
  lastActivityTime = currentTime;
  Serial.print(F("[OK] Button pressed at "));
  Serial.print(currentTime / 1000.0, 1);
  Serial.print(F("s (currentState="));
  Serial.print(currentState);
  Serial.println(F(")"));
}

void onButtonRelease(unsigned long currentTime) {
  lastActivityTime = currentTime;
  unsigned long pressDuration = releaseTime - pressStartTime;
  
  Serial.print(F("[OK] Button released at "));
  Serial.print(currentTime / 1000.0, 1);
  Serial.print(F("s (Duration: "));
  Serial.print(pressDuration);
  //Serial.print(F("ms, currentState="));
  //Serial.print(currentState);
  Serial.println(F(")"));
  
  // Handle short press (if not already handled as long press)
  if (pressDuration < LONG_PRESS_TIME && currentState != STATE_BRIGHTNESS_ADJUST) {
    onShortPress(currentTime);
  }
  
  // Exit brightness adjust mode on release
  if (currentState == STATE_BRIGHTNESS_ADJUST) {
    enterState(STATE_COLOR_CYCLE);
  }
}

void onShortPress(unsigned long currentTime) {
  if (currentState == STATE_IDLE) {
    enterState(STATE_COLOR_CYCLE);
    // First press from IDLE should show the first color immediately
    //cycleToNextColor();
  } else if (currentState == STATE_COLOR_CYCLE) {
    cycleToNextColor();
  }
}

void onLongPress(unsigned long currentTime) {
  Serial.print(F("[OK] Long press detected at "));
  Serial.print(currentTime / 1000.0, 1);
  Serial.println(F("s"));
  
  enterState(STATE_BRIGHTNESS_ADJUST);
}

void executeCurrentState(unsigned long currentTime) {
  switch (currentState) {
    case STATE_IDLE:
      executeIdleState(currentTime);
      break;
      
    case STATE_COLOR_CYCLE:
      executeColorCycleState(currentTime);
      break;
      
    case STATE_BRIGHTNESS_ADJUST:
      executeBrightnessAdjustState(currentTime);
      break;
  }
}

void executeIdleState(unsigned long currentTime) {
  // LED is off, waiting for user input
  // Nothing to do here - all handled by button events
}

void executeColorCycleState(unsigned long currentTime) {
  // Display current color - state maintained until next button press or timeout
  // Nothing to do here - color set on entry and button events
}

void executeBrightnessAdjustState(unsigned long currentTime) {
  // Automatically cycle through brightness levels while in this state
  if (currentTime - brightnessAdjustTime >= BRIGHTNESS_ADJUST_RATE) {
    adjustBrightness();
    brightnessAdjustTime = currentTime;
  }
}

void enterState(AppState newState) {
  AppState previousState = currentState;
  currentState = newState;
  lastStateChange = millis();
  // Note: lastActivityTime should only be updated by button events, not state changes
  
  // State entry actions
  switch (newState) {
    case STATE_IDLE:
      Serial.println(F("[INFO] Entering IDLE mode"));
      // Turn off LED in idle mode
      pixel.setPixelColor(0, COLOR_OFF);
      pixel.show();
      break;
      
    case STATE_COLOR_CYCLE:
      Serial.println(F("[INFO] Entering COLOR_CYCLE mode"));
      if (previousState == STATE_IDLE) {
        currentColorIndex = 0; // Start with 0 (RED)
      }
      updateLED();
      break;
      
    case STATE_BRIGHTNESS_ADJUST:
      Serial.println(F("[INFO] Entering BRIGHTNESS_ADJUST mode"));
      brightnessAdjustTime = millis();
      // Keep current color, just adjust brightness
      break;
  }
}

void cycleToNextColor() {
  currentColorIndex = (currentColorIndex + 1) % NUM_COLORS;
  updateLED();
  
  Serial.print(F("[OK] Color changed to "));
  Serial.print(COLOR_NAMES[currentColorIndex]);
  Serial.print(F(" at "));
  Serial.print(millis() / 1000.0, 1);
  Serial.println(F("s"));
}

void adjustBrightness() {
  currentBrightnessIndex = (currentBrightnessIndex + 1) % NUM_BRIGHTNESS_LEVELS;
  pixel.setBrightness(BRIGHTNESS_LEVELS[currentBrightnessIndex]);
  pixel.show();
  
  Serial.print(F("[OK] Brightness adjusted to "));
  Serial.print(BRIGHTNESS_LEVELS[currentBrightnessIndex]);
  Serial.print(F(" ("));
  Serial.print((BRIGHTNESS_LEVELS[currentBrightnessIndex] * 100) / 255);
  Serial.print(F("%) at "));
  Serial.print(millis() / 1000.0, 1);
  Serial.println(F("s"));
}

void updateLED() {
  pixel.setBrightness(BRIGHTNESS_LEVELS[currentBrightnessIndex]);
  pixel.setPixelColor(0, COLORS[currentColorIndex]);
  pixel.show();
}

void checkAutoReturn(unsigned long currentTime) {
  if (currentState != STATE_IDLE && 
      (currentTime - lastActivityTime) >= AUTO_RETURN_TIME) {
    Serial.print(F("[INFO] Auto-return to idle after "));
    Serial.print(AUTO_RETURN_TIME / 1000.0, 1);
    Serial.println(F("s of inactivity"));
    enterState(STATE_IDLE);
  }
}