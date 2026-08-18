param(
    [string]$OutputFilePath,
    [string]$Operator = "",
    [string]$EnvironmentName = "",
    [string]$PolicyConstraints = "",
    [switch]$OpenInEditor
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$templatePath = Join-Path $repoRoot "docs\winui-parity-interactive-capture-template.md"

if (-not (Test-Path $templatePath)) {
    throw "Template not found at: $templatePath"
}

if ([string]::IsNullOrWhiteSpace($OutputFilePath)) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputFilePath = Join-Path $repoRoot ("docs\winui-parity-interactive-capture-" + $timestamp + ".md")
}

$outputDirectory = Split-Path -Path $OutputFilePath -Parent
if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
    New-Item -Path $outputDirectory -ItemType Directory -Force | Out-Null
}

$branch = "(unknown)"
$commit = "(unknown)"

Push-Location $repoRoot
try {
    $branchResult = git rev-parse --abbrev-ref HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($branchResult)) {
        $branch = $branchResult.Trim()
    }

    $commitResult = git rev-parse --short HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($commitResult)) {
        $commit = $commitResult.Trim()
    }
}
finally {
    Pop-Location
}

if ([string]::IsNullOrWhiteSpace($Operator)) {
    $Operator = "$env:USERNAME"
}

if ([string]::IsNullOrWhiteSpace($EnvironmentName)) {
    $EnvironmentName = "Interactive parity validation"
}

if ([string]::IsNullOrWhiteSpace($PolicyConstraints)) {
    $PolicyConstraints = "Document any AppLocker, elevation, or Revit-host restrictions encountered during capture."
}

$revitVersions = @()
foreach ($year in 2024..2027) {
    $addinPath = Join-Path $env:APPDATA ("Autodesk\Revit\Addins\" + $year + "\BatchRvtAddin" + $year + ".addin")
    if (Test-Path $addinPath) {
        $revitVersions += $year
    }
}

$revitVersionsText = if ($revitVersions.Count -gt 0) {
    ($revitVersions | ForEach-Object { "Revit " + $_ }) -join ", "
}
else {
    "(none detected in %APPDATA% add-ins path)"
}

$dateText = Get-Date -Format "yyyy-MM-dd"
$captureContent = @"
# WinUI Parity Interactive Capture Template

Date: $dateText

Session metadata:

- Operator: $Operator
- Environment name: $EnvironmentName
- Machine: $env:COMPUTERNAME
- Branch and commit: $branch ($commit)
- Revit versions installed: $revitVersionsText
- Policy constraints observed: $PolicyConstraints

Input set used for both UIs:

- Settings file:
- Task script:
- Revit file list:
- Log folder:

## Scenario 3 Capture

### WinForms observations

- Launch result:
- Running indicator:
- Completion indicator:
- Final status text:
- Timestamped notes:

### WinUI observations

- Launch result:
- Running indicator:
- Completion indicator:
- Final status text:
- Timestamped notes:

### Scenario 3 parity checkpoints

| Checkpoint | WinForms | WinUI | Parity Result | Notes |
| --- | --- | --- | --- | --- |
| Launch success/failure shape equivalent |  |  | PASS or PARTIAL |  |
| Running-state transition equivalent |  |  | PASS or PARTIAL |  |
| Completion signaling equivalent |  |  | PASS or PARTIAL |  |

Scenario 3 overall:

- PASS or PARTIAL:
- Rationale:

## Scenario 4 Capture

### WinForms observations

- Stop action trigger used:
- Close-time prompt flow observed:
- Final termination state:
- Operator-facing feedback:
- Timestamped notes:

### WinUI observations

- Stop action trigger used:
- Close-time prompt flow observed:
- Final termination state:
- Operator-facing feedback:
- Timestamped notes:

### Scenario 4 parity checkpoints

| Checkpoint | WinForms | WinUI | Parity Result | Notes |
| --- | --- | --- | --- | --- |
| Stop action available while running |  |  | PASS or PARTIAL |  |
| Close-time prompt flow equivalent |  |  | PASS or PARTIAL |  |
| Final process termination outcome equivalent |  |  | PASS or PARTIAL |  |
| Operator feedback equivalence in meaning |  |  | PASS or PARTIAL |  |

Scenario 4 overall:

- PASS or PARTIAL:
- Rationale:

## Attachments

- Screenshots or recordings:
- Logs:
- Additional artifacts:

## Gate Decision Update

- Scenario 3 final result:
- Scenario 4 final result:
- P2 status recommendation:
- Follow-up work items:
"@

Set-Content -Path $OutputFilePath -Value $captureContent -Encoding UTF8

Write-Host "Created interactive capture file: $OutputFilePath"

if ($OpenInEditor) {
    $codeCommand = Get-Command code -ErrorAction SilentlyContinue
    if ($null -ne $codeCommand) {
        & $codeCommand.Source $OutputFilePath
    }
    else {
        Write-Warning "VS Code command line launcher ('code') is not available on PATH."
    }
}
