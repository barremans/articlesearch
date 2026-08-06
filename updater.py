# =============================================================================
# ArticleSearch
# File:    updater.py
# Role:    Update-check tegen GitHub — leest version.txt (releases/latest/)
#          voor de versievergelijking, en (nieuw) de release notes van de
#          laatste GitHub Release via de Releases API voor "Wat is er
#          nieuw?".
# Version: 1.1.0
# Author:  Bart Bossuyt
# Changes: 1.1.0 — WHATSNEW-1: nieuwe functie fetch_release_notes() — haalt
#                   tag_name/body/html_url op van de laatste gepubliceerde
#                   GitHub Release (Releases API, GET .../releases/latest).
#                   `body` bevat de release notes zoals ingevuld bij het
#                   publiceren van de Release op GitHub (Markdown). Wordt
#                   pas aangeroepen wanneer de gebruiker expliciet op
#                   "Wat is er nieuw?" klikt (ui_main.py) — geen extra
#                   netwerkcall bij elke opstart. Draft/pre-release Releases
#                   worden door dit endpoint automatisch genegeerd.
# Changes: 1.0.0 — Baseline: bestaande functionaliteit (version.txt-check +
#                   download) vóór introductie van versiebeheer in
#                   commentaar.
# =============================================================================
import webbrowser
import requests
from packaging.version import parse as parse_version
from PySide6.QtWidgets import QMessageBox

OWNER  = "barremans"
REPO   = "articlesearch"
BRANCH = "main"
REL_DIR = "releases/latest"

RAW_VERSION_URL      = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{REL_DIR}/version.txt"
CONTENTS_VERSION_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{REL_DIR}/version.txt?ref={BRANCH}"

# WHATSNEW-1: officiële GitHub Releases API — geeft de laatste gepubliceerde
# (niet-draft, niet-pre-release) Release terug, incl. release notes (body).
RELEASES_API_LATEST = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"

# ZET DIT IN: token met scope 'repo' (PAT classic)
TOKEN = "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"

def _headers_raw():
    # raw github ondersteunt geen auth
    return {"Accept": "text/plain"}

def _headers_api():
    h = {"Accept": "application/vnd.github.v3.raw"}
    if TOKEN:
        h["Authorization"] = f"token {TOKEN}"
    return h


# WHATSNEW-1: aparte header-set voor de Releases API — hier willen we het
# JSON-object terug (tag_name/body/html_url), dus GEEN "v3.raw" Accept-
# header (die zou enkel platte bestandsinhoud teruggeven, zoals bij
# _headers_api() hierboven voor de Contents API).
def _headers_releases_api():
    h = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = f"token {TOKEN}"
    return h


def fetch_release_notes(timeout=8) -> dict:
    """
    WHATSNEW-1: haalt de release notes (body) van de laatste gepubliceerde
    GitHub Release op, via de officiële Releases API.

    Retourneert: {"tag_name": str, "body": str, "html_url": str}
    - "body" is de Markdown-tekst zoals ingevuld bij het publiceren van de
      Release op GitHub (kan leeg zijn als er niets werd ingevuld).
    - "html_url" wijst naar de releasepagina zelf — bruikbaar als fallback-
      link wanneer "body" leeg is of het ophalen faalt.

    Raises requests.HTTPError / requests.RequestException bij netwerk- of
    API-fouten — de aanroeper (UI) vangt dit af en toont een nette fallback.
    """
    r = requests.get(RELEASES_API_LATEST, headers=_headers_releases_api(), timeout=timeout)
    if not r.ok:
        raise requests.HTTPError(f"{r.status_code} for {RELEASES_API_LATEST}: {r.text[:200]}")
    data = r.json()
    return {
        "tag_name": data.get("tag_name", ""),
        "body": (data.get("body") or "").strip(),
        "html_url": data.get("html_url") or f"https://github.com/{OWNER}/{REPO}/releases/latest",
    }

def _fetch_version_txt(timeout=8) -> str:
    # 1) Raw (werkt voor public)
    try:
        r = requests.get(RAW_VERSION_URL, headers=_headers_raw(), timeout=timeout)
        if r.ok:
            return r.text
        print(f"[update-check] raw GET {RAW_VERSION_URL} -> {r.status_code}")
    except Exception as e:
        print(f"[update-check] raw exception: {e}")

    # 2) Contents API (werkt ook voor private, mits TOKEN)
    r = requests.get(CONTENTS_VERSION_URL, headers=_headers_api(), timeout=timeout)
    if not r.ok:
        # 404 bij private zonder juiste token is normaal
        raise requests.HTTPError(f"{r.status_code} for {CONTENTS_VERSION_URL}: {r.text[:200]}")
    return r.text  # met Accept: v3.raw = pure file-inhoud

def _parse_version_file(txt: str):
    # regel 1: versie; regel 2: optionele download-URL
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    if not lines:
        raise RuntimeError("version.txt is leeg")
    version = lines[0].lstrip("vV")
    url = lines[1] if len(lines) >= 2 and lines[1].startswith(("http://", "https://")) else None
    return version, url

def _asset_url(version: str, asset_name: str | None = None) -> str:
    if not asset_name:
        asset_name = f"ArticleSearchSetup_{version}.exe"
    return f"https://github.com/{OWNER}/{REPO}/releases/download/v{version}/{asset_name}"

def check_for_update(current_version: str, parent=None, callback=None) -> bool:
    try:
        txt = _fetch_version_txt()
        remote_version, _ = _parse_version_file(txt)
        is_newer = parse_version(remote_version) > parse_version(current_version)
        print(f"[update-check] Lokale versie: {current_version}, Remote versie: {remote_version}")
        if callback:
            callback(is_newer)
        elif is_newer:
            QMessageBox.information(
                parent, "Nieuwe versie beschikbaar",
                f"Je gebruikt {current_version}, nieuwste is {remote_version}.\n"
                f"Klik op 'Update nu' om te downloaden."
            )
        return is_newer
    except Exception as e:
        print(f"[update-check] Mislukt: {e}")
        if callback:
            callback(False)
        return False

def download_latest_release(parent=None):
    try:
        txt = _fetch_version_txt()
        version, url = _parse_version_file(txt)
        if not url:
            url = _asset_url(version)
        QMessageBox.information(parent, "Update", "De nieuwste installer wordt geopend in je browser.")
        webbrowser.open(url)
    except Exception as e:
        QMessageBox.critical(parent, "Fout bij download", str(e))