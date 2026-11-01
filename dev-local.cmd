@echo off
setlocal
cd /d "%~dp0"
set "DONUT_LOCAL_FEATURES=1"
set "NEXT_PUBLIC_DONUT_LOCAL_FEATURES=1"
set "BROWSER_CACHE_DIR=%~dp0.local\cbrowser\cache"
pnpm tauri dev
