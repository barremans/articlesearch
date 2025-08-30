# cc_service.py
"""
Dunne service-laag voor CreditControl-API.
Vraagt data op met ConfigurationID = so_configP_Cc en MultiKey { "@key": <CardCode> }.
Geeft None terug bij fout; UI kan dan fallbacken op BP-financials.
"""

from __future__ import annotations
import requests
from typing import Optional, Dict, Any

from config import API_ENVIRONMENTS, ENVIRONMENT
from cc_token import get_cc_auth_header

# (optioneel) SSL warnings weg zoals elders
requests.packages.urllib3.disable_warnings()  # type: ignore


def _extract_cc_bp(payload: Any) -> Optional[Dict[str, Any]]:
    """
    Ondersteunt meerdere servervarianten:
      - {"Data": {"BP": {...}}}
      - {"BP": {...}}
    Retourneert de dict met CC BP-velden of None.
    """
    if not isinstance(payload, dict):
        return None

    # 1) Klassiek: Data → BP
    data_node = payload.get("Data")
    if isinstance(data_node, dict):
        bp_node = data_node.get("BP")
        if isinstance(bp_node, dict):
            return bp_node

    # 2) Rechtstreeks: BP op root
    bp_root = payload.get("BP")
    if isinstance(bp_root, dict):
        return bp_root

    return None


def fetch_cc_data(card_code: str) -> Optional[Dict[str, Any]]:
    """
    Roept CreditControl endpoint aan met @key = CardCode.
    Retourneert dict met de CC 'BP'-node, of None bij fout.
    """
    if not card_code:
        return None

    try:
        env_cfg = API_ENVIRONMENTS.get(ENVIRONMENT, {})
        config_id = env_cfg.get("so_configP_Cc")
        if not config_id:
            return None

        url = env_cfg["base_url"].rstrip("/") + "/api/datarequest"
        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {"@key": card_code},  # << BELANGRIJK: @key = CardCode
        }
        headers = get_cc_auth_header()

        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # API-fout?
        if isinstance(data, dict) and data.get("IsError"):
            return None

        # CC 'BP' eruit halen (Data->BP of root->BP)
        cc_bp = _extract_cc_bp(data)
        return cc_bp

    except Exception:
        # Geen pop-up hier; UI valt stilletjes terug op BP-waarden.
        return None
