# cc_service.py 031220251328
"""
Service-laag voor CreditControl-API (V1 + V2-ondersteuning).
- Probeert eerst V2 (ConfigurationID = so_configP_CcV2, met @CardCode)
- Valt terug op V1 (ConfigurationID = so_configP_Cc, met @key)
- Normaliseert veldnamen zodat de UI geen aanpassing nodig heeft.
- Retourneert steeds een dict met de CC 'BP'-node, of None bij fout.
"""

from __future__ import annotations
import requests
from typing import Optional, Dict, Any

from config import API_ENVIRONMENTS, ENVIRONMENT
from cc_token import get_cc_auth_header

requests.packages.urllib3.disable_warnings()  # type: ignore


# ----------------------------- Helpers -----------------------------
def _extract_cc_bp(payload: Any) -> Optional[Dict[str, Any]]:
    """
    Ondersteunt meerdere servervarianten:
      - {"Data": {"BP": {...}}}
      - {"Data": {"BP": [ {...} ]}}
      - {"Data": [ {"BP": [ {...} ]} ]}
      - {"BP": {...}}
      - {"BP": [ {...} ]}
    Normaliseert veldnamen tussen CC V1 en V2.
    """
    if not isinstance(payload, dict):
        return None

    # --- BP-node vinden ---
    data_node = payload.get("Data")

    # Als Data een lijst is → eerste element
    if isinstance(data_node, list) and data_node:
        data_node = data_node[0]

    bp_node = None
    if isinstance(data_node, dict):
        bp_node = data_node.get("BP")

    # BP zelf kan ook een lijst zijn
    if isinstance(bp_node, list) and bp_node:
        bp_node = bp_node[0]

    # Fallback: BP op rootniveau
    if bp_node is None:
        bp_node = payload.get("BP")
        if isinstance(bp_node, list) and bp_node:
            bp_node = bp_node[0]

    if not isinstance(bp_node, dict):
        return None

    # --- V2 → V1 veldmapping + extra info ---
    mappings = {
        "CreditLimit": "CreditLine",
        "CurrentBalance": "Balance",
        "TotalOpenOrders": "OpenOrders",
        "TotalOpenDeliveries": "OpenDeliveries",
        "TotalOpenInvoices": "OpenInvoices",
        "TotalOpenDownPayments": "DownPayments",
        "OpenCredit": "CreditExposure",

        "CreditStatus": "CreditLimitStatusText",
        "CreditLimitStatusText": "CreditLimitStatusText",
        "CreditUsagePercent": "PercentageUsedCredit",
        "AvailableCredit": "AvailableCredit",
        "CreditOverLimit": "CreditOverLimit",
        "RiskColorType": "RiskColorType",
        "IsCreditLimitExceeded": "IsCreditLimitExceeded",

        "PaymentGroup": "PymntGroup",
        "LastUpdate": "U_UpdateDate",
        "LastInvoiceDate": "LastInvoiceDate",

        "RiskCategory": "RiskCategory",
        "SuggestedAction": "SuggestedAction",
        "ProposedCreditLine": "ProposedCreditLine",
        "MoetAangepastWorden": "MoetAangepastWorden",
        "SafetyBufferPercent": "SafetyBufferPercent",
        "AtradiusCoveragePercent": "AtradiusCoveragePercent",
        "AtradiusLandGroup": "AtradiusLandGroup",
        "MaxSelfAssessmentLimit": "MaxSelfAssessmentLimit",
        "MaxAtradiusCoverageAmount": "MaxAtradiusCoverageAmount",
        "Exposure_vs_Atradius_Coverage": "Exposure_vs_Atradius_Coverage",
        "IsUnratedDebtor": "IsUnratedDebtor",
        "Risk_For_CGK": "Risk_For_CGK",
    }

    normalized = bp_node.copy()
    for old_key, new_key in mappings.items():
        if new_key in bp_node:
            normalized[old_key] = bp_node[new_key]

    return normalized




# ----------------------------- Core API-calls -----------------------------
def _call_cc_api(config_id: str, multikey: dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generieke helper om een CreditControl API-call uit te voeren.
    """
    if not config_id:
        return None

    env_cfg = API_ENVIRONMENTS.get(ENVIRONMENT, {})
    url = env_cfg.get("base_url", "").rstrip("/") + "/api/datarequest"
    headers = get_cc_auth_header()

    try:
        resp = requests.post(url, headers=headers, json={
            "ConfigurationID": config_id,
            "MultiKey": multikey
        }, verify=False, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict) and data.get("IsError"):
            return None

        return _extract_cc_bp(data)

    except Exception as e:
        print(f"[CC_API] Error fetching CreditControl data: {e}")
        return None



# ----------------------------- Public functie -----------------------------
def fetch_cc_data(card_code: str) -> Optional[Dict[str, Any]]:
    if not card_code:
        return None

    print(f"[CC] ENVIRONMENT = {ENVIRONMENT}")  # 👈 zie welke omgeving actief is
    env_cfg = API_ENVIRONMENTS.get(ENVIRONMENT, {})

    # ---- 1️⃣ Nieuwe V2 ----
    config_v2 = env_cfg.get("so_configP_CcV2")
    print(f"[CC] config_v2 = {config_v2}")  # 👈 check of gevonden wordt
    if config_v2:
        print(f"[CC] Probeert V2-call voor {card_code} ...")
        multikey_v2 = {
            "@CardCode": card_code,
            "@Sales": "",
            "@Docowner": "",
            "@RiskCat": "",
            "@MinPrUsed": "",
            "@MaxPrUsed": "",
            "@OrderB": "",
            "@Action": "",
            "@5000Mismatch": "",
            "@mismatch": "",
            "@5000Increase": ""
        }
        cc_data = _call_cc_api(config_v2, multikey_v2)
        if cc_data:
            print(f"[CC] ✅ V2 gelukt, data ontvangen voor {card_code}")
            return cc_data
        else:
            print(f"[CC] ⚠️ V2 mislukt of leeg, probeer fallback...")

    # ---- 2️⃣ Fallback naar oude versie ----
    config_v1 = env_cfg.get("so_configP_Cc")
    print(f"[CC] config_v1 = {config_v1}")  # 👈 altijd tonen
    if config_v1:
        cc_data = _call_cc_api(config_v1, {"@key": card_code})
        if cc_data:
            print(f"[CC] ✅ Fallback naar V1 gelukt voor {card_code}")
            return cc_data

    print(f"[CC] ❌ Geen CC-data voor {card_code}")
    return None
