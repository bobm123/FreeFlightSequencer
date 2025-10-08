# Application Detection Fix - Detecting State Not Updating

## Issue

On connect/disconnect/reconnect, the "Detected App:" display would show "Detecting..." even though the Arduino application had already sent an [APP] message that was visible in the Serial Monitor.

**User feedback:**
> "On connect/disconnect/reconnect, the Detected App: display shows detecting even though the arduino app has reported an [APP] message."

## Root Cause

Two issues prevented proper detection updates on reconnect:

### 1. Detection Throttling
The TabManager had a 2-second throttle to prevent rapid re-detection:

```python
def _detect_application(self, message: str) -> ApplicationType:
    """Detect application type from serial message patterns."""
    # Avoid rapid re-detection
    current_time = time.time()
    if current_time - self.last_detection_time < 2.0:
        return ApplicationType.UNKNOWN  # Ignore detection attempts
```

**Problem:** After disconnect/reconnect, if the Arduino sent [APP] message within 2 seconds of the last detection, it would be ignored.

### 2. Stale Detection State
The TabManager maintained `self.active_app` state, and only called the detection callback when the detected app changed:

```python
detected_app = self._detect_application(message)
if detected_app != ApplicationType.UNKNOWN:
    if detected_app != self.active_app:  # Only notify if changed
        self.active_app = detected_app
        if self.detection_callback:
            self.detection_callback(detected_app)
```

**Problem:** On reconnect, `self.active_app` was still set to the previous app (e.g., FlightSequencer), so even if detection succeeded, the callback wasn't called because `detected_app == self.active_app`. Meanwhile, the GUI showed "Detecting..." because it set that on connection.

## Solution

Added `reset_detection()` method to TabManager and call it on both connect and disconnect to ensure clean detection state.

## Implementation

### TabManager Reset Method

**File:** `gui/src/core/tab_manager.py`

```python
def reset_detection(self):
    """Reset detection state (call on connect/disconnect)."""
    self.active_app = ApplicationType.UNKNOWN
    self.last_detection_time = 0
```

This resets:
- `active_app` to UNKNOWN - ensures callback will be called on next detection
- `last_detection_time` to 0 - clears throttle timer, allows immediate detection

### Connection Handler Updates

**File:** `gui/src/gui/multi_tab_gui.py`

```python
def _on_connection_changed(self, connected, port):
    """Handle connection state changes."""
    self.connected = connected

    if connected:
        self.connection_status_var.set(f"Connected to {port}")
        self.detected_app_var.set("Detecting...")

        # Reset tab manager detection state to allow fresh detection
        self.tab_manager.reset_detection()

        # Send identification query after connection
        self.root.after(2000, self.tab_manager.send_identification_query)
    else:
        self.connection_status_var.set("Disconnected")
        self.detected_app_var.set("None")
        self.current_app = ApplicationType.UNKNOWN
        self.message_count = 0
        self.message_count_var.set("Messages: 0")

        # Reset tab manager detection state
        self.tab_manager.reset_detection()
```

**Key changes:**
- Call `reset_detection()` on **connect** (before Arduino messages arrive)
- Call `reset_detection()` on **disconnect** (clean state for next connection)

## Detection Flow

### Before Fix (Broken)

```
1. Connect → Set "Detecting..."
2. TabManager.active_app = FlightSequencer (from previous session)
3. Arduino sends "[APP] FlightSequencer"
4. TabManager detects FlightSequencer
5. Compares: detected (FlightSequencer) == active_app (FlightSequencer)
6. No callback called (no change detected)
7. GUI still shows "Detecting..." ✗
```

### After Fix (Working)

```
1. Connect → Set "Detecting..."
2. Call reset_detection() → active_app = UNKNOWN, last_detection_time = 0
3. Arduino sends "[APP] FlightSequencer"
4. TabManager detects FlightSequencer (throttle cleared, allows immediate detection)
5. Compares: detected (FlightSequencer) != active_app (UNKNOWN)
6. Callback called → GUI updates to "FlightSequencer" ✓
7. GUI shows "Detected App: FlightSequencer" ✓
```

## Benefits

### Reliable Detection on Reconnect
- ✅ Detection state reset on every connect
- ✅ Throttle timer cleared on every connect
- ✅ Arduino [APP] messages always detected after reconnect

### Clean State Management
- ✅ Disconnect clears detection state
- ✅ No stale state carried over to next connection
- ✅ Each connection starts fresh

### Immediate Detection
- ✅ Throttle timer cleared allows immediate detection
- ✅ No 2-second delay from previous detection
- ✅ First [APP] message after connect is always detected

### Correct UI Updates
- ✅ "Detecting..." always replaced by actual app name
- ✅ Detection callback always called on reconnect
- ✅ UI state matches actual detection state

## Detection Timing

### Throttle Purpose
The 2-second throttle prevents detection from firing multiple times as the Arduino sends multiple [APP] messages during startup:

```
[APP] FlightSequencer
[BOARD] Adafruit Qt Py SAMD21
[INFO] Current Parameters
...
[APP] FlightSequencer  ← Would trigger re-detection without throttle
```

The throttle is appropriate for steady-state operation, but needs to be cleared on reconnect.

### Reset Timing
```
Connect event
  ↓
Reset detection (active_app = UNKNOWN, timer = 0)
  ↓
Wait ~100-500ms for Arduino to boot and send messages
  ↓
Arduino sends [APP] message
  ↓
Detection succeeds (throttle clear, active_app was UNKNOWN)
  ↓
Callback updates GUI to show detected app
```

## Edge Cases Handled

### Rapid Disconnect/Reconnect
- Each connect resets state
- Even if reconnecting within 2 seconds, timer is cleared
- Detection works immediately

### Arduino Sends Multiple [APP] Messages
- First [APP] triggers detection and sets timer
- Subsequent [APP] messages within 2 seconds are ignored (by design)
- This is correct behavior (prevents duplicate detection callbacks)

### Reconnect to Same Arduino App
- Even though app type is same, state is reset
- `active_app = UNKNOWN` ensures callback fires
- GUI updates from "Detecting..." to app name

### Reconnect to Different Arduino App
- State reset ensures fresh detection
- Detection of different app works normally
- Tab switches to newly detected app

## Testing

```bash
cd gui
python gui_main.py
```

**Test cases:**
1. **Initial connect:** Shows "Detecting..." then updates to "FlightSequencer" ✓
2. **Disconnect:** Shows "None" ✓
3. **Reconnect:** Shows "Detecting..." then updates to "FlightSequencer" ✓
4. **Rapid reconnect:** Detection works even if <2 seconds ✓
5. **Multiple [APP] messages:** First one detected, others ignored ✓

## Related Code

### Detection Patterns
The detection patterns in TabManager remain unchanged:

```python
self.detection_patterns = {
    ApplicationType.FLIGHT_SEQUENCER: [
        r'\[APP\] FlightSequencer',
        r'FlightSequencer.*starting',
        r'Motor Run Time.*seconds'
    ],
    ApplicationType.GPS_AUTOPILOT: [
        r'\[APP\] GpsAutopilot',
        r'GPS Autopilot.*starting',
        r'Launch datum.*GPS'
    ],
}
```

The fix ensures these patterns are checked with clean state on each connection.

## Files Modified

```
gui/src/gui/multi_tab_gui.py      (call reset_detection on connect/disconnect)
gui/src/core/tab_manager.py       (add reset_detection method)
gui/docs/APP_DETECTION_FIX.md     (this file)
```

## Conclusion

Application detection now works reliably on connect/disconnect/reconnect by resetting the detection state (active app and throttle timer) on every connection event. This ensures the detection callback fires when Arduino sends [APP] messages, updating the GUI from "Detecting..." to the actual application name.

**Before:** "Detected App: Detecting..." stuck even after [APP] message received
**After:** "Detected App: FlightSequencer" updates immediately after [APP] message ✓
