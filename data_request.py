# data_request.py

import json
import logging
import requests
import urllib3
from config import API_ENVIRONMENTS, ENVIRONMENT
from settings import load_show_stock

# Auth: standaard + BpS (voor BP-zoeklijst)
from auth import get_auth_header
try:
    from auth import get_auth_header_bps
    _HAS_BPS = True
except Exception:
    get_auth_header_bps = None   # type: ignore
    _HAS_BPS = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("ArticleSearch")
if not logger.handlers:
    h = logging.StreamHandler()
    f = logging.Formatter("[%(levelname)s] %(asctime)s - [ArticleSearch] %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
logger.setLevel(logging.INFO)


def _mask(s: str, keep: int = 20) -> str:
    if not s:
        return ""
    return s[:keep] + "..." if len(s) > keep else s


def _choose_headers(kind: str) -> dict:
    """Gebruik voor BP-zoeken de BpS-client; anders de standaard client."""
    if kind == "bp" and _HAS_BPS and callable(get_auth_header_bps):  # type: ignore
        hdrs = get_auth_header_bps()  # type: ignore
        logger.info("Auth client: BpS (BP zoeklijst)")
        return hdrs
    hdrs = get_auth_header()
    if kind == "bp":
        logger.info("Auth client: DEFAULT (fallback; get_auth_header_bps niet gevonden)")
    else:
        logger.info("Auth client: DEFAULT")
    return hdrs


def send_data_request(
    zoekterm: str,
    mode: str,
    project_search: bool = False,
    is_closed: str = "",
    kind: str = "data",   # "data" | "project" | "bp" | "cc"
    bp_type: str = "",    # enkel gebruikt wanneer kind == "bp" → "", "C", of "S"
):
    """
    Project: retourneert een dict.
    Artikels / BP / CC: retourneert een lijst van item-dicts.

    kind:
      - "data"    : artikels
      - "project" : project-search
      - "bp"      : business partner search (lijst, via BpS)
      - "cc"      : credit control lookup
    """
    env = API_ENVIRONMENTS[ENVIRONMENT]
    base = env["base_url"]
    url = f"{base}/api/datarequest"

    # Kies juiste config-ID
    if kind == "project" or project_search:
        candidate_keys = ["project_configP_id"]
    elif kind == "bp":
        # MIN search data eerst; fallbacks laten legacy werken
        candidate_keys = ["bp_configP_Bp", "bp_config_id", "so_configP_Bp"]
    elif kind == "cc":
        candidate_keys = ["so_configP_Cc", "cc_config_id"]
    else:
        candidate_keys = ["data_config_id"]

    config_key = next((k for k in candidate_keys if k in env and env[k]), None)
    if not config_key:
        available = ", ".join(sorted(env.keys()))
        raise RuntimeError(
            f"Ontbrekende config voor '{kind}': geen van {candidate_keys} gevonden in API_ENVIRONMENTS "
            f"voor omgeving '{ENVIRONMENT}'. Beschikbaar: {available}"
        )
    config_id = env[config_key]

    # Debug
    safe_env = {k: v for k, v in env.items() if "secret" not in k.lower()}
    logger.info(f"ENV={ENVIRONMENT}")
    logger.info(f"URL={url}")
    logger.info(f"Kind={kind} | project_search={project_search}")
    logger.info(f"ENV mapping: {json.dumps(safe_env, indent=2)}")
    logger.info(f"Config key gekozen: {config_key} => {config_id}")

    # Payload per soort
    if kind == "project" or project_search:
        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {"@prjID": zoekterm, "@is_closed": is_closed},
        }
    elif kind == "bp":
        # ← Exacte opbouw zoals vereist door BpS:
        # {
        #   "ConfigurationID": "U63P1T",
        #   "MultiKey": { "@zoekterm": "...", "@mode": "", "@card_type": "" }
        # }
        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {
                "@zoekterm": zoekterm,
                "@mode": (mode if mode in ("AND", "OR") else ""),  # lege string OK
                "@card_type": bp_type or ""                       # "", "C" of "S"
            },
        }
    elif kind == "cc":
        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {"@key": zoekterm},
        }
    else:
        # Artikels (standaard)
        payload = {
            "ConfigurationID": config_id,
            "DatabaseName": "SBOCGKLIVE",
            "DatabaseAlias": "",
            "MultiKey": {
                "@zoekterm": zoekterm,
                "@mode": mode,
                "@show_stock": load_show_stock(),
            },
        }

    headers = _choose_headers(kind)
    if "Authorization" in headers:
        logger.info(f"Auth={_mask(headers['Authorization'])}")
    logger.info("Payload:\n" + json.dumps(payload, indent=2, ensure_ascii=False))

    def _post_and_parse(pld: dict):
        resp = requests.post(url, headers=headers, data=json.dumps(pld, ensure_ascii=False), verify=False)
        logger.info(f"HTTP {resp.status_code}")
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                logger.error(f"Response body (preview): {resp.text}")
            except Exception:
                pass
            raise e
        return resp.json()

    try:
        result = _post_and_parse(payload)
    except requests.exceptions.HTTPError as e:
        if kind == "bp":
            # Extra hint voor verkeerde config/params
            resp = getattr(e, "response", None)
            text = ""
            try:
                text = resp.text if resp is not None else ""
            except Exception:
                pass
            raise RuntimeError(f"Netwerkfout bij bp-search: {e} | Response body: {text}")
        raise RuntimeError(f"Netwerkfout bij {kind}-search: {e}")

    if result.get("IsError"):
        code = result.get("ErrorCode")
        msg = result.get("ErrorMessage")
        raise RuntimeError(f"API Error {code}: {msg}")

    data = result.get("Data")

    # Project → dict
    if kind == "project" or project_search:
        return data or {}

    # Artikelen / BP / CC → lijst
    normalized = []
    for itm in (data or []):
        if isinstance(itm, dict):
            normalized.append(itm.get("item", itm))
        else:
            normalized.append({})
    return normalized
