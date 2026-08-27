# =============================================================================
# ArticleSearch
# File:    duepayment_token.py
# Role:    Token-laag voor "Betalingsgedrag & Openstaande Posten" (PaymentsDue)
#          — 2 aparte OAuth-achtige clients tegen de centrale CGK-API, naar
#          analogie van het meerdere-clients-in-1-bestand-patroon uit auth.py:
#            - DuePaymentDetail   -> per-klant gemiddelden (config UIY02H)
#            - DuePaymentOverview -> per-document detail   (config YCT5LR)
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Eerste versie.
# =============================================================================
import logging
import time

from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager

env_config = API_ENVIRONMENTS[ENVIRONMENT]
base_url = env_config["base_url"]

# --- Client: DuePaymentDetail (1 rij per klant, config UIY02H) ---
_detail_cfg = API_CLIENTS.get("DuePaymentDetail", {}).get(ENVIRONMENT)
detail_token = (
    TokenManager(
        client_id=_detail_cfg["client_id"],
        client_secret=_detail_cfg["client_secret"],
        base_url=base_url,
    )
    if _detail_cfg else None
)


def get_auth_header_detail() -> dict:
    """Auth headers voor de PaymentsDue-Detail-databron (per klant, UIY02H)."""
    if not detail_token:
        raise RuntimeError(
            "DuePaymentDetail-client ontbreekt in API_CLIENTS voor omgeving "
            f"'{ENVIRONMENT}'. Voeg API_CLIENTS['DuePaymentDetail']['{ENVIRONMENT}'] "
            "toe in config.py."
        )
    return detail_token.get_auth_header()


# --- Client: DuePaymentOverview (1 rij per document, config YCT5LR) ---
_overview_cfg = API_CLIENTS.get("DuePaymentOverview", {}).get(ENVIRONMENT)
overview_token = (
    TokenManager(
        client_id=_overview_cfg["client_id"],
        client_secret=_overview_cfg["client_secret"],
        base_url=base_url,
    )
    if _overview_cfg else None
)


def get_auth_header_overview() -> dict:
    """Auth headers voor de PaymentsDue-Overview-databron (per document, YCT5LR)."""
    if not overview_token:
        raise RuntimeError(
            "DuePaymentOverview-client ontbreekt in API_CLIENTS voor omgeving "
            f"'{ENVIRONMENT}'. Voeg API_CLIENTS['DuePaymentOverview']['{ENVIRONMENT}'] "
            "toe in config.py."
        )
    return overview_token.get_auth_header()


def preload_tokens(retries: int = 3, delay: int = 2) -> None:
    """
    Optioneel: preload beide PaymentsDue-tokens bij app-start (analoog
    po_token.py). Wordt momenteel nergens automatisch aangeroepen — de
    tokens worden anders gewoon lazy opgehaald bij de eerste 'Ophalen'-klik.
    """
    for name, tm in (("DuePaymentDetail", detail_token), ("DuePaymentOverview", overview_token)):
        if not tm:
            logging.warning(f"[{name}] Client niet geconfigureerd — preload overgeslagen.")
            continue
        for attempt in range(1, retries + 1):
            try:
                tm.ensure_token()
                logging.info(f"[{name}] Token succesvol geladen op poging {attempt}")
                break
            except Exception as e:
                logging.warning(f"[{name}] Token poging {attempt} mislukt: {e}")
                if attempt < retries:
                    time.sleep(delay)
        else:
            logging.error(f"[{name}] Kan geen token verkrijgen na meerdere pogingen.")
