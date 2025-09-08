# Button Test Specification

## Test Description
Validates button HAL functionality including debounced press detection, long press detection, and interrupt-driven state changes reported through the main loop.

## Hardware Requirements
- Push button connected via signal distribution board
- Button configured as active-low with internal pullup
- Arduino serial monitor at 9600 baud

## Test Implementation Requirements

### Interrupt-Driven Detection
- Use external interrupt to detect button state changes
- Implement debouncing in interrupt service routine (50ms default)
- Detect both press and release events
- Identify long presses (>5 seconds duration)

### Main Loop Reporting
- Main loop polls for button state changes
- Serial output reports all button events with timestamps
- State changes detected in interrupts, reported from main loop
- Clear indication of press type (short press vs long press)

## Test Procedure

### Manual Test Steps
1. Start button test via serial interface
2. Perform short button press (< 1 second)
3. Wait 2 seconds
4. Perform long button press (6-7 seconds)
5. Wait 2 seconds
6. Perform rapid multiple presses (test debouncing)
7. Wait 5 seconds for test completion

### Expected Serial Output
See `ExpectedResults.txt` in this directory for typical output format and content. 

The test provides factual output including:
- Button press/release timing with timestamps
- Press duration calculations and categorization (SHORT/LONG)
- Detection of rapid button sequences
- Final summary statistics

User should compare actual serial monitor output with ExpectedResults.txt to validate proper operation.

## Validation Criteria

### User Validation Process
1. Run ButtonTest.ino and perform the manual test steps
2. Compare serial monitor output with ExpectedResults.txt
3. Verify all button events were detected and properly categorized
4. Check that timing calculations and formatting match expected patterns

### Good Output Indicators
- All button presses correctly detected and reported
- Press duration accurately calculated and categorized:
  - SHORT: < 5000ms
  - LONG: >= 5000ms
- No spurious button events during debounce periods
- Interrupt-driven detection with main loop reporting functional
- Timestamp accuracy within reasonable tolerance

### Problem Indicators
- Missing button press or release events
- Incorrect duration calculations or categorization
- Spurious events indicating debouncing failure
- Interrupt system not functioning properly
- Serial output formatting errors or missing data

## Implementation Notes

### Interrupt Service Routine
- Keep ISR minimal - set flags only
- Implement debounce timer in ISR
- Record press/release timestamps
- Set state change flags for main loop processing

### Main Loop Processing
- Check for button state change flags
- Calculate press durations
- Format and send serial output
- Clear state change flags
- Handle test timing and completion

### Memory Considerations
- Minimize ISR execution time
- Use volatile variables for ISR/main loop communication
- Efficient timestamp storage and calculation