@echo off
setlocal

if "%1"=="" (
    if "%ARDUINO_PORT%"=="" (
        echo Error: No COM port specified. Either set ARDUINO_PORT environment variable or pass port as argument.
        echo Usage: monitor.bat [COM_PORT]
        echo Example: monitor.bat COM4
        exit /b 1
    )
    set PORT=%ARDUINO_PORT%
) else (
    set PORT=%1
)

echo Starting serial monitor on %PORT% at 9600 baud...
arduino-cli monitor --port %PORT% --config baudrate=9600