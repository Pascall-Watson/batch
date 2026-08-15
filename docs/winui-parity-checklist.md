# WinUI Parity Checklist (First Pass)

Date: 2026-08-15

Primary gate for this phase:

- WinUI can run the primary batch workflow with no regression compared to WinForms.

Status legend:

- Implemented: WinUI behavior exists and is materially aligned with WinForms for this item.
- Partial: WinUI behavior exists, but parity gaps or edge-case differences remain.
- Not started: WinUI behavior is missing or diverges enough that parity is not met.

## 1) Baseline freeze and parity checklist

| ID | Parity item | Current WinUI status | Evidence | Gap to close |
| --- | --- | --- | --- | --- |
| B1 | Startup preflight warns when no supported Revit add-in is installed | Implemented | Shared preflight helper added in [src/shared/Batch.Shared.Util/BatchUiPreflight.cs](src/shared/Batch.Shared.Util/BatchUiPreflight.cs#L6) and used by both launch paths: [src/apps/Batch.App.Gui/Program.cs](src/apps/Batch.App.Gui/Program.cs#L38), [src/apps/Batch.App.Ui/App.xaml.cs](src/apps/Batch.App.Ui/App.xaml.cs#L18). | Keep helper as the single source for launch preflight messaging. |
| B2 | Default settings path auto-load on startup | Implemented | WinForms loads at form startup: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L388). WinUI loads on window construction: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L50). Both rely on shared default path API: [src/shared/Batch.Shared.Util/BatchRvtSettings.cs](src/shared/Batch.Shared.Util/BatchRvtSettings.cs#L236). | Keep behavior; include in parity test scenarios. |
| B3 | Alternate settings file selection and explicit load | Implemented | WinForms import flow: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L915). WinUI browse + load flow: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L259), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L289). | Keep behavior; verify with same sample settings file. |
| B4 | Load-failure feedback is explicit and actionable | Partial | WinForms has TODO after initial load failure (no explicit surfaced error): [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L390). WinUI emits status and output errors: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L474), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L484). | Decide canonical behavior, then align both UIs (or document intentional improvement). |

## 2) Thin application-service contract for UI actions

| ID | Contract item | Current WinUI status | Evidence | Gap to close |
| --- | --- | --- | --- | --- |
| C1 | Extract settings workflow service (load/save/save-as/summary) from window code-behind | Implemented | Shared seam added in [src/shared/Batch.Shared.Util/BatchSettingsWorkflowService.cs](src/shared/Batch.Shared.Util/BatchSettingsWorkflowService.cs#L6) and consumed by WinUI/WinForms: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L21), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L449), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L75), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L401). | Keep extending this seam if additional settings workflows are added. |
| C2 | Extract run-control service (start/stop/process lifecycle) from window code-behind | Implemented | Shared seam added in [src/shared/Batch.Shared.Util/BatchRunServices.cs](src/shared/Batch.Shared.Util/BatchRunServices.cs#L107) and consumed by WinUI/WinForms: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L24), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L350), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L78), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L545). | Add explicit lifecycle event abstraction only if needed for richer UI state machines. |
| C3 | Extract output/status policy service (stdout/stderr filters, status transitions) | Implemented | Shared output policy seam added in [src/shared/Batch.Shared.Util/BatchRunServices.cs](src/shared/Batch.Shared.Util/BatchRunServices.cs#L67) and used by both UIs: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L386), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L394), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L587), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L597). | Status text policy can be similarly centralized in a future pass if needed. |
| C4 | Launcher behavior uses shared CLI-first fallback path | Implemented | WinUI calls shared launcher: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L342). Shared resolver prefers CLI then legacy exe: [src/shared/Batch.Shared.Util/BatchRvt.cs](src/shared/Batch.Shared.Util/BatchRvt.cs#L142), [src/shared/Batch.Shared.Util/BatchRvt.cs](src/shared/Batch.Shared.Util/BatchRvt.cs#L149). | Keep behavior; ensure both app outputs package launcher files identically. |

## 3) First vertical slice in WinUI (load/edit-save/start-stop/output)

| ID | Vertical-slice item | Current WinUI status | Evidence | Gap to close |
| --- | --- | --- | --- | --- |
| V1 | Load settings (default + selected file) | Implemented | WinUI load path and UI actions: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L289), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L454). | Add scenario validation against WinForms baseline outputs. |
| V2 | Edit settings content before save | Partial | WinUI provides raw JSON editor and summary labels: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L204), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L531). WinForms has broad typed settings controls for batch workflows: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L98), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L277). | For parity gate, either implement minimum typed controls for primary workflow or define JSON editing as accepted interim UX with validation criteria. |
| V3 | Save settings and save-as/export | Implemented | WinUI save and save-as: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L297), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L303), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L493). WinForms save/import/export: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L420), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L926). | Add parity scenarios for roundtrip save/load equivalence. |
| V4 | Start run with equivalent pre-run validation | Implemented | Shared pre-run validator seam added in [src/shared/Batch.Shared.Util/BatchRunServices.cs](src/shared/Batch.Shared.Util/BatchRunServices.cs#L13) and applied in WinUI/WinForms before launch: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L337), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L513), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L522). | Keep validating any new settings dimensions through the same service. |
| V5 | Stop run behavior during active processing | Implemented | WinUI now mirrors WinForms close-time stop flow with terminate/no/cancel decision and save-default follow-up while retaining explicit Stop action: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L280), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L310), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L471). WinForms baseline remains in [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L443). | Capture one interactive side-by-side run to document identical operator feedback during mid-run close. |
| V6 | Stream output with equivalent stdout filtering behavior | Implemented | Shared output policy now suppresses non-BatchRvt stdout lines and both UIs consume it: [src/shared/Batch.Shared.Util/BatchRunServices.cs](src/shared/Batch.Shared.Util/BatchRunServices.cs#L67), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L386), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L587). | Keep policy centralized so future tweaks apply to both UIs simultaneously. |
| V7 | Stream output with equivalent stderr filtering/error toggles | Implemented | WinForms filters log4cplus and gates errors on setting: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L614). WinUI mirrors this behavior: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L394), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L397). | Keep behavior; include toggle-on/toggle-off tests in parity runbook. |
| V8 | Equivalent run-status signaling (running/exited/failed) | Implemented | WinUI now uses explicit run-state transitions with legacy-equivalent Running/Done start-button semantics and matching status updates: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L20), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L381), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L412), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L540). WinForms baseline remains in [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L573) and [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L621). | Keep future run-state text and enablement changes synchronized across both UIs. |

## 4) Parity validation execution (both UIs, same scenarios)

| ID | Validation item | Current WinUI status | Evidence | Gap to close |
| --- | --- | --- | --- | --- |
| P1 | Scenario matrix exists for side-by-side WinForms vs WinUI runs | Implemented | Scenario matrix is captured in this checklist and executed evidence is logged in [docs/winui-parity-gate-evidence.md](docs/winui-parity-gate-evidence.md). | Keep extending scenarios as new parity-sensitive behavior is introduced. |
| P2 | Primary workflow gate executed and recorded | Partial | Execution evidence captured in [docs/winui-parity-gate-evidence.md](docs/winui-parity-gate-evidence.md), including passes for shared workflow and filtering scenarios plus noted environment constraints. | Complete full interactive end-to-end run comparisons once UI automation/Revit-host execution is available. |
| P3 | Automated tests cover WinUI parity-critical behavior | Implemented | Added parity tests in [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L298), [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L351), [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L410), [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L458). | Add UI automation tests later if policy allows. |

## 5) Cutover and fallback

| ID | Cutover item | Current WinUI status | Evidence | Gap to close |
| --- | --- | --- | --- | --- |
| F1 | WinForms remains shipping fallback until parity proof | Implemented | Installer packages WinForms output and Start menu shortcut: [installer/inno/RevitBatchProcessor.iss](installer/inno/RevitBatchProcessor.iss#L21), [installer/inno/RevitBatchProcessor.iss](installer/inno/RevitBatchProcessor.iss#L31). CI also verifies WinForms release output path: [.github/workflows/build_msi.yml](.github/workflows/build_msi.yml#L100). | Keep in place until parity gate passes. |
| F2 | WinUI made default only after parity evidence | Not started | No installer/CI default path points to WinUI yet (manual review). | After parity pass, stage a separate cutover PR for installer shortcut, packaging, and docs updates. |

## Suggested first gate scenarios (next execution pass)

1. Load default settings file, verify primary fields are represented, and save without introducing schema drift.
2. Modify task script and file list values, save-as to a new file, reload in both UIs, compare resulting JSON.
3. Start batch run with valid settings and compare launch success, running status transitions, and completion signaling.
4. Start batch run and stop mid-run; compare process termination behavior and user feedback.
5. Run with non-BatchRvt stdout noise and stderr noise (including log4cplus prefix), compare visible output lines and error toggle behavior.

Exit condition for the vertical slice:

- All V1-V8 items are Implemented.
- P1 and P2 are complete with captured evidence from both UIs for the same input scenarios.
- F1 remains true until the above is complete.
