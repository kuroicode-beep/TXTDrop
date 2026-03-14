# TXTDrop

A minimal Windows clipboard saving utility.  
Runs in the system tray. Press a hotkey. Clipboard is saved.

---

## Usage

| Clipboard | Hotkey | Result |
|-----------|--------|--------|
| Text | `CTRL + SHIFT + Z` | `txtdrop_<title>_YYYYMMDD_HHMMSS.txt` |
| Image | `CTRL + SHIFT + Z` | `txtdrop_YYYYMMDD_HHMMSS.png` |
| Empty | `CTRL + SHIFT + Z` | Nothing happens |

Right-click the tray icon to access **Settings**, **Log**, **Ollama refresh**, or **Exit**.

---

## Setup

### 1. Install dependencies

```
py -3.12 -m pip install -r requirements.txt
```

### 2. Run directly

```
py -3.12 main.py
```

On first launch a folder selection dialog appears.  
The chosen path is saved to `txtdrop.db` (SQLite) next to the executable.

---

## Build Executable

Requires [PyInstaller](https://pyinstaller.org/):

```
py -3.12 -m pip install pyinstaller
```

Then run the build script:

```
build.bat
```

Output: `dist\TXTDrop\TXTDrop.exe`

The script automatically generates `icon.ico` before building.  
To generate the icon separately:

```
py -3.12 create_icon.py
```

---

## Build Installer (optional)

1. Build the executable first (`build.bat`)
2. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
3. Run `build.bat` — it calls Inno Setup automatically if installed

Output: `Output\TXTDropSetup.exe`

The installer:
- Installs `TXTDrop\` folder to `%LocalAppData%\Programs`
- Creates a Start Menu entry
- Optionally adds a Windows startup registry entry

---

## Files

| File | Description |
|------|-------------|
| `main.py` | Application entry point |
| `config.py` | Settings & log persistence (SQLite) |
| `ollama_client.py` | Ollama API integration for AI filenames |
| `create_icon.py` | Generates `icon.ico` for the build |
| `requirements.txt` | Python dependencies |
| `TXTDrop.spec` | PyInstaller build spec (onedir) |
| `build.bat` | Full build pipeline (icon → PyInstaller → Inno Setup) |
| `installer.iss` | Inno Setup installer script |
| `txtdrop.db` | Created at runtime — stores settings, history, logs |
