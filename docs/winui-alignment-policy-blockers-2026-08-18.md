# WinUI Alignment And Policy Blockers

Date: 2026-08-18

## Goal

Align `Batch.App.Ui` startup with WinUI gallery patterns and avoid local workaround/hack startup paths.

## Alignment Changes Applied

1. Added `App.xaml` with standard WinUI resource setup:
   - `<XamlControlsResources xmlns="using:Microsoft.UI.Xaml.Controls" />`
2. Switched `App` to `partial` and called `InitializeComponent()` in constructor.
3. Removed custom `Program.cs` entrypoint and re-enabled generated WinUI entrypoint.
4. Removed WinUI probe/fallback/style-forcing instrumentation from `MainWindow`:
   - no `BATCH_WINUI_PROBE_STAGE`
   - no fallback shell content
   - no recursive `ApplyVisibleDefaults`
5. Kept normal preflight and shell error logging behavior.

## Current External Blockers (Policy)

Build diagnostics confirm official WinUI toolchain executables are still blocked by policy:

1. XAML compiler blocked:
- `C:\Users\Wayne\.nuget\packages\microsoft.windowsappsdk.winui\2.2.1\tools\net472\XamlCompiler.exe`
- Symptom: `output.json` not created with group policy block message.

2. PRI generator blocked (when PRI generation is enabled):
- `C:\Users\Wayne\.nuget\packages\microsoft.windows.sdk.buildtools\10.0.26100.4654\bin\10.0.26100.0\x64\makepri.exe`
- Symptom: `MSB6003` from `MrtCore.PriGen.targets`.

## Conclusion

The app is now structurally aligned with gallery-style WinUI startup, but execution remains blocked by AppLocker/Group Policy on required Microsoft build tools.

Use the updated unblock artifacts:
- `docs/winui-xaml-unblock-file-paths.txt`
- `docs/winui-xaml-unblock-it-request.txt`
