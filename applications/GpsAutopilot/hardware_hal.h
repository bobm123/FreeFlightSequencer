/*
 * hardware_hal.h - Hardware Abstraction Layer Header
 *
 * Hardware abstraction layer for GpsAutopilot on QtPY SAMD21
 * with Signal Distribution MkII carrier board.
 *
 * Hardware Configuration:
 * - QtPY SAMD21: 48MHz ARM Cortex-M0+, 256KB Flash, 32KB RAM
 * - GPS Module: UART interface (Serial1)
 * - Roll Servo: PWM output (pin A3)
 * - Motor ESC: PWM output (pin A2)
 * - Button: Digital input with pullup (pin A0)
 * - NeoPixel LED: Digital output (pin 11)
 */

#ifndef HARDWARE_HAL_H
#define HARDWARE_HAL_H

#include <Arduino.h>
#include "config.h"

// Hardware initialization
void HAL_Init();

// GPS interface functions
uint32_t HAL_ReadGPS(uint8_t* buffer, uint32_t maxBytes);
bool HAL_GPSAvailable();
char HAL_ReadGPSChar();

// Servo/ESC control functions
void HAL_SetServoPosition(float rollCommand);    // Roll servo control (-1.0 to +1.0)
void HAL_SetMotorSpeed(float throttleCommand);   // Motor ESC control (0.0 to 1.0)
void HAL_SetServoMicroseconds(uint16_t microseconds);  // Direct servo control
void HAL_SetMotorMicroseconds(uint16_t microseconds);  // Direct motor control

// Digital I/O functions
bool HAL_ReadButton();
void HAL_SetLED(uint8_t red, uint8_t green, uint8_t blue);
void HAL_ToggleLED();

// Analog input functions
float HAL_ReadBatteryVoltage();
float HAL_ReadAnalogPin(uint8_t pin);

// Timing functions
bool HAL_ClockMainLoop(float* deltaTime);       // 50Hz main loop timing
uint32_t HAL_GetSystemTime();                   // System time in milliseconds
void HAL_DelayMicroseconds(uint32_t microseconds);
void HAL_DelayMilliseconds(uint32_t milliseconds);

// System information functions
uint32_t HAL_GetFreeMemory();
float HAL_GetCPUUsage();
void HAL_SystemReset();

// Communication functions
void HAL_SerialPrint(const char* message);
void HAL_SerialPrintln(const char* message);
bool HAL_SerialAvailable();
char HAL_SerialRead();

// Hardware configuration
typedef struct {
    uint16_t servoMinPulse;     // Minimum servo pulse width (us)
    uint16_t servoMaxPulse;     // Maximum servo pulse width (us)
    uint16_t servoCenterPulse;  // Center servo pulse width (us)
    uint16_t motorMinPulse;     // Minimum motor pulse width (us)
    uint16_t motorMaxPulse;     // Maximum motor pulse width (us)
    uint8_t gpsBaudRate;        // GPS baud rate (index: 0=9600, 1=19200, 2=38400)
    bool buttonInverted;        // Button logic inversion
    float batteryScale;         // Battery voltage scaling factor
} HAL_Config_t;

// Hardware status
typedef struct {
    bool gpsConnected;
    bool servoConnected;
    bool motorConnected;
    bool buttonWorking;
    bool ledWorking;
    uint32_t systemUptime;
    float cpuUsage;
    uint32_t freeMemory;
} HAL_Status_t;

// Configuration and status functions
void HAL_SetConfig(const HAL_Config_t* config);
void HAL_GetConfig(HAL_Config_t* config);
void HAL_GetStatus(HAL_Status_t* status);

// Diagnostic functions
bool HAL_TestServo();
bool HAL_TestMotor();
bool HAL_TestGPS();
bool HAL_TestButton();
bool HAL_TestLED();
void HAL_RunDiagnostics();

// Power management
void HAL_EnterLowPowerMode();
void HAL_ExitLowPowerMode();
void HAL_SetCPUFrequency(uint32_t frequency);

// Error handling
typedef enum {
    HAL_ERROR_NONE = 0,
    HAL_ERROR_GPS_TIMEOUT,
    HAL_ERROR_SERVO_FAULT,
    HAL_ERROR_MOTOR_FAULT,
    HAL_ERROR_MEMORY_LOW,
    HAL_ERROR_SYSTEM_FAULT
} HAL_Error_t;

HAL_Error_t HAL_GetLastError();
void HAL_ClearError();
void HAL_SetErrorCallback(void (*callback)(HAL_Error_t error));

#endif // HARDWARE_HAL_H