# Power Consumption Analysis: Multi-Board Flight Control Systems

## Executive Summary

Power consumption is critical for flight applications where battery weight directly impacts flight performance and endurance. This analysis evaluates power requirements across different Xiao/Qt Py form factor boards to optimize battery life while maintaining flight-critical performance.

## Current System Power Requirements

### **Existing SAMD21 System Analysis**
Based on FlightSequencer and GpsAutopilot applications:

#### **Active Components During Flight:**
- **MCU (SAMD21)**: Continuous processing at 48MHz
- **GPS Module**: Continuous UART communication at 9600 baud
- **Servo Systems**: PWM output for roll control (A3) and motor ESC (A2)
- **NeoPixel LED**: Status indication (pin 11)
- **Serial Communication**: 9600 baud USB/UART for telemetry

#### **Estimated Current Draw (SAMD21 Baseline):**
```
Component               | Active Current | Sleep Current | Duty Cycle | Avg Current
------------------------|----------------|---------------|------------|------------
SAMD21 MCU             | 8-15mA @ 48MHz | 74µA (board)  | 100%       | 12mA
GPS Module             | 25-45mA        | N/A           | 100%       | 35mA
NeoPixel (1 LED)       | 20mA @ full    | 0µA           | 10%        | 2mA
Servo Control (2x PWM) | 1mA            | 0µA           | 100%       | 1mA
Serial UART            | 1mA            | 0µA           | 100%       | 1mA
------------------------|----------------|---------------|------------|------------
TOTAL SYSTEM           |                |               |            | ~51mA
```

**Estimated Flight Time:**
- 500mAh LiPo: ~9.8 hours
- 1000mAh LiPo: ~19.6 hours

## Multi-Board Power Comparison Matrix

### **Comprehensive Board Analysis**

| Board | MCU Type | Active Current | Sleep Current | Flash | RAM | Wireless | Est. Flight Time (500mAh) |
|-------|----------|----------------|---------------|-------|-----|----------|---------------------------|
| **Adafruit Qt Py Series** |
| Qt Py SAMD21 | ARM M0+ 48MHz | 12mA | 74µA | 256KB | 32KB | None | 9.8h (baseline) |
| Qt Py RP2040 | ARM M0+ 133MHz | 18-25mA | ~100µA | 2MB | 264KB | None | 8.5h (estimated) |
| Qt Py ESP32-S2 | Xtensa LX7 240MHz | 22-35mA | 22µA | 4MB | 320KB | WiFi | 7.2h (no wireless) |
| Qt Py ESP32-S3 | Xtensa 240MHz | 28-40mA | 10µA | 8MB | 512KB | WiFi/BLE | 6.5h (no wireless) |
| Qt Py ESP32-C3 | RISC-V 160MHz | 20-28mA | 43µA | 4MB | 400KB | WiFi/BLE | 8.0h (no wireless) |
| Qt Py CH32V203 | RISC-V 144MHz | 15-20mA | ~50µA | 256KB | 10KB | None | 9.2h (estimated) |
| **Seeed XIAO Series** |
| XIAO SAMD21 | ARM M0+ 48MHz | 11mA | ~70µA | 256KB | 32KB | None | 10.0h (estimated) |
| XIAO RP2040 | ARM M0+ 133MHz | 17-24mA | ~90µA | 2MB | 264KB | None | 8.8h (estimated) |
| XIAO ESP32C3 | RISC-V 160MHz | 22-30mA | 43µA | 4MB | 400KB | WiFi/BLE | 7.8h (no wireless) |
| XIAO ESP32C6 | RISC-V 160MHz | 25-35mA | ~40µA | 4MB | 512KB | WiFi 6/BLE | 7.0h (no wireless) |
| XIAO ESP32S3 | Xtensa 240MHz | 30-45mA | 14µA | 8MB | 512KB | WiFi/BLE | 6.2h (no wireless) |
| XIAO nRF52840 | ARM M4F 64MHz | 8-12mA | ~5µA | 1MB | 256KB | BLE 5.0 | 11.5h (no wireless) |

### **Power Consumption Breakdown**

#### **MCU-Only Consumption (excluding peripherals):**
```
Low Power Champions:
- nRF52840: 8-12mA active, 5µA sleep -> Best for battery applications
- SAMD21: 11-12mA active, 70µA sleep -> Current baseline performance
- CH32V203: 15-20mA active, 50µA sleep -> Good RISC-V option

High Performance Options:
- RP2040: 17-25mA active, 90µA sleep -> More memory, dual-core
- ESP32C3: 22-30mA active, 43µA sleep -> Wireless capable, efficient
- ESP32S3: 30-45mA active, 14µA sleep -> Highest performance, best sleep

Power Hungry:
- ESP32C6: 25-35mA active, 40µA sleep -> WiFi 6 overhead
```

#### **System-Level Power Analysis (with peripherals):**
```
Total System Current Draw Estimates:
- nRF52840 System: ~44mA (11.4h on 500mAh)
- SAMD21 System: ~51mA (9.8h on 500mAh) <- Current baseline
- CH32V203 System: ~54mA (9.3h on 500mAh)
- RP2040 System: ~58mA (8.6h on 500mAh)
- Qt Py ESP32C3 System: ~59mA (8.5h on 500mAh, wireless disabled)
- XIAO ESP32C3 System: ~61mA (8.2h on 500mAh, wireless disabled)
- Qt Py ESP32S2 System: ~62mA (8.1h on 500mAh, wireless disabled)
- ESP32C6 System: ~66mA (7.6h on 500mAh, wireless disabled)
- Qt Py ESP32S3 System: ~68mA (7.4h on 500mAh, wireless disabled)
- XIAO ESP32S3 System: ~71mA (7.0h on 500mAh, wireless disabled)
```

## Flight Application Specific Considerations

### **Power Profile During Flight Phases**

#### **FlightSequencer Power Profile:**
```
Phase            | Duration | MCU Load | GPS | Servo | LED  | Power Draw
-----------------|----------|----------|-----|-------|------|----------
READY            | Variable | Low      | Off | Off   | Blink| 15mA
ARMED            | 30s      | Medium   | On  | Off   | Flash| 50mA
MOTOR_SPOOL      | 5s       | High     | On  | Active| On   | 65mA
MOTOR_RUN        | 20s      | High     | On  | Active| On   | 65mA
GLIDE            | 90s      | Medium   | On  | Active| Blink| 55mA
DT_DEPLOY        | 5s       | High     | On  | Active| On   | 65mA
LANDING          | Variable | Low      | On  | Off   | Blink| 45mA
```

#### **GpsAutopilot Power Profile:**
```
Phase            | Duration | MCU Load | GPS | Servo | LED  | Power Draw
-----------------|----------|----------|-----|-------|------|----------
GPS_ACQUIRING    | 60-300s  | Medium   | On  | Off   | Heart| 50mA
READY            | Variable | Medium   | On  | Off   | Heart| 50mA
ARMED            | Variable | High     | On  | Off   | Flash| 52mA
MOTOR_SPOOL      | 10s      | High     | On  | Active| On   | 67mA
GPS_GUIDED_FLIGHT| Variable | High     | On  | Active| On   | 67mA
EMERGENCY        | Variable | High     | On  | Active| Flash| 70mA
```

### **Critical Power Optimization Opportunities**

#### **1. Sleep Mode Optimization**
```cpp
// Power savings during idle periods
void enterLowPowerMode() {
#ifdef BOARD_SUPPORTS_DEEP_SLEEP
  // Put MCU in deep sleep between GPS updates
  delay_with_sleep(GPS_RECORD_INTERVAL);  // 1000ms between GPS reads
#endif
}

// Potential savings: 5-15mA during GPS intervals
// Flight time improvement: +10-20%
```

#### **2. GPS Power Management**
```cpp
// GPS module control for non-critical phases
void manageGPSPower(FlightPhase phase) {
  switch(phase) {
    case READY:
      // GPS can be disabled until ARM
      gps_power_save_mode();  // Save ~20mA
      break;
    case MOTOR_RUN:
      // Full GPS tracking during motor phase
      gps_full_power_mode();
      break;
  }
}
```

#### **3. LED Power Optimization**
```cpp
// Smart LED brightness management
void optimizeLEDPower() {
#if HAS_NEOPIXEL
  // Reduce brightness during flight (visibility less critical)
  pixel.setBrightness(64);  // 25% brightness saves ~15mA
#endif
}
```

## Board Selection Recommendations

### **Power-Optimized Board Rankings**

#### **1. Ultra-Long Flight Applications (>12 hours)**
```
Rank | Board        | Est. Flight Time | Pros                      | Cons
-----|--------------|------------------|---------------------------|------------------
1    | nRF52840     | 11.4h           | Lowest power, BLE option  | Limited processing
2    | SAMD21       | 9.8h            | Proven platform           | Limited memory
3    | CH32V203     | 9.3h            | RISC-V, cost effective    | Least memory (10KB)
```

#### **2. Balanced Performance/Power (8-10 hours)**
```
Rank | Board        | Est. Flight Time | Pros                      | Cons
-----|--------------|------------------|---------------------------|------------------
1    | RP2040       | 8.6h            | Dual-core, lots of memory| Higher power
2    | Qt Py ESP32C3| 8.5h            | WiFi/BLE, Qt Py form     | Wireless complexity
3    | XIAO ESP32C3 | 8.2h            | WiFi/BLE capability       | Wireless complexity
4    | Qt Py ESP32S2| 8.1h            | WiFi, Qt Py form         | No Bluetooth
```

#### **3. High-Performance Applications (6-8 hours)**
```
Rank | Board        | Est. Flight Time | Pros                      | Cons
-----|--------------|------------------|---------------------------|------------------
1    | ESP32C6      | 7.6h            | WiFi 6, Matter support    | High power draw
2    | Qt Py ESP32S3| 7.4h            | AI acceleration, Qt Py    | High power draw
3    | XIAO ESP32S3 | 7.0h            | AI acceleration, camera   | Highest power
```

### **Power Optimization Strategies by Board Type**

#### **SAMD21/nRF52840 (Low Power Champions)**
- **Strategy**: Maximize sleep efficiency
- **Optimizations**:
  - Deep sleep between GPS updates
  - GPS power management
  - LED brightness reduction
- **Achievable Improvement**: +15-25% flight time

#### **RP2040 (Balanced Option)**
- **Strategy**: Utilize dual-core efficiency
- **Optimizations**:
  - Core 0: Flight control loop
  - Core 1: GPS processing, data logging
  - Sleep unused core during low activity
- **Achievable Improvement**: +10-20% flight time

#### **ESP32 Series (High Performance)**
- **Strategy**: Wireless-first with smart power management
- **Optimizations**:
  - Disable WiFi during flight (ground telemetry only)
  - CPU frequency scaling based on flight phase
  - Smart peripheral power control
- **Achievable Improvement**: +20-30% flight time

## Battery Recommendations by Board Type

### **Battery Selection Matrix**

| Board Type | Recommended Battery | Flight Time | Weight | Cost | Use Case |
|------------|--------------------|-----------.|--------|------|----------|
| **nRF52840** | 350mAh 1S LiPo | 8.0h | 12g | $8 | Ultra-light, long endurance |
| **SAMD21** | 500mAh 1S LiPo | 9.8h | 18g | $10 | Current standard |
| **RP2040** | 750mAh 1S LiPo | 12.9h | 28g | $15 | Extended flight, data logging |
| **Qt Py ESP32C3** | 1000mAh 1S LiPo | 13.5h | 35g | $18 | Qt Py form, telemetry-enabled |
| **XIAO ESP32C3** | 1000mAh 1S LiPo | 13.1h | 35g | $18 | Telemetry-enabled flights |
| **Qt Py ESP32S2** | 1200mAh 1S LiPo | 14.5h | 42g | $20 | Qt Py form, WiFi telemetry |
| **Qt Py ESP32S3** | 1500mAh 1S LiPo | 16.2h | 50g | $25 | Qt Py form, AI acceleration |
| **XIAO ESP32S3** | 1500mAh 1S LiPo | 15.0h | 50g | $25 | High-performance applications |

### **Weight vs Performance Trade-offs**

```
Power Efficiency Ranking (mAh per hour of flight):
1. nRF52840: 43.9 mAh/hour (most efficient)
2. SAMD21: 51.0 mAh/hour (current baseline)
3. CH32V203: 53.8 mAh/hour
4. RP2040: 58.1 mAh/hour
5. Qt Py ESP32C3: 58.8 mAh/hour
6. XIAO ESP32C3: 61.0 mAh/hour
7. Qt Py ESP32S2: 61.7 mAh/hour
8. ESP32C6: 65.8 mAh/hour
9. Qt Py ESP32S3: 67.6 mAh/hour
10. XIAO ESP32S3: 71.4 mAh/hour (least efficient)
```

## Implementation Recommendations

### **Phase 1: Power-Aware Board Support**
1. **Add power monitoring** to existing SAMD21 code
2. **Implement sleep modes** for idle periods
3. **Add battery voltage monitoring** for all boards
4. **Create power optimization flags** for compilation

### **Phase 2: Board-Specific Power Optimization**
1. **nRF52840**: Focus on ultra-low-power sleep modes
2. **RP2040**: Implement dual-core power management
3. **ESP32**: Add wireless-aware power profiles

### **Phase 3: Advanced Power Management**
1. **Adaptive power scaling** based on flight phase
2. **Smart peripheral management** (GPS, LED, sensors)
3. **Battery life prediction** and low-power warnings
4. **Flight time optimization** algorithms

## Critical Information Still Needed

### **Immediate Testing Requirements:**
1. **Real-world power measurements** for each board with actual flight hardware
2. **Battery life validation** under actual flight conditions
3. **Power consumption during servo load** (varying with control authority)
4. **Temperature effects** on power consumption and battery performance
5. **Wireless power consumption** patterns for ESP32 boards

### **Long-term Optimization Opportunities:**
1. **Custom power management firmware** for each board type
2. **Dynamic frequency scaling** based on flight requirements
3. **Predictive power management** using flight profile data
4. **Solar charging integration** for extended flight applications

This analysis provides the foundation for power-conscious multi-board support while maintaining flight-critical performance requirements.