# =============================================================================
# ArticleSearch
# File:    duepayment_info.py
# Role:    Logica/data-laag voor "Betalingsgedrag & Openstaande Posten"
#          (PaymentsDue) — bouwt de MultiKey-payload en normaliseert de
#          respons voor de 2 endpoints:
#            - get_payments_due_detail()   -> AVG_DUE_PAYMENTS_DETAIL (UIY02H)
#            - get_payments_due_overview() -> PAYMENTS_DUE_OVERVIEW   (YCT5LR)
#          Response-vorm van beide endpoints: {"Data": [ {...}, ... ]} — een
#          platte lijst van dicts, GEEN "item"-wrapper (in tegenstelling tot
#          bv. artbp_info.py / data_request.py bij bp/cc).
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Eerste versie.
# =============================================================================
import json
import logging

import requests
import urllib3

from config import API_ENVIRONMENTS, ENVIRONMENT
from duepayment_token import get_auth_header_detail, get_auth_header_overview

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("ArticleSearch.DuePayment")
if not logger.handlers:
    h = logging.StreamHandler()
    f = logging.Formatter("[%(levelname)s] %(asctime)s - [DuePayment] %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
logger.setLevel(logging.INFO)


def _post(config_id: str, multikey: dict, headers: dict) -> list:
    env = API_ENVIRONMENTS[ENVIRONMENT]
    base = env["base_url"].rstrip("/")
    url = f"{base}/api/datarequest"
    payload = {"ConfigurationID": config_id, "MultiKey": multikey}

    logger.info(f"URL={url} | ConfigurationID={config_id} | MultiKey={multikey}")

    resp = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False),
        verify=False,
        timeout=30,
    )
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        try:
            logger.error(f"Response body (preview): {resp.text[:2000]}")
        except Exception:
            pass
        raise RuntimeError(f"Netwerkfout bij PaymentsDue-aanvraag: {e}")

    result = resp.json()
    if result.get("IsError"):
        raise RuntimeError(f"API Error {result.get('ErrorCode')}: {result.get('ErrorMessage')}")

    data = result.get("Data")
    return data if isinstance(data, list) else []


def get_payments_due_detail(months: str = "24", cardcode: str = "", due: str = "") -> list:
    """
    Eén rij per klant, met totalen/gemiddelden.
    (AVG_DUE_PAYMENTS_DETAIL, config `duepayment_detail_configP_id` = UIY02H)

    due:
      ""  = geen filter — alle klanten, slechtste betaler bovenaan
      "0" = enkel klanten die gemiddeld te laat betalen
      "1" = enkel klanten die gemiddeld op tijd of vroeger betalen
    """
    env = API_ENVIRONMENTS[ENVIRONMENT]
    config_id = env.get("duepayment_detail_configP_id")
    if not config_id:
        raise RuntimeError(
            "Ontbrekende config 'duepayment_detail_configP_id' in API_ENVIRONMENTS "
            f"voor omgeving '{ENVIRONMENT}'."
        )
    multikey = {
        "@months": str(months or "24"),
        "@cardcode": cardcode or "",
        "@due": due or "",
    }
    headers = get_auth_header_detail()
    return _post(config_id, multikey, headers)


def get_payments_due_overview(months: str = "24", cardcode: str = "") -> list:
    """
    Eén rij per document (factuur of voorschot).
    (PAYMENTS_DUE_OVERVIEW, config `duepayment_overview_configP_id` = YCT5LR)
    """
    env = API_ENVIRONMENTS[ENVIRONMENT]
    config_id = env.get("duepayment_overview_configP_id")
    if not config_id:
        raise RuntimeError(
            "Ontbrekende config 'duepayment_overview_configP_id' in API_ENVIRONMENTS "
            f"voor omgeving '{ENVIRONMENT}'."
        )
    multikey = {
        "@months": str(months or "24"),
        "@cardcode": cardcode or "",
    }
    headers = get_auth_header_overview()
    return _post(config_id, multikey, headers)
