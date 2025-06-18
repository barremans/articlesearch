@echo off
setlocal enabledelayedexpansion

:: === Timestamp genereren ===
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set dag=%%a
    set maand=%%b
    set jaar=%%c
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set uur=%%a
    set minuut=%%b
)
if 1%uur% LSS 20 set uur=0%uur%
if 1%minuut% LSS 20 set minuut=0%minuut%
set TIMESTAMP=%jaar%%maand%%dag%-%uur%%minuut%
set "LOGFILE=build_log.txt"

:: === Projectinstellingen ===
set "PROJECT_NAME=ArticleSearch"
set "BASE_FOLDER=dist\%PROJECT_NAME%"
set "BUILD_FOLDER=%BASE_FOLDER%_%TIMESTAMP%"
set "ZIP_PATH=dist\%PROJECT_NAME%_%TIMESTAMP%.zip"
set "SPEC_FILE=SearchArticle.spec"
set "EXE_PATH=%BASE_FOLDER%\%PROJECT_NAME%.exe"

echo [0] 🧹 Opruimen van vorige tijdelijke folders...
if exist build rmdir /S /Q build
if exist __pycache__ rmdir /S /Q __pycache__

echo [1] 🔧 Pip en vereisten controleren...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo. >> %LOGFILE%
echo --- Build gestart op %DATE% %TIME% --- >> %LOGFILE%
echo [1] Pip packages geverifieerd. >> %LOGFILE%

echo [2] 🛠 Bouwen met PyInstaller...
pyinstaller --clean --noconfirm "%SPEC_FILE%"
if errorlevel 1 (
    echo ❌ Fout tijdens build met PyInstaller. >> %LOGFILE%
    echo ❌ Buildproces afgebroken.
    pause
    exit /b 1
)

:: ✅ Check of EXE correct gegenereerd is
if not exist "%EXE_PATH%" (
    echo ❌ Artikelzoeker EXE niet aangetroffen op verwachte locatie: %EXE_PATH%
    echo ❌ Controleer je .spec-bestand of PyInstaller output. >> %LOGFILE%
    pause
    exit /b 1
)

:: Hernoem volledige map (dist\ArticleSearch -> dist\ArticleSearch_YYYYMMDD-HHMM)
echo [INFO] Hernoemen outputmap naar timestamped folder...
rename "%BASE_FOLDER%" "%PROJECT_NAME%_%TIMESTAMP%"

:: Update pad
set "BUILD_FOLDER=dist\%PROJECT_NAME%_%TIMESTAMP%"

echo.
echo [3] 📁 Assets en extra bestanden toevoegen...
if exist assets (
    xcopy /E /I /Y assets "%BUILD_FOLDER%\assets" >nul
)
if exist assets\css (
    xcopy /E /I /Y assets\css "%BUILD_FOLDER%\assets\css" >nul
)
if exist logs (
    xcopy /E /I /Y logs "%BUILD_FOLDER%\logs" >nul
)
if exist label (
    xcopy /E /I /Y label "%BUILD_FOLDER%\label" >nul
)

copy /Y settings.json "%BUILD_FOLDER%\" >nul
copy /Y help.md "%BUILD_FOLDER%\" >nul
copy /Y requirements.txt "%BUILD_FOLDER%\" >nul

:: ✅ Versiebestand kopiëren indien aanwezig
if exist releases\latest\version.txt (
    copy /Y releases\latest\version.txt "%BUILD_FOLDER%\" >nul
)

:: ✅ install_and_run.bat ook meenemen
if exist install_and_run.bat (
    copy /Y install_and_run.bat "%BUILD_FOLDER%\" >nul
)

echo [INFO] Assets gekopieerd. >> %LOGFILE%

echo.
echo [4] 📂 Buildmap openen...
start "" "%BUILD_FOLDER%"

echo.
echo [5] 📦 ZIP maken van buildmap...
powershell -Command "Compress-Archive -Path '%BUILD_FOLDER%\*' -DestinationPath '%ZIP_PATH%' -Force"

echo ✅ Artikelzoeker is succesvol gebouwd en verpakt als: %ZIP_PATH%
echo [INFO] ZIP-archief aangemaakt: %ZIP_PATH% >> %LOGFILE%
echo --- Einde build op %DATE% %TIME% --- >> %LOGFILE%

pause
