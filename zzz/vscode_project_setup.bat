@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

echo.
echo === 💻 VS Code Project Setup voor Artikelzoeker ===
echo.

:: === Stap 1: Vraag doelmap op ===
set "DEFAULT_DIR=C:\Dev\SearchArticle"
set /p TARGET_DIR=Voer doelmap in voor installatie [%DEFAULT_DIR%]: 
if "%TARGET_DIR%"=="" set TARGET_DIR=%DEFAULT_DIR%

echo [INFO] Project wordt geïnstalleerd naar: %TARGET_DIR%

:: === Stap 2: Maak doelmap aan indien nodig ===
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

:: === Stap 3: Kopieer projectbestanden ===
echo [INFO] Kopiëren van projectbestanden...
xcopy /Y /E /I * "%TARGET_DIR%" >nul

:: === Stap 4: Python venv aanmaken ===
echo [INFO] Virtuele omgeving aanmaken...
cd /d "%TARGET_DIR%"
python -m venv .venv

if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtuele omgeving kon niet worden aangemaakt. Is Python geïnstalleerd?
    pause
    exit /b 1
)

:: === Stap 5: Dependencies installeren ===
echo [INFO] Virtuele omgeving activeren en packages installeren...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

:: === Stap 6: VS Code extensies installeren (optioneel) ===
if exist extensions.txt (
    echo [INFO] VS Code extensies installeren...
    for /f %%e in (extensions.txt) do (
        code --install-extension %%e
    )
)

:: === Stap 7: Open VS Code in deze map ===
echo.
echo ✅ Setup voltooid! Project wordt geopend in Visual Studio Code...
code .

pause
endlocal
