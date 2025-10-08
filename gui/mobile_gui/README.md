# FreeFlightSequencer Mobile GUI (Kivy)

Touch-optimized mobile interface for FreeFlightSequencer and GPS Autopilot flight control systems.

## Features

- **Touch-native interface** - Designed for tablets and smartphones
- **Cross-platform** - Works on Android, iOS, Windows, macOS, Linux
- **Responsive layout** - Adapts to screen orientation and size
- **Real-time monitoring** - Live serial communication with Arduino
- **Flight parameter control** - Touch-friendly input controls
- **GPS navigation display** - Visual status indicators

## Platform Support

### Desktop Development (Windows/Linux/macOS)
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Android Build
```bash
# Install buildozer (Linux/macOS or WSL on Windows)
pip install buildozer

# Build APK
buildozer android debug

# Deploy to connected device
buildozer android debug deploy run
```

### iOS Build
```bash
# macOS only
# Install kivy-ios
pip install kivy-ios

# Create Xcode project
toolchain create FreeFlightSequencer .

# Build for iOS
toolchain build kivy

# Create Xcode project
toolchain create FreeFlightSequencer main.py
```

## Architecture

### Core Components

**main.py** - Application entry point and tab management
**src/serial_comm.py** - Threaded serial communication manager
**src/tabs/flight_sequencer.py** - FlightSequencer control interface
**src/tabs/gps_autopilot.py** - GPS Autopilot monitoring interface

### Key Design Patterns

1. **Data Binding** - Kivy properties for automatic UI updates
2. **Responsive Layout** - GridLayout and BoxLayout with dp() units
3. **Async Communication** - Threaded serial I/O with callbacks
4. **Single Parameter Store** - Consistent with desktop GUI architecture

## Development Tips

### Testing on Desktop
The mobile GUI runs on desktop for development with simulated tablet window size (800x1280).

### Touch vs Mouse
- Mouse clicks simulate touch events
- Multi-touch gestures require actual touch screen

### DPI Scaling
All measurements use `dp()` (density-independent pixels) for consistent sizing across devices.

### Serial Port Access

**Android**: Requires USB OTG adapter and USB host API
**iOS**: Requires MFi-certified serial adapter or Bluetooth
**Desktop**: Standard pyserial access

## Comparison with Tkinter GUI

| Feature | Tkinter GUI | Kivy Mobile GUI |
|---------|-------------|-----------------|
| Platform | Desktop | Desktop + Mobile |
| Touch Support | Limited | Native |
| Orientation | Manual | Automatic |
| DPI Scaling | Manual | Built-in |
| Packaging | Simple | buildozer/Xcode |
| Performance | Good | Excellent (GPU) |

## Future Enhancements

- [ ] Bluetooth serial support for wireless connection
- [ ] Flight path visualization with matplotlib
- [ ] Data export to cloud storage
- [ ] Real-time GPS map overlay
- [ ] Voice commands for hands-free operation
- [ ] Offline parameter profiles
- [ ] Multi-aircraft support

## Hardware Requirements

### Minimum
- Android 5.0+ or iOS 12+
- 7" screen (tablet recommended)
- 1GB RAM
- USB OTG support (Android) or MFi adapter (iOS)

### Recommended
- Android 10+ or iOS 14+
- 10" tablet
- 2GB+ RAM
- GPS module (for location logging)

## Troubleshooting

### Android USB Serial Not Working
- Enable USB debugging in Developer Options
- Install appropriate USB serial driver
- Check USB OTG adapter compatibility

### iOS Serial Connection Issues
- Ensure MFi-certified adapter
- Check app permissions in Settings
- Some adapters require specific apps

### Build Errors
- Update buildozer: `pip install --upgrade buildozer`
- Clean build directory: `buildozer android clean`
- Check Android SDK/NDK versions in buildozer.spec

## License

Same as parent FreeFlightSequencer project.
