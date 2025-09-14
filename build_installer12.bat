@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem -----------------------------------------------------------------
rem  build_installer12.bat  — fixeert "0.0.0" door robuust versielezen
rem -----------------------------------------------------------------

rem [0] Python kiezen (venv eerst) + PATH opschonen
set "VENV_DIR=%CD%\.venv\Scripts"
if not exist "%VENV_DIR%\python.exe" set "VENV_DIR=%CD%\Scripts"
if exist "%VENV_DIR%\python.exe" (set "PYTHON_EXE=%VENV_DIR%\python.exe") else (set "PYTHON_EXE=python")

set "PATH=%VENV_DIR%;%VENV_DIR%\..;%VENV_DIR%\Scripts;%PATH%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312\Scripts;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313\Scripts;=%"

echo [info] Python executable: %PYTHON_EXE%
"%PYTHON_EXE%" -V
"%PYTHON_EXE%" -c "import sys,site; up=getattr(site,'getusersitepackages',lambda:'n/a')(); print('[diag] exe=',sys.executable); print('[diag] base_prefix=',sys.base_prefix); print('[diag] ENABLE_USER_SITE=',getattr(site,'ENABLE_USER_SITE','n/a')); print('[diag] usersite_path=',up); print('[diag] usersite_in_sys_path=', (isinstance(up,str) and (up in sys.path)))"

rem [1] Versie ophogen (patch/minor/major)
set /p PART_TO_BUMP=Welke versie wil je verhogen? (patch/minor/major) : 
if "%PART_TO_BUMP%"=="" set "PART_TO_BUMP=patch"
echo [0] 🔁 Versie verhogen via bump_version.py (%PART_TO_BUMP%)...
"%PYTHON_EXE%" bump_version.py %PART_TO_BUMP% || (echo ❌ Fout bij versie verhogen.& pause & exit /b 1)

rem [2] Versie lezen — ROBUUST (importlib) + regex fallback
set "PY_READV=%TEMP%\__read_version_tmp.py"
set "VER_TXT=%TEMP%\__version_out.txt"
del /q "%PY_READV%" "%VER_TXT%" >nul 2>&1
> "%PY_READV%" echo import importlib.util, io, os, re
>>"%PY_READV%" echo p=os.path.abspath('version.py'); v="0.0.0"
>>"%PY_READV%" echo try:
>>"%PY_READV%" echo ^    spec=importlib.util.spec_from_file_location("ver",p)
>>"%PY_READV%" echo ^    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
>>"%PY_READV%" echo ^    v=getattr(m,"__version__","0.0.0")
>>"%PY_READV%" echo except Exception:
>>"%PY_READV%" echo ^    t=io.open(p,'r',encoding='utf-8').read()
>>"%PY_READV%" echo ^    m=re.search(r"__version__\s*=\s*['\^\"\s]*([0-9]+(?:\.[0-9]+){1,2})",t)
>>"%PY_READV%" echo ^    v=m.group(1) if m else "0.0.0"
>>"%PY_READV%" echo io.open(r'%VER_TXT%','w',encoding='utf-8').write(v)
"%PYTHON_EXE%" "%PY_READV%" || (echo ❌ Kon versie niet bepalen via Python.& del /q "%PY_READV%" >nul & pause & exit /b 1)
del /q "%PY_READV%" >nul 2>&1
set "VERSION=" & set /p VERSION=<"%VER_TXT%"
del /q "%VER_TXT%" >nul 2>&1
if not defined VERSION (echo ❌ Kon versie niet lezen.& pause & exit /b 1)
echo [1] 🔎 Versie gedetecteerd: %VERSION%

rem [3] Projectconfig
set "PROJECT_NAME=ArticleSearch"
set "SPEC_FILE=SearchArticle.spec"
set "DIST_FOLDER=dist"
set "BUILD_FOLDER=%PROJECT_NAME%_%VERSION%"
set "ABS_BUILD_FOLDER=%CD%\%DIST_FOLDER%\%BUILD_FOLDER%"
set "INITIAL_EXE=%DIST_FOLDER%\%PROJECT_NAME%\%PROJECT_NAME%.exe"
set "ISS_FILE=%DIST_FOLDER%\installer.iss"
set "SETUP_EXE=%PROJECT_NAME%Setup_%VERSION%.exe"
set "LOGFILE=build_log.txt"

rem [4] Opruimen
echo [2] 🧹 Opruimen...
if exist build rmdir /S /Q build
if exist "%DIST_FOLDER%" rmdir /S /Q "%DIST_FOLDER%"
if exist __pycache__ rmdir /S /Q __pycache__
del /q "warn-*.txt" >nul 2>&1

rem [5] Vereisten & PyInstaller
echo [3] 🔧 Pip/vereisten...
"%PYTHON_EXE%" -m pip install --upgrade pip || (echo ❌ pip upgrade faalde.& pause & exit /b 1)
"%PYTHON_EXE%" -m pip install -r requirements.txt || (echo ❌ pip install -r faalde.& pause & exit /b 1)
"%PYTHON_EXE%" -c "import PyInstaller" >nul 2>&1 || (
  echo [3b] 📦 PyInstaller installeren...
  "%PYTHON_EXE%" -m pip install "pyinstaller==6.11.1" "pyinstaller-hooks-contrib==2025.0" || (echo ❌ Installatie PyInstaller faalde.& pause & exit /b 1)
)

echo --- Build gestart op %DATE% %TIME% --- >> "%LOGFILE%"

rem [6] PyInstaller build (onedir)
echo [4] 🛠 Bouwen met PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm "%SPEC_FILE%" || (echo ❌ PyInstaller build faalde.& pause & exit /b 1)
if not exist "%INITIAL_EXE%" (echo ❌ EXE niet gevonden op "%INITIAL_EXE%".& pause & exit /b 1)

rem [7] Hernoemen naar map met versie
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

rem [8] Extra assets kopiëren (handig voor testen zonder installer)
echo [5] 📁 Assets kopiëren...
for %%D in (assets logs label docs translations) do (
  if exist "%%D" xcopy /E /I /Y "%%D" "%DIST_FOLDER%\%BUILD_FOLDER%\%%D" >nul
)
for %%F in (requirements.txt help.md settings.json) do (
  if exist "%%F" copy /Y "%%F" "%DIST_FOLDER%\%BUILD_FOLDER%\" >nul
)
> "%DIST_FOLDER%\%BUILD_FOLDER%\version.txt" echo %VERSION%

echo(
set "MAKE_INSTALLER="
set /p MAKE_INSTALLER=Ook Inno Setup installer bouwen? [J/N] : 
if /I "%MAKE_INSTALLER%"=="J" (set "DO_ISCC=1") else (set "DO_ISCC=0")
if "%DO_ISCC%"=="0" goto DONE

rem [9] Installer .iss genereren (neemt alles recursief mee)
if not exist "%DIST_FOLDER%" mkdir "%DIST_FOLDER%" >nul 2>&1
del /q "%ISS_FILE%" >nul 2>&1
echo [6] 📝 Installer-script aanmaken...

>>"%ISS_FILE%" echo [Setup]
>>"%ISS_FILE%" echo AppId={{A1B2C3D4-E5F6-47A8-9023-ABCDEF123456}
>>"%ISS_FILE%" echo AppName=%PROJECT_NAME%
>>"%ISS_FILE%" echo AppVersion=%VERSION%
>>"%ISS_FILE%" echo AppVerName=%PROJECT_NAME% %VERSION%
>>"%ISS_FILE%" echo DefaultDirName=C:\%PROJECT_NAME%
>>"%ISS_FILE%" echo DisableDirPage=yes
>>"%ISS_FILE%" echo DefaultGroupName=%PROJECT_NAME%
>>"%ISS_FILE%" echo OutputDir=%DIST_FOLDER%
>>"%ISS_FILE%" echo OutputBaseFilename=%PROJECT_NAME%Setup_%VERSION%
>>"%ISS_FILE%" echo Compression=lzma
>>"%ISS_FILE%" echo SolidCompression=yes
>>"%ISS_FILE%" echo Uninstallable=yes
>>"%ISS_FILE%" echo CreateAppDir=yes
>>"%ISS_FILE%" echo PrivilegesRequired=admin
>>"%ISS_FILE%" echo ArchitecturesInstallIn64BitMode=x64
>>"%ISS_FILE%" echo SetupIconFile="%ABS_BUILD_FOLDER%\assets\logo.ico"
>>"%ISS_FILE%" echo DirExistsWarning=no

>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [InstallDelete]
>>"%ISS_FILE%" echo Type: filesandordirs; Name: "{app}\_internal"
>>"%ISS_FILE%" echo Type: filesandordirs; Name: "{app}\__pycache__"

>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Files]
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Icons]
>>"%ISS_FILE%" echo Name: "{group}\%PROJECT_NAME%"; Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\logo.ico"
>>"%ISS_FILE%" echo Name: "{commondesktop}\%PROJECT_NAME%"; Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Tasks]
>>"%ISS_FILE%" echo Name: "desktopicon"; Description: "Maak een snelkoppeling op het bureaublad"; GroupDescription: "Extra opties:"

>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Run]
>>"%ISS_FILE%" echo Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; Description: "Start %PROJECT_NAME%"; Flags: nowait postinstall skipifsilent

rem [10] Inno Setup compileren
echo [7] 🔨 Inno Setup compileren...
set "ISCC_EXE="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE (
  echo ⚠️  ISCC.exe niet gevonden. Installeer Inno Setup 6.
  goto DONE
)
"%ISCC_EXE%" "%ISS_FILE%"
if errorlevel 1 (
  echo [FOUT] Inno Setup compile mislukt. Zie "%ISS_FILE%".
  goto DONE
)
echo ✅ Installer aangemaakt: %DIST_FOLDER%\%PROJECT_NAME%Setup_%VERSION%.exe

:DONE
echo(
echo 📂 Output: %DIST_FOLDER%\%PROJECT_NAME%_%VERSION%
echo 💡 Test direct: "%DIST_FOLDER%\%PROJECT_NAME%_%VERSION%\%PROJECT_NAME%.exe"
echo --- Build voltooid op %DATE% %TIME% --- >> "%LOGFILE%"
pause
