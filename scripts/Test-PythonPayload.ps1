param(
    [ValidateSet('Debug', 'Release')][string]$Configuration = 'Release',
    [ValidateSet('x64', 'AnyCPU')][string]$Platform = 'x64',
    [string]$RepositoryRoot = (Split-Path $PSScriptRoot -Parent)
)
$ErrorActionPreference = 'Stop'

function Get-PayloadHash([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha256.ComputeHash($stream)) }
    finally { $sha256.Dispose(); $stream.Dispose() }
}

# Read assembly identities without loading any add-in or Revit code.
foreach ($year in @('App', 2024, 2025, 2026, 2027)) {
    $framework = if ($year -eq 'App' -or $year -eq 2024) { 'net48' } elseif ($year -eq 2027) { 'net10.0-windows' } else { 'net8.0-windows' }
    $scripts = if ($year -eq 2027) { 'Scripts34' } else { 'Scripts27' }
    $otherScripts = if ($year -eq 2027) { 'Scripts27' } else { 'Scripts34' }
    $engine = if ($year -eq 2027) { '3.4.2.0' } else { '2.7.12.0' }
    $dlr = if ($year -eq 2027) { '1.3.5.0' } else { '1.3.1.0' }
    $payload = Join-Path $RepositoryRoot "src/addins/Batch.AddIn.$year/bin/x64/$Configuration"
    if ($year -eq 'App') { $payload = Join-Path $RepositoryRoot "src/apps/Batch.App.Gui/bin/x64/$Configuration" }
    $nested = Get-ChildItem $payload -Directory -Recurse | Where-Object { $_.Name -match '^net(48|8[.-]|10[.-])' }
    if ($nested) { throw "$year includes nested framework outputs: $($nested.FullName -join ', ')" }
    if ($year -ne 'App' -and -not (Test-Path (Join-Path $payload "Batch.AddIn.$year.dll"))) { throw "$year missing add-in assembly" }
    foreach ($assembly in @('IronPython', 'IronPython.Modules', 'Microsoft.Dynamic', 'Microsoft.Scripting', 'Microsoft.Scripting.Metadata')) {
        $path = Join-Path $payload "$assembly.dll"
        $actual = [Reflection.AssemblyName]::GetAssemblyName($path).Version.ToString()
        $expected = if ($assembly.StartsWith('IronPython')) { $engine } else { $dlr }
        if ($actual -cne $expected) { throw "$year incompatible $assembly version: $actual (expected $expected)" }
    }
    foreach ($shared in @('Batch.Shared.ScriptHost', 'Batch.Shared.Util')) {
        $platformFolder = if ($Platform -eq 'AnyCPU') { '' } else { "$Platform/" }
        $expectedPath = Join-Path $RepositoryRoot "src/shared/$shared/bin/$platformFolder$Configuration/$framework/$shared.dll"
        $actualPath = Join-Path $payload "$shared.dll"
        if ((Get-PayloadHash $expectedPath) -cne (Get-PayloadHash $actualPath)) {
            throw "$year has stale/wrong-target $shared; rebuild the solution."
        }
    }
    # Verify the full engine/DLR file set against the restored runtime assets,
    # not just major versions (same-name DLLs from different targets can differ).
    $assetsPath = Join-Path $RepositoryRoot "src/addins/Batch.AddIn.$year/obj/project.assets.json"
    if ($year -eq 'App') { $assetsPath = Join-Path $RepositoryRoot 'src/shared/Batch.Shared.ScriptHost/obj/project.assets.json' }
    $assets = Get-Content $assetsPath -Raw | ConvertFrom-Json
    $target = $assets.targets.PSObject.Properties | Where-Object { $_.Name -notmatch '/' -and ($year -ne 'App' -or $_.Name -eq '.NETFramework,Version=v4.8' -or $_.Name -eq 'net48') } | Select-Object -First 1
    if (-not $target) { throw "$year missing restored target graph" }
    foreach ($package in $target.Value.PSObject.Properties | Where-Object { $_.Name -match '^(IronPython|DynamicLanguageRuntime)/' }) {
        foreach ($asset in $package.Value.runtime.PSObject.Properties | Where-Object { $_.Name.EndsWith('.dll') }) {
            # Legacy desktop apps copy only referenced engine modules, unlike SDK add-ins.
            if ($year -eq 'App' -and [IO.Path]::GetFileName($asset.Name) -in @('IronPython.SQLite.dll', 'IronPython.Wpf.dll')) { continue }
            $restoredPath = $null
            foreach ($folder in $assets.packageFolders.PSObject.Properties.Name) {
                $candidate = Join-Path (Join-Path $folder $package.Name.ToLowerInvariant()) $asset.Name
                if (Test-Path $candidate) { $restoredPath = $candidate; break }
            }
            if (-not $restoredPath) { throw "$year missing restored asset $($asset.Name)" }
            $destination = Join-Path $payload ([IO.Path]::GetFileName($asset.Name))
            if ((Get-PayloadHash $restoredPath) -cne (Get-PayloadHash $destination)) {
                throw "$year incompatible engine/DLR asset $destination"
            }
        }
    }
    if (Test-Path (Join-Path $payload $otherScripts)) { throw "$year includes incompatible $otherScripts" }
    $sourceScripts = @(Get-ChildItem (Join-Path $RepositoryRoot "src/shared/Batch.Shared.Util/$scripts") -Filter *.py -Recurse)
    $payloadScripts = @(Get-ChildItem (Join-Path $payload $scripts) -Filter *.py -Recurse)
    if ($sourceScripts.Count -ne $payloadScripts.Count) { throw "$year includes missing/extra host modules" }
    foreach ($source in $sourceScripts) {
        $relative = $source.FullName.Substring((Join-Path $RepositoryRoot 'src/shared/Batch.Shared.Util').Length + 1)
        $destination = Join-Path $payload $relative
        if ((Get-PayloadHash $source.FullName) -cne (Get-PayloadHash $destination)) { throw "$year stale host script: $relative" }
    }
    if ($year -eq 2027) {
        if (-not (Test-Path (Join-Path $payload 'lib/os.py'))) { throw '2027 missing Python 3 standard library' }
        $library = $assets.libraries.PSObject.Properties['IronPython.StdLib/3.4.2'].Value
        if (-not $library) { throw '2027 missing restored Python 3 standard library package' }
        foreach ($file in $library.files | Where-Object { $_ -like 'contentFiles/any/any/lib/*' }) {
            $restoredPath = $null
            foreach ($folder in $assets.packageFolders.PSObject.Properties.Name) {
                $candidate = Join-Path (Join-Path $folder $library.path) $file
                if (Test-Path $candidate) { $restoredPath = $candidate; break }
            }
            if (-not $restoredPath) { throw "2027 missing restored standard-library file $file" }
            $destination = Join-Path $payload $file.Substring('contentFiles/any/any/'.Length)
            if ((Get-PayloadHash $restoredPath) -cne (Get-PayloadHash $destination)) {
                throw "2027 stale/incompatible standard-library file $destination"
            }
        }
    } elseif (Test-Path (Join-Path $payload 'lib')) { throw "$year includes a loose Python 3 standard library" }
    Write-Host "$year payload passed: $framework / IronPython $engine / DLR $dlr / $scripts"
}