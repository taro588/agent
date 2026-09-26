#define MyAppName "GameArt AI Toolkit"
#define MyAppVersion GetVersionNumbersString("..\dist\GameArtAI.exe")
#define MyAppPublisher "GameArt AI Toolkit"
#define MyAppExeName "GameArtAI.exe"

[Setup]
AppId={{B7F1D6B4-7B58-4A8D-9A1A-4B3D2F1E9C11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\GameArt AI Toolkit
DisableProgramGroupPage=yes
OutputBaseFilename=GameArt-AI-Toolkit-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayName={#MyAppName}

[Files]
Source: "..\dist\GameArtAI.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\GameArt AI Toolkit"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch GameArt AI Toolkit"; Flags: nowait postinstall skipifsilent
