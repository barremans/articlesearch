# =============================================================================
# ArticleSearch
# File:    artbp_token.py
# Role:    Auth-headers voor de "ArtBpSearch"-client (artikels gekoppeld aan
#          een leverancier/BP). Aparte TokenManager-instantie, analoog aan
#          stock_token.py — zo blijft elke databron zijn eigen OAuth-client
#          houden voor granulaire toegangscontrole.
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Initiële versie (ART-BP-1).
# =============================================================================
from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager
import logging
import time

base_url = API_ENVIRONMENTS[ENVIRONMENT]["base_url"]
client_config = API_CLIENTS["ArtBpSearch"][ENVIRONMENT]

artbp_token = TokenManager(
    client_id=client_config["client_id"],
    client_secret=client_config["client_secret"],
    base_url=base_url
)


def get_auth_header():
    return artbp_token.get_auth_header()


def preload_token(retries: int = 3, delay: int = 2):
    logging.info("[Startup] Vooraf token laden voor ArtBpSearch...")
    for attempt in range(1, retries + 1):
        try:
            artbp_token.ensure_token()
            return
        except Exception as e:
            logging.warning(f"[ArtBpSearch] Token poging {attempt} mislukt: {e}")
            if attempt < retries:
                time.sleep(delay)
    logging.error("[ArtBpSearch] Kan geen token verkrijgen na meerdere pogingen.")