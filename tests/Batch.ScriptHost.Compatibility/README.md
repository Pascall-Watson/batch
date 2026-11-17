# Script-host compatibility probe

Standalone, Revit-free x64 console probe. Build this project explicitly, separately
from the solution, using an already provisioned SDK/reference assemblies. Targets:
`net48`, `net8.0-windows`, and `net10.0-windows`. There are no package or project
references; automatic .NET Framework reference-assembly package acquisition is
disabled. The .NET Framework 4.8 targeting pack must already be available.
This project disables add-in deployment and does not change the solution.
The [payload-validator regression tests](../../scripts/Test-PythonPayload.Regression.ps1)
exercise optional GUI engine DLLs (absent, correct and incompatible), extra/hidden
standard-library files, a shadow package, same-count replacement, missing files
and modified hashes. They use isolated temporary fixtures and cached dependencies,
never changing actual build outputs or deployed folders. Run them with Windows
PowerShell after a Release x64 solution build; the release workflow runs them too.
The modern probes use the Windows Desktop shared framework, just like the add-ins;
its framework assemblies (including System.CodeDom) are intentionally not copied
into the payload. No new test framework or engine packages are introduced.

The recommended entry point is [the regression runner](../../scripts/Test-ScriptHostCompatibility.ps1)
after a Release x64 solution build and explicit probe build, all with
`EnableAddinDeployment=false`. The runner validates every installer source payload,
checks handler source selection and runs a fresh process for each add-in. It hosts
the desktop probe in Windows PowerShell, avoiding a direct EXE launch where local
policy blocks repository executables. It does not change system execution policy.

## Invocation

Run a **fresh process for each payload**, using the probe target matching the
payload runtime. Arguments, in order:

1. `payloadDirectory`: exact built add-in output/artifact directory, not its parent.
2. `expectedTargetFramework`: exact assembly attribute, such as
   `.NETFramework,Version=v4.8`, `.NETCoreApp,Version=v8.0`, or
   `.NETCoreApp,Version=v10.0`.
3. `expectedScriptsFolder`: `Scripts27` or `Scripts34` (a folder name, not a path).
4. `expectedEngineVersion`: `2.7.12.0` or `3.4.2.0`.
5. Optional `addinYear`: diagnostic label only. Handler source/IL selection belongs
   in the caller's validator; this probe does not load the Revit add-in assembly.

For modern targets, use `dotnet exec` on the built probe DLL. For .NET Framework,
run the built desktop EXE directly. For example, from the repository root in
PowerShell after explicitly building the probe and desired payload elsewhere:

```powershell
dotnet exec tests/Batch.ScriptHost.Compatibility/bin/Debug/net10.0-windows/Batch.ScriptHost.Compatibility.dll '<payload-directory>' '.NETCoreApp,Version=v10.0' Scripts34 3.4.2.0 2027
& tests/Batch.ScriptHost.Compatibility/bin/Debug/net48/Batch.ScriptHost.Compatibility.exe '<payload-directory>' '.NETFramework,Version=v4.8' Scripts27 2.7.12.0 2024
```

Use the analogous `net8.0-windows` DLL with `.NETCoreApp,Version=v8.0`,
`Scripts27`, and `2.7.12.0` for that payload. Paths above assume the default
Debug output layout. Execution policy restrictions are external to this probe;
use an approved execution mechanism rather than changing policy.

## Checks and boundaries

- Loads ScriptHost, Shared.Util, IronPython and DLR assemblies from the payload
  using reflection and framework-specific assembly resolution. Checks both shared
  assemblies' actual target-framework attributes and exact engine/DLR versions.
  Cached assembly metadata verified during implementation: IronPython 2.7.12.0
  pairs with Microsoft.Dynamic/Microsoft.Scripting 1.3.1.0; IronPython 3.4.2.0
  pairs with DLR 1.3.5.0. Reference bindings must preserve exact engine-family
  identities (stronger than matching majors), one loaded identity per name, and
  payload locations. Runtime-provided framework dependencies may live outside it.
- Clears engine filesystem search paths before using actual `ScriptUtil` main-module,
  standard-library and file-source
  helpers. Recursively **compiles every payload host .py file without executing or
  importing host scripts**. A syntax failure names the offending source path.
- IronPython 3 must reject the original repository Scripts27 host source with a
  syntax error. Its payload must be beneath a repository ancestor containing the
  solution marker so that source can be located. IronPython 2 must compile the
  legacy `except Exception, e:` syntax.
- Executes only a safe `sys.version_info` expression and standard-library imports
  (`sys`, `os`, `json`, `traceback`, `collections`, `encodings`) plus a JSON round
  trip in the main scope. Python 2 imports work with no filesystem search paths;
  Python 3 JSON must originate from the payload library. It never imports task/file-host modules. Imported stdlib
  code does execute; this is not a security sandbox for untrusted payloads.
- Requires only the matching Scripts27/Scripts34 folder; Python 3 requires loose
  `lib/os.py`, while Python 2 must have no loose lib folder. Rejects nested
  net48/net8/net10 build-output directories beneath the supplied artifact root.
- Sets the orchestration environment marker to a dummy nonempty value, invokes
  the actual host entry point with a wrong folder and dummy UI object, and
  requires its compatibility `InvalidOperationException`. Restores the marker
  in `finally`. This runs before engine creation and must not reach host execution.
- Rejects RevitAPI resolution and checks that no RevitAPI assembly was loaded.
  Never starts Revit, opens models, or writes deployed folders. Stdlib imports
  retain their normal runtime behavior; the probe does not request file writes.

Successful output lists checks and the script count; failures unwrap reflection
exceptions and return exit code 1. Exit code 0 proves these compatibility checks,
**not** successful Revit API imports, add-in handler selection, task execution,
model processing, or behavior inside Revit. See [recorded validation results](Investigation.md).