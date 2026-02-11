@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem ===============================================================
rem build_installer13.bat — Build + Inno Setup installer generator
rem - Installeert ALTIJD in C:\ArticleSearch
rem - Admin vereist (geschikt voor Intune SYSTEM deployment)
rem - Optionele code signing hook
rem ===============================================================

rem [0] Basisconfig
set "PROJECT_NAME=ArticleSearch"
set "SPEC_FILE=SearchArticle.spec"
set "DIST_FOLDER=dist"
set "LOGFILE=build_log.txt"

rem Mapnamen die worden gemaakt:
rem   dist\ArticleSearch_<versie>\
rem Installer output:
rem   dist\ArticleSearchSetup_<versie>.exe

rem [1] Python selecteren (venv eerst) + PATH opschonen
set "PYTHON_EXE="
for %%P in ("%CD%\.venv\Scripts\python.exe" "%CD%\Scripts\python.exe") do (
  if exist "%%~fP" set "PYTHON_EXE=%%~fP"
)
if not defined PYTHON_EXE set "PYTHON_EXE=python"

rem Een paar bekende user-site paden weghalen om verrassingen te vermijden
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python312\Scripts;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313;=%"
set "PATH=%PATH:C:\Users\pcadmin\AppData\Local\Programs\Python\Python313\Scripts;=%"

echo [info] Python: %PYTHON_EXE%
"%PYTHON_EXE%" -V || (echo ❌ Geen werkende Python gevonden.& pause & exit /b 1)

rem [2] Versie verhogen (vraag: patch/minor/major)
set /p PART_TO_BUMP=Welke versie wil je verhogen? (patch/minor/major) : 
if "%PART_TO_BUMP%"=="" set "PART_TO_BUMP=patch"
echo [0] 🔁 Versie verhogen via bump_version.py (%PART_TO_BUMP%)...
"%PYTHON_EXE%" bump_version.py %PART_TO_BUMP%
if errorlevel 1 (
  echo ❌ Fout bij het verhogen van de versie.
  pause & exit /b 1
)

rem [3] Versie robuust uitlezen uit version.py (importlib + regex fallback)
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
"%PYTHON_EXE%" "%PY_READV%" || (echo ❌ Versie uitlezen faalde.& del /q "%PY_READV%" >nul & pause & exit /b 1)
del /q "%PY_READV%" >nul 2>&1
set "VERSION=" & set /p VERSION=<"%VER_TXT%"
del /q "%VER_TXT%" >nul 2>&1
if not defined VERSION (echo ❌ Kon versie niet lezen.& pause & exit /b 1)

echo [1] 🔎 Versie: %VERSION%

rem [4] Afgeleide paden
set "BUILD_FOLDER=%PROJECT_NAME%_%VERSION%"
set "ABS_BUILD_FOLDER=%CD%\%DIST_FOLDER%\%BUILD_FOLDER%"
set "INITIAL_EXE=%DIST_FOLDER%\%PROJECT_NAME%\%PROJECT_NAME%.exe"
set "ISS_FILE=%DIST_FOLDER%\installer.iss"
set "SETUP_EXE=%PROJECT_NAME%Setup_%VERSION%.exe"

rem [5] Clean
echo [2] 🧹 Opruimen...
if exist build rmdir /S /Q build
if exist "%DIST_FOLDER%" rmdir /S /Q "%DIST_FOLDER%"
if exist __pycache__ rmdir /S /Q __pycache__
del /q "warn-*.txt" >nul 2>&1

rem [6] Vereisten + PyInstaller
echo [3] 🔧 Pip & vereisten...
"%PYTHON_EXE%" -m pip install --upgrade pip || (echo ❌ pip upgrade faalde.& pause & exit /b 1)
if exist requirements.txt (
  "%PYTHON_EXE%" -m pip install -r requirements.txt || (echo ❌ pip install -r faalde.& pause & exit /b 1)
)

"%PYTHON_EXE%" -c "import PyInstaller" >nul 2>&1 || (
  echo [3b] 📦 PyInstaller installeren...
  "%PYTHON_EXE%" -m pip install "pyinstaller==6.11.1" "pyinstaller-hooks-contrib==2025.0" || (echo ❌ Installatie PyInstaller faalde.& pause & exit /b 1)
)

echo --- Build gestart op %DATE% %TIME% --- >> "%LOGFILE%"

rem [7] Build met PyInstaller (onedir via je SPEC)
echo [4] 🛠 PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm "%SPEC_FILE%"
if errorlevel 1 (echo ❌ PyInstaller build faalde.& pause & exit /b 1)
if not exist "%INITIAL_EXE%" (echo ❌ EXE niet gevonden op "%INITIAL_EXE%".& pause & exit /b 1)

rem [8] Hernoemen naar map met versie
if exist "%DIST_FOLDER%\%BUILD_FOLDER%" rmdir /S /Q "%DIST_FOLDER%\%BUILD_FOLDER%"
rename "%DIST_FOLDER%\%PROJECT_NAME%" "%BUILD_FOLDER%" >nul 2>&1
if errorlevel 1 (
  echo [rename] Fallback via robocopy...
  robocopy "%DIST_FOLDER%\%PROJECT_NAME%" "%DIST_FOLDER%\%BUILD_FOLDER%" /E /MOVE >nul
  if errorlevel 8 (echo ❌ Fallback kopie mislukt.& pause & exit /b 1)
  if exist "%DIST_FOLDER%\%PROJECT_NAME%" rmdir /S /Q "%DIST_FOLDER%\%PROJECT_NAME%"
)

if not exist "%DIST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe" (
  echo ❌ %PROJECT_NAME%.exe ontbreekt in %DIST_FOLDER%\%BUILD_FOLDER%.
  pause & exit /b 1
)

rem [9] Assets kopiëren (optioneel)
echo [5] 📁 Assets kopiëren...
for %%D in (assets logs label docs translations) do (
  if exist "%%D" xcopy /E /I /Y "%%D" "%DIST_FOLDER%\%BUILD_FOLDER%\%%D" >nul
)
for %%F in (requirements.txt help.md settings.json) do (
  if exist "%%F" copy /Y "%%F" "%DIST_FOLDER%\%BUILD_FOLDER%\" >nul
)
> "%DIST_FOLDER%\%BUILD_FOLDER%\version.txt" echo %VERSION%

rem [10] Installer maken?
set "DO_ISCC=1"
set /p MAKE_INSTALLER=Ook Inno Setup installer bouwen? [J/N] : 
if /I "%MAKE_INSTALLER%"=="N" set "DO_ISCC=0"
if "%DO_ISCC%"=="0" goto SHOW_OUTPUT

rem [11] Inno Setup script genereren (harde install dir + admin)
if not exist "%DIST_FOLDER%" mkdir "%DIST_FOLDER%" >nul 2>&1
del /q "%ISS_FILE%" >nul 2>&1
echo [6] 📝 Installer-script genereren...

>>"%ISS_FILE%" echo ; --- Inno Setup script, automatisch gegenereerd ---
>>"%ISS_FILE%" echo [Setup]
>>"%ISS_FILE%" echo AppId={{A1B2C3D4-E5F6-47A8-9023-ABCDEF123456}
>>"%ISS_FILE%" echo AppName=%PROJECT_NAME%
>>"%ISS_FILE%" echo AppVersion=%VERSION%
>>"%ISS_FILE%" echo AppVerName=%PROJECT_NAME% %VERSION%
>>"%ISS_FILE%" echo DefaultDirName=C:\%PROJECT_NAME%
>>"%ISS_FILE%" echo DisableDirPage=yes
>>"%ISS_FILE%" echo UsePreviousAppDir=no
>>"%ISS_FILE%" echo DefaultGroupName=%PROJECT_NAME%
>>"%ISS_FILE%" echo DisableProgramGroupPage=yes
>>"%ISS_FILE%" echo OutputDir=%DIST_FOLDER%
>>"%ISS_FILE%" echo OutputBaseFilename=%PROJECT_NAME%Setup_%VERSION%
>>"%ISS_FILE%" echo Compression=lzma
>>"%ISS_FILE%" echo SolidCompression=yes
>>"%ISS_FILE%" echo Uninstallable=yes
>>"%ISS_FILE%" echo CreateAppDir=yes
>>"%ISS_FILE%" echo PrivilegesRequired=admin
>>"%ISS_FILE%" echo ArchitecturesInstallIn64BitMode=x64
>>"%ISS_FILE%" echo DirExistsWarning=no
>>"%ISS_FILE%" echo WizardStyle=modern
>>"%ISS_FILE%" echo SetupIconFile="%ABS_BUILD_FOLDER%\assets\logo.ico"

rem --- Optioneel: code signing (vul je eigen SignTool hier in) ---
rem Voorbeeld (uitcommentarieerd). Zet je eigen paden/subject/thumbprint:
rem >>"%ISS_FILE%" echo SignTool=msbuild;...\signtool.exe sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /sha1 YOUR_THUMBPRINT $f

>>"%ISS_FILE%" echo
>>"%ISS_FILE%" echo [InstallDelete]
>>"%ISS_FILE%" echo Type: filesandordirs; Name: "{app}\_internal"
>>"%ISS_FILE%" echo Type: filesandordirs; Name: "{app}\__pycache__"

>>"%ISS_FILE%" echo
>>"%ISS_FILE%" echo [Files]
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

>>"%ISS_FILE%" echo
>>"%ISS_FILE%" echo [Icons]
>>"%ISS_FILE%" echo Name: "{group}\%PROJECT_NAME%"; Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\logo.ico"
>>"%ISS_FILE%" echo Name: "{commondesktop}\%PROJECT_NAME%"; Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

>>"%ISS_FILE%" echo
>>"%ISS_FILE%" echo [Tasks]
>>"%ISS_FILE%" echo Name: "desktopicon"; Description: "Maak een snelkoppeling op het bureaublad"; GroupDescription: "Extra opties:"

>>"%ISS_FILE%" echo
>>"%ISS_FILE%" echo [Run]
>>"%ISS_FILE%" echo Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; Description: "Start %PROJECT_NAME%"; Flags: nowait postinstall skipifsilent

rem [12] Inno Setup compileren
echo [7] 🔨 Inno Setup compileren...
set "ISCC_EXE="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE (
  echo ⚠️  ISCC.exe niet gevonden. Installeer Inno Setup 6.
  goto SHOW_OUTPUT
)

"%ISCC_EXE%" "%ISS_FILE%"
if errorlevel 1 (
  echo [FOUT] Inno Setup compile mislukt. Bekijk "%ISS_FILE%".
  goto SHOW_OUTPUT
)
echo ✅ Installer aangemaakt: %DIST_FOLDER%\%PROJECT_NAME%Setup_%VERSION%.exe

:SHOW_OUTPUT
echo(
echo 📂 Output-map: %DIST_FOLDER%\%PROJECT_NAME%_%VERSION%
echo 💡 Testen: "%DIST_FOLDER%\%PROJECT_NAME%_%VERSION%\%PROJECT_NAME%.exe"
echo 🧩 Installer (indien gebouwd): %DIST_FOLDER%\%PROJECT_NAME%Setup_%VERSION%.exe
echo --- Build voltooid op %DATE% %TIME% --- >> "%LOGFILE%"
pause
endlocal
