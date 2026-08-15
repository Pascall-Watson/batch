# WinUI Parity Interactive Runbook

Date: 2026-08-15

Purpose:

- Capture side-by-side interactive parity evidence for scenario 3 and scenario 4 in an environment where both UIs can be executed with Revit-capable inputs.
- Produce a completed evidence artifact using [docs/winui-parity-interactive-capture-template.md](docs/winui-parity-interactive-capture-template.md).

## 0) Bootstrap Capture Artifact

1. Run the bootstrap script to create a timestamped capture document prefilled with environment metadata:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\New-WinUiParityInteractiveCapture.ps1 -OpenInEditor
```

2. Use the generated file under [docs](docs) as the working evidence artifact for this run session.

## 1) Preconditions

1. Revit add-in preflight passes for both apps.
2. Both binaries are built in Release x64:
   - [src/apps/Batch.App.Gui/bin/x64/Release/Batch.App.Gui.exe](src/apps/Batch.App.Gui/bin/x64/Release/Batch.App.Gui.exe)
   - [src/apps/Batch.App.Ui/bin/x64/Release/net10.0-windows10.0.19041.0/Batch.App.Ui.exe](src/apps/Batch.App.Ui/bin/x64/Release/net10.0-windows10.0.19041.0/Batch.App.Ui.exe)
3. One shared settings input is available for both UI runs.
4. Revit-host execution is permitted in the environment.
5. If AppLocker blocks the WinUI executable, document the exact message and stop the runbook.

## 2) Shared Test Input

1. Record one canonical settings file path.
2. Record one canonical log folder path.
3. Record one canonical model list path.
4. Record one canonical task script path.
5. Do not change these between WinForms and WinUI during a scenario pair.

## 3) Scenario 3: Start Run And Compare Launch/Status/Completion

1. Open WinForms and load the canonical settings file.
2. Start the run.
3. Capture launch result and first visible running indicator.
4. Wait for run completion or a deterministic terminal state.
5. Capture completion indicator and final status text.
6. Repeat steps 1-5 in WinUI using the same settings.
7. Compare parity checkpoints:
   - Launch success/failure shape is equivalent.
   - Running state indicator transitions are equivalent.
   - Completion indicator and end-state messaging are equivalent.
8. Mark PASS or PARTIAL in the template for each checkpoint.

## 4) Scenario 4: Start Run, Stop Mid-Run, Compare Termination And Feedback

1. Open WinForms with the canonical settings and start a run.
2. Trigger stop during active processing.
3. Capture stop feedback including close-time prompts if close is used.
4. Capture final process state after stop request.
5. Repeat steps 1-4 in WinUI using the same settings.
6. Compare parity checkpoints:
   - Stop action is available while running.
   - Prompt flow during close-time stop is equivalent.
   - Final process termination outcome is equivalent.
   - Operator-facing feedback is equivalent in meaning.
7. Mark PASS or PARTIAL in the template for each checkpoint.

## 5) Evidence Recording Rules

1. Use one filled copy of [docs/winui-parity-interactive-capture-template.md](docs/winui-parity-interactive-capture-template.md) per run session.
2. Include exact observed status text when practical.
3. Include timestamps for each major transition.
4. Include all blockers verbatim, especially policy or host restrictions.
5. Do not normalize or reinterpret failed behavior; record it exactly.

## 6) Exit Criteria For P2 Closure

1. Scenario 3 marked PASS for both UIs with matching parity checkpoints.
2. Scenario 4 marked PASS for both UIs with matching parity checkpoints.
3. Completed template linked from [docs/winui-parity-gate-evidence.md](docs/winui-parity-gate-evidence.md).
4. Remaining blockers section in [docs/winui-parity-gate-evidence.md](docs/winui-parity-gate-evidence.md) is removed or updated to reflect completion.
