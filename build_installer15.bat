@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem Altijd uitvoeren vanuit de map waar dit .bat bestand staat
cd /d "%~dp0"

rem ================================================
rem build_installer15.bat - Build + Inno Setup installer generator
rem - Installeert ALTIJD in C:\ArticleSearch
rem - Admin vereist (geschikt voor Intune SYSTEM deployment)
rem - Met code signing (self-signed)
rem ================================================

rem 🧩 Basisconfig
set "PROJECT_NAME=ArticleSearch"
set "SPEC_FILE=SearchArticle.spec"
set "DST_FOLDER=dist"
set "LOGFILE=build_log.txt"

rem ---- Python uit .venv prefereren ----
set "PYEXE="
if exist ".venv\Scripts\python.exe" set "PYEXE=.venv\Scripts\python.exe"
if not defined PYEXE if exist "Scripts\python.exe" set "PYEXE=Scripts\python.exe"
if not defined PYEXE set "PYEXE=python"

rem Alleen naar absolute path omzetten als het effectief een bestaand bestandspad is
for %%I in ("%PYEXE%") do (
  if exist "%%~fI" set "PYEXE=%%~fI"
)

echo [info] Python: %PYEXE%
"%PYEXE%" -V >nul 2>&1 || (echo ❌ Geen werkende Python gevonden.& pause & exit /b 1)

rem ---- Versie verhogen ----
set /p PART_TO_BUMP=Welke versie wil je verhogen? (patch/minor/major) : 
if "%PART_TO_BUMP%"=="" set "PART_TO_BUMP=patch"
echo [0] 🔁 Versie verhogen via bump_version.py (%PART_TO_BUMP%)...
"%PYEXE%" bump_version.py %PART_TO_BUMP% || (echo ❌ Versieverhoging mislukt.& pause & exit /b 1)

rem ---- Versie robuust uitlezen uit version.py ----
set "PY_READV=%TEMP%\__read_version_tmp.py"
set "VER_TXT=%TEMP%\__version_out.txt"
del /q "%PY_READV%" "%VER_TXT%" >nul 2>&1
> "%PY_READV%" echo import importlib.util, io, os, re
>>"%PY_READV%" echo p=os.path.abspath('version.py'); v="0.0.0"
>>"%PY_READV%" echo try:
>>"%PY_READV%" echo ^    spec=importlib.util.spec_from_file_location("ver",p)
>>"%PY_READV%" echo ^    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
>>"%PY_READV%" echo ^    v=str(getattr(m,"__version__","0.0.0"))
>>"%PY_READV%" echo except Exception:
>>"%PY_READV%" echo ^    t=io.open(p,'r',encoding='utf-8').read()
>>"%PY_READV%" echo ^    m=re.search(r"__version__\s*=\s*['\^\"\s]*([0-9]+(?:\.[0-9]+){1,2})",t)
>>"%PY_READV%" echo ^    v=m.group(1) if m else "0.0.0"
>>"%PY_READV%" echo io.open(r'%VER_TXT%','w',encoding='utf-8').write(v.strip())
"%PYEXE%" "%PY_READV%" || (echo ❌ Versie uitlezen faalde.& del /q "%PY_READV%" >nul & pause & exit /b 1)
del /q "%PY_READV%" >nul 2>&1
set "NEW_VERSION=" & set /p NEW_VERSION=<"%VER_TXT%"
del /q "%VER_TXT%" >nul 2>&1
if not defined NEW_VERSION (echo ❌ Kon versie niet lezen.& pause & exit /b 1)
echo [1] 🔎 Versie: %NEW_VERSION%

rem ---- Afgeleide paden ----
set "BUILD_FOLDER=%PROJECT_NAME%_%NEW_VERSION%"
set "ABS_BUILD_FOLDER=%CD%\%DST_FOLDER%\%BUILD_FOLDER%"
set "INITIAL_EXE=%DST_FOLDER%\%PROJECT_NAME%\%PROJECT_NAME%.exe"
set "ISS_FILE=%DST_FOLDER%\installer.iss"

rem 🧹 Opschonen
echo [2] 🧹 Opruimen...
rmdir /s /q build 2>nul
rmdir /s /q "%DST_FOLDER%" 2>nul
del /q "%LOGFILE%" 2>nul

rem 📦 Vereisten
echo [3] 🔧 Pip ^& vereisten...
"%PYEXE%" -m pip install --upgrade pip >nul
if exist requirements.txt "%PYEXE%" -m pip install -r requirements.txt || (echo ❌ pip install -r faalde.& pause & exit /b 1)

rem ⚙️ PyInstaller aanwezig?
"%PYEXE%" -c "import PyInstaller" >nul 2>&1 || (
  echo [3b] 📦 PyInstaller installeren...
  "%PYEXE%" -m pip install "pyinstaller==6.11.1" "pyinstaller-hooks-contrib==2025.0" || (echo ❌ Installatie PyInstaller faalde.& pause & exit /b 1)
)

echo --- Build gestart op %DATE% %TIME% --- >> "%LOGFILE%"

rem 🛠 Build (via SPEC)
echo [4] 🛠 PyInstaller...
"%PYEXE%" -m PyInstaller --clean --noconfirm "%SPEC_FILE%" || (echo ❌ PyInstaller build faalde.& pause & exit /b 1)
if not exist "%INITIAL_EXE%" (echo ❌ EXE niet gevonden op "%INITIAL_EXE%".& pause & exit /b 1)

rem 🔁 Hernoemen naar map met versie
if exist "%DST_FOLDER%\%BUILD_FOLDER%" rmdir /S /Q "%DST_FOLDER%\%BUILD_FOLDER%"
rename "%DST_FOLDER%\%PROJECT_NAME%" "%BUILD_FOLDER%" >nul 2>&1
if errorlevel 1 (
  echo [rename] Fallback via robocopy...
  robocopy "%DST_FOLDER%\%PROJECT_NAME%" "%DST_FOLDER%\%BUILD_FOLDER%" /E /MOVE >nul
  if errorlevel 8 (echo ❌ Fallback kopie mislukt.& pause & exit /b 1)
  if exist "%DST_FOLDER%\%PROJECT_NAME%" rmdir /S /Q "%DST_FOLDER%\%PROJECT_NAME%"
)
if not exist "%DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe" (
  echo ❌ %PROJECT_NAME%.exe ontbreekt in %DST_FOLDER%\%BUILD_FOLDER%.
  pause & exit /b 1
)

rem 📁 Assets kopiëren
echo [5] 📁 Assets kopiëren...
for %%D in (assets logs label docs translations) do (
  if exist "%%D" xcopy /E /I /Y "%%D" "%DST_FOLDER%\%BUILD_FOLDER%\%%D" >nul
)
for %%F in (requirements.txt help.md settings.json) do (
  if exist "%%F" copy /Y "%%F" "%DST_FOLDER%\%BUILD_FOLDER%\" >nul
)
> "%DST_FOLDER%\%BUILD_FOLDER%\version.txt" echo %NEW_VERSION%

rem [5b] 🔏 Signen van de BINNEN-EXE
set "SIGN_PFX=C:\certs\cgk_local_signing.pfx"
set "SIGN_PWD=MijnSterkWachtwoord123"
set "SIGNTOOL="
if exist "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe" set "SIGNTOOL=C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
if not defined SIGNTOOL set "SIGNTOOL=signtool.exe"

if exist "%SIGN_PFX%" (
  echo [5b] 🔏 Signen van %DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe ...
  "%SIGNTOOL%" sign ^
    /f "%SIGN_PFX%" /p "%SIGN_PWD%" ^
    /fd SHA256 /td SHA256 ^
    /tr http://timestamp.sectigo.com ^
    "%DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe" || (
      echo [WAARSCHUWING] Signen van app-EXE faalde.
  )
) else (
  echo [INFO] Geen PFX gevonden op %SIGN_PFX% — oversla signen van app-EXE.
)

rem ❓ Inno Setup?
set "DO_ISCC=1"
set /p MAKE_INSTALLER=Ook Inno Setup installer bouwen? [J/N] : 
if /I "%MAKE_INSTALLER%"=="N" set "DO_ISCC=0"
if "%DO_ISCC%"=="0" goto SHOW_OUTPUT

rem 📝 Inno script genereren (zonder SignTool in .iss)
if not exist "%DST_FOLDER%" mkdir "%DST_FOLDER%" >nul 2>&1
del /q "%ISS_FILE%" >nul 2>&1
echo [6] 📝 Installer-script genereren...

>>"%ISS_FILE%" echo ; --- Inno Setup script, automatisch gegenereerd ---
>>"%ISS_FILE%" echo [Setup]
>>"%ISS_FILE%" echo AppId={{A1B2C3D4-E5F6-47A8-9023-ABCDEF123456}
>>"%ISS_FILE%" echo AppName=%PROJECT_NAME%
>>"%ISS_FILE%" echo AppVersion=%NEW_VERSION%
>>"%ISS_FILE%" echo AppVerName=%PROJECT_NAME% %NEW_VERSION%
>>"%ISS_FILE%" echo DefaultDirName=C:\%PROJECT_NAME%
>>"%ISS_FILE%" echo DisableDirPage=yes
>>"%ISS_FILE%" echo UsePreviousAppDir=no
>>"%ISS_FILE%" echo DefaultGroupName=%PROJECT_NAME%
>>"%ISS_FILE%" echo DisableProgramGroupPage=yes
>>"%ISS_FILE%" echo OutputDir=%DST_FOLDER%
>>"%ISS_FILE%" echo OutputBaseFilename=%PROJECT_NAME%Setup_%NEW_VERSION%
>>"%ISS_FILE%" echo Compression=lzma
>>"%ISS_FILE%" echo SolidCompression=yes
>>"%ISS_FILE%" echo Uninstallable=yes
>>"%ISS_FILE%" echo CreateAppDir=yes
>>"%ISS_FILE%" echo PrivilegesRequired=admin
>>"%ISS_FILE%" echo ArchitecturesInstallIn64BitMode=x64
>>"%ISS_FILE%" echo DirExistsWarning=no
>>"%ISS_FILE%" echo WizardStyle=modern
>>"%ISS_FILE%" echo SetupIconFile="%ABS_BUILD_FOLDER%\assets\logo.ico"
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

rem 🔨 Inno Setup compileren
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
echo ✅ Installer aangemaakt: %DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe

rem [7b] 🔏 Post-sign: de INSTALLER zelf ondertekenen
if exist "%DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe" (
  if exist "%SIGN_PFX%" (
    echo [7b] 🔏 Signen van installer: %DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe ...
    "%SIGNTOOL%" sign ^
      /f "%SIGN_PFX%" /p "%SIGN_PWD%" ^
      /fd SHA256 /td SHA256 ^
      /tr http://timestamp.sectigo.com ^
      "%DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe" || (
        echo [WAARSCHUWING] Signen van installer faalde.
    )
  ) else (
    echo [INFO] Geen PFX gevonden op %SIGN_PFX% — installer niet gesigned.
  )
)

:SHOW_OUTPUT
echo.
echo 📂 Output-map: %DST_FOLDER%\%BUILD_FOLDER%
echo 💡 Testen: "%DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe"
echo 🧩 Installer (indien gebouwd): %DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe
pause
endlocal
