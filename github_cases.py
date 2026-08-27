# =============================================================================
# ArticleSearch
# File:    github_cases.py
# Role:    show_github_cases() — toont open Issues + Pull Requests uit de
#          repo (GitHubCasesClient) via Help-menu → GitHub Cases.
# Version: 1.1.0
# Author:  Bart Bossuyt
# Changes: 1.1.0 — Token terug hardcoded i.p.v. via omgevingsvariabele
#                   ARTICLESEARCH_GITHUB_PAT. Reden: de app wordt via een
#                   setup/installer verspreid naar andere machines, waar
#                   het niet haalbaar is om per machine manueel een env var
#                   te configureren — dat gaf daar de "Geen GitHub-token
#                   geconfigureerd"-foutmelding (v1.0.0). Zelfde patroon en
#                   zelfde token als GitHubClient in bug_report_dialog.py
#                   (v1.0.0) — één token, hardcoded op beide plekken, zodat
#                   "Open cases tonen" en "Meld via GitHub" consistent
#                   werken zonder extra installatiestap. Bevestigd door
#                   gebruiker (2026-08-06) dat dit token momenteel geldig/
#                   werkend is — de eerdere 401-melding uit sessie 20 was
#                   dus vermoedelijk tijdelijk of aan een ander token
#                   gekoppeld. Zie ⚠️ kanttekening in bug_report_dialog.py:
#                   nog steeds een hardcoded secret in de broncode, met de
#                   bekende afweging (leesbaar te extraheren uit de
#                   installer) — bewuste keuze van de gebruiker, consistent
#                   met de rest van het project (config.py, updater.py).
# Changes: 1.0.0 — Eerste keer onder versiebeheer. BUGFIX/SECURITY:
#                   hetzelfde hardcoded GitHub PAT als in
#                   bug_report_dialog.py (v1.1.0) gaf op 2026-08-06 een
#                   401 Unauthorized. Token kwam toen uit een
#                   omgevingsvariabele ARTICLESEARCH_GITHUB_PAT — één
#                   token, één plek om te configureren/vervangen.
#                   GitHubCasesClient.__init__() gaf een duidelijke
#                   RuntimeError als de variabele ontbrak/leeg was.
#                   (Teruggedraaid in v1.1.0, zie hierboven.)
# =============================================================================

import requests
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QMessageBox

# Zelfde token als GitHubClient in bug_report_dialog.py — hergebruikt voor
# zowel het melden (BugDialog) als het bekijken (dit bestand) van cases.
# Hardcoded (i.p.v. env var) zodat dit ook werkt op machines waar de app
# via de setup geïnstalleerd wordt, zonder extra configuratiestap.
TOKEN = "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"

class GitHubCasesClient:
    def __init__(self):
        self.token = "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"
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