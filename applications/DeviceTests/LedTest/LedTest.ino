/*
 * LedTest.ino - NeoPixel LED HAL Test Application
 * 
 * Tests NeoPixel color display, brightness control, and power management
 * using timed sequences with factual output reporting.
 * 
 * Hardware Requirements:
 * - Adafruit QT Py SAMD21
 * - Onboard NeoPixel LED (pin 11)
 * 
 * Serial Output: 9600 baud
 * 
 * Test validates:
 * - Primary color display (Red, Green, Blue)
 * - Secondary color display (Cyan, Magenta, Yellow, White)
 * - Brightness control across full range (0-255)
 * - Power control (on/off states)
 * - Color accuracy and timing
 */

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

// Hardware pin definitions
const int NEOPIXEL_PIN = 11;     // Onboard NeoPixel
const int NEOPIXEL_COUNT = 1;    // Single LED

// Test configuration
const unsigned long TEST_DURATION = 65000;    // 65 second test duration
const unsigned long COLOR_DISPLAY_TIME = 3000; // 3 seconds per color
const unsigned long BRIGHTNESS_STEP_TIME = 200; // 200ms per brightness step
const unsigned long POWER_CYCLE_TIME = 500;    // 500ms for power states

// Test statistics
int colorsDisplayed = 0;
int brightnessSteps = 0;
int powerCycles = 0;
unsigned long testStartTime = 0;
bool testActive = false;

// NeoPixel instance
Adafruit_NeoPixel pixel(NEOPIXEL_COUNT, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// Test state management
enum TestPhase {
  PHASE_ANNOUNCE_PRIMARY,
  PHASE_PRIMARY_COLORS,
  PHASE_ANNOUNCE_BRIGHTNESS,
  PHASE_BRIGHTNESS_RAMP,
  PHASE_ANNOUNCE_POWER,
  PHASE_POWER_CONTROL,
  PHASE_COMPLETE
};
TestPhase currentPhase = PHASE_ANNOUNCE_PRIMARY;
unsigned long phaseStartTime = 0;
int phaseStep = 0;
bool phaseMessageSent = false;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect (Leonardo/Micro compatibility)
  }

  Serial.println(F("[APP] LedTest"));

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
  
  // Initialize NeoPixel
  pixel.begin();
  pixel.clear();
  pixel.show();
  
  // Start test
  startLedTest();
}

void loop() {
  if (!testActive) {
    return;
  }
  
  unsigned long currentTime = millis();
  
  // Check for overall test timeout
  if (currentTime - testStartTime > TEST_DURATION) {
    completeLedTest();
    return;
  }
  
  // Execute current test phase
  executeCurrentPhase(currentTime);
  
  // Small delay to prevent excessive polling
  delay(10);
}

void executeCurrentPhase(unsigned long currentTime) {
  unsigned long phaseElapsed = currentTime - phaseStartTime;
  
  switch (currentPhase) {
    case PHASE_ANNOUNCE_PRIMARY:
      executeAnnouncePrimary(phaseElapsed);
      break;
      
    case PHASE_PRIMARY_COLORS:
      executePrimaryColorTest(phaseElapsed);
      break;
      
    case PHASE_ANNOUNCE_BRIGHTNESS:
      executeAnnounceBrightness(phaseElapsed);
      break;
      
    case PHASE_BRIGHTNESS_RAMP:
      executeBrightnessRampTest(phaseElapsed);
      break;
      
    case PHASE_ANNOUNCE_POWER:
      executeAnnouncePower(phaseElapsed);
      break;
      
    case PHASE_POWER_CONTROL:
      executePowerControlTest(phaseElapsed);
      break;
      
    case PHASE_COMPLETE:
      completeLedTest();
      break;
  }
}

void executeAnnouncePrimary(unsigned long phaseElapsed) {
  // static bool firstCall = true;
  // if (firstCall) {
  //   Serial.print(F("[DEBUG] executeAnnouncePrimary first call: phaseElapsed="));
  //   Serial.println(phaseElapsed);
  //   firstCall = false;
  // }
  
  if (!phaseMessageSent) {
    // Turn off LED and announce
    pixel.clear();
    pixel.show();
    Serial.println(F("[INFO] About to display RED, GREEN, BLUE and combinations"));
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= 2000) { // 2 second delay for LED off period
    advanceToNextPhase(PHASE_PRIMARY_COLORS);
  }
}

void executePrimaryColorTest(unsigned long phaseElapsed) {
  // static bool firstCall = true;
  // if (firstCall) {
  //   Serial.print(F("[DEBUG] executePrimaryColorTest first call: phaseElapsed="));
  //   Serial.println(phaseElapsed);
  //   firstCall = false;
  // }
  
  // RGB color combinations: single colors at full brightness, combinations at reduced brightness
  const uint32_t colors[] = {
    pixel.Color(255, 0, 0),      // RED
    pixel.Color(0, 255, 0),      // GREEN  
    pixel.Color(0, 0, 255),      // BLUE
    pixel.Color(127, 127, 0),    // RED+GREEN (Yellow)
    pixel.Color(127, 0, 127),    // RED+BLUE (Magenta)
    pixel.Color(0, 127, 127),    // GREEN+BLUE (Cyan)
    pixel.Color(85, 85, 85)      // RED+GREEN+BLUE (White)
  };
  const char* colorNames[] = {"RED", "GREEN", "BLUE", "RED+GREEN", "RED+BLUE", "GREEN+BLUE", "RED+GREEN+BLUE"};
  const int numColors = 7;
  
  int colorIndex = phaseElapsed / COLOR_DISPLAY_TIME;
  
  if (colorIndex < numColors) {
    if (phaseStep != colorIndex) {
      // Reset brightness to full for color display
      pixel.setBrightness(255);
      // Display new color
      pixel.setPixelColor(0, colors[colorIndex]);
      pixel.show();
      Serial.print(F("[OK] Color displayed: ["));
      Serial.print(colorIndex);
      Serial.print(F("] "));
      Serial.print(colorNames[colorIndex]);
      Serial.print(F(" at "));
      Serial.print((millis()) / 1000.0, 1);
      Serial.print(F("s (phaseElapsed="));
      Serial.print(phaseElapsed);
      Serial.println(F("ms)"));
      colorsDisplayed++;
      phaseStep = colorIndex;
    }
  } else {
    // Move to next phase
    advanceToNextPhase(PHASE_ANNOUNCE_BRIGHTNESS);
  }
}

void executeAnnounceBrightness(unsigned long phaseElapsed) {
  // static bool firstCall = true;
  // if (firstCall) {
  //   Serial.print(F("[DEBUG] executeAnnounceBrightness first call: phaseElapsed="));
  //   Serial.println(phaseElapsed);
  //   firstCall = false;
  // }
  
  if (!phaseMessageSent) {
    // Turn off LED and announce
    pixel.clear();
    pixel.show();
    Serial.println(F("[INFO] About to cycle brightness 3 times"));
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= 2000) { // 2 second delay for LED off period
    advanceToNextPhase(PHASE_BRIGHTNESS_RAMP);
  }
}

void executeBrightnessRampTest(unsigned long phaseElapsed) {
  // static bool firstCall = true;
  // if (firstCall) {
  //   Serial.print(F("[DEBUG] executeBrightnessRampTest first call: phaseElapsed="));
  //   Serial.println(phaseElapsed);
  //   firstCall = false;
  // }
  
  // Brightness ramp 3 complete cycles: 0 -> 255 -> 0
  const int maxBrightness = 255;
  const int brightnessStepSize = 32;
  const int stepsPerCycle = (maxBrightness / brightnessStepSize) * 2; // Up and down
  const int totalCycles = 3;
  const int totalSteps = stepsPerCycle * totalCycles;
  
  int stepIndex = phaseElapsed / BRIGHTNESS_STEP_TIME;
  
  if (stepIndex < totalSteps) {
    int cycleStep = stepIndex % stepsPerCycle;
    int brightness;
    
    if (cycleStep < stepsPerCycle / 2) {
      // Ramp up
      brightness = cycleStep * brightnessStepSize;
    } else {
      // Ramp down
      brightness = maxBrightness - ((cycleStep - stepsPerCycle / 2) * brightnessStepSize);
    }
    
    if (brightness < 0) brightness = 0;
    if (brightness > 255) brightness = 255;
    
    if (phaseStep != stepIndex) {
      // Set new brightness with white color (no serial output)
      pixel.setBrightness(brightness);
      pixel.setPixelColor(0, pixel.Color(255, 255, 255));
      pixel.show();
      brightnessSteps++;
      phaseStep = stepIndex;
    }
  } else {
    // Report completion and move to next phase
    if (phaseStep != -1) {
      Serial.print(F("[OK] Brightness cycling completed at "));
      Serial.print((millis()) / 1000.0, 1);
      Serial.println(F("s"));
      phaseStep = -1;
    }
    advanceToNextPhase(PHASE_ANNOUNCE_POWER);
  }
}

void executeAnnouncePower(unsigned long phaseElapsed) {
  // static bool firstCall = true;
  // if (firstCall) {
  //   Serial.print(F("[DEBUG] executeAnnouncePower first call: phaseElapsed="));
  //   Serial.println(phaseElapsed);
  //   firstCall = false;
  // }
  
  if (!phaseMessageSent) {
    // Turn off LED and announce
    pixel.clear();
    pixel.show();
    Serial.println(F("[INFO] About to blink GREEN LED 3 times"));
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= 2000) { // 2 second delay for LED off period
    advanceToNextPhase(PHASE_POWER_CONTROL);
  }
}

void executePowerControlTest(unsigned long phaseElapsed) {
  // static bool firstCall = true;
  // if (firstCall) {
  //   Serial.print(F("[DEBUG] executePowerControlTest first call: phaseElapsed="));
  //   Serial.println(phaseElapsed);
  //   firstCall = false;
  // }
  
  // Power cycling: 3 clear blinks (on/off states)
  const int numCycles = 3;
  const unsigned long cycleTime = 1500; // 1.5 seconds per complete blink (on + off)
  
  int cycleIndex = phaseElapsed / cycleTime;
  
  if (cycleIndex < numCycles) {
    bool isOn = (phaseElapsed % cycleTime) < 750; // On for first 750ms of each cycle
    int expectedStep = cycleIndex * 2 + (isOn ? 0 : 1);
    
    if (phaseStep != expectedStep) {
      if (isOn) {
        // Power on - show green at medium brightness
        pixel.setBrightness(128);
        pixel.setPixelColor(0, pixel.Color(0, 255, 0));
        pixel.show();
      } else {
        // Power off - complete darkness
        pixel.setBrightness(0);
        pixel.clear();
        pixel.show();
        powerCycles++;
      }
      phaseStep = expectedStep;
    }
  } else {
    // Ensure LED is off and report completion
    if (phaseStep != -1) {
      pixel.setBrightness(0);
      pixel.clear();
      pixel.show();
      Serial.print(F("[OK] Power control completed ("));
      Serial.print(powerCycles);
      Serial.print(F(" blinks) at "));
      Serial.print((millis()) / 1000.0, 1);
      Serial.println(F("s"));
      phaseStep = -1;
    }
    advanceToNextPhase(PHASE_COMPLETE);
  }
}

void advanceToNextPhase(TestPhase nextPhase) {
  currentPhase = nextPhase;
  phaseStartTime = millis();
  phaseStep = -1;  // Initialize to -1 so first color (index 0) will display
  phaseMessageSent = false;
}

void startLedTest() {
  testStartTime = millis();
  testActive = true;
  colorsDisplayed = 0;
  brightnessSteps = 0;
  powerCycles = 0;
  advanceToNextPhase(PHASE_ANNOUNCE_PRIMARY);
  
  Serial.println(F("[INFO] NeoPixel LED Test Starting"));
  Serial.println(F("[INFO] Testing colors, brightness, and power control"));
  Serial.print(F("[INFO] Test will run for "));
  Serial.print(TEST_DURATION / 1000.0, 1);
  Serial.println(F(" seconds"));
  Serial.println();
}

void completeLedTest() {
  testActive = false;
  
  // Turn off LED
  pixel.clear();
  pixel.show();
  
  Serial.println();
  Serial.println(F("[INFO] NeoPixel LED Test Complete - verify output"));
  Serial.print(F("[INFO] Events executed: "));
  Serial.print(colorsDisplayed);
  Serial.print(F(" colors, "));
  Serial.print(brightnessSteps);
  Serial.print(F(" brightness steps, "));
  Serial.print(powerCycles);
  Serial.println(F(" power cycles"));
  Serial.println(F("[INFO] Color accuracy: User visual verification required"));
  Serial.println(F("[INFO] Brightness control: User visual verification required"));
  Serial.println(F("[INFO] Power control: User visual verification required"));
}