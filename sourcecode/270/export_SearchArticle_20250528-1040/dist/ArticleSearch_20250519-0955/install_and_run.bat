@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

echo.
echo === 📥 Installatie vanaf USB of externe bron ===
echo.

:: ====== USB-driveletter vragen ======
set /p USB_DRIVE=Geef de stationsletter van de USB-stick (bv. E): 
set USB_PATH=%USB_DRIVE%:\

:: ====== Zoek laatste SearchArticle_* folder ======
set "SOURCE_FOLDER="
for /f "delims=" %%d in ('dir "%USB_PATH%ArticleSearch_*" /ad /b /o-d') do (
    set "SOURCE_FOLDER=%USB_PATH%%%d"
    goto found
)

:found
if not defined SOURCE_FOLDER (
    echo ❌ Geen geldige map gevonden met naam 'SearchArticle_*' op %USB_PATH%
    pause
    exit /b
)

echo [INFO] Geselecteerde bronmap: %SOURCE_FOLDER%

:: ====== Doelmap opvragen ======
set /p TARGET_FOLDER=Geef de DOELMAP op (bv. C:\SearchArticle): 
if not exist "%TARGET_FOLDER%" (
    echo [INFO] Doelmap bestaat niet. Aanmaken...
    mkdir "%TARGET_FOLDER%"
)

:: ====== Bestanden kopiëren ======
echo.
echo [1] 📁 Kopieer projectbestanden naar harde schijf...
xcopy /Y /E "%SOURCE_FOLDER%\*.py" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\*.md" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\*.bat" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\requirements.txt" "%TARGET_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\label_settings.py" "%TARGET_FOLDER%\" >nul
if exist "%SOURCE_FOLDER%\version.txt" (
    xcopy /Y "%SOURCE_FOLDER%\version.txt" "%TARGET_FOLDER%\" >nul
)

if exist "%SOURCE_FOLDER%\arial.ttf" (
    xcopy /Y "%SOURCE_FOLDER%\arial.ttf" "%TARGET_FOLDER%\" >nul
)

if exist "%SOURCE_FOLDER%\settings.json" (
    xcopy /Y "%SOURCE_FOLDER%\settings.json" "%TARGET_FOLDER%\" >nul
)

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
if exist "%SOURCE_FOLDER%\css" (
    xcopy /E /I /Y "%SOURCE_FOLDER%\css" "%TARGET_FOLDER%\css" >nul
)

:: ====== Logboek schrijven ======
echo Laatste import: %DATE% %TIME% > "%TARGET_FOLDER%\import_log.txt"
echo [INFO] Bestanden geïnstalleerd naar: %TARGET_FOLDER%

:: ====== Start EXE indien beschikbaar ======
if exist "%TARGET_FOLDER%\dist\ArticleSearch\ArticleSearch.exe" (
    echo.
    echo ✅ Artikelzoeker starten...
    start "" "%TARGET_FOLDER%\dist\ArticleSearch\ArticleSearch.exe"
) else (
    echo ⚠️ Geen uitvoerbaar bestand gevonden in dist\
)

pause
endlocal
