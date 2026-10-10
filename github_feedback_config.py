# =============================================================================
# ArticleSearch
# File:    github_feedback_config.py
# Role:    App-specifieke instellingen voor het uniforme GitHub-
#          feedbackpakket (github_feedback.py / bug_report_dialog.py /
#          github_cases.py): naam van de app, doelrepo voor de meldingen,
#          en hoe de naam van de melder en de app-versie bepaald worden.
#          Dit is het ENIGE bestand van het pakket dat per app verschilt
#          (naast github_secret_local.py, dat het token bevat). Bevat geen
#          token en mag dus gewoon in git.
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Eerste versie. Neemt owner/repo over die voorheen
#                   hardcoded in bug_report_dialog.py en github_cases.py
#                   stonden, en de AD-naam-koppeling uit
#                   bug_report_dialog.py v1.4.0.
# =============================================================================
#
# LET OP: importeer hier bovenaan GEEN app-modules (permissions_azure,
# version, ...). check_github_secret.py leest dit bestand ook buiten de app
# om, tijdens de build. App-modules horen enkel BINNEN de functies hieronder.

APP_NAME = "ArticleSearch"
GITHUB_OWNER = "barremans"
GITHUB_REPO = "articlesearch"


def get_reporter_name() -> str:
    """
    Naam voor het veld "Je naam" in het meldscherm. Een niet-lege waarde
    wordt vooringevuld en read-only gemaakt; een lege waarde laat het veld
    leeg en bewerkbaar (zelfde gedrag als bug_report_dialog.py v1.4.0).
    """
    try:
        from permissions_azure import get_current_user_display_name
        return (get_current_user_display_name() or "").strip()
    except Exception:
        return ""


def get_app_version() -> str:
    """Versie van de app, vermeld in de kopregel van elke melding."""
    try:
        from version import __version__
        return str(__version__)
    except Exception:
        return ""
