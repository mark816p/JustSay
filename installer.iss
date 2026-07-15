[Setup]
AppId={{9C18B47E-D477-4C07-A54A-12E7B5E1E6B9}}
AppName=JustSay
AppVersion=1.1
DefaultDirName={autopf}\JustSay
DefaultGroupName=JustSay
OutputBaseFilename=JustSay_Setup
OutputDir=dist
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UsePreviousAppDir=yes
UpdateUninstallLogAppName=yes
WizardStyle=modern
UninstallDisplayIcon={app}\JustSay.exe

[Files]
Source: "*"; DestDir: "{app}"; Excludes: "dist,build,__pycache__,.git,history_audio,*.iss"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\JustSay"; Filename: "wscript.exe"; Parameters: """{app}\JustSay.vbs"""
Name: "{autodesktop}\JustSay"; Filename: "wscript.exe"; Parameters: """{app}\JustSay.vbs"""
Name: "{userstartup}\JustSay"; Filename: "wscript.exe"; Parameters: """{app}\JustSay.vbs"""

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Run JustSay automatically when Windows starts"; GroupDescription: "Startup"; Flags: checked

[Run]
Filename: "wscript.exe"; Parameters: """{app}\JustSay.vbs"""; Description: "Launch JustSay"; Flags: nowait postinstall skipifsilent
