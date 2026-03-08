[Setup]
AppName=TXTDrop
AppVersion=1.0
AppPublisher=TXTDrop
DefaultDirName={autopf}\TXTDrop
DefaultGroupName=TXTDrop
OutputBaseFilename=TXTDropSetup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\TXTDrop.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TXTDrop"; Filename: "{app}\TXTDrop.exe"
Name: "{group}\Uninstall TXTDrop"; Filename: "{uninstallexe}"

[Tasks]
Name: "startup"; Description: "Launch TXTDrop automatically on Windows startup"; GroupDescription: "Startup Options:"; Flags: unchecked

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "TXTDrop"; ValueData: """{app}\TXTDrop.exe"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\TXTDrop.exe"; Description: "Launch TXTDrop now"; Flags: nowait postinstall skipifsilent
