@echo off
set AS_BUMP_PART=patch
set AS_MAKE_INSTALLER=J
set AS_DO_SIGN=J
call "C:\searcharticle_code\build_installer15.bat"
exit /b %ERRORLEVEL%
