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
| B1 | Startup preflight warns when no supported Revit add-in is installed | Not started | WinForms checks installed versions and blocks startup with error UI: [src/apps/Batch.App.Gui/Program.cs](src/apps/Batch.App.Gui/Program.cs#L40), [src/apps/Batch.App.Gui/Program.cs](src/apps/Batch.App.Gui/Program.cs#L48). WinUI launches window directly: [src/apps/Batch.App.Ui/Program.cs](src/apps/Batch.App.Ui/Program.cs#L16), [src/apps/Batch.App.Ui/App.xaml.cs](src/apps/Batch.App.Ui/App.xaml.cs#L15). | Add the same preflight check and user-facing failure message before opening MainWindow. |
| B2 | Default settings path auto-load on startup | Implemented | WinForms loads at form startup: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L388). WinUI loads on window construction: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L50). Both rely on shared default path API: [src/shared/Batch.Shared.Util/BatchRvtSettings.cs](src/shared/Batch.Shared.Util/BatchRvtSettings.cs#L236). | Keep behavior; include in parity test scenarios. |
| B3 | Alternate settings file selection and explicit load | Implemented | WinForms import flow: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L915). WinUI browse + load flow: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L259), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L289). | Keep behavior; verify with same sample settings file. |
| B4 | Load-failure feedback is explicit and actionable | Partial | WinForms has TODO after initial load failure (no explicit surfaced error): [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L390). WinUI emits status and output errors: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L474), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L484). | Decide canonical behavior, then align both UIs (or document intentional improvement). |

## 2) Thin application-service contract for UI actions

| ID | Contract item | Current WinUI status | Evidence | Gap to close |
| --- | --- | --- | --- | --- |
| C1 | Extract settings workflow service (load/save/save-as/summary) from window code-behind | Not started | WinUI currently performs settings read/write/model-load directly in MainWindow handlers: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L454), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L493). | Introduce a thin service interface and move file + parsing logic out of view layer. |
| C2 | Extract run-control service (start/stop/process lifecycle) from window code-behind | Not started | WinUI starts/stops Process directly in MainWindow: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L322), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L414). | Define run service contract and process lifecycle events independent of UI framework. |
| C3 | Extract output/status policy service (stdout/stderr filters, status transitions) | Not started | Output filtering and status strings are coded in MainWindow handlers: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L373), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L389), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L564). | Centralize filtering/status policy so WinForms and WinUI can share behavior. |
| C4 | Launcher behavior uses shared CLI-first fallback path | Implemented | WinUI calls shared launcher: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L342). Shared resolver prefers CLI then legacy exe: [src/shared/Batch.Shared.Util/BatchRvt.cs](src/shared/Batch.Shared.Util/BatchRvt.cs#L142), [src/shared/Batch.Shared.Util/BatchRvt.cs](src/shared/Batch.Shared.Util/BatchRvt.cs#L149). | Keep behavior; ensure both app outputs package launcher files identically. |

## 3) First vertical slice in WinUI (load/edit-save/start-stop/output)

| ID | Vertical-slice item | Current WinUI status | Evidence | Gap to close |
| --- | --- | --- | --- | --- |
| V1 | Load settings (default + selected file) | Implemented | WinUI load path and UI actions: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L289), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L454). | Add scenario validation against WinForms baseline outputs. |
| V2 | Edit settings content before save | Partial | WinUI provides raw JSON editor and summary labels: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L204), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L531). WinForms has broad typed settings controls for batch workflows: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L98), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L277). | For parity gate, either implement minimum typed controls for primary workflow or define JSON editing as accepted interim UX with validation criteria. |
| V3 | Save settings and save-as/export | Implemented | WinUI save and save-as: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L297), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L303), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L493). WinForms save/import/export: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L420), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L926). | Add parity scenarios for roundtrip save/load equivalence. |
| V4 | Start run with equivalent pre-run validation | Not started | WinForms validates required script/file/folder options before launch: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L500). WinUI only validates settings-path presence/existence before launch: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L327), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L332). | Add pre-run validation contract aligned with primary WinForms checks. |
| V5 | Stop run behavior during active processing | Partial | WinUI exposes explicit Stop and force-kill: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L368), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L422). WinForms uses close-time confirmation when running: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L429), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L451). | Decide desired canonical stop UX; align prompts/status across both UIs for parity comparisons. |
| V6 | Stream output with equivalent stdout filtering behavior | Not started | WinForms intentionally suppresses non-BatchRvt stdout lines: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L604). WinUI currently appends non-BatchRvt lines as REVIT MESSAGE: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L385), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L386). | Match legacy filter semantics (or ratify new policy and explicitly update baseline). |
| V7 | Stream output with equivalent stderr filtering/error toggles | Implemented | WinForms filters log4cplus and gates errors on setting: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L614). WinUI mirrors this behavior: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L394), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L397). | Keep behavior; include toggle-on/toggle-off tests in parity runbook. |
| V8 | Equivalent run-status signaling (running/exited/failed) | Partial | WinForms uses start button state/text and running mode switch: [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L573), [src/apps/Batch.App.Gui/BatchRvtGuiForm.cs](src/apps/Batch.App.Gui/BatchRvtGuiForm.cs#L621). WinUI uses status text and start/stop enablement: [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L365), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L410), [src/apps/Batch.App.Ui/MainWindow.xaml.cs](src/apps/Batch.App.Ui/MainWindow.xaml.cs#L564). | Define canonical status state model and compare by state transitions, not control text alone. |

## 4) Parity validation execution (both UIs, same scenarios)

| ID | Validation item | Current WinUI status | Evidence | Gap to close |
| --- | --- | --- | --- | --- |
| P1 | Scenario matrix exists for side-by-side WinForms vs WinUI runs | Not started | No parity runbook found in repository (manual review). | Add a reproducible scenario checklist with expected outcomes and evidence capture format. |
| P2 | Primary workflow gate executed and recorded | Not started | No recorded run artifacts in repository (manual review). | Execute gate scenarios and capture pass/fail results for both UIs. |
| P3 | Automated tests cover WinUI parity-critical behavior | Not started | Shared launcher fallback tests exist: [tests/Batch.Shared.Util.Tests/BatchRvtTests.cs](tests/Batch.Shared.Util.Tests/BatchRvtTests.cs#L209). No tests found referencing Batch.App.Ui in tests tree (manual search). | Add tests for extracted services and output policy; keep UI framework-specific smoke tests minimal. |

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
