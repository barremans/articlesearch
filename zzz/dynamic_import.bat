@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

echo.
echo === 📥 Installatie vanaf USB of externe bron ===
echo.

:: ====== USB-driveletter vragen ======
:inputdrive
set /p USB_DRIVE=Geef de stationsletter van de USB-stick (bv. E): 
if not exist "%USB_DRIVE%:\" (
    echo ❌ Station %USB_DRIVE% bestaat niet. Probeer opnieuw.
    goto inputdrive
)
set USB_PATH=%USB_DRIVE%:\

:: ====== Zoek laatste ArticleSearch_* folder ======
set "SOURCE_FOLDER="
for /f "delims=" %%d in ('dir "%USB_PATH%ArticleSearch_*" /ad /b /o-d') do (
    set "SOURCE_FOLDER=%USB_PATH%%%d"
    goto found
)

:found
if not defined SOURCE_FOLDER (
    echo ❌ Geen geldige map gevonden met naam 'ArticleSearch_*' op %USB_PATH%
    pause
    exit /b
)

echo [INFO] Geselecteerde bronmap: %SOURCE_FOLDER%

:: ====== Doelmap instellen op C:\SearchArticle ======
set "TARGET_FOLDER=C:\SearchArticle"
set FIRST_INSTALL=0

if not exist "%TARGET_FOLDER%" (
    echo [INFO] Doelmap bestaat nog niet. Wordt aangemaakt...
    mkdir "%TARGET_FOLDER%"
    set FIRST_INSTALL=1
) else (
    echo [INFO] Doelmap bestaat reeds. Bestanden worden overschreven (behalve settings.json).
)

echo.
echo [1] 📁 Kopieer projectbestanden naar %TARGET_FOLDER%

xcopy /Y /E "%SOURCE_FOLDER%\*.py" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\*.md" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\*.bat" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\requirements.txt" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\label_settings.py" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\version.txt" "%TARGET_FOLDER%\" >nul

if exist "%SOURCE_FOLDER%\arial.ttf" (
    xcopy /Y "%SOURCE_FOLDER%\arial.ttf" "%TARGET_FOLDER%\" >nul
)

if exist "%SOURCE_FOLDER%\.env" (
    xcopy /Y "%SOURCE_FOLDER%\.env" "%TARGET_FOLDER%\" >nul
)

if %FIRST_INSTALL%==1 (
    if exist "%SOURCE_FOLDER%\settings.json" (
        echo [INFO] Eerste installatie – settings.json wordt gekopieerd.
        xcopy /Y "%SOURCE_FOLDER%\settings.json" "%TARGET_FOLDER%\" >nul
    )
) else (
    echo [INFO] Bestaande installatie – settings.json blijft behouden.
)

:: ====== Mappen kopiëren ======
if exist "%SOURCE_FOLDER%\label" (
    xcopy /E /I /Y "%SOURCE_FOLDER%\label" "%TARGET_FOLDER%\label" >nul
)
if exist "%SOURCE_FOLDER%\assets" (
    xcopy /E /I /Y "%SOURCE_FOLDER%\assets" "%TARGET_FOLDER%\assets" >nul
)
if exist "%SOURCE_FOLDER%\logs" (
    xcopy /E /I /Y "%SOURCE_FOLDER%\logs" "%TARGET_FOLDER%\logs" >nul
)
if exist "%SOURCE_FOLDER%\dist" (
    xcopy /E /I /Y "%SOURCE_FOLDER%\dist" "%TARGET_FOLDER%\dist" >nul
)
if exist "%SOURCE_FOLDER%\assets\css" (
    xcopy /E /I /Y "%SOURCE_FOLDER%\assets\css" "%TARGET_FOLDER%\assets\css" >nul
)

:: ====== Logboek schrijven ======
echo Laatste import: %DATE% %TIME% > "%TARGET_FOLDER%\import_log.txt"
echo [INFO] Bestanden geïnstalleerd naar: %TARGET_FOLDER%

:: ====== Snelkoppeling maken op bureaublad ======
set SHORTCUT_NAME=Artikelzoeker
set SHORTCUT_PATH=%USERPROFILE%\Desktop\%SHORTCUT_NAME%.lnk
set TARGET_EXE=%TARGET_FOLDER%\dist\ArticleSearch\ArticleSearch.exe

if exist "%TARGET_EXE%" (
    echo.
    echo 🧷 Snelkoppeling aanmaken op bureaublad...

    powershell -ExecutionPolicy Bypass -NoProfile -Command ^
    "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');" ^
    "$s.TargetPath='%TARGET_EXE%';" ^
    "$s.WorkingDirectory='%TARGET_FOLDER%\dist\ArticleSearch';" ^
    "$s.IconLocation='%TARGET_EXE%';" ^
    "$s.Save()"

    echo ✅ Snelkoppeling aangemaakt: %SHORTCUT_PATH%
    echo.
    echo ✅ Artikelzoeker starten...
    start "" "%TARGET_EXE%"
) else (
    echo ⚠️ Geen uitvoerbaar bestand gevonden in dist\ArticleSearch
)

pause
endlocal
