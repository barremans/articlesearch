# cc_token.py
import logging
import time

from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager

# Basisconfig voor CreditControl
env_cfg     = API_ENVIRONMENTS[ENVIRONMENT]
base_url    = env_cfg["base_url"]
client_cfg  = API_CLIENTS["Cc"][ENVIRONMENT]

_cc_token = TokenManager(
    client_id     = client_cfg["client_id"],
    client_secret = client_cfg["client_secret"],
    base_url      = base_url,
)

def get_cc_auth_header() -> dict:
    """Authorization header voor CreditControl calls."""
    return _cc_token.get_auth_header()

def preload_cc_token(retries: int = 3, delay: int = 2) -> None:
    """Eventueel bij start alvast een CC-token ophalen."""
    logging.info("[CC] Vooraf token laden…")
    for attempt in range(1, retries + 1):
        try:
            _cc_token.ensure_token()
            logging.info(f"[CC] Token geladen (poging {attempt})")
            return
        except Exception as e:
            logging.warning(f"[CC] Token poging {attempt} mislukt: {e}")
            if attempt < retries:
                time.sleep(delay)
    logging.error("[CC] Kan geen token verkrijgen.")
