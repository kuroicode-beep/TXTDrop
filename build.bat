@echo off
setlocal enabledelayedexpansion
title TXTDrop Build

echo.
echo  =============================
echo   TXTDrop  ^|  Build Pipeline
echo  =============================
echo.

:: -------------------------------------------------------
:: Step 1 — Generate icon.ico
:: -------------------------------------------------------
echo [1/3] Generating icon...
python create_icon.py
if errorlevel 1 (
    echo.
    echo  ERROR: Icon generation failed.
    echo  Make sure Pillow is installed: pip install Pillow
    goto :fail
)

:: -------------------------------------------------------
:: Step 2 — Build TXTDrop.exe with PyInstaller
:: -------------------------------------------------------
echo.
echo [2/3] Building executable with PyInstaller...
pyinstaller --noconsole --onefile --icon icon.ico --name TXTDrop main.py --clean --hidden-import winsound
if errorlevel 1 (
    echo.
    echo  ERROR: PyInstaller build failed.
    echo  Make sure PyInstaller is installed: pip install pyinstaller
    goto :fail
)

:: -------------------------------------------------------
:: Step 3 — Compile installer with Inno Setup
:: -------------------------------------------------------
echo.
echo [3/3] Compiling installer with Inno Setup...

:: Search common Inno Setup install paths
set "ISCC="
for %%P in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    "C:\Program Files\Inno Setup 5\ISCC.exe"
) do (
    if exist %%P set "ISCC=%%~P"
)

if not defined ISCC (
    echo.
    echo  WARNING: Inno Setup not found. Skipping installer build.
    echo  Download: https://jrsoftware.org/isinfo.php
    echo.
    echo  Executable only: dist\TXTDrop.exe
    goto :exeonly
)

"%ISCC%" installer.iss
if errorlevel 1 (
    echo.
    echo  ERROR: Inno Setup compilation failed.
    goto :fail
)

:: -------------------------------------------------------
:: Done
:: -------------------------------------------------------
echo.
echo  =============================
echo   BUILD COMPLETE
echo  =============================
echo   Installer : Output\TXTDropSetup.exe
echo   Executable: dist\TXTDrop.exe
echo  =============================
echo.
pause
exit /b 0

:exeonly
echo  =============================
echo   BUILD COMPLETE (exe only)
echo  =============================
echo   Executable: dist\TXTDrop.exe
echo  =============================
echo.
pause
exit /b 0

:fail
echo.
echo  Build stopped.
pause
exit /b 1
