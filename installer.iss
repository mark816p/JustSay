[Setup]
AppId={{9C18B47E-D477-4C07-A54A-12E7B5E1E6B9}}
AppName=JustSay
AppVersion=1.0
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

[Files]
Source: "dist\JustSay.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\JustSay"; Filename: "{app}\JustSay.exe"
Name: "{autodesktop}\JustSay"; Filename: "{app}\JustSay.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
