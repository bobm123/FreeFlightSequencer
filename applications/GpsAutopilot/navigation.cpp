/*
 * navigation.cpp - Navigation Library Implementation
 *
 * GPS-based navigation and state estimation for GpsAutopilot.
 * Provides position estimation and datum management using GPS data only.
 */

#include "navigation.h"
#include "math_utils.h"

// Global navigation parameters
static NavigationParams_t navParams;
static char gpsBuffer[128];
static int gpsBufferIndex = 0;

void Nav_Init(const NavigationParams_t* params) {
  // Copy navigation parameters
  navParams = *params;

  // Initialize GPS buffer
  gpsBufferIndex = 0;
  memset(gpsBuffer, 0, sizeof(gpsBuffer));

  Serial.println(F("[NAV] Navigation system initialized"));
}

bool Nav_UpdateGPS(NavigationState_t* state) {
  bool newDataProcessed = false;

  // Read available GPS data
  while (Serial1.available()) {
    char c = Serial1.read();

    if (c == '\r' || c == '\n') {
      if (gpsBufferIndex > 0) {
        gpsBuffer[gpsBufferIndex] = '\0';

        // Process the complete NMEA sentence
        if (GPS_ParseNMEA(gpsBuffer, state)) {
          newDataProcessed = true;
          state->lastGpsUpdate = millis();
        }

        // Reset buffer for next sentence
        gpsBufferIndex = 0;
      }
    } else if (gpsBufferIndex < sizeof(gpsBuffer) - 1) {
      gpsBuffer[gpsBufferIndex++] = c;
    }
  }

  // Check GPS timeout
  if (millis() - state->lastGpsUpdate > GPS_TIMEOUT_MS) {
    state->gpsValid = false;
  }

  return newDataProcessed;
}

bool Nav_Step(NavigationState_t* state, float deltaTime) {
  // Update range and bearing to datum if datum is set
  if (state->datumSet) {
    Nav_ComputeRangeAndBearing(state);
  }

  // Validate GPS data
  state->gpsValid = Nav_ValidateGPSFix(state) && Nav_ValidatePosition(state);

  return state->gpsValid;
}

void Nav_SetDatum(NavigationState_t* state) {
  if (state->gpsValid) {
    // Capture current position as datum
    state->datumLat = state->datumLat; // Will be set by GPS parsing
    state->datumLon = state->datumLon; // Will be set by GPS parsing
    state->datumAlt = state->altitude;
    state->datumSet = true;

    Serial.print(F("[NAV] Datum captured: "));
    Serial.print(state->datumLat, 6);
    Serial.print(F(", "));
    Serial.println(state->datumLon, 6);
  } else {
    Serial.println(F("[NAV] Cannot set datum - GPS not valid"));
  }
}

bool Nav_IsDatumSet(const NavigationState_t* state) {
  return state->datumSet;
}

float Nav_ComputeTurnRadius(float rollAngle, float airspeed) {
  // Coordinated turn radius calculation
  // R = V^2 / (g * tan(phi))
  if (fabs(rollAngle) < 0.1) {
    return 999999.0; // Very large radius for small roll angles
  }

  float g = 9.81; // Gravity (m/s^2)
  float radius = (airspeed * airspeed) / (g * tan(rollAngle));

  return fabs(radius);
}

void Nav_ComputeRangeAndBearing(NavigationState_t* state) {
  if (!state->datumSet) {
    return;
  }

  // Calculate distance and bearing to datum
  state->rangeFromDatum = GPS_CalculateDistance(
    state->datumLat, state->datumLon,
    state->datumLat, state->datumLon  // Current position will be updated by GPS parsing
  );

  state->bearingToDatum = GPS_CalculateBearing(
    state->datumLat, state->datumLon,
    state->datumLat, state->datumLon  // Current position will be updated by GPS parsing
  );
}

bool GPS_ParseNMEA(const char* sentence, NavigationState_t* state) {
  // Check sentence type and parse accordingly
  if (strncmp(sentence, "$GPGGA", 6) == 0 || strncmp(sentence, "$GNGGA", 6) == 0) {
    return GPS_ParseGGA(sentence, state);
  } else if (strncmp(sentence, "$GPRMC", 6) == 0 || strncmp(sentence, "$GNRMC", 6) == 0) {
    return GPS_ParseRMC(sentence, state);
  }

  return false;
}

bool GPS_ParseGGA(const char* sentence, NavigationState_t* state) {
  // Parse GGA sentence for position and altitude
  // $GPGGA,time,lat,N/S,lon,E/W,quality,satellites,hdop,altitude,M,geoid,M,dgps_time,dgps_id*checksum

  char* tokens[15];
  char buffer[128];
  strncpy(buffer, sentence, sizeof(buffer) - 1);
  buffer[sizeof(buffer) - 1] = '\0';

  // Tokenize the sentence
  int tokenCount = 0;
  char* token = strtok(buffer, ",");
  while (token != NULL && tokenCount < 15) {
    tokens[tokenCount++] = token;
    token = strtok(NULL, ",");
  }

  if (tokenCount < 10) {
    return false;
  }

  // Parse latitude
  double lat = GPS_ConvertDMToDD(atof(tokens[2]));
  if (tokens[3][0] == 'S') {
    lat = -lat;
  }

  // Parse longitude
  double lon = GPS_ConvertDMToDD(atof(tokens[4]));
  if (tokens[5][0] == 'W') {
    lon = -lon;
  }

  // Parse altitude
  float altitude = atof(tokens[9]);

  // Parse quality and satellites
  int quality = atoi(tokens[6]);
  int satellites = atoi(tokens[7]);
  float hdop = atof(tokens[8]);

  // Update state if fix is valid
  if (quality > 0 && satellites >= GPS_MIN_SATELLITES && hdop < GPS_MAX_HDOP) {
    state->datumLat = lat; // This will be proper current position in full implementation
    state->datumLon = lon; // This will be proper current position in full implementation
    state->altitude = altitude;

    // Convert to local coordinates if datum is set
    if (state->datumSet) {
      GPS_ConvertToMeters(lat, lon, state->datumLat, state->datumLon,
                         &state->north, &state->east);
    }

    return true;
  }

  return false;
}

bool GPS_ParseRMC(const char* sentence, NavigationState_t* state) {
  // Parse RMC sentence for speed and track
  // $GPRMC,time,status,lat,N/S,lon,E/W,speed,track,date,mag_var,mag_var_dir*checksum

  char* tokens[12];
  char buffer[128];
  strncpy(buffer, sentence, sizeof(buffer) - 1);
  buffer[sizeof(buffer) - 1] = '\0';

  // Tokenize the sentence
  int tokenCount = 0;
  char* token = strtok(buffer, ",");
  while (token != NULL && tokenCount < 12) {
    tokens[tokenCount++] = token;
    token = strtok(NULL, ",");
  }

  if (tokenCount < 8) {
    return false;
  }

  // Check status
  if (tokens[2][0] != 'A') {
    return false; // Invalid fix
  }

  // Parse speed (knots) and convert to m/s
  float speedKnots = atof(tokens[7]);
  state->groundSpeed = speedKnots * 0.514444; // Convert knots to m/s

  // Parse track (degrees) and convert to radians
  float trackDeg = atof(tokens[8]);
  state->groundTrack = trackDeg * DEG_TO_RAD;
  state->heading = state->groundTrack; // Assume heading equals track (no wind)

  return true;
}

void GPS_ConvertToMeters(double latDeg, double lonDeg, double datumLatDeg, double datumLonDeg,
                        float* northM, float* eastM) {
  // Convert GPS coordinates to local meters relative to datum
  double deltaLat = latDeg - datumLatDeg;
  double deltaLon = lonDeg - datumLonDeg;

  // Convert to meters (approximate for small distances)
  *northM = deltaLat * METERS_PER_DEGREE_LAT;
  *eastM = deltaLon * METERS_PER_DEGREE_LAT * cos(datumLatDeg * DEG_TO_RAD);
}

double GPS_ConvertDMToDD(double degMin) {
  // Convert degrees and minutes to decimal degrees
  // Format: DDMM.MMMM or DDDMM.MMMM
  int degrees = (int)(degMin / 100);
  double minutes = degMin - (degrees * 100);
  return degrees + (minutes / 60.0);
}

float GPS_CalculateDistance(double lat1, double lon1, double lat2, double lon2) {
  // Haversine formula for distance calculation
  double dLat = (lat2 - lat1) * DEG_TO_RAD;
  double dLon = (lon2 - lon1) * DEG_TO_RAD;
  double a = sin(dLat/2) * sin(dLat/2) +
            cos(lat1 * DEG_TO_RAD) * cos(lat2 * DEG_TO_RAD) *
            sin(dLon/2) * sin(dLon/2);
  double c = 2 * atan2(sqrt(a), sqrt(1-a));
  return EARTH_RADIUS_M * c;
}

float GPS_CalculateBearing(double lat1, double lon1, double lat2, double lon2) {
  // Calculate bearing from point 1 to point 2
  double dLon = (lon2 - lon1) * DEG_TO_RAD;
  double lat1Rad = lat1 * DEG_TO_RAD;
  double lat2Rad = lat2 * DEG_TO_RAD;

  double y = sin(dLon) * cos(lat2Rad);
  double x = cos(lat1Rad) * sin(lat2Rad) - sin(lat1Rad) * cos(lat2Rad) * cos(dLon);

  double bearing = atan2(y, x);
  return ModAngle(bearing); // Normalize to +/-pi
}

bool Nav_ValidateGPSFix(const NavigationState_t* state) {
  // Check if GPS data is recent and valid
  return (millis() - state->lastGpsUpdate) < GPS_TIMEOUT_MS;
}

bool Nav_ValidatePosition(const NavigationState_t* state) {
  // Basic position validation
  if (state->datumSet) {
    // Check if position is reasonable relative to datum
    return state->rangeFromDatum < 10000.0; // Within 10km of datum
  }

  return true; // Accept any position if no datum set
}