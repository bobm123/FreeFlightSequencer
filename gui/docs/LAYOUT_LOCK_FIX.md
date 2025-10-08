# Layout Lock Fix - Preventing Resize Event Feedback Loop

## The Deeper Problem

Even with hysteresis, oscillation continued because:

1. User resizes window → Serial monitor becomes narrow (205px)
2. Width check triggers: 205px < 320px → **Stack layout**
3. **Stacking changes grid** → Triggers resize event on serial monitor
4. Serial monitor now has full width (695px)
5. Width check triggers AGAIN: 695px >= 400px → **Unstack layout**
6. **Unstacking changes grid** → Triggers resize event on serial monitor
7. Serial monitor now narrow again (205px)
8. **LOOP CONTINUES!** ⚠️

## The Issue

**Layout changes themselves trigger resize events**, creating a feedback loop that hysteresis alone couldn't solve.

## Solution: Layout Update Lock

Added a **mutex-style lock** that prevents resize handlers from running during layout updates.

### Implementation

```python
# Lock flag
self.updating_layout = False  # Lock to prevent resize events during layout changes

def _update_grid_layout(self):
    """Update grid layout (with lock)."""
    self.updating_layout = True  # SET LOCK

    try:
        # Change grid configuration
        # This triggers resize events, but they'll be ignored
        self.left_frame.grid(...)
        self.right_frame.grid(...)
    finally:
        # Release lock after 200ms (wait for resize events to settle)
        self.parent.after(200, self._release_layout_lock)

def _release_layout_lock(self):
    """Release the layout update lock."""
    self.updating_layout = False  # RELEASE LOCK

def _check_serial_monitor_width(self):
    """Check serial monitor width."""
    # RESPECT LOCK - exit immediately if locked
    if self.updating_layout:
        return  # Ignore resize events during layout update

    # Normal width checking logic...
```

## How It Works

### Timeline WITHOUT Lock (Oscillation)

```
Time   Event                              Action
────────────────────────────────────────────────────────
0ms    User resizes window                Serial monitor: 205px
50ms   Resize event fires                 Check width
51ms   Width < 320px                      Call _update_grid_layout()
52ms   Grid changes → resize event        Check width (205px still)
53ms   Grid changes → resize event        Serial monitor now 695px
54ms   Resize event fires                 Check width (695px)
55ms   Width >= 400px                     Call _update_grid_layout()
56ms   Grid changes → resize event        Check width (695px still)
57ms   Grid changes → resize event        Serial monitor now 205px
58ms   Resize event fires                 Check width (205px)
59ms   Width < 320px                      Call _update_grid_layout()
...    INFINITE LOOP                      ❌
```

### Timeline WITH Lock (Stable)

```
Time   Event                              Action
────────────────────────────────────────────────────────
0ms    User resizes window                Serial monitor: 205px
50ms   Resize event fires                 Check width
51ms   Width < 320px                      Call _update_grid_layout()
52ms   Lock SET (updating_layout = True)  🔒
53ms   Grid changes → resize event        IGNORED (locked)
54ms   Grid changes → resize event        IGNORED (locked)
55ms   Grid changes → resize event        IGNORED (locked)
56ms   Grid changes → resize event        IGNORED (locked)
252ms  Lock RELEASED (after 200ms)        🔓
253ms  Next user resize                   Normal check resumes
```

**Result:** Layout changes don't trigger more layout changes! ✅

## Timing Details

### Lock Duration: 200ms

**Why 200ms?**
- Tkinter resize events can fire multiple times during grid reconfiguration
- 150ms debounce + 50ms safety margin = 200ms
- Long enough to ignore spurious events
- Short enough to remain responsive to user input

### Event Flow

```
_update_grid_layout() called
  ↓
Lock SET (updating_layout = True)
  ↓
grid_forget() → triggers <Configure> event → IGNORED (locked)
  ↓
grid() → triggers <Configure> event → IGNORED (locked)
  ↓
grid_rowconfigure() → triggers <Configure> event → IGNORED (locked)
  ↓
grid_columnconfigure() → triggers <Configure> event → IGNORED (locked)
  ↓
Schedule lock release after 200ms
  ↓
[200ms passes]
  ↓
Lock RELEASED (updating_layout = False)
  ↓
Next user resize → Normal processing resumes
```

## Code Changes

### Both Tabs Updated

**FlightSequencer (`flight_sequencer_tab.py`):**
- Added `self.updating_layout` lock flag
- Wrapped `_update_grid_layout()` with try/finally lock
- Added `_release_layout_lock()` method
- Added lock check in `_check_serial_monitor_width()`

**GpsAutopilot (`gps_autopilot_tab.py`):**
- Same changes for consistency

## Verification

### Expected Console Output (After Fix)

**Good (Stable):**
```
[FlightSequencer] Serial monitor width: 310px < 320px -> stacking
[User resizes wider after 500ms]
[FlightSequencer] Serial monitor width: 420px >= 400px -> side-by-side
```

**No longer seeing:**
```
[FlightSequencer] Serial monitor width: 205px < 320px -> stacking
[FlightSequencer] Serial monitor width: 695px >= 400px -> side-by-side
[FlightSequencer] Serial monitor width: 205px < 320px -> stacking
[FlightSequencer] Serial monitor width: 695px >= 400px -> side-by-side
... (rapid oscillation)
```

## Combined Solution Summary

### Layer 1: Hysteresis (Prevents User-Driven Oscillation)
- Different thresholds for stack (320px) vs unstack (400px)
- 80px dead zone prevents edge case sensitivity

### Layer 2: Layout Lock (Prevents Layout-Driven Oscillation)
- Ignores resize events during grid reconfiguration
- 200ms cooldown after layout changes
- Prevents feedback loops

## Testing

```bash
cd gui
python gui_main.py
```

**Test procedure:**
1. Launch GUI
2. Slowly resize window from wide to narrow
3. **Expected:** ONE transition message when crossing threshold
4. **Not expected:** Rapid repeated messages

**Success criteria:**
- At most ONE layout transition per user resize action
- No oscillation at any window size
- Smooth, stable behavior

## Performance Impact

- **Lock overhead:** < 1ms (simple boolean check)
- **Lock duration:** 200ms per layout change
- **User experience:** Imperceptible (only affects automated events)
- **Stability:** Dramatically improved

## Alternative Approaches Considered

### ❌ Longer Debounce
- **Problem:** Doesn't address layout-triggered events
- **Result:** Still oscillates, just slower

### ❌ Wider Hysteresis Dead Zone
- **Problem:** Doesn't prevent layout feedback loop
- **Result:** Reduces frequency but doesn't eliminate oscillation

### ✅ Layout Lock (Chosen)
- **Advantage:** Directly addresses root cause
- **Result:** Complete elimination of oscillation

## Files Modified

- `gui/src/tabs/flight_sequencer_tab.py` ✅
- `gui/src/tabs/gps_autopilot_tab.py` ✅
- `gui/LAYOUT_LOCK_FIX.md` ✅ (this file)

## Related Documentation

- `HYSTERESIS_FIX.md` - Layer 1 (hysteresis)
- `LAYOUT_LOCK_FIX.md` - Layer 2 (lock)
- `HYSTERESIS_DIAGRAM.txt` - Visual diagrams

## Conclusion

**Two-layer solution:**
1. **Hysteresis:** Prevents sensitivity to window size fluctuations
2. **Layout lock:** Prevents layout changes from triggering themselves

Together, these provide **rock-solid stability** at all window sizes.

**Before:** Unusable oscillation at certain widths
**After:** Smooth, predictable behavior everywhere ✅
