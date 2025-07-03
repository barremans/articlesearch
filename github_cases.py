# github_cases.py

import requests
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QMessageBox

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
