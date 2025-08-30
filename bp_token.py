# bp_token.py
import logging
import time

from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager

# Haal base_url en client-config op voor de 'Bp' service
env_config    = API_ENVIRONMENTS[ENVIRONMENT]
client_config = API_CLIENTS["Bp"][ENVIRONMENT]
base_url      = env_config["base_url"]

# Maak TokenManager-instance voor Bp
project_token = TokenManager(
    client_id     = client_config["client_id"],
    client_secret = client_config["client_secret"],
    base_url      = base_url
)

def get_auth_header() -> dict:
    """
    Retourneert een dict met Authorization-header:
    {'Authorization': 'Bearer <token>'}
    """
    return project_token.get_auth_header()

def preload_token(retries: int = 3, delay: int = 2) -> None:
    """
    Probeert bij startup alvast een geldig token op te halen,
    met maximaal `retries` pogingen en `delay` seconden ertussen.
    """
    logging.info("[Startup] Vooraf token laden voor Bp…")
    for attempt in range(1, retries + 1):
        try:
            project_token.ensure_token()
            logging.info(f"[Bp] Token succesvol geladen op poging {attempt}")
            return
        except Exception as e:
            logging.warning(f"[Bp] Token poging {attempt} mislukt: {e}")
            if attempt < retries:
                time.sleep(delay)
    logging.error("[Bp] Kan geen token verkrijgen na meerdere pogingen.")
