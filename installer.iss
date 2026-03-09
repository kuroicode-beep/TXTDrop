[Setup]
AppName=TXTDrop
AppVersion=0.4
AppPublisher=SVIL — Singularity Visual Intelligence Lab
AppPublisherURL=https://github.com/kuroicode-beep/TXTDrop
DefaultDirName={autopf}\TXTDrop
DefaultGroupName=TXTDrop
OutputDir=Output
OutputBaseFilename=TXTDropSetup
SetupIconFile=icon.ico
WizardStyle=modern
WizardImageFile=wizard_large.bmp
WizardSmallImageFile=wizard_small.bmp
WizardImageStretch=no
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Languages]
Name: "korean";  MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\TXTDrop.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TXTDrop";           Filename: "{app}\TXTDrop.exe"
Name: "{group}\Uninstall TXTDrop"; Filename: "{uninstallexe}"

[Tasks]
Name: "startup"; Description: "Windows 시작 시 TXTDrop 자동 실행"; GroupDescription: "시작 옵션:"; Flags: unchecked

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "TXTDrop"; ValueData: """{app}\TXTDrop.exe"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\TXTDrop.exe"; Description: "TXTDrop 지금 실행"; Flags: nowait postinstall skipifsilent
