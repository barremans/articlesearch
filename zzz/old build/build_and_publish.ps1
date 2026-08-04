# build_and_publish.ps1  — V7.1.0 (consolidatie: publish-script nu in projectmap)
# Changes V7.1.0: publishScript verplaatst naar C:\searcharticle_code (zelfde
#   map als projectDir/build_installer15.bat), i.p.v. de losse map
#   C:\PY\Upload2GitLarge — alle release-tooling nu samen in één map, minder
#   kans dat een los script per ongeluk kwijtraakt bij een volgende release
#   na een lange stilte. Kopieer publish_and_update.ps1 (en evt. .bat,
#   sign_installer.ps1) manueel naar C:\searcharticle_code vóór je dit
#   script opnieuw draait.
param(
  [switch]$Auto
)

$ErrorActionPreference = "Stop"

# === Paden (ongewijzigd) ===
$projectDir    = "C:\searcharticle_code"
$releaseDir    = "C:\articleseacrh_release\articlesearch\releases\latest"
$publishScript = "C:\searcharticle_code\publish_and_update.ps1"   # was: C:\PY\Upload2GitLarge\publish_and_update.ps1

# === Code signing configuratie ===
# Zet $EnableSigning=$false als je (tijdelijk) niet wil signeren
$EnableSigning = $true
$SignToolPath  = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
$PfxPath       = "C:\certs\cgk_local_signing.pfx"
$PfxPassword   = "MijnSterkWachtwoord123"
$TimeStampUrl  = "http://timestamp.sectigo.com"

# === Helpers ===
function Find-BuildBat {
  param([string]$root)
  $files = Get-ChildItem -Path $root -Filter 'build_installer*.bat' -File -ErrorAction SilentlyContinue
  if (-not $files) { throw "Geen build_installer*.bat gevonden in $root" }

  $bestFile = $null
  $bestRank = -1
  foreach ($f in $files) {
    $rank = 0
    $m = [regex]::Match($f.Name, 'build_installer(\d+)\.bat$', 'IgnoreCase')
    if ($m.Success) { $rank = [int]$m.Groups[1].Value }
    if ($rank -gt $bestRank) { $bestRank = $rank; $bestFile = $f }
  }
  return $bestFile.FullName
}

function Get-Version-FromVersionPy {
  param([string]$codeDir)
  $verFile = Join-Path $codeDir 'version.py'
  if (-not (Test-Path $verFile)) { return $null }
  $txt = Get-Content $verFile -Raw
  $m = [regex]::Match($txt, '__version__\s*=\s*["''](?<v>\d+\.\d+\.\d+)["'']')
  if ($m.Success) { return $m.Groups['v'].Value }
  return $null
}

function Find-ExeCandidates {
  param([string]$codeDir)
  $cands = @()
  foreach ($p in @('dist','dist\dist')) {
    $abs = Join-Path $codeDir $p
    if (Test-Path $abs) {
      $cands += Get-ChildItem -Path $abs -Filter 'ArticleSearchSetup_*.exe' -File -ErrorAction SilentlyContinue
    }
  }
  return $cands | Sort-Object LastWriteTime -Descending
}

function Pick-ExeInteractive {
  param([System.IO.FileInfo[]]$cands)
  if (-not $cands -or $cands.Count -eq 0) { return $null }
  if ($cands.Count -eq 1) { return $cands[0] }

  Write-Host "Kies de installer om te publiceren:"
  for ($i=0; $i -lt $cands.Count; $i++) {
    Write-Host ("[{0}] {1}" -f $i, $cands[$i].FullName)
  }
  while ($true) {
    $sel = Read-Host "Nummer"
    if ([int]::TryParse($sel, [ref]$null)) {
      $idx = [int]$sel
      if ($idx -ge 0 -and $idx -lt $cands.Count) { return $cands[$idx] }
    }
    Write-Host "Ongeldige keuze, probeer opnieuw." -ForegroundColor Yellow
  }
}

function Read-YesNo($prompt, [bool]$defaultYes=$true) {
  $suffix = $defaultYes ? "[J/n]" : "[j/N]"
  while ($true) {
    $ans = Read-Host "$prompt $suffix"
    if ([string]::IsNullOrWhiteSpace($ans)) { return $defaultYes }
    $a = $ans.Trim().ToLower()
    if ($a -in @("j","ja","y","yes")) { return $true }
    if ($a -in @("n","nee","no")) { return $false }
  }
}

function Test-Signature {
  param([string]$Path)
  & $SignToolPath verify /pa "$Path" *> $null
  return ($LASTEXITCODE -eq 0)
}

function Sign-File {
  param([string]$Path)
  if (-not (Test-Path $SignToolPath)) { throw "[SIGN] SignTool niet gevonden: $SignToolPath" }
  if (-not (Test-Path $PfxPath))      { throw "[SIGN] PFX niet gevonden: $PfxPath" }

  Write-Host "[SIGN] Signeren: $Path"
  & $SignToolPath sign `
      /f "$PfxPath" `
      /p "$PfxPassword" `
      /fd SHA256 `
      /td SHA256 `
      /tr $TimeStampUrl `
      "$Path"
  if ($LASTEXITCODE -ne 0) { throw "[SIGN] SignTool sign faalde (exitcode $LASTEXITCODE)." }

  Write-Host "[SIGN] Verifiëren..."
  if (-not (Test-Signature -Path $Path)) {
    throw "[SIGN] Verificatie van handtekening mislukt."
  }
  Write-Host "[SIGN] OK: handtekening geldig."
}

# === Checks ===
if (-not (Test-Path $projectDir))    { throw "CodeDir niet gevonden: $projectDir" }
if (-not (Test-Path $publishScript)) { throw "PublishScript niet gevonden: $publishScript" }
if (-not (Test-Path $releaseDir))    { New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null }

# === 1) Build ===
$buildBat = Find-BuildBat -root $projectDir
Write-Host "[INFO] Buildscript: $buildBat"

Push-Location $projectDir
try {
  if ($Auto) {
    Write-Host "[INFO] Build uitvoeren (interactief in .bat; -Auto doet géén auto-antwoorden)."
    & $buildBat
  } else {
    Write-Host "[INFO] Build uitvoeren (interactief)..."
    & $buildBat
  }
} finally {
  Pop-Location
}

# === 2) Versie bepalen ===
$version = Get-Version-FromVersionPy -codeDir $projectDir
$cands   = Find-ExeCandidates -codeDir $projectDir

if (-not $version -and $cands.Count -gt 0) {
  $m = [regex]::Match($cands[0].Name, 'ArticleSearchSetup_(?<v>\d+\.\d+\.\d+)\.exe$', 'IgnoreCase')
  if ($m.Success) { $version = $m.Groups['v'].Value }
}
if (-not $version) {
  Write-Host "[WAARSCHUWING] Versie niet gevonden in version.py of bestandsnaam." -ForegroundColor Yellow
}

# === 3) Installer kiezen ===
$chosen = $null
if ($Auto) {
  if ($cands.Count -eq 0) { throw "Geen installers gevonden in dist\ of dist\dist\." }
  $chosen = $cands[0]  # meest recente
} else {
  $chosen = Pick-ExeInteractive -cands $cands
  if (-not $chosen) { throw "Geen installer gekozen/gevonden." }
}

if (-not $version) {
  $m2 = [regex]::Match($chosen.Name, 'ArticleSearchSetup_(?<v>\d+\.\d+\.\d+)\.exe$', 'IgnoreCase')
  if ($m2.Success) { $version = $m2.Groups['v'].Value }
}
if (-not $version) { throw "Kon versie niet afleiden uit $($chosen.Name)." }

Write-Host "[OK] Gekozen installer: $($chosen.FullName)"
Write-Host "[OK] Gedetecteerde versie: $version"

# === 3b) Signeren vóór kopiëren/uploaden ===
if ($EnableSigning) {
  try {
    Sign-File -Path $chosen.FullName
  } catch {
    throw "[ERROR] Signing stap faalde: $($_.Exception.Message)"
  }
} else {
  Write-Host "[SIGN] Signing overgeslagen (EnableSigning=$EnableSigning)."
}

# === 4) Kopiëren naar staging en versie.txt schrijven (regel 1 = versie) ===
$destExe = Join-Path $releaseDir ("ArticleSearchSetup_{0}.exe" -f $version)
Copy-Item -Force $chosen.FullName $destExe
Set-Content -Path (Join-Path $releaseDir 'version.txt') -Value $version -Encoding UTF8
Write-Host "[OK] Gekopieerd naar staging: $releaseDir"

# (optioneel) extra check: staat de staging-exe ook gesigneerd?
if ($EnableSigning -and -not (Test-Signature -Path $destExe)) {
  Write-Host "[SIGN] Staging-exe lijkt ongetekend; sign opnieuw in staging..."
  Sign-File -Path $destExe
}

# === 5) Uploaden? ===
$doUpload = $Auto ? $true : (Read-YesNo "Nu uploaden naar GitHub releases en versie in repo bijwerken?" $true)
if (-not $doUpload) {
  Write-Host "Upload overgeslagen op verzoek." -ForegroundColor Yellow
  Write-Host "Je kunt later handmatig draaien: `"$publishScript`""
  exit 0
}

Write-Host "[INFO] Start upload naar GitHub..."
& $publishScript
if ($LASTEXITCODE -ne 0) { throw "Publicatie script gaf een fout terug (exitcode $LASTEXITCODE)." }

Write-Host ""
Write-Host "============================================================"
Write-Host "[DONE] Build + sign + publish afgerond."
Write-Host "Versie: $version"
Write-Host "Staging: $releaseDir"
Write-Host "============================================================"
