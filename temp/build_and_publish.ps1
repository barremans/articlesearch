# build_and_publish.ps1 - ArticleSearch
# Vraagt alle build-parameters vooraf, voert build_installer15.bat niet-
# interactief uit (via AS_*-env vars, zelfde patroon als Networkmap_Creator),
# en publiceert daarna via publish.ps1 naar GitHub.
# Run vanuit repo root (C:\searcharticle_code):  .\build_and_publish.ps1
#
# Let op: gebruikt bewust GEEN PowerShell 7-only syntax (zoals de ?:
# ternary-operator uit de vorige versie) - werkt daardoor zowel onder
# Windows PowerShell 5.1 als PowerShell 7.x.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$buildBat  = Join-Path $Root "build_installer15.bat"
$publishPs = Join-Path $Root "publish.ps1"

if (-not (Test-Path $buildBat))  { throw "Niet gevonden: $buildBat" }
if (-not (Test-Path $publishPs)) { throw "Niet gevonden: $publishPs" }

# ============================================================
# Parameters vooraf vragen
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "  ArticleSearch - Build + Publish"
Write-Host "============================================================"
Write-Host ""

# Versie-bump
$bumpPart = ""
while ($bumpPart -notin @("patch", "minor", "major")) {
    $bumpPart = Read-Host "Versie verhogen? [patch/minor/major] (Enter = patch)"
    if ($bumpPart -eq "") { $bumpPart = "patch" }
}
Write-Host "[OK] Versie-bump: $bumpPart"

# Installer bouwen
$makeInstaller = ""
while ($makeInstaller -notin @("J", "N", "j", "n")) {
    $makeInstaller = Read-Host "Inno Setup installer bouwen? [J/N] (Enter = J)"
    if ($makeInstaller -eq "") { $makeInstaller = "J" }
}
$makeInstaller = $makeInstaller.ToUpper()
Write-Host "[OK] Installer: $makeInstaller"

# Signing (default N - MS Intune blokkeert soms signtool/folder-toegang;
# expliciet moet je "J" kiezen, net als bij Networkmap_Creator)
$doSign = ""
while ($doSign -notin @("J", "N", "j", "n")) {
    $doSign = Read-Host "Binaries signen (certificaatstore)? [J/N] (Enter = N)"
    if ($doSign -eq "") { $doSign = "N" }
}
$doSign = $doSign.ToUpper()
Write-Host "[OK] Signing: $doSign"

# Publiceren naar GitHub
$doPublish = ""
while ($doPublish -notin @("J", "N", "j", "n")) {
    $doPublish = Read-Host "Publiceren naar GitHub na build? [J/N] (Enter = J)"
    if ($doPublish -eq "") { $doPublish = "J" }
}
$doPublish = $doPublish.ToUpper()
Write-Host "[OK] Publiceren: $doPublish"

Write-Host ""
Write-Host "------------------------------------------------------------"
Write-Host "  Samenvatting:"
Write-Host "    Versie-bump : $bumpPart"
Write-Host "    Installer   : $makeInstaller"
Write-Host "    Signing     : $doSign"
Write-Host "    Publiceren  : $doPublish"
Write-Host "------------------------------------------------------------"
$bevestig = Read-Host "Starten? [J/N]"
if ($bevestig.ToUpper() -ne "J") {
    Write-Host "Afgebroken."
    exit 0
}

# ============================================================
# [STEP 1/2] Build uitvoeren via omgevingsvariabelen
# ============================================================

Write-Host ""
Write-Host "[STEP 1/2] Build starten..."

# Schrijf een tijdelijk wrapper .bat bestand dat variabelen zet en
# build_installer15.bat aanroept - vermijdt PowerShell -> cmd
# argument-parsing problemen.
$wrapperPath = Join-Path $Root "_build_wrapper.bat"
$wrapperContent = "@echo off`r`n"
$wrapperContent += "set AS_BUMP_PART=$bumpPart`r`n"
$wrapperContent += "set AS_MAKE_INSTALLER=$makeInstaller`r`n"
$wrapperContent += "set AS_DO_SIGN=$doSign`r`n"
$wrapperContent += "call `"$buildBat`"`r`n"
$wrapperContent += "exit /b %ERRORLEVEL%`r`n"
[System.IO.File]::WriteAllText($wrapperPath, $wrapperContent, [System.Text.Encoding]::ASCII)

Write-Host "--- Wrapper inhoud ---"
Get-Content $wrapperPath | ForEach-Object { Write-Host $_ }
Write-Host "--- Einde wrapper ---"

$buildExitCode = 0
& cmd.exe /c "`"$wrapperPath`""
$buildExitCode = $LASTEXITCODE

Remove-Item $wrapperPath -ErrorAction SilentlyContinue

# Omgevingsvariabelen opruimen (waren al gezet als fallback)
Remove-Item Env:\AS_BUMP_PART      -ErrorAction SilentlyContinue
Remove-Item Env:\AS_MAKE_INSTALLER -ErrorAction SilentlyContinue
Remove-Item Env:\AS_DO_SIGN        -ErrorAction SilentlyContinue

if ($buildExitCode -ne 0) {
    throw "Build faalde (exitcode $buildExitCode). Zie output hierboven."
}

Write-Host "[STEP 1/2] Build geslaagd."

# ============================================================
# [STEP 2/2] Publiceren (optioneel)
# ============================================================

if ($doPublish -eq "J") {
    if ($makeInstaller -ne "J") {
        Write-Host "[WARN] Installer niet gebouwd - publiceren overgeslagen."
    }
    else {
        Write-Host ""
        Write-Host "[STEP 2/2] Publiceren via publish.ps1..."
        & powershell -ExecutionPolicy Bypass -File $publishPs
        if ($LASTEXITCODE -ne 0) { throw "Publish faalde (exitcode $LASTEXITCODE)." }
        Write-Host "[STEP 2/2] Publiceren geslaagd."
    }
}
else {
    Write-Host "[STEP 2/2] Publiceren overgeslagen (keuze gebruiker)."
}

Write-Host ""
Write-Host "============================================================"
Write-Host "[DONE] Build + Publish afgerond."
Write-Host "============================================================"