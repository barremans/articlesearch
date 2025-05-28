
# updater.py
import requests
import webbrowser
from PySide6.QtWidgets import QMessageBox

OWNER = "barremans"
REPO = "articlesearch"
BRANCH = "main"
RELEASE_FOLDER = "releases/latest"
VERSION_PATH = f"{RELEASE_FOLDER}/version.txt"
CONTENTS_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{RELEASE_FOLDER}?ref={BRANCH}"
VERSION_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{VERSION_PATH}?ref={BRANCH}"

# 🔐 Token (alleen nodig voor private repos)
TOKEN = "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"

HEADERS = {
    "Accept": "application/vnd.github.v3.raw",
    "Authorization": f"token {TOKEN}"
}

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
        is_update_available = latest != current_version

        if callback:
            callback(is_update_available)
        elif is_update_available:
            QMessageBox.information(
                parent,
                "Nieuwe versie beschikbaar",
                f"Je gebruikt versie {current_version}, maar versie {latest} is beschikbaar.\n"
                "Ga naar 'Over...' in het menu om bij te werken."
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
        zip_files = [f for f in files if f["name"].lower().endswith(".zip")]

        if not zip_files:
            QMessageBox.warning(parent, "Download niet beschikbaar", "Geen ZIP-bestand gevonden in de release.")
            return

        download_url = zip_files[0].get("download_url")
        if not download_url:
            raise Exception("Geen downloadlink beschikbaar voor het ZIP-bestand.")

        QMessageBox.information(parent, "Download", "De nieuwste versie wordt geopend in je browser.")
        webbrowser.open(download_url)

    except Exception as e:
        QMessageBox.critical(parent, "Fout bij download", str(e))
