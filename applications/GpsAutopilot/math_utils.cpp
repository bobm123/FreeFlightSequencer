/*
 * math_utils.cpp - Mathematical Utilities Implementation
 *
 * Mathematical functions and utilities for flight control calculations.
 */

#include "math_utils.h"

// Angle mathematics
float ModAngle(float angle) {
  // Normalize angle to +/-pi range
  while (angle > PI) {
    angle -= TWO_PI;
  }
  while (angle < -PI) {
    angle += TWO_PI;
  }
  return angle;
}

float ModAngle2Pi(float angle) {
  // Normalize angle to 0-2*pi range
  while (angle >= TWO_PI) {
    angle -= TWO_PI;
  }
  while (angle < 0.0) {
    angle += TWO_PI;
  }
  return angle;
}

float AngleDifference(float angle1, float angle2) {
  // Compute the smallest angle difference between two angles
  float diff = angle2 - angle1;
  return ModAngle(diff);
}

// Coordinate turn calculations
float CoordTurn(float turnRate, float velocity) {
  // Calculate bank angle for coordinated turn
  // phi = atan(V * turnRate / g)
  if (velocity <= 0.0) {
    return 0.0;
  }

  float bankAngle = atan((velocity * turnRate) / GRAVITY_MPS2);
  return Saturate(bankAngle, -PI/3, PI/3); // Limit to +/-60 degrees
}

float TurnRadius(float velocity, float bankAngle) {
  // Calculate turn radius for given velocity and bank angle
  // R = V^2 / (g * tan(phi))
  if (fabs(bankAngle) < 0.01) {
    return 999999.0; // Very large radius for small bank angles
  }

  float radius = (velocity * velocity) / (GRAVITY_MPS2 * tan(fabs(bankAngle)));
  return radius;
}

// Filtering functions
float LowPassFilter(float* state, float input, float timeConstant, float deltaTime) {
  // First-order low-pass filter
  if (timeConstant <= 0.0 || deltaTime <= 0.0) {
    return input;
  }

  float alpha = deltaTime / (timeConstant + deltaTime);
  *state = *state + alpha * (input - *state);
  return *state;
}

float HighPassFilter(float* state, float* lastInput, float input, float timeConstant, float deltaTime) {
  // First-order high-pass filter
  if (timeConstant <= 0.0 || deltaTime <= 0.0) {
    return input - *lastInput;
  }

  float alpha = timeConstant / (timeConstant + deltaTime);
  *state = alpha * (*state + input - *lastInput);
  *lastInput = input;
  return *state;
}

float RateLimitFilter(float desired, float current, float maxRate, float deltaTime) {
  // Rate limiting filter
  if (maxRate <= 0.0 || deltaTime <= 0.0) {
    return desired;
  }

  float error = desired - current;
  float maxChange = maxRate * deltaTime;

  if (error > maxChange) {
    return current + maxChange;
  } else if (error < -maxChange) {
    return current - maxChange;
  } else {
    return desired;
  }
}

// Control utilities
float DeadBand(float input, float deadband) {
  // Apply deadband to input
  if (fabs(input) < deadband) {
    return 0.0;
  } else if (input > 0.0) {
    return input - deadband;
  } else {
    return input + deadband;
  }
}

float Saturate(float input, float min, float max) {
  // Saturate input to min/max limits
  if (input < min) {
    return min;
  } else if (input > max) {
    return max;
  } else {
    return input;
  }
}

float Hysteresis(float input, float threshold, bool* state) {
  // Hysteresis function with state memory
  if (!*state && input > threshold) {
    *state = true;
  } else if (*state && input < -threshold) {
    *state = false;
  }
  return *state ? 1.0 : 0.0;
}

// Vector mathematics - 2D
float Vector2_Magnitude(const Vector2_t* v) {
  return sqrt(v->x * v->x + v->y * v->y);
}

float Vector2_Angle(const Vector2_t* v) {
  return atan2(v->y, v->x);
}

void Vector2_Normalize(Vector2_t* v) {
  float mag = Vector2_Magnitude(v);
  if (mag > 0.0) {
    v->x /= mag;
    v->y /= mag;
  }
}

float Vector2_Dot(const Vector2_t* a, const Vector2_t* b) {
  return a->x * b->x + a->y * b->y;
}

void Vector2_Rotate(Vector2_t* v, float angle) {
  float cos_a = cos(angle);
  float sin_a = sin(angle);
  float x = v->x * cos_a - v->y * sin_a;
  float y = v->x * sin_a + v->y * cos_a;
  v->x = x;
  v->y = y;
}

// Vector mathematics - 3D
float Vector3_Magnitude(const Vector3_t* v) {
  return sqrt(v->x * v->x + v->y * v->y + v->z * v->z);
}

void Vector3_Normalize(Vector3_t* v) {
  float mag = Vector3_Magnitude(v);
  if (mag > 0.0) {
    v->x /= mag;
    v->y /= mag;
    v->z /= mag;
  }
}

float Vector3_Dot(const Vector3_t* a, const Vector3_t* b) {
  return a->x * b->x + a->y * b->y + a->z * b->z;
}

void Vector3_Cross(const Vector3_t* a, const Vector3_t* b, Vector3_t* result) {
  result->x = a->y * b->z - a->z * b->y;
  result->y = a->z * b->x - a->x * b->z;
  result->z = a->x * b->y - a->y * b->x;
}

// Geodetic calculations
void GeodeticToENU(double lat, double lon, double alt,
                   double refLat, double refLon, double refAlt,
                   float* east, float* north, float* up) {
  // Convert geodetic coordinates to East-North-Up local frame
  double dLat = (lat - refLat) * DEG_TO_RAD;
  double dLon = (lon - refLon) * DEG_TO_RAD;
  double dAlt = alt - refAlt;

  // Approximate conversion for small distances
  double cosLat = cos(refLat * DEG_TO_RAD);

  *north = dLat * EARTH_RADIUS_M;
  *east = dLon * EARTH_RADIUS_M * cosLat;
  *up = dAlt;
}

void ENUToGeodetic(float east, float north, float up,
                   double refLat, double refLon, double refAlt,
                   double* lat, double* lon, double* alt) {
  // Convert East-North-Up coordinates to geodetic
  double cosLat = cos(refLat * DEG_TO_RAD);

  double dLat = north / EARTH_RADIUS_M;
  double dLon = east / (EARTH_RADIUS_M * cosLat);

  *lat = refLat + dLat * RAD_TO_DEG;
  *lon = refLon + dLon * RAD_TO_DEG;
  *alt = refAlt + up;
}

float GreatCircleDistance(double lat1, double lon1, double lat2, double lon2) {
  // Haversine formula for great circle distance
  double dLat = (lat2 - lat1) * DEG_TO_RAD;
  double dLon = (lon2 - lon1) * DEG_TO_RAD;
  double a = sin(dLat/2) * sin(dLat/2) +
            cos(lat1 * DEG_TO_RAD) * cos(lat2 * DEG_TO_RAD) *
            sin(dLon/2) * sin(dLon/2);
  double c = 2 * atan2(sqrt(a), sqrt(1-a));
  return EARTH_RADIUS_M * c;
}

float GreatCircleBearing(double lat1, double lon1, double lat2, double lon2) {
  // Calculate bearing from point 1 to point 2
  double dLon = (lon2 - lon1) * DEG_TO_RAD;
  double lat1Rad = lat1 * DEG_TO_RAD;
  double lat2Rad = lat2 * DEG_TO_RAD;

  double y = sin(dLon) * cos(lat2Rad);
  double x = cos(lat1Rad) * sin(lat2Rad) - sin(lat1Rad) * cos(lat2Rad) * cos(dLon);

  double bearing = atan2(y, x);
  return ModAngle(bearing);
}

// Interpolation functions
float LinearInterp(float x, float x1, float y1, float x2, float y2) {
  if (fabs(x2 - x1) < 1e-6) {
    return y1;
  }
  return y1 + (y2 - y1) * (x - x1) / (x2 - x1);
}

float BilinearInterp(float x, float y, float x1, float x2, float y1, float y2,
                     float q11, float q12, float q21, float q22) {
  float r1 = LinearInterp(x, x1, q11, x2, q21);
  float r2 = LinearInterp(x, x1, q12, x2, q22);
  return LinearInterp(y, y1, r1, y2, r2);
}

// Statistics functions
void Stats_Init(Statistics_t* stats) {
  stats->sum = 0.0;
  stats->sumSquares = 0.0;
  stats->count = 0;
  stats->mean = 0.0;
  stats->variance = 0.0;
  stats->stdDev = 0.0;
}

void Stats_AddSample(Statistics_t* stats, float sample) {
  stats->sum += sample;
  stats->sumSquares += sample * sample;
  stats->count++;
}

void Stats_Compute(Statistics_t* stats) {
  if (stats->count > 0) {
    stats->mean = stats->sum / stats->count;

    if (stats->count > 1) {
      stats->variance = (stats->sumSquares - stats->sum * stats->mean) / (stats->count - 1);
      stats->stdDev = sqrt(stats->variance);
    } else {
      stats->variance = 0.0;
      stats->stdDev = 0.0;
    }
  }
}

void Stats_Reset(Statistics_t* stats) {
  Stats_Init(stats);
}

// Circular buffer functions
void CircularBuffer_Init(CircularBuffer_t* cb) {
  cb->index = 0;
  cb->count = 0;
  cb->sum = 0.0;
  cb->full = false;

  for (int i = 0; i < CIRCULAR_BUFFER_SIZE; i++) {
    cb->buffer[i] = 0.0;
  }
}

void CircularBuffer_Add(CircularBuffer_t* cb, float value) {
  if (cb->full) {
    cb->sum -= cb->buffer[cb->index];
  } else {
    cb->count++;
    if (cb->count == CIRCULAR_BUFFER_SIZE) {
      cb->full = true;
    }
  }

  cb->buffer[cb->index] = value;
  cb->sum += value;

  cb->index = (cb->index + 1) % CIRCULAR_BUFFER_SIZE;
}

float CircularBuffer_Mean(const CircularBuffer_t* cb) {
  if (cb->count == 0) {
    return 0.0;
  }
  return cb->sum / cb->count;
}

float CircularBuffer_Variance(const CircularBuffer_t* cb) {
  if (cb->count < 2) {
    return 0.0;
  }

  float mean = CircularBuffer_Mean(cb);
  float sumSquares = 0.0;

  for (int i = 0; i < cb->count; i++) {
    float diff = cb->buffer[i] - mean;
    sumSquares += diff * diff;
  }

  return sumSquares / (cb->count - 1);
}

// Fast math approximations
float FastSin(float x) {
  // Fast sine approximation using Taylor series
  x = ModAngle(x);
  float x2 = x * x;
  return x * (1.0 - x2 / 6.0 * (1.0 - x2 / 20.0));
}

float FastCos(float x) {
  // Fast cosine approximation
  return FastSin(x + HALF_PI);
}

float FastAtan2(float y, float x) {
  // Fast atan2 approximation
  if (x == 0.0) {
    return (y > 0.0) ? HALF_PI : -HALF_PI;
  }

  float atan = y / x;
  if (fabs(x) > fabs(y)) {
    atan = atan / (1.0 + 0.28 * atan * atan);
    if (x < 0.0) {
      atan += (y < 0.0) ? -PI : PI;
    }
  } else {
    atan = HALF_PI - atan / (atan * atan + 0.28);
    if (y < 0.0) {
      atan -= PI;
    }
  }

  return atan;
}

float FastSqrt(float x) {
  // Fast square root using Newton-Raphson
  if (x <= 0.0) {
    return 0.0;
  }

  float guess = x * 0.5;
  for (int i = 0; i < 3; i++) {
    guess = 0.5 * (guess + x / guess);
  }

  return guess;
}

// Lookup table utilities
float LookupTable1D(const float* table, const float* inputs, int size, float input) {
  // 1D linear interpolation lookup table
  if (size < 2) {
    return (size == 1) ? table[0] : 0.0;
  }

  // Check bounds
  if (input <= inputs[0]) {
    return table[0];
  }
  if (input >= inputs[size-1]) {
    return table[size-1];
  }

  // Find interpolation indices
  for (int i = 0; i < size-1; i++) {
    if (input >= inputs[i] && input <= inputs[i+1]) {
      return LinearInterp(input, inputs[i], table[i], inputs[i+1], table[i+1]);
    }
  }

  return table[size-1];
}

float LookupTable2D(const float* table, const float* xInputs, const float* yInputs,
                    int xSize, int ySize, float x, float y) {
  // 2D bilinear interpolation lookup table
  if (xSize < 2 || ySize < 2) {
    return 0.0;
  }

  // Find x indices
  int x1_idx = 0, x2_idx = xSize - 1;
  for (int i = 0; i < xSize - 1; i++) {
    if (x >= xInputs[i] && x <= xInputs[i+1]) {
      x1_idx = i;
      x2_idx = i + 1;
      break;
    }
  }

  // Find y indices
  int y1_idx = 0, y2_idx = ySize - 1;
  for (int i = 0; i < ySize - 1; i++) {
    if (y >= yInputs[i] && y <= yInputs[i+1]) {
      y1_idx = i;
      y2_idx = i + 1;
      break;
    }
  }

  // Get corner values
  float q11 = table[y1_idx * xSize + x1_idx];
  float q12 = table[y2_idx * xSize + x1_idx];
  float q21 = table[y1_idx * xSize + x2_idx];
  float q22 = table[y2_idx * xSize + x2_idx];

  // Perform bilinear interpolation
  return BilinearInterp(x, y,
                       xInputs[x1_idx], xInputs[x2_idx],
                       yInputs[y1_idx], yInputs[y2_idx],
                       q11, q12, q21, q22);
}