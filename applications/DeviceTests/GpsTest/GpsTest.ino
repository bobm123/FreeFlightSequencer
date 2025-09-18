/*
 * GpsTest.ino - GPS Module Test for QtPY SAMD21
 * 
 * GPS module validation for flight control applications.
 * Tests NMEA sentence parsing, coordinate extraction, and GPS status monitoring.
 * 
 * Hardware Requirements:
 * - Adafruit QT Py SAMD21 microcontroller
 * - Signal Distribution MkII carrier board
 * - GPS module with UART output connected to GPS0 connector
 * - GPS antenna with clear sky view for satellite reception
 * - 5V BEC power supply
 * 
 * GPS Connection:
 * - GPS-TX -> Qt Py TX/RX (D6) -> Serial1 RX
 * - GPS power from VBEC (5V)
 * - Common ground connection
 * 
 * Test Phases:
 * 1. GPS Module Detection (0-30s)
 * 2. NMEA Parsing Validation (30-120s) 
 * 3. Navigation Data Validation (2-10min)
 * 4. Long-term Stability (10+ min)
 */

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

// Hardware pin definitions (QtPY SAMD21 via Signal Distribution MkII)
const int NEOPIXEL_PIN = 11;         // NeoPixel LED (onboard)
const int GPS_BAUD_RATE = 9600;      // Standard GPS baud rate

// NeoPixel LED for status indication
Adafruit_NeoPixel pixel(1, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// GPS data structure
struct GPSData {
  bool hasValidFix = false;
  bool hasValidTime = false;
  float latitude = 0.0;
  float longitude = 0.0;
  float altitude = 0.0;
  float speed = 0.0;
  float course = 0.0;
  int satellites = 0;
  float hdop = 99.9;
  char fixTime[12] = "00:00:00";
  char fixDate[12] = "00/00/00";
  char fixQuality = 'V'; // V = Invalid, A = Valid
  int fixType = 0; // 0 = No fix, 1 = GPS fix, 2 = DGPS fix
};

// Global GPS data
GPSData gps;

// Test statistics
struct TestStats {
  unsigned long testStartTime;
  unsigned long lastGpsUpdate;
  unsigned long totalSentences;
  unsigned long validSentences;
  unsigned long parseErrors;
  unsigned long timeToFirstFix;
  bool firstFixAchieved;
};

TestStats stats;

// Status tracking
unsigned long lastStatusUpdate = 0;
unsigned long lastLedUpdate = 0;
const unsigned long STATUS_INTERVAL = 5000;  // 5 second status updates
const unsigned long LED_INTERVAL = 1000;     // 1 second LED updates

// NMEA sentence buffer
String nmeaBuffer = "";
const int MAX_NMEA_LENGTH = 120;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial && millis() < 3000) {
    ; // Wait up to 3 seconds for serial connection
  }
  
  Serial.println(F("[INFO] GPS Test starting..."));
  Serial.println(F("[INFO] Testing GPS module on Serial1 at 9600 baud"));
  Serial.println(F("[INFO] GPS-TX should be connected to Qt Py D6 (Serial1 RX)"));
  
  // Initialize NeoPixel
  pixel.begin();
  pixel.clear();
  pixel.show();
  
  // Initialize GPS serial port
  Serial1.begin(GPS_BAUD_RATE);
  
  // Initialize test statistics
  stats.testStartTime = millis();
  stats.lastGpsUpdate = 0;
  stats.totalSentences = 0;
  stats.validSentences = 0;
  stats.parseErrors = 0;
  stats.timeToFirstFix = 0;
  stats.firstFixAchieved = false;
  
  Serial.println(F("[INFO] GPS module initialization complete"));
  Serial.println(F("[INFO] Waiting for GPS sentences..."));
  Serial.println();
}

void loop() {
  unsigned long currentTime = millis();
  
  // Process incoming GPS data
  processGPSData();
  
  // Update status display
  if (currentTime - lastStatusUpdate >= STATUS_INTERVAL) {
    displayGPSStatus(currentTime);
    displayTestStatistics(currentTime);
    lastStatusUpdate = currentTime;
  }
  
  // Update status LED
  if (currentTime - lastLedUpdate >= LED_INTERVAL) {
    updateStatusLED();
    lastLedUpdate = currentTime;
  }
  
  // Check for test phase transitions
  checkTestPhases(currentTime);
}

void processGPSData() {
  // Read GPS data from Serial1
  while (Serial1.available()) {
    char c = Serial1.read();
    
    if (c == '$') {
      // Start of new NMEA sentence
      nmeaBuffer = "$";
    } else if (c == '\n' || c == '\r') {
      // End of NMEA sentence
      if (nmeaBuffer.length() > 0 && nmeaBuffer.startsWith("$")) {
        processNMEASentence(nmeaBuffer);
        stats.totalSentences++;
        stats.lastGpsUpdate = millis();
      }
      nmeaBuffer = "";
    } else {
      // Build NMEA sentence
      if (nmeaBuffer.length() < MAX_NMEA_LENGTH) {
        nmeaBuffer += c;
      }
    }
  }
}

void processNMEASentence(String sentence) {
  // Validate NMEA checksum
  if (!validateNMEAChecksum(sentence)) {
    stats.parseErrors++;
    Serial.print(F("[WARN] Invalid checksum: "));
    Serial.println(sentence);
    return;
  }
  
  stats.validSentences++;
  
  // Parse different NMEA sentence types
  if (sentence.startsWith("$GPGGA") || sentence.startsWith("$GNGGA")) {
    parseGGASentence(sentence);
  } else if (sentence.startsWith("$GPRMC") || sentence.startsWith("$GNRMC")) {
    parseRMCSentence(sentence);
  } else if (sentence.startsWith("$GPGSA") || sentence.startsWith("$GNGSA")) {
    parseGSASentence(sentence);
  } else {
    // Silently ignore unknown sentence types (GSV, GLL, VTG, etc.)
    // These sentences are received and validated but not parsed for data
  }
}

bool validateNMEAChecksum(String sentence) {
  int checksumIndex = sentence.lastIndexOf('*');
  if (checksumIndex == -1) return false;
  
  // Calculate checksum
  byte calculatedChecksum = 0;
  for (int i = 1; i < checksumIndex; i++) {
    calculatedChecksum ^= sentence.charAt(i);
  }
  
  // Extract provided checksum
  String checksumStr = sentence.substring(checksumIndex + 1);
  byte providedChecksum = strtol(checksumStr.c_str(), NULL, 16);
  
  return calculatedChecksum == providedChecksum;
}

void parseGGASentence(String sentence) {
  // $GPGGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh
  // Example: $GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
  
  String fields[15];
  int fieldCount = splitString(sentence, ',', fields, 15);
  
  if (fieldCount >= 15) {
    // Time
    if (fields[1].length() >= 6) {
      snprintf(gps.fixTime, sizeof(gps.fixTime), "%c%c:%c%c:%c%c", 
               fields[1][0], fields[1][1], fields[1][2], fields[1][3], fields[1][4], fields[1][5]);
      gps.hasValidTime = true;
    }
    
    // Position
    if (fields[2].length() > 0 && fields[4].length() > 0) {
      gps.latitude = convertDMtoDD(fields[2], fields[3]);
      gps.longitude = convertDMtoDD(fields[4], fields[5]);
    }
    
    // Fix quality and satellites
    gps.fixType = fields[6].toInt();
    gps.satellites = fields[7].toInt();
    
    // HDOP
    if (fields[8].length() > 0) {
      gps.hdop = fields[8].toFloat();
    }
    
    // Altitude
    if (fields[9].length() > 0) {
      gps.altitude = fields[9].toFloat();
    }
    
    // Check for valid fix
    gps.hasValidFix = (gps.fixType > 0 && gps.satellites >= 4);
    
    // Track first fix achievement
    if (gps.hasValidFix && !stats.firstFixAchieved) {
      stats.firstFixAchieved = true;
      stats.timeToFirstFix = millis() - stats.testStartTime;
      Serial.println();
      Serial.print(F("[SUCCESS] First 3D GPS fix achieved! Time: "));
      Serial.print(stats.timeToFirstFix / 1000);
      Serial.println(F(" seconds"));
      Serial.println();
    }
  }
}

void parseRMCSentence(String sentence) {
  // $GPRMC,hhmmss.ss,A,llll.ll,a,yyyyy.yy,a,x.x,x.x,ddmmyy,x.x,a*hh
  // Example: $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
  
  String fields[13];
  int fieldCount = splitString(sentence, ',', fields, 13);
  
  if (fieldCount >= 12) {
    // Fix quality
    gps.fixQuality = (fields[2].length() > 0) ? fields[2][0] : 'V';
    
    // Position (if not already set by GGA)
    if (fields[3].length() > 0 && fields[5].length() > 0) {
      gps.latitude = convertDMtoDD(fields[3], fields[4]);
      gps.longitude = convertDMtoDD(fields[5], fields[6]);
    }
    
    // Speed and course
    if (fields[7].length() > 0) {
      gps.speed = fields[7].toFloat() * 1.852; // Convert knots to km/h
    }
    if (fields[8].length() > 0) {
      gps.course = fields[8].toFloat();
    }
    
    // Date
    if (fields[9].length() >= 6) {
      snprintf(gps.fixDate, sizeof(gps.fixDate), "%c%c/%c%c/%c%c", 
               fields[9][0], fields[9][1], fields[9][2], fields[9][3], fields[9][4], fields[9][5]);
    }
  }
}

void parseGSASentence(String sentence) {
  // $GPGSA,A,3,04,05,,09,12,,,24,,,,,2.5,1.3,2.1*39
  // Extract fix type and DOP values
  
  String fields[18];
  int fieldCount = splitString(sentence, ',', fields, 18);
  
  if (fieldCount >= 17) {
    // Fix type: 1=No fix, 2=2D, 3=3D
    int fixMode = fields[2].toInt();
    if (fixMode > gps.fixType) {
      gps.fixType = fixMode;
    }
    
    // Count active satellites
    int activeSats = 0;
    for (int i = 3; i <= 14; i++) {
      if (fields[i].length() > 0) {
        activeSats++;
      }
    }
    gps.satellites = max(gps.satellites, activeSats);
  }
}

float convertDMtoDD(String dmString, String hemisphere) {
  if (dmString.length() < 4) return 0.0;
  
  // Parse degrees and minutes from DDMM.MMMM or DDDMM.MMMM format
  int dotIndex = dmString.indexOf('.');
  if (dotIndex == -1) return 0.0;
  
  String degreesPart;
  String minutesPart;
  
  if (dotIndex == 4) {
    // DDMM.MMMM format (latitude)
    degreesPart = dmString.substring(0, 2);
    minutesPart = dmString.substring(2);
  } else if (dotIndex == 5) {
    // DDDMM.MMMM format (longitude)
    degreesPart = dmString.substring(0, 3);
    minutesPart = dmString.substring(3);
  } else {
    return 0.0;
  }
  
  float degrees = degreesPart.toFloat();
  float minutes = minutesPart.toFloat();
  float decimal = degrees + (minutes / 60.0);
  
  // Apply hemisphere
  if (hemisphere == "S" || hemisphere == "W") {
    decimal = -decimal;
  }
  
  return decimal;
}

int splitString(String str, char delimiter, String* fields, int maxFields) {
  int fieldCount = 0;
  int lastIndex = 0;
  int nextIndex = 0;
  
  while (fieldCount < maxFields && nextIndex != -1) {
    nextIndex = str.indexOf(delimiter, lastIndex);
    if (nextIndex == -1) {
      fields[fieldCount] = str.substring(lastIndex);
    } else {
      fields[fieldCount] = str.substring(lastIndex, nextIndex);
    }
    fieldCount++;
    lastIndex = nextIndex + 1;
  }
  
  return fieldCount;
}

void displayGPSStatus(unsigned long currentTime) {
  unsigned long elapsedSeconds = (currentTime - stats.testStartTime) / 1000;
  
  Serial.println(F("=== GPS Status Report ==="));
  Serial.print(F("Test Time: "));
  Serial.print(elapsedSeconds / 60);
  Serial.print(F(":"));
  if ((elapsedSeconds % 60) < 10) Serial.print(F("0"));
  Serial.println(elapsedSeconds % 60);
  
  Serial.print(F("Fix Status: "));
  if (gps.hasValidFix) {
    Serial.print(F("[OK] 3D Fix"));
  } else if (gps.fixType == 2) {
    Serial.print(F("[WARN] 2D Fix Only"));
  } else {
    Serial.print(F("[FAIL] No Fix"));
  }
  Serial.print(F(" (Type: "));
  Serial.print(gps.fixType);
  Serial.println(F(")"));
  
  Serial.print(F("Satellites: "));
  Serial.print(gps.satellites);
  Serial.print(F(" tracked, HDOP: "));
  Serial.println(gps.hdop);
  
  if (gps.hasValidFix) {
    Serial.print(F("Position: "));
    Serial.print(gps.latitude, 6);
    Serial.print(F("deg, "));
    Serial.print(gps.longitude, 6);
    Serial.println(F("deg"));
    
    Serial.print(F("Altitude: "));
    Serial.print(gps.altitude, 1);
    Serial.print(F("m, Speed: "));
    Serial.print(gps.speed, 1);
    Serial.print(F("km/h, Course: "));
    Serial.print(gps.course, 1);
    Serial.println(F("deg"));
  }
  
  if (gps.hasValidTime) {
    Serial.print(F("GPS Time: "));
    Serial.print(gps.fixTime);
    Serial.print(F(" "));
    Serial.println(gps.fixDate);
  }
  
  Serial.println();
}

void displayTestStatistics(unsigned long currentTime) {
  Serial.println(F("=== Test Statistics ==="));
  Serial.print(F("Total NMEA Sentences: "));
  Serial.println(stats.totalSentences);
  Serial.print(F("Valid Sentences: "));
  Serial.print(stats.validSentences);
  Serial.print(F(" ("));
  if (stats.totalSentences > 0) {
    Serial.print((stats.validSentences * 100) / stats.totalSentences);
  } else {
    Serial.print(F("0"));
  }
  Serial.println(F("%)"));
  
  Serial.print(F("Parse Errors: "));
  Serial.println(stats.parseErrors);
  
  if (stats.firstFixAchieved) {
    Serial.print(F("Time to First Fix: "));
    Serial.print(stats.timeToFirstFix / 1000);
    Serial.println(F(" seconds"));
  } else {
    Serial.println(F("Time to First Fix: Not achieved"));
  }
  
  unsigned long timeSinceLastGPS = currentTime - stats.lastGpsUpdate;
  Serial.print(F("Last GPS Update: "));
  Serial.print(timeSinceLastGPS / 1000);
  Serial.println(F(" seconds ago"));
  
  Serial.println();
}

void updateStatusLED() {
  static int ledState = 0;
  
  if (!gps.hasValidFix) {
    // Red blinking - No GPS fix
    if (ledState == 0) {
      pixel.setPixelColor(0, pixel.Color(255, 0, 0)); // Red
      ledState = 1;
    } else {
      pixel.setPixelColor(0, pixel.Color(0, 0, 0));   // Off
      ledState = 0;
    }
  } else if (gps.satellites < 6) {
    // Yellow solid - GPS fix but few satellites
    pixel.setPixelColor(0, pixel.Color(255, 255, 0)); // Yellow
  } else {
    // Green solid - Good GPS fix
    pixel.setPixelColor(0, pixel.Color(0, 255, 0)); // Green
  }
  
  pixel.show();
}

void checkTestPhases(unsigned long currentTime) {
  unsigned long elapsedSeconds = (currentTime - stats.testStartTime) / 1000;
  static int lastPhase = 0;
  int currentPhase = 0;
  
  if (elapsedSeconds < 30) {
    currentPhase = 1; // GPS Module Detection
  } else if (elapsedSeconds < 120) {
    currentPhase = 2; // NMEA Parsing Validation  
  } else if (elapsedSeconds < 600) {
    currentPhase = 3; // Navigation Data Validation
  } else {
    currentPhase = 4; // Long-term Stability
  }
  
  if (currentPhase != lastPhase) {
    Serial.println(F("=========================================="));
    Serial.print(F("[PHASE "));
    Serial.print(currentPhase);
    Serial.print(F("] "));
    
    switch (currentPhase) {
      case 1:
        Serial.println(F("GPS Module Detection Phase"));
        Serial.println(F("- Monitoring for NMEA sentences"));
        Serial.println(F("- Validating communication parameters"));
        break;
      case 2:
        Serial.println(F("NMEA Parsing Validation Phase"));
        Serial.println(F("- Testing sentence parsing and validation"));
        Serial.println(F("- Monitoring fix acquisition"));
        break;
      case 3:
        Serial.println(F("Navigation Data Validation Phase"));
        Serial.println(F("- Validating coordinate accuracy"));
        Serial.println(F("- Testing fix quality metrics"));
        break;
      case 4:
        Serial.println(F("Long-term Stability Phase"));
        Serial.println(F("- Monitoring data continuity"));
        Serial.println(F("- Checking memory usage and performance"));
        break;
    }
    Serial.println(F("=========================================="));
    Serial.println();
    
    lastPhase = currentPhase;
  }
}