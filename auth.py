# auth.py
from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager

# --- Base URL voor alle clients ---
base_url = API_ENVIRONMENTS[ENVIRONMENT]["base_url"]

# --- Default (ArticleSearch) client: alles behalve BP-zoeklijst ---
_article_cfg = API_CLIENTS["ArticleSearch"][ENVIRONMENT]
article_token = TokenManager(
    client_id=_article_cfg["client_id"],
    client_secret=_article_cfg["client_secret"],
    base_url=base_url
)

def get_auth_header():
    """Auth headers voor standaard calls (artikels, project, cc, ...)."""
    return article_token.get_auth_header()

def preload_token():
    """Optioneel: preload standaard token bij app-start."""
    article_token.ensure_token()


# --- BpS client: ENKEL voor BP-zoeklijst (MIN search data) ---
# Zorgt ervoor dat alleen BP-search een andere client gebruikt.
_bps_cfg_env = API_CLIENTS.get("BpS", {}).get(ENVIRONMENT)
bps_token = (
    TokenManager(
        client_id=_bps_cfg_env["client_id"],
        client_secret=_bps_cfg_env["client_secret"],
        base_url=base_url
    )
    if _bps_cfg_env else None
)

def get_auth_header_bps():
    """
    Auth headers voor BP-zoeklijst (MIN data).
    Gebruik deze ALLEEN wanneer kind == 'bp' in data_request.py.
    """
    if not bps_token:
        raise RuntimeError(
            "BpS client ontbreekt in API_CLIENTS voor omgeving "
            f"'{ENVIRONMENT}'. Voeg API_CLIENTS['BpS']['{ENVIRONMENT}'] toe in config.py."
        )
    return bps_token.get_auth_header()
