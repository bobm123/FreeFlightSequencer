/*
 * communications.h - Communications Library Header
 *
 * Parameter management and basic data logging for GpsAutopilot.
 * Adapted from FreeFlight communications for Arduino Serial interface.
 *
 * Hardware Limitations:
 * - No real-time telemetry hardware available
 * - Serial-based parameter configuration only
 * - Local data logging capabilities
 */

#ifndef COMMUNICATIONS_H
#define COMMUNICATIONS_H

#include <Arduino.h>
#include "config.h"

// Message types for data logging
typedef enum {
  MSG_NAV_STATE = 1,
  MSG_CONTROL_STATE = 2,
  MSG_GPS_RAW = 3,
  MSG_SYSTEM_STATUS = 4,
  MSG_PARAMETER_UPDATE = 5
} MessageType_t;

// System status structure
typedef struct {
  uint32_t uptime;
  uint8_t flightState;
  bool gpsValid;
  bool datumSet;
  bool autonomousMode;
  float batteryVoltage;
  uint32_t freeMemory;
} SystemStatus_t;

// Function prototypes
void Coms_Init();
void Coms_Step();
void Coms_LogData(MessageType_t msgType, const void* data, uint8_t dataSize);
void Coms_LogNavigationState(const NavigationState_t* navState);
void Coms_LogControlState(const ControlState_t* controlState);
void Coms_LogSystemStatus(const SystemStatus_t* status);

// Parameter management functions
bool Coms_UpdateNavigationParams(const NavigationParams_t* params);
bool Coms_UpdateControlParams(const ControlParams_t* params);
bool Coms_UpdateActuatorParams(const ActuatorParams_t* params);

// Serial interface functions
void Coms_ProcessSerialCommand();
void Coms_SendStatus();
void Coms_SendParameters();

// Data formatting functions
void Coms_FormatNavData(const NavigationState_t* navState, char* buffer, size_t bufferSize);
void Coms_FormatControlData(const ControlState_t* controlState, char* buffer, size_t bufferSize);

// Utility functions
uint32_t Coms_GetFreeMemory();
float Coms_GetBatteryVoltage();

#endif // COMMUNICATIONS_H