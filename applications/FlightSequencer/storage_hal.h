/*
 * storage_hal.h - Storage Hardware Abstraction Layer
 *
 * Provides unified parameter storage interface across SAMD21 (FlashStorage)
 * and ESP32-S3 (Preferences) platforms
 */

#ifndef STORAGE_HAL_H
#define STORAGE_HAL_H

#include "board_config.h"

// Forward declaration of FlightParameters struct
struct FlightParameters;

// Storage abstraction functions - implementation in main .ino file
bool initStorage();
FlightParameters loadParametersFromStorage();
bool saveParametersToStorage(const FlightParameters& params);
bool isStorageValid();

#endif // STORAGE_HAL_H