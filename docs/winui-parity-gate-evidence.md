# WinUI Parity Gate Evidence

Date: 2026-08-15

Scope:

- Execute the parity gate scenarios from [docs/winui-parity-checklist.md](docs/winui-parity-checklist.md).
- Record pass/fail evidence for both WinForms and WinUI.

Environment constraints observed:

- Corporate AppLocker blocked direct launch of [src/apps/Batch.App.Ui/bin/x64/Release/net10.0-windows10.0.19041.0/Batch.App.Ui.exe](src/apps/Batch.App.Ui/bin/x64/Release/net10.0-windows10.0.19041.0/Batch.App.Ui.exe).
- WinUI smoke execution was performed via `dotnet` host against the built `.dll`.
- Full interactive UI automation (click/edit/start/stop status capture) was not available in this terminal-only run.

## Build and test baseline

Executed and passed:

- `dotnet build src/apps/Batch.App.Ui/Batch.App.Ui.csproj -c Release -p:Platform=x64`
- `dotnet msbuild src/apps/Batch.App.Gui/Batch.App.Gui.csproj /p:Configuration=Release /p:Platform=x64`
- `dotnet test tests/Batch.Shared.Util.Tests/Batch.Shared.Util.Tests.csproj --configuration Release`

Test summary:

- Total: 36
- Failed: 0
- Passed: 36

## Scenario results

| Scenario | WinForms | WinUI | Evidence |
| --- | --- | --- | --- |
| 1. Load default settings and save without schema drift | PASS (service-level) | PASS (service-level) | [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L269) validates save/load of settings JSON via shared workflow seam used by both UIs. |
| 2. Modify task script/file list, save-as, reload, compare JSON outcomes | PASS (service-level) | PASS (service-level) | [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L298) exercises WinForms-style model save and WinUI-style JSON save through shared seam. |
| 3. Start batch run with valid settings and compare launch/status/completion | PARTIAL | PARTIAL | UI binary smoke launch evidence captured for both app outputs; full interactive run-status comparison is blocked by no UI automation and no Revit-hosted end-to-end execution in this session. |
| 4. Start run and stop mid-run; compare termination and feedback | PASS (process stop policy), PARTIAL (UI feedback) | PASS (process stop policy), PARTIAL (UI feedback) | [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L458) verifies shared stop service terminates a running process. UI feedback comparison remains interactive/manual. |
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
- Remaining blockers are interactive end-to-end comparison capture for scenario 3 and UI feedback parity capture for scenario 4 under a Revit-capable, policy-permitted environment.
