/*
 * control.cpp - Control Library Implementation
 *
 * Autonomous flight control system implementing circular orbit guidance.
 * Uses GPS position data to maintain aircraft within specified radius.
 */

#include "control.h"
#include "math_utils.h"

// Global control parameters
static ControlParams_t controlParams;

void Control_Init(const ControlParams_t* params) {
  // Copy control parameters
  controlParams = *params;

  Serial.println(F("[CTRL] Control system initialized"));
  Serial.print(F("[CTRL] Orbit radius: "));
  Serial.print(controlParams.OrbitRadius);
  Serial.println(F(" meters"));
}

void Control_Step(const NavigationState_t* navState, ControlState_t* controlState, float deltaTime) {
  // Only run control if GPS is valid and datum is set
  if (!navState->gpsValid || !navState->datumSet) {
    controlState->autonomousMode = false;
    controlState->rollCommand = 0.0;
    controlState->motorCommand = 0.5; // Mid-power for manual control
    return;
  }

  // Check safety conditions
  if (!Control_CheckSafetyConditions(navState)) {
    controlState->autonomousMode = false;
    controlState->rollCommand = 0.0;
    controlState->motorCommand = 0.0; // Cut motor for safety
    Serial.println(F("[CTRL] Safety limits exceeded - disabling autonomous control"));
    return;
  }

  // Enable autonomous mode if conditions are met
  controlState->autonomousMode = true;

  // 1. Orbit Control: Compute range error and desired track
  float orbitError = Control_ComputeOrbitError(navState, controlParams.OrbitRadius);
  float desiredTrack = Control_ComputeDesiredTrack(navState, orbitError);

  // Store control values
  controlState->rangeError = orbitError;
  controlState->desiredTrack = desiredTrack;
  controlState->desiredRange = controlParams.OrbitRadius;

  // 2. Track Control: Compute track error and roll command
  float trackError = Control_ComputeTrackError(navState->groundTrack, desiredTrack);
  float rollCommand = Control_ComputeRollCommand(trackError, controlState, deltaTime);

  // Store control values
  controlState->trackError = trackError;
  controlState->rollCommand = rollCommand;

  // 3. Motor Control: Basic altitude/speed management
  float motorCommand = Control_ComputeMotorCommand(navState, deltaTime);
  controlState->motorCommand = motorCommand;

  // 4. Apply safety limits and validation
  Control_ApplySafetyLimits(controlState);
  Control_ValidateCommands(controlState);

  // Update timing
  controlState->lastUpdate = millis();

#ifdef DEBUG_CONTROL
  // Debug output
  Serial.print(F("[CTRL] Range: "));
  Serial.print(navState->rangeFromDatum);
  Serial.print(F(" Error: "));
  Serial.print(orbitError);
  Serial.print(F(" Track: "));
  Serial.print(navState->groundTrack * RAD_TO_DEG);
  Serial.print(F(" Desired: "));
  Serial.print(desiredTrack * RAD_TO_DEG);
  Serial.print(F(" Roll: "));
  Serial.println(rollCommand);
#endif
}

void Control_Reset(ControlState_t* controlState) {
  // Reset all control state variables
  controlState->rollCommand = 0.0;
  controlState->motorCommand = 0.0;
  controlState->rangeError = 0.0;
  controlState->trackError = 0.0;
  controlState->rollError = 0.0;
  controlState->trackIntegral = 0.0;
  controlState->rollIntegral = 0.0;
  controlState->desiredTrack = 0.0;
  controlState->desiredRange = 0.0;
  controlState->autonomousMode = false;
  controlState->lastUpdate = millis();

  Serial.println(F("[CTRL] Control state reset"));
}

void Control_SetAutonomousMode(ControlState_t* controlState, bool enable) {
  controlState->autonomousMode = enable;
  if (!enable) {
    // Reset integral terms when disabling autonomous mode
    controlState->trackIntegral = 0.0;
    controlState->rollIntegral = 0.0;
  }
}

float Control_ComputeOrbitError(const NavigationState_t* navState, float desiredRadius) {
  // Simple proportional control for orbit radius
  return navState->rangeFromDatum - desiredRadius;
}

float Control_ComputeDesiredTrack(const NavigationState_t* navState, float orbitError) {
  // Compute desired ground track to maintain circular orbit
  // Base track is tangent to circle plus correction for range error

  // Tangent angle for circular orbit (90 degrees ahead of bearing to datum)
  float tangentTrack = navState->bearingToDatum + PI/2;

  // Add proportional correction based on range error
  float trackCorrection = controlParams.Kp_orbit * orbitError;

  float desiredTrack = tangentTrack + trackCorrection;

  // Normalize angle to +/-pi
  return ModAngle(desiredTrack);
}

float Control_ComputeTrackError(float currentTrack, float desiredTrack) {
  // Compute track error with proper angle wrapping
  float error = desiredTrack - currentTrack;
  return ModAngle(error);
}

float Control_ComputeRollCommand(float trackError, ControlState_t* controlState, float deltaTime) {
  // PI controller for track following

  // Proportional term
  float proportional = controlParams.Kp_trk * trackError;

  // Integral term with windup protection
  controlState->trackIntegral += trackError * deltaTime;

  // Integral windup protection
  float maxIntegral = 1.0 / controlParams.Ki_trk; // Limit integral contribution
  controlState->trackIntegral = VALIDATE_RANGE(controlState->trackIntegral,
                                               -maxIntegral, maxIntegral);

  float integral = controlParams.Ki_trk * controlState->trackIntegral;

  // Combine P and I terms
  float rollCommand = proportional + integral;

  // Limit roll command
  rollCommand = VALIDATE_RANGE(rollCommand, -MAX_ROLL_COMMAND, MAX_ROLL_COMMAND);

  return rollCommand;
}

float Control_ComputeMotorCommand(const NavigationState_t* navState, float deltaTime) {
  // Simple motor control - maintain moderate power
  // In future versions, this could include altitude control

  float baseMotorCommand = 0.6; // 60% power as baseline

  // Adjust based on distance from datum (closer = less power to avoid tight turns)
  if (navState->rangeFromDatum < controlParams.OrbitRadius * 0.5) {
    baseMotorCommand = 0.4; // Reduce power when too close
  } else if (navState->rangeFromDatum > controlParams.OrbitRadius * 1.5) {
    baseMotorCommand = 0.8; // Increase power when too far
  }

  return VALIDATE_RANGE(baseMotorCommand, 0.0, MAX_MOTOR_COMMAND);
}

bool Control_ValidateCommands(ControlState_t* controlState) {
  // Validate that all commands are within acceptable ranges
  bool valid = true;

  if (fabs(controlState->rollCommand) > MAX_ROLL_COMMAND) {
    controlState->rollCommand = VALIDATE_RANGE(controlState->rollCommand,
                                              -MAX_ROLL_COMMAND, MAX_ROLL_COMMAND);
    valid = false;
  }

  if (controlState->motorCommand < 0.0 || controlState->motorCommand > MAX_MOTOR_COMMAND) {
    controlState->motorCommand = VALIDATE_RANGE(controlState->motorCommand,
                                               0.0, MAX_MOTOR_COMMAND);
    valid = false;
  }

  return valid;
}

void Control_ApplySafetyLimits(ControlState_t* controlState) {
  // Apply conservative safety limits to all commands

  // Limit roll command rate of change
  static float lastRollCommand = 0.0;
  float maxRollRate = 0.5; // Maximum roll command change per second
  float rollRate = (controlState->rollCommand - lastRollCommand) / CONTROL_LOOP_DT;

  if (fabs(rollRate) > maxRollRate) {
    float sign = (rollRate > 0) ? 1.0 : -1.0;
    controlState->rollCommand = lastRollCommand + sign * maxRollRate * CONTROL_LOOP_DT;
  }

  lastRollCommand = controlState->rollCommand;

  // Ensure motor command is always within safe limits
  controlState->motorCommand = VALIDATE_RANGE(controlState->motorCommand, 0.0, 0.9);
}

bool Control_CheckSafetyConditions(const NavigationState_t* navState) {
  // Check various safety conditions

  // Check if aircraft is within safety radius
  if (navState->rangeFromDatum > controlParams.SafetyRadius) {
    return false;
  }

  // Check GPS validity
  if (!navState->gpsValid) {
    return false;
  }

  // Check if datum is set
  if (!navState->datumSet) {
    return false;
  }

  // Check altitude limits (if available)
  if (navState->altitude > MAX_ALTITUDE_AGL || navState->altitude < MIN_ALTITUDE_AGL) {
    // Note: Altitude check may not be reliable with GPS only
    // This is mainly for extreme cases
  }

  return true;
}

void Control_SetManualOverride(ControlState_t* controlState, float rollCmd, float motorCmd) {
  // Set manual control commands and disable autonomous mode
  controlState->autonomousMode = false;
  controlState->rollCommand = VALIDATE_RANGE(rollCmd, -MAX_ROLL_COMMAND, MAX_ROLL_COMMAND);
  controlState->motorCommand = VALIDATE_RANGE(motorCmd, 0.0, MAX_MOTOR_COMMAND);

  // Reset integral terms
  controlState->trackIntegral = 0.0;
  controlState->rollIntegral = 0.0;
}

void Control_ClearManualOverride(ControlState_t* controlState) {
  // Clear manual override and prepare for autonomous mode
  controlState->autonomousMode = false; // Will be re-enabled by Control_Step if conditions are met
  controlState->rollCommand = 0.0;
  controlState->motorCommand = 0.0;

  // Reset integral terms
  controlState->trackIntegral = 0.0;
  controlState->rollIntegral = 0.0;
}