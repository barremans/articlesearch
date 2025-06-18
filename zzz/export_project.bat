@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: === Timestamp aanmaken ===
for /f "tokens=1-3 delims=/- " %%a in ('date /t') do (
    set jaar=%%c & set maand=%%b & set dag=%%a
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set uur=%%a & set minuut=%%b
)
if 1%uur% LSS 20 set uur=0%uur%
if 1%minuut% LSS 20 set minuut=0%minuut%
set TIMESTAMP=%jaar%%maand%%dag%-%uur%%minuut%

:: === Instellingen ===
set "SOURCE_FOLDER=C:\SearchArticle"
set "DIST_FOLDER=%SOURCE_FOLDER%\dist"
set "ZIP_NAME=export_SearchArticle_%TIMESTAMP%.zip"
set "ZIP_PATH=%DIST_FOLDER%\%ZIP_NAME%"

echo.
echo [INFO] Project:       %SOURCE_FOLDER%
echo [INFO] Zip-output:    %ZIP_PATH%

:: === Maak dist-map aan indien nodig ===
if not exist "%DIST_FOLDER%" (
    mkdir "%DIST_FOLDER%"
    echo [INFO] Aangemaakte folder: %DIST_FOLDER%
)

:: === Bouw tijdelijk PowerShell-script ===
set "PS_SCRIPT=%TEMP%\export_searcharticle.ps1"
(
  echo # Exporteer alle bestanden behalve de dist-map
  echo $files = Get-ChildItem -Path '%SOURCE_FOLDER%' -Recurse -File ^
         ^| Where-Object { $_.FullName -notmatch '\\dist\\' }
  echo Compress-Archive -Path $files.FullName -DestinationPath '%ZIP_PATH%' -Force
) > "%PS_SCRIPT%"

:: === Voer het PowerShell-script uit ===
echo [0] 📦 ZIP maken van gehele project (excl. dist)...
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" ^
  -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"

if errorlevel 1 (
    echo ❌ Fout bij aanmaken ZIP.
    del "%PS_SCRIPT%"
    pause
    exit /b 1
)

:: === Opruimen tijdelijke PS ===
del "%PS_SCRIPT%"

echo ✅ ZIP succesvol aangemaakt: %ZIP_PATH%
pause
endlocal
