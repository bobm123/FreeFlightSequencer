# Makefile for LedTest Arduino project
# Target: Adafruit QT Py SAMD21

# Arduino configuration
BOARD = adafruit:samd:adafruit_qtpy_m0
BAUD = 9600

# Project files
SKETCH = LedTest.ino

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
	if exist $(BUILD_DIR) rmdir /s /q $(BUILD_DIR)
	if exist *.hex del *.hex
	if exist *.elf del *.elf

.PHONY: all compile upload clean