<#
.SYNOPSIS
  Installeert het SearchArticle-project vanaf USB naar lokale schijf en zet virtuele omgeving op.
#>

Write-Host "`n=== 🚀 Installatie van SearchArticle vanaf USB ===`n"

# === 1. Vraag USB-driveletter ===
do {
    $usb = Read-Host "Geef de stationsletter van de USB-stick (bv. E)"
} while (-not (Test-Path "$usb`:\"))

# === 2. Zoek meest recente exportmap ===
$exportDir = Get-ChildItem "$usb`:\" -Directory -Filter "export_SearchArticle_*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $exportDir) {
    Write-Error "❌ Geen export_SearchArticle_* map gevonden op $usb`:\""
    exit 1
}
Write-Host "📁 Gekozen map: $($exportDir.FullName)"

# === 3. Doelmap instellen ===
$dest = "C:\Projects\SearchArticle"
if (-not (Test-Path $dest)) {
    New-Item -Path $dest -ItemType Directory -Force | Out-Null
    $isFirst = $true
    Write-Host "🆕 Doelmap aangemaakt: $dest"
} else {
    $isFirst = $false
    Write-Host "📂 Doelmap bestaat al. Bestanden worden overschreven (zonder settings.json)."
}

# === 4. Bewaar oude settings.json indien nodig ===
if (-not $isFirst -and (Test-Path "$dest\settings.json")) {
    Copy-Item "$dest\settings.json" "$env:TEMP\settings.json.bak" -Force
    Write-Host "⚠️  settings.json tijdelijk geback-upt."
}

# === 5. Kopieer projectbestanden (excl. zzz-map) ===
robocopy $exportDir.FullName $dest /E /XD "$($exportDir.FullName)\zzz" /NFL /NDL /NJH /NJS > $null
Write-Host "✅ Bestanden gekopieerd."

# === 6. Zet settings.json terug indien nodig ===
if (Test-Path "$env:TEMP\settings.json.bak") {
    Move-Item "$env:TEMP\settings.json.bak" "$dest\settings.json" -Force
    Write-Host "✅ settings.json teruggezet."
}

# === 7. Controleer Python-installatie ===
try {
    $py = & python --version 2>&1
    Write-Host "`n[INFO] Gevonden: $py"
} catch {
    Write-Error "❌ Python niet gevonden in PATH. Installeer Python eerst."
    exit 1
}

# === 8. Maak virtuele omgeving aan indien nodig ===
Set-Location $dest
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "🐍 Venv aanmaken..."
    python -m venv venv
} else {
    Write-Host "♻️  Bestaande venv wordt gebruikt."
}

# === 9. Activeer venv en installeer requirements ===
Write-Host "📦 Dependencies installeren..."
& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "✅ requirements.txt geïnstalleerd."
} else {
    Write-Warning "⚠️ Geen requirements.txt aanwezig."
}

Write-Host "`n🎉 Klaar! Open het project in VS Code via: $dest"
