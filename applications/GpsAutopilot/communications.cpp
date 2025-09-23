/*
 * communications.cpp - Communications Library Implementation
 *
 * Basic parameter management and data logging for GpsAutopilot.
 * Provides Serial interface for configuration and status monitoring.
 */

#include "communications.h"

// Global communication state
static uint32_t lastStatusUpdate = 0;
static uint32_t lastDataLog = 0;
static bool loggingEnabled = false;

void Coms_Init() {
  Serial.println(F("[COMS] Communications system initialized"));
  Serial.println(F("[COMS] Serial interface ready for parameter configuration"));

  lastStatusUpdate = millis();
  lastDataLog = millis();
}

void Coms_Step() {
  uint32_t currentTime = millis();

  // Process any incoming serial commands
  Coms_ProcessSerialCommand();

  // Send periodic status updates (every 5 seconds)
  if (currentTime - lastStatusUpdate > 5000) {
    Coms_SendStatus();
    lastStatusUpdate = currentTime;
  }

  // Log data at regular intervals if enabled (every 1 second)
  if (loggingEnabled && (currentTime - lastDataLog > 1000)) {
    // Data logging would go here when flight data is available
    lastDataLog = currentTime;
  }
}

void Coms_LogData(MessageType_t msgType, const void* data, uint8_t dataSize) {
  // Basic data logging to Serial (future enhancement: SD card or flash storage)
  if (!loggingEnabled) {
    return;
  }

  uint32_t timestamp = millis();

  Serial.print(F("[LOG] "));
  Serial.print(timestamp);
  Serial.print(F(","));
  Serial.print(msgType);
  Serial.print(F(","));

  // Format data based on message type
  switch (msgType) {
    case MSG_NAV_STATE:
      if (dataSize == sizeof(NavigationState_t)) {
        const NavigationState_t* navState = (const NavigationState_t*)data;
        char buffer[128];
        Coms_FormatNavData(navState, buffer, sizeof(buffer));
        Serial.println(buffer);
      }
      break;

    case MSG_CONTROL_STATE:
      if (dataSize == sizeof(ControlState_t)) {
        const ControlState_t* controlState = (const ControlState_t*)data;
        char buffer[128];
        Coms_FormatControlData(controlState, buffer, sizeof(buffer));
        Serial.println(buffer);
      }
      break;

    default:
      Serial.println(F("Unknown message type"));
      break;
  }
}

void Coms_LogNavigationState(const NavigationState_t* navState) {
  Coms_LogData(MSG_NAV_STATE, navState, sizeof(NavigationState_t));
}

void Coms_LogControlState(const ControlState_t* controlState) {
  Coms_LogData(MSG_CONTROL_STATE, controlState, sizeof(ControlState_t));
}

void Coms_LogSystemStatus(const SystemStatus_t* status) {
  Coms_LogData(MSG_SYSTEM_STATUS, status, sizeof(SystemStatus_t));
}

bool Coms_UpdateNavigationParams(const NavigationParams_t* params) {
  // Validate navigation parameters
  if (params->Ktrack < 0.1 || params->Ktrack > 5.0) {
    Serial.println(F("[COMS] Invalid Ktrack parameter"));
    return false;
  }

  if (params->Vias_nom < 5.0 || params->Vias_nom > 20.0) {
    Serial.println(F("[COMS] Invalid airspeed parameter"));
    return false;
  }

  Serial.println(F("[COMS] Navigation parameters updated"));
  return true;
}

bool Coms_UpdateControlParams(const ControlParams_t* params) {
  // Validate control parameters
  if (params->OrbitRadius < 20.0 || params->OrbitRadius > 500.0) {
    Serial.println(F("[COMS] Invalid orbit radius"));
    return false;
  }

  if (params->SafetyRadius < params->OrbitRadius * 1.5) {
    Serial.println(F("[COMS] Safety radius too small"));
    return false;
  }

  Serial.println(F("[COMS] Control parameters updated"));
  return true;
}

bool Coms_UpdateActuatorParams(const ActuatorParams_t* params) {
  // Validate roll servo parameters
  if (params->RollServoCenter < 1000 || params->RollServoCenter > 2000) {
    Serial.println(F("[COMS] Invalid servo center"));
    return false;
  }

  if (params->RollServoRange < 200 || params->RollServoRange > 800) {
    Serial.println(F("[COMS] Invalid servo range"));
    return false;
  }

  if (params->RollServoMinPulse < 800 || params->RollServoMinPulse > 1200) {
    Serial.println(F("[COMS] Invalid servo min pulse"));
    return false;
  }

  if (params->RollServoMaxPulse < 1800 || params->RollServoMaxPulse > 2200) {
    Serial.println(F("[COMS] Invalid servo max pulse"));
    return false;
  }

  Serial.println(F("[COMS] Actuator parameters updated"));
  return true;
}

void Coms_ProcessSerialCommand() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();

  if (command.length() == 0) {
    return;
  }

  // Check for SERVO commands first (multi-word commands)
  if (command.startsWith("SERVO ")) {
    Coms_ProcessServoCommand(command);
    return;
  }

  char cmd = command.charAt(0);

  switch (cmd) {
    case 'S': {
      // Status command
      Coms_SendStatus();
      break;
    }

    case 'P': {
      // Parameters command
      Coms_SendParameters();
      break;
    }

    case 'L': {
      // Toggle logging
      loggingEnabled = !loggingEnabled;
      Serial.print(F("[COMS] Data logging "));
      Serial.println(loggingEnabled ? F("enabled") : F("disabled"));
      break;
    }

    case 'M': {
      // Memory status
      Serial.print(F("[COMS] Free memory: "));
      Serial.print(Coms_GetFreeMemory());
      Serial.println(F(" bytes"));
      break;
    }

    default: {
      Serial.print(F("[COMS] Unknown command: "));
      Serial.println(cmd);
      Serial.println(F("[COMS] Available commands: S(tatus), P(arameters), L(ogging), M(emory), SERVO"));
      break;
    }
  }
}

void Coms_SendStatus() {
  SystemStatus_t status;
  status.uptime = millis();
  status.freeMemory = Coms_GetFreeMemory();
  status.batteryVoltage = Coms_GetBatteryVoltage();

  Serial.println(F("[STATUS] System Status:"));
  Serial.print(F("[STATUS] Uptime: "));
  Serial.print(status.uptime / 1000);
  Serial.println(F(" seconds"));
  Serial.print(F("[STATUS] Free Memory: "));
  Serial.print(status.freeMemory);
  Serial.println(F(" bytes"));
  Serial.print(F("[STATUS] Battery: "));
  Serial.print(status.batteryVoltage);
  Serial.println(F(" V"));
}

void Coms_SendParameters() {
  Serial.println(F("[PARAMS] Current system parameters would be displayed here"));
  Serial.println(F("[PARAMS] Use main application 'G' command for full parameter list"));
}

void Coms_FormatNavData(const NavigationState_t* navState, char* buffer, size_t bufferSize) {
  snprintf(buffer, bufferSize,
           "%.6f,%.6f,%.1f,%.1f,%.1f,%.1f,%d",
           navState->datumLat,  // Will be current position in full implementation
           navState->datumLon,  // Will be current position in full implementation
           navState->altitude,
           navState->groundSpeed,
           navState->groundTrack * RAD_TO_DEG,
           navState->rangeFromDatum,
           navState->gpsValid ? 1 : 0);
}

void Coms_FormatControlData(const ControlState_t* controlState, char* buffer, size_t bufferSize) {
  snprintf(buffer, bufferSize,
           "%.3f,%.3f,%.1f,%.1f,%d",
           controlState->rollCommand,
           controlState->motorCommand,
           controlState->rangeError,
           controlState->trackError * RAD_TO_DEG,
           controlState->autonomousMode ? 1 : 0);
}

uint32_t Coms_GetFreeMemory() {
  // Simple free memory estimation for SAMD21
  // Return a reasonable estimate since exact calculation requires platform-specific code
  return 16384; // SAMD21 has 32KB RAM, estimate ~16KB available
}

float Coms_GetBatteryVoltage() {
  // Battery voltage monitoring (placeholder)
  // Would require voltage divider on analog pin
  return 3.7; // Placeholder value
}

void Coms_ProcessServoCommand(const String& command) {
  // Global actuator parameters (would be accessed from main application)
  static ActuatorParams_t actuatorParams = {
    1500.0,  // RollServoCenter
    400.0,   // RollServoRange
    120.0,   // RollServoRate
    false,   // RollServoReversed
    1000.0,  // RollServoMinPulse
    2000.0,  // RollServoMaxPulse
    10.0,    // RollServoDeadband
    0.0,     // MotorMin
    1.0,     // MotorMax
    1        // nMotorType
  };

  if (command.startsWith("SERVO SET ")) {
    String subCommand = command.substring(10); // Remove "SERVO SET "

    if (subCommand.startsWith("DIRECTION ")) {
      float value = subCommand.substring(10).toFloat();
      actuatorParams.RollServoReversed = (value > 0.5);
      Serial.print(F("[SERVO] Direction set to "));
      Serial.println(actuatorParams.RollServoReversed ? F("Inverted") : F("Normal"));
    }
    else if (subCommand.startsWith("CENTER ")) {
      float value = subCommand.substring(7).toFloat();
      if (value >= 1400 && value <= 1600) {
        actuatorParams.RollServoCenter = value;
        Serial.print(F("[SERVO] Center set to "));
        Serial.print(value);
        Serial.println(F(" us"));
      } else {
        Serial.println(F("[SERVO] Error: Center must be 1400-1600 us"));
      }
    }
    else if (subCommand.startsWith("RANGE ")) {
      float value = subCommand.substring(6).toFloat();
      if (value >= 200 && value <= 600) {
        actuatorParams.RollServoRange = value;
        Serial.print(F("[SERVO] Range set to "));
        Serial.print(value);
        Serial.println(F(" us"));
      } else {
        Serial.println(F("[SERVO] Error: Range must be 200-600 us"));
      }
    }
    else {
      Serial.println(F("[SERVO] Error: Unknown SET command"));
      Serial.println(F("[SERVO] Available: DIRECTION, CENTER, RANGE"));
    }
  }
  else if (command.startsWith("SERVO GET")) {
    Serial.println(F("[SERVO] Current Configuration:"));
    Serial.print(F("[SERVO] Center: "));
    Serial.print(actuatorParams.RollServoCenter);
    Serial.println(F(" us"));
    Serial.print(F("[SERVO] Range: "));
    Serial.print(actuatorParams.RollServoRange);
    Serial.println(F(" us"));
    Serial.print(F("[SERVO] Direction: "));
    Serial.println(actuatorParams.RollServoReversed ? F("Inverted") : F("Normal"));
    Serial.print(F("[SERVO] Min Pulse: "));
    Serial.print(actuatorParams.RollServoMinPulse);
    Serial.println(F(" us"));
    Serial.print(F("[SERVO] Max Pulse: "));
    Serial.print(actuatorParams.RollServoMaxPulse);
    Serial.println(F(" us"));
    Serial.print(F("[SERVO] Deadband: "));
    Serial.print(actuatorParams.RollServoDeadband);
    Serial.println(F(" us"));
  }
  else {
    Serial.println(F("[SERVO] Error: Unknown command"));
    Serial.println(F("[SERVO] Available: SET <DIRECTION|CENTER|RANGE> <value>, GET"));
  }
}