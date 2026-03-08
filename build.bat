@echo off
echo [TXTDrop] Generating icon...
python create_icon.py
if errorlevel 1 (
    echo Failed to generate icon.
    pause
    exit /b 1
)

echo [TXTDrop] Building executable...
pyinstaller --noconsole --onefile --icon icon.ico --name TXTDrop main.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete: dist\TXTDrop.exe
pause
