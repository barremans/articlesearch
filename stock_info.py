# stock_info.py
import json
import logging
import requests
import urllib3
from stock_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("ArticleSearch.StockInfo")


def _normalize_detail_payload(payload):
    """
    Converteer de payload naar een dictionary.
    - dict -> dict
    - list -> eerste dict-element of {'RAW': payload}
    - bytes/bytearray -> JSON parse, anders {'RAW_TEXT': ...}
    - str -> JSON parse, anders {'RAW_TEXT': ...}
    - None/anders -> {}
    """
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        if payload and isinstance(payload[0], dict):
            return payload[0]
        return {"RAW": payload}
    if isinstance(payload, (bytes, bytearray)):
        try:
            return json.loads(payload.decode("utf-8", errors="ignore"))
        except Exception:
            try:
                txt = payload[:2000].decode("utf-8", errors="ignore")
            except Exception:
                txt = ""
            return {"RAW_TEXT": txt}
    if isinstance(payload, str):
        s = payload.strip()
        try:
            return json.loads(s)
        except Exception:
            return {"RAW_TEXT": s[:2000]}
    return {"RAW": payload}


def get_item_detail_stockinfo(item_code: str) -> dict:
    env_config = API_ENVIRONMENTS[ENVIRONMENT]
    url = f"{env_config['base_url']}/api/datarequest"
    # config_id = env_config["stock_config_id"]
    config_id = env_config["stock_configP_id"]

    payload = json.dumps({
        "ConfigurationID": config_id,
        "MultiKey": {
            "@item": item_code,
            "@cancelled": "",
            "@validFor": "",
            "@grouplocked": "",
            "@LockedSAPWh": "",
            "@FreezedSAPWh": "",
            "@InactiveWhs": "",
            "@DropshipWhs": "",
            "@LockedWhs": "",
            "@validPartner": "",
            "@validSAP": "",
            "@Whs": "",
            "@blockloc": "",
            "@productionloc": "",
            "@activeloc": "",
            "@zone": ""
        }
    })

    headers = get_auth_header()

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Fout tijdens verzoek naar stockinfo: {e}")

    if isinstance(data, dict) and data.get("IsError"):
        # functioneel API-fout; dit mag blijven falen
        raise ValueError(f"API-fout: {data.get('ErrorMessage')}")

    # Sommige omgevingen leveren de data onder 'Data', soms direct.
    detail = data.get("Data") if isinstance(data, dict) else data

    normalized = _normalize_detail_payload(detail)
    if not isinstance(normalized, dict):
        # zou niet mogen gebeuren, maar extra safeguard
        normalized = {"RAW": normalized}

    logger.info(
        "Detail voor %s genormaliseerd: type=%s, keys=%s",
        item_code, type(normalized).__name__, list(normalized.keys())[:10]
    )
    return normalized
