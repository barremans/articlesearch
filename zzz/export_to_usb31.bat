@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: === 0. Meet de starttijd in epoch-seconden via PowerShell ===
for /f %%a in ('powershell -NoProfile -Command "[int]((Get-Date).ToUniversalTime() - [datetime]''1970-01-01'').TotalSeconds"') do set "STARTSEC=%%a"

:: === 1. Timestamp aanmaken via WMIC ===
for /f %%i in ('wmic os get LocalDateTime ^| find "."') do set ldt=%%i
set TIMESTAMP=%ldt:~0,8%-%ldt:~8,6%

:: === 2. Instellingen ===
set "SOURCE_FOLDER=C:\SearchArticle"
set "VENV_PATH=%SOURCE_FOLDER%\venv"

:KIES_USB
set /p USB_DRIVE=Geef de stationsletter van de USB-stick (bv. E): 
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
echo [0] Pip freeze uitvoeren (vereist geactiveerde venv)...
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
    echo [!] requirements.txt NIET aangemaakt.
)

:: === 5. Kopiëren met voortgang en snelheid (excl. map "zzz") ===
echo [1] Kopiëren van projectmap (excl. map "zzz") met voortgang...
robocopy "%SOURCE_FOLDER%" "%USB_FOLDER%" /E /XD "%SOURCE_FOLDER%\zzz" /ETA /FP
if errorlevel 8 (
    echo [FOUT] Er trad een fout op tijdens het kopiëren van de projectmap.
) else (
    echo [OK] Alle bestanden en submappen zonder "zzz" gekopieerd.
)

:: === 6. (Optioneel) Virtuele omgeving meenemen ===
if exist "%VENV_PATH%" (
    echo [2] Kopiëren van virtuele omgeving...
    robocopy "%VENV_PATH%" "%USB_FOLDER%\venv" /E /ETA /FP
    if errorlevel 8 (
        echo [WAARSCHUWING] Fout bij kopiëren virtuele omgeving.
    ) else (
        echo [OK] Virtuele omgeving gekopieerd.
    )
) else (
    echo [INFO] Geen virtuele omgeving om mee te nemen.
)

:: === 7. Logbestand schrijven ===
echo [3] Logbestand schrijven...
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
    echo Map "zzz" uitgesloten
) > "%USB_FOLDER%\export_log.txt"
echo [OK] Logbestand aangemaakt.

:: === 8. Meet de eindtijd en toon totale duur ===
for /f %%a in ('powershell -NoProfile -Command "[int]((Get-Date).ToUniversalTime() - [datetime]''1970-01-01'').TotalSeconds"') do set "ENDSEC=%%a"
set /A DURATION=ENDSEC - STARTSEC
if %DURATION% LSS 0 set /A DURATION+=86400

:: Bereken uren:minuten:seconden
set /A h=DURATION/3600
set /A m=(DURATION%%3600)/60
set /A s=DURATION%%60

echo.
echo Start timestamp: %STARTSEC%  sec
echo Eind timestamp : %ENDSEC%  sec
echo Totale duur    : %h% uur %m% min %s% sec

echo.
echo Export succesvol afgerond.
echo Project staat nu op: "%USB_FOLDER%"

pause
endlocal
