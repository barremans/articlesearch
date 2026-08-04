# publish.ps1 - ArticleSearch (release + asset + version.txt)
# Run vanuit de repo root (C:\searcharticle_code):  .\publish.ps1
# Vereist: gh (ingelogd) + git
#
# Naar Networkmap-patroon: locatie wordt DYNAMISCH bepaald via
# $MyInvocation i.p.v. een hardgecodeerd pad - voorkomt het padprobleem
# dat publish_and_update.ps1/.bat eerder had (verkeerd C:\searcharticle
# resp. C:\articlesearch i.p.v. het echte C:\searcharticle_code).
# Vervangt publish_and_update.ps1 en publish_and_update.bat volledig.

param(
    [string]$Owner = "barremans",
    [string]$Repo = "articlesearch"
)

$ErrorActionPreference = "Stop"

# Repo root = map waar dit script staat (dynamisch, geen hardcoded pad)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# 1) Versie lezen uit version.py (root van de repo, geen app\-submap zoals Networkmap)
$versionPy = Join-Path $Root "version.py"
if (-not (Test-Path $versionPy)) { throw "Niet gevonden: $versionPy" }

$txt = Get-Content $versionPy -Raw
$m = [regex]::Match($txt, '__version__\s*=\s*["''](?<v>\d+\.\d+\.\d+)["'']')
if (-not $m.Success) { throw "Kon __version__ niet vinden in version.py" }
$version = $m.Groups["v"].Value

$tag = "v$version"
$assetName = "ArticleSearchSetup_$version.exe"
$assetPath = Join-Path $Root ("dist\" + $assetName)

Write-Host "[INFO] Repo: $Owner/$Repo"
Write-Host "[INFO] Versie: $version"
Write-Host "[INFO] Tag: $tag"
Write-Host "[INFO] Asset: $assetPath"

# 2) Installer bestaat?
if (-not (Test-Path $assetPath)) {
    throw "Installer niet gevonden: $assetPath`nRun eerst build_installer15.bat en maak de installer."
}

# 3) Release bestaat? Anders maken. ("release not found" mag NIET crashen)
$releaseExists = $false
try {
    & gh release view $tag --repo "$Owner/$Repo" *> $null
    if ($LASTEXITCODE -eq 0) { $releaseExists = $true }
}
catch {
    $releaseExists = $false
}

if (-not $releaseExists) {
    Write-Host "[INFO] Release $tag bestaat nog niet. Maken..."
    & gh release create $tag --repo "$Owner/$Repo" --title "$tag" --notes "Release $tag"
    if ($LASTEXITCODE -ne 0) { throw "Aanmaken release $tag mislukt." }
}
else {
    Write-Host "[INFO] Release $tag bestaat al."
}

# 4) Upload asset (clobber = overschrijven indien al aanwezig)
Write-Host "[INFO] Uploaden asset..."
& gh release upload $tag "$assetPath" --repo "$Owner/$Repo" --clobber
if ($LASTEXITCODE -ne 0) { throw "Upload asset mislukt." }

# 5) Download-URL opbouwen (stabiel, zelfde patroon als updater.py's _asset_url())
$downloadUrl = "https://github.com/$Owner/$Repo/releases/download/$tag/$assetName"
Write-Host "[OK] Download URL: $downloadUrl"

# 6) version.txt (2 regels) schrijven in repo - dit is het bestand dat
#    updater.py (check_for_update) rechtstreeks als raw-bestand ophaalt.
$versionTxt = Join-Path $Root "releases\latest\version.txt"
$versionDir = Split-Path -Parent $versionTxt
if (-not (Test-Path $versionDir)) { New-Item -ItemType Directory -Path $versionDir -Force | Out-Null }

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($versionTxt, "$version`n$downloadUrl", $utf8NoBom)

# 7) Commit + push version.py EN version.txt (geen -C nodig, we staan al in $Root)
#    version.py werd hierboven al gelezen; dit commit 'm nu ook effectief,
#    zodat de bump nooit meer enkel lokaal blijft staan (was de oorzaak van
#    de version.py/version.txt-mismatch die eerder ontdekt werd).
& git add "version.py" "releases/latest/version.txt"
& git commit -m "Release $version - sync version.py and version.txt" *> $null
# 'nothing to commit' is ok; push blijft veilig
& git push

Write-Host ""
Write-Host "============================================================"
Write-Host "[DONE] Published $tag"
Write-Host "Release: https://github.com/$Owner/$Repo/releases/tag/$tag"
Write-Host "Version file: https://raw.githubusercontent.com/$Owner/$Repo/main/releases/latest/version.txt"
Write-Host "============================================================"