# Arduino C Integration Project Plan

## Overview

This project plan outlines the progressive development of Arduino applications that integrate existing C libraries with the Adafruit QT Py SAMD21 hardware platform. The plan follows a building-block approach, starting with simple applications and advancing to complex flight control systems.

## Project Phases

### Phase 1: Basic Hardware Validation
**Objective**: Validate hardware platform and establish development workflow

#### 1.1 LED and Button Application
- **Description**: Simple application demonstrating basic GPIO control
- **Features**:
  - Button press detection with debouncing
  - NeoPixel LED control and status indication
  - Serial output for debugging
- **Success Criteria**: TBD after initial implementation
- **Estimated Duration**: 1-2 days
- **Dependencies**: Hardware setup, Arduino IDE configuration

### Phase 2: Device Test Suite
**Objective**: Comprehensive testing framework for all connected hardware

#### 2.1 Hardware Abstraction Layer Tests
- **Button Test**: Press detection, debouncing validation, interrupt handling
- **NeoPixel Test**: Color patterns, brightness control, power management
- **Serial Communication Test**: USB and Hardware UART functionality
- **PWM Output Tests**: Servo and ESC signal generation and validation

#### 2.2 Peripheral Integration Tests
- **GPS Module Test**: NMEA parsing, coordinate extraction, satellite status
- **Servo Control Test**: Position control, calibration, limits testing *(✅ ServoTest completed and validated)*
- **ESC Control Test**: Throttle control, arming sequence, safety features
- **System Integration Test**: All devices operating simultaneously

- **Success Criteria**: TBD after Phase 1 completion
- **Estimated Duration**: 3-5 days
- **Dependencies**: Phase 1 completion, hardware connections verified

### Phase 3: Flight Sequencer Port
**Objective**: Port PicAXE-based flight sequencer to Arduino platform

#### 3.1 Requirements Analysis
- **Source Platform**: PicAXE BASIC code analysis
- **Target Platform**: Arduino C++ with integrated C libraries
- **Flight Sequences**: Takeoff, cruise, landing patterns for free flight models
- **Timing Control**: Precision timing for servo movements and delays

#### 3.2 Architecture Design
- **State Machine**: Flight phase management
- **Timing System**: Non-blocking delays and sequence control
- **Safety Features**: Failsafe modes and emergency sequences
- **Configuration**: Adjustable parameters for different aircraft

#### 3.3 Implementation Phases
1. **Core Sequencer Engine**: State machine and timing framework *(✅ COMPLETED)*
2. **Servo Control Integration**: Position commands and smooth transitions *(✅ COMPLETED)*
3. **Safety Systems**: Timeout handling and failsafe sequences *(✅ COMPLETED)*
4. **Configuration System**: Parameter storage and adjustment *(Phase 2 - Future)*
5. **Testing and Validation**: Flight sequence simulation and validation *(✅ ALL TESTS PASSED - 1.1, 1.2, 1.3)*

- **Success Criteria**: ✅ Phase 1 COMPLETED with all validation tests passed
- **Estimated Duration**: 1-2 weeks *(Phase 1 completed in 1 week)*
- **Dependencies**: Phase 2 completion, PicAXE source code analysis *(Phase 1 requirements met)*

### Phase 4: GPS Autopilot Port
**Objective**: Port existing C-based GPS autopilot to Arduino platform

#### 4.1 C Library Integration
- **Source Analysis**: Existing C autopilot codebase evaluation
- **Module Identification**: Navigation, control, communication, parameter modules
- **Dependency Mapping**: Required libraries and hardware interfaces
- **Memory Assessment**: RAM and Flash requirements analysis

#### 4.2 Arduino Integration Architecture
- **Hardware Abstraction**: GPS, servo, ESC, and sensor interfaces
- **C Library Wrappers**: Arduino-compatible wrapper functions
- **Memory Management**: Optimization for SAMD21 constraints
- **Real-time Considerations**: Timing and interrupt handling

#### 4.3 Implementation Phases
1. **Hardware Abstraction Layer**: GPS and actuator interfaces
2. **Navigation Module Port**: GPS parsing and waypoint navigation
3. **Control Module Port**: PID controllers and servo commands
4. **Communication Port**: Telemetry and parameter interfaces
5. **Integration Testing**: Complete system validation
6. **Flight Testing**: Progressive flight test validation

- **Success Criteria**: TBD after Phase 3 completion
- **Estimated Duration**: 3-4 weeks
- **Dependencies**: Phase 3 completion, C source code access, flight testing capability

## Development Milestones

### Milestone 1: Platform Validation (End of Phase 1)
- Hardware platform operational
- Development toolchain established
- Basic GPIO and communication functional

### Milestone 2: Hardware Qualification (End of Phase 2)
- All peripheral devices tested and validated
- Test framework established for regression testing
- System integration verified

### Milestone 3: Flight Sequencer Operational (End of Phase 3) ✅ ACHIEVED
- ✅ PicAXE functionality successfully ported to QtPY SAMD21
- ✅ Flight sequences operational and tested (ALL TESTS 1.1, 1.2, 1.3 PASSED)
- ✅ Multi-flight operation validated (state variable reset bug fixed)
- ✅ Safety systems validated (emergency cutoff in all active states, reset functionality)
- ✅ Enhanced safety features (emergency cutoff during spool, run, and glide phases)
- **Phase 1 Status**: ✅ COMPLETED - Production-ready flight sequencer with hardcoded parameters
- **Phase 2 Status**: READY TO BEGIN - Parameter programming interface

### Milestone 4: Autopilot System Complete (End of Phase 4)
- C library integration successful
- GPS navigation and flight control operational
- System ready for flight testing and deployment

## Technical Approach

### C Library Integration Strategy
1. **Preserve Original Code**: Keep existing C libraries unchanged when possible
2. **Wrapper Architecture**: Create Arduino-compatible wrapper functions
3. **Memory Optimization**: Use PROGMEM and optimize for SAMD21 constraints
4. **Modular Design**: Enable selective module integration
5. **Testing Framework**: Comprehensive validation at each integration step

### Development Tools and Environment
- **Arduino IDE**: Primary development environment with Verify/Upload workflow
- **Arduino CLI**: Command-line builds using Makefile for each application
- **Hardware Debugging**: Serial monitor and status LED feedback
- **Version Control**: Git repository with incremental commits and proper .gitignore
- **Documentation**: Progressive documentation with each phase
- **Testing**: Automated test suites where possible

### Risk Mitigation
- **Memory Constraints**: Early memory usage monitoring and optimization
- **Timing Requirements**: Careful analysis of real-time constraints
- **Hardware Integration**: Progressive testing of each component
- **Flight Safety**: Extensive ground testing before flight validation
- **Code Complexity**: Modular approach with clear interfaces

## Project Directory Structure

### Overview

The directory structure promotes code reuse, modular development, and clear separation between applications and shared libraries across project phases.

### Root Directory Structure

```
ProjectRoot/
├── applications/                     # Individual Arduino applications
│   ├── LedButton/                   # Phase 1: LED and Button app
│   ├── DeviceTests/                 # Phase 2: Device test suite
│   ├── FlightSequencer/             # Phase 3: Flight sequencer
│   ├── GpsAutopilot/                # Phase 4: GPS autopilot
│   └── examples/                    # Simple example applications
├── lib/                             # Original C code libraries (unchanged)
│   ├── module1/                     # Software modules from original project
│   ├── module2/
│   └── moduleN/
├── shared/                          # Reusable Arduino components
│   ├── hardware/                    # Hardware abstraction layer
│   ├── wrappers/                    # C library wrapper functions
│   ├── utilities/                   # Common utility functions
│   └── tests/                       # Shared testing framework
├── hardware/                        # Hardware documentation and files
├── docs/                           # Project documentation
├── tools/                          # Development tools and scripts
├── .gitignore                      # Git ignore patterns
├── .gitattributes                  # Git file handling attributes
├── README.md                       # Project overview and setup
└── CLAUDE.md                       # AI code generation guidelines
```

### Application Directory Structure

Each application follows a consistent internal structure:

```
applications/application_name/
├── application_name.ino             # Main Arduino sketch
├── README.md                        # Application-specific documentation
├── config.h                        # Application configuration
├── src/                            # Application-specific source files
└── tests/                          # Application-specific tests
```

### Code Reuse Strategy

#### Phase Development Progression
1. **Phase 1**: Develop basic HAL components (button, LED)
2. **Phase 2**: Extend HAL with additional devices, create test framework
3. **Phase 3**: Reuse HAL components, add timing utilities and state machine
4. **Phase 4**: Reuse all previous components, add C library wrappers

#### Shared Components
- **Hardware Abstraction Layer**: GPIO, serial, PWM, button, NeoPixel, GPS, servo, ESC
- **C Library Wrappers**: Arduino-compatible interfaces for original C modules
- **Utilities**: Debug, memory monitoring, timing, math, configuration storage
- **Testing Framework**: Hardware validation and integration tests

## Resource Requirements

### Hardware
- Adafruit QT Py SAMD21 development board
- Signal distribution board with connections
- GPS module, servo, ESC, and test fixtures
- USB programming cable and power supply

### Software
- Arduino IDE with SAMD21 board support
- Required libraries (Servo, NeoPixel, FlashStorage)
- Serial monitor and debugging tools
- Git version control system with proper repository structure

### Documentation
- Source code for PicAXE flight sequencer
- C library source code for autopilot
- Hardware schematics and connection diagrams
- Flight testing procedures and safety protocols

## Version Control with Git

### Repository Structure
The project uses Git for version control with a structured approach to track development across phases while maintaining clean history and proper file management.

### Git Configuration Files

#### .gitignore
```gitignore
# Arduino IDE generated files
*.hex
*.elf
*.bin
*.map

# Build artifacts
build/
*.o
*.a
*.so

# Arduino IDE specific
.arduino15/
libraries/
hardware/

# Platform specific
.DS_Store
Thumbs.db
*.tmp
*.bak
*.swp
*~

# IDE and editor files
.vscode/
.idea/
*.sublime-*
*.code-workspace

# Documentation build artifacts
docs/_build/
docs/.doctrees/

# Test artifacts
test_results/
coverage/

# Temporary files
temp/
tmp/
*.log

# Hardware design files (optional - keep source, ignore outputs)
hardware/**/*.brd.backup
hardware/**/*.sch.backup
hardware/**/gerbers/
hardware/**/drill/
hardware/**/pick_place/

# Keep important hardware files
!hardware/**/*.kicad_sch
!hardware/**/*.kicad_pcb
!hardware/**/*.kicad_pro
!hardware/**/*.png
!hardware/**/*.pdf
```

#### .gitattributes
```gitattributes
# Set default line endings
* text=auto

# Arduino files
*.ino text eol=lf
*.h text eol=lf
*.c text eol=lf
*.cpp text eol=lf

# Documentation
*.md text eol=lf
*.txt text eol=lf

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.pdf binary
*.zip binary

# KiCad files
*.kicad_sch text eol=lf
*.kicad_pcb text eol=lf
*.kicad_pro text eol=lf
```

### Development Workflow
1. **Feature Branches**: Create branches for each phase development
2. **Incremental Commits**: Small, focused commits with clear messages
3. **Documentation Updates**: Keep docs synchronized with code changes
4. **Shared Component Versioning**: Tag releases when shared components are stable
5. **Cross-Phase Validation**: Test applications when shared components change

### Commit Message Convention
```
[PHASE] Component: Brief description

Longer description if needed explaining the changes,
rationale, and any breaking changes.

- Bullet points for specific changes
- Reference issues or requirements addressed
```

Examples:
- `[PHASE1] HAL: Add button debouncing with configurable timing`
- `[PHASE2] Tests: Implement GPS module validation framework`
- `[SHARED] Utils: Add memory monitoring utilities for SAMD21`

## Build System

### Dual Build Approach
Each application supports both Arduino IDE and command-line builds for flexibility in development environments.

### Arduino IDE Build Process
Standard Arduino development workflow:
1. Open application `.ino` file in Arduino IDE
2. Select board: `Tools > Board > Adafruit SAMD Boards > Adafruit QT Py (SAMD21)`
3. Select port: `Tools > Port > [COM port or /dev/ttyX]`
4. **Verify** (Ctrl+R): Compile without uploading
5. **Upload** (Ctrl+U): Compile and flash to device

### Arduino CLI Build Process

#### Simple Applications (Single .ino files)
Simple Arduino sketches use a standardized build pattern with Makefiles located in each sketch directory:

```makefile
# Simple Arduino sketch Makefile template
# Located in: applications/[app_name]/Makefile

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

# Clean build artifacts (Windows-compatible)
clean:
	if exist $(BUILD_DIR) rmdir /s /q $(BUILD_DIR)
	if exist *.hex del *.hex
	if exist *.elf del *.elf

.PHONY: all compile upload clean
```

**Key Features:**
- File dependency checking prevents unnecessary recompilation
- Uses `ARDUINO_PORT` environment variable for uploads
- Windows-compatible clean commands
- Located in sketch directory alongside .ino file

#### Serial Monitoring
Serial monitoring uses a batch file in the project root (`monitor.bat`):

```batch
@echo off
setlocal

if "%1"=="" (
    if "%ARDUINO_PORT%"=="" (
        echo Error: No COM port specified. Either set ARDUINO_PORT environment variable or pass port as argument.
        echo Usage: monitor.bat [COM_PORT]
        echo Example: monitor.bat COM4
        exit /b 1
    )
    set PORT=%ARDUINO_PORT%
) else (
    set PORT=%1
)

echo Starting serial monitor on %PORT% at 9600 baud...
arduino-cli monitor --port %PORT% --config baudrate=9600
```

#### Complex Applications (Future)
Complex applications with libraries and shared code will use an extended Makefile structure:

```makefile
# Complex application Makefile template (Future use)
# Located in: applications/[app_name]/Makefile

# Configuration
BOARD_FQBN = adafruit:samd:adafruit_qtpy_m0
SKETCH = $(shell basename $(CURDIR)).ino

# Shared library paths
SHARED_HARDWARE = ../../shared/hardware
SHARED_UTILITIES = ../../shared/utilities
SHARED_WRAPPERS = ../../shared/wrappers

# Build directory
BUILD_DIR = build

# Default target
all: compile

# Compile sketch with library paths
compile:
	arduino-cli compile --fqbn $(BOARD_FQBN) --build-path $(BUILD_DIR) \
		--library $(SHARED_HARDWARE) \
		--library $(SHARED_UTILITIES) \
		--library $(SHARED_WRAPPERS) .

# Upload to device
upload: compile
	arduino-cli upload --fqbn $(BOARD_FQBN) --port $(ARDUINO_PORT) --input-dir $(BUILD_DIR)

# Install required libraries
install-deps:
	arduino-cli lib install "Adafruit NeoPixel"
	arduino-cli lib install "FlashStorage"
	arduino-cli lib install "Servo"

.PHONY: all compile upload install-deps
```

#### Root Makefile
```makefile
# Root project Makefile
# Builds all applications

APPLICATIONS = LedButton DeviceTests FlightSequencer GpsAutopilot

# Build all applications
all:
	@for app in $(APPLICATIONS); do \
		echo "Building $$app..."; \
		$(MAKE) -C applications/$$app compile; \
	done

# Clean all applications
clean:
	@for app in $(APPLICATIONS); do \
		echo "Cleaning $$app..."; \
		$(MAKE) -C applications/$$app clean; \
	done

# Install dependencies for all applications
install-deps:
	arduino-cli core update-index
	arduino-cli core install adafruit:samd
	@for app in $(APPLICATIONS); do \
		$(MAKE) -C applications/$$app install-deps; \
	done

# Show help
help:
	@echo "Available targets:"
	@echo "  all          - Build all applications"
	@echo "  clean        - Clean all build artifacts"
	@echo "  install-deps - Install Arduino CLI dependencies"
	@echo "  help         - Show this help message"

.PHONY: all clean install-deps help
```

#### Arduino CLI Setup
```bash
# Install Arduino CLI (one time setup)
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Initialize configuration
arduino-cli config init

# Update package index
arduino-cli core update-index

# Install SAMD board support
arduino-cli core install adafruit:samd

# Install required libraries
arduino-cli lib install "Adafruit NeoPixel"
arduino-cli lib install "FlashStorage" 
arduino-cli lib install "Servo"
```

### Build System Benefits
- **IDE Users**: Familiar Arduino IDE workflow with Verify/Upload
- **CLI Users**: Automated builds, scripting, and CI/CD integration
- **Memory Analysis**: Easy memory usage reporting via Makefile
- **Dependency Management**: Automated library installation
- **Batch Operations**: Build/clean multiple applications at once

### Integration with Git Workflow
```bash
# Example development workflow
git checkout -b feature/button-debounce
cd applications/LedButton
make compile                    # Test build
make upload                     # Flash to device
make monitor                    # Test functionality
git add -A && git commit -m "[PHASE1] HAL: Improve button debouncing"
```

This progressive approach ensures each phase builds upon the previous foundation while validating both hardware integration and C library porting techniques. Success metrics will be defined and refined as we complete each phase and gain practical experience with the platform.