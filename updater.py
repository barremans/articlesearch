# updater.py — private/public repo + 2-regelige version.txt
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
