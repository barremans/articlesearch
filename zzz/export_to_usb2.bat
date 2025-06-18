@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: === 1. Timestamp aanmaken via WMIC (uniform format) ===
for /f %%i in ('wmic os get LocalDateTime ^| find "."') do set ldt=%%i
:: ldt = e.g. 20250601HHMMSS.xxxxxx+timezone
set TIMESTAMP=%ldt:~0,8%-%ldt:~8,6%

:: === 2. Instellingen ===
set "SOURCE_FOLDER=C:\SearchArticle"
set "VENV_PATH=%SOURCE_FOLDER%\venv"

:KIES_USB
set /p USB_DRIVE=Geef de stationsletter van de USB-stick (bv. E): 
:: Zorg dat de gebruiker een letter invoert en dat de schijf bestaat
if "%USB_DRIVE%"=="" (
    echo [FOUT] Geen stationsletter ingevoerd. Probeer opnieuw.
    goto KIES_USB
)
if not exist "%USB_DRIVE%:\" (
    echo [FOUT] Stationsletter %USB_DRIVE%: bestaat niet of is niet toegankelijk. Probeer opnieuw.
    goto KIES_USB
)

set "USB_FOLDER=%USB_DRIVE%:\export_SearchArticle_%TIMESTAMP%"

echo.
echo [INFO] Exporteren van project: "%SOURCE_FOLDER%"
echo [INFO] Doelmap: "%USB_FOLDER%"

:: === 3. Doelmap aanmaken ===
if not exist "%USB_FOLDER%" (
    echo [INFO] Doelmap bestaat niet. Wordt aangemaakt...
    mkdir "%USB_FOLDER%"
) else (
    echo [INFO] Doelmap bestaat al. Bestanden kunnen worden overschreven.
)

:: === 4. Export dependencies ===
echo [0] 🔧 Pip freeze uitvoeren (vereist geactiveerde venv)...
if exist "%VENV_PATH%\Scripts\activate.bat" (
    call "%VENV_PATH%\Scripts\activate.bat"
    pip freeze > "%SOURCE_FOLDER%\requirements.txt"
    if exist "%SOURCE_FOLDER%\requirements.txt" (
        echo [OK] requirements.txt aangemaakt.
    ) else (
        echo [FOUT] requirements.txt kon niet worden aangemaakt.
    )
) else (
    echo [WAARSCHUWING] Geen virtuele omgeving gevonden in: "%VENV_PATH%"
    echo [!] requirements.txt NIET aangemaakt. Controleer handmatig.
)

:: === 5. Kopieer hoofdbestanden met Robocopy ===
echo [1] 📄 Kopiëren van scripts, instellingen en vereisten met robocopy...
robocopy "%SOURCE_FOLDER%" "%USB_FOLDER%" *.py *.md *.bat *.txt /E /NFL /NDL /NJH /NJS
if errorlevel 8 (
    echo [FOUT] Er trad een fout op tijdens het kopiëren van hoofdbestanden.
) else (
    echo [OK] Hoofdbestanden gekopieerd.
)

:: Extra losse bestanden
for %%f in ("settings.json" "arial.ttf") do (
    if exist "%SOURCE_FOLDER%\%%~f" (
        copy /Y "%SOURCE_FOLDER%\%%~f" "%USB_FOLDER%\"
        echo [INFO] "%%~f" gekopieerd.
    )
)

:: === 6. Kopieer submappen ===
echo [2] 📁 Kopiëren van submappen (assets, logs, dist...)...
for %%d in (assets assets\css logs label dist) do (
    if exist "%SOURCE_FOLDER%\%%d" (
        robocopy "%SOURCE_FOLDER%\%%d" "%USB_FOLDER%\%%d" /E /NFL /NDL /NJH /NJS
        if errorlevel 8 (
            echo [WAARSCHUWING] Fout bij kopiëren van map: %%d
        ) else (
            echo [OK] Map "%%d" gekopieerd.
        )
    ) else (
        echo [INFO] Submap "%%d" bestaat niet, wordt overgeslagen.
    )
)

:: === 7. Virtuele omgeving meenemen (optioneel) ===
if exist "%VENV_PATH%" (
    echo [3] 🐍 Kopiëren van virtuele omgeving...
    robocopy "%VENV_PATH%" "%USB_FOLDER%\venv" /E /NFL /NDL /NJH /NJS
    if errorlevel 8 (
        echo [WAARSCHUWING] Er trad een fout op tijdens het kopiëren van de virtuele omgeving.
    ) else (
        echo [OK] Virtuele omgeving gekopieerd.
    )
) else (
    echo [INFO] Geen virtuele omgeving om mee te nemen.
)

:: === 8. Logbestand schrijven ===
echo [4] 🗒 Logbestand schrijven...
(
    echo Laatste export: %DATE% %TIME%
    echo Bronmap: %SOURCE_FOLDER%
    echo Bestemming: %USB_FOLDER%
    echo Virtuele omgeving meegenomen: %VENV_PATH%
    echo requirements.txt aanwezig:
    if exist "%SOURCE_FOLDER%\requirements.txt" (
        echo   JA
    ) else (
        echo   NEE
    )
) > "%USB_FOLDER%\export_log.txt"
echo [OK] Logbestand aangemaakt.

echo.
echo ✅ Export succesvol afgerond.
echo ➡️  Project staat nu op: "%USB_FOLDER%"

pause
endlocal
