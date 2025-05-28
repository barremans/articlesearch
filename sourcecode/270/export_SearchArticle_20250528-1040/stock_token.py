# stock_token.py
from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager
import logging
import time

# Eerst base_url ophalen
base_url = API_ENVIRONMENTS[ENVIRONMENT]["base_url"]
client_config = API_CLIENTS["StockInfo"][ENVIRONMENT]

# TokenManager instantie
stock_token = TokenManager(
    client_id=client_config["client_id"],
    client_secret=client_config["client_secret"],
    base_url=base_url
)

def get_auth_header():
    return stock_token.get_auth_header()

def preload_token():
    stock_token.ensure_token()

def preload_token(retries=3, delay=2):
    logging.info("[Startup] Vooraf token laden voor StockInfo...")
    for attempt in range(1, retries + 1):
        try:
            stock_token.ensure_token()
            return
        except Exception as e:
            logging.warning(f"[StockInfo] Token poging {attempt} mislukt: {e}")
            if attempt < retries:
                time.sleep(delay)
    logging.error("[StockInfo] Kan geen token verkrijgen na meerdere pogingen.")