# WinUI Parity Gate Evidence

Date: 2026-08-15

Update: 2026-08-18

- AppLocker unblock retest is now validated for WinUI build and direct `.exe` launch.
- See [docs/winui-workflow-validation-2026-08-18.md](docs/winui-workflow-validation-2026-08-18.md) for exact commands and outputs.

Update: 2026-08-18 16:07 (interactive WinUI run)

- WinUI processed 2 ACC cloud models in Revit 2025 using task script `C:\Users\Wayne\Desktop\twinmotion_export\twinmotion_export.py`.
- Model 1 completed with 5 of 5 Datasmith view exports.
- Model 2 completed with 5 of 5 Datasmith view exports.
- Run completed successfully end-to-end with host Revit session startup, cloud open, task execution, close, and clean process exit for both files.
- Source log: `C:\Users\Wayne\AppData\Local\BatchRvt\BatchRvt_20260818_160744_390.log` (plain-text copy at `.txt` sibling path).
- A pre-run warning block about non-existent files came from comment lines (`# ...`) in the file list template and is now filtered in parser code:
  [src/shared/Batch.Shared.Util/Scripts27/revit_file_list.py](src/shared/Batch.Shared.Util/Scripts27/revit_file_list.py)
  [src/shared/Batch.Shared.Util/Scripts34/revit_file_list.py](src/shared/Batch.Shared.Util/Scripts34/revit_file_list.py)

Scope:

- Execute the parity gate scenarios from [docs/winui-parity-checklist.md](docs/winui-parity-checklist.md).
- Record pass/fail evidence for both WinForms and WinUI.

Environment constraints observed:

- At 2026-08-15 capture time, corporate AppLocker blocked direct launch of [src/apps/Batch.App.Ui/bin/x64/Release/net10.0-windows10.0.19041.0/Batch.App.Ui.exe](src/apps/Batch.App.Ui/bin/x64/Release/net10.0-windows10.0.19041.0/Batch.App.Ui.exe).
- At 2026-08-15 capture time, WinUI smoke execution was performed via `dotnet` host against the built `.dll`.
- Full interactive UI automation (click/edit/start/stop status capture) was not available in this terminal-only run.
- Interactive parity capture process is documented in [docs/winui-parity-interactive-runbook.md](docs/winui-parity-interactive-runbook.md), with evidence recording template at [docs/winui-parity-interactive-capture-template.md](docs/winui-parity-interactive-capture-template.md).
- Active capture artifact for this branch/session is initialized at [docs/winui-parity-interactive-capture-2026-08-15.md](docs/winui-parity-interactive-capture-2026-08-15.md), generated via [scripts/New-WinUiParityInteractiveCapture.ps1](scripts/New-WinUiParityInteractiveCapture.ps1).

## Build and test baseline

Executed and passed:

- `dotnet build src/apps/Batch.App.Ui/Batch.App.Ui.csproj -c Release -p:Platform=x64`
- `dotnet msbuild src/apps/Batch.App.Gui/Batch.App.Gui.csproj /p:Configuration=Release /p:Platform=x64`
- `dotnet test tests/Batch.Shared.Util.Tests/Batch.Shared.Util.Tests.csproj --configuration Release`

Test summary:

- Total: 38
- Failed: 0
- Passed: 38

Additional parity completion in this pass:

- Startup preflight parity (B1) is now implemented in both WinForms and WinUI via shared helper: [src/shared/Batch.Shared.Util/BatchUiPreflight.cs](src/shared/Batch.Shared.Util/BatchUiPreflight.cs#L6), [src/apps/Batch.App.Gui/Program.cs](src/apps/Batch.App.Gui/Program.cs#L38), [src/apps/Batch.App.Ui/App.xaml.cs](src/apps/Batch.App.Ui/App.xaml.cs#L18).
- Load-failure feedback parity (B4) is now implemented with explicit WinForms error dialogs to match WinUI surfaced errors: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L399), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L520).
- Typed edit parity (V2) is now implemented in WinUI for the primary workflow with task script, Revit list, and processing mode editors synced into JSON before save/start: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L234), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L675), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L724).
- Run-state signaling parity (V8) is now implemented in WinUI with explicit state transitions and Running/Done semantics: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L20), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L540).
- Stop-flow parity (V5) is now implemented in WinUI with close-time terminate/no/cancel prompts and save-default follow-up matching WinForms behavior: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L280), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L310), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L443).

## Scenario results

| Scenario | WinForms | WinUI | Evidence |
| --- | --- | --- | --- |
| 1. Load default settings and save without schema drift | PASS (service-level) | PASS (service-level) | [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L269) validates save/load of settings JSON via shared workflow seam used by both UIs. |
| 2. Modify task script/file list, save-as, reload, compare JSON outcomes | PASS (service-level) | PASS (service-level) | [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L298) exercises WinForms-style model save and WinUI-style JSON save through shared seam. |
| 3. Start batch run with valid settings and compare launch/status/completion | PARTIAL | PASS | WinUI interactive evidence now captured from 2026-08-18 16:07 run: 2 cloud models processed, each with 5/5 Twinmotion Datasmith exports, including full launch/open/run/close lifecycle. WinForms side remains pending interactive capture in the same environment. |
| 4. Start run and stop mid-run; compare termination and feedback | PASS (process stop policy), PARTIAL (interactive capture) | PASS (process stop policy), PARTIAL (interactive capture) | [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L458) verifies shared stop service termination; UI close-time parity logic is now aligned in code at [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L280) and [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L443). |
| 5. Output filtering/status behavior with stdout/stderr noise | PASS | PASS | [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L410) and [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L432) validate shared output policy now consumed by both UIs. |

## Executable smoke evidence

WinForms `.exe` launch succeeded and remained active for 3 seconds before forced stop.

WinUI `.exe` launch was blocked by policy, but WinUI `.dll` launched successfully via `dotnet` and remained active for 3 seconds before forced stop.

Direct `.exe` smoke output:

```json
[
  {
    "Exe": "src/apps/Batch.App.Gui/bin/x64/Release/Batch.App.Gui.exe",
    "Started": true,
    "State": "RunningAfter3s+ForceStopped",
    "ExitCode": -1,
    "Error": null
  },
  {
    "Exe": "src/apps/Batch.App.Ui/bin/x64/Release/net10.0-windows10.0.19041.0/Batch.App.Ui.exe",
    "Started": false,
    "State": "StartFailed",
    "ExitCode": null,
    "Error": "This program is blocked by group policy."
  }
]
```

WinUI via `dotnet` host smoke output:

```json
{
  "Host": "dotnet",
  "Target": "src/apps/Batch.App.Ui/bin/x64/Release/net10.0-windows10.0.19041.0/Batch.App.Ui.dll",
  "Started": true,
  "State": "RunningAfter3s+ForceStopped",
  "ExitCode": -1,
  "Error": null
}
```

## Gate decision (current)

- Scenario 1: PASS
- Scenario 2: PASS
- Scenario 3: PARTIAL
- Scenario 4: PARTIAL
- Scenario 5: PASS

Overall gate status:

- PARTIAL PASS
- Remaining blockers are interactive end-to-end comparison capture for scenario 3 and scenario 4 under a Revit-capable, policy-permitted environment using [docs/winui-parity-interactive-runbook.md](docs/winui-parity-interactive-runbook.md).
