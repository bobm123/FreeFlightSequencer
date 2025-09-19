# GpsAutopilot Makefile
# Arduino build system for QtPY SAMD21

# Arduino configuration
BOARD = adafruit:samd:adafruit_qtpy_m0
BAUD = 9600

# Project files
SKETCH = GpsAutopilot.ino
SOURCES = navigation.cpp control.cpp communications.cpp math_utils.cpp hardware_hal.cpp

# Build directory
BUILD_DIR = build

# Default target
all: compile

# Compile the sketch
compile: $(BUILD_DIR)/$(SKETCH).bin

$(BUILD_DIR)/$(SKETCH).bin: $(SKETCH) $(SOURCES) *.h
	arduino-cli compile --fqbn $(BOARD) --output-dir $(BUILD_DIR) $(SKETCH)

# Upload to board
upload: $(BUILD_DIR)/$(SKETCH).bin
	arduino-cli upload --fqbn $(BOARD) --port $(ARDUINO_PORT) --input-dir $(BUILD_DIR) $(SKETCH)

# Clean build artifacts
#	rm -rf $(BUILD_DIR)
#	rm -f *.hex *.elf
clean:
	del /Q $(BUILD_DIR)

.PHONY: all compile upload clean