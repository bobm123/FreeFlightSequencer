# Claude Code Generation Context

This file contains important guidelines and constraints for AI-assisted code generation in this Arduino project.

## Code Generation Guidelines

### Serial Output Character Set
**IMPORTANT**: Avoid using special Unicode characters in Serial.print() and Serial.println() statements.

**Rationale**: While the Arduino IDE supports Unicode characters, future display devices (LCD displays, terminal emulators, embedded displays, etc.) may have limited character sets that cannot render special characters properly.

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