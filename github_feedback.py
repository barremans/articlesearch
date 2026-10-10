# =============================================================================
# GitHub-feedbackpakket (uniform — identiek in elke app)
# File:    github_feedback.py
# Role:    GitHubFeedbackClient — maakt een bug-/feature-melding aan als
#          GitHub Issue en haalt de open meldingen op, via de GitHub REST
#          API. Bevat GEEN Qt en GEEN token: het token komt uit het niet-
#          getrackte bestand github_secret_local.py, de app-naam en de
#          doelrepo uit github_feedback_config.py.
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Eerste versie. Vervangt de GitHubClient-klasse uit
#                   bug_report_dialog.py en de GitHubCasesClient-klasse uit
#                   github_cases.py (beide hadden een hardcoded token).
#                   Achtergrond: GitHub trekt elk token in zodra het in een
#                   publieke repo gepusht wordt (Secret Scanning) — dat was
#                   de oorzaak van de terugkerende 401-fouten. Het token
#                   staat daarom nergens meer in een getrackt bestand.
#                   Een melding is voortaan altijd een Issue (label "bug" of
#                   "enhancement"); er wordt geen branch, bestand of Pull
#                   Request meer aangemaakt. Het token heeft daardoor enkel
#                   het recht "Issues: lezen en schrijven" nodig, en geen
#                   schrijfrechten op de code van de repo.
# =============================================================================
#
# UITROL IN EEN ANDERE APP
# ------------------------
# Identiek kopiëren (niets aanpassen):
#     github_feedback.py, bug_report_dialog.py, github_cases.py,
#     check_github_secret.py, github_secret_local.example.py
# Per app aanpassen:
#     github_feedback_config.py   -> APP_NAME, GITHUB_OWNER, GITHUB_REPO
#     github_secret_local.py      -> het token (NOOIT committen)
# Eenmalig per repo:
#     .gitignore                  -> regel "*_secret_local.py"
#     <app>.spec                  -> controleblok + hiddenimports (zie
#                                    SearchArticle.spec van ArticleSearch)
# Token (GitHub > Settings > Developer settings > Fine-grained tokens):
#     Repository access : Only select repositories -> enkel deze repo
#     Permissions       : Issues = Read and write
#                         Pull requests = Read-only (enkel nodig om oude,
#                         nog openstaande feature-PR's te blijven tonen)
#     Eén token per app. Controleer daarna met:
#         python check_github_secret.py
# =============================================================================

from __future__ import annotations

from datetime import datetime

import requests

import github_feedback_config as _cfg

API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"

REPORT_TYPE_BUG = "Bugmelding"
REPORT_TYPE_FEATURE = "Feature-aanvraag"
REPORT_TYPES = (REPORT_TYPE_BUG, REPORT_TYPE_FEATURE)

LABEL_BUG = "bug"
LABEL_FEATURE = "enhancement"

TITLE_MAX_LEN = 50
PAGE_SIZE = 100
MAX_PAGES = 5


class GitHubFeedbackError(Exception):
    """Fout bij het praten met GitHub, met een voor de gebruiker leesbare tekst."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def load_token() -> str:
    """
    Leest het token uit github_secret_local.py (GITHUB_TOKEN).

    Dat bestand staat in .gitignore en komt dus nooit op GitHub; PyInstaller
    bundelt het wel mee in de exe. Ontbreekt het bestand (bv. een verse
    clone zonder token), dan is het resultaat een lege string — de app
    blijft dan gewoon werken, enkel het verzenden van een melding niet.
    """
    try:
        import github_secret_local
    except ImportError:
        return ""
    return str(getattr(github_secret_local, "GITHUB_TOKEN", "") or "").strip()


def is_feature(report_type: str) -> bool:
    return (report_type or "").strip().lower() == REPORT_TYPE_FEATURE.lower()


def build_title(description: str, report_type: str) -> str:
    """Titel van het Issue: prefix + de eerste regel van de omschrijving."""
    lines = [ln.strip() for ln in (description or "").splitlines() if ln.strip()]
    first_line = " ".join(lines[0].split()) if lines else ""
    prefix = "✨ Feature" if is_feature(report_type) else "🐞 Bug"
    return f"{prefix}: {first_line[:TITLE_MAX_LEN]}"


def build_body(reporter: str, description: str, report_type: str, when: datetime | None = None) -> str:
    """
    Tekst van het Issue. De eerste regel is een kopregel, gevolgd door een
    lege regel en dan de omschrijving — github_cases.clean_body_text() knipt
    die kopregel er bij het tonen weer af, dus dit formaat niet wijzigen.
    """
    date_str = (when or datetime.now()).strftime("%Y-%m-%d %H:%M")
    app = _app_label()
    suffix = f" ({app})" if app else ""
    return (
        f"Automatisch gegenereerde {(report_type or '').lower()} door "
        f"{reporter or 'onbekend'} op {date_str}{suffix}:\n\n{description}"
    )


def _app_label() -> str:
    name = str(getattr(_cfg, "APP_NAME", "") or "").strip()
    version = ""
    getter = getattr(_cfg, "get_app_version", None)
    if callable(getter):
        try:
            version = str(getter() or "").strip()
        except Exception:
            version = ""
    return f"{name} {version}".strip()


class GitHubFeedbackClient:
    def __init__(self, owner: str | None = None, repo: str | None = None,
                 token: str | None = None, timeout: int = 15):
        self.owner = owner or _cfg.GITHUB_OWNER
        self.repo = repo or _cfg.GITHUB_REPO
        self.token = load_token() if token is None else (token or "").strip()
        self.timeout = timeout
        self.api_base = f"{API_ROOT}/repos/{self.owner}/{self.repo}"

    # ------------------------------------------------------------------ intern
    @property
    def has_token(self) -> bool:
        return bool(self.token)

    def _headers(self, with_auth: bool) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if with_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _send(self, method: str, url: str, with_auth: bool, **kwargs) -> requests.Response:
        try:
            return requests.request(method, url, headers=self._headers(with_auth),
                                    timeout=self.timeout, **kwargs)
        except requests.exceptions.RequestException as exc:
            raise GitHubFeedbackError(
                "GitHub is niet bereikbaar. Controleer je internetverbinding "
                f"en probeer opnieuw.\n\nDetail: {exc.__class__.__name__}"
            ) from exc

    @staticmethod
    def _error_for(resp: requests.Response, action: str) -> GitHubFeedbackError:
        code = resp.status_code
        if code == 401:
            text = ("Het GitHub-token van deze versie is ongeldig of ingetrokken. "
                    "Meld dit aan IT: er is een nieuwe versie met een nieuw token nodig.")
        elif code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            text = "GitHub heeft tijdelijk te veel aanvragen ontvangen. Probeer het later opnieuw."
        elif code in (403, 404):
            text = ("Het GitHub-token van deze versie heeft geen toegang tot de repository "
                    "of mist het recht 'Issues'. Meld dit aan IT.")
        elif code == 410:
            text = "Issues staan uitgeschakeld voor deze repository. Meld dit aan IT."
        elif code == 422:
            text = "GitHub weigerde de melding (ongeldige inhoud)."
        else:
            text = "Onverwacht antwoord van GitHub."
        return GitHubFeedbackError(f"{action} is mislukt.\n\n{text}\n\n(HTTP {code})", status_code=code)

    # --------------------------------------------------------------- schrijven
    def submit_report(self, reporter: str, description: str, report_type: str) -> str:
        """Maakt het Issue aan en geeft de URL ervan terug."""
        if not self.has_token:
            raise GitHubFeedbackError(
                "Deze versie bevat geen GitHub-token, daarom kan er geen melding "
                "verzonden worden. Meld dit aan IT."
            )
        payload = {
            "title": build_title(description, report_type),
            "body": build_body(reporter, description, report_type),
            "labels": [LABEL_FEATURE if is_feature(report_type) else LABEL_BUG],
        }
        resp = self._send("POST", f"{self.api_base}/issues", with_auth=True, json=payload)
        if resp.status_code != 201:
            raise self._error_for(resp, "Het verzenden van de melding")
        return resp.json().get("html_url") or "Melding aangemaakt, maar geen URL ontvangen."

    # ------------------------------------------------------------------- lezen
    def _get_page(self, page: int) -> list:
        url = f"{self.api_base}/issues"
        params = {"state": "open", "per_page": PAGE_SIZE, "page": page}
        resp = self._send("GET", url, with_auth=True, params=params)
        if resp.status_code == 401 and self.has_token:
            # Ingetrokken token: een publieke repo is ook zonder token leesbaar.
            # Zo blijft "Open cases" werken, ook als het token ongeldig werd.
            resp = self._send("GET", url, with_auth=False, params=params)
        if resp.status_code != 200:
            raise self._error_for(resp, "Het ophalen van de open meldingen")
        data = resp.json()
        return data if isinstance(data, list) else []

    def get_open_items(self) -> list:
        """Alle open Issues én Pull Requests (GitHub geeft beide via dit endpoint)."""
        items: list = []
        for page in range(1, MAX_PAGES + 1):
            batch = self._get_page(page)
            items.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
        return items

    def get_open_reports(self) -> dict:
        """
        Open meldingen, opgesplitst:
          "bugs"     — Issues zonder label "enhancement"
          "features" — Issues met label "enhancement", plus nog openstaande
                       Pull Requests (zo werden features vroeger aangemaakt)
        """
        bugs, features = [], []
        for item in self.get_open_items():
            labels = {str(lb.get("name", "")).lower() for lb in item.get("labels", []) if isinstance(lb, dict)}
            if "pull_request" in item or LABEL_FEATURE in labels:
                features.append(item)
            else:
                bugs.append(item)
        return {"bugs": bugs, "features": features}
