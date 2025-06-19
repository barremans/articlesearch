
#updater.pyimport requests
import requests
import webbrowser
from PySide6.QtWidgets import QMessageBox
from packaging.version import parse as parse_version



# 🔧 GitHub configuratie
OWNER = "barremans"
REPO = "articlesearch"
BRANCH = "main"
RELEASE_FOLDER = "releases/latest"
VERSION_FILE_NAME = "version.txt"

# 🔗 API URL's
CONTENTS_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{RELEASE_FOLDER}?ref={BRANCH}"
VERSION_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{RELEASE_FOLDER}/{VERSION_FILE_NAME}?ref={BRANCH}"

# 🔐 GitHub token (alleen nodig voor private repo's)
TOKEN = "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"

HEADERS = {
    "Accept": "application/vnd.github.v3.raw",
    "Authorization": f"token {TOKEN}"
}

def extract_version_from_filename(name: str):
    parts = name.rstrip(".exe").split("_")
    if len(parts) >= 2:
        try:
            return parse_version(parts[-1])
        except Exception:
            return None
    return None

def check_for_update(current_version: str, parent=None, callback=None):
    try:
        response = requests.get(VERSION_API_URL, headers=HEADERS, timeout=5)
        if response.status_code != 200:
            print(f"[update-check] Fout {response.status_code} bij ophalen version.txt")
            if callback:
                callback(False)
            return

        latest = response.text.strip().lstrip("vV")
        print(f"[update-check] Lokale versie: {current_version}, Remote versie: {latest}")
        is_update_available = parse_version(latest) > parse_version(current_version)

        if callback:
            # 👉 alleen knop activeren
            callback(is_update_available)
        elif is_update_available:
            # 👉 alleen popup tonen als geen callback
            QMessageBox.information(
                parent,
                "Nieuwe versie beschikbaar",
                f"Je gebruikt versie {current_version}, maar versie {latest} is beschikbaar.\n"
                "Klik op 'Update nu' in het menu om de nieuwste versie te downloaden."
            )
    except Exception as e:
        print(f"[update-check] Mislukt: {e}")
        if callback:
            callback(False)


def download_latest_release(parent=None):
    try:
        response = requests.get(CONTENTS_API_URL, headers=HEADERS, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Kan inhoud niet ophalen van GitHub. Status: {response.status_code}")

        files = response.json()
        exe_files = [f for f in files if f["name"].lower().endswith(".exe")]

        versioned_files = []
        for f in exe_files:
            version = extract_version_from_filename(f["name"])
            if version is not None:
                versioned_files.append((version, f["download_url"]))

        if not versioned_files:
            QMessageBox.warning(parent, "Geen update gevonden", "Er is geen .exe-bestand met een geldige versie gevonden.")
            return

        versioned_files.sort(reverse=True, key=lambda x: x[0])
        latest_url = versioned_files[0][1]

        QMessageBox.information(parent, "Update beschikbaar", "De nieuwste versie wordt geopend in je browser.")
        webbrowser.open(latest_url)

    except Exception as e:
        QMessageBox.critical(parent, "Fout bij download", str(e))
