@echo off
setlocal
cd /d "%~dp0"
call "%~dp0.local\cbrowser\cbrowser.cmd" %*
