#define AppName "Revit Batch Processor"
#define AppVersion "2.3.3.0"

; Fail even when ISCC is invoked directly rather than through the wrapper/CI.
#define PythonPayloadCheck AddBackslash(SourcePath) + "..\..\scripts\Test-PythonPayload.ps1"
#if Exec("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File """ + PythonPayloadCheck + """ -Configuration Release", SourcePath, 1, SW_HIDE) != 0
	#error Python payload validation failed. Rebuild Release x64 and run scripts/Test-PythonPayload.ps1.
#endif

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
OutputBaseFilename=Pascall-Watson-RevitBatchProcessor-2.3.3.0-Setup
OutputDir=Output

; Remove only application-owned Python payloads before copying an upgrade.
; No user task scripts or model locations are touched.
[InstallDelete]
Type: filesandordirs; Name: "{app}\Scripts27"
Type: filesandordirs; Name: "{app}\Scripts34"
Type: filesandordirs; Name: "{app}\lib"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2024\BatchRvt\Scripts27"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2024\BatchRvt\Scripts34"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2024\BatchRvt\lib"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2025\BatchRvt\Scripts27"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2025\BatchRvt\Scripts34"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2025\BatchRvt\lib"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2026\BatchRvt\Scripts27"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2026\BatchRvt\Scripts34"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2026\BatchRvt\lib"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2027\BatchRvt\Scripts27"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2027\BatchRvt\Scripts34"
Type: filesandordirs; Name: "{userappdata}\Autodesk\Revit\Addins\2027\BatchRvt\lib"

; TODO VERSION UPDATE - ADD FILES TO INSTALLER CONFIG
[Files]
Source: "..\..\src\apps\Batch.App.Gui\bin\x64\Release\*"; DestDir: "{app}"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\..\src\addins\Batch.AddIn.2024\bin\x64\Release\*"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2024\BatchRvt"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\..\src\addins\Batch.AddIn.2024\BatchRvtAddin2024.addin"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2024"; Flags: ignoreversion
Source: "..\..\src\addins\Batch.AddIn.2025\bin\x64\Release\*"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2025\BatchRvt"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\..\src\addins\Batch.AddIn.2025\BatchRvtAddin2025.addin"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2025"; Flags: ignoreversion
Source: "..\..\src\addins\Batch.AddIn.2026\bin\x64\Release\*"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2026\BatchRvt"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\..\src\addins\Batch.AddIn.2026\BatchRvtAddin2026.addin"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2026"; Flags: ignoreversion
Source: "..\..\src\addins\Batch.AddIn.2027\bin\x64\Release\*"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2027\BatchRvt"; Flags: ignoreversion createallsubdirs recursesubdirs
Source: "..\..\src\addins\Batch.AddIn.2027\BatchRvtAddin2027.addin"; DestDir: "{userappdata}\Autodesk\Revit\Addins\2027"; Flags: ignoreversion
[Icons]
Name: "{group}\Revit Batch Processor (GUI)"; Filename: "{app}\Batch.App.Gui.exe"; WorkingDir: "{app}"








