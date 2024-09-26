; Define the name of the installer
OutFile "QView3D Setup.exe"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; Define the name and version of the application
Name "QView3D"
Caption "QView3D Installer"
!define VERSION "0.9.0"
!define PUBLISHER "SUNY Hydra Lab"

; Include the MUI2 (Modern User Interface 2) for better UI
!include "MUI2.nsh"
!define MUI_ICON ".\public\favicon2.ico"

!define MUI_WELCOMEPAGE_TITLE "Welcome to the QView3D Installer"
!define MUI_WELCOMEPAGE_TEXT "This installer will guide you through the installation of QView3D.$\n$\nWarning: This program is in development and may contain bugs.$\n$\nClick Next to continue or Cancel to exit the installer."

!define MUI_LICENSEPAGE_TEXT "Please read the following License Agreement carefully. If you accept the terms of the agreement, click the 'I Agree' checkbox to continue with the installation."
!define MUI_LICENSEPAGE_CHECKBOX $0
!define MUI_LICENSEPAGE_CHECKBOX_TEXT "I accept the terms of the License Agreement"

!define MUI_FINISHPAGE_RUN "$DESKTOP\QView3D.lnk"


; Include x64.nsh for checking if the system is x64
!include "x64.nsh"

Function .onInit
    Var /GLOBAL PROGRAM_FILES
    Var /Global InstallDirSuffix
    StrCpy "$InstallDirSuffix" "\SUNY Hydra Lab\Qview3D"
    ; Check if the system is x64 and set the installation directory
    ${If} ${RunningX64}
        StrCpy "$PROGRAM_FILES" "$PROGRAMFILES64"
    ${Else}
        StrCpy "$PROGRAM_FILES" "$PROGRAMFILES32"
    ${EndIf}
    StrCpy "$INSTDIR" `$PROGRAM_FILES$InstallDirSuffix`

; Function to check if the system is in dark mode
;    Var /GLOBAL BG_COLOR
;    Var /GLOBAL TEXT_COLOR
;    ReadRegDWORD $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" "AppsUseLightTheme"
;    ${If} $0 == 0
;        ; Dark mode
;        StrCpy $BG_COLOR "#444444"
;        StrCpy $TEXT_COLOR "#FFFFFF"
;    ${Else}
;        ; Light mode
;        StrCpy $BG_COLOR "#bbbbbb"
;        StrCpy $TEXT_COLOR "#000000"
;    ${EndIf}
;    !define MUI_BGCOLOR "$BG_COLOR"
;    !define MUI_TEXTCOLOR "$TEXT_COLOR"

FunctionEnd

; Define the pages to be displayed
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Define the language
!insertmacro MUI_LANGUAGE "English"

; Define installation types
InstType "Client"
InstType "Server"
InstType "Both"

Section "Client" client
    SectionInstType 0 2
    DetailPrint "Installing client..."
    ; Set the installation directory
    DetailPrint "Setting installation directory..."
    SetOutPath "$INSTDIR\client"
    DetailPrint "Setting installation directory...done"

    ; Package the client build into the installer
    File /r ".\client\out\QView3D-win32-x64\*"

    ; Create a shortcut on the desktop
    CreateShortcut "$DESKTOP\QView3D.lnk" "$INSTDIR\client\QView3D.exe"

    ; Create a shortcut in the start menu
    CreateDirectory "$SMPROGRAMS\QView3D"
    CreateShortcut "$SMPROGRAMS\QView3D\QView3D.lnk" "$INSTDIR\client\QView3D.exe"
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Register the uninstaller
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "DisplayName" "QView3D"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "DisplayIcon" "$INSTDIR\client\QView3D.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "DisplayVersion" "${VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "NoRepair" 1
SectionEnd

Section /o "Server" server
    SectionInstType 1 2
    ; Set the installation directory
    SetOutPath "$INSTDIR\server"

    ; Package the server build into the installer
    File /r "C:\Users\Ari Yeger\Desktop\school\F24\Projects\QView3D\server\*"
    ;File "C:\Users\Ari Yeger\Desktop\school\F24\Projects\QView3D\server\QView3D.exe"
    ; Create a shortcut on the desktop
    CreateShortcut "$DESKTOP\QView3D_Server.lnk" "$INSTDIR\server\QView3D.exe"

    ; Create a shortcut in the start menu
    CreateDirectory "$SMPROGRAMS\QView3D"
    CreateShortcut "$SMPROGRAMS\QView3D\QView3D.lnk" "$INSTDIR\server\QView3D.exe"
    WriteUninstaller "$INSTDIR\uninstall.exe"


    ; Register the uninstaller
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "DisplayName" "QView3D"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "DisplayIcon" "$INSTDIR\server\QView3D.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "DisplayVersion" "${VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D" "NoRepair" 1
SectionEnd

LangString DESC_client ${LANG_ENGLISH} "This installs the standalone Electron Application. This is for users who have a server on a separate machine."
LangString DESC_server ${LANG_ENGLISH} "This installs the standalone Flask Server Application. This is for users who have a client on a separate machine."
;LangString DESC_both ${LANG_ENGLISH} "This installs the combined application. This is for users who have both the client and server on the same machine."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${client} $(DESC_client)
!insertmacro MUI_DESCRIPTION_TEXT ${server} $(DESC_server)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Define the uninstaller section
Section "Uninstall"
    ${If} ${RunningX64}
        StrCpy "$PROGRAM_FILES" "$PROGRAMFILES64"
    ${Else}
        StrCpy "$PROGRAM_FILES" "$PROGRAMFILES32"
    ${EndIf}
    ; Remove the installed files
    DetailPrint "Removing installed files..."
    ; check if the client was installed
    IfFileExists `$PROGRAM_FILES\SUNY Hydra Lab\QView3D\client\QView3D.exe` 0 +4
    DetailPrint "   Removing client files..."
    RMDir /r `$PROGRAM_FILES\SUNY Hydra Lab\QView3D\client`
    DetailPrint "   Removing client files...done"

    ; check if the server was installed
    IfFileExists `$PROGRAM_FILES\SUNY Hydra Lab\QView3D\server\QView3D.exe` 0 +4
    DetailPrint "   Removing server files..."
    RMDir /r `$PROGRAM_FILES\SUNY Hydra Lab\QView3D\server`
    DetailPrint "   Removing server files...done"

    ; Remove the installation directory
    RMDir /r `$PROGRAM_FILES\SUNY Hydra Lab`

    ; Remove the desktop shortcut
    Delete `$DESKTOP\QView3D.lnk`

    ; Remove the start menu shortcut
    Delete `$SMPROGRAMS\QView3D\QView3D.lnk`
    RMDir `$SMPROGRAMS\QView3D`
    DetailPrint "Removing installed files...done"

    ; Remove the uninstaller registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\QView3D"
SectionEnd