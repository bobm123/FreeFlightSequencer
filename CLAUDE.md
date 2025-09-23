# Claude Code Generation Context

This file contains important guidelines and constraints for AI-assisted code generation in this Arduino project.

## 🚀 Current Project Status - Dual Flight Control System Complete

### ✅ GPS Autopilot System (READY FOR FLIGHT TESTING)
The GPS autopilot system has been fully implemented and is ready for comprehensive testing:

**Core Features Implemented:**
- Complete state machine: READY → ARMED → MOTOR_SPOOL → GPS_GUIDED_FLIGHT → EMERGENCY/LANDING
- GPS-based navigation with NMEA parsing (supports GNGGA and GNRMC sentences)
- Autonomous circular flight pattern around launch datum
- Button-controlled progression (long press = ARM, short press = launch)
- Dual LED system: Red for flight states + Blue flash for GPS data reception
- GPS signal loss failsafe with configurable gentle turn and reduced power
- Full GUI integration with real-time status display and parameter control

### ✅ FlightSequencer System (PRODUCTION READY)
Enhanced E36-Timer replacement with advanced data handling:

**Core Features Implemented:**
- Complete flight sequencing: READY → ARMED → MOTOR_SPOOL → MOTOR_RUN → GLIDE → DT_DEPLOY → LANDING
- GPS data logging with robust CSV parsing and error recovery
- Parameter programming: motor time, flight time, motor speed, DT servo positions, dwell time
- Emergency cutoff capability from all flight states
- Multi-format data export: JSON, CSV, KML with flight path visualization
- **LATEST**: Robust CSV parsing handles transmission line breaks in GPS coordinates

### ✅ Unified GUI System (FULLY OPERATIONAL)
Multi-tab interface managing both flight control systems:

**Core Features Implemented:**
- Multi-application support with automatic tab switching
- Real-time parameter synchronization from Arduino responses
- Robust flight data download with automatic error recovery
- Flight path visualization with matplotlib integration
- Export capabilities: JSON, CSV, KML formats for analysis
- **LATEST**: Fixed "could not convert string to float: '-'" parsing error

**Hardware Configuration:**
- QtPY SAMD21 + Signal Distribution MkII
- Roll servo on A3, Motor ESC on A2, Button on A0, NeoPixel on pin 11
- GPS module on Serial1 (TX/RX pins) - optional for FlightSequencer, required for GPS Autopilot

**Ready for Operation:**
1. **GPS Autopilot**: Ready for flight testing of autonomous navigation
2. **FlightSequencer**: Field-tested with robust data recovery capabilities
3. **GUI Interface**: Handles both applications with comprehensive error handling
4. **Data Analysis**: Complete flight data export and visualization pipeline

**Last Working State:** Both flight control systems operational with GUI providing comprehensive parameter control, real-time monitoring, and robust data export capabilities. CSV parsing robustness improvements ensure reliable flight data recovery even with transmission errors.

## Code Generation Guidelines

### Serial Output Character Set
**CRITICAL**: Never use Unicode characters anywhere in Arduino code - including Serial.print(), Serial.println(), and ALL COMMENTS.

**Rationale**: While the Arduino IDE supports Unicode characters, future display devices (LCD displays, terminal emulators, embedded displays, etc.) may have limited character sets that cannot render special characters properly. Unicode in comments can also cause compilation issues on different systems.

**This applies to:**
- All Serial.print() and Serial.println() statements
- All code comments (// and /* */)
- All string literals and constants
- All variable names and function names

**Examples:**
```cpp
// AVOID - Special Unicode characters
Serial.println("[PASS] Test passed");
Serial.println("[FAIL] Test failed");
Serial.println("[DEBUG] Debug info");
Serial.println("[WARN] Warning");

// PREFERRED - Standard ASCII characters
Serial.println("[OK] Test passed");
Serial.println("[FAIL] Test failed");
Serial.println("[DEBUG] Debug info"); 
Serial.println("[WARN] Warning");
```

**Alternative Approaches:**
- Use standard ASCII brackets: `[OK]`, `[FAIL]`, `[WARN]`, `[INFO]`, `[DEBUG]`
- Use text indicators: `PASS`, `FAIL`, `ERROR`, `WARNING`, `INFO`
- Use simple symbols: `+`, `-`, `!`, `*`, `>`

### Additional Guidelines

#### Memory Efficiency
- Prefer `F()` macro for string literals to store them in Flash memory
- Example: `Serial.println(F("System initialized"));`

#### Consistent Formatting
- Use consistent prefixes for log levels
- Include timestamps when appropriate
- Keep messages concise but informative

#### Example Serial Output Format
```cpp
// Consistent logging format
Serial.println(F("[INIT] Hardware initialization starting..."));
Serial.println(F("[OK] Button HAL initialized"));
Serial.println(F("[OK] NeoPixel HAL initialized"));
Serial.println(F("[WARN] GPS not detected, continuing without GPS"));
Serial.println(F("[INFO] System ready"));
```

This ensures maximum compatibility across different display devices and maintains professional, readable output formatting.

## Arduino Build System Guidelines

### Simple Arduino Sketch Build Pattern
For single-file Arduino sketches (like device tests and simple applications), use this standardized build approach:

#### Makefile Structure
- Place Makefile in each sketch directory alongside the .ino file
- Use file dependencies to avoid unnecessary recompilation
- Standard targets: `all`/`compile`, `upload`, `clean`
- Cross-platform compatible commands in clean target

#### Environment Variables
- Use `ARDUINO_PORT` environment variable for upload/monitor operations
- Let arduino-cli fail gracefully if environment variable not set
- No error checking or fallback logic in Makefiles

#### Serial Monitoring
- Use `monitor.bat` in project root for serial monitoring
- Accept COM port as command line argument or from `ARDUINO_PORT`
- Hard-coded 9600 baud rate (revisit for complex applications)

#### Example Makefile Template
```makefile
# Arduino configuration
BOARD = adafruit:samd:adafruit_qtpy_m0
BAUD = 9600

# Project files
SKETCH = [SketchName].ino

# Build directory
BUILD_DIR = build

# Default target
all: compile

# Compile the sketch
compile: $(BUILD_DIR)/$(SKETCH).bin

$(BUILD_DIR)/$(SKETCH).bin: $(SKETCH)
	arduino-cli compile --fqbn $(BOARD) --output-dir $(BUILD_DIR) $(SKETCH)

# Upload to board
upload: $(BUILD_DIR)/$(SKETCH).bin
	arduino-cli upload --fqbn $(BOARD) --port $(ARDUINO_PORT) --input-dir $(BUILD_DIR) $(SKETCH)

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)
	rm -f *.hex *.elf

.PHONY: all compile upload clean
```

#### Build System Design Principles
- **Simplicity over complexity**: Use standard Unix commands (`rm -rf`, `rm -f`) instead of platform-specific conditionals
- **Cross-platform compatibility**: Avoid Windows batch syntax (`if exist`, `rmdir /s /q`) in favor of bash-compatible commands
- **Fail-safe operations**: Commands like `rm -f` handle missing files gracefully without errors
- **Consistent behavior**: Same Makefile works across different development environments

**Note**: This pattern is suitable for simple sketches. Complex applications with libraries and shared code will require adapted build systems.

### Test Application Structure
When creating device test applications, follow this standardized structure:

#### Required Files
All test applications must include these four files:
```
applications/DeviceTests/<TestName>/
|-- <TestName>.ino           # Main test sketch
|-- <TestName>Spec.md        # Test specification with objectives and pass criteria
|-- Makefile                 # Arduino build system (using template above)
`-- ExpectedResults.txt      # Sample output showing expected serial messages
```

#### Test Specification Guidelines
The `<TestName>Spec.md` file should include:
- **Overview**: Brief description of test purpose
- **Hardware Requirements**: Required components and connections
- **Test Objectives**: What functionality is being validated
- **Test Sequence**: Step-by-step test phases
- **Expected Behavior**: What should happen during successful test
- **Pass Criteria**: Specific requirements for test success
- **Failure Modes**: Common issues and troubleshooting

#### Expected Results Format
The `ExpectedResults.txt` file should contain:
- Sample serial output from successful test run
- Key messages showing test progression
- Timing information where relevant
- Statistical summaries and completion messages

This standardized structure ensures consistent documentation, build capability, and validation reference for all device test applications.

## Parameter Management Design Pattern

### Overview
For managing real-time parameters between Arduino applications and GUI tabs, use this proven single-source-of-truth architecture to avoid ad hoc response handling and ensure consistent GUI state.

### Core Principles
1. **Single Parameter Store** - One canonical source for each tab's parameter values
2. **Comprehensive Response Parsing** - Parse ALL Arduino response formats that indicate parameter changes
3. **Automatic GUI Sync** - GUI fields always reflect the current parameter store
4. **Simple Commands** - Buttons send commands only, no response expectations

### Recent Implementation Success: FlightSequencer CSV Parsing Robustness

The FlightSequencer tab now includes advanced CSV parsing capabilities that handle real-world transmission issues:

#### CSV Parsing Error Recovery
- **Problem Solved**: GPS coordinates split across transmission boundaries (e.g., longitude `-77.196556` transmitted as `-` on one line, `77.196556` on next)
- **Solution**: Multi-line record reassembly with coordinate validation
- **Error Handling**: Gracefully skip corrupted records while preserving valid flight data
- **Debug Support**: Automatic preservation of problematic data for analysis

#### Implementation Example
```python
# Detect incomplete GPS records and merge with next line
if line.startswith('GPS,'):
    parts = line.split(',')
    # Check for incomplete coordinate values (just a minus sign)
    if len(parts) >= 6:
        lat_field = parts[4] if len(parts) > 4 else ""
        lon_field = parts[5] if len(parts) > 5 else ""
        if lat_field in ["-", ""] or lon_field in ["-", ""]:
            # Merge with next line to complete the record
            merged_line = line + next_line.strip()
```

This pattern successfully resolved the "could not convert string to float: '-'" error and provides a template for handling similar transmission artifacts in other applications.

### Implementation Pattern

#### 1. Parameter Store Definition
```python
# Single source of truth for [TabName] parameters
self.current_[tab]_params = {
    'param1': None,
    'param2': None,
    'param3': None,
    'current_state': 'UNKNOWN'
}
```

#### 2. Serial Data Handler
```python
def handle_serial_data(self, data):
    """Handle incoming serial data for [TabName]."""
    # Display in serial monitor
    self.serial_monitor_widget.log_received(data)

    # Update canonical parameter store from ANY Arduino response
    self._update_parameter_store(data)

    # Update GUI to reflect current parameter store
    self._sync_gui_with_parameters()

    # Handle other responses (downloads, etc.)
    self._handle_other_responses(data)
```

#### 3. Comprehensive Parameter Parsing
```python
def _update_parameter_store(self, data):
    """Update canonical parameter store from any Arduino response."""
    # Parse ALL possible formats for each parameter:
    # "[INFO] Param1: 123" (from G command)
    # "[OK] Param1 = 456" (from set command)
    # "[WARN] Param1 out of range (10-100)" (extract limits)

    param1_match = re.search(r'Param1[:\s=]+(\d+)', data, re.IGNORECASE)
    if param1_match:
        self.current_[tab]_params['param1'] = int(param1_match.group(1))

    # State/phase detection from messages
    if re.search(r'specific state message', data, re.IGNORECASE):
        self.current_[tab]_params['current_state'] = 'STATE_NAME'
```

#### 4. Automatic GUI Synchronization
```python
def _sync_gui_with_parameters(self):
    """Update GUI fields to match canonical parameter store."""
    def update_gui():
        params = self.current_[tab]_params

        # Update input fields with current parameter values
        if params['param1'] is not None:
            self.param1_var.set(str(params['param1']))

        # Update status displays
        self.current_state_var.set(f"State: {params['current_state']}")

    self.parent.after(0, update_gui)
```

#### 5. Simple Command Methods
```python
def _set_param1(self):
    """Set param1 value."""
    try:
        value = self.param1_var.get().strip()
        # Validate if needed
        command = f"P1 {value}"
        self._send_command(command)  # Just send command, automatic update
    except ValueError as e:
        messagebox.showerror("Invalid Value", str(e))

def _get_parameters(self):
    """Get current parameters."""
    self._send_command("G")  # Just send command, no response handling

def _reset_parameters(self):
    """Reset parameters to defaults."""
    if messagebox.askyesno("Reset", "Reset to defaults?"):
        self._send_command("R")  # Just send command, automatic update
```

#### 6. Connection Handling
```python
def handle_connection_change(self, connected):
    """Handle connection status changes."""
    if not connected:
        self._clear_parameters()
    else:
        # Auto-request current state after connection settles
        self.parent.after(2500, self._get_parameters)

def _clear_parameters(self):
    """Clear parameter store and GUI when disconnected."""
    def clear_params():
        # Reset canonical parameter store
        self.current_[tab]_params = {
            'param1': None,
            'param2': None,
            'current_state': 'DISCONNECTED'
        }
        # Clear GUI fields
        self.param1_var.set("")
        self.current_state_var.set("State: DISCONNECTED")

    self.parent.after(0, clear_params)
```

### Benefits of This Pattern
- **Eliminates Race Conditions** - No timing dependencies between commands and responses
- **Handles All Response Formats** - Comprehensive parsing catches any parameter mention
- **Automatic GUI Updates** - No manual field updates needed
- **Clean Command Logic** - Commands just send, responses automatically update
- **Single Source of Truth** - Parameter values always consistent
- **Easy to Extend** - Add new parameters by extending the store and parsing

### Anti-Patterns to Avoid
```python
# BAD - Ad hoc response handling
def _set_param(self):
    self._send_command("P 123")
    self.parent.after(1000, self._update_fields_maybe)  # Race condition

# BAD - Command-specific response expectations
def _reset_params(self):
    self._send_command("R")
    self.parent.after(1000, self._get_parameters)  # Double command

# BAD - Manual field updates
def handle_response(self, data):
    if "OK Motor" in data:
        self.motor_var.set("some_value")  # Inconsistent with other updates
```

### Implementation Checklist
When adding this pattern to a new tab:
- [ ] Define canonical parameter store dictionary
- [ ] Implement comprehensive response parsing in `_update_parameter_store()`
- [ ] Create automatic GUI sync in `_sync_gui_with_parameters()`
- [ ] Simplify all command methods to just send commands
- [ ] Handle connection changes with store clearing and auto-refresh
- [ ] Test with all Arduino response formats (INFO, OK, ERR, etc.)
- [ ] Verify GUI updates immediately on any parameter change

## Finite State Machine (FSM) Design Guidelines

### FSM Implementation Principles
When implementing finite state machines in Arduino applications, follow these established patterns:

#### State Responsibility
- Each state should have a single, well-defined responsibility
- Announcement states handle messages and timing delays only
- Action states perform the actual work (LED control, sensor reading, etc.)
- Avoid mixing state responsibilities to maintain clean separation

#### State Transitions
- Use `advanceToNextPhase()` function for consistent state transitions
- Initialize `phaseStep = -1` to ensure first iteration (index 0) executes properly
- Reset timing and flags consistently on each transition
- Maintain `phaseElapsed = currentTime - phaseStartTime` for phase-relative timing

#### Moore vs Mealy FSM Patterns
- **Prefer Moore FSM**: Outputs depend only on current state, easier to debug and maintain
- **Avoid Mealy FSM**: Outputs depend on state + inputs, creates coupling between states
- Never implement functionality of one state within another state

#### Variable Initialization Principles
- **Always initialize to legal values**: Never use "magic" illegal values (-1, 255, etc.) expecting other code to fix them
- **Explicit state management**: If you need "not set" state, use explicit flags or enums, not out-of-range values
- **Defensive programming**: All variables should hold valid values at all times to prevent hard-to-debug failures
- **Flight-critical systems**: Invalid states can cause catastrophic failures in control systems

#### State Machine Structure
```cpp
enum TestPhase {
  PHASE_ANNOUNCE_X,     // Announcement and preparation
  PHASE_EXECUTE_X,      // Actual work execution  
  PHASE_ANNOUNCE_Y,     // Next announcement
  PHASE_EXECUTE_Y,      // Next work execution
  PHASE_COMPLETE        // Final state
};

void advanceToNextPhase(TestPhase nextPhase) {
  currentPhase = nextPhase;
  phaseStartTime = millis();
  phaseStep = -1;  // Ensures first iteration (index 0) executes
  phaseMessageSent = false;
}
```

#### Common FSM Anti-Patterns to Avoid
- **Cross-state coupling**: Implementing work logic in announcement states
- **Initialization errors**: Starting `phaseStep` at 0 when first index is 0
- **Timing chain breaks**: Not resetting `phaseStartTime` properly on transitions
- **State order dependencies**: Creating hidden dependencies between state order

These patterns ensure maintainable, debuggable state machines suitable for complex flight control and navigation systems.

## GUI Design Guidelines

### Tkinter Layout Alignment Principles

#### Label Alignment in Parameter Forms
When creating parameter input forms with labels, entry fields, and buttons, ensure consistent alignment using fixed-width labels rather than spacing characters.

**Problem**: Using spaces or manual padding in label text does not provide reliable alignment across different fonts and platforms.

```python
# AVOID - Unreliable spacing with manual characters
ttk.Label(frame, text="Motor Run Time (sec): ").pack(side='left')     # 1 space
ttk.Label(frame, text="DT Retracted (us):    ").pack(side='left')     # 4 spaces
ttk.Label(frame, text="DT Deployed (us):     ").pack(side='left')     # 5 spaces
```

**Solution**: Use consistent `width` parameter on all labels to create uniform column alignment.

```python
# PREFERRED - Fixed width ensures perfect alignment
ttk.Label(frame, text="Motor Run Time (sec):", width=22).pack(side='left')
ttk.Label(frame, text="Total Flight Time (sec):", width=22).pack(side='left')
ttk.Label(frame, text="Motor Speed (95-200):", width=22).pack(side='left')
ttk.Label(frame, text="DT Retracted (us):", width=22).pack(side='left')
ttk.Label(frame, text="DT Deployed (us):", width=22).pack(side='left')
ttk.Label(frame, text="DT Dwell Time (sec):", width=22).pack(side='left')
```

#### Width Sizing Guidelines
- **Measure the longest label text** in the group and add 2-3 characters for padding
- **Use consistent width** across all related labels in the same form section
- **Standard widths**: 15 chars for short labels, 22 chars for medium labels, 30 chars for long labels
- **Test on different platforms** to ensure alignment works on Windows, Mac, and Linux

#### Benefits
- **Professional appearance**: Perfect vertical alignment of input fields and buttons
- **Cross-platform consistency**: Width-based alignment works regardless of font rendering
- **Maintainable code**: Easy to add new parameters without breaking alignment
- **User experience**: Consistent visual structure improves form usability

This pattern should be applied to all parameter input forms, configuration dialogs, and settings panels in the GUI applications.