<#
.SYNOPSIS
    Removes all traces of the Revit Batch Processor (BatchRvt) from this machine.

.DESCRIPTION
    Cleans up everything installed or created by the Revit Batch Processor
    Inno installer and its runtime data:

      * %LOCALAPPDATA%\RevitBatchProcessor            (main install dir)
      * %APPDATA%\Autodesk\Revit\Addins\<year>\BatchRvt            (addin folders)
      * %APPDATA%\Autodesk\Revit\Addins\<year>\BatchRvtAddin<year>.addin (manifests,
        including legacy versions 2015-2027 left by older installers)
      * %APPDATA%\BatchRvt                            (GUI settings: BatchRvtGui.Settings.json)
      * %LOCALAPPDATA%\BatchRvt                       (script/session data + logs)
      * Start Menu shortcut group "Revit Batch Processor"
      * HKCU uninstall registry key {B5CA57EA-7BB2-4620-916C-AE98376C1EF1}_is1

    Run the official uninstaller first if it still exists:
      %LOCALAPPDATA%\RevitBatchProcessor\unins000.exe

.PARAMETER WhatIf
    Shows what would be deleted without deleting anything.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Remove-RevitBatchProcessor.ps1 -WhatIf
    powershell -ExecutionPolicy Bypass -File .\Remove-RevitBatchProcessor.ps1
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param()

$ErrorActionPreference = 'Continue'

# --- Safety: Revit must be closed -------------------------------------------------
$revitProcesses = Get-Process -Name 'Revit', 'RevitAccelerator' -ErrorAction SilentlyContinue
if ($revitProcesses) {
    Write-Warning 'Revit is currently running. Close all Revit instances before running this script.'
    $revitProcesses | ForEach-Object { Write-Warning ("  PID {0}: {1}" -f $_.Id, $_.ProcessName) }
    exit 1
}

$script:removedCount = 0
$script:failedCount  = 0

# $PSCmdlet is $null when the script body is executed via Invoke-Expression/iex
# (e.g. to bypass AppLocker path rules). Fall back to "always proceed" in that case.
function Test-ShouldProcess {
    param(
        [Parameter(Mandatory)][string]$Target,
        [Parameter(Mandatory)][string]$Action
    )
    if ($null -ne $PSCmdlet) {
        return $PSCmdlet.ShouldProcess($Target, $Action)
    }
    return $true
}

function Remove-ItemSafely {
    param(
        [Parameter(Mandatory)][string]$Path,
        [string]$Description = ''
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Verbose "Not present: $Path"
        return
    }
    $label = if ($Description) { $Description } else { $Path }
    if (Test-ShouldProcess -Target $Path -Action "Remove $label") {
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            Write-Host "[REMOVED] $Path" -ForegroundColor Green
            $script:removedCount++
        }
        catch {
            Write-Warning "[FAILED]  $Path -- $($_.Exception.Message)"
            $script:failedCount++
        }
    }
}

Write-Host ''
Write-Host '=== Revit Batch Processor cleanup ===' -ForegroundColor Cyan

# --- 1. Main install directory -----------------------------------------------------
Remove-ItemSafely -Path (Join-Path $env:LOCALAPPDATA 'RevitBatchProcessor') `
                  -Description 'Main install directory'

# --- 2. Revit addin folders + manifest files (all years, incl. legacy 2015-2027) ---
$addinsRoot = Join-Path $env:APPDATA 'Autodesk\Revit\Addins'
if (Test-Path -LiteralPath $addinsRoot) {
    $yearDirs = Get-ChildItem -LiteralPath $addinsRoot -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match '^\d{4}$' }

    foreach ($yearDir in $yearDirs) {
        Remove-ItemSafely -Path (Join-Path $yearDir.FullName 'BatchRvt') `
                          -Description "Addin folder (Revit $($yearDir.Name))"
        Remove-ItemSafely -Path (Join-Path $yearDir.FullName "BatchRvtAddin$($yearDir.Name).addin") `
                          -Description "Addin manifest (Revit $($yearDir.Name))"
    }
}
else {
    Write-Verbose "Not present: $addinsRoot"
}

# --- 3. Runtime data written by the app --------------------------------------------
Remove-ItemSafely -Path (Join-Path $env:APPDATA 'BatchRvt') `
                  -Description 'GUI settings (BatchRvtGui.Settings.json)'
Remove-ItemSafely -Path (Join-Path $env:LOCALAPPDATA 'BatchRvt') `
                  -Description 'Script/session data and logs'

# --- 4. Start Menu shortcut group ----------------------------------------------------
Remove-ItemSafely -Path (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Revit Batch Processor') `
                  -Description 'Start Menu shortcut group'

# --- 5. Uninstall registry key -------------------------------------------------------
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{B5CA57EA-7BB2-4620-916C-AE98376C1EF1}_is1'
if (Test-Path -LiteralPath $uninstallKey) {
    if (Test-ShouldProcess -Target $uninstallKey -Action 'Remove uninstall registry key') {
        try {
            Remove-Item -LiteralPath $uninstallKey -Recurse -Force -ErrorAction Stop
            Write-Host "[REMOVED] $uninstallKey" -ForegroundColor Green
            $script:removedCount++
        }
        catch {
            Write-Warning "[FAILED]  $uninstallKey -- $($_.Exception.Message)"
            $script:failedCount++
        }
    }
}
else {
    Write-Verbose "Not present: $uninstallKey"
}

# --- Summary -------------------------------------------------------------------------
Write-Host ''
Write-Host ("Done. Removed: {0}  Failed: {1}" -f $script:removedCount, $script:failedCount) -ForegroundColor Cyan
if ($script:failedCount -gt 0) {
    Write-Warning 'Some items could not be removed. Check that no files are locked (Revit/Explorer) and re-run.'
    exit 1
}
