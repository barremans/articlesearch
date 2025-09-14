:: =========================
:: build_installer8.bat  (V6.0.3)
:: Schone build + Inno Setup.
:: =========================
@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

:: --- [0] Venv kiezen (.venv preferred) ---
set "VENV_DIR=%CD%\.venv\Scripts"
if not exist "%VENV_DIR%\python.exe" set "VENV_DIR=%CD%\Scripts"
if exist "%VENV_DIR%\python.exe" (set "PYTHON_EXE=%VENV_DIR%\python.exe") else (set "PYTHON_EXE=python")

:: --- [0a] PATH sane maken (System32 NIET verwijderen) ---
set "PATH=%VENV_DIR%;%VENV_DIR%\..;%VENV_DIR%\Scripts;%PATH%"
set PYTHONNOUSERSITE=1
set PYTHONPATH=
:: strip expliciete pcadmin-Pythonpaden
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312\Scripts;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312\Library\bin;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313\Scripts;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313\Library\bin;=%"

echo [info] Python executable: %PYTHON_EXE%
"%PYTHON_EXE%" -V

:: --- Diagnose / fail-fast ---
"%PYTHON_EXE%" -c "import sys,site; up=getattr(site,'getusersitepackages',lambda:'n/a')(); active=isinstance(up,str) and (up in sys.path); print('[diag] exe=',sys.executable); print('[diag] base_prefix=',sys.base_prefix); print('[diag] ENABLE_USER_SITE=',getattr(site,'ENABLE_USER_SITE','n/a')); print('[diag] usersite_path=',up); print('[diag] usersite_in_sys_path=',active)"
call "%PYTHON_EXE%" -c "import sys; raise SystemExit(0 if 'pcadmin' not in sys.base_prefix.lower() else 1)" && goto :BASE_OK
echo ❌ Verkeerde interpreter-basis (pcadmin). Stop.
pause
exit /b 1
:BASE_OK

:: --- [0b] VC-runtime local (geen fout als niet aanwezig) ---
for %%D in (vcruntime140.dll vcruntime140_1.dll msvcp140.dll) do (
  if exist "%WINDIR%\System32\%%D" copy /Y "%WINDIR%\System32\%%D" "%VENV_DIR%\" >nul 2>&1
)

:: --- [1] Versie ophogen (patch/minor/major) ---
set /p PART_TO_BUMP=Welke versie wil je verhogen? (patch/minor/major) : 
if "%PART_TO_BUMP%"=="" set "PART_TO_BUMP=patch"
echo [0] 🔁 Versie verhogen via bump_version.py (%PART_TO_BUMP%)...
"%PYTHON_EXE%" bump_version.py %PART_TO_BUMP%
if errorlevel 1 (
  echo ❌ Fout bij het verhogen van de versie.
  pause & exit /b 1
)

:: --- [2] Versie lezen (veilig, geen FOR/backticks/blocks) ---
set "VER_OUT=%TEMP%\__ver_out.txt"
"%PYTHON_EXE%" -c "import importlib.util as u; s=u.spec_from_file_location('v','version.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print(getattr(m,'__version__','0.0.0'))" > "%VER_OUT%" 2>nul
set "VERSION="
set /p VERSION=<"%VER_OUT%"
del "%VER_OUT%" >nul 2>&1
if not defined VERSION (
  echo ❌ Kon versie niet lezen.
  pause & exit /b 1
)
echo [1] 🔎 Versie gedetecteerd: %VERSION%

:: --- [3] Projectconfig ---
set "PROJECT_NAME=ArticleSearch"
set "SPEC_FILE=SearchArticle.spec"
set "DIST_FOLDER=dist"
set "BUILD_FOLDER=%PROJECT_NAME%_%VERSION%"
set "LOGFILE=build_log.txt"

set "INITIAL_EXE_PATH=%DIST_FOLDER%\%PROJECT_NAME%\%PROJECT_NAME%.exe"
set "ABS_BUILD_FOLDER=%CD%\%DIST_FOLDER%\%BUILD_FOLDER%"

set "INSTALLER_OUTPUT=%DIST_FOLDER%"
set "ISS_FILE=%INSTALLER_OUTPUT%\installer.iss"
set "OUTPUT_BASE=ArticleSearchSetup_%VERSION%"
set "SETUP_EXE=%OUTPUT_BASE%.exe"

:: --- [4] Opruimen ---
echo [2] 🧹 Opruimen...
if exist build rd /s /q build
if exist "%DIST_FOLDER%" rd /s /q "%DIST_FOLDER%"
if exist __pycache__ rd /s /q __pycache__
if exist "%ISS_FILE%" del /Q "%ISS_FILE%" >nul 2>&1

:: --- [5] Vereisten ---
echo [3] 🔧 Pip/vereisten...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (echo ❌ Pip install faalde. & pause & exit /b 1)

:: Zorg dat PyInstaller aanwezig is
"%PYTHON_EXE%" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
  echo [3b] 📦 PyInstaller installeren...
  "%PYTHON_EXE%" -m pip install "pyinstaller==6.11.1" "pyinstaller-hooks-contrib==2025.0"
  if errorlevel 1 (echo ❌ Installatie van PyInstaller faalde. & pause & exit /b 1)
)

echo --- Build gestart op %DATE% %TIME% --- >> "%LOGFILE%"

:: --- [6] PyInstaller build ---
echo [4] 🛠 Bouwen met PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm "%SPEC_FILE%"
if errorlevel 1 (echo ❌ Fout tijdens build met PyInstaller. >> "%LOGFILE%" & pause & exit /b 1)

if not exist "%INITIAL_EXE_PATH%" (
  echo ❌ EXE niet gevonden op "%INITIAL_EXE_PATH%".
  pause & exit /b 1
)

:: --- [7] Hernoemen naar versie ---
if exist "%DIST_FOLDER%\%BUILD_FOLDER%" rd /s /q "%DIST_FOLDER%\%BUILD_FOLDER%"
ren "%DIST_FOLDER%\%PROJECT_NAME%" "%BUILD_FOLDER%" >nul 2>&1
if errorlevel 1 (
  echo [rename] Fallback via robocopy...
  robocopy "%DIST_FOLDER%\%PROJECT_NAME%" "%DIST_FOLDER%\%BUILD_FOLDER%" /E /MOVE >nul
  if errorlevel 8 (echo ❌ Fallback kopie mislukt. & pause & exit /b 1)
  if exist "%DIST_FOLDER%\%PROJECT_NAME%" rd /s /q "%DIST_FOLDER%\%PROJECT_NAME%"
)

if not exist "%DIST_FOLDER%\%BUILD_FOLDER%\ArticleSearch.exe" (
  echo ❌ Na hernoemen ontbreekt ArticleSearch.exe in %DIST_FOLDER%\%BUILD_FOLDER%.
  pause & exit /b 1
)

:: --- [8] Extra assets ---
echo [5] 📁 Extra bestanden kopiëren...
for %%d in (assets,assets\css,logs,label,docs,translations) do (
  if exist "%%d" xcopy /E /I /Y "%%d" "%DIST_FOLDER%\%BUILD_FOLDER%\%%d" >nul
)
for %%f in (requirements.txt help.md) do (
  if exist "%%f" copy /Y "%%f" "%DIST_FOLDER%\%BUILD_FOLDER%\" >nul
)
if exist settings.json copy /Y settings.json "%DIST_FOLDER%\%BUILD_FOLDER%\" >nul
echo %VERSION% > "%DIST_FOLDER%\%BUILD_FOLDER%\version.txt"
echo ✅ Assets en metadata toegevoegd. >> "%LOGFILE%"

:: --- [9] Inno Setup .iss genereren ---
echo [6] 📝 Installer-script aanmaken...
if not exist "%INSTALLER_OUTPUT%" md "%INSTALLER_OUTPUT%"

set "ABS_BUILD_FOLDER=%CD%\%DIST_FOLDER%\%BUILD_FOLDER%"
> "%ISS_FILE%"  echo [Setup]
>>"%ISS_FILE%" echo AppId={{A1B2C3D4-E5F6-47A8-9023-ABCDEF123456}
>>"%ISS_FILE%" echo AppName=ArticleSearch
>>"%ISS_FILE%" echo AppVersion=%VERSION%
>>"%ISS_FILE%" echo DefaultDirName=C:\ArticleSearch
>>"%ISS_FILE%" echo DisableDirPage=yes
>>"%ISS_FILE%" echo DefaultGroupName=ArticleSearch
>>"%ISS_FILE%" echo OutputDir="%INSTALLER_OUTPUT%"
>>"%ISS_FILE%" echo OutputBaseFilename=%OUTPUT_BASE%
>>"%ISS_FILE%" echo Compression=lzma
>>"%ISS_FILE%" echo SolidCompression=yes
>>"%ISS_FILE%" echo Uninstallable=yes
>>"%ISS_FILE%" echo CreateAppDir=yes
>>"%ISS_FILE%" echo PrivilegesRequired=admin
>>"%ISS_FILE%" echo SetupIconFile="%CD%\assets\logo.ico"
>>"%ISS_FILE%" echo(
>>"%ISS_FILE%" echo [Files]
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\ArticleSearch.exe"; DestDir: "{app}"; Flags: ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\settings.json"; DestDir: "{app}"; Flags: onlyifdoesntexist skipifsourcedoesntexist
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\version.txt"; DestDir: "{app}"; Flags: ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\docs\help.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\label\*"; DestDir: "{app}\label"; Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\logs\*"; DestDir: "{app}\logs"; Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\docs\*"; DestDir: "{app}\docs"; Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\translations\*"; DestDir: "{app}\translations"; Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo(
>>"%ISS_FILE%" echo [Icons]
>>"%ISS_FILE%" echo Name: "{group}\ArticleSearch"; Filename: "{app}\ArticleSearch.exe"; IconFilename: "{app}\assets\logo.ico"
>>"%ISS_FILE%" echo Name: "{commondesktop}\ArticleSearch"; Filename: "{app}\ArticleSearch.exe"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon
>>"%ISS_FILE%" echo(
>>"%ISS_FILE%" echo [Tasks]
>>"%ISS_FILE%" echo Name: "desktopicon"; Description: "Maak een snelkoppeling op het bureaublad"; GroupDescription: "Extra opties:"
>>"%ISS_FILE%" echo(
>>"%ISS_FILE%" echo [Run]
>>"%ISS_FILE%" echo Filename: "{app}\ArticleSearch.exe"; Description: "Start ArticleSearch"; Flags: nowait postinstall skipifsilent

if exist installer_code.isl (
  >>"%ISS_FILE%" echo(
  >>"%ISS_FILE%" echo [Code]
  >>"%ISS_FILE%" type installer_code.isl >> "%ISS_FILE%"
)

:: --- [10] Compileer Inno Setup ---
echo [7] 🔨 Inno Setup compileren...
set "ISCC_EXE="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"

if not defined ISCC_EXE (
  echo ❌ Inno Setup Compiler (ISCC.exe) niet gevonden!
  pause & exit /b 1
)

"%ISCC_EXE%" "%ISS_FILE%"
if errorlevel 1 (
  echo ❌ Inno Setup compile mislukt. Zie %ISS_FILE%.
  pause & exit /b 1
)

echo ✅ Installer aangemaakt: %INSTALLER_OUTPUT%\%SETUP_EXE%

echo(
echo 📂 Outputmap openen in Verkenner...
start "" "%DIST_FOLDER%\%BUILD_FOLDER%"

echo ✅ Build en installatiepakket succesvol afgerond.
echo --- Build voltooid op %DATE% %TIME% --- >> "%LOGFILE%"
pause
