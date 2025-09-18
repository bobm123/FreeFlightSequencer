/*
 * control.h - Control Library Header
 *
 * Autonomous flight control system for GPS-guided circular orbit flight.
 * Adapted from FreeFlight control library for Arduino platform.
 *
 * Control Strategy:
 * 1. Orbit Control: Maintain circular pattern around GPS datum
 * 2. Track Control: Generate roll commands for desired ground track
 * 3. Motor Control: Basic speed control for altitude management
 */

#ifndef CONTROL_H
#define CONTROL_H

#include <Arduino.h>
#include "config.h"

// Function prototypes
void Control_Init(const ControlParams_t* params);
void Control_Step(const NavigationState_t* navState, ControlState_t* controlState, float deltaTime);
void Control_Reset(ControlState_t* controlState);
void Control_SetAutonomousMode(ControlState_t* controlState, bool enable);

// Orbit control functions
float Control_ComputeOrbitError(const NavigationState_t* navState, float desiredRadius);
float Control_ComputeDesiredTrack(const NavigationState_t* navState, float orbitError);

// Track control functions
float Control_ComputeTrackError(float currentTrack, float desiredTrack);
float Control_ComputeRollCommand(float trackError, ControlState_t* controlState, float deltaTime);

// Motor control functions
float Control_ComputeMotorCommand(const NavigationState_t* navState, float deltaTime);

// Safety and validation functions
bool Control_ValidateCommands(ControlState_t* controlState);
void Control_ApplySafetyLimits(ControlState_t* controlState);
bool Control_CheckSafetyConditions(const NavigationState_t* navState);

// Manual override functions
void Control_SetManualOverride(ControlState_t* controlState, float rollCmd, float motorCmd);
void Control_ClearManualOverride(ControlState_t* controlState);

#endif // CONTROL_H