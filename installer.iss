#define MyAppName "Fortnite Splash Maker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "zahidkaya1"
#define MyAppExeName "FortniteSplashMaker.exe"

[Setup]
AppId={{9F7D3F5E-9D93-4B2B-8C1D-6E6767A6E9D1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\FortniteSplashMaker
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=release
OutputBaseFilename=FortniteSplashMaker-v1.0.0-Setup
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
ChangesAssociations=no
VersionInfoVersion=1.0.0.0
VersionInfoCompany=zahidkaya1
VersionInfoDescription=Fortnite Splash Maker Installer
VersionInfoProductName=Fortnite Splash Maker
VersionInfoProductVersion=1.0.0.0
VersionInfoCopyright=Copyright (C) 2026 zahidkaya1

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Ek seçenekler:"; Flags: unchecked

[Files]
Source: "dist\FortniteSplashMaker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\library"

[Icons]
Name: "{autoprograms}\Fortnite Splash Maker"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\Fortnite Splash Maker"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Fortnite Splash Maker'ı çalıştır"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\settings.json"
Type: dirifempty; Name: "{app}\library"
