# .claude/ — local working notes

Living docs for the IronPython 2.7 → 3.4 migration and the Revit 2027 work. Not shipped in releases; not on the master branch's build path. Safe to evolve freely.

## Files

- [`ironpython-34-migration.md`](ironpython-34-migration.md) — the canonical migration plan. Updated as the architecture is refined.
- [`sandbox-ipy34-hello/`](sandbox-ipy34-hello/) — throwaway net10.0 console project that proves `print("hello")` runs on IronPython 3.4.2 outside any Revit context. Stage 0 sanity check.

## Session log: 2026-05-13 — Phase 1 GREEN

Phase 1 of the migration (hello-world end-to-end inside Revit 2027) was validated on `feature-revit2027-support`. The .NET 10 + Revit 2027 + IronPython 3.4 stack works; a Python 3 stub script ran successfully inside Revit 2027 and wrote a log line.

### What landed

Branch: `feature-revit2027-support`. All on top of the prior PR that got `BatchRvtGUI.exe` to launch on .NET 10.

| Phase | Change |
|---|---|
| 1.1 | Multi-targeted `BatchRvtScriptHost.csproj` and `BatchRvtUtil.csproj` as `net48;net10.0-windows`. Both modernized to SDK-style. TFM-conditional `IronPython` ref: 2.7.12 for net48, 3.4.2 for net10.0-windows. Dropped a pile of unused refs (xunit, Moq, FluentAssertions, System.IO-shim, etc.). |
| 1.2 | Added `IronPython.StdLib 3.4.2` NuGet for the net10.0-windows TFM. `ScriptUtil.AddPythonStandardLibrary` is now TFM-conditional: net48 keeps the embedded-zip `ResourceMetaPathImporter` route; net10 adds a `lib/` search path (the StdLib package's ~640 `.py` files deploy via ContentFiles to the addin folder). |
| 1.3 | `ScriptHostUtil.ExecuteBatchScriptHost` now takes `scriptsFolderName` from each addin. Removed the `BATCHRVT__SCRIPTS_FOLDER_PATH` env-var dance. Added an "orchestration marker" check on `BATCHRVT__SCRIPT_FILE_PATH` so the addin no-ops cleanly when Revit is launched outside a batch session. All 13 per-version addins updated: 2027 passes `"Scripts34"`, 2015–2026 pass `"Scripts"`. |
| 1.4 | Dropped `IronPython 2.7.12` `PackageReference` from `BatchRvtAddin2027.csproj` — it inherits 3.4.2 transitively from the multi-targeted ScriptHost. |
| 1.5 | Created `BatchRvtUtil/Scripts34/revit_script_host.py` — a minimal Python 3 stub that writes a hello line + IronPython version + env-var state to a log file, then exits. |
| 1.6 | End-to-end test: `BatchRvtGUI` → `BatchRvt.exe` orchestrator → spawns Revit 2027 → addin loads → IPy 3.4 engine boots → stub script runs → hello log written. **Green.** |

### Incidental fixes along the way

Things broken by Phase 1 work that needed unblocking; not technically part of the plan but required to get an end-to-end run.

- **`BatchRvt.exe`, `BatchRvtGUI`, `BatchRevitDynamo`** all had `<Reference><HintPath>..\References\IronPython-2.7.3\*.dll</HintPath><Private>True</Private></Reference>` lines, forcing copy-local of the local IronPython 2.7.3 DLLs into their deploy folders. After 1.1, that conflicted with the 2.7.12 NuGet refs ScriptHost transitively pulled in. Fix: deleted those local refs (none of these projects directly `using IronPython` — they only need it transitively). They now inherit the right version automatically.
- **`ExternalEvent` GC root bug.** `BatchRvtAddin2027.OnStartup` created the handler as a local variable. On .NET 10 with Revit 2027, GC reclaims it before Revit pumps the event → `Execute` never fires, no error, just silence. Fix: stored the handler in a `private static` field on `BatchRvtAddinApplication`. See [revit2027-gotchas memory](../../../.claude/projects/.../memory/project_revit2027_gotchas.md) (saved to user-level memory).

### Empirical findings worth not forgetting

Three things discovered during this session that are not derivable from reading the codebase — they only show up at runtime. Saved as durable project memories under `~/.claude/projects/.../memory/`.

1. **IronPython 2.7 cannot run inside Revit 2027.** Confirmed via `System.ArgumentException: Type doesn't have a method with a given name and signature` from `Microsoft.Scripting.Generation.ILGen.EmitCall` → `IronPython.Runtime.Types.NewTypeMaker.ImplementCTDOverride` → `ImplementCustomTypeDescriptor`. The 2.7 IL emitter looks for a method on `ICustomTypeDescriptor` whose signature differs between .NET Framework and .NET 10. The migration to 3.4 isn't optional; it's the only path forward for 2027.
2. **`Path.GetTempPath()` is sandboxed inside Revit 2027's process** to a per-session GUID subfolder (e.g. `C:\Users\<user>\AppData\Local\Temp\<GUID>\`), not the user's normal `%TEMP%`. External tooling that looks for diagnostic files in plain `%TEMP%` won't find them. For diagnostic logs from addin code, either hardcode an absolute path (`C:\Users\Public\` is reliably writable) or recurse-search `%TEMP%`.
3. **`IExternalEventHandler` instances must be statically rooted on .NET 10.** The pattern `var h = new MyHandler(); h.Raise();` from OnStartup, with `h` as a local, silently fails on Revit 2027 — GC reclaims `h` before `Execute` is pumped. Likely applies to `IUpdater`, `IEventArgs` subscribers, etc. as well.

### Cleanup still pending before commit

Before squashing this work into a PR:

1. **Sweep scattered diag log files** from `%TEMP%\<GUID>\`, `C:\Users\Public\`, `~\`, and the deployed addin folder. Pattern: `batchrvt_*_diag.log`, `batchrvt_ipy34_hello.log`.

### What's next (Phase 2)

Phase 1 only proves the stack works with a *stub* `revit_script_host.py`. The 16-import boot path that the original `BatchRvtUtil/Scripts/revit_script_host.py` depends on is still all Python 2 syntax — `print x`, `except E, e:`, `xrange`, etc. Phase 2 is the mechanical port of those modules (and the long tail of ~45 task-script utility modules) to Python 3 syntax in `BatchRvtUtil/Scripts34/`.

A functional end-to-end batch run against Revit 2027 requires Phase 2.

### Branch state

- `feature-revit2027-support` has all Phase 1 changes + the prior 2027 launch fix.
- Solution builds clean (0 errors, ~50 warnings — most are MSBuild noise about old addins (2015–2023) still using local-HintPath IronPython 2.7.3 refs, which work fine for those targets).
- All 13 addins deploy successfully to `%AppData%\Autodesk\Revit\Addins\<year>\BatchRvt\` via the per-project PostBuild step.
