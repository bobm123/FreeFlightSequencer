# Arduino C Code Integration Guide

This comprehensive guide covers integrating existing C libraries and legacy code into Arduino projects with minimal modifications to the original source.

## Overview and Key Principles

- Keep C code free of `main()` and OS dependencies
- Use `extern "C"` for safe linking with C++/Arduino code  
- Wrap functions that expect OS, file I/O, or hardware outside Arduino's model
- Watch for memory limits, naming collisions, and platform portability
- Preserve original C code unchanged when possible

## 1. Build System & File Structure

### Fundamentals
- Arduino IDE compiles `.ino` files as C++ and automatically generates prototypes
- You can add `.c` and `.h` files directly — the build system compiles them with `avr-gcc` or the board's compiler
- Arduino provides its own `main()`, so your C code must not define `main()`
- Use `extern "C"` in headers when calling C functions from C++ code to prevent name mangling

### Basic extern "C" Pattern
```c
// wrapper.h
#ifdef __cplusplus
extern "C" {
#endif

void my_c_function(int val);

#ifdef __cplusplus
}
#endif
```

### Header Conflicts and Solutions

**Problem:**
```c
// original_code.h
void my_c_function(void);

// In Arduino sketch - may cause linker errors
#include "original_code.h"
```

**Solution - Create Wrapper Header:**
```cpp
// arduino_wrapper.h
#ifdef __cplusplus
extern "C" {
#endif

#include "original_code.h"

#ifdef __cplusplus
}
#endif
```

## 2. Memory & Resource Constraints

### Understanding Arduino Memory Limits
AVR microcontrollers have very limited RAM (2KB on Arduino Uno). Large arrays can cause stack overflow.

### Problem Example
```c
// This will likely crash on Arduino Uno
void processData() {
    char buffer[1024];  // Too large for 2KB RAM!
    // ... processing code
}
```

### Memory Solutions
```c
// Option 1: Use PROGMEM for constants
#include <avr/pgmspace.h>
const char lookupTable[] PROGMEM = { /* large data */ };

// Option 2: Reduce buffer size
void processData() {
    char buffer[64];  // Much safer size
    // ... processing code
}

// Option 3: Dynamic allocation (use carefully)
#ifdef ARDUINO
    char* buffer = (char*)malloc(size);  // Check if NULL!
    if (buffer != NULL) {
        // ... use buffer
        free(buffer);
    }
#endif
```

### Memory Monitoring
```cpp
// Add to your sketch for memory monitoring
void printFreeMemory() {
    extern int __heap_start, *__brkval; 
    int v; 
    int freeMemory = (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval); 
    Serial.print("Free memory: ");
    Serial.println(freeMemory);
}
```

## 3. Standard Library Limitations

### Missing Functions
Arduino's libc is minimal - many standard functions are missing or limited.

```c
// These typically won't work on Arduino:
FILE* fp = fopen("file.txt", "r");     // No file system
void* ptr = malloc(100);               // Limited/risky malloc
printf("Hello %d\n", value);          // No printf
```

### Arduino Alternatives
```c
// Arduino wrapper function for printf
void c_printf(const char* format, int value) {
    #ifdef ARDUINO
        Serial.print("Value: ");
        Serial.println(value);
    #else
        printf(format, value);
    #endif
}

// Override printf for Arduino (advanced technique)
extern "C" int printf(const char* format, ...) {
    char buffer[128];
    va_list args;
    va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    Serial.print(buffer);
    return strlen(buffer);
}
```

## 4. Compiler & Language Compatibility

### Common Issues
- Arduino compiles with modern C++ (C++17+ depending on platform)
- No implicit `int` (fix older code)
- Mixed code and declarations must follow C99/C++ rules
- Inline assembly may need adaptation per MCU (AVR, ARM, ESP32)

### Compiler-Specific Code to Avoid
```c
// MSVC-specific - won't work on Arduino
__declspec(dllexport) void myFunction();

// GCC extension - may work but not portable
void myFunction() __attribute__((weak));
```

### Arduino-Compatible Alternatives
```c
// Standard C - works everywhere
void myFunction(void);
```

## 5. Hardware Abstraction & Platform Dependencies

### OS Dependencies
C code written for desktop/OS environments may require stubbing or replacing parts.

**Original C Code:**
```c
// sensor_reader.c
#include <stdio.h>

void readSensor() {
    int value = getSensorValue();
    printf("Sensor: %d\n", value);
}
```

**Arduino Wrapper:**
```cpp
// sensor_arduino.cpp
#include "sensor_reader.h"

void arduino_readSensor() {
    readSensor();  // Calls original function
}
```

### Hardware Interface Considerations
- Bare-metal register access may conflict with Arduino's core libraries
- Decide whether to keep direct register manipulation or wrap with Arduino APIs like `Serial`, `digitalWrite`, etc.
- Example: `fopen`, `fread` can be wrapped with Arduino's SD library equivalents

## 6. Cross-Platform & Portability

### Data Types
```c
// Use fixed-width types from <stdint.h> for portability
uint8_t  data;     // Instead of unsigned char
uint16_t value;    // Instead of unsigned int
uint32_t counter;  // Instead of unsigned long

// Avoid assuming word sizes
int32_t explicit_int;  // Instead of int
```

### Conditional Compilation
```c
// Use preprocessor directives for platform-specific code
#ifdef ARDUINO
    #include <Arduino.h>
    #define DEBUG_PRINT(x) Serial.println(x)
    #define DELAY_MS(x) delay(x)
    #define GET_TIME() millis()
#else
    #include <stdio.h>
    #include <unistd.h>
    #include <time.h>
    #define DEBUG_PRINT(x) printf("%s\n", x)
    #define DELAY_MS(x) usleep((x) * 1000)
    #define GET_TIME() (unsigned long)time(NULL)
#endif
```

## 7. Naming Conflicts & Namespaces

The Arduino global namespace can cause collisions. If your C code uses common names like `init` or `delay`, rename or wrap them.

```c
// Problematic - conflicts with Arduino delay()
void delay(int ms);

// Better - use prefixed names
void mylib_delay(int ms);

// Or wrap with different name
void custom_wait(int ms) {
    #ifdef ARDUINO
        delay(ms);
    #else
        mylib_delay(ms);
    #endif
}
```

## 8. Timing Considerations

C code may assume faster processors or different timing models.

### Problematic Code
```c
// May cause watchdog reset on Arduino
void longCalculation() {
    for(int i = 0; i < 1000000; i++) {
        complexMath();
    }
}
```

### Arduino-Safe Version
```c
void longCalculation() {
    for(int i = 0; i < 1000000; i++) {
        complexMath();
        
        #ifdef ARDUINO
            if(i % 1000 == 0) {
                yield();  // Allow other processes
                // or delay(1); for longer operations
            }
        #endif
    }
}
```

## Project Structure Templates

### Simple Template
```
MyArduinoProject/
├── MyArduinoProject.ino          # Main Arduino sketch
├── wrapper.h                     # C++ safe wrapper header
├── wrapper.cpp                   # Arduino wrapper implementations
├── mylib.c                       # Original C code
└── mylib.h                       # Original C header
```

### Advanced Template (for larger projects with multiple libraries)
```
MyArduinoProject/
├── MyArduinoProject.ino          # Main Arduino sketch
├── arduino_main.h                # Main Arduino interface header
├── arduino_main.cpp              # Main Arduino interface implementation
├── lib/                          # Original C code libraries (unchanged)
│   ├── module1/                  # First software module
│   │   ├── module1.h
│   │   └── module1.c
│   ├── module2/                  # Second software module
│   │   ├── module2.h  
│   │   └── module2.c
│   └── moduleN/                  # Additional modules as needed
│       ├── moduleN.h
│       └── moduleN.c
├── hardware/                     # Arduino hardware abstraction layer
│   ├── hal_common.h              # Common HAL definitions
│   ├── hal_device1.h             # Device-specific interfaces
│   ├── hal_device1.cpp
│   └── hal_deviceN.cpp           # Additional devices as needed
├── wrappers/                     # Arduino-C integration wrappers
│   ├── module1_wrapper.h         # One wrapper per software module
│   ├── module1_wrapper.cpp
│   ├── module2_wrapper.h
│   ├── module2_wrapper.cpp
│   └── hardware_wrapper.h        # Hardware abstraction wrapper
└── docs/
    └── arduino-c-integration-guide.md
```

## Complete Implementation Examples

### Simple Example Files

**mylib.h (Original C Library Header)**
```c
#ifndef MYLIB_H
#define MYLIB_H

#include <stdint.h>

void my_c_function(int val);
uint16_t calculate_checksum(const uint8_t* data, size_t len);

#endif
```

**mylib.c (Original C Library Source)**
```c
#include "mylib.h"

void my_c_function(int val) {
    // Original C implementation
    // Keep this file unchanged
}

uint16_t calculate_checksum(const uint8_t* data, size_t len) {
    uint16_t sum = 0;
    for(size_t i = 0; i < len; i++) {
        sum += data[i];
    }
    return sum;
}
```

**wrapper.h (C++ Safe Wrapper Header)**
```c
#ifndef WRAPPER_H
#define WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "mylib.h"  // Bring in the C functions

#ifdef __cplusplus
}
#endif

#endif
```

**wrapper.cpp (Arduino Wrapper Implementation)**
```cpp
#include "wrapper.h"
#include <Arduino.h>

// Example: wrap a C function to use Arduino's Serial
void call_my_c_function_and_print(int val) {
    my_c_function(val);
    Serial.print("Called my_c_function with val=");
    Serial.println(val);
}

// Wrapper that handles memory constraints
bool safe_calculate_checksum(const uint8_t* data, size_t len, uint16_t* result) {
    if(len > 256) {  // Safety check for Arduino memory
        Serial.println("Error: Data too large for Arduino");
        return false;
    }
    
    *result = calculate_checksum(data, len);
    return true;
}
```

### Advanced Example Files

**arduino_wrapper.h (Advanced Wrapper)**
```cpp
#ifndef ARDUINO_WRAPPER_H
#define ARDUINO_WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

// Include original C headers
#include "lib/original_code.h"

// Arduino-specific wrapper functions
void arduino_init_c_library(void);
bool arduino_process_data(const char* data, int len);

#ifdef __cplusplus
}
#endif

#endif
```

**arduino_wrapper.cpp (Advanced Implementation)**
```cpp
#include "arduino_wrapper.h"
#include <Arduino.h>

extern "C" {
    // Provide Arduino implementations of missing functions
    void debug_print(const char* msg) {
        Serial.println(msg);
    }
    
    unsigned long get_timestamp(void) {
        return millis();
    }
    
    // Memory allocation wrapper with safety checks
    void* safe_malloc(size_t size) {
        if(size > 512) {  // Limit allocation size
            debug_print("Warning: Large allocation requested");
            return NULL;
        }
        return malloc(size);
    }
}

void arduino_init_c_library(void) {
    Serial.println("Initializing C library...");
    init_c_library();
    printFreeMemory();  // Monitor memory after init
}

bool arduino_process_data(const char* data, int len) {
    // Safety checks for Arduino constraints
    if(len < 1 || len > 64) {
        Serial.println("Error: Invalid data length");
        return false;
    }
    
    if(data == NULL) {
        Serial.println("Error: NULL data pointer");
        return false;
    }
    
    // Call original C function with validated parameters
    process_data(data, len);
    return true;
}
```

### Main Arduino Sketch Examples

**Simple Sketch**
```cpp
#include <Arduino.h>
#include "wrapper.h"

// Forward declaration of C++ wrapper
void call_my_c_function_and_print(int val);

void setup() {
    Serial.begin(9600);
    while (!Serial) {} // Wait for Serial (Leonardo/Micro)
    Serial.println("Arduino + C integration example");
    
    call_my_c_function_and_print(42);
}

void loop() {
    // Direct C function call (also works)
    my_c_function(123);
    
    delay(1000);
}
```

**Advanced Sketch**
```cpp
#include "arduino_wrapper.h"

void setup() {
    Serial.begin(9600);
    while (!Serial) {}
    Serial.println("Advanced Arduino + C integration");
    
    arduino_init_c_library();
}

void loop() {
    char testData[] = "sensor_data";
    
    if(arduino_process_data(testData, sizeof(testData)-1)) {
        Serial.println("Data processed successfully");
    } else {
        Serial.println("Data processing failed");
    }
    
    printFreeMemory();
    delay(2000);
}
```

## Practical Integration Steps

1. **Analyze the C code**: Identify dependencies, memory usage, and OS-specific functions
2. **Create project structure**: Place `.c` and `.h` files in appropriate directories
3. **Create wrapper header**: Add `extern "C"` guards around C includes
4. **Implement Arduino wrappers**: Replace OS functions with Arduino equivalents
5. **Add safety checks**: Validate memory usage and parameter ranges
6. **Test incrementally**: Start with simple functions, add complexity gradually
7. **Monitor resources**: Use memory monitoring to detect issues early

## Testing and Validation

### Memory Testing
```cpp
void testMemoryUsage() {
    Serial.println("=== Memory Test ===");
    printFreeMemory();
    
    // Test your C functions here
    arduino_process_data("test", 4);
    
    printFreeMemory();
    Serial.println("=== Test Complete ===");
}
```

### Integration Testing
```cpp
void runIntegrationTests() {
    Serial.println("Running integration tests...");
    
    // Test 1: Basic functionality
    my_c_function(100);
    Serial.println("✓ Basic function call");
    
    // Test 2: Memory constraints
    uint8_t testData[32];
    uint16_t checksum;
    if(safe_calculate_checksum(testData, sizeof(testData), &checksum)) {
        Serial.println("✓ Checksum calculation");
    }
    
    // Test 3: Error handling
    if(!arduino_process_data(NULL, 0)) {
        Serial.println("✓ Error handling");
    }
    
    Serial.println("All tests completed");
}
```

This integrated approach provides a robust foundation for incorporating existing C code into Arduino projects while maintaining safety, compatibility, and performance.