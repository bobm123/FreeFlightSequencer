/*
 * board_config.h - Multi-board hardware abstraction for FlightSequencer
 *
 * Supports Adafruit Qt Py SAMD21 and ESP32-S3 with Signal Distribution MkII
 */

#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

// Board identification and configuration
#if defined(ADAFRUIT_QTPY_M0) || defined(ARDUINO_SAMD_QTPY_M0)
  #define BOARD_NAME "Adafruit Qt Py SAMD21"
  #define BOARD_TYPE_SAMD21
  #define HAS_FLASH_STORAGE 1
  #define HAS_NEOPIXEL 1
  #define HAS_HARDWARE_SERIAL 1
  #define MEMORY_FLASH_KB 256
  #define MEMORY_RAM_KB 32

#elif defined(ADAFRUIT_QTPY_ESP32S2) || defined(ARDUINO_ADAFRUIT_QTPY_ESP32S2)
  #define BOARD_NAME "Adafruit Qt Py ESP32-S2"
  #define BOARD_TYPE_ESP32S2
  #define HAS_PREFERENCES 1
  #define HAS_NEOPIXEL 1
  #define HAS_HARDWARE_SERIAL 1
  #define HAS_WIFI 1
  #define MEMORY_FLASH_KB 4096
  #define MEMORY_RAM_KB 320

#elif defined(ARDUINO_ARCH_SAMD)
  #define BOARD_NAME "SAMD21 Compatible Board"
  #define BOARD_TYPE_SAMD21
  #define HAS_FLASH_STORAGE 1
  #define HAS_NEOPIXEL 1
  #define HAS_HARDWARE_SERIAL 1
  #define MEMORY_FLASH_KB 256
  #define MEMORY_RAM_KB 32

#elif defined(ARDUINO_ARCH_CH32V)
  #define BOARD_NAME "Adafruit Qt Py CH32V203"
  #define BOARD_TYPE_CH32V203
  #define HAS_FLASH_STORAGE 1
  #define HAS_NEOPIXEL 1
  #define HAS_HARDWARE_SERIAL 1
  #define MEMORY_FLASH_KB 256
  #define MEMORY_RAM_KB 10

#elif defined(ARDUINO_ARCH_ESP32)
  #define BOARD_NAME "ESP32 Compatible Board"
  #define BOARD_TYPE_ESP32
  #define HAS_PREFERENCES 1
  #define HAS_NEOPIXEL 1
  #define HAS_HARDWARE_SERIAL 1
  #define HAS_WIFI 1
  #define HAS_BLUETOOTH 1
  #define MEMORY_FLASH_KB 4096
  #define MEMORY_RAM_KB 512

#else
  #error "Unsupported board - please add board configuration"
#endif

// Pin assignments (same for both Qt Py boards via Signal Distribution MkII)
#define DT_SERVO_PIN       A3    // Dethermalizer servo (CH1 connector)
#define MOTOR_SERVO_PIN    A2    // Motor ESC (ESC0 connector)
#define BUTTON_PIN         A0    // Push button (onboard switch)

// NeoPixel pin - use board-specific definition if available
#if defined(PIN_NEOPIXEL)
  #define NEOPIXEL_PIN     PIN_NEOPIXEL  // Board-specific NeoPixel pin
#else
  #define NEOPIXEL_PIN     11            // Fallback for older board definitions
#endif

// Board-specific includes
#ifdef HAS_FLASH_STORAGE
  #include <FlashStorage.h>
#endif

#ifdef HAS_PREFERENCES
  #include <Preferences.h>
#endif

// Servo library selection based on architecture
#if defined(ARDUINO_ARCH_ESP32)
  #include <ESP32Servo.h>
#else
  #include <Servo.h>
#endif

// Always include these
#include <Adafruit_NeoPixel.h>

#endif // BOARD_CONFIG_H