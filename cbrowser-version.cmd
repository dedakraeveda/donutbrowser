@echo off
setlocal
cd /d "%~dp0"
"%~dp0.local\cbrowser\python\python.exe" "%~dp0.local\cbrowser\select_version.py" %*
