# Arduino configuration
# SAMD21 Qt Py (original platform)
BOARD = adafruit:samd:adafruit_qtpy_m0

# ESP32-S2 Qt Py (multi-board support)
#BOARD = esp32:esp32:adafruit_qtpy_esp32s2

# Project files
SKETCH = FlightSequencer.ino

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