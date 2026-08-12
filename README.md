<p align="center">
  <img src="src/apps/Batch.App.Gui/Images/batch.png" alt="Revit Batch Processor logo" width="128">
</p>

# Revit Batch Processor (RBP)

[![Release](https://img.shields.io/github/v/release/Pascall-Watson/batch?include_prereleases&label=release)](https://github.com/Pascall-Watson/batch/releases)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)](#getting-started)
[![Revit](https://img.shields.io/badge/Revit-2024--2027-0696D7)](#supported-revit-versions)
[![Downloads](https://img.shields.io/github/downloads/Pascall-Watson/batch/total)](https://github.com/Pascall-Watson/batch/releases)

Fully automated batch processing of Revit files with your own Python or Dynamo task scripts. The Pascall-Watson fork of [BVN Architecture's Revit Batch Processor](https://github.com/bvn-architecture/RevitBatchProcessor), originally authored by Daniel Rumery.

RBP helps BIM, computational design, and Revit API teams run repeatable automation across many `.rvt` and `.rfa` files without manually opening each model. Use the Windows GUI for interactive setup, or run the command-line tool from scheduled jobs and build pipelines. The batch engine handles version-aware Revit launching, central-file options, per-version add-ins, logging, dialog handling, and unattended processing.

> **This fork:** [Pascall-Watson/batch](https://github.com/Pascall-Watson/batch) · **Upstream:** [bvn-architecture/RevitBatchProcessor](https://github.com/bvn-architecture/RevitBatchProcessor) · **Current release:** <!-- RBP-VERSION -->`2.3.0.0`<!-- /RBP-VERSION --> ([download](https://github.com/Pascall-Watson/batch/releases))

## Table of Contents

- [Features](#features)
- [Supported Revit Versions](#supported-revit-versions)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Install from a Release](#install-from-a-release)
  - [Build from Source](#build-from-source)
- [Usage](#usage)
  - [Running the GUI](#running-the-gui)
  - [Running from the Command Line](#running-from-the-command-line)
  - [Revit File Lists](#revit-file-lists)
  - [Python Task Scripts](#python-task-scripts)
  - [Dynamo Task Scripts](#dynamo-task-scripts)
  - [Scheduled and Unattended Runs](#scheduled-and-unattended-runs)
  - [Loading .NET DLLs from a Task Script](#loading-net-dlls-from-a-task-script)
- [Command-Line Reference](#command-line-reference)
- [Python Task Script API](#python-task-script-api)
- [Project Structure](#project-structure)
- [Development](#development)
- [Installer and Packaging](#installer-and-packaging)
- [Release Process](#release-process)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Support](#support)

## Features

- **Batch Revit automation** — process many project and family files with one repeatable workflow.
- **Python and Dynamo task scripts** — run custom Revit API logic or Dynamo workspaces against each file.
- **Version-aware processing** — select a fixed Revit version or let RBP match the version each file was saved in.
- **Central file workflows** — detach from central, create new local files, audit files, and control workset opening behavior.
- **GUI and CLI entry points** — configure jobs visually, export them as JSON settings, and run the same job unattended.
- **Automatic dialog handling** — capture and respond to common English-language Revit dialogs during processing.
- **Pre- and post-processing hooks** — prepare inputs and clean up outputs around the main task script.
- **File-list generation** — scan folders for `.rvt` and `.rfa` files and produce a text list compatible with RBP.
- **BIM 360 / ACC / Forma cloud model support** — process cloud models using Revit version, project GUID, and model GUID entries, with an optional region code.
- **Per-file sessions and timeouts** — isolate crashes and hang-prone models so one file does not block the batch.

## Supported Revit Versions

This fork ships one add-in project per Revit version. Each add-in embeds the script host and Python engine appropriate for its Revit runtime:

| Revit version | Add-in project | Target framework | Python engine |
| --- | --- | --- | --- |
| 2024 | `Batch.AddIn.2024` | .NET Framework 4.8 | IronPython 2.7 (`Scripts27`) |
| 2025 | `Batch.AddIn.2025` | .NET 8 (`net8.0-windows`) | IronPython 2.7 (`Scripts27`) |
| 2026 | `Batch.AddIn.2026` | .NET 8 (`net8.0-windows`) | IronPython 2.7 (`Scripts27`) |
| 2027 | `Batch.AddIn.2027` | .NET 10 (`net10.0-windows`) | IronPython 3.4 (`Scripts34`) |

Revit API assemblies are restored from NuGet (`Nice3point.Revit.Api.RevitAPI` / `Nice3point.Revit.Api.RevitAPIUI`), so a local Revit installation is not required to build — only to run.

## Tech Stack

| Area | Technology | Notes |
| --- | --- | --- |
| Primary language | C# | Legacy project files for the apps; SDK-style projects for the add-ins and shared libraries. |
| Desktop framework | Windows Forms | Used by the `Batch.App.Gui` application. |
| Apps runtime | .NET Framework 4.8 | `Batch.App.Gui`, `Batch.App.Cli`, and `Batch.Integration.Dynamo`. |
| Shared libraries | `net48` + `net10.0-windows` | `Batch.Shared.Util` and `Batch.Shared.ScriptHost` multi-target both runtimes. |
| Script execution | IronPython 2.7.12 / 3.4.2 | Engine selected per Revit version; see the matrix above. |
| Visual scripting | Dynamo (version tied to Revit) | Runs `.dyn` workspaces via the Dynamo for Revit build installed for the target Revit version. |
| Data input | `.txt`, `.xlsx` | Text files contain one model path per line; Excel files use the first column. |
| Serialization | Newtonsoft.Json | Referenced from `third_party/References`; used for settings and data exchange. |
| Testing | xUnit 2.x, FluentAssertions, Moq | `tests/Batch.Shared.Util.Tests` covers utility, settings, and CLI argument behavior. |
| Installer | Inno Setup 5 or 6 | Installer scripts live in `installer/inno/`. |

## Getting Started

### Prerequisites

- Windows with one or more supported Autodesk Revit versions installed (2024-2027) to run batches.
- Visual Studio 2022 or later with the .NET desktop development workload.
- .NET Framework 4.8 Developer Pack (apps and Revit 2024 add-in).
- .NET 10 SDK — pinned to `10.0.100` by `global.json` (shared libraries and Revit 2025-2027 add-ins).
- MSBuild and NuGet CLI, available from a Visual Studio Developer PowerShell or Command Prompt.
- Dynamo for Revit, only if you want to run Dynamo task scripts. Dynamo versions are tied to specific Revit versions — install the Dynamo build that matches your target Revit version (see [Which Dynamo versions are supported for Revit](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Which-Dynamo-versions-are-supported-for-Revit.html)).
- Microsoft Excel, only if you want to use `.xlsx` model lists.
- Inno Setup 5 or 6, only if you want to build the Windows installer.

For Dynamo workflows, install exactly one Dynamo version per Revit version. Multiple Dynamo installs for the same Revit version can prevent Dynamo Revit modules from loading correctly.

### Install from a Release

Download the latest installer from this fork's [Releases](https://github.com/Pascall-Watson/batch/releases) page and run it:

```powershell
Start-Process "https://github.com/Pascall-Watson/batch/releases"
```

The installer deploys the GUI/CLI to `%LOCALAPPDATA%\RevitBatchProcessor` and the add-ins to `%APPDATA%\Autodesk\Revit\Addins\<year>`, and adds a **Revit Batch Processor (GUI)** shortcut to the Start menu.

The original BVN `v1.12.1` installer remains available from the upstream project for comparison or legacy installation testing:

```powershell
Start-Process "https://github.com/bvn-architecture/RevitBatchProcessor/releases/download/v1.12.1/RevitBatchProcessorSetup_v1.12.1.exe"
```

### Build from Source

```powershell
git clone https://github.com/Pascall-Watson/batch.git
cd batch
nuget restore .\Batch.sln
dotnet restore .\Batch.sln
msbuild .\Batch.sln /p:Configuration=Debug /p:Platform=x64
```

After building, start the GUI directly from the output folder:

```powershell
.\src\apps\Batch.App.Gui\bin\x64\Debug\Batch.App.Gui.exe
```

During a successful build, each add-in project deploys its files to the matching Revit add-ins folder (for example `%APPDATA%\Autodesk\Revit\Addins\2025\BatchRvt\`). To build without touching the Revit add-ins folders:

```powershell
msbuild .\Batch.sln /p:Configuration=Release /p:Platform=x64 /p:EnableAddinDeployment=false
```

## Usage

### Running the GUI

The GUI is the easiest way to configure a batch: pick the files or folder to process, choose the task script, set central-file and workset options, and start the run. Every setting can be exported to a `BatchRvt.Settings.json` file, which the CLI can later load verbatim — this is the recommended way to move from an interactive setup to a scheduled job.

```powershell
.\src\apps\Batch.App.Gui\bin\x64\Debug\Batch.App.Gui.exe
```

### Running from the Command Line

Run a Python task script against a text file list in detach mode:

```powershell
.\src\apps\Batch.App.Cli\bin\x64\Release\Batch.App.Cli.exe `
  --task_script "C:\BatchTasks\ReportModelInfo.py" `
  --file_list "C:\BatchTasks\RevitFileList.txt" `
  --revit_version 2025 `
  --detach `
  --log_folder "C:\BatchTasks\Logs"
```

Or replay a settings file exported from the GUI:

```powershell
.\src\apps\Batch.App.Cli\bin\x64\Release\Batch.App.Cli.exe `
  --settings_file "C:\BatchTasks\BatchRvt.Settings.json" `
  --log_folder "C:\BatchTasks\Logs"
```

When no settings file is given, the CLI operates in batch mode and defaults to opening central files detached from central.

### Revit File Lists

For a text file list, place one fully qualified Revit file path on each line:

```text
P:\15\ProjectABC\MainModel.rvt
P:\16\ProjectXYZ\ModelA.rvt
P:\16\ProjectXYZ\ModelB.rvt
P:\16\ProjectXYZ\ConsultantModel.rvt
```

For BIM 360 / ACC / Forma cloud-hosted models (BIM 360, Autodesk Construction Cloud, and Autodesk Forma are successive names for the same Autodesk cloud service), use the Revit version, project GUID, and model GUID separated by spaces:

```text
2024 75b6464c-ba0f-4529-b049-0de9e473c2d6 0d54b8cc-3837-4df2-8c8e-0a94f4828868
2024 c0dc2fda-fd34-42fe-8bb7-bd9f43841dbf d9f011d6-d52c-4c9f-9d7b-eb8388bd3ed0
```

Cloud model entries accept an optional fourth field for the ACC region code. If omitted, RBP defaults to `US`:

```text
2024 75b6464c-ba0f-4529-b049-0de9e473c2d6 0d54b8cc-3837-4df2-8c8e-0a94f4828868 EU
```

Supported region codes are `US`, `EU`, `AUS`, `GBR`, `DEU`, `CAN`, `IND`, and `JPN`; common aliases such as `EMEA`, `APAC`, and `UK` are normalized automatically (see `src/shared/Batch.Shared.Util/Scripts27/cloud_region_util.py`).

Excel (`.xlsx`) lists read model paths from the first column. The GUI can also generate a file list by scanning a folder tree for `.rvt` and `.rfa` files.

### Python Task Scripts

A task script runs once per Revit file and receives the active document through the `revit_script_util` helper module:

```python
"""Write basic model information to the RBP log."""

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import *

import revit_script_util
from revit_script_util import Output

doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()

Output("Processing: " + revitFilePath)
Output("Model title: " + doc.Title)
```

Task scripts for Revit 2024-2026 run on IronPython 2.7; scripts for Revit 2027 run on IronPython 3.4. Keep syntax compatible with the engine your target Revit version uses.

### Dynamo Task Scripts

Save the Dynamo workspace with Run mode set to `Automatic`, then pass the `.dyn` file as the task script:

```powershell
.\src\apps\Batch.App.Cli\bin\x64\Release\Batch.App.Cli.exe `
  --task_script "C:\BatchTasks\AuditViews.dyn" `
  --file_list "C:\BatchTasks\RevitFileList.xlsx" `
  --revit_version 2024 `
  --detach
```

Dynamo tasks always use a separate Revit session for each Revit file, because Dynamo opens documents in the Revit UI context. The workspace runs against the Dynamo for Revit build installed for the target Revit version — Dynamo versions are tied to specific Revit versions, so the `.dyn` file must be compatible with that pairing (see [Autodesk's Dynamo–Revit version matrix](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Which-Dynamo-versions-are-supported-for-Revit.html)).

### Scheduled and Unattended Runs

Export settings from the GUI, then call the CLI from Windows Task Scheduler or another automation tool:

```powershell
$BatchCli = "$env:LOCALAPPDATA\RevitBatchProcessor\Batch.App.Cli.exe"
$Settings = "C:\BatchTasks\NightlyAudit\BatchRvt.Settings.json"
$Logs     = "C:\BatchTasks\NightlyAudit\Logs"

& $BatchCli --settings_file $Settings --log_folder $Logs
```

This pattern suits nightly health checks, batch upgrades, data extraction, or regression-testing your own Revit add-ins against a model library. Combine it with `--per_file_timeout` and per-file sessions so a single crashing model cannot stall the whole run.

### Loading .NET DLLs from a Task Script

Place your DLL beside the Python task script. RBP adds the task script's folder to the script search path, so the DLL can be loaded directly:

```python
import clr

clr.AddReference("MyUtilities")
from MyNameSpace import SomeClass

SomeClass.DoSomeWork(doc)
```

## Command-Line Reference

RBP exposes a command-line interface rather than an HTTP API.

```text
Batch.App.Cli.exe --settings_file <SETTINGS_FILE_PATH> [--log_folder <LOG_FOLDER_PATH>]
Batch.App.Cli.exe --file_list <REVIT_FILE_LIST_PATH> --task_script <TASK_SCRIPT_FILE_PATH> [options]
```

| Option | Value | Description |
| --- | --- | --- |
| `--settings_file` | Path to a JSON settings file | Loads a processing configuration exported from the GUI. |
| `--file_list` | Path to a `.txt` or `.xlsx` file | Supplies the Revit model list when not using a settings file. |
| `--task_script` | Path to a `.py` or `.dyn` file | Script or Dynamo workspace to run once per model. |
| `--revit_version` | Revit year, e.g. `2025` | Forces all files through a specific Revit version. If omitted, RBP uses the version each file was saved in. |
| `--log_folder` | Folder path | Writes logs to the specified folder. |
| `--detach` | Flag | Opens central files detached from central (default in batch mode). |
| `--create_new_local` | Flag | Creates a new local file for workshared central models. |
| `--worksets` | `open_all` or `close_all` | Controls initial workset opening behavior. |
| `--audit` | Flag | Opens models with the Revit audit option enabled. |
| `--per_file_timeout` | Minutes | Abandons processing of a file that exceeds the timeout and moves on. |
| `--help` | Flag | Prints command-line help. |

## Python Task Script API

The `revit_script_util` module is available to every Python task script:

| Helper | Return type | Description |
| --- | --- | --- |
| `revit_script_util.Output(message)` | `None` | Writes a message to the RBP console and log. |
| `revit_script_util.GetScriptDocument()` | `Autodesk.Revit.DB.Document` | Returns the Revit document being processed. |
| `revit_script_util.GetUIApplication()` | `Autodesk.Revit.UI.UIApplication` | Returns the active Revit UI application object. |
| `revit_script_util.GetRevitFilePath()` | `str` | Returns the full path of the current Revit file. |
| `revit_script_util.GetSessionId()` | `str` | Returns the current RBP session identifier. |

More helpers (cloud model IDs, data-export folders, workset configuration, safe document closing, and more) live in `src/shared/Batch.Shared.Util/Scripts27/revit_script_util.py` and its `Scripts34` counterpart. For additional guidance, see the upstream [Revit Batch Processor FAQ](https://github.com/bvn-architecture/RevitBatchProcessor/wiki/Revit-Batch-Processor-FAQ) and Jan Christel's [sample RBP scripts](https://github.com/jchristel/SampleCodeRevitBatchProcessor/).

## Project Structure

```text
.
|-- .github/workflows/        # Release workflow and the README version-update script.
|-- deployment/revit-addin/   # Add-in deploy/remove batch scripts used by builds.
|-- installer/inno/           # Inno Setup script and compile batch files.
|-- packages/                 # NuGet restore output for the legacy projects.
|-- scripts/                  # msbuild.py helper and Remove-RevitBatchProcessor.ps1 cleanup tool.
|-- src/
|   |-- addins/               # Batch.AddIn.2024 - Batch.AddIn.2027 (one per Revit version).
|   |-- apps/                 # Batch.App.Cli and Batch.App.Gui.
|   |-- integrations/         # Batch.Integration.Dynamo.
|   `-- shared/               # Batch.Shared.Util (incl. Scripts27/Scripts34), Batch.Shared.ScriptHost, Common.
|-- tests/                    # Batch.Shared.Util.Tests (xUnit).
|-- third_party/References/   # Local reference assemblies (Newtonsoft.Json).
|-- Batch.sln                 # Main Visual Studio solution.
|-- Directory.Build.targets   # Shared MSBuild settings.
|-- global.json               # .NET SDK pin (10.0.100).
|-- MinimumRecommendedRules.ruleset
`-- LICENSE.txt               # GNU GPL v3.
```

## Development

Restore, build, and test from a Visual Studio Developer PowerShell:

```powershell
nuget restore .\Batch.sln
dotnet restore .\Batch.sln
msbuild .\Batch.sln /p:Configuration=Debug /p:Platform=x64
dotnet test .\tests\Batch.Shared.Util.Tests\Batch.Shared.Util.Tests.csproj -c Debug
```

A full solution build is the main regression check. You can also run the tests with Visual Studio Test Explorer or `vstest.console.exe`, and run code analysis with the repository ruleset:

```powershell
msbuild .\Batch.sln /p:Configuration=Debug /p:Platform=x64 /p:RunCodeAnalysis=true
```

Most Revit integration behavior requires manual validation because it depends on installed Revit versions, add-in deployment, and real model files. For pull requests that touch Revit orchestration, include the Revit version tested, the model type, the task script type, and whether the run used detach or new-local processing.

## Installer and Packaging

The installer is built with Inno Setup from `installer/inno/RevitBatchProcessor.iss`:

```powershell
.\installer\inno\compile_rbp_setup.bat
```

The installer:

- installs the GUI and CLI to `%LOCALAPPDATA%\RevitBatchProcessor`,
- deploys the add-in files and `.addin` manifests to `%APPDATA%\Autodesk\Revit\Addins\<year>` for 2024-2027,
- creates a Start menu shortcut for the GUI.

To remove every trace of RBP (install folder, add-ins, settings, logs, Start menu group, and the uninstall registry key), run the cleanup script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Remove-RevitBatchProcessor.ps1 -WhatIf
```

## Release Process

Releases are automated by the [`build_msi.yml`](.github/workflows/build_msi.yml) workflow, which triggers when a GitHub release is published:

1. Normalizes the release tag into a version number.
2. Stamps the version into `installer/inno/RevitBatchProcessor.iss` and `src/shared/Common/GlobalAssemblyInfo.cs`.
3. Restores, builds the solution in Release x64, and runs the unit tests.
4. Compiles the Inno Setup installer and uploads it as a release asset.
5. Runs [`update_readme.py`](.github/workflows/update_readme.py) to update the **Current release** version in this README. The script only rewrites the text between the `<!-- RBP-VERSION -->` marker pair and fails the workflow if that marker is missing or ambiguous — it never pattern-matches version numbers elsewhere in the file.
6. Opens a pull request (`github-actions/update-readme` branch) with the version bumps for review.

## Contributing

Contributions to this fork are welcome. The original primary author of the upstream BVN project is no longer able to provide ongoing support, so community-maintained fixes, documentation improvements, and Revit-version updates are especially valuable.

Recommended workflow:

1. Fork the repository and create a focused branch from the default branch.
2. Restore packages and build the solution locally (see [Development](#development)).
3. Make a small, reviewable change, and add or update tests where the change can be tested outside Revit.
4. Open a pull request against [Pascall-Watson/batch](https://github.com/Pascall-Watson/batch) with the problem, solution, and validation steps clearly described.

Coding and review expectations:

- Keep changes scoped to one behavior or Revit-version update at a time.
- Preserve the existing project structure and per-version add-in pattern.
- When adding a new Revit year, update `src/shared/Batch.Shared.Util/RevitVersion.cs`, the add-in projects, the installer script, and the documentation together.
- Prefer clear, imperative commit messages such as `Fix cloud model file-list parsing`.
- Include manual Revit validation notes when the behavior cannot be covered by unit tests.

## Troubleshooting

<details>
<summary>Build fails because NuGet packages or xUnit props are missing.</summary>

Run package restore before building:

```powershell
nuget restore .\Batch.sln
dotnet restore .\Batch.sln
```

If Visual Studio still reports missing package imports, delete stale `bin/` and `obj/` folders for the affected project and restore again.
</details>

<details>
<summary>Build fails because the wrong .NET SDK is used.</summary>

`global.json` pins the .NET 10 SDK (`10.0.100`). Install the matching SDK, or check which SDKs are available with `dotnet --list-sdks`. The Revit 2025-2027 add-ins and the shared libraries cannot build with only the .NET Framework 4.8 tooling installed.
</details>

<details>
<summary>Build fails because Revit API references are missing.</summary>

The add-in projects for Revit 2024-2027 restore API references via NuGet package dependencies (`Nice3point.Revit.Api.*`). Ensure package restore succeeds before building.
</details>

<details>
<summary>Dynamo scripts fail even though they run in Dynamo.</summary>

Make sure the `.dyn` file is saved with Run mode set to `Automatic`. Also confirm there is exactly one Dynamo installation for the target Revit version; multiple Dynamo installs for the same Revit version can prevent Dynamo Revit modules from loading. Dynamo versions are tied to specific Revit versions — check [Autodesk's support matrix](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Which-Dynamo-versions-are-supported-for-Revit.html) if the workspace was authored in a different Dynamo version than the target Revit ships with.
</details>

<details>
<summary>RBP does not dismiss a Revit dialog automatically.</summary>

Automatic dialog handling currently recognizes English-language Revit dialog titles, text, and buttons. Non-English Windows or Revit installations may require manual intervention or additional dialog-handling logic.
</details>

<details>
<summary>Processing stops after a Revit crash.</summary>

Use the option to process each Revit file in a separate Revit session, and set `--per_file_timeout` for CLI runs. That isolates failures so one crashed or hung session does not block the rest of the batch.
</details>

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE.txt). You may use, study, modify, and redistribute the software under the GPL terms, provided derivative distributions preserve the same license obligations. The software is provided without warranty; see the full license text for details.

## Acknowledgements

- Daniel Rumery ([@DanRumery](https://github.com/DanRumery)), original and primary author.
- BVN Architecture, original project sponsor and upstream repository owner.
- Vincent Cadoret ([@vinnividivicci](https://github.com/vinnividivicci)), Ryan Schwartz ([@RyanSchw](https://github.com/RyanSchw)), Dimitar Venkov ([@dimven](https://github.com/dimven)), Nicklas Ostergaard ([@NicklasOestergaard](https://github.com/NicklasOestergaard)), Peter Smith ([@punderscoresmithuk](https://github.com/punderscoresmithuk)), and Maciej Wypych ([@maciejwypych](https://github.com/maciejwypych)) for code contributions and Revit-version upgrades.
- Jan Christel ([@jchristel](https://github.com/jchristel)) for maintaining public [sample RBP Python scripts](https://github.com/jchristel/SampleCodeRevitBatchProcessor/).
- The Autodesk Revit API, Dynamo, IronPython, xUnit, FluentAssertions, Moq, Newtonsoft.Json, and Inno Setup communities.
- The Dynamo and Revit API forums for ongoing community support and troubleshooting knowledge.

## Support

The original author is unable to provide ongoing support for RBP. For fork-specific issues, use the Pascall-Watson repository; for historical context, compare against the upstream BVN project and community resources.

- Repository: [Pascall-Watson/batch](https://github.com/Pascall-Watson/batch)
- Bug reports and feature requests: [GitHub Issues](https://github.com/Pascall-Watson/batch/issues)
- Upstream project: [bvn-architecture/RevitBatchProcessor](https://github.com/bvn-architecture/RevitBatchProcessor)
- Upstream FAQ: [Revit Batch Processor FAQ](https://github.com/bvn-architecture/RevitBatchProcessor/wiki/Revit-Batch-Processor-FAQ)
- Community help: Dynamo forums and Revit API forums

When opening an issue, include the RBP version, Revit version, Windows version, task script type, file-list type, relevant log output, and a minimal reproduction when possible.