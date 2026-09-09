@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Demo.ps1" %*
set "SRT_CHECK_EXIT=%ERRORLEVEL%"
echo.
echo Check complete. Exit code: %SRT_CHECK_EXIT%
pause
exit /b %SRT_CHECK_EXIT%
