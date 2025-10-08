# Responsive Layout Behavior Guide

## Overview

The GUI automatically adapts its layout based on window size and shape to provide optimal usability.

## Layout Modes

### 1. Desktop Mode (Wide Window)
**Triggers:** Window width > serial monitor threshold (320px)

```
┌─────────────────────────────────────────────────────────┐
│  Flight Code Manager                                    │
├───────────────────┬─────────────────────────────────────┤
│                   │                                     │
│  Flight Controls  │    Serial Monitor                   │
│                   │    (> 40 characters wide)           │
│  ┌─────────────┐  │                                     │
│  │ Parameters  │  │    [INFO] System ready              │
│  │ Motor: 20s  │  │    [OK] Parameters set              │
│  │ Flight: 120s│  │    GPS,12345,3,GLIDE,39.2,-77.1    │
│  │             │  │    ...                              │
│  └─────────────┘  │                                     │
│                   │                                     │
│  Flight Data      │                                     │
│  Flight History   │                                     │
│                   │                                     │
└───────────────────┴─────────────────────────────────────┘
```

**Characteristics:**
- Controls on left (1/3 width)
- Serial monitor on right (2/3 width)
- Side-by-side arrangement
- Optimal for desktop/laptop use

---

### 2. Narrow Serial Monitor Mode
**Triggers:** Serial monitor panel width < 320px (40 characters * 8px/char)

```
┌─────────────────────────────────────────────────────────┐
│  Flight Code Manager                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Flight Controls                                        │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Parameters                                       │   │
│  │ Motor Run Time: [20] Set                        │   │
│  │ Flight Time:   [120] Set                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Flight Data | Flight History                          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Serial Monitor (Stacked)                               │
│                                                         │
│  [INFO] System ready                                    │
│  [OK] Parameters set successfully                       │
│  GPS,12345,3,GLIDE,39.24567,-77.19655                  │
│  ...                                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Controls on top
- Serial monitor on bottom (full width)
- Prevents text wrapping in serial monitor
- Maintains readability of GPS coordinates

**Why 40 characters?**
- GPS coordinates: ~35 characters minimum
- Timestamps: ~8 characters
- Message prefixes: [INFO], [OK], etc.
- **Total:** Needs at least 40 chars for proper display

---

### 3. Mobile/Tall Window Mode
**Triggers:** Window aspect ratio > 1.2:1 (height > width * 1.2)

```
┌──────────────────────┐
│  Flight Code Manager │
├──────────────────────┤
│                      │
│  Flight Controls     │
│                      │
│  ┌────────────────┐  │
│  │ Motor: [20] S  │  │
│  │ Flight:[120] S │  │
│  └────────────────┘  │
│                      │
│  [Get] [Reset]       │
│  [Save] [Load]       │
│  (buttons stacked)   │
│                      │
│  Flight History      │
│                      │
├──────────────────────┤
│                      │
│  Serial Monitor      │
│                      │
│  [INFO] Ready        │
│  [OK] Set params     │
│  GPS,12345,3,GLIDE   │
│  39.24567,-77.19655  │
│  ...                 │
│                      │
└──────────────────────┘
```

**Characteristics:**
- Vertical stacking
- Controls on top, monitor below
- Buttons stack vertically
- Optimized for portrait tablets/phones

---

## Automatic Behavior Summary

| Window State | Layout Mode | Serial Monitor | Button Layout |
|-------------|-------------|----------------|---------------|
| Wide desktop | Side-by-side | Right panel | Horizontal |
| Narrow desktop | Stacked | Bottom (full) | Horizontal |
| Tall window | Stacked | Bottom (full) | Vertical |
| Tablet portrait | Stacked | Bottom (full) | Vertical |

## Resize Thresholds (With Hysteresis)

### Serial Monitor Width Thresholds
```python
self.serial_monitor_width_threshold_low = 40 * 8   # 320 pixels (stack threshold)
self.serial_monitor_width_threshold_high = 50 * 8  # 400 pixels (unstack threshold)
```
- **LOW threshold (320px):** Stack when width drops below this
- **HIGH threshold (400px):** Unstack when width exceeds this
- **Dead zone (80px):** Prevents oscillation between modes
- 40 characters minimum for GPS data
- ~8 pixels per character (monospace font)

**Hysteresis prevents layout thrashing:** Once stacked, requires 400px+ to unstack. Once unstacked, requires < 320px to stack.

### Button Stacking Threshold
```python
self.narrow_width_threshold = 500  # pixels
```
- Control panel < 500px → buttons stack vertically
- Ensures buttons remain easily clickable

### Mobile/Tall Threshold
```python
self.mobile_threshold_ratio = 1.2  # height/width
```
- Aspect ratio > 1.2 → mobile layout
- Common on tablets in portrait mode

## Real-World Examples

### Example 1: Laptop (1920x1080)
**Result:** Desktop mode
- Wide screen allows side-by-side
- Serial monitor has plenty of width (> 40 chars)
- All controls horizontal

### Example 2: Narrow Window (800x600)
**Result:** Serial monitor stacks
- Window manually resized narrow
- Serial monitor would be < 40 chars
- Automatically stacks to maintain readability

### Example 3: Tablet Portrait (768x1024)
**Result:** Mobile mode
- Tall aspect ratio (1024/768 = 1.33 > 1.2)
- Everything stacks vertically
- Touch-friendly layout

### Example 4: Laptop Split Screen (960x1080)
**Result:** Hybrid
- Not quite mobile threshold (1080/960 = 1.125)
- But serial monitor narrow
- Stacks serial monitor only

## Developer Notes

### Testing Responsive Behavior

```bash
# Run test script
cd gui
python test_responsive.py
```

**Manual testing:**
1. Start with wide window
2. Drag right edge to narrow window
3. Watch serial monitor stack at 320px
4. Continue narrowing to see button stacking
5. Resize to tall aspect ratio for mobile mode

### Console Debug Output

The GUI prints layout transitions:
```
[FlightSequencer] Serial monitor width: 350px -> side-by-side
[FlightSequencer] Serial monitor width: 290px -> stacking (< 40 chars)
[FlightSequencer] Width layout change: 450px -> narrow
[GUI] Applied DPI scaling: 1.5x (DPI: 144)
```

### Adding Custom Thresholds

To adjust behavior, modify in tab `__init__`:

```python
# Make serial monitor stack earlier/later
self.serial_monitor_width_threshold = 50 * 8  # 50 chars instead of 40

# Make buttons stack at different width
self.narrow_width_threshold = 600  # Stack at 600px instead of 500px
```

## Benefits

### For Users
- ✅ Always readable serial output
- ✅ No horizontal scrolling
- ✅ Adapts to any screen size
- ✅ Works on desktop, laptop, tablet
- ✅ No manual layout adjustments needed

### For Developers
- ✅ Grid-based layout (no widget destruction)
- ✅ Fast resize transitions (< 25ms)
- ✅ Maintains widget state
- ✅ Easy to customize thresholds
- ✅ Debug output for testing

## Troubleshooting

### Serial monitor not stacking when narrow
**Check:** Console output for width detection
**Fix:** Ensure resize event binding present:
```python
self.right_frame.bind('<Configure>', self._on_serial_monitor_resize)
```

### Layout switching too frequently (FIXED)
**Cause:** Window size oscillating near threshold
**Solution Applied:** Hysteresis with dual thresholds
- Stack at < 320px
- Unstack at >= 400px
- 80px dead zone prevents oscillation

If still occurring, increase dead zone:
```python
self.serial_monitor_width_threshold_high = 60 * 8  # 480px (160px dead zone)
```

### Widget state lost during resize
**Cause:** Widget destruction instead of grid reconfiguration
**Solution:** Use `grid_forget()` + `grid()`, never `destroy()`

## Future Enhancements

- [ ] User-configurable thresholds in settings
- [ ] Save/restore layout preferences
- [ ] Per-monitor layout memory
- [ ] Custom breakpoints for different workflows
- [ ] Visual size grip indicator
- [ ] Smooth animated transitions

## Related Documentation

- **GUI_REFACTORING.md** - Technical implementation details
- **QUICK_START.md** - Getting started guide
- **test_responsive.py** - Automated test script
