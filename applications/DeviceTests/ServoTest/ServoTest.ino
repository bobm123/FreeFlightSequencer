/*
 * ServoTest.ino - Servo/PWM Interface Test Application
 * 
 * Tests standard Arduino Servo library with dual servo control
 * for motor ESC and dethermalizer deployment simulation.
 * 
 * Hardware Requirements:
 * - Adafruit QT Py SAMD21
 * - Two servo connections (Motor ESC and Dethermalizer)
 * - Push button connected to A0 for test control
 * 
 * Serial Output: 9600 baud
 * 
 * Test validates:
 * - Servo library initialization and attachment
 * - PWM pulse width control (950us to 2000us range)  
 * - Motor ESC speed ramp sequences
 * - Dethermalizer deployment/retract sequences
 * - Timing accuracy and servo response
 */

#include <Arduino.h>
#include <Servo.h>

// Hardware pin definitions (QtPY SAMD21 via Signal Distribution MkII)
const int MOTOR_SERVO_PIN = A2;      // Pin for motor ESC control (ESC0)
const int DT_SERVO_PIN = A3;         // Pin for dethermalizer servo (CH1)
const int BUTTON_PIN = A0;           // Push button for test control
const int LED_BUILTIN_PIN = 11;      // Onboard NeoPixel (for status)

// Servo objects
Servo motorServo;
Servo dtServo;

// Servo control parameters (matching E36-Timer values)
const int MIN_SPEED = 95;        // 95 -> 950us pulse (motor idle)
const int MAX_SPEED = 200;       // 200 -> 2000us pulse (motor full)
const int DT_RETRACT = 1000;     // 1000us pulse (dethermalizer retracted)
const int DT_DEPLOY = 2000;      // 2000us pulse (dethermalizer deployed)

// Test configuration
const unsigned long TEST_DURATION = 60000;    // 60 second test duration
const unsigned long RAMP_STEP_TIME = 200;     // 200ms per speed step
const unsigned long DT_DEPLOY_TIME = 2000;    // 2 second deploy hold
const unsigned long SEQUENCE_PAUSE = 3000;    // 3 second pause between sequences

// Test state management
enum TestPhase {
  PHASE_ANNOUNCE_MOTOR,
  PHASE_MOTOR_RAMP_UP,
  PHASE_MOTOR_FULL_SPEED,
  PHASE_MOTOR_RAMP_DOWN,
  PHASE_ANNOUNCE_DT,
  PHASE_DT_DEPLOY,
  PHASE_DT_RETRACT,
  PHASE_ANNOUNCE_COMBINED,
  PHASE_COMBINED_SEQUENCE,
  PHASE_COMPLETE
};

TestPhase currentPhase = PHASE_ANNOUNCE_MOTOR;
unsigned long phaseStartTime = 0;
unsigned long testStartTime = 0;
int phaseStep = 0;
bool phaseMessageSent = false;
bool testActive = false;
bool buttonPressed = false;

// Test statistics
int motorRampCycles = 0;
int dtDeployCycles = 0;
int combinedSequences = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  // Initialize button
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initialize status LED
  pinMode(LED_BUILTIN_PIN, OUTPUT);
  digitalWrite(LED_BUILTIN_PIN, LOW);
  
  // Initialize servos
  motorServo.attach(MOTOR_SERVO_PIN);
  dtServo.attach(DT_SERVO_PIN);
  
  // Set servos to safe initial positions
  motorServo.writeMicroseconds(MIN_SPEED * 10);  // Motor idle
  dtServo.writeMicroseconds(DT_RETRACT);         // DT retracted
  
  Serial.println(F("[INFO] Servo Test Application Initialized"));
  Serial.println(F("[INFO] Motor servo on pin A2, DT servo on pin A3"));
  Serial.println(F("[INFO] Press button to start test sequence"));
  Serial.println();
}

void loop() {
  // Check for button press to start test
  if (!testActive && digitalRead(BUTTON_PIN) == LOW) {
    if (!buttonPressed) {
      buttonPressed = true;
      delay(50); // Simple debounce
      startServoTest();
    }
  } else if (digitalRead(BUTTON_PIN) == HIGH) {
    buttonPressed = false;
  }
  
  if (!testActive) {
    return;
  }
  
  unsigned long currentTime = millis();
  
  // Check for overall test timeout
  if (currentTime - testStartTime > TEST_DURATION) {
    completeServoTest();
    return;
  }
  
  // Execute current test phase
  executeCurrentPhase(currentTime);
  
  // Small delay to prevent excessive polling
  delay(10);
}

void executeCurrentPhase(unsigned long currentTime) {
  unsigned long phaseElapsed = currentTime - phaseStartTime;
  
  switch (currentPhase) {
    case PHASE_ANNOUNCE_MOTOR:
      executeAnnounceMotor(phaseElapsed);
      break;
      
    case PHASE_MOTOR_RAMP_UP:
      executeMotorRampUp(phaseElapsed);
      break;
      
    case PHASE_MOTOR_FULL_SPEED:
      executeMotorFullSpeed(phaseElapsed);
      break;
      
    case PHASE_MOTOR_RAMP_DOWN:
      executeMotorRampDown(phaseElapsed);
      break;
      
    case PHASE_ANNOUNCE_DT:
      executeAnnounceDT(phaseElapsed);
      break;
      
    case PHASE_DT_DEPLOY:
      executeDTDeploy(phaseElapsed);
      break;
      
    case PHASE_DT_RETRACT:
      executeDTRetract(phaseElapsed);
      break;
      
    case PHASE_ANNOUNCE_COMBINED:
      executeAnnounceCombined(phaseElapsed);
      break;
      
    case PHASE_COMBINED_SEQUENCE:
      executeCombinedSequence(phaseElapsed);
      break;
      
    case PHASE_COMPLETE:
      completeServoTest();
      break;
  }
}

void executeAnnounceMotor(unsigned long phaseElapsed) {
  if (!phaseMessageSent) {
    Serial.println(F("[INFO] Testing motor ESC servo ramp sequence"));
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= 2000) {
    advanceToNextPhase(PHASE_MOTOR_RAMP_UP);
  }
}

void executeMotorRampUp(unsigned long phaseElapsed) {
  // Ramp motor from MIN_SPEED to MAX_SPEED in steps
  int rampSteps = (MAX_SPEED - MIN_SPEED) / 5; // 5 unit steps
  int stepIndex = phaseElapsed / RAMP_STEP_TIME;
  
  if (stepIndex < rampSteps) {
    int motorSpeed = MIN_SPEED + (stepIndex * 5);
    if (motorSpeed > MAX_SPEED) motorSpeed = MAX_SPEED;
    
    if (phaseStep != stepIndex) {
      motorServo.writeMicroseconds(motorSpeed * 10);
      Serial.print(F("[OK] Motor speed: "));
      Serial.print(motorSpeed);
      Serial.print(F(" ("));
      Serial.print(motorSpeed * 10);
      Serial.println(F("us)"));
      phaseStep = stepIndex;
    }
  } else {
    Serial.println(F("[OK] Motor ramp up completed"));
    advanceToNextPhase(PHASE_MOTOR_FULL_SPEED);
  }
}

void executeMotorFullSpeed(unsigned long phaseElapsed) {
  if (!phaseMessageSent) {
    motorServo.writeMicroseconds(MAX_SPEED * 10);
    Serial.print(F("[INFO] Motor at full speed: "));
    Serial.print(MAX_SPEED * 10);
    Serial.println(F("us for 3 seconds"));
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= 3000) {
    advanceToNextPhase(PHASE_MOTOR_RAMP_DOWN);
  }
}

void executeMotorRampDown(unsigned long phaseElapsed) {
  // Ramp motor from MAX_SPEED back to MIN_SPEED
  int rampSteps = (MAX_SPEED - MIN_SPEED) / 5; // 5 unit steps
  int stepIndex = phaseElapsed / RAMP_STEP_TIME;
  
  if (stepIndex < rampSteps) {
    int motorSpeed = MAX_SPEED - (stepIndex * 5);
    if (motorSpeed < MIN_SPEED) motorSpeed = MIN_SPEED;
    
    if (phaseStep != stepIndex) {
      motorServo.writeMicroseconds(motorSpeed * 10);
      Serial.print(F("[OK] Motor speed: "));
      Serial.print(motorSpeed);
      Serial.print(F(" ("));
      Serial.print(motorSpeed * 10);
      Serial.println(F("us)"));
      phaseStep = stepIndex;
    }
  } else {
    motorServo.writeMicroseconds(MIN_SPEED * 10);
    Serial.println(F("[OK] Motor ramp down completed - motor idle"));
    motorRampCycles++;
    advanceToNextPhase(PHASE_ANNOUNCE_DT);
  }
}

void executeAnnounceDT(unsigned long phaseElapsed) {
  if (!phaseMessageSent) {
    Serial.println(F("[INFO] Testing dethermalizer deployment sequence"));
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= 2000) {
    advanceToNextPhase(PHASE_DT_DEPLOY);
  }
}

void executeDTDeploy(unsigned long phaseElapsed) {
  if (!phaseMessageSent) {
    dtServo.writeMicroseconds(DT_DEPLOY);
    Serial.print(F("[OK] Dethermalizer deployed: "));
    Serial.print(DT_DEPLOY);
    Serial.println(F("us"));
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= DT_DEPLOY_TIME) {
    advanceToNextPhase(PHASE_DT_RETRACT);
  }
}

void executeDTRetract(unsigned long phaseElapsed) {
  if (!phaseMessageSent) {
    dtServo.writeMicroseconds(DT_RETRACT);
    Serial.print(F("[OK] Dethermalizer retracted: "));
    Serial.print(DT_RETRACT);
    Serial.println(F("us"));
    dtDeployCycles++;
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= 1000) {
    advanceToNextPhase(PHASE_ANNOUNCE_COMBINED);
  }
}

void executeAnnounceCombined(unsigned long phaseElapsed) {
  if (!phaseMessageSent) {
    Serial.println(F("[INFO] Testing combined flight sequence simulation"));
    phaseMessageSent = true;
  }
  
  if (phaseElapsed >= 2000) {
    advanceToNextPhase(PHASE_COMBINED_SEQUENCE);
  }
}

void executeCombinedSequence(unsigned long phaseElapsed) {
  // Simulate E36 flight sequence: motor ramp, run, stop, then DT deploy
  const unsigned long MOTOR_RAMP_TIME = 1000;    // 1 second ramp
  const unsigned long MOTOR_RUN_TIME = 5000;     // 5 second run
  const unsigned long GLIDE_TIME = 3000;         // 3 second glide
  const unsigned long DT_TIME = 2000;            // 2 second DT deploy
  
  if (phaseElapsed < MOTOR_RAMP_TIME) {
    // Motor ramp phase
    int motorSpeed = MIN_SPEED + ((phaseElapsed * (MAX_SPEED - MIN_SPEED)) / MOTOR_RAMP_TIME);
    if (motorSpeed > MAX_SPEED) motorSpeed = MAX_SPEED;
    
    motorServo.writeMicroseconds(motorSpeed * 10);
    
    if (phaseStep == 0) {
      Serial.println(F("[INFO] Combined sequence: Motor ramping"));
      phaseStep = 1;
    }
  } 
  else if (phaseElapsed < MOTOR_RAMP_TIME + MOTOR_RUN_TIME) {
    // Motor run phase
    motorServo.writeMicroseconds(MAX_SPEED * 10);
    
    if (phaseStep == 1) {
      Serial.println(F("[INFO] Combined sequence: Motor at full speed"));
      phaseStep = 2;
    }
  }
  else if (phaseElapsed < MOTOR_RAMP_TIME + MOTOR_RUN_TIME + GLIDE_TIME) {
    // Glide phase
    motorServo.writeMicroseconds(MIN_SPEED * 10);
    
    if (phaseStep == 2) {
      Serial.println(F("[INFO] Combined sequence: Motor off - gliding"));
      phaseStep = 3;
    }
  }
  else if (phaseElapsed < MOTOR_RAMP_TIME + MOTOR_RUN_TIME + GLIDE_TIME + DT_TIME) {
    // DT deploy phase
    dtServo.writeMicroseconds(DT_DEPLOY);
    
    if (phaseStep == 3) {
      Serial.println(F("[INFO] Combined sequence: Dethermalizer deployed"));
      phaseStep = 4;
    }
  }
  else {
    // Sequence complete
    dtServo.writeMicroseconds(DT_RETRACT);
    
    if (phaseStep == 4) {
      Serial.println(F("[OK] Combined flight sequence completed"));
      combinedSequences++;
      phaseStep = 5;
    }
    
    advanceToNextPhase(PHASE_COMPLETE);
  }
}

void advanceToNextPhase(TestPhase nextPhase) {
  currentPhase = nextPhase;
  phaseStartTime = millis();
  phaseStep = 0;
  phaseMessageSent = false;
}

void startServoTest() {
  testStartTime = millis();
  testActive = true;
  motorRampCycles = 0;
  dtDeployCycles = 0;
  combinedSequences = 0;
  advanceToNextPhase(PHASE_ANNOUNCE_MOTOR);
  
  Serial.println(F("[INFO] Servo Test Starting"));
  Serial.println(F("[INFO] Testing motor ESC and dethermalizer servos"));
  Serial.print(F("[INFO] Test will run for "));
  Serial.print(TEST_DURATION / 1000);
  Serial.println(F(" seconds"));
  Serial.println();
}

void completeServoTest() {
  testActive = false;
  
  // Set servos to safe positions
  motorServo.writeMicroseconds(MIN_SPEED * 10);
  dtServo.writeMicroseconds(DT_RETRACT);
  
  Serial.println();
  Serial.println(F("[INFO] Servo Test Complete - verify output"));
  Serial.print(F("[INFO] Sequences executed: "));
  Serial.print(motorRampCycles);
  Serial.print(F(" motor ramps, "));
  Serial.print(dtDeployCycles);
  Serial.print(F(" DT deployments, "));
  Serial.print(combinedSequences);
  Serial.println(F(" combined sequences"));
  Serial.println(F("[INFO] PWM range tested: 950us to 2000us"));
  Serial.println(F("[INFO] Servo response: User visual verification required"));
  
  // Flash status LED to indicate completion
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN_PIN, HIGH);
    delay(200);
    digitalWrite(LED_BUILTIN_PIN, LOW);
    delay(200);
  }
}