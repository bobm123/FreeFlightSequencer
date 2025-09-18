/*
 * math_utils.h - Mathematical Utilities Header
 *
 * Mathematical functions and utilities for GpsAutopilot system.
 * Adapted from FreeFlight math library for Arduino platform.
 */

#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#include <Arduino.h>
#include <math.h>

// Mathematical constants
#define PI 3.14159265358979323846
#define TWO_PI (2.0 * PI)
#define HALF_PI (PI / 2.0)
#define RAD_TO_DEG (180.0 / PI)
#define DEG_TO_RAD (PI / 180.0)

// Earth constants
#define EARTH_RADIUS_M 6371000.0
#define GRAVITY_MPS2 9.81

// Angle mathematics
float ModAngle(float angle);
float ModAngle2Pi(float angle);
float AngleDifference(float angle1, float angle2);

// Coordinate turn calculations
float CoordTurn(float turnRate, float velocity);
float TurnRadius(float velocity, float bankAngle);

// Filtering functions
float LowPassFilter(float* state, float input, float timeConstant, float deltaTime);
float HighPassFilter(float* state, float* lastInput, float input, float timeConstant, float deltaTime);
float RateLimitFilter(float desired, float current, float maxRate, float deltaTime);

// Control utilities
float DeadBand(float input, float deadband);
float Saturate(float input, float min, float max);
float Hysteresis(float input, float threshold, bool* state);

// Vector mathematics
typedef struct {
    float x;
    float y;
    float z;
} Vector3_t;

typedef struct {
    float x;
    float y;
} Vector2_t;

// Vector operations
float Vector2_Magnitude(const Vector2_t* v);
float Vector2_Angle(const Vector2_t* v);
void Vector2_Normalize(Vector2_t* v);
float Vector2_Dot(const Vector2_t* a, const Vector2_t* b);
void Vector2_Rotate(Vector2_t* v, float angle);

float Vector3_Magnitude(const Vector3_t* v);
void Vector3_Normalize(Vector3_t* v);
float Vector3_Dot(const Vector3_t* a, const Vector3_t* b);
void Vector3_Cross(const Vector3_t* a, const Vector3_t* b, Vector3_t* result);

// Geodetic calculations
void GeodeticToENU(double lat, double lon, double alt,
                   double refLat, double refLon, double refAlt,
                   float* east, float* north, float* up);
void ENUToGeodetic(float east, float north, float up,
                   double refLat, double refLon, double refAlt,
                   double* lat, double* lon, double* alt);
float GreatCircleDistance(double lat1, double lon1, double lat2, double lon2);
float GreatCircleBearing(double lat1, double lon1, double lat2, double lon2);

// Interpolation functions
float LinearInterp(float x, float x1, float y1, float x2, float y2);
float BilinearInterp(float x, float y, float x1, float x2, float y1, float y2,
                     float q11, float q12, float q21, float q22);

// Statistics functions
typedef struct {
    float sum;
    float sumSquares;
    uint32_t count;
    float mean;
    float variance;
    float stdDev;
} Statistics_t;

void Stats_Init(Statistics_t* stats);
void Stats_AddSample(Statistics_t* stats, float sample);
void Stats_Compute(Statistics_t* stats);
void Stats_Reset(Statistics_t* stats);

// Circular buffer for running statistics
#define CIRCULAR_BUFFER_SIZE 32

typedef struct {
    float buffer[CIRCULAR_BUFFER_SIZE];
    uint32_t index;
    uint32_t count;
    float sum;
    bool full;
} CircularBuffer_t;

void CircularBuffer_Init(CircularBuffer_t* cb);
void CircularBuffer_Add(CircularBuffer_t* cb, float value);
float CircularBuffer_Mean(const CircularBuffer_t* cb);
float CircularBuffer_Variance(const CircularBuffer_t* cb);

// Fast math approximations
float FastSin(float x);
float FastCos(float x);
float FastAtan2(float y, float x);
float FastSqrt(float x);

// Lookup table utilities
float LookupTable1D(const float* table, const float* inputs, int size, float input);
float LookupTable2D(const float* table, const float* xInputs, const float* yInputs,
                    int xSize, int ySize, float x, float y);

#endif // MATH_UTILS_H