#define AppName "Revit Batch Processor"
#define AppVersion "2.1.1.0"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
PrivilegesRequired=lowest
AppId={{B5CA57EA-7BB2-4620-916C-AE98376C1EF1}
DisableDirPage=auto
DefaultDirName={localappdata}\RevitBatchProcessor
SetupLogging=True
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
DefaultGroupName=Revit Batch Processor
OutputBaseFilename=Pascall-Watson-RevitBatchProcessor-2.1.1.0-Setup
OutputDir=Output

; TODO VERSION UPDATE - ADD FILES TO INSTALLER CONFIG
[Files]
Source: "..\BatchRvtGUI\bin\x64\Release\*"; DestDir: "{app}"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\BatchRvtAddin2024\bin\x64\Release\*"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2024\BatchRvt"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\BatchRvtAddin2024\BatchRvtAddin2024.addin"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2024"; Flags: ignoreversion
Source: "..\BatchRvtAddin2025\bin\x64\Release\*"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2025\BatchRvt"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\BatchRvtAddin2025\BatchRvtAddin2025.addin"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2025"; Flags: ignoreversion
Source: "..\BatchRvtAddin2026\bin\x64\Release\*"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2026\BatchRvt"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\BatchRvtAddin2026\BatchRvtAddin2026.addin"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2026"; Flags: ignoreversion
Source: "..\BatchRvtAddin2027\bin\x64\Release\*"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2027\BatchRvt"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\BatchRvtAddin2027\BatchRvtAddin2027.addin"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2027"; Flags: ignoreversion
[Icons]
Name: "{group}\Revit Batch Processor (GUI)"; Filename: "{app}\BatchRvtGUI.exe"; WorkingDir: "{app}"





