# WinUI Workflow Validation

Date: 2026-08-18

## Scope

Validate that the WinUI XAML compiler/AppLocker unblock resolves the blocked workflow and that normal project build/test flows succeed.

## Commands Executed

1. Clean + Release build (WinUI project):

```powershell
dotnet clean src/apps/Batch.App.Ui/Batch.App.Ui.csproj -c Release -p:Platform=x64
dotnet build src/apps/Batch.App.Ui/Batch.App.Ui.csproj -c Release -p:Platform=x64 -v:m
```

Result:
- PASS
- `Batch.App.Ui net9.0-windows10.0.19041.0 succeeded`
- No group-policy block error from `XamlCompiler.exe`

2. Direct executable smoke launch (3s then force-stop):

Targets:
- `src/apps/Batch.App.Ui/bin/x64/Release/net9.0-windows10.0.19041.0/Batch.App.Ui.exe`
- `src/apps/Batch.App.Gui/bin/x64/Release/Batch.App.Gui.exe`

Result:
- PASS for both executables
- Both started and remained running until force-stop
- No AppLocker/group-policy launch block observed

3. GUI baseline build + shared tests:

```powershell
dotnet msbuild src/apps/Batch.App.Gui/Batch.App.Gui.csproj /p:Configuration=Release /p:Platform=x64 /v:m
dotnet test tests/Batch.Shared.Util.Tests/Batch.Shared.Util.Tests.csproj --configuration Release -v minimal
```

Result:
- Initial GUI build attempt: FAILED due to output file lock from a still-running `Batch.App.Gui` process (environmental)
- After stopping `Batch.App.Gui` and `Batch.App.Ui` processes, GUI build: PASS
- Shared tests: PASS (38 passed, 0 failed)

4. Solution-level build and test:

```powershell
dotnet build Batch.sln -c Debug -p:Platform=x64 -p:EnableAddinDeployment=false -v:m
dotnet test Batch.sln -c Debug -p:Platform=x64 --no-build -v minimal
```

Result:
- Build: PASS
- Test: PASS (38 passed, 0 failed)

## Conclusion

- WinUI workflow is unblocked for x64 build and direct executable launch.
- The previous blocker (`This program is blocked by group policy`) is no longer observed in this environment.
- Remaining caution: stop running UI executables before rebuilding GUI outputs to avoid MSBuild copy-lock errors.
