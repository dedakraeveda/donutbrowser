@echo off
setlocal
cd /d "%~dp0"
set "PYTHONNOUSERSITE=1"
set "BROWSER_CACHE_DIR=%~dp0.local\cbrowser\cache"
"%~dp0.local\cbrowser\python\python.exe" %*
