# =============================================================================
# ArticleSearch
# File:    prod_token.py
# Role:    Auth-headers voor Prod Stock Overview (search-type "Prod") — twee
#          onafhankelijke API-clients:
#            - "ProdDataset" (client_id "Datasetprod")       -> dataset
#              opvragen/aanmaken/bijwerken (prod_info.list_datasets() /
#              prod_info.save_dataset())
#            - "ProdStock"   (client_id "ProdStockOverview")  -> artikel-
#              stock-overzicht per dataset (prod_info.get_prod_stock_overview())
#          Elk met een eigen TokenManager-instantie, zelfde patroon als
#          auth.py (get_auth_header/get_auth_header_bps).
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Initiële versie.
# =============================================================================
from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager

base_url = API_ENVIRONMENTS[ENVIRONMENT]["base_url"]

# --- Dataset-client (Datasetprod): opvragen + aanmaken/bijwerken van datasets ---
_dataset_cfg = API_CLIENTS.get("ProdDataset", {}).get(ENVIRONMENT)
prod_dataset_token = (
    TokenManager(
        client_id=_dataset_cfg["client_id"],
        client_secret=_dataset_cfg["client_secret"],
        base_url=base_url
    )
    if _dataset_cfg else None
)

# --- Stock-client (ProdStockOverview): artikel-stock-overzicht ---
_stock_cfg = API_CLIENTS.get("ProdStock", {}).get(ENVIRONMENT)
prod_stock_token = (
    TokenManager(
        client_id=_stock_cfg["client_id"],
        client_secret=_stock_cfg["client_secret"],
        base_url=base_url
    )
    if _stock_cfg else None
)


def get_auth_header_dataset() -> dict:
    """Auth headers voor dataset opvragen/aanmaken/bijwerken (client 'ProdDataset')."""
    if not prod_dataset_token:
        raise RuntimeError(
            "ProdDataset-client ontbreekt in API_CLIENTS voor omgeving "
            f"'{ENVIRONMENT}'. Voeg API_CLIENTS['ProdDataset']['{ENVIRONMENT}'] toe in config.py."
        )
    return prod_dataset_token.get_auth_header()


def get_auth_header_stock() -> dict:
    """Auth headers voor het artikel-stock-overzicht (client 'ProdStock')."""
    if not prod_stock_token:
        raise RuntimeError(
            "ProdStock-client ontbreekt in API_CLIENTS voor omgeving "
            f"'{ENVIRONMENT}'. Voeg API_CLIENTS['ProdStock']['{ENVIRONMENT}'] toe in config.py."
        )
    return prod_stock_token.get_auth_header()


def preload_tokens():
    """Optioneel: beide tokens vooraf laden (niet aangeroepen vanuit main.py —
    Prod Stock Overview volgt bewust het 'geen data bij openen'-patroon, dus
    ook geen preload bij app-start nodig)."""
    try:
        if prod_dataset_token:
            prod_dataset_token.ensure_token()
        if prod_stock_token:
            prod_stock_token.ensure_token()
    except Exception:
        pass
