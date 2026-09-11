@echo off
setlocal EnableExtensions

:: ============================================================
:: SearchArticle export naar USB
:: - zzz wordt NIET gekopieerd
:: - .venv en venv worden uitgesloten van hoofdcopy
:: - voorkeur voor .venv als beide bestaan
:: - gekozen virtuele omgeving wordt exact 1 keer gekopieerd
:: - requirements.txt wordt aangemaakt
:: - totale uitvoeringstijd wordt getoond
:: ============================================================


:: === 0. Starttijd opslaan ===

for /f %%a in ('powershell -NoProfile -Command "[int64]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"') do set "STARTSEC=%%a"


:: === 1. Timestamp aanmaken ===

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TIMESTAMP=%%i"


:: === 2. Instellingen ===

set "SOURCE_FOLDER=C:\searcharticle_code"

set "DOT_VENV_PATH=%SOURCE_FOLDER%\.venv"
set "VENV_NORMAL_PATH=%SOURCE_FOLDER%\venv"

set "VENV_PATH="
set "VENV_NAME="


:: === 3. Virtuele omgeving detecteren ===

if exist "%DOT_VENV_PATH%\Scripts\python.exe" (
    set "VENV_PATH=%DOT_VENV_PATH%"
    set "VENV_NAME=.venv"
) else if exist "%VENV_NORMAL_PATH%\Scripts\python.exe" (
    set "VENV_PATH=%VENV_NORMAL_PATH%"
    set "VENV_NAME=venv"
)


:: === 4. USB-station kiezen ===

:KIES_USB

echo.
set /p "USB_DRIVE=Geef de stationsletter van de USB-stick (bv. E): "

if not defined USB_DRIVE (
    echo [FOUT] Geen stationsletter ingevoerd. Probeer opnieuw.
    goto KIES_USB
)

:: Eventuele dubbele punt verwijderen
set "USB_DRIVE=%USB_DRIVE::=%"

:: Alleen eerste teken gebruiken
set "USB_DRIVE=%USB_DRIVE:~0,1%"

if not exist "%USB_DRIVE%:\" (
    echo [FOUT] Stationsletter %USB_DRIVE%: bestaat niet of is niet toegankelijk.
    echo Probeer opnieuw.
    goto KIES_USB
)


:: === 5. Doelmap bepalen ===

set "USB_FOLDER=%USB_DRIVE%:\export_SearchArticle_%TIMESTAMP%"

echo.
echo ============================================================
echo SearchArticle export
echo ============================================================
echo.
echo [INFO] Bronmap : "%SOURCE_FOLDER%"
echo [INFO] USB     : "%USB_DRIVE%:"
echo [INFO] Doelmap : "%USB_FOLDER%"
echo.

if defined VENV_PATH (
    echo [INFO] Virtuele omgeving gevonden:
    echo        "%VENV_PATH%"
) else (
    echo [WAARSCHUWING] Geen .venv of venv gevonden.
)

echo.


:: === 6. Controle bronmap ===

if not exist "%SOURCE_FOLDER%\" (
    echo [FOUT] Bronmap bestaat niet:
    echo "%SOURCE_FOLDER%"
    goto EINDE_MET_FOUT
)


:: === 7. Doelmap aanmaken ===

if not exist "%USB_FOLDER%" (
    echo [INFO] Doelmap bestaat niet. Wordt aangemaakt...

    mkdir "%USB_FOLDER%"

    if errorlevel 1 (
        echo [FOUT] Doelmap kon niet worden aangemaakt.
        goto EINDE_MET_FOUT
    )

) else (

    echo [INFO] Doelmap bestaat reeds.
    echo [INFO] Bestaande bestanden kunnen worden overschreven.
)

echo.


:: === 8. requirements.txt aanmaken ===

echo ============================================================
echo [0] Python dependencies exporteren
echo ============================================================
echo.

if defined VENV_PATH (

    echo [INFO] requirements.txt wordt aangemaakt via:
    echo        "%VENV_PATH%\Scripts\python.exe"
    echo.

    "%VENV_PATH%\Scripts\python.exe" -m pip freeze > "%SOURCE_FOLDER%\requirements.txt"

    if exist "%SOURCE_FOLDER%\requirements.txt" (
        echo [OK] requirements.txt aangemaakt.
    ) else (
        echo [WAARSCHUWING] requirements.txt kon niet worden aangemaakt.
    )

) else (

    echo [WAARSCHUWING] Geen virtuele omgeving gevonden.
    echo [WAARSCHUWING] requirements.txt wordt niet aangemaakt.

)

echo.


:: === 9. Projectmap kopieren ===
:: zzz, .venv en venv worden hier altijd uitgesloten

echo ============================================================
echo [1] Projectmap kopieren
echo ============================================================
echo.

echo [INFO] Uitgesloten:
echo        "%SOURCE_FOLDER%\zzz"
echo        "%SOURCE_FOLDER%\.venv"
echo        "%SOURCE_FOLDER%\venv"
echo.

robocopy "%SOURCE_FOLDER%" "%USB_FOLDER%" ^
    /E ^
    /XD "%SOURCE_FOLDER%\zzz" "%SOURCE_FOLDER%\.venv" "%SOURCE_FOLDER%\venv" ^
    /ETA ^
    /FP

set "ROBO_PROJECT=%ERRORLEVEL%"

if %ROBO_PROJECT% GEQ 8 goto PROJECT_COPY_FOUT

echo.
echo [OK] Projectbestanden succesvol gekopieerd.
echo [OK] Map zzz uitgesloten.
echo [OK] .venv en venv uitgesloten van hoofdcopy.
echo.

goto PROJECT_COPY_KLAAR


:PROJECT_COPY_FOUT

echo.
echo [FOUT] Ernstige fout tijdens kopieren van de projectmap.
echo [FOUT] Robocopy exit code: %ROBO_PROJECT%
echo.

goto EINDE_MET_FOUT


:PROJECT_COPY_KLAAR


:: === 10. Virtuele omgeving exact 1 keer kopieren ===

echo ============================================================
echo [2] Virtuele omgeving kopieren
echo ============================================================
echo.

if defined VENV_PATH (

    echo [INFO] Bron:
    echo        "%VENV_PATH%"
    echo.
    echo [INFO] Doel:
    echo        "%USB_FOLDER%\%VENV_NAME%"
    echo.

    robocopy "%VENV_PATH%" "%USB_FOLDER%\%VENV_NAME%" ^
        /E ^
        /ETA ^
        /FP

    set "ROBO_VENV=%ERRORLEVEL%"

    if %ROBO_VENV% GEQ 8 goto VENV_COPY_FOUT

    echo.
    echo [OK] Virtuele omgeving succesvol gekopieerd.
    echo [OK] Gekopieerde omgeving: %VENV_NAME%
    echo.

    goto VENV_KLAAR

) else (

    echo [INFO] Geen .venv of venv gevonden.
    echo [INFO] Geen virtuele omgeving gekopieerd.
    echo.

    goto VENV_KLAAR
)


:VENV_COPY_FOUT

echo.
echo [WAARSCHUWING] Fout tijdens kopieren van de virtuele omgeving.
echo [WAARSCHUWING] Robocopy exit code: %ROBO_VENV%
echo [WAARSCHUWING] Projectbestanden zelf zijn reeds gekopieerd.
echo.


:VENV_KLAAR


:: === 11. Eindtijd meten ===

for /f %%a in ('powershell -NoProfile -Command "[int64]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"') do set "ENDSEC=%%a"

set /a DURATION=ENDSEC-STARTSEC

set /a HOURS=DURATION/3600
set /a MINUTES=(DURATION%%3600)/60
set /a SECONDS=DURATION%%60


:: === 12. Logbestand schrijven ===

echo ============================================================
echo [3] Logbestand schrijven
echo ============================================================
echo.

(
    echo SearchArticle export
    echo ====================
    echo.
    echo Exportdatum: %DATE%
    echo Exporttijd: %TIME%
    echo.
    echo Bronmap: %SOURCE_FOLDER%
    echo Bestemming: %USB_FOLDER%
    echo.
    echo Map zzz uitgesloten: JA
    echo Map .venv uitgesloten van hoofdcopy: JA
    echo Map venv uitgesloten van hoofdcopy: JA
    echo.
    echo Totale duur: %HOURS% uur %MINUTES% min %SECONDS% sec
    echo.
) > "%USB_FOLDER%\export_log.txt"


if exist "%SOURCE_FOLDER%\requirements.txt" (
    echo requirements.txt aanwezig: JA>> "%USB_FOLDER%\export_log.txt"
) else (
    echo requirements.txt aanwezig: NEE>> "%USB_FOLDER%\export_log.txt"
)


if defined VENV_PATH (
    echo Virtuele omgeving gevonden: JA>> "%USB_FOLDER%\export_log.txt"
    echo Virtuele omgeving bron: %VENV_PATH%>> "%USB_FOLDER%\export_log.txt"
    echo Virtuele omgeving naam: %VENV_NAME%>> "%USB_FOLDER%\export_log.txt"

    if exist "%USB_FOLDER%\%VENV_NAME%\" (
        echo Virtuele omgeving gekopieerd: JA>> "%USB_FOLDER%\export_log.txt"
    ) else (
        echo Virtuele omgeving gekopieerd: NEE>> "%USB_FOLDER%\export_log.txt"
    )

) else (

    echo Virtuele omgeving gevonden: NEE>> "%USB_FOLDER%\export_log.txt"
    echo Virtuele omgeving gekopieerd: NEE>> "%USB_FOLDER%\export_log.txt"

)


if exist "%USB_FOLDER%\export_log.txt" (
    echo [OK] Logbestand aangemaakt.
) else (
    echo [WAARSCHUWING] Logbestand kon niet worden aangemaakt.
)

echo.


:: === 13. Eindresultaat ===

echo ============================================================
echo EXPORT SUCCESVOL AFGEROND
echo ============================================================
echo.
echo Project staat op:
echo "%USB_FOLDER%"
echo.
echo Totale duur:
echo %HOURS% uur %MINUTES% min %SECONDS% sec
echo.
echo ============================================================
echo.

pause
goto EINDE


:: === 14. Foutafhandeling ===

:EINDE_MET_FOUT

for /f %%a in ('powershell -NoProfile -Command "[int64]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"') do set "ENDSEC=%%a"

set /a DURATION=ENDSEC-STARTSEC
set /a HOURS=DURATION/3600
set /a MINUTES=(DURATION%%3600)/60
set /a SECONDS=DURATION%%60

echo.
echo ============================================================
echo EXPORT AFGEBROKEN MET EEN FOUT
echo ============================================================
echo.
echo Totale duur tot fout:
echo %HOURS% uur %MINUTES% min %SECONDS% sec
echo.
echo Controleer bovenstaande foutmeldingen.
echo.

pause


:EINDE

endlocal