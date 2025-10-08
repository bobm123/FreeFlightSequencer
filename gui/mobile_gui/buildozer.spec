[app]
# Application title
title = FreeFlightSequencer

# Package name
package.name = freeflightsequencer

# Package domain (for Android)
package.domain = org.freeflight

# Source code directory
source.dir = .

# Application entry point
source.main = main.py

# Application version
version = 2.0

# Application requirements
requirements = python3,kivy,pyserial

# Android permissions
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,USB_ACCESSORY,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Android features
android.api = 31
android.minapi = 21
android.ndk = 25b

# iOS settings
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

# Orientation (supports rotation)
orientation = all

# Enable fullscreen
fullscreen = 0

[buildozer]
# Log level (0 = error, 1 = info, 2 = debug)
log_level = 2

# Build directory
build_dir = ./.buildozer

# Binary directory
bin_dir = ./bin
