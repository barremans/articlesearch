# =============================================================================
# ArticleSearch
# File:    artbp_info.py
# Role:    Haalt artikels op die gekoppeld zijn aan een leverancier (BP),
#          via de ArtBpSearch-webservice (config KX9RLR). Gezocht wordt
#          altijd op CardCode (uniek, @CardName blijft leeg). Gebruikt door
#          ui_bp_articles_tab.py (tab "Artikels" in het BP-venster).
# Version: 1.0.2
# Author:  Bart Bossuyt
# Changes: 1.0.2 — Documentatie bijgewerkt: "FrgnName" wordt hier nog steeds
#                   opgehaald/doorgegeven (blijft deel van de API-respons),
#                   maar wordt sinds ui_bp_articles_tab.py v1.3.0 niet meer
#                   getoond in de UI (kolom "Omschrijving (Frgn)"
#                   verwijderd op vraag van gebruiker). Geen functionele
#                   wijziging in dit bestand.
# Changes: 1.0.1 — Documentatie bijgewerkt: API-respons bevat nu ook
#                   "SuppCatNum" (leveranciersartikelnummer). Geen
#                   functionele wijziging in dit bestand (velden worden hier
#                   ongewijzigd/plat doorgegeven; kolomweergave zit in
#                   ui_bp_articles_tab.py).
# Changes: 1.0.0 — Initiële versie (ART-BP-1). Response-vorm:
#                   {"Data": [{"Item": {...velden...}}, ...]} — elk element
#                   wordt uitgepakt uit de "Item"-wrapper tot een platte lijst
#                   van dicts (ItemCode, ItemName, FrgnName, ItmsGrpCod,
#                   ItmsGrpNam, UserText, LastPurPrc, LastPurCur, CardCode,
#                   CardName, QtyPurchasedLast6Months,
#                   QtyPurchasedLast12Months).
# =============================================================================
import json
import logging
import requests
import urllib3
from artbp_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("ArticleSearch.ArtBpInfo")


def get_supplier_articles(card_code: str) -> list:
    """
    Haalt de artikels op die gekoppeld zijn aan de leverancier met de
    opgegeven CardCode. Retourneert een lijst van platte item-dicts
    (nooit None — lege lijst bij geen resultaten).
    """
    env_config = API_ENVIRONMENTS[ENVIRONMENT]
    url = f"{env_config['base_url']}/api/datarequest"
    config_id = env_config["artbp_configP_id"]

    payload = json.dumps({
        "ConfigurationID": config_id,
        "MultiKey": {
            "@CardCode": (card_code or "").strip(),
            "@CardName": ""
        }
    })

    headers = get_auth_header()

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Fout tijdens verzoek naar ArtBpSearch: {e}")

    if isinstance(data, dict) and data.get("IsError"):
        raise ValueError(f"API-fout: {data.get('ErrorMessage')}")

    raw_list = data.get("Data") if isinstance(data, dict) else data
    if not isinstance(raw_list, list):
        return []

    articles = []
    for entry in raw_list:
        if not isinstance(entry, dict):
            continue
        item = entry.get("Item", entry)  # uitpakken uit de "Item"-wrapper
        if isinstance(item, dict):
            articles.append(item)

    logger.info(
        "Artikels opgehaald voor CardCode=%s: %d resultaten",
        card_code, len(articles)
    )
    return articles