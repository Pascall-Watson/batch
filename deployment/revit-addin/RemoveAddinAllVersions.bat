@echo off

pushd %~dp0

for %%i in (2024 2025 2026 2027) do (
	echo.
	echo Removing BatchRvt addin for Revit %%i
	call RemoveAddin.bat %%i
	)

echo Done.
echo.

popd
