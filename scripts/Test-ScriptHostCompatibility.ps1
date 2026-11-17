param(
    [ValidateSet('Debug', 'Release')][string]$Configuration = 'Release',
    [string]$RepositoryRoot = (Split-Path $PSScriptRoot -Parent),
    [switch]$DesktopProbe
)
$ErrorActionPreference = 'Stop'
$probeRoot = Join-Path $RepositoryRoot "tests/Batch.ScriptHost.Compatibility/bin/$Configuration"

if ($DesktopProbe) {
    # Windows PowerShell is a .NET Framework host; no Revit or app launcher is used.
    $probe = [Reflection.Assembly]::LoadFrom((Join-Path $probeRoot 'net48/Batch.ScriptHost.Compatibility.exe'))
    $probeArgs = [string[]]@(
        (Join-Path $RepositoryRoot "src/addins/Batch.AddIn.2024/bin/x64/$Configuration"),
        '.NETFramework,Version=v4.8', 'Scripts27', '2.7.12.0', '2024'
    )
    exit $probe.EntryPoint.Invoke($null, (, $probeArgs))
}

& (Join-Path $PSScriptRoot 'Test-PythonPayload.ps1') -Configuration $Configuration -RepositoryRoot $RepositoryRoot
foreach ($year in 2024..2027) {
    $scripts = if ($year -eq 2027) { 'Scripts34' } else { 'Scripts27' }
    $handler = Get-Content (Join-Path $RepositoryRoot "src/addins/Batch.AddIn.$year/BatchRvtAddinApplication.cs") -Raw
    if ($handler -notmatch ('ExecuteBatchScriptHost\(pluginFolderPath_, uiApp, "' + $scripts + '"\)')) {
        throw "$year handler no longer selects $scripts; review the compatibility matrix."
    }
    if ($year -eq 2024) {
        $output = & "$env:SystemRoot/System32/WindowsPowerShell/v1.0/powershell.exe" -NoProfile -File $PSCommandPath -Configuration $Configuration -RepositoryRoot $RepositoryRoot -DesktopProbe 2>&1
    } else {
        $tfm = if ($year -eq 2027) { 'net10.0-windows' } else { 'net8.0-windows' }
        $framework = if ($year -eq 2027) { '.NETCoreApp,Version=v10.0' } else { '.NETCoreApp,Version=v8.0' }
        $engine = if ($year -eq 2027) { '3.4.2.0' } else { '2.7.12.0' }
        $output = & dotnet (Join-Path $probeRoot "$tfm/Batch.ScriptHost.Compatibility.dll") `
            (Join-Path $RepositoryRoot "src/addins/Batch.AddIn.$year/bin/x64/$Configuration") $framework $scripts $engine $year 2>&1
    }
    if ($LASTEXITCODE -ne 0) {
        $output | ForEach-Object { Write-Host $_ }
        throw "$year actual-engine compatibility probe failed."
    }
    Write-Host "$year : $($output | Select-Object -Last 1)"
}