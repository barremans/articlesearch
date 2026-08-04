<#  sign_installer.ps1
    - Zoekt de nieuwste ArticleSearchSetup_*.exe in opgegeven mappen
    - Signeert met PFX (SHA256 + RFC3161 timestamp)
    - Verifieert de handtekening achteraf
    - V1.0.0
#>

[CmdletBinding(SupportsShouldProcess)]
param(
  # Pad naar .pfx (vereist)
  [Parameter(Mandatory=$true)]
  [string]$PfxPath,

  # Wachtwoord voor .pfx (je kunt ook -UsePrompt gebruiken ipv dit)
  [string]$PfxPassword,

  # Interactief wachtwoord in popup i.p.v. plain text
  [switch]$UsePrompt,

  # Optioneel: expliciet pad naar installer; overschrijft zoeken
  [string]$InstallerPath,

  # Mappen om te doorzoeken (volgorde is prioriteit)
  [string[]]$SearchDirs = @(
    "$PSScriptRoot\dist",
    "$PSScriptRoot\dist\dist",
    "C:\articleseacrh_release\articlesearch\releases\latest"
  ),

  # Timestamp servers (worden in volgorde geprobeerd)
  [string[]]$TimestampServers = @(
    "http://timestamp.sectigo.com",
    "http://timestamp.digicert.com",
    "http://timestamp.globalsign.com/scripts/timstamp.dll"
  ),

  # Hash algoritme
  [ValidateSet("sha256","sha1")]
  [string]$Digest = "sha256",

  # Aantal retry pogingen als timestamp faalt
  [int]$MaxTimestampRetries = 3
)

$ErrorActionPreference = "Stop"

function Get-SignToolPath {
  # 1) Als signtool in PATH staat
  $signtool = (Get-Command signtool.exe -ErrorAction SilentlyContinue)?.Source
  if ($signtool) { return $signtool }

  # 2) Veelvoorkomende Windows SDK paden
  $candidates = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22000.0\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\8.1\bin\x64\signtool.exe"
  )
  foreach ($p in $candidates) {
    if (Test-Path $p) { return $p }
  }
  throw "SignTool (signtool.exe) niet gevonden. Installeer de Windows 10/11 SDK of voeg signtool aan PATH toe."
}

function Find-LatestInstaller {
  param([string[]]$Dirs)
  $files = @()
  foreach ($d in $Dirs) {
    if (-not [string]::IsNullOrWhiteSpace($d) -and (Test-Path $d)) {
      $files += Get-ChildItem -Path $d -Filter "ArticleSearchSetup_*.exe" -File -ErrorAction SilentlyContinue
    }
  }
  if (-not $files) { return $null }
  return ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
}

# ----------- Validaties -----------
if (-not (Test-Path $PfxPath)) { throw "PFX niet gevonden: $PfxPath" }

if ($UsePrompt) {
  $SecurePwd = Read-Host -AsSecureString "PFX wachtwoord"
} else {
  if ([string]::IsNullOrWhiteSpace($PfxPassword)) {
    throw "Geef -PfxPassword op of gebruik -UsePrompt."
  }
  $SecurePwd = (ConvertTo-SecureString -String $PfxPassword -AsPlainText -Force)
}

if ([string]::IsNullOrWhiteSpace($InstallerPath)) {
  $candidate = Find-LatestInstaller -Dirs $SearchDirs
  if (-not $candidate) { throw "Geen installer gevonden in: $($SearchDirs -join '; ')" }
  $InstallerPath = $candidate.FullName
}

if (-not (Test-Path $InstallerPath)) { throw "Installer niet gevonden: $InstallerPath" }

Write-Host "[INFO] Installer: $InstallerPath"
Write-Host "[INFO] PFX      : $PfxPath"

# ----------- SignTool bouwen -----------
$signtool = Get-SignToolPath
Write-Host "[INFO] SignTool : $signtool"

# Tijdelijke PFX-wachtwoord naar clear text voor signtool (helaas vereist)
# Tip: draai dit script enkel lokaal of uit een beveiligde pipeline.
$unsecurePwd = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
  [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePwd)
)

# Signeren met timestamp + retries
$tsOk = $false
$lastErr = $null
foreach ($ts in $TimestampServers) {
  for ($i=1; $i -le $MaxTimestampRetries; $i++) {
    try {
      Write-Host "[INFO] Signeren (attempt $i) met TSA: $ts"
      & "$signtool" sign `
        /f "$PfxPath" `
        /p "$unsecurePwd" `
        /fd $Digest `
        /tr "$ts" `
        /td $Digest `
        "$InstallerPath"
      if ($LASTEXITCODE -ne 0) {
        throw "signtool sign exitcode: $LASTEXITCODE"
      }
      $tsOk = $true
      break
    } catch {
      $lastErr = $_
      Start-Sleep -Seconds ([Math]::Min(2*$i, 10))
    }
  }
  if ($tsOk) { break }
}

if (-not $tsOk) {
  Write-Warning "Timestampen faalde op alle servers. Probeer nog één keer zonder timestamp (niet aanbevolen)…"
  & "$signtool" sign /f "$PfxPath" /p "$unsecurePwd" /fd $Digest "$InstallerPath"
  if ($LASTEXITCODE -ne 0) {
    throw "Signeren zonder timestamp is ook mislukt. Laatste fout: $lastErr"
  }
}

# ----------- Verifiëren -----------
Write-Host "[INFO] Verifiëren van handtekening…"
& "$signtool" verify /pa /all "$InstallerPath"
if ($LASTEXITCODE -ne 0) {
  throw "Verificatie mislukt (exitcode $LASTEXITCODE)."
}

Write-Host ""
Write-Host "=============================="
Write-Host "✅ Signeren voltooid!"
Write-Host "Bestand : $InstallerPath"
Write-Host "Hash    : $Digest"
Write-Host "=============================="
