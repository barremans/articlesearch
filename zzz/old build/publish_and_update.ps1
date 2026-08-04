# publish_and_update.ps1  -- v1.3.0
# Changes v1.3.0: BUGFIX -- $RepoClone wees naar "C:\searcharticle" (niet-
#   bestaand of verkeerd pad), terwijl de echte lokale git-clone op
#   "C:\searcharticle_code" staat (zelfde map als $projectDir in
#   build_and_publish.ps1). Zonder deze fix faalt de version.txt-push met
#   "Geen git-repo gevonden".
# Changes v1.2.1: baseline (asset-URL retry-lus, robuuste release create/upload).

$ErrorActionPreference = "Stop"

# ======================
# Config
# ======================
$Owner     = "barremans"
$Repo      = "articlesearch"
$BuildDir  = "C:\articleseacrh_release\articlesearch\releases\latest"
$RepoClone = "C:\searcharticle_code"   # lokale clone van de repo (BUGFIX v1.3.0: was "C:\searcharticle")

# ======================
# Input check
# ======================
$versionFile = Join-Path $BuildDir "version.txt"
if (-not (Test-Path $versionFile)) { throw "[ERROR] Niet gevonden: $versionFile" }
$version = (Get-Content $versionFile -Raw).Split("`n")[0].Trim()
if ([string]::IsNullOrWhiteSpace($version)) { throw "[ERROR] version.txt is leeg." }

$exeName = "ArticleSearchSetup_$version.exe"
$exeFile = Join-Path $BuildDir $exeName
if (-not (Test-Path $exeFile)) { throw "[ERROR] Installer niet gevonden: $exeFile" }

# ======================
# Tools / login
# ======================
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "[ERROR] GitHub CLI niet gevonden." }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "[ERROR] Git niet gevonden." }

& gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host "[INFO] Nog niet ingelogd bij GitHub. Inloggen..."
  gh auth login
}

# ======================
# Release create / upload (betrouwbaar)
# ======================
$tag = "v$version"
Write-Host "[INFO] Publiceren $exeFile naar release $tag op $Owner/$Repo ..."

# Bestaat de release?
& gh release view $tag --repo "$Owner/$Repo" *> $null
$releaseExists = ($LASTEXITCODE -eq 0)

if (-not $releaseExists) {
  Write-Host "[INFO] Release $tag bestaat nog niet. Maken..."
  # Maak eerst de release ZONDER assets
  & gh release create $tag --repo "$Owner/$Repo" --title "$tag" --notes "Release $tag"
  if ($LASTEXITCODE -ne 0) { throw "[ERROR] Aanmaken van release $tag mislukt." }
} else {
  Write-Host "[INFO] Release $tag bestaat al."
}

# Upload (of her-upload) altijd expliciet
Write-Host "[INFO] Asset uploaden (overschrijven indien bestaat)..."
& gh release upload $tag "$exeFile" --repo "$Owner/$Repo" --clobber
if ($LASTEXITCODE -ne 0) { throw "[ERROR] Uploaden van asset naar release $tag mislukt." }

# ======================
# Asset-URL ophalen (ruimer wachten, met veldnaam-fallback)
# ======================
$assetUrl = $null
$maxTries = 15      # ~ 15 * 1s = 15s
for ($i=1; $i -le $maxTries -and -not $assetUrl; $i++) {
  Start-Sleep -Seconds 1
  $assetsJson = gh release view $tag --repo "$Owner/$Repo" --json assets | ConvertFrom-Json
  if ($assetsJson -and $assetsJson.assets) {
    $asset = $assetsJson.assets | Where-Object { $_.name -eq $exeName } | Select-Object -First 1
    if ($asset) {
      $hasBrowser = $asset.PSObject.Properties.Name -contains 'browser_download_url'
      $hasUrl     = $asset.PSObject.Properties.Name -contains 'url'
      if ($hasBrowser -and $asset.browser_download_url) {
        $assetUrl = $asset.browser_download_url
      } elseif ($hasUrl -and $asset.url) {
        $assetUrl = $asset.url
      } else {
        # laatste fallback: zelf opbouwen
        $assetUrl = "https://github.com/$Owner/$Repo/releases/download/$tag/$exeName"
      }
    }
  }
}
if (-not $assetUrl) {
  $raw = gh release view $tag --repo "$Owner/$Repo" --json assets
  throw "[ERROR] Kon asset-URL niet ophalen uit release $tag.`nDebug assets JSON:`n$raw"
}

Write-Host "[OK] Release klaar. Download-URL:"
Write-Host $assetUrl
Write-Host ""

# ======================
# Repo updaten: version.txt (2 regels)
# ======================
if (-not (Test-Path (Join-Path $RepoClone ".git"))) { throw "[ERROR] Geen git-repo gevonden op $RepoClone" }

# altijd eerst synchroon met origin/main
git -C $RepoClone fetch origin
git -C $RepoClone checkout main
git -C $RepoClone reset --hard origin/main

# lokale version.txt bijwerken en kopiëren
Set-Content -Path $versionFile -Value "$version`n$assetUrl" -Encoding UTF8

$repoVersionFile = Join-Path $RepoClone "releases\latest\version.txt"
$repoVersionDir  = Split-Path $repoVersionFile
if (-not (Test-Path $repoVersionDir)) { New-Item -ItemType Directory -Path $repoVersionDir -Force | Out-Null }

Copy-Item -Path $versionFile -Destination $repoVersionFile -Force
git -C $RepoClone add "releases/latest/version.txt"
git -C $RepoClone commit -m "Update version.txt to $version" | Out-Null
git -C $RepoClone push

Write-Host ""
Write-Host "============================================================"
Write-Host "[DONE] Release $tag gepubliceerd en version.txt geüpdatet."
Write-Host "Repo-map: https://github.com/$Owner/$Repo/tree/main/releases/latest"
Write-Host "Release:  https://github.com/$Owner/$Repo/releases/tag/$tag"
Write-Host "============================================================"
