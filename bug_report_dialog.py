# =============================================================================
# ArticleSearch
# File:    bug_report_dialog.py
# Role:    BugDialog (QDialog) — laat de gebruiker een bug of feature-
#          aanvraag melden. Het verzenden zelf gebeurt door
#          GitHubFeedbackClient (github_feedback.py): de melding wordt een
#          GitHub Issue. Dit bestand bevat geen token en geen repo-naam
#          meer en is identiek in elke app; app-specifieke zaken (repo,
#          naam van de melder) komen uit github_feedback_config.py.
# Version: 2.0.0
# Author:  Bart Bossuyt
# Changes: 2.0.0 — SECURITY/BUGFIX: hardcoded GitHub-token verwijderd.
#                   Oorzaak van de terugkerende 401-fouten bleek GitHub
#                   Secret Scanning: elk token dat in de (publieke) repo
#                   gepusht werd, werd automatisch ingetrokken (bevestigd
#                   via de security log van het GitHub-account, 2026-10-10).
#                   Het token staat nu in het niet-getrackte bestand
#                   github_secret_local.py en wordt gelezen door
#                   github_feedback.py.
#                   De klasse GitHubClient is uit dit bestand verdwenen en
#                   vervangen door GitHubFeedbackClient (github_feedback.py).
#                   GEWIJZIGD GEDRAG: een melding is voortaan altijd een
#                   Issue — bug met label "bug", feature met label
#                   "enhancement". Er wordt geen branch, .md-bestand of
#                   Pull Request meer aangemaakt; de regel "Bestandsnaam"
#                   is daarom uit de voorvertoning verdwenen. Reden: zo
#                   heeft het token enkel het recht "Issues" nodig en geen
#                   schrijfrechten op de code van de repo.
#                   De naam van de melder komt nu via
#                   github_feedback_config.get_reporter_name() (zelfde
#                   gedrag als v1.4.0: AD-naam vooringevuld en read-only,
#                   anders leeg en bewerkbaar).
#                   Kleine verbeteringen: wachtcursor tijdens het verzenden,
#                   en duidelijke Nederlandstalige foutmeldingen i.p.v. de
#                   ruwe "401 Client Error ..."-tekst.
#                   BugDialog(parent, initial_type, initial_description) is
#                   ongewijzigd — bestaande aanroepen (ui_main.py,
#                   ui_peppol.py) blijven werken zonder aanpassing.
# Changes: 1.4.0 — Het "Je naam"-veld wordt nu automatisch voorgevuld met
#                   de displayName van de ingelogde Azure AD-gebruiker
#                   (`permissions_azure.get_current_user_display_name()`,
#                   gecached sinds de AD-login bij app-start) en read-only
#                   gemaakt zodra dat gelukt is — de gebruiker hoeft zijn
#                   naam dan niet meer manueel te typen. **Fallback**: als
#                   er (nog) geen gecachede gebruikersnaam is (bv. AD-login
#                   niet gelukt/overgeslagen), blijft het veld leeg én
#                   bewerkbaar zoals voorheen — anders zou een gebruiker
#                   nooit meer een melding kunnen indienen in dat geval.
#                   Geen wijziging aan `submit_report()` zelf: die leest
#                   nog steeds gewoon `self.name_input.text()`.
# Changes: 1.3.0 — BUGFIX: hardcoded token gaf op 2026-08-31 een bevestigde
#                   401 Unauthorized bij _get_commit_sha() (GET
#                   .../git/ref/heads/main), gemeld via "Meld via GitHub"
#                   (screenshot). Vervangen door een echt nieuw token
#                   (ghp_FZlpfbWf...) — zelfde structurele les als sessie
#                   23: een 401 wordt nooit opgelost door hetzelfde token
#                   opnieuw te gebruiken, enkel door een vers gegenereerd
#                   token. Zelfde nieuwe token ook toegepast in
#                   github_cases.py (v1.3.0). Geen architecturale
#                   wijziging — blijft bewust hardcoded op beide plekken
#                   (geen centrale env var), zelfde afweging als eerder
#                   (setup/installer-verspreiding maakt per-machine
#                   configuratie onhaalbaar).
# Changes: 1.1.0 — Documentatie-update: het hardcoded token gaf op
#                   2026-08-06 tijdelijk een 401 (zie sessie 20), maar is
#                   door de gebruiker bevestigd als momenteel geldig/
#                   werkend token — zelfde token nu ook hergebruikt in
#                   github_cases.py (v1.1.0), i.p.v. de tussentijdse
#                   env-var-aanpak daar. Geen functionele wijziging aan dit
#                   bestand.
# Changes: 1.0.0 — Eerste keer onder versiebeheer. BugDialog.__init__()
#                   uitgebreid met optionele parameters initial_type
#                   ("Bugmelding"/"Feature-aanvraag") en
#                   initial_description — laat aanroepende code (bv. het
#                   Peppol-controlescherm bij een onbekende foutcode) de
#                   dialoog vooraf invullen. Backward-compatible: bestaande
#                   aanroepen zonder deze parameters (BugDialog(parent))
#                   werken ongewijzigd — velden blijven dan leeg zoals
#                   voorheen.
# =============================================================================
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QLineEdit, QComboBox
)

import github_feedback_config
from github_feedback import (
    GitHubFeedbackClient, GitHubFeedbackError,
    REPORT_TYPE_BUG, REPORT_TYPE_FEATURE, REPORT_TYPES,
    build_title, build_body,
)


# BugDialog GUI
class BugDialog(QDialog):
    def __init__(self, parent=None, initial_type: str | None = None, initial_description: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Bug of Feature melden")
        self.setMinimumSize(400, 450)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Type melding:"))
        self.type_select = QComboBox()
        self.type_select.addItems([REPORT_TYPE_BUG, REPORT_TYPE_FEATURE])
        if initial_type in REPORT_TYPES:
            self.type_select.setCurrentText(initial_type)
        layout.addWidget(self.type_select)

        layout.addWidget(QLabel("Je naam:"))
        self.name_input = QLineEdit()
        # Automatisch voorvullen met de ingelogde gebruiker + read-only
        # maken, mét fallback (leeg/bewerkbaar) als er geen naam bekend is.
        current_user_name = github_feedback_config.get_reporter_name()
        if current_user_name:
            self.name_input.setText(current_user_name)
            self.name_input.setReadOnly(True)
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Omschrijf de melding:"))
        self.text_edit = QTextEdit()
        if initial_description:
            self.text_edit.setPlainText(initial_description)
        layout.addWidget(self.text_edit)

        submit_btn = QPushButton("Verzenden")
        submit_btn.clicked.connect(self.submit_report)
        layout.addWidget(submit_btn)

    def submit_report(self):
        description = self.text_edit.toPlainText().strip()
        reporter = self.name_input.text().strip()
        report_type = self.type_select.currentText().strip()

        if not reporter:
            QMessageBox.warning(self, "Fout", "Je naam moet ingevuld zijn.")
            return

        if not description:
            QMessageBox.warning(self, "Fout", "De beschrijving mag niet leeg zijn.")
            return

        # Preview tonen (zelfde titel/tekst als wat effectief verzonden wordt)
        preview_text = (
            f"🔖 Titel: {build_title(description, report_type)}\n\n"
            f"📝 Beschrijving:\n{build_body(reporter, description, report_type)}\n\n"
            f"Doorgaan met verzenden?"
        )

        reply = QMessageBox.question(self, "Voorvertoning", preview_text, QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            url = GitHubFeedbackClient().submit_report(reporter, description, report_type)
            error = None
        except GitHubFeedbackError as e:
            url, error = None, str(e)
        except Exception as e:
            url, error = None, f"Onverwachte fout bij het verzenden:\n{e}"
        finally:
            QApplication.restoreOverrideCursor()

        if error:
            QMessageBox.critical(self, "GitHub Fout", error)
            return

        QMessageBox.information(self, "Verzonden", f"{report_type} verzonden:\n{url}")
        self.accept()
