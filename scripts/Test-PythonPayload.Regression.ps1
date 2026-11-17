# Requires restored assets/cache and existing x64 shared outputs; never builds or loads Revit.
[CmdletBinding()]
param(
    [ValidateSet('Debug', 'Release')][string]$Configuration = 'Release',
    [string]$RepositoryRoot
)
$ErrorActionPreference = 'Stop'
if (-not $RepositoryRoot) { $RepositoryRoot = Split-Path $PSScriptRoot -Parent }
$validator = Join-Path $RepositoryRoot 'scripts/Test-PythonPayload.ps1'
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('Batch-PythonPayload-' + [Guid]::NewGuid().ToString('N'))
$script:passed = 0

function Write-FixtureText([string]$Path, [string]$Text) {
    $null = New-Item -ItemType Directory -Path (Split-Path $Path -Parent) -Force
    [IO.File]::WriteAllText($Path, $Text)
}

function Copy-FixtureFile([string]$Source, [string]$Destination) {
    $null = New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

function Find-CachedFile($Graph, [string]$PackagePath, [string]$Asset) {
    foreach ($cacheRoot in $Graph.packageFolders.PSObject.Properties.Name) {
        $candidate = Join-Path (Join-Path $cacheRoot $PackagePath) $Asset
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    throw "Required restored cache file missing: $PackagePath/$Asset"
}

function Assert-Payload([string]$Name, [string]$Rejection = '') {
    $failure = $null
    try { & $validator -Configuration $Configuration -Platform x64 -RepositoryRoot $fixture *> $null }
    catch { $failure = $_ }
    if ($Rejection) {
        if (-not $failure) { throw "$Name : validator unexpectedly accepted the fixture" }
        if (-not $failure.Exception.Message.Contains($Rejection)) { throw $failure }
    } elseif ($failure) { throw $failure }
    $script:passed++
    Write-Host "PASS $script:passed : $Name"
}

try {
    foreach ($scriptFolder in @('Scripts27', 'Scripts34')) {
        Write-FixtureText (Join-Path $fixture "src/shared/Batch.Shared.Util/$scriptFolder/host.py") "# synthetic host module`n"
    }
    $payloads = @{}
    $cachedEngines = @{}
    foreach ($year in @('App', '2024', '2025', '2026', '2027')) {
        $framework = if ($year -in @('App', '2024')) { 'net48' } elseif ($year -eq '2027') { 'net10.0-windows' } else { 'net8.0-windows' }
        $projectPath = if ($year -eq 'App') { 'src/shared/Batch.Shared.ScriptHost' } else { "src/addins/Batch.AddIn.$year" }
        $assetsRelative = "$projectPath/obj/project.assets.json"
        $graph = Get-Content -LiteralPath (Join-Path $RepositoryRoot $assetsRelative) -Raw | ConvertFrom-Json
        $targetEntry = $graph.targets.PSObject.Properties | Where-Object {
            $_.Name -notmatch '/' -and ($year -ne 'App' -or $_.Name -in @('.NETFramework,Version=v4.8', 'net48'))
        } | Select-Object -First 1
        if (-not $targetEntry) { throw "Required restored target missing: $assetsRelative" }
        $payloadRelative = if ($year -eq 'App') { "src/apps/Batch.App.Gui/bin/x64/$Configuration" } else { "$projectPath/bin/x64/$Configuration" }
        $payload = Join-Path $fixture $payloadRelative
        $payloads[$year] = $payload
        $cachedEngines[$year] = @{}
        $packages = @{}
        foreach ($packageEntry in $targetEntry.Value.PSObject.Properties | Where-Object { $_.Name -match '^(IronPython|DynamicLanguageRuntime)/' }) {
            $packages[$packageEntry.Name] = @{ runtime = $packageEntry.Value.runtime }
            foreach ($runtimeEntry in $packageEntry.Value.runtime.PSObject.Properties | Where-Object { $_.Name.EndsWith('.dll') }) {
                $dllName = [IO.Path]::GetFileName($runtimeEntry.Name)
                $cachedFile = Find-CachedFile $graph $packageEntry.Name.ToLowerInvariant() $runtimeEntry.Name
                $cachedEngines[$year][$dllName] = $cachedFile
                if ($year -eq 'App' -and $dllName -in @('IronPython.SQLite.dll', 'IronPython.Wpf.dll')) { continue }
                Copy-FixtureFile $cachedFile (Join-Path $payload $dllName)
            }
        }
        if ($packages.Count -ne 2) { throw "Expected restored IronPython and DLR packages: $assetsRelative" }
        $libraries = @{}
        if ($year -eq '2027') {
            $stdlib = $graph.libraries.PSObject.Properties['IronPython.StdLib/3.4.2'].Value
            if (-not $stdlib) { throw 'Required restored IronPython.StdLib/3.4.2 missing' }
            $stdlibFiles = @('contentFiles/any/any/lib/os.py', 'contentFiles/any/any/lib/json/__init__.py')
            $libraries['IronPython.StdLib/3.4.2'] = @{ path = $stdlib.path; files = $stdlibFiles }
            foreach ($stdlibFile in $stdlibFiles) {
                if ($stdlibFile -notin $stdlib.files) { throw "Required standard-library manifest entry missing: $stdlibFile" }
                $cachedFile = Find-CachedFile $graph $stdlib.path $stdlibFile
                Copy-FixtureFile $cachedFile (Join-Path $payload $stdlibFile.Substring('contentFiles/any/any/'.Length))
            }
            $expectedJsonSource = Find-CachedFile $graph $stdlib.path $stdlibFiles[1]
        }
        $targets = @{}
        $targets[$targetEntry.Name] = $packages
        $minimalGraph = @{ targets = $targets; packageFolders = $graph.packageFolders; libraries = $libraries }
        Write-FixtureText (Join-Path $fixture $assetsRelative) ($minimalGraph | ConvertTo-Json -Depth 30)
        foreach ($shared in @('Batch.Shared.ScriptHost', 'Batch.Shared.Util')) {
            $sharedRelative = "src/shared/$shared/bin/x64/$Configuration/$framework/$shared.dll"
            $sharedSource = Join-Path $RepositoryRoot $sharedRelative
            Copy-FixtureFile $sharedSource (Join-Path $fixture $sharedRelative)
            Copy-FixtureFile $sharedSource (Join-Path $payload "$shared.dll")
        }
        $scriptFolder = if ($year -eq '2027') { 'Scripts34' } else { 'Scripts27' }
        Copy-FixtureFile (Join-Path $fixture "src/shared/Batch.Shared.Util/$scriptFolder/host.py") (Join-Path $payload "$scriptFolder/host.py")
        if ($year -ne 'App') { Write-FixtureText (Join-Path $payload "Batch.AddIn.$year.dll") 'synthetic existence marker' }
    }
    Assert-Payload 'baseline; both GUI optional DLLs absent'
    $optionalDlls = @('IronPython.SQLite.dll', 'IronPython.Wpf.dll')
    foreach ($optionalDll in $optionalDlls) {
        $optionalPath = Join-Path $payloads['App'] $optionalDll
        try {
            Copy-FixtureFile $cachedEngines['App'][$optionalDll] $optionalPath
            Assert-Payload "$optionalDll correct; other GUI optional DLL absent"
            Copy-FixtureFile $cachedEngines['2027'][$optionalDll] $optionalPath
            Assert-Payload "$optionalDll from IronPython 3 rejected" 'App incompatible engine/DLR asset'
        } finally { Remove-Item -LiteralPath $optionalPath -Force -ErrorAction Stop }
    }
    try {
        foreach ($optionalDll in $optionalDlls) {
            Copy-FixtureFile $cachedEngines['App'][$optionalDll] (Join-Path $payloads['App'] $optionalDll)
        }
        Assert-Payload 'both correct GUI optional DLLs present'
    } finally {
        foreach ($optionalDll in $optionalDlls) {
            $optionalPath = Join-Path $payloads['App'] $optionalDll
            if (Test-Path -LiteralPath $optionalPath) { Remove-Item -LiteralPath $optionalPath -Force }
        }
    }
    Assert-Payload 'GUI optional DLL baseline restored'
    $libRoot = Join-Path $payloads['2027'] 'lib'
    foreach ($extra in @('extra.py', 'os/__init__.py', 'extra.dat', 'hidden.dat')) {
        $extraPath = Join-Path $libRoot $extra
        try {
            Write-FixtureText $extraPath 'unmanifested content'
            if ($extra -eq 'hidden.dat') {
                [IO.File]::SetAttributes($extraPath, ([IO.File]::GetAttributes($extraPath) -bor [IO.FileAttributes]::Hidden))
                if (([IO.File]::GetAttributes($extraPath) -band [IO.FileAttributes]::Hidden) -eq 0) { throw 'Hidden attribute was not set' }
            }
            Assert-Payload "stdlib extra $extra rejected" 'unmanifested standard-library file'
        } finally {
            if (Test-Path -LiteralPath $extraPath) { Remove-Item -LiteralPath $extraPath -Force }
            if ($extra -eq 'os/__init__.py') {
                $shadowDirectory = Join-Path $libRoot 'os'
                if (Test-Path -LiteralPath $shadowDirectory) { Remove-Item -LiteralPath $shadowDirectory -Force }
            }
        }
    }
    $expectedJson = Join-Path $libRoot 'json/__init__.py'
    $replacement = Join-Path $libRoot 'json/unexpected.py'
    try {
        Move-Item -LiteralPath $expectedJson -Destination $replacement
        Assert-Payload 'same-count stdlib replacement rejected' 'unmanifested standard-library file'
    } finally {
        if (Test-Path -LiteralPath $replacement) { Move-Item -LiteralPath $replacement -Destination $expectedJson }
    }
    $stash = Join-Path $fixture 'saved-json.py'
    try {
        Move-Item -LiteralPath $expectedJson -Destination $stash
        Assert-Payload 'missing expected stdlib file rejected' '2027 missing standard-library files'
    } finally {
        if (Test-Path -LiteralPath $stash) { Move-Item -LiteralPath $stash -Destination $expectedJson }
    }
    try {
        [IO.File]::AppendAllText($expectedJson, "`n# changed hash`n")
        Assert-Payload 'modified expected stdlib hash rejected' '2027 stale/incompatible standard-library file'
    } finally { Copy-FixtureFile $expectedJsonSource $expectedJson }
    Assert-Payload 'final restored baseline'
} finally {
    if (Test-Path -LiteralPath $fixture) { Remove-Item -LiteralPath $fixture -Recurse -Force }
}
Write-Host "PASS: $script:passed regression checks; temporary fixture removed."