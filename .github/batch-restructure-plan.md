# Batch Solution Restructure Plan (Plan Only)

## Scope And Intent

This document is planning-only. It does **not** apply code or file changes.

Goal:

- Standardise naming to a consistent `Batch` prefix.
- Improve folder clarity and dependency visibility.
- Preserve all existing behaviour across Revit 2024-2027 and both Python runtime payloads.
- Keep the four separate AddIn projects (one per year).

Non-goals:

- No consolidation of AddIns into multi-targeting.
- No runtime behaviour changes.
- No merging of `Scripts27` and `Scripts34`.

---

## Proposed Naming Convention (Consistent `Batch`)

Use `Batch.*` names across projects and solution entries.

Project naming pattern:

- `Batch.App.Cli`
- `Batch.App.Gui`
- `Batch.Integration.Dynamo`
- `Batch.Shared.Util`
- `Batch.Shared.ScriptHost`
- `Batch.AddIn.2024`
- `Batch.AddIn.2025`
- `Batch.AddIn.2026`
- `Batch.AddIn.2027`
- `Batch.Shared.Util.Tests`

Folder naming pattern:

- `src/apps/*`
- `src/integrations/*`
- `src/shared/*`
- `src/addins/*`
- `tests/*`
- `deployment/revit-addin/*`
- `installer/inno/*`
- `third_party/*`

Notes:

- Keep per-year AddIn split.
- Keep AddIn target frameworks and pinned Revit API package versions exactly as-is.
- Keep script runtime split (`Scripts27` and `Scripts34`) exactly as-is.
- Keep `packages/` at repository root (lowercase) to avoid mass rewrites of legacy `..\packages\...` imports.

---

## Proposed Repository Layout

```text
batch/
├─ src/
│  ├─ apps/
│  │  ├─ Batch.App.Cli/
│  │  └─ Batch.App.Gui/
│  ├─ integrations/
│  │  └─ Batch.Integration.Dynamo/
│  ├─ shared/
│  │  ├─ Batch.Shared.Util/
│  │  │  ├─ Scripts27/
│  │  │  └─ Scripts34/
│  │  ├─ Batch.Shared.ScriptHost/
│  │  └─ Common/
│  └─ addins/
│     ├─ Batch.AddIn.2024/
│     ├─ Batch.AddIn.2025/
│     ├─ Batch.AddIn.2026/
│     └─ Batch.AddIn.2027/
├─ tests/
│  └─ Batch.Shared.Util.Tests/
├─ deployment/
│  └─ revit-addin/
├─ installer/
│  └─ inno/
├─ third_party/
│  └─ References/
├─ .github/
├─ Batch.sln
├─ Directory.Build.targets
├─ global.json
├─ packages/
└─ README.md
```

---

## Canonical Modern Paths

| Component | Path |
| --- | --- |
| CLI app | `src/apps/Batch.App.Cli/` |
| GUI app | `src/apps/Batch.App.Gui/` |
| Dynamo integration | `src/integrations/Batch.Integration.Dynamo/` |
| Shared util library | `src/shared/Batch.Shared.Util/` |
| Shared script host library | `src/shared/Batch.Shared.ScriptHost/` |
| Revit addin 2024 | `src/addins/Batch.AddIn.2024/` |
| Revit addin 2025 | `src/addins/Batch.AddIn.2025/` |
| Revit addin 2026 | `src/addins/Batch.AddIn.2026/` |
| Revit addin 2027 | `src/addins/Batch.AddIn.2027/` |
| Shared util tests | `tests/Batch.Shared.Util.Tests/` |
| Common shared code | `src/shared/Common/` |
| Addin deployment scripts | `deployment/revit-addin/` |
| Installer scripts | `installer/inno/` |
| Third-party references | `third_party/References/` |
| NuGet package cache | `packages/` (retain at repo root) |

---

## Dependency-Aware Implementation Plan

### Phase 1 - Structural Move + Solution Wiring

1. Create top-level folders: `src`, `tests`, `deployment`, `installer`, `third_party`.
2. Move project folders to new locations per map above.
3. Update `Batch.sln` project paths for every moved project.
4. Keep current project GUIDs and build configurations unchanged.

### Phase 2 - Project Renames (Logical Names)

1. Rename `.csproj` files to `Batch.*` pattern.
2. Update `<AssemblyName>` and `<RootNamespace>` values to `Batch.*` equivalents.
3. Update in-code namespaces and using statements where required.
4. Preserve target frameworks and package versions, especially AddIns.

### Phase 3 - Reference Repair (Critical)

Update all relative paths that move-sensitive projects currently rely on:

- `ProjectReference Include="..\..."`
- `Compile Include="..\Common\GlobalAssemblyInfo.cs"`
- `HintPath` entries to `References` and `packages`
- `Import Project="..\packages\..."`
- Analyzer includes to `..\packages\...`

This is required for legacy non-SDK projects after moving under `src`/`tests`.

### Phase 4 - AddIn And Deployment Integrity

1. Keep four AddIn projects separate (2024, 2025, 2026, 2027).
2. Keep each AddIn single-target.
3. Keep pinned Revit API package versions unchanged.
4. Keep post-build deployment logic behaviour unchanged.
5. Keep `.addin` per-year manifest validity and destination paths intact.

### Phase 5 - Script Runtime Integrity

1. Keep `Scripts27` and `Scripts34` as separate directories.
2. Keep existing per-year script host routing logic:
   - 2024-2026 -> `Scripts27`
   - 2027 -> `Scripts34`
3. Ensure script content copy rules still include both runtime trees.

### Phase 6 - Installer/CI/Docs Alignment

1. Update installer source paths in Inno config after folder/project renames.
2. Update deployment batch script references and relative locations.
3. Update GitHub workflow paths for restore/build/test/package verification.
4. Update README structure and command examples to new paths/names.

### Phase 7 - Validation Gates

Run and pass all of the following before merge:

1. `nuget restore` and `dotnet restore`.
2. Full solution build `Debug` and `Release` (`x64`).
3. `Batch.Shared.Util.Tests` execution.
4. Local AddIn deploy/remove scripts for all years (2024-2027).
5. Installer dry run and source verification.
6. GUI smoke test and CLI smoke test.
7. Per-year Revit AddIn load sanity checks.

---

## Project-Specific Update Checklist

### Shared

- `Batch.sln` path entries and dependencies.
- `Directory.Build.targets` remains at repo root.
- `global.json` remains at repo root.

### Applications

- CLI project path, project name, assembly name, root namespace, project references.
- GUI project path, project name, assembly name, root namespace, icon/content paths, project references.
- Dynamo integration project path, project name, references.

### Shared Libraries

- Util project path/name plus script payload copy rules (`Scripts27`, `Scripts34`).
- Script host project path/name while preserving multi-targeting.
- Common assembly info linked-file include paths.

### AddIns (Per Year)

For each of 2024, 2025, 2026, 2027:

1. Project path/name updates.
2. `ProjectReference` rewrites to shared projects.
3. Post-build `DeployAddin` script path rewrite (if script folder moved).
4. `.addin` manifest path checks for assembly and class.
5. Keep package version pins unchanged.

### Deployment + Installer + CI

- `deployment/revit-addin/*.bat` relative path rewrites.
- `installer/inno/*.iss` source path rewrites.
- `.github/workflows/build_msi.yml` path rewrites and verification rules.

---

## Risk Controls

- Use one focused PR per phase where possible.
- Do not combine naming changes with behaviour changes.
- Keep runtime and AddIn compatibility checks mandatory.
- Keep a rollback point after each phase.

---

## Explicit Constraints To Enforce During Implementation

1. Four AddIn projects must remain separate.
2. AddIns must remain single-targeted.
3. Pinned Revit API package versions must remain unchanged.
4. Shared code must remain centralised (no duplication into AddIns).
5. Existing multi-targeting must remain only in shared script host/util projects.
6. `Scripts27` and `Scripts34` must remain separate and non-merged.

---

## Suggested Execution Order (Practical)

1. Create new folder skeleton.
2. Move shared projects first.
3. Move app and integration projects.
4. Move AddIn projects.
5. Move tests, deployment, installer, and third-party folders.
6. Repair `.sln` and all project references.
7. Repair CI/installer/docs.
8. Run full validation gate.

---

## Completion Criteria

The plan is complete when:

- All projects build from new locations.
- All tests pass.
- AddIns for 2024-2027 still load and execute.
- Both Python runtime payloads remain discoverable and functional.
- Installer and CI pipelines succeed with updated paths.
