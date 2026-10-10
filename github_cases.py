# =============================================================================
# ArticleSearch
# File:    github_cases.py
# Role:    show_github_cases() — toont de open bugmeldingen en feature-
#          aanvragen uit de repo, opgehaald door GitHubFeedbackClient
#          (github_feedback.py). Dit bestand bevat geen token en geen
#          repo-naam meer en is identiek in elke app.
# Version: 2.0.0
# Author:  Bart Bossuyt
# Changes: 2.0.0 — SECURITY/BUGFIX: hardcoded GitHub-token verwijderd
#                   (zelfde oorzaak en aanpak als bug_report_dialog.py
#                   v2.0.0: GitHub Secret Scanning trok elk gepusht token
#                   in). De klasse GitHubCasesClient is verdwenen en
#                   vervangen door GitHubFeedbackClient (github_feedback.py).
#                   GEWIJZIGD GEDRAG: de twee rubrieken heten nu "Open
#                   bugmeldingen" en "Open feature-aanvragen" (was: "Open
#                   Issues" / "Open Pull Requests"), omdat een feature
#                   voortaan ook een Issue is. Oude, nog openstaande
#                   feature-Pull Requests blijven gewoon zichtbaar onder
#                   "Open feature-aanvragen".
#                   ROBUUSTER: is het token ongeldig geworden, dan wordt de
#                   (publieke) repo zonder token gelezen — dit scherm blijft
#                   dus werken, ook bij een ingetrokken token.
#                   De tekst van een melding wordt nu ge-escaped vóór ze als
#                   HTML getoond wordt (tekens als < en > in bv. een ruwe
#                   Peppol-boodschap braken voorheen de weergave).
#                   show_github_cases(parent) is ongewijzigd qua aanroep.
# Changes: 1.3.0 — BUGFIX: hardcoded token gaf op 2026-08-31 een bevestigde
#                   401 Unauthorized (gemeld via "Meld via GitHub",
#                   screenshot — zelfde onderliggende oorzaak als bij
#                   bug_report_dialog.py). Vervangen door een echt nieuw
#                   token (ghp_FZlpfbWf...), zelfde token als in
#                   bug_report_dialog.py v1.3.0. Structurele les (herhaald
#                   uit sessie 23): een 401 wordt nooit opgelost door
#                   hetzelfde token opnieuw te gebruiken.
#                   OPKUIS: dode, ongebruikte module-level `TOKEN`-constante
#                   verwijderd — die verwees nog naar het allereerste,
#                   allang vervallen token uit sessie 20/21
#                   ("ghp_0wmMscwn1p...") en werd nergens effectief
#                   gebruikt (GitHubCasesClient.__init__() had altijd al
#                   zijn eigen, aparte self.token). Puur verwarrende dode
#                   code, geen functionele wijziging door de verwijdering.
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

import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QTextBrowser, QPushButton, QMessageBox
)

from github_feedback import GitHubFeedbackClient, GitHubFeedbackError


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


def _items_to_html(items: list, empty_text: str) -> str:
    if not items:
        return f"{empty_text}<br>"
    text = ""
    for item in items:
        cleaned = clean_body_text(item.get("body") or "")
        if not cleaned:
            cleaned = (item.get("title") or "").strip()
        cleaned = html.escape(cleaned).replace("\n", "<br>")
        text += f"- {cleaned}<br><br>"
    return text


def show_github_cases(parent):
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        reports = GitHubFeedbackClient().get_open_reports()
        error = None
    except GitHubFeedbackError as e:
        reports, error = None, str(e)
    except Exception as e:
        reports, error = None, str(e)
    finally:
        QApplication.restoreOverrideCursor()

    if error:
        QMessageBox.critical(parent, "GitHub Fout", f"Kon open cases niet ophalen:\n{error}")
        return

    text = "<b><u>🐞 Open bugmeldingen</u></b><br><br>"
    text += _items_to_html(reports["bugs"], "Geen open bugmeldingen.")
    text += "<br><b><u>✨ Open feature-aanvragen</u></b><br><br>"
    text += _items_to_html(reports["features"], "Geen open feature-aanvragen.")

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
