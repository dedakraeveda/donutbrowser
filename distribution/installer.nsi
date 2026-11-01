Unicode True
!include "MUI2.nsh"
!ifndef PAYLOAD
!error "PAYLOAD must point to the reviewed payload"
!endif
!ifndef OUTPUT
!error "OUTPUT must name a new installer"
!endif
Name "Donut Agent Kit"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\DonutAgentKit"
RequestExecutionLevel user
SetCompressor /SOLID lzma
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PAYLOAD}\LICENSE-Donut-AGPL-3.0.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\Donut Agent Kit.exe"
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!define MUI_FINISHPAGE_TEXT "Donut and CBrowser are installed separately from your existing Donut. Read START_HERE.md before connecting agents. Personal state stays in the state directory and is retained on uninstall."
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Russian"
Section "Donut + CBrowser"
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}\*"
  WriteUninstaller "$INSTDIR\Uninstall Donut Agent Kit.exe"
  CreateDirectory "$SMPROGRAMS\Donut Agent Kit"
  CreateShortcut "$SMPROGRAMS\Donut Agent Kit\Donut Agent Kit.lnk" "$INSTDIR\Donut Agent Kit.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\QuiteDonutAgentKit" "DisplayName" "Donut Agent Kit"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\QuiteDonutAgentKit" "UninstallString" '$"$INSTDIR\Uninstall Donut Agent Kit.exe$"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\QuiteDonutAgentKit" "InstallLocation" "$INSTDIR"
SectionEnd
Section "Uninstall"
  ; Generated list deletes only shipped files; never recursively remove user state.
  !include "${PAYLOAD}\uninstall-files.nsh"
  Delete "$INSTDIR\Uninstall Donut Agent Kit.exe"
  Delete "$SMPROGRAMS\Donut Agent Kit\Donut Agent Kit.lnk"
  RMDir "$SMPROGRAMS\Donut Agent Kit"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\QuiteDonutAgentKit"
  RMDir "$INSTDIR"
SectionEnd
