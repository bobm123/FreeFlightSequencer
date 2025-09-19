/*
 * hardware_hal.cpp - Hardware Abstraction Layer Implementation
 *
 * Arduino-specific hardware interface for QtPY SAMD21 + Signal Distribution MkII.
 */

#include "hardware_hal.h"
#include <Servo.h>
#include <Adafruit_NeoPixel.h>

// Hardware objects (external, defined in main .ino file)
extern Servo rollServo;
extern Servo motorServo;
extern Adafruit_NeoPixel pixel;

// HAL state variables
static HAL_Config_t halConfig;
static HAL_Status_t halStatus;
static HAL_Error_t lastError = HAL_ERROR_NONE;
static void (*errorCallback)(HAL_Error_t) = NULL;

// Timing variables
static uint32_t lastLoopTime = 0;
static uint32_t loopCounter = 0;
static uint32_t cpuUsageAccumulator = 0;

// Pin definitions
#define ROLL_SERVO_PIN A3
#define MOTOR_SERVO_PIN A2
#define BUTTON_PIN A0
#define NEOPIXEL_PIN 11
#define BATTERY_PIN A1  // Optional battery voltage monitoring

void HAL_Init() {
  // Initialize default configuration
  halConfig.servoMinPulse = 1000;
  halConfig.servoMaxPulse = 2000;
  halConfig.servoCenterPulse = 1500;
  halConfig.motorMinPulse = 1000;
  halConfig.motorMaxPulse = 2000;
  halConfig.gpsBaudRate = 0;  // 9600 baud
  halConfig.buttonInverted = true;  // Active low
  halConfig.batteryScale = 1.0;

  // Initialize hardware status
  halStatus.gpsConnected = false;
  halStatus.servoConnected = true;
  halStatus.motorConnected = true;
  halStatus.buttonWorking = true;
  halStatus.ledWorking = true;
  halStatus.systemUptime = 0;
  halStatus.cpuUsage = 0.0;
  halStatus.freeMemory = HAL_GetFreeMemory();

  // Initialize timing
  lastLoopTime = millis();

  Serial.println(F("[HAL] Hardware abstraction layer initialized"));
}

// GPS interface functions
uint32_t HAL_ReadGPS(uint8_t* buffer, uint32_t maxBytes) {
  uint32_t bytesRead = 0;

  while (Serial1.available() && bytesRead < maxBytes - 1) {
    buffer[bytesRead] = Serial1.read();
    bytesRead++;
  }

  buffer[bytesRead] = '\0';  // Null terminate
  return bytesRead;
}

bool HAL_GPSAvailable() {
  return Serial1.available() > 0;
}

char HAL_ReadGPSChar() {
  if (Serial1.available()) {
    return Serial1.read();
  }
  return 0;
}

// Servo/ESC control functions
void HAL_SetServoPosition(float rollCommand) {
  // Convert normalized command (-1.0 to +1.0) to microseconds
  rollCommand = constrain(rollCommand, -1.0, 1.0);

  uint16_t range = halConfig.servoMaxPulse - halConfig.servoMinPulse;
  uint16_t microseconds = halConfig.servoCenterPulse + (rollCommand * range / 2.0);

  microseconds = constrain(microseconds, halConfig.servoMinPulse, halConfig.servoMaxPulse);

  rollServo.writeMicroseconds(microseconds);
}

void HAL_SetRollServo(float rollCommand, const ActuatorParams_t* params) {
  // Apply direction reversal
  float adjustedCommand = params->RollServoReversed ? -rollCommand : rollCommand;

  // Constrain command to valid range
  adjustedCommand = constrain(adjustedCommand, -1.0, 1.0);

  // Convert roll command (-1.0 to +1.0) to pulse width
  float pulseWidth = params->RollServoCenter +
                    (adjustedCommand * params->RollServoRange / 2.0);

  // Apply safety limits
  pulseWidth = constrain(pulseWidth,
                        params->RollServoMinPulse,
                        params->RollServoMaxPulse);

  // Apply deadband around center
  float centerDiff = fabs(pulseWidth - params->RollServoCenter);
  if (centerDiff < params->RollServoDeadband) {
    pulseWidth = params->RollServoCenter;
  }

  // Output to servo
  rollServo.writeMicroseconds((int)pulseWidth);

#ifdef DEBUG_SERVO
  Serial.print(F("[SERVO] Cmd: "));
  Serial.print(rollCommand);
  Serial.print(F(" Adj: "));
  Serial.print(adjustedCommand);
  Serial.print(F(" Pulse: "));
  Serial.println(pulseWidth);
#endif
}

void HAL_SetMotorSpeed(float throttleCommand) {
  // Convert normalized command (0.0 to 1.0) to microseconds
  throttleCommand = constrain(throttleCommand, 0.0, 1.0);

  uint16_t range = halConfig.motorMaxPulse - halConfig.motorMinPulse;
  uint16_t microseconds = halConfig.motorMinPulse + (throttleCommand * range);

  microseconds = constrain(microseconds, halConfig.motorMinPulse, halConfig.motorMaxPulse);

  motorServo.writeMicroseconds(microseconds);
}

void HAL_SetServoMicroseconds(uint16_t microseconds) {
  microseconds = constrain(microseconds, halConfig.servoMinPulse, halConfig.servoMaxPulse);
  rollServo.writeMicroseconds(microseconds);
}

void HAL_SetMotorMicroseconds(uint16_t microseconds) {
  microseconds = constrain(microseconds, halConfig.motorMinPulse, halConfig.motorMaxPulse);
  motorServo.writeMicroseconds(microseconds);
}

// Digital I/O functions
bool HAL_ReadButton() {
  bool state = digitalRead(BUTTON_PIN);
  return halConfig.buttonInverted ? !state : state;
}

void HAL_SetLED(uint8_t red, uint8_t green, uint8_t blue) {
  pixel.setPixelColor(0, pixel.Color(red, green, blue));
  pixel.show();
}

void HAL_ToggleLED() {
  static bool ledState = false;
  ledState = !ledState;
  HAL_SetLED(ledState ? 255 : 0, 0, 0);
}

// Analog input functions
float HAL_ReadBatteryVoltage() {
  #ifdef BATTERY_PIN
  int adcValue = analogRead(BATTERY_PIN);
  float voltage = (adcValue / 1023.0) * 3.3 * halConfig.batteryScale;
  return voltage;
  #else
  return 3.7;  // Placeholder value
  #endif
}

float HAL_ReadAnalogPin(uint8_t pin) {
  int adcValue = analogRead(pin);
  return (adcValue / 1023.0) * 3.3;  // Convert to voltage
}

// Timing functions
bool HAL_ClockMainLoop(float* deltaTime) {
  uint32_t currentTime = millis();
  uint32_t elapsed = currentTime - lastLoopTime;

  // Target 50Hz (20ms) loop rate
  if (elapsed >= 20) {
    *deltaTime = elapsed / 1000.0;
    lastLoopTime = currentTime;
    loopCounter++;

    // Update CPU usage calculation
    cpuUsageAccumulator += elapsed;
    if (loopCounter % 50 == 0) {  // Update every second
      halStatus.cpuUsage = (cpuUsageAccumulator / 1000.0) * 100.0;
      cpuUsageAccumulator = 0;
    }

    return true;
  }

  return false;
}

uint32_t HAL_GetSystemTime() {
  return millis();
}

void HAL_DelayMicroseconds(uint32_t microseconds) {
  delayMicroseconds(microseconds);
}

void HAL_DelayMilliseconds(uint32_t milliseconds) {
  delay(milliseconds);
}

// System information functions
uint32_t HAL_GetFreeMemory() {
  // Simple free memory estimation for SAMD21
  // Return a reasonable estimate since exact calculation requires platform-specific code
  return 16384; // SAMD21 has 32KB RAM, estimate ~16KB available
}

float HAL_GetCPUUsage() {
  return halStatus.cpuUsage;
}

void HAL_SystemReset() {
  // ARM Cortex-M0+ system reset
  NVIC_SystemReset();
}

// Communication functions
void HAL_SerialPrint(const char* message) {
  Serial.print(message);
}

void HAL_SerialPrintln(const char* message) {
  Serial.println(message);
}

bool HAL_SerialAvailable() {
  return Serial.available() > 0;
}

char HAL_SerialRead() {
  if (Serial.available()) {
    return Serial.read();
  }
  return 0;
}

// Configuration and status functions
void HAL_SetConfig(const HAL_Config_t* config) {
  halConfig = *config;

  // Apply configuration changes
  if (config->gpsBaudRate == 1) {
    Serial1.begin(19200);
  } else if (config->gpsBaudRate == 2) {
    Serial1.begin(38400);
  } else {
    Serial1.begin(9600);
  }

  Serial.println(F("[HAL] Configuration updated"));
}

void HAL_GetConfig(HAL_Config_t* config) {
  *config = halConfig;
}

void HAL_GetStatus(HAL_Status_t* status) {
  halStatus.systemUptime = millis();
  halStatus.freeMemory = HAL_GetFreeMemory();
  *status = halStatus;
}

// Diagnostic functions
bool HAL_TestServo() {
  Serial.println(F("[HAL] Testing servo..."));

  // Test servo by moving through range
  HAL_SetServoMicroseconds(halConfig.servoCenterPulse);
  delay(500);
  HAL_SetServoMicroseconds(halConfig.servoMinPulse);
  delay(500);
  HAL_SetServoMicroseconds(halConfig.servoMaxPulse);
  delay(500);
  HAL_SetServoMicroseconds(halConfig.servoCenterPulse);
  delay(500);

  halStatus.servoConnected = true;  // Assume success (no feedback)
  return true;
}

bool HAL_TestMotor() {
  Serial.println(F("[HAL] Testing motor..."));

  // Test motor at low speed
  HAL_SetMotorMicroseconds(halConfig.motorMinPulse + 50);
  delay(1000);
  HAL_SetMotorMicroseconds(halConfig.motorMinPulse);
  delay(500);

  halStatus.motorConnected = true;  // Assume success (no feedback)
  return true;
}

bool HAL_TestGPS() {
  Serial.println(F("[HAL] Testing GPS..."));

  uint32_t startTime = millis();
  bool dataReceived = false;

  // Wait for GPS data for 5 seconds
  while (millis() - startTime < 5000) {
    if (HAL_GPSAvailable()) {
      dataReceived = true;
      break;
    }
    delay(100);
  }

  halStatus.gpsConnected = dataReceived;

  if (dataReceived) {
    Serial.println(F("[HAL] GPS test: PASS"));
  } else {
    Serial.println(F("[HAL] GPS test: FAIL - No data received"));
  }

  return dataReceived;
}

bool HAL_TestButton() {
  Serial.println(F("[HAL] Testing button - press button within 5 seconds..."));

  uint32_t startTime = millis();
  bool buttonPressed = false;
  bool lastState = HAL_ReadButton();

  while (millis() - startTime < 5000) {
    bool currentState = HAL_ReadButton();
    if (currentState != lastState) {
      buttonPressed = true;
      break;
    }
    lastState = currentState;
    delay(50);
  }

  halStatus.buttonWorking = buttonPressed;

  if (buttonPressed) {
    Serial.println(F("[HAL] Button test: PASS"));
  } else {
    Serial.println(F("[HAL] Button test: FAIL - No button press detected"));
  }

  return buttonPressed;
}

bool HAL_TestLED() {
  Serial.println(F("[HAL] Testing LED..."));

  // Test LED with different colors
  HAL_SetLED(255, 0, 0);  // Red
  delay(500);
  HAL_SetLED(0, 255, 0);  // Green
  delay(500);
  HAL_SetLED(0, 0, 255);  // Blue
  delay(500);
  HAL_SetLED(0, 0, 0);    // Off

  halStatus.ledWorking = true;  // Assume success (no feedback)
  Serial.println(F("[HAL] LED test: PASS"));
  return true;
}

void HAL_RunDiagnostics() {
  Serial.println(F("[HAL] Running hardware diagnostics..."));

  HAL_TestLED();
  HAL_TestServo();
  HAL_TestGPS();

  // Button test is optional (requires user interaction)
  Serial.println(F("[HAL] Diagnostics complete"));

  // Print summary
  Serial.println(F("[HAL] Hardware Status:"));
  Serial.print(F("[HAL] GPS: "));
  Serial.println(halStatus.gpsConnected ? F("CONNECTED") : F("NOT CONNECTED"));
  Serial.print(F("[HAL] Servo: "));
  Serial.println(halStatus.servoConnected ? F("OK") : F("FAULT"));
  Serial.print(F("[HAL] Motor: "));
  Serial.println(halStatus.motorConnected ? F("OK") : F("FAULT"));
  Serial.print(F("[HAL] LED: "));
  Serial.println(halStatus.ledWorking ? F("OK") : F("FAULT"));
}

// Power management (basic implementations)
void HAL_EnterLowPowerMode() {
  // Basic low power mode for SAMD21
  Serial.println(F("[HAL] Entering low power mode"));
  // Implementation would use SAMD21 sleep modes
}

void HAL_ExitLowPowerMode() {
  Serial.println(F("[HAL] Exiting low power mode"));
}

void HAL_SetCPUFrequency(uint32_t frequency) {
  // SAMD21 CPU frequency adjustment
  Serial.print(F("[HAL] CPU frequency change requested: "));
  Serial.println(frequency);
  // Implementation would adjust SAMD21 clock settings
}

// Error handling
HAL_Error_t HAL_GetLastError() {
  return lastError;
}

void HAL_ClearError() {
  lastError = HAL_ERROR_NONE;
}

void HAL_SetErrorCallback(void (*callback)(HAL_Error_t error)) {
  errorCallback = callback;
}

// Internal error reporting function
void HAL_ReportError(HAL_Error_t error) {
  lastError = error;

  if (errorCallback != NULL) {
    errorCallback(error);
  }

  // Log error to serial
  Serial.print(F("[HAL] ERROR: "));
  switch (error) {
    case HAL_ERROR_GPS_TIMEOUT:
      Serial.println(F("GPS timeout"));
      break;
    case HAL_ERROR_SERVO_FAULT:
      Serial.println(F("Servo fault"));
      break;
    case HAL_ERROR_MOTOR_FAULT:
      Serial.println(F("Motor fault"));
      break;
    case HAL_ERROR_MEMORY_LOW:
      Serial.println(F("Low memory"));
      break;
    case HAL_ERROR_SYSTEM_FAULT:
      Serial.println(F("System fault"));
      break;
    default:
      Serial.println(F("Unknown error"));
      break;
  }
}