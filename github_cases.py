# =============================================================================
# ArticleSearch
# File:    github_cases.py
# Role:    show_github_cases() — toont open Issues + Pull Requests uit de
#          repo (GitHubCasesClient) via Help-menu → GitHub Cases.
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Eerste keer onder versiebeheer. BUGFIX/SECURITY:
#                   hetzelfde hardcoded GitHub PAT als in
#                   bug_report_dialog.py (v1.1.0) gaf op 2026-08-06 een
#                   401 Unauthorized. Token komt nu uit dezelfde
#                   omgevingsvariabele ARTICLESEARCH_GITHUB_PAT — één
#                   token, één plek om te configureren/vervangen.
#                   GitHubCasesClient.__init__() geeft een duidelijke
#                   RuntimeError als de variabele ontbreekt/leeg is.
# =============================================================================

import os
import requests
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QMessageBox

# Zelfde omgevingsvariabele als bug_report_dialog.py — één GitHub PAT,
# hergebruikt voor zowel het melden (BugDialog) als het bekijken (dit
# bestand) van cases. Zie bug_report_dialog.py voor instructies om een
# nieuw token aan te maken en de env var te zetten.
GITHUB_PAT_ENV_VAR = "ARTICLESEARCH_GITHUB_PAT"

class GitHubCasesClient:
    def __init__(self):
        self.token = os.getenv(GITHUB_PAT_ENV_VAR, "").strip()
        if not self.token:
            raise RuntimeError(
                f"Geen GitHub-token geconfigureerd. Stel de omgevings"
                f"variabele '{GITHUB_PAT_ENV_VAR}' in met een geldig "
                f"Personal Access Token (scope: repo) en herstart de app."
            )
        self.owner = "barremans"
        self.repo = "articlesearch"
        self.api_base = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        }

    def get_open_issues(self):
        url = f"{self.api_base}/issues?state=open"
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return [issue for issue in resp.json() if "pull_request" not in issue]

    def get_open_prs(self):
        url = f"{self.api_base}/pulls?state=open"
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

def clean_body_text(body: str) -> str:
    """
    Haalt 'Automatisch gegenereerde ... door ... op ...' koptekst weg,
    zodat enkel de beschrijving overblijft.
    """
    if not body:
        return ""
    parts = body.split("\n\n", 1)
    if len(parts) > 1:
        return parts[1].strip()
    return body.strip()

def show_github_cases(parent):
    try:
        client = GitHubCasesClient()
        issues = client.get_open_issues()
        prs = client.get_open_prs()

        text = "<b><u>📄 Open Issues</u></b><br><br>"
        if issues:
            for issue in issues:
                cleaned = clean_body_text(issue.get("body", ""))
                cleaned = cleaned.replace("\n", "<br>")
                text += f"- {cleaned}<br><br>"
        else:
            text += "Geen open issues.<br>"

        text += "<br><b><u>🔀 Open Pull Requests</u></b><br><br>"
        if prs:
            for pr in prs:
                cleaned = clean_body_text(pr.get("body", ""))
                cleaned = cleaned.replace("\n", "<br>")
                text += f"- {cleaned}<br><br>"
        else:
            text += "Geen open pull requests.<br>"

        dialog = QDialog(parent)
        dialog.setWindowTitle("Open GitHub Cases")
        dialog.resize(800, 800)

        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setHtml(text)  # HTML voor bold en underline
        layout.addWidget(browser)

        close_btn = QPushButton("Sluiten")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    except Exception as e:
        QMessageBox.critical(parent, "GitHub Fout", f"Kon open cases niet ophalen:\n{e}")