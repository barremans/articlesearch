@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: === [0] Vraag welk deel van de versie moet worden verhoogd ===
set /p PART_TO_BUMP=Welke versie wil je verhogen? (patch/minor/major) : 
if "%PART_TO_BUMP%"=="" set PART_TO_BUMP=patch

echo [0] 🔁 Versie verhogen via bump_version.py (%PART_TO_BUMP%)...
python bump_version.py %PART_TO_BUMP%
if errorlevel 1 (
    echo ❌ Fout bij het verhogen van de versie.
    pause
    exit /b 1
)

:: === [1] Versie uitlezen uit version.py ===
for /f "tokens=2 delims== " %%v in ('findstr "__version__" version.py') do (
    set VERSION=%%~v
)
set VERSION=%VERSION:"=%
set VERSION=%VERSION: =%

:: === Projectconfiguratie ===
set "PROJECT_NAME=ArticleSearch"
set "SPEC_FILE=SearchArticle.spec"
set "DIST_FOLDER=dist"
set "BUILD_FOLDER=%PROJECT_NAME%_%VERSION%"
set "EXE_PATH=%DIST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe"
set "ABS_BUILD_FOLDER=%CD%\%DIST_FOLDER%\%BUILD_FOLDER%"
set "LOGFILE=build_log.txt"

:: === Icoon instellen vanuit vaste map ===
set "ABS_ICON_PATH=C:\searcharticle\assets\logo.ico"
if not exist "%ABS_ICON_PATH%" (
    echo ❌ Icoonbestand niet gevonden op %ABS_ICON_PATH%
    pause
    exit /b 1
)

echo [2] 🧹 Opruimen van vorige tijdelijke folders...
if exist build rmdir /S /Q build
if exist __pycache__ rmdir /S /Q __pycache__

echo [3] 🔧 Pip en vereisten controleren...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo. >> "%LOGFILE%"
echo --- Build gestart op %DATE% %TIME% --- >> "%LOGFILE%"

echo [4] 🛠 Bouwen met PyInstaller...
pyinstaller --clean --noconfirm "%SPEC_FILE%"
if errorlevel 1 (
    echo ❌ Fout tijdens build met PyInstaller. >> "%LOGFILE%"
    pause
    exit /b 1
)

if not exist "%DIST_FOLDER%\%PROJECT_NAME%\%PROJECT_NAME%.exe" (
    echo ❌ EXE niet gevonden.
    pause
    exit /b 1
)

:: Herbenoem outputmap naar versie
if exist "%DIST_FOLDER%\%BUILD_FOLDER%" rmdir /S /Q "%DIST_FOLDER%\%BUILD_FOLDER%"
rename "%DIST_FOLDER%\%PROJECT_NAME%" "%BUILD_FOLDER%"
if errorlevel 1 (
    echo ❌ Kan map niet hernoemen. Mogelijk in gebruik.
    pause
    exit /b 1
)

echo [5] 📁 Extra bestanden kopiëren...
for %%d in (assets,assets\css,logs,label,docs) do (
    if exist "%%d" (
        xcopy /E /I /Y "%%d" "%DIST_FOLDER%\%BUILD_FOLDER%\%%d" >nul
    )
)

for %%f in (requirements.txt help.md) do (
    if exist "%%f" (
        copy /Y "%%f" "%DIST_FOLDER%\%BUILD_FOLDER%\" >nul
    )
)

:: settings.json kopiëren indien aanwezig
if exist settings.json (
    copy /Y settings.json "%DIST_FOLDER%\%BUILD_FOLDER%\" >nul
)

:: versie vastleggen
echo %VERSION% > "%DIST_FOLDER%\%BUILD_FOLDER%\version.txt"

echo ✅ Assets en metadata toegevoegd. >> "%LOGFILE%"

:: === [6] Installer-script aanmaken ===
set "INSTALLER_OUTPUT=%DIST_FOLDER%"
set "SETUP_EXE=ArticleSearchSetup_%VERSION%.exe"
set "ISS_FILE=%INSTALLER_OUTPUT%\installer.iss"

> "%ISS_FILE%" echo [Setup]
>> "%ISS_FILE%" echo AppId={{A1B2C3D4-E5F6-47A8-9023-ABCDEF123456}
>> "%ISS_FILE%" echo AppName=ArticleSearch
>> "%ISS_FILE%" echo AppVersion=%VERSION%
>> "%ISS_FILE%" echo DefaultDirName=C:\ArticleSearch
>> "%ISS_FILE%" echo DisableDirPage=yes
>> "%ISS_FILE%" echo DefaultGroupName=ArticleSearch
>> "%ISS_FILE%" echo OutputDir=%INSTALLER_OUTPUT%
>> "%ISS_FILE%" echo OutputBaseFilename=%SETUP_EXE:.exe=%  
>> "%ISS_FILE%" echo Compression=lzma
>> "%ISS_FILE%" echo SolidCompression=yes
>> "%ISS_FILE%" echo Uninstallable=yes
>> "%ISS_FILE%" echo CreateAppDir=yes
>> "%ISS_FILE%" echo PrivilegesRequired=none
>> "%ISS_FILE%" echo SetupIconFile="%ABS_ICON_PATH%"

>> "%ISS_FILE%" echo.
>> "%ISS_FILE%" echo [Files]
>> "%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; Excludes: settings.json

if exist "%ABS_BUILD_FOLDER%\settings.json" (
    >> "%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\settings.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
) else (
    echo ⚠️ settings.json niet gevonden – wordt niet toegevoegd aan installer.
)

>> "%ISS_FILE%" echo.
>> "%ISS_FILE%" echo [Icons]
>> "%ISS_FILE%" echo Name: "{userdesktop}\ArticleSearch"; Filename: "{app}\ArticleSearch.exe"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

>> "%ISS_FILE%" echo.
>> "%ISS_FILE%" echo [Tasks]
>> "%ISS_FILE%" echo Name: "desktopicon"; Description: "Maak een snelkoppeling op het bureaublad"; GroupDescription: "Extra opties:"

>> "%ISS_FILE%" echo.
>> "%ISS_FILE%" echo [Run]
>> "%ISS_FILE%" echo Filename: "{app}\ArticleSearch.exe"; Description: "Start ArticleSearch"; Flags: nowait postinstall skipifsilent

:: Optionele code toevoegen indien aanwezig
if exist installer_code.isl (
    >> "%ISS_FILE%" echo.
    >> "%ISS_FILE%" echo [Code]
    >> "%ISS_FILE%" type installer_code.isl >> "%ISS_FILE%"
)

:: === [7] Compileer de installer ===
echo [7] 🔨 Inno Setup compileren...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "%ISS_FILE%"
    echo ✅ Installer aangemaakt: %INSTALLER_OUTPUT%\%SETUP_EXE%
) else (
    echo ⚠️ Inno Setup Compiler (ISCC.exe) niet gevonden!
)

echo 📦 Installer build voltooid.
echo --- Build klaar op %DATE% %TIME% --- >> "%LOGFILE%"
pause
