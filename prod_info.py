# =============================================================================
# ArticleSearch
# File:    prod_info.py
# Role:    Business-logica voor Prod Stock Overview (search-type "Prod"):
#            - list_datasets()        : datasets opvragen (optioneel
#                                        gefilterd op naam en/of eigenaar),
#                                        via het generieke /api/datarequest
#                                        endpoint (ConfigurationID "BAEIG0").
#            - save_dataset()         : dataset aanmaken/bijwerken (upsert
#                                        via CODE) via het aparte import-
#                                        endpoint (NIET /api/datarequest).
#            - next_dataset_code()    : eerstvolgende vrije DS_Code bepalen.
#            - parse_artnbr()/build_items_string() : conversie tussen de
#                                        ruwe "DS_ArtNbr"-tekst (",\r\n"-
#                                        gescheiden) en een schone Python-
#                                        lijst van artikelcodes.
#            - get_prod_stock_overview(): stock-overzicht per artikelcode
#                                        opvragen (ConfigurationID "VX3PMC",
#                                        client "ProdStockOverview").
# Version: 1.3.0
# Author:  Bart Bossuyt
# Changes: 1.3.0 — BUGFIX (bevestigd door gebruiker, screenshot database):
#                   "Normaliseren"/plak-normalisatie in
#                   ui_prod_datasets_dialog.py leek niet te werken — de
#                   enters kwamen bij het opslaan altijd terug in
#                   DS_ArtNbr. Oorzaak: build_items_string() gebruikte nog
#                   steeds "\r\n," als scheidingsteken (_ITEM_JOIN_SEP),
#                   ongeacht wat er al genormaliseerd was in het veld.
#                   _ITEM_JOIN_SEP aangepast naar een pure komma (",").
#                   Geldt zowel voor het opslaan van datasets (ARTNBR) als
#                   voor het opvragen van het stock-overzicht (@items) —
#                   in beide gevallen splitst de backend toch al op komma
#                   (parameter "@del": ","), dus functioneel geen verschil
#                   daar. parse_artnbr() bleef ongewijzigd en leest beide
#                   formaten (met/zonder "\r\n") nog steeds correct in,
#                   dus bestaande datasets met de oude opmaak blijven
#                   werken.
# Changes: 1.2.0 — save_dataset() werkt DS_ChangeDate nu automatisch bij
#                   met het huidige tijdstip ("CHANGEDATE",
#                   "YYYY-MM-DD HH:MM:SS") bij elke create/update. ⚠️
#                   Aanname: veldnaam/formaat niet bevestigd via een
#                   aangeleverd voorbeeld — zie docstring bij save_dataset().
# Changes: 1.1.0 — normalize_pasted_items() toegevoegd: normaliseert een
#                   geplakte/getypte lijst artikelnummers (willekeurig
#                   scheidingsteken — spatie, tab, puntkomma, regeleinde, of
#                   een mix) naar één lange, komma-gescheiden string zonder
#                   witruimte/enters. Gebruikt in ui_prod_datasets_dialog.py
#                   (automatisch bij plakken in het artikelnummers-veld, en
#                   via de "Normaliseren"-knop).
# Changes: 1.0.0 — Initiële versie.
# =============================================================================
import json
import logging
import re
import requests
import urllib3
from datetime import datetime

from config import API_ENVIRONMENTS, ENVIRONMENT
from prod_token import get_auth_header_dataset, get_auth_header_stock

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("ArticleSearch.ProdInfo")
if not logger.handlers:
    h = logging.StreamHandler()
    f = logging.Formatter("[%(levelname)s] %(asctime)s - [ArticleSearch.ProdInfo] %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# Items binnen "DS_ArtNbr"/"@items" werden in de aangeleverde voorbeeld-
# data (dblist.txt/search_prodArt.txt) aan elkaar geplakt met
# "artikel1\r\n,artikel2\r\n,artikel3" — de "\r\n" bleek daar louter opmaak
# (backend splitst zelf op komma, parameter "@del": ","). BUG (bevestigd
# door gebruiker, 2026-08-31): build_items_string() gebruikte dit "\r\n,"
# nog steeds als scheidingsteken bij het OPSLAAN, waardoor de enters altijd
# terugkwamen in DS_ArtNbr — ook nadat het artikelnummers-veld via plakken/
# "Normaliseren" al naar een zuivere komma-string was omgezet. Nu een pure
# komma, consistent met normalize_pasted_items(). parse_artnbr() blijft
# BEIDE formaten (met en zonder "\r\n") correct inlezen, dus bestaande
# datasets met de oude opmaak blijven gewoon werken.
_ITEM_JOIN_SEP = ","


def _env() -> dict:
    return API_ENVIRONMENTS[ENVIRONMENT]


def _base_url() -> str:
    return _env()["base_url"].rstrip("/")


def _dataset_config_id() -> str:
    cid = _env().get("prod_dataset_configP_id")
    if not cid:
        raise RuntimeError(
            f"Ontbrekende config 'prod_dataset_configP_id' in API_ENVIRONMENTS['{ENVIRONMENT}']."
        )
    return cid


def _stock_config_id() -> str:
    cid = _env().get("prod_stock_configP_id")
    if not cid:
        raise RuntimeError(
            f"Ontbrekende config 'prod_stock_configP_id' in API_ENVIRONMENTS['{ENVIRONMENT}']."
        )
    return cid


def _import_path() -> str:
    return _env().get("prod_dataset_import_path", "/api/import/DATAPROD/U/dbname/SBOCGKLIVE")


# ----------------------------------------------------------------------
# Helpers: artikelcode-lijst <-> ruwe "DS_ArtNbr"/"@items"-tekst
# ----------------------------------------------------------------------
def parse_artnbr(raw) -> list:
    """
    Zet de ruwe DS_ArtNbr-tekst (of @items-tekst) om naar een schone lijst
    van artikelcodes. Robuust tegen ",\\r\\n"-, los "\\n"- of los ","-
    gescheiden varianten.
    """
    if not raw:
        return []
    cleaned = str(raw).replace("\r\n", "\n").replace("\r", "\n")
    items = []
    for line in cleaned.split("\n"):
        for part in line.split(","):
            part = part.strip()
            if part:
                items.append(part)
    return items


def build_items_string(items: list) -> str:
    """Zet een lijst artikelcodes om naar het formaat dat de API verwacht."""
    cleaned = [str(i).strip() for i in (items or []) if str(i).strip()]
    return _ITEM_JOIN_SEP.join(cleaned)


# Scheidingstekens die bij het plakken/normaliseren van een lijst
# artikelnummers als "iets anders dan komma" herkend worden: komma,
# puntkomma, tab, regeleinde, of willekeurige witruimte (spaties). Punten
# binnen artikelcodes zelf (bv. "40.2.1.1") worden bewust NIET als
# scheidingsteken behandeld.
_PASTE_DELIM_RE = re.compile(r'[,;\t\r\n]+|\s+')


def normalize_pasted_items(text: str) -> str:
    """
    Normaliseert een geplakte of getypte lijst artikelnummers naar één
    lange, komma-gescheiden string zonder witruimte/enters — ongeacht welk
    scheidingsteken origineel gebruikt werd (spatie, tab, puntkomma,
    regeleinde, of een mix hiervan).

    Voorbeeld:
        "40.2.1.1; 40.2.1.50\\n40.2.1.2   40.2.1.3"
        -> "40.2.1.1,40.2.1.50,40.2.1.2,40.2.1.3"
    """
    if not text:
        return ""
    parts = _PASTE_DELIM_RE.split(text)
    items = [p.strip() for p in parts if p and p.strip()]
    return ",".join(items)


# ----------------------------------------------------------------------
# Datasets opvragen (client "ProdDataset", ConfigurationID "prod_dataset_configP_id")
# ----------------------------------------------------------------------
def list_datasets(name: str = "", owner: str = "") -> list:
    """
    Datasets opvragen, optioneel gefilterd op naam en/of eigenaar
    (@name/@owner — beide optioneel, lege string = geen filter).
    Retourneert een lijst van dicts: DS_Code, DS_Name, DS_ArtNbr,
    DS_ChangeBy, DS_ChangeDate, DS_Lock, DS_Owner.
    """
    url = f"{_base_url()}/api/datarequest"
    payload = {
        "ConfigurationID": _dataset_config_id(),
        "MultiKey": {
            "@name": name or "",
            "@owner": owner or "",
        },
    }
    headers = get_auth_header_dataset()
    logger.info(f"Datasets opvragen | name='{name}' owner='{owner}'")

    resp = requests.post(url, headers=headers, data=json.dumps(payload, ensure_ascii=False), verify=False, timeout=30)
    logger.info(f"HTTP {resp.status_code}")
    resp.raise_for_status()
    result = resp.json()

    if result.get("IsError"):
        raise RuntimeError(f"API Error {result.get('ErrorCode')}: {result.get('ErrorMessage')}")

    return result.get("Data") or []


def next_dataset_code(existing_datasets: list = None) -> int:
    """
    Bepaalt de eerstvolgende vrije DS_Code (max(bestaande) + 1).
    ⚠️ Aanname (nog te bevestigen): er is geen aparte "nieuwe code"-endpoint
    beschikbaar — dit is een client-side berekening op basis van de laatst
    opgehaalde lijst. Bij gelijktijdig aanmaken door twee gebruikers is een
    codebotsing theoretisch mogelijk (niet opgevangen).
    """
    if existing_datasets is None:
        existing_datasets = list_datasets()
    max_code = 0
    for ds in existing_datasets:
        try:
            c = int(ds.get("DS_Code") or 0)
            if c > max_code:
                max_code = c
        except (TypeError, ValueError):
            continue
    return max_code + 1


# ----------------------------------------------------------------------
# Dataset aanmaken/bijwerken (client "ProdDataset", apart import-endpoint)
# ----------------------------------------------------------------------
def save_dataset(code, name: str, artnbr_list: list, changeby: str, owner: str, lock: str = "0") -> dict:
    """
    Dataset aanmaken of bijwerken (upsert via CODE) — LET OP: dit gebruikt
    NIET het generieke /api/datarequest-endpoint, maar het aparte
    import-endpoint (zie config.py: 'prod_dataset_import_path').

    DS_ChangeDate wordt bij elke save automatisch bijgewerkt met het
    huidige tijdstip (server/klok van de machine die opslaat).
    ⚠️ Aanname, nog te bevestigen: het importveld heet "CHANGEDATE"
    (naar analogie met CHANGEBY -> DS_ChangeBy, LOCK -> DS_Lock, ...) en
    verwacht "YYYY-MM-DD HH:MM:SS". Dit is niet bevestigd via een
    aangeleverd voorbeeld (dbsetCreateUpdate.txt bevatte dit veld niet) —
    pas aan indien de API een andere veldnaam/formaat verwacht.
    """
    url = f"{_base_url()}{_import_path()}"
    payload = {
        "CODE": str(code),
        "NAME": name,
        "ARTNBR": build_items_string(artnbr_list),
        "CHANGEBY": changeby,
        "CHANGEDATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "LOCK": str(lock),
        "OWNER": owner or "",
    }
    headers = get_auth_header_dataset()
    logger.info(f"Dataset opslaan | CODE={code} NAME='{name}' OWNER='{owner}' #items={len(artnbr_list or [])}")

    resp = requests.post(url, headers=headers, data=json.dumps(payload, ensure_ascii=False), verify=False, timeout=30)
    logger.info(f"HTTP {resp.status_code}")
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        try:
            logger.error(f"Response body (preview): {resp.text}")
        except Exception:
            pass
        raise RuntimeError(f"Netwerkfout bij opslaan dataset: {e}")

    result = resp.json()
    if result.get("IsError"):
        raise RuntimeError(f"API Error {result.get('ErrorCode')}: {result.get('ErrorMessage')}")

    return result


# ----------------------------------------------------------------------
# Stock-overzicht (client "ProdStock", ConfigurationID "prod_stock_configP_id")
# ----------------------------------------------------------------------
def get_prod_stock_overview(items: list) -> list:
    """
    Stock-overzicht opvragen voor een lijst artikelcodes (typisch de
    artikelen van één dataset, via parse_artnbr(dataset['DS_ArtNbr'])).
    Retourneert een platte lijst van dicts (geen 'item'-wrapper, bevestigd
    via search_prodArt.txt): ArtCode, Omschrijving, StockHeden, MinSAP,
    MaxSAP, MaxRek, TotaalStock, Gereserveerd, InBestelling, Beschikbaar,
    KGOpVoorraad, BENPlatenPerPallet, NietCgk, Stock_Algemeen,
    Stock_Antwerpen, Stock_Miami, LISA_Qty.

    ⚠️ Nog niet getest met zeer grote datasets (honderden/duizenden
    artikelen) — geen chunking/batching geïmplementeerd; indien dit later
    een probleem blijkt (payload/timeout), moet dit alsnog toegevoegd worden.
    """
    if not items:
        return []

    url = f"{_base_url()}/api/datarequest"
    payload = {
        "ConfigurationID": _stock_config_id(),
        "MultiKey": {
            "@items": build_items_string(items),
            "@del": ",",
        },
    }
    headers = get_auth_header_stock()
    logger.info(f"Stock-overzicht opvragen | #items={len(items)}")

    resp = requests.post(url, headers=headers, data=json.dumps(payload, ensure_ascii=False), verify=False, timeout=60)
    logger.info(f"HTTP {resp.status_code}")
    resp.raise_for_status()
    result = resp.json()

    if result.get("IsError"):
        raise RuntimeError(f"API Error {result.get('ErrorCode')}: {result.get('ErrorMessage')}")

    return result.get("Data") or []