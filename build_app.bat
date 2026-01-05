@echo off
echo ========================================
echo   EPIC Motor Test App Builder
echo ========================================
echo.

REM Clean up previous builds
echo Cleaning up old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "EPIC Motor Test.spec" del "EPIC Motor Test.spec"
echo.

REM Build the executable
echo Building executable with PyInstaller...
echo This may take a few minutes...
echo.

pyinstaller --onefile --windowed --name "EPIC Motor Test" --icon=motor_icon.ico --hidden-import=phoenix6 --collect-all phoenix6 --collect-all phoenix6.hardware motor_test_app.py

echo.
echo ========================================
if exist "dist\EPIC Motor Test.exe" (
    echo   BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created at:
    echo   dist\EPIC Motor Test.exe
    echo.
    echo You can now:
    echo   1. Run the app from: dist\EPIC Motor Test.exe
    echo   2. Create a desktop shortcut to that file
    echo   3. Copy the .exe to any Windows computer
    echo.
) else (
    echo   BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo Make sure you have:
    echo   - PyInstaller installed: pip install pyinstaller
    echo   - motor_icon.ico file in this directory
    echo   - motor_test_app.py file in this directory
    echo.
)

pause
