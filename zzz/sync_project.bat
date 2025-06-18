@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: === Instellingen ===
set PROJECT_DIR=%~dp0
set VENV_DIR=%PROJECT_DIR%venv

echo [INFO] Project importeren vanuit: %PROJECT_DIR%

:: === 0. Oude venv opruimen (optioneel) ===
if exist "%VENV_DIR%" (
    echo [WAARSCHUWING] Virtuele omgeving bestaat al!
    set /p DELETE_VENV=Wil je deze verwijderen en opnieuw opbouwen? (j/n): 
    if /I "!DELETE_VENV!"=="j" (
        echo Verwijderen...
        rmdir /S /Q "%VENV_DIR%"
    ) else (
        echo Virtuele omgeving wordt behouden.
    )
)

:: === 1. Virtuele omgeving aanmaken ===
echo [1] 🐍 Nieuwe virtuele omgeving aanmaken in: %VENV_DIR%
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo ❌ Fout bij aanmaken van venv. Is Python geïnstalleerd?
    pause
    exit /b 1
)

:: === 2. Activatie + dependencies installeren ===
call "%VENV_DIR%\Scripts\activate.bat"

if exist "%PROJECT_DIR%\requirements.txt" (
    echo [2] 📦 requirements.txt gevonden, dependencies installeren...
    pip install -r "%PROJECT_DIR%\requirements.txt"
    if errorlevel 1 (
        echo ❌ Fout bij installeren van packages.
        pause
        exit /b 1
    )
    echo ✅ Dependencies geïnstalleerd.
) else (
    echo ⚠️ Geen requirements.txt gevonden in: %PROJECT_DIR%
)

:: === 3. Bevestiging ===
echo.
echo ✅ Project klaar voor gebruik!
echo Activeer met: call venv\Scripts\activate.bat
pause
endlocal
