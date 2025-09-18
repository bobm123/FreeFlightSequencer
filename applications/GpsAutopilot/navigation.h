/*
 * navigation.h - Navigation Library Header
 *
 * GPS-based navigation and state estimation for GpsAutopilot.
 * Adapted from FreeFlight navigation library for Arduino platform.
 *
 * Hardware Limitations:
 * - GPS-only navigation (no IMU available)
 * - Position and heading derived from GPS data only
 * - No accelerometer-based attitude estimation
 */

#ifndef NAVIGATION_H
#define NAVIGATION_H

#include <Arduino.h>
#include "config.h"

// Function prototypes
void Nav_Init(const NavigationParams_t* params);
bool Nav_UpdateGPS(NavigationState_t* state);
bool Nav_Step(NavigationState_t* state, float deltaTime);
void Nav_SetDatum(NavigationState_t* state);
bool Nav_IsDatumSet(const NavigationState_t* state);
float Nav_ComputeTurnRadius(float rollAngle, float airspeed);
void Nav_ComputeRangeAndBearing(NavigationState_t* state);

// GPS parsing functions
bool GPS_ParseNMEA(const char* sentence, NavigationState_t* state);
bool GPS_ParseGGA(const char* sentence, NavigationState_t* state);
bool GPS_ParseRMC(const char* sentence, NavigationState_t* state);

// Coordinate conversion functions
void GPS_ConvertToMeters(double latDeg, double lonDeg, double datumLatDeg, double datumLonDeg,
                        float* northM, float* eastM);
double GPS_ConvertDMToDD(double degMin);
float GPS_CalculateDistance(double lat1, double lon1, double lat2, double lon2);
float GPS_CalculateBearing(double lat1, double lon1, double lat2, double lon2);

// Navigation state validation
bool Nav_ValidateGPSFix(const NavigationState_t* state);
bool Nav_ValidatePosition(const NavigationState_t* state);

#endif // NAVIGATION_H