# TXTDrop

A minimal Windows clipboard saving utility.  
Runs in the system tray. Press a hotkey. Clipboard is saved.

---

## Usage

| Clipboard | Hotkey | Result |
|-----------|--------|--------|
| Text | `CTRL + SHIFT + Z` | `txtdrop_YYYYMMDD_HHMMSS.txt` |
| Image | `CTRL + SHIFT + Z` | `txtdrop_YYYYMMDD_HHMMSS.png` |
| Empty | `CTRL + SHIFT + Z` | Nothing happens |

Right-click the tray icon to **Change Folder** or **Exit**.

---

## Setup

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Run directly

```
python main.py
```

On first launch a folder selection dialog appears.  
The chosen path is saved to `config.json` next to the executable.

---

## Build Executable

Requires [PyInstaller](https://pyinstaller.org/):

```
pip install pyinstaller
```

Then run the build script:

```
build.bat
```

Output: `dist\TXTDrop.exe`

The script automatically generates `icon.ico` before building.  
To generate the icon separately:

```
python create_icon.py
```

---

## Build Installer (optional)

1. Build the executable first (`build.bat`)
2. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
3. Open `installer.iss` in Inno Setup Compiler
4. Click **Build → Compile**

Output: `Output\TXTDropSetup.exe`

The installer:
- Installs `TXTDrop.exe` to `Program Files`
- Creates a Start Menu entry
- Optionally adds a Windows startup registry entry

---

## Files

| File | Description |
|------|-------------|
| `main.py` | Application entry point |
| `create_icon.py` | Generates `icon.ico` for the build |
| `requirements.txt` | Python dependencies |
| `build.bat` | Builds `dist\TXTDrop.exe` |
| `installer.iss` | Inno Setup installer script |
| `config.json` | Created at runtime — stores save folder path |
