# bug_report_dialog.py
import requests
import base64
import uuid
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QLineEdit, QComboBox
)

# GitHubClient klasse
class GitHubClient:
    def __init__(self):
        self.token = "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"
        self.owner = "barremans"
        self.repo = "articlesearch"
        self.base_branch = "main"

        self.api_base = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        }

    def submit_report(self, reporter: str, description: str, report_type: str) -> str:
        is_feature = report_type.lower() == "feature-aanvraag"
        prefix = "feature" if is_feature else "bug"
        label = "enhancement" if is_feature else "bug"
        branch_name = f"{prefix}-{uuid.uuid4().hex[:8]}"
        file_path = f"{prefix}s/{branch_name}.md"
        commit_msg = f"{'✨ Feature-aanvraag' if is_feature else '🪲 Bugmelding'}: {description[:50]}"
        pr_title = f"{'✨ Feature' if is_feature else '🐞 Bug'}: {description[:50]}"
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        body_text = (
            f"Automatisch gegenereerde {report_type.lower()} door {reporter or 'onbekend'} op {date_str}:\n\n{description}"
        )

        # Commit melding als bestand in de repo
        file_url = f"{self.api_base}/contents/{file_path}"
        content = f"**Type:** {report_type}\n**Reporter:** {reporter or 'onbekend'}\n**Datum:** {date_str}\n\n**Beschrijving:**\n\n{description}"
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        commit_sha = self._get_commit_sha()
        self._create_branch(branch_name, commit_sha)
        file_data = {
            "message": commit_msg,
            "content": encoded_content,
            "branch": branch_name
        }
        file_res = requests.put(file_url, json=file_data, headers=self.headers)
        file_res.raise_for_status()

        if is_feature:
            # Maak Pull Request aan
            pr_url = f"{self.api_base}/pulls"
            pr_data = {
                "title": pr_title,
                "body": body_text,
                "head": branch_name,
                "base": self.base_branch
            }
            pr_res = requests.post(pr_url, json=pr_data, headers=self.headers)
            pr_res.raise_for_status()

            pr_number = pr_res.json()["number"]
            label_url = f"{self.api_base}/issues/{pr_number}/labels"
            label_data = {"labels": [label]}
            label_res = requests.post(label_url, json=label_data, headers=self.headers)
            label_res.raise_for_status()

            return pr_res.json().get("html_url", "Pull Request aangemaakt maar geen URL ontvangen.")
        else:
            # Maak een Issue aan voor bugs
            issue_url = f"{self.api_base}/issues"
            issue_data = {
                "title": pr_title,
                "body": body_text,
                "labels": [label]
            }
            issue_res = requests.post(issue_url, json=issue_data, headers=self.headers)
            issue_res.raise_for_status()

            return issue_res.json().get("html_url", "Issue succesvol aangemaakt maar geen URL ontvangen.")

    def _get_commit_sha(self) -> str:
        ref_url = f"{self.api_base}/git/ref/heads/{self.base_branch}"
        ref_res = requests.get(ref_url, headers=self.headers)
        ref_res.raise_for_status()
        return ref_res.json()["object"]["sha"]

    def _create_branch(self, branch_name: str, commit_sha: str):
        create_ref_url = f"{self.api_base}/git/refs"
        new_ref = {
            "ref": f"refs/heads/{branch_name}",
            "sha": commit_sha
        }
        create_res = requests.post(create_ref_url, json=new_ref, headers=self.headers)
        create_res.raise_for_status()

# BugDialog GUI
class BugDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bug of Feature melden")
        self.setMinimumSize(400, 450)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Type melding:"))
        self.type_select = QComboBox()
        self.type_select.addItems(["Bugmelding", "Feature-aanvraag"])
        layout.addWidget(self.type_select)

        layout.addWidget(QLabel("Je naam:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Omschrijf de melding:"))
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        submit_btn = QPushButton("Verzenden")
        submit_btn.clicked.connect(self.submit_report)
        layout.addWidget(submit_btn)

    def submit_report(self):
        description = self.text_edit.toPlainText().strip()
        reporter = self.name_input.text().strip()
        report_type = self.type_select.currentText().strip()

        if not description:
            QMessageBox.warning(self, "Fout", "De beschrijving mag niet leeg zijn.")
            return

        # Preview tonen
        file_type = "features" if report_type == "Feature-aanvraag" else "bugs"
        filename = f"{file_type}/{report_type.lower()}-{uuid.uuid4().hex[:8]}.md"
        pr_title = f"{'✨ Feature' if report_type == 'Feature-aanvraag' else '🐞 Bug'}: {description[:50]}"
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        pr_body = (
            f"Automatisch gegenereerde {report_type.lower()} door {reporter or 'onbekend'} op {date_str}:\n\n{description}"
        )

        preview_text = (
            f"📄 Bestandsnaam: {filename}\n\n"
            f"🔖 Titel: {pr_title}\n\n"
            f"📝 Beschrijving:\n{pr_body}\n\n"
            f"Doorgaan met verzenden?"
        )

        reply = QMessageBox.question(self, "Voorvertoning", preview_text, QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            gh = GitHubClient()
            url = gh.submit_report(reporter, description, report_type)
            QMessageBox.information(self, "Verzonden", f"{report_type} verzonden:\n{url}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "GitHub Fout", str(e))
