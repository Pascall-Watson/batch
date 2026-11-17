@echo off

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\..\scripts\Test-PythonPayload.ps1" -Configuration Release
if errorlevel 1 exit /b 1

call inno_setup_compile.bat RevitBatchProcessor.iss
