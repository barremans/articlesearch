<#
.SYNOPSIS
  Kopieert je SearchArticle-project vanaf USB naar schijf en zet meteen de venv op.
#>

# === 1. Vraag USB-stationsletter ===
do {
    $usb = Read-Host "Geef de stationsletter van de USB-stick (bv. E)"
} while (-not (Test-Path "$usb`:\"))

# === 2. Zoek projectmap op USB (nieuwste export_SearchArticle_*) ===
$dirs = Get-ChildItem "$usb`:\" -Directory -Filter "export_SearchArticle_*"
if ($dirs.Count -eq 0) {
    Write-Error "Geen export_SearchArticle_* map gevonden op $usb`:\"
    exit 1
}
$sourceDir = $dirs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "[INFO] Gekozen bronmap: $($sourceDir.FullName)"

# === 3. Vraag doelmap op lokale schijf ===
$defaultDest = Join-Path $HOME "Projects\SearchArticle"
$dest = Read-Host "Doelmap (ENTER voor standaard: $defaultDest)"
if (-not $dest) { $dest = $defaultDest }

# Maak doelmap aan als nodig
if (-not (Test-Path $dest)) {
    New-Item -Path $dest -ItemType Directory -Force | Out-Null
}

# === 4. Kopieer project met robocopy ===
Write-Host "[INFO] Kopiëren naar $dest..."
robocopy $sourceDir.FullName $dest /MIR /NFL /NDL /NJH /NJS
if ($LASTEXITCODE -ge 8) {
    Write-Warning "Er trad een fout op bij het kopiëren."
} else {
    Write-Host "[OK] Kopiëren voltooid."
}

Set-Location $dest

# === 5. Check of Python beschikbaar is ===
try {
    $py = & python --version 2>&1
    Write-Host "[INFO] Found: $py"
} catch {
    Write-Error "Python niet gevonden in PATH. Stop."
    exit 1
}

# === 6. Venv aanmaken of hergebruiken ===
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[INFO] Aanmaken virtuele omgeving..."
    python -m venv venv
} else {
    Write-Host "[INFO] Venv bestaat al, wordt hergebruikt."
}

# === 7. Venv activeren ===
Write-Host "[INFO] Venv activeren..."
& .\venv\Scripts\Activate.ps1

# === 8. Pip upgraden en requirements installeren ===
Write-Host "[INFO] Pip upgraden..."
python -m pip install --upgrade pip
if (Test-Path "requirements.txt") {
    Write-Host "[INFO] Dependencies installeren..."
    pip install -r requirements.txt
} else {
    Write-Warning "requirements.txt niet gevonden, skip installatie."
}

Write-Host "`n✅ Setup compleet! Je kunt nu in VS Code aan de slag."
