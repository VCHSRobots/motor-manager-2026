@echo off
echo ========================================
echo   EPIC Motor Test App Builder
echo   (Folder-based for hardware drivers)
echo ========================================
echo.

REM Clean up previous builds
echo Cleaning up old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "EPIC Motor Test.spec" del "EPIC Motor Test.spec"
echo.

REM Build the executable (folder-based, better for hardware drivers)
echo Building executable with PyInstaller...
echo This may take a few minutes...
echo.

pyinstaller --windowed --name "EPIC Motor Test" --icon=motor_icon.ico --hidden-import=phoenix6 --collect-all phoenix6 motor_test_app.py

echo.
echo ========================================
if exist "dist\EPIC Motor Test\EPIC Motor Test.exe" (
    echo   BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created at:
    echo   dist\EPIC Motor Test\EPIC Motor Test.exe
    echo.
    echo NOTE: This creates a FOLDER with the .exe and all dependencies.
    echo You must keep all files in the folder together.
    echo.
    echo To distribute:
    echo   1. Zip the entire "dist\EPIC Motor Test" folder
    echo   2. On target PC, unzip and run EPIC Motor Test.exe
    echo.
    echo To create desktop shortcut:
    echo   Right-click "EPIC Motor Test.exe" and Send to Desktop
    echo.
) else (
    echo   BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo.
)

pause
