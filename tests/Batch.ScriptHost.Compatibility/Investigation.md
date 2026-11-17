# Revit 2025/2026 Python compatibility investigation

## Baseline findings (2026-11-17)

The earlier report is only partly consistent with the checked-in source:

- Revit 2025/2026 target .NET 8 and explicitly select Scripts27. Scripts27 contains
  Python 2 exception-handler syntax rejected by IronPython 3.
- However, both checked-in shared projects targeted **only net48 and net10.0-windows**.
  ScriptHost selected IronPython 2.7.12 for net48 and 3.4.2 for net10; Shared.Util
  had no explicit IronPython 3 reference. No project-reference override, custom
  assembly resolver, or build property forcing Python 3 was found in the repository.
- A fresh cached-package restore and unchanged Revit 2025 build selected **net48**
  shared libraries through the SDK's default AssetTargetFallback, producing NU1702
  warnings. Therefore the exact claim that clean current source necessarily pairs
  Python 3 with Scripts27 is **refuted**. The confirmed source defect is the missing
  native .NET 8 shared-library build, plus unguarded packaging of flat output trees.
- Before restore, existing ignored local assets selected IronPython 3.4.2 / DLR
  1.3.5 for net8 Revit 2025/2026 and listed net8 shared targets absent from the source.
  These stale/local artifacts illustrate the mismatch, not a reproducible clean
  source configuration and not evidence about either user's installed package.
- IronPython 2.7.12 has netcoreapp3.1 and netstandard2.0 assets; the SDK selects its
  netcoreapp3.1 implementation for the new net8 target. Actual-engine checks on
  .NET 8 demonstrate engine creation, Python 2 syntax and embedded stdlib imports
  without Revit. No Python compatibility change was needed.

## Correction

Both shared projects now have a native .NET 8 target using Python 2, while .NET 10
retains Python 3. Shared.Util obtains IronPython transitively from ScriptHost;
redundant add-in engine references were removed. Utility script-folder selection
uses the same engine-specific constant as the host. A runtime guard rejects a
caller requesting the wrong script family before any host script is executed.

Only matching host scripts are copied. Python 2 embeds its existing library;
Python 3's library is explicitly propagated through project references. Build
cleanup removes opposite-family script/library folders from local output. The
installer validates all source roots, engine/DLR and shared-library hashes, scripts
and Python 3 stdlib before recursively packaging them. Its upgrade cleanup is
restricted to application-owned Python folders. Those installation-time actions
were **not executed** during this investigation.

## Recorded validation

All builds/tests explicitly disabled deployment with EnableAddinDeployment=false;
the terminal environment also disabled deployment. Existing SDKs, reference packs,
tools and cached packages were used; no software was installed.

- Full solution: Visual Studio MSBuild Release x64 with cached-package restore,
  subsequent incremental builds and a final full Rebuild: **passed**. Native net8 shared libraries
  resolve without the baseline NU1702 fallback. Existing SYSLIB0012 (CodeBase) and
  CA1416 platform warnings remain; they are outside this compatibility correction.
- Existing utility xUnit suite: **27 passed, 0 failed**.
- Standalone probe build: net48/net8/net10, **passed** with no new package references.
- Revit 2024 payload: **59 host scripts compiled**, 132 probe checks passed.
- Revit 2025 and 2026 payloads: **59 scripts each**, 166 checks each passed.
- Revit 2027 payload: **39 scripts**, 163 checks passed. Python 3 rejected the
  original Scripts27 host with Microsoft.Scripting.SyntaxErrorException.
- All engine probes: standard-library imports and JSON round trip passed, isolated
  filesystem search paths, expected engine/DLR/target identities, wrong-folder
  guard and no-Revit assembly checks passed. Framework dependencies come from the
  corresponding Windows Desktop runtime, not an arbitrary engine-package cache.
- GUI plus all four add-in packaging gates: **passed**.
- Negative packaging control: a temporary Scripts34 marker in the **local build
  output** for Revit 2025 was rejected by the validator and direct Inno compiler
  (exit 2). A deployment-disabled build removed it, then all checks passed again.
- Inno Setup 6.7.3 compile with **/O-** (output disabled): **passed**, including
  the preprocessor payload gate. No installer was generated or run.

## Limits and separate observations

These are parsing/stdlib/assembly-binding tests, not Revit runtime tests. No Revit
process, model, task cleanup, shared network script or deployed folder was touched.
No commit, push or release was performed. Installer upgrade execution, add-in load
contexts alongside other Revit add-ins, API imports and real tasks remain untested.
The runner checks handler source selection, not the compiled handler's IL.

Existing external-event lifetime handling differs: the 2027 application retains
its handler statically; earlier handlers use a local variable. This is separate
from Python parsing and was not changed. The .NET runtime requirements of later
Revit 2025/2026 updates also need a separate version-specific support review; this
fix preserves the repository's existing .NET 8 add-in targets and Python contract.

Roberto's installed CLI/add-in/payload and Ed's working installation were not
inspected. Their versions are unknown. Replace any confirmed mixed/old-fallback
package with a complete corrected build; do not infer installation identity from
matching intended installer names or repair only one dependency DLL.