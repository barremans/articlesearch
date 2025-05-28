@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: === Timestamp aanmaken ===
for /f "tokens=1-3 delims=/- " %%a in ('date /t') do (
    set jaar=%%c
    set maand=%%b
    set dag=%%a
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set uur=%%a
    set minuut=%%b
)
if 1%uur% LSS 20 set uur=0%uur%
if 1%minuut% LSS 20 set minuut=0%minuut%
set TIMESTAMP=%jaar%%maand%%dag%-%uur%%minuut%

:: === Instellingen ===
set SOURCE_FOLDER=C:\SearchArticle
set VENV_PATH=%SOURCE_FOLDER%\venv
set /p USB_DRIVE=Geef de stationsletter van de USB-stick (bv. E): 
set USB_FOLDER=%USB_DRIVE%:\export_SearchArticle_%TIMESTAMP%

echo.
echo [INFO] Exporteren van project: %SOURCE_FOLDER%
echo [INFO] Doelmap: %USB_FOLDER%

:: === Maak doelmap aan ===
if not exist "%USB_FOLDER%" (
    echo [INFO] Doelmap bestaat niet. Wordt aangemaakt...
    mkdir "%USB_FOLDER%"
)

:: === 0. Export dependencies ===
echo [0] 🔧 Pip freeze uitvoeren (vereist geactiveerde venv)...
if exist "%VENV_PATH%\Scripts\activate.bat" (
    call "%VENV_PATH%\Scripts\activate.bat"
    pip freeze > "%SOURCE_FOLDER%\requirements.txt"
    echo [OK] requirements.txt aangemaakt.
) else (
    echo [WAARSCHUWING] Geen virtuele omgeving gevonden in: %VENV_PATH%
    echo [!] requirements.txt NIET aangemaakt. Controleer handmatig.
)

:: === 1. Kopieer hoofdbestanden ===
echo [1] 📄 Kopiëren van scripts, instellingen en vereisten...
xcopy /Y /E "%SOURCE_FOLDER%\*.py" "%USB_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\*.md" "%USB_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\*.bat" "%USB_FOLDER%\" >nul
xcopy /Y "%SOURCE_FOLDER%\*.txt" "%USB_FOLDER%\" >nul
if exist "%SOURCE_FOLDER%\requirements.txt" (
    xcopy /Y "%SOURCE_FOLDER%\requirements.txt" "%USB_FOLDER%\" >nul
)

:: Extra bestanden
if exist "%SOURCE_FOLDER%\settings.json" (
    xcopy /Y "%SOURCE_FOLDER%\settings.json" "%USB_FOLDER%\" >nul
)
if exist "%SOURCE_FOLDER%\arial.ttf" (
    xcopy /Y "%SOURCE_FOLDER%\arial.ttf" "%USB_FOLDER%\" >nul
)

:: === 2. Kopieer mappen ===
echo [2] 📁 Kopiëren van submappen (assets, logs, dist...)...
for %%d in (assets,assets\css,logs,label,dist) do (
    if exist "%SOURCE_FOLDER%\%%d" (
        xcopy /E /I /Y "%SOURCE_FOLDER%\%%d" "%USB_FOLDER%\%%d" >nul
    )
)

:: === 3. Virtuele omgeving meenemen (optioneel) ===
if exist "%VENV_PATH%" (
    echo [3] 🐍 Kopiëren van virtuele omgeving...
    xcopy /E /I /Y "%VENV_PATH%" "%USB_FOLDER%\venv" >nul
) else (
    echo [INFO] Geen virtuele omgeving om mee te nemen.
)

:: === 4. Logboek schrijven ===
echo Laatste export: %DATE% %TIME% > "%USB_FOLDER%\export_log.txt"
echo Bronmap: %SOURCE_FOLDER% >> "%USB_FOLDER%\export_log.txt"
echo Bestemming: %USB_FOLDER% >> "%USB_FOLDER%\export_log.txt"
echo Virtuele omgeving meegenomen: %VENV_PATH% >> "%USB_FOLDER%\export_log.txt"
echo requirements.txt aanwezig: >> "%USB_FOLDER%\export_log.txt"
if exist "%SOURCE_FOLDER%\requirements.txt" (
    echo   JA >> "%USB_FOLDER%\export_log.txt"
) else (
    echo   NEE >> "%USB_FOLDER%\export_log.txt"
)

echo.
echo ✅ Export succesvol afgerond.
echo ➡️  Project staat nu op: %USB_FOLDER%
pause
endlocal
