@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

:: ------------------------------------------------------------
::  build_installer9.bat  (robust; geen FOR /F voor versie)
:: ------------------------------------------------------------

:: [0] Python kiezen (venv eerst)
set "VENV_DIR=%CD%\.venv\Scripts"
if not exist "%VENV_DIR%\python.exe" set "VENV_DIR=%CD%\Scripts"
if exist "%VENV_DIR%\python.exe" (set "PYTHON_EXE=%VENV_DIR%\python.exe") else (set "PYTHON_EXE=python")

:: PATH opschonen (haal user-Pythons weg)
set "PATH=%VENV_DIR%;%VENV_DIR%\..;%VENV_DIR%\Scripts;%PATH%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312\Scripts;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313\Scripts;=%"

echo [info] Python executable: %PYTHON_EXE%
"%PYTHON_EXE%" -V

:: simpele diagnostiek (via tijdelijk .py)
set "PY_DIAG=%TEMP%\__diag_tmp.py"
> "%PY_DIAG%" echo import sys, site
>>"%PY_DIAG%" echo up=getattr(site,'getusersitepackages',lambda:'n/a')()
>>"%PY_DIAG%" echo print("[diag] exe=",sys.executable)
>>"%PY_DIAG%" echo print("[diag] base_prefix=",sys.base_prefix)
>>"%PY_DIAG%" echo print("[diag] ENABLE_USER_SITE=",getattr(site,'ENABLE_USER_SITE','n/a'))
>>"%PY_DIAG%" echo print("[diag] usersite_path=",up)
>>"%PY_DIAG%" echo print("[diag] usersite_in_sys_path=",isinstance(up,str) and (up in sys.path))
"%PYTHON_EXE%" "%PY_DIAG%"
del /q "%PY_DIAG%" >nul 2>&1

:: [1] Versie bumpen
set /p PART_TO_BUMP=Welke versie wil je verhogen? (patch/minor/major) : 
if "%PART_TO_BUMP%"=="" set "PART_TO_BUMP=patch"
echo [0] 🔁 Versie verhogen via bump_version.py (%PART_TO_BUMP%)...
"%PYTHON_EXE%" bump_version.py %PART_TO_BUMP% || (echo ❌ Fout bij het verhogen van de versie.& pause & exit /b 1)

:: [2] Versie lezen (zonder FOR /F; via temp-bestand)
set "PY_READV=%TEMP%\__read_version_tmp.py"
set "VER_TXT=%TEMP%\__version_out.txt"
del /q "%PY_READV%" "%VER_TXT%" >nul 2>&1
> "%PY_READV%" echo import re,io
>>"%PY_READV%" echo t=open(r'version.py','r',encoding='utf-8').read()
>>"%PY_READV%" echo m=re.search(r"__version__\s*=\s*'([^']+)'",t)
>>"%PY_READV%" echo open(r'%VER_TXT%','w',encoding='utf-8').write(m.group(1) if m else "0.0.0")
"%PYTHON_EXE%" "%PY_READV%" || (echo ❌ Kon versie niet bepalen via Python.& del /q "%PY_READV%" >nul 2^>^&1 & pause & exit /b 1)
del /q "%PY_READV%" >nul 2>&1
set "VERSION="
set /p VERSION=<"%VER_TXT%"
del /q "%VER_TXT%" >nul 2>&1
if not defined VERSION (echo ❌ Kon versie niet lezen.& pause & exit /b 1)
echo [1] 🔎 Versie gedetecteerd: %VERSION%

:: [3] Projectvariabelen
set "PROJECT_NAME=ArticleSearch"
set "SPEC_FILE=SearchArticle.spec"
set "DIST_FOLDER=dist"
set "BUILD_FOLDER=%PROJECT_NAME%_%VERSION%"
set "ABS_BUILD=%CD%\%DIST_FOLDER%\%BUILD_FOLDER%"
set "INITIAL_EXE=%DIST_FOLDER%\%PROJECT_NAME%\%PROJECT_NAME%.exe"
set "LOGFILE=build_log.txt"

:: [4] Opruimen
echo [2] 🧹 Opruimen...
if exist build rmdir /S /Q build
if exist "%DIST_FOLDER%" rmdir /S /Q "%DIST_FOLDER%"
if exist __pycache__ rmdir /S /Q __pycache__
del /q "warn-*.txt" >nul 2>&1

:: [5] Vereisten & PyInstaller
echo [3] 🔧 Pip/vereisten...
"%PYTHON_EXE%" -m pip install --upgrade pip || (echo ❌ pip upgrade faalde.& pause & exit /b 1)
"%PYTHON_EXE%" -m pip install -r requirements.txt || (echo ❌ pip install -r faalde.& pause & exit /b 1)
"%PYTHON_EXE%" -c "import PyInstaller" >nul 2>&1 || (
  echo [3b] 📦 PyInstaller installeren...
  "%PYTHON_EXE%" -m pip install "pyinstaller==6.11.1" "pyinstaller-hooks-contrib==2025.0" || (echo ❌ Installatie PyInstaller faalde.& pause & exit /b 1)
)

echo --- Build gestart op %DATE% %TIME% --- >> "%LOGFILE%"

:: [6] PyInstaller build (onedir)
echo [4] 🛠 Bouwen met PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm "%SPEC_FILE%" || (echo ❌ PyInstaller build faalde.& pause & exit /b 1)
if not exist "%INITIAL_EXE%" (echo ❌ EXE niet gevonden op "%INITIAL_EXE%".& pause & exit /b 1)

:: [7] Hernoemen naar map met versie
if exist "%DIST_FOLDER%\%BUILD_FOLDER%" rmdir /S /Q "%DIST_FOLDER%\%BUILD_FOLDER%"
rename "%DIST_FOLDER%\%PROJECT_NAME%" "%BUILD_FOLDER%" >nul 2>&1
if errorlevel 1 (
  echo [rename] Fallback via robocopy...
  robocopy "%DIST_FOLDER%\%PROJECT_NAME%" "%DIST_FOLDER%\%BUILD_FOLDER%" /E /MOVE >nul
  if errorlevel 8 (echo ❌ Fallback kopie mislukt.& pause & exit /b 1)
  if exist "%DIST_FOLDER%\%PROJECT_NAME%" rmdir /S /Q "%DIST_FOLDER%\%PROJECT_NAME%"
)
if not exist "%DIST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe" (
  echo ❌ Na hernoemen ontbreekt %PROJECT_NAME%.exe in %DIST_FOLDER%\%BUILD_FOLDER%.
  pause & exit /b 1
)

:: [8] Extra assets kopiëren
echo [5] 📁 Assets kopiëren...
for %%D in (assets logs label docs translations) do (
  if exist "%%D" xcopy /E /I /Y "%%D" "%DIST_FOLDER%\%BUILD_FOLDER%\%%D" >nul
)
for %%F in (requirements.txt help.md settings.json) do (
  if exist "%%F" copy /Y "%%F" "%DIST_FOLDER%\%BUILD_FOLDER%\" >nul
)
> "%DIST_FOLDER%\%BUILD_FOLDER%\version.txt" echo %VERSION%

:: ---------- TOT HIER is de EXE klaar in dist\ArticleSearch_%VERSION% ----------

echo(
set "MAKE_INSTALLER="
set /p MAKE_INSTALLER=Ook Inno Setup installer bouwen? [J/N] : 
if /I "%MAKE_INSTALLER%"=="J" (set "DO_ISCC=1") else (set "DO_ISCC=0")
if "%DO_ISCC%"=="0" goto DONE

:: [9] Installer script genereren
set "ISS_FILE=%DIST_FOLDER%\installer.iss"
if not exist "%DIST_FOLDER%" mkdir "%DIST_FOLDER%" >nul 2>&1
del /q "%ISS_FILE%" >nul 2>&1
echo [6] 📝 Installer-script aanmaken...

>>"%ISS_FILE%" echo [Setup]
>>"%ISS_FILE%" echo AppId={{A1B2C3D4-E5F6-47A8-9023-ABCDEF123456}
>>"%ISS_FILE%" echo AppName=ArticleSearch
>>"%ISS_FILE%" echo AppVersion=%VERSION%
>>"%ISS_FILE%" echo DefaultDirName=C:\ArticleSearch
>>"%ISS_FILE%" echo DisableDirPage=yes
>>"%ISS_FILE%" echo DefaultGroupName=ArticleSearch
>>"%ISS_FILE%" echo OutputDir=%DIST_FOLDER%
>>"%ISS_FILE%" echo OutputBaseFilename=ArticleSearchSetup_%VERSION%
>>"%ISS_FILE%" echo Compression=lzma
>>"%ISS_FILE%" echo SolidCompression=yes
>>"%ISS_FILE%" echo Uninstallable=yes
>>"%ISS_FILE%" echo CreateAppDir=yes
>>"%ISS_FILE%" echo PrivilegesRequired=admin
>>"%ISS_FILE%" echo SetupIconFile="%CD%\assets\logo.ico"
>>"%ISS_FILE%" echo(
>>"%ISS_FILE%" echo [Files]
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\ArticleSearch.exe"; DestDir: "{app}"; Flags: ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\settings.json";   DestDir: "{app}"; Flags: onlyifdoesntexist
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\version.txt";     DestDir: "{app}"; Flags: ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\docs\help.md";    DestDir: "{app}"; Flags: ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\assets\*";        DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\label\*";         DestDir: "{app}\label"; Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\logs\*";          DestDir: "{app}\logs";  Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\docs\*";          DestDir: "{app}\docs";  Flags: recursesubdirs createallsubdirs ignoreversion
>>"%ISS_FILE%" echo Source: "%ABS_BUILD%\translations\*";  DestDir: "{app}\translations"; Flags: recursesubdirs createallsubdirs ignoreversion
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
  type installer_code.isl >> "%ISS_FILE%"
)

:: [10] Inno Setup compileren
echo [7] 🔨 Inno Setup compileren...
set "ISCC_EXE="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"

if not defined ISCC_EXE goto NO_ISCC
"%ISCC_EXE%" "%ISS_FILE%"
if errorlevel 1 goto ISCC_FAIL
echo ✅ Installer aangemaakt in %DIST_FOLDER%.
goto DONE

:NO_ISCC
echo [FOUT] Inno Setup Compiler ^(ISCC.exe^) niet gevonden!
goto DONE

:ISCC_FAIL
echo [FOUT] Inno Setup compile mislukt. Zie "%ISS_FILE%".
goto DONE

:DONE
echo(
echo 📂 Output: %DIST_FOLDER%\%BUILD_FOLDER%
echo 💡 Start de app vanaf die map: "%DIST_FOLDER%\%BUILD_FOLDER%\ArticleSearch.exe"
echo --- Build voltooid op %DATE% %TIME% --- >> "%LOGFILE%"
pause
