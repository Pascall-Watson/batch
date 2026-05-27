# IronPython 2.7 → 3.4 Migration Plan

*Context for the Revit 2027 / .NET 10 upgrade. Decision made 2026-05-12.*

## TL;DR

**The issue.** Revit 2027 runs on .NET 10. We're still on IronPython 2.7, which was built for .NET Framework — its dynamic-language runtime and reflection paths don't play nice with modern .NET, and Python 2 itself has been EOL since 2020. The IronPython team has moved on; 3.4 is the only line they actually test against .NET 10. Revit 2027 forces our hand: we have to move to IronPython 3.4.

**The plan.** Keep two script folders side-by-side: `Scripts27/` (frozen, used by Revit 2015–2026) and `Scripts34/` (used by Revit 2027+). Each per-version addin DLL knows its own scripts folder name (compile-time constant in C#) — no env var detour, no version-comparison logic anywhere. The GUI's Revit-version dropdown is already the only trigger; which Revit spawns determines which addin loads, and each addin is self-aware about its Python flavor. No dual-compat gymnastics, no shims — each set stays idiomatic for its Python version, and `Scripts27/` quietly retires when we drop older Revit support.

**Hello-world stage.** Before porting all ~50 scripts, prove the stack works: swap IronPython 3.4 into the Revit 2027 addin, port just the handful of boot-path scripts to Python 3, and run one trivial task end-to-end in Revit 2027. If that lights up green, the rest is mechanical. If it doesn't, we find out cheap.

## Why two folders, not dual-compat shims

Considered making all 50 scripts compatible with both 2.7 and 3.4. Rejected because:

- Every script becomes a least-common-denominator of two languages — no f-strings, manual `unicode` handling, `from __future__` boilerplate everywhere.
- Doubles the test matrix forever.
- The 2.7 target is sunsetting anyway.

With two folders, each set stays idiomatic, the 2.7 tree freezes into maintenance-only, and dropping pre-2027 support later is just deleting a directory. The tradeoff is bug-fix duplication during the overlap period — accepted.

## Phased plan

### Phase 0 — Prep (no code yet)

- Audit the ~50 scripts in `BatchRvtUtil/Scripts/` for the dependency chain. The current `revit_script_host.py` imports ~17 modules; for the MVP we don't port them — we write a *stub* `revit_script_host.py` in `Scripts34/` that proves the engine boots and exits. Porting the full tree is Phase 2.
- Decide multi-target story for `BatchRvtScriptHost` and `BatchRvtUtil`. They're currently `net4.8` and the 2027 addin (`net10.0-windows`) loads them via netfx compat — already fragile. Either multi-target them (`net48;net10.0-windows`) with TFM-conditional IronPython refs, or fork `BatchRvtScriptHost34` / `BatchRvtUtil34`. Multi-target is cleaner; fork is faster.

### Architecture decision — the dropdown is the only trigger

The GUI's Revit-version dropdown is already the single decision point. It cascades:

```
dropdown picks 2027 → BatchRvt.exe spawns Revit2027.exe → Revit loads only the 2027 addin
                                                          → that addin's DLL has IPy 3.4 baked in (TFM-conditional NuGet)
                                                          → that addin's C# knows its scripts folder is "Scripts34"
```

No env var. No `if year >= 2027`. Each addin is self-aware. `ScriptHostUtil.ExecuteBatchScriptHost` takes the scripts folder name as a C# parameter from each addin's `OnStartup`. `BATCHRVT__SCRIPTS_FOLDER_PATH` is deleted along with `script_environment.SetBatchRvtScriptsFolderPath` and its outer-launcher plumbing.

### Phase 1 — MVP / Hello World

Smallest thing that proves the approach. Do not port other scripts yet.

1. Multi-target `BatchRvtScriptHost.csproj` and `BatchRvtUtil.csproj` as `net48;net10.0-windows`, with TFM-conditional `<PackageReference Include="IronPython">` (2.7.12 for net48, 3.4.x for net10.0-windows). Embedded `python_27_lib.zip` stays under net48; add `python_34_lib.zip` under net10.0-windows; `ScriptUtil.cs` picks the right zip via `#if NET10_0_OR_GREATER`.
2. `BatchRvtAddin2027.csproj` drops its own IronPython 2.7 ref — it inherits 3.4 transitively from the multi-targeted ScriptHost.
3. Refactor `ScriptHostUtil.ExecuteBatchScriptHost(pluginFolderPath, uiApplicationObject)` to also accept `scriptsFolderName` (e.g., `"Scripts27"` or `"Scripts34"`). Each addin's `OnStartup` passes its own constant. Delete the env var read.
4. Create `BatchRvtUtil/Scripts34/revit_script_host.py` as a stub: write `"hello from IPy 3.4 on .NET 10"` + timestamp to `%TEMP%\batchrvt_ipy34_hello.log`, then return. No other imports.
5. Launch Revit 2027 by hand (no outer BatchRvt.exe orchestration yet — the addin loads on any Revit startup, but the original code path requires the env var; after the refactor in step 3 it'll run unconditionally).

**Success criterion:** Revit 2027 launches, no crash, `%TEMP%\batchrvt_ipy34_hello.log` exists with the expected line.

### Phase 2 — Port the long tail

Audit pass (2026-05-21): the actual boot-path closure from `revit_script_host.py` is **38 modules**, not ~17. Splitting Phase 2 into two checkpoints so we can validate IPC before committing to the full port.

#### Phase 2a — Minimal pipe handshake

Stops the orchestrator's infinite retry loop (see [[revit2027-gotchas]] §4). Port the smallest closure that lets the script host inside Revit 2027 phone home to `BatchRvt.exe`:

- `script_environment.py` — env-var protocol the orchestrator uses to pass pipe handle + script paths.
- `client_util.py` — anonymous pipe client.
- `stream_io_util.py` — `StreamWriter` + `WithIgnoredIOException` (broken-pipe tolerance on shutdown).
- `thread_util.py` — `Threading.Thread.Join` wrapper used by terminate path.
- Replace `Scripts34/revit_script_host.py`: read env vars → open pipe → write a hello line → cleanly terminate the Revit process.

**Py2→3 fixes spotted during the audit, to apply per-file as we port:**
- `except X, e:` → `except X as e:` (every file uses old syntax).
- `import exceptions` + `exceptions.Exception` → just `Exception` (only `exception_util.py`; the `exceptions` module is gone in Py3).
- `xrange` → `range` (`revit_script_host.py`).
- Verify `.Item[varName]` indexer on `StringDictionary` still works through IPy 3.4's CLR interop — if not, switch to `dict-style` `[varName]`.

**Success criterion:** launch a batch job from the GUI targeting Revit 2027. Orchestrator spawns Revit once, sees the pipe message, does not retry. GUI exits cleanly.

#### Phase 2b — Full boot path

Port the remaining ~34 modules in dependency order (leaves first). Fix any IPy 2→3 hosting-API divergences in C# (`Python.GetSysModule`, `meta_path.append`, `FullFrames` engine option — verify each survives). Functional-parity smoke test: same batch job in 2027 vs. 2026.

Dependency tiers (from the 2026-05-21 audit):
- **Leaves (no internal deps):** `time_util`, `revit_session`, `revit_dynamo_error`, `json_util`, `environment`, `console_util`, `win32_pinvoke`, `util`, `winforms_util`.
- **Level 1:** `exception_util`, `test_mode_util`, `win32_mpr`, `revit_dialog_util`, `network_util`, `logging_util`, `revit_file_version`, `csv_util`, `text_file_util`, `std_io_util`, `revit_process`.
- **Level 2:** `global_test_mode`, `script_host_error`, `cloud_region_util`, `revit_file_list`, `revit_failure_handling`, `snapshot_data_util`, `revit_file_util`, `revit_dynamo`, `script_util`, `revit_process_host`.
- **Top:** `path_util`, `snapshot_data_exporter`, `revit_script_util`, `revit_script_host` (replace the 2a stub with the real one).

**Phase 2b landmark — 2026-05-21.** End-to-end batch task ran successfully inside Revit 2027 on IPy 3.4 / .NET 10. View/sheet counter task script extracted real model data (Sheets: 17, Views: 51 on `Snowdon Towers Sample HVAC.rvt`), CSV row written, Revit process exited cleanly, orchestrator moved to the next file. Full boot path (38 modules) validated.

One syntax-error gotcha caught during smoke test: `Formatting.None` (a Newtonsoft.Json enum) in `json_util.py` no longer parses under Py3 — `None` is a strict keyword and `Foo.None` is a SyntaxError. Fix: resolve once at module load via `getattr(Formatting, "None")`. The same trap applies to any CLR enum member literally named `None`, `True`, or `False`. (Generated debug surfaced this: `Microsoft.Scripting.SyntaxErrorException: invalid syntax` with no further detail in `e.ToString()` — the user-visible message is unhelpful. Workaround when triaging future SyntaxError noise: `python -m py_compile *.py` against Python 3.x catches the same grammar errors.)

### Phase 3 — Ship & freeze

- Rename `Scripts/` → `Scripts27/`, update all 2015–2026 PostBuild deploys and each <=2026 addin's C# `scriptsFolderName` constant.
- Mark `Scripts27/` maintenance-only in the README; document the bug-fix-twice discipline during the overlap window.
- Version bump, installer update.

---

The whole plan hinges on Phase 1. If the .NET 10 + IPy 3.4 + Revit 2027 stack boots one script, the rest is mechanical work.
