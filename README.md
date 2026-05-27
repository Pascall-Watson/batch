# Revit Batch Processor (RBP)

[![Build](https://img.shields.io/badge/build-manual-lightgrey)](#testing)
[![Release](https://img.shields.io/github/v/release/Pascall-Watson/batch?include_prereleases&label=release)](https://github.com/Pascall-Watson/batch/releases)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE.txt)
[![Language](https://img.shields.io/github/languages/top/Pascall-Watson/batch)](https://github.com/Pascall-Watson/batch/search?l=c%23)
[![Downloads](https://img.shields.io/github/downloads/Pascall-Watson/batch/total)](https://github.com/Pascall-Watson/batch/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)](#getting-started)
[![Revit](https://img.shields.io/badge/Revit-2015--2027-0696D7)](#tech-stack)

Pascall-Watson fork of Revit Batch Processor for large-scale Revit automation with custom Python or Dynamo task scripts.

This repository is the Pascall-Watson fork of [BVN Architecture's Revit Batch Processor](https://github.com/bvn-architecture/RevitBatchProcessor), originally authored by Daniel Rumery. Revit Batch Processor helps BIM, computational design, and Revit API teams run repeatable automation across many `.rvt` and `.rfa` files without manually opening each model. Use the Windows GUI for interactive setup, or run the command-line tool from scheduled jobs and build pipelines. This fork preserves RBP's practical batch orchestration model: version-aware Revit launching, central-file options, per-version add-ins, script templates, logging, and unattended processing.

> Fork repository: [Pascall-Watson/batch](https://github.com/Pascall-Watson/batch). Upstream repository: [bvn-architecture/RevitBatchProcessor](https://github.com/bvn-architecture/RevitBatchProcessor). The shared codebase currently reports `v1.12.1` beta, and source in this fork includes add-in projects for Revit 2015 through 2027.

<a id="table-of-contents"></a>
## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Project](#running-the-project)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Testing](#testing)
- [Deployment](#deployment)
- [FAQ / Troubleshooting](#faq--troubleshooting)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Contact & Support](#contact--support)

<a id="features"></a>
## Features

- Batch Revit automation - process many project and family files with one repeatable workflow.
- Python and Dynamo task scripts - run custom Revit API logic or Dynamo workspaces against each file.
- Version-aware processing - select a fixed Revit version or let RBP match the version each file was saved in.
- Central file workflows - detach from central, create new local files, audit files, and control workset opening behavior.
- GUI and CLI entry points - configure jobs visually or run unattended from scripts and Windows Task Scheduler.
- Automatic dialog handling - capture and respond to common English-language Revit dialogs during processing.
- Pre- and post-processing hooks - prepare inputs and clean up outputs around the main task script.
- File-list generation - scan folders for `.rvt` and `.rfa` files and produce a text list compatible with RBP.
- BIM 360 / cloud model list support - process cloud models using Revit version, project GUID, and model GUID entries.
- Installer and add-in deployment scripts - build and deploy the per-version Revit add-ins from source.

<a id="demo"></a>
## Demo

![Revit Batch Processor GUI](BatchRvt_Screenshot.png)

<!-- TODO: Add demo assets -->

Use this section for a short GIF, terminal recording, or screenshots that show a complete batch run from setup through logs. RBP is a Windows desktop tool, so there is no hosted live demo for the application itself.

<a id="tech-stack"></a>
## Tech Stack

| Area | Technology | Notes |
| --- | --- | --- |
| Primary language | C# | Legacy project files plus newer SDK-style project support for the Revit 2027 add-in. |
| Desktop framework | Windows Forms | Used by the BatchRvtGUI application. |
| Runtime target | .NET Framework 4.8 | Main GUI, CLI, utility, script host, and Revit 2015-2026 add-in projects. |
| Revit 2027 add-in | `net10.0-windows` | Uses `Nice3point.Revit.Api.RevitAPI` and `Nice3point.Revit.Api.RevitAPIUI` packages. |
| Revit integration | Autodesk Revit API / RevitAPIUI | Per-version add-in projects for Revit 2015-2027. |
| Script execution | IronPython 2.7.x | Runs Python task scripts with access to Revit API objects. |
| Visual scripting | Dynamo 1.3+ | Runs Dynamo `.dyn` workspaces when Dynamo is installed for the target Revit version. |
| Data input | `.txt`, `.xlsx` | Text files contain one model path per line; Excel files use the first column. |
| Serialization | Newtonsoft.Json | Used for settings and data exchange. |
| Testing | xUnit 2.x | `BatchRvtUtil.Tests` contains unit tests for utility behavior. |
| Test helpers | FluentAssertions, Moq, Castle.Core | Used across test and project references. |
| Installer | Inno Setup 5 or 6 | Setup scripts live in `Setup/`. |

<a id="getting-started"></a>
## Getting Started

<a id="prerequisites"></a>
### Prerequisites

- Windows with access to a supported Autodesk Revit installation.
- Visual Studio 2017 or later with the .NET desktop development workload.
- .NET Framework 4.8 Developer Pack for the main solution projects.
- MSBuild available from a Visual Studio Developer PowerShell or Developer Command Prompt.
- NuGet CLI or Visual Studio package restore.
- Revit API references for the Revit versions you build locally. Legacy add-in projects reference assemblies under `References/Revit/<year>/`.
- Dynamo 1.3 or later if you want to run Dynamo task scripts.
- Microsoft Office / Excel if you want to use `.xlsx` model lists.
- Inno Setup 5 or 6 if you want to build the Windows installer.

For Dynamo workflows, install exactly one Dynamo version per Revit version. Multiple Dynamo installs for the same Revit version can prevent Dynamo Revit modules from loading correctly.

<a id="installation"></a>
### Installation

Install from this fork's packaged releases when an installer is available:

```powershell
Start-Process "https://github.com/Pascall-Watson/batch/releases"
```

The original BVN `v1.12.1` beta installer remains available from the upstream project for comparison or legacy installation testing:

```powershell
Start-Process "https://github.com/bvn-architecture/RevitBatchProcessor/releases/download/v1.12.1/RevitBatchProcessorSetup_v1.12.1.exe"
```

Build from source when you want to develop, debug, or package the project yourself:

```powershell
git clone https://github.com/Pascall-Watson/batch.git
cd batch
nuget restore .\RevitBatchProcessor.sln
msbuild .\RevitBatchProcessor.sln /p:Configuration=Debug /p:Platform=x64
```

You can also use the repository build script from the `scripts/` folder:

```powershell
.\scripts\build_BatchRvtGUI.Debug.bat
```

During a successful build, per-version add-in projects deploy their add-in files to the matching Revit add-ins folder, for example `%APPDATA%\Autodesk\Revit\Addins\2025\BatchRvt\`.

<a id="configuration"></a>
### Configuration

RBP does not require a `.env` file. Most runtime configuration is created in the GUI and can be exported as a settings JSON file for later CLI runs.

Use this optional PowerShell template to keep command-line paths readable while preparing a job:

```powershell
$TaskScript = "C:\BatchTasks\HealthCheck.py"
$FileList = "C:\BatchTasks\RevitFileList.txt"
$LogFolder = "C:\BatchTasks\Logs"
$RevitVersion = "2025"
```

For a text file list, place one fully qualified Revit file path on each line:

```text
P:\15\ProjectABC\MainModel.rvt
P:\16\ProjectXYZ\ModelA.rvt
P:\16\ProjectXYZ\ModelB.rvt
P:\16\ProjectXYZ\ConsultantModel.rvt
```

For BIM 360 / cloud-hosted models, use the Revit version, project GUID, and model GUID separated by spaces:

```text
2020 75b6464c-ba0f-4529-b049-0de9e473c2d6 0d54b8cc-3837-4df2-8c8e-0a94f4828868
2020 c0dc2fda-fd34-42fe-8bb7-bd9f43841dbf d9f011d6-d52c-4c9f-9d7b-eb8388bd3ed0
```

<!-- TODO: Add a checked-in sample BatchRvt.Settings.json once the supported settings schema is documented. -->

<a id="running-the-project"></a>
### Running the Project

Start the debug GUI build:

```powershell
.\scripts\start_BatchRvtGUI.Debug.bat
```

Show CLI help after building:

```powershell
.\BatchRvt\bin\x64\Debug\BatchRvt.exe --help
```

Build a release configuration:

```powershell
msbuild .\RevitBatchProcessor.sln /p:Configuration=Release /p:Platform=x64
```

Run the command-line processor with an exported settings file:

```powershell
.\BatchRvt\bin\x64\Release\BatchRvt.exe --settings_file "C:\BatchTasks\BatchRvt.Settings.json" --log_folder "C:\BatchTasks\Logs"
```

<a id="usage"></a>
## Usage

### Use case 1: Run a basic Python task script

Create a Python script that receives the active Revit document from `revit_script_util` and writes output to the RBP log:

```python
"""Write basic model information to the RBP log."""

import clr
import System

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

Run it against a text file list in detach mode:

```powershell
.\BatchRvt\bin\x64\Release\BatchRvt.exe `
  --task_script "C:\BatchTasks\ReportModelInfo.py" `
  --file_list "C:\BatchTasks\RevitFileList.txt" `
  --revit_version 2025 `
  --detach `
  --log_folder "C:\BatchTasks\Logs"
```

### Use case 2: Run a Dynamo workspace for each model

Save the Dynamo workspace with Run mode set to `Automatic`, then pass the `.dyn` file as the task script:

```powershell
.\BatchRvt\bin\x64\Release\BatchRvt.exe `
  --task_script "C:\BatchTasks\AuditViews.dyn" `
  --file_list "C:\BatchTasks\RevitFileList.xlsx" `
  --revit_version 2024 `
  --detach
```

Dynamo tasks always use a separate Revit session for each Revit file because Dynamo opens documents in the Revit UI context.

### Use case 3: Schedule unattended processing

Export settings from the GUI, then call the CLI from Windows Task Scheduler or another automation tool:

```powershell
$BatchRvt = "$env:LOCALAPPDATA\RevitBatchProcessor\BatchRvt.exe"
$Settings = "C:\BatchTasks\NightlyAudit\BatchRvt.Settings.json"
$Logs = "C:\BatchTasks\NightlyAudit\Logs"

& $BatchRvt --settings_file $Settings --log_folder $Logs
```

This pattern is useful for nightly health checks, batch upgrades, data extraction, or regression testing your own Revit API add-ins against a model library.

### Advanced: Execute code from a C# DLL in a Python task

Place your DLL beside the Python task script. RBP adds the task script folder to the script search path, so the DLL can be loaded directly:

```python
import clr

clr.AddReference("MyUtilities")
from MyNameSpace import SomeClass

SomeClass.DoSomeWork(doc)
```

<a id="api-reference"></a>
## API Reference

RBP exposes a command-line interface rather than an HTTP API.

### Command-line syntax

```powershell
BatchRvt.exe --settings_file <SETTINGS_FILE_PATH> [--log_folder <LOG_FOLDER_PATH>]
BatchRvt.exe --file_list <REVIT_FILE_LIST_PATH> --task_script <TASK_SCRIPT_FILE_PATH> [options]
```

### CLI options

| Option | Value | Description |
| --- | --- | --- |
| `--settings_file` | Path to JSON settings file | Loads a processing configuration exported from the GUI. |
| `--file_list` | Path to `.txt` or `.xlsx` file | Supplies the Revit model list when not using a settings file. |
| `--task_script` | Path to `.py` or `.dyn` file | Script or Dynamo workspace to run once per model. |
| `--revit_version` | Revit year, for example `2025` | Forces all files through a specific Revit version. If omitted, RBP attempts to use the version each file was saved in. |
| `--log_folder` | Folder path | Writes logs to the specified folder. |
| `--detach` | Flag | Opens central files detached from central. |
| `--create_new_local` | Flag | Creates a new local file for workshared central models. |
| `--worksets` | `open_all` or `close_all` | Controls initial workset opening behavior. |
| `--audit` | Flag | Opens models with Revit audit enabled. |
| `--help` | Flag | Prints command-line help. |

### Python task script helpers

| Helper | Return type | Description |
| --- | --- | --- |
| `revit_script_util.GetSessionId()` | `str` | Returns the current RBP session identifier. |
| `revit_script_util.GetUIApplication()` | `Autodesk.Revit.UI.UIApplication` | Returns the active Revit UI application object. |
| `revit_script_util.GetScriptDocument()` | `Autodesk.Revit.DB.Document` | Returns the Revit document being processed. |
| `revit_script_util.GetRevitFilePath()` | `str` | Returns the full path of the current Revit file. |
| `revit_script_util.Output(message)` | `None` | Writes a message to the RBP console and log. |

See this fork's [docs](docs/) and the upstream [Revit Batch Processor FAQ](https://github.com/bvn-architecture/RevitBatchProcessor/wiki/Revit-Batch-Processor-FAQ) for additional guidance.

<a id="project-structure"></a>
## Project Structure

```text
.
|-- AddinDeployment/          # Batch files that copy/remove Revit add-in files.
|-- BatchRevitDynamo/         # Dynamo execution integration.
|-- BatchRvt/                 # Command-line batch processor executable.
|-- BatchRvtAddin2015/        # Revit 2015 add-in project.
|-- BatchRvtAddin20xx/        # Additional per-version Revit add-in projects through 2027.
|-- BatchRvtGUI/              # Windows Forms GUI application.
|-- BatchRvtScriptHost/       # Script host invoked by Revit add-ins.
|-- BatchRvtUtil/             # Shared utilities, script templates, and Revit orchestration code.
|-- BatchRvtUtil.Tests/       # xUnit tests for utility code.
|-- Common/                   # Shared assembly metadata.
|-- References/               # Local third-party and Revit API reference assemblies.
|-- Setup/                    # Inno Setup installer scripts.
|-- docs/                     # Additional project documentation.
|-- packages/                 # NuGet package restore output for legacy projects.
|-- scripts/                  # Build, clean, start, and MSBuild helper scripts.
|-- Directory.Build.targets   # Shared MSBuild settings.
|-- RevitBatchProcessor.sln   # Main Visual Studio solution.
|-- LICENSE.txt               # GNU GPL v3 license text.
`-- README.md                 # Project overview and contributor guide.
```

<a id="roadmap"></a>
## Roadmap

- [x] Revit 2015-2026 add-in support.
- [x] GUI-driven batch setup and settings export.
- [x] Command-line processing for scheduled and unattended runs.
- [x] Python and Dynamo task script execution.
- [x] Central file options for detach, new local, audit, and worksets.
- [x] Source-level Revit 2027 add-in project.
- [ ] Validate and publish the next packaged installer release.
- [ ] Expand automated test coverage around settings, file-list parsing, and CLI behavior.
- [ ] Document a stable sample `BatchRvt.Settings.json` schema.
- [ ] Improve localized dialog handling beyond English-language Revit dialogs.
- [ ] Add contributor onboarding files such as `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`.

Track proposed work and bugs for this fork in [GitHub Issues](https://github.com/Pascall-Watson/batch/issues).

<a id="contributing"></a>
## Contributing

Contributions to this fork are welcome. The original primary author of the upstream BVN project is no longer able to provide ongoing support, so community-maintained fixes, documentation improvements, and Revit-version updates are especially valuable.

Recommended workflow:

1. Fork the repository.
2. Create a focused branch from the default branch.
3. Restore packages and build the solution locally.
4. Make a small, reviewable change.
5. Add or update tests where the change can be tested outside Revit.
6. Run the relevant build and test commands from [Testing](#testing).
7. Open a pull request against [Pascall-Watson/batch](https://github.com/Pascall-Watson/batch) with the problem, solution, and validation steps clearly described.

```powershell
git checkout -b fix/describe-the-problem
nuget restore .\RevitBatchProcessor.sln
msbuild .\RevitBatchProcessor.sln /p:Configuration=Debug /p:Platform=x64
```

Coding and review expectations:

- Keep changes scoped to one behavior or Revit-version update at a time.
- Preserve existing project structure and per-version add-in patterns.
- Update `BatchRvtUtil/RevitVersion.cs`, add-in projects, installer scripts, and documentation together when adding a new Revit year.
- Prefer clear, imperative commit messages such as `Fix cloud model file-list parsing`.
- Include manual Revit validation notes when the behavior cannot be covered by unit tests.
- Look for issues labeled `good first issue`, `help wanted`, or similar newcomer-friendly labels.

<!-- TODO: Add CONTRIBUTING.md and CODE_OF_CONDUCT.md if the project wants dedicated contributor governance documents. -->

<a id="testing"></a>
## Testing

Restore dependencies and build the test project:

```powershell
nuget restore .\RevitBatchProcessor.sln
msbuild .\BatchRvtUtil.Tests\BatchRvtUtil.Tests.csproj /p:Configuration=Debug /p:Platform=AnyCPU
```

Run unit tests with Visual Studio Test Explorer, or from a Developer PowerShell with `vstest.console.exe` available:

```powershell
vstest.console.exe .\BatchRvtUtil.Tests\bin\Debug\BatchRvtUtil.Tests.dll
```

Run a solution build as the main regression check:

```powershell
msbuild .\RevitBatchProcessor.sln /p:Configuration=Debug /p:Platform=x64
```

Run code analysis with the repository ruleset when available in your Visual Studio installation:

```powershell
msbuild .\RevitBatchProcessor.sln /p:Configuration=Debug /p:Platform=x64 /p:RunCodeAnalysis=true
```

Most Revit integration behavior requires manual validation because it depends on installed Revit versions, Revit API assemblies, add-in deployment, and real model files. For pull requests that touch Revit orchestration, include the Revit version tested, the model type, the task script type, and whether the run used detach or new-local processing.

<a id="deployment"></a>
## Deployment

RBP deploys as a Windows desktop application plus per-version Revit add-ins.

Builds deploy add-ins automatically through post-build scripts into the matching Revit add-ins folder:

```text
%APPDATA%\Autodesk\Revit\Addins\<year>\BatchRvt\
```

Build the installer with Inno Setup 5 or 6 installed:

```powershell
.\Setup\compile_rbp_setup.bat
```

Installer definitions live in `Setup/RevitBatchProcessor.iss` and `Setup/RevitBatchProcessor_BVN.iss`. RBP is not a web service and does not target Docker, Vercel, Heroku, or cloud deployment platforms.

<a id="faq--troubleshooting"></a>
## FAQ / Troubleshooting

<details>
<summary>Build fails because NuGet packages or xUnit props are missing.</summary>

Run package restore before building:

```powershell
nuget restore .\RevitBatchProcessor.sln
```

If Visual Studio still reports missing package imports, delete stale `bin/` and `obj/` folders for the affected project and restore again.
</details>

<details>
<summary>Build fails because Revit API references are missing.</summary>

Legacy add-in projects reference local assemblies under `References/Revit/<year>/`. Install the matching Revit version or provide the required `RevitAPI.dll` and `RevitAPIUI.dll` reference assemblies for the years you want to build.
</details>

<details>
<summary>Dynamo scripts fail even though they run in Dynamo.</summary>

Make sure the `.dyn` file is saved with Run mode set to `Automatic`. Also confirm there is exactly one Dynamo installation for the target Revit version; multiple Dynamo installs for the same Revit version can prevent Dynamo Revit modules from loading.
</details>

<details>
<summary>RBP does not dismiss a Revit dialog automatically.</summary>

Automatic dialog handling currently recognizes English-language Revit dialog titles, text, and buttons. Non-English Windows or Revit installations may require manual intervention or additional dialog-handling logic.
</details>

<details>
<summary>Processing stops after a Revit crash.</summary>

Use the option to process each Revit file in a separate Revit session. That mode isolates failures so one crashed session is less likely to block the rest of the batch.
</details>

<a id="license"></a>
## License

This project is licensed under the [GNU General Public License v3.0](LICENSE.txt). You may use, study, modify, and redistribute the software under the GPL terms, provided derivative distributions preserve the same license obligations. The software is provided without warranty; see the full license text for details.

<a id="acknowledgements"></a>
## Acknowledgements

- Daniel Rumery ([@DanRumery](https://github.com/DanRumery)), original and primary author.
- BVN Architecture, original project sponsor and upstream repository owner.
- Pascall-Watson, maintainers of this fork.
- Vincent Cadoret ([@vinnividivicci](https://github.com/vinnividivicci)), Ryan Schwartz ([@RyanSchw](https://github.com/RyanSchw)), Dimitar Venkov ([@dimven](https://github.com/dimven)), Nicklas Ostergaard ([@NicklasOestergaard](https://github.com/NicklasOestergaard)), Peter Smith ([@punderscoresmithuk](https://github.com/punderscoresmithuk)), and Maciej Wypych ([@maciejwypych](https://github.com/maciejwypych)) for code contributions and Revit-version upgrades.
- Jan Christel ([@jchristel](https://github.com/jchristel)) for maintaining public [sample RBP Python scripts](https://github.com/jchristel/SampleCodeRevitBatchProcessor/).
- Autodesk Revit API, Dynamo, IronPython, xUnit, FluentAssertions, Moq, Newtonsoft.Json, and Inno Setup communities.
- The Dynamo and Revit API forums for ongoing community support and troubleshooting knowledge.

<a id="contact--support"></a>
## Contact & Support

<!-- TODO: Confirm current maintainers and preferred support channels. -->

The original author is unable to provide ongoing support for RBP. For fork-specific issues, use the Pascall-Watson repository; for historical context, compare against the upstream BVN project and community resources.

- Repository: [Pascall-Watson/batch](https://github.com/Pascall-Watson/batch)
- Bug reports and feature requests: [GitHub Issues](https://github.com/Pascall-Watson/batch/issues)
- Upstream project: [bvn-architecture/RevitBatchProcessor](https://github.com/bvn-architecture/RevitBatchProcessor)
- Upstream FAQ: [Revit Batch Processor FAQ](https://github.com/bvn-architecture/RevitBatchProcessor/wiki/Revit-Batch-Processor-FAQ)
- Community help: Dynamo forums and Revit API forums

When opening an issue, include the RBP version, Revit version, Windows version, task script type, file-list type, relevant log output, and a minimal reproduction when possible.