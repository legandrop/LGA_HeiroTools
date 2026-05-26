@echo off
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"

:: Copy the script to temp so it survives git checkout (which may delete repo files)
copy /Y "%SCRIPT_DIR%git-safe-merge.ps1" "%TEMP%\git-safe-merge.ps1" >nul
powershell -ExecutionPolicy Bypass -File "%TEMP%\git-safe-merge.ps1" -WorkingDir "%REPO_ROOT%"
pause
