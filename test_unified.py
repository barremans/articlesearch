# test_unified.py
# Test in VS Code met één Play-knop:
#  1) MODE = "kind"  -> gebruikt data_request.send_data_request(kind=...)
#  2) MODE = "raw"   -> post exact de JSON payload die je hieronder plakt

import json
import requests
import urllib3

# project imports
from config import API_ENVIRONMENTS, ENVIRONMENT
from auth import get_auth_header
from data_request import send_data_request  # geen aanpassingen nodig

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =======================
# CONFIG – PAS HIER AAN
# =======================
MODE = "raw"            # kies: "kind" of "raw"
TEST = "cc"              # bij MODE="kind": kies uit "cc" | "bp" | "data" | "project"

# Opties voor kind-mode (zonder 'debug')
KIND_OPTIONS = {
    "cc": {
        "zoekterm": "K07058",
        "mode": "",
        "is_closed": "",
    },
    "bp": {
        "zoekterm": "250201242",
        "mode": "",
        "is_closed": "",
    },
    "data": {
        "zoekterm": "BE43977",
        "mode": "c",
        "is_closed": "",
    },
    "project": {
        "zoekterm": "PRJ123",  # jouw project-ID
        "mode": "",
        "is_closed": "",       # "", "Y", "N"
    },
        "bps": {
        "zoekterm": "bekaert",
        "mode": "",
        "card_type": "",
    },
}

# Endpoint voor RAW-mode
RAW_ENDPOINT = "datarequest"   # bv. "datarequest", "stockinfo", ...

# Kies of je een custom payload wil plakken
USE_CUSTOM_RAW = True

# 1) Zet USE_CUSTOM_RAW=True en plak hier je payload (exact wat je wil posten)
CUSTOM_RAW_PAYLOAD = {
    "ConfigurationID": "U63P1T",
    "MultiKey":{
        "@zoekterm": "bekaert",
        "@mode": "",
        "@card_type": ""
    }
}

# 2) Of zet USE_CUSTOM_RAW=False en kies een template hieronder via TEST
RAW_PAYLOAD_TEMPLATES = {
    "cc": {
        "ConfigurationID": "OLH3RP",     # vervang indien nodig
        "MultiKey": {"@key": "K07058"}
    },
    "bp": {
        "ConfigurationID": API_ENVIRONMENTS[ENVIRONMENT].get("so_configP_Bp", "C80TSJ"),
        "MultiKey": {"@zoekterm": "250201242", "@mode": "", "@type": ""}
    },
    "data": {
        "ConfigurationID": API_ENVIRONMENTS[ENVIRONMENT]["data_config_id"],
        "DatabaseName": "SBOCGKLIVE",
        "DatabaseAlias": "",
        "MultiKey": {"@zoekterm": "BE43977", "@mode": "c", "@show_stock": "Y"}
    },
    "project": {
        "ConfigurationID": API_ENVIRONMENTS[ENVIRONMENT]["project_configP_id"],
        "MultiKey": {"@prjID": "PRJ123", "@is_closed": ""}
    },
    "so": {
        "ConfigurationID": API_ENVIRONMENTS[ENVIRONMENT]["so_configP_id"],
        "MultiKey": {"@so": "250201242", "@status": "c"}
    }
}
# =======================


def print_result(data):
    """Netjes afdrukken: toon Data als aanwezig, anders alles."""
    print("---------- RESPONSE ----------")
    if isinstance(data, dict) and "Data" in data:
        print(json.dumps(data["Data"], indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

    if isinstance(data, dict) and data.get("IsError"):
        print(f"[WARN] API Error {data.get('ErrorCode')}: {data.get('ErrorMessage')}")


def run_kind():
    cfg = KIND_OPTIONS.get(TEST)
    if not cfg:
        raise SystemExit(f"[ERROR] Onbekende TEST voor kind-mode: {TEST}")

    print(f"[INFO] MODE=kind | kind={TEST} | ENV={ENVIRONMENT}")

    result = send_data_request(
        zoekterm=cfg["zoekterm"],
        mode=cfg["mode"],
        project_search=(TEST == "project"),
        is_closed=cfg["is_closed"],
        kind=TEST,
    )
    # send_data_request retourneert al gemapte data (lijst of dict)
    wrapped = {"Data": result}
    print_result(wrapped)


def run_raw():
    env = API_ENVIRONMENTS[ENVIRONMENT]
    base = env["base_url"]
    url = f"{base}/api/{RAW_ENDPOINT}"

    payload = CUSTOM_RAW_PAYLOAD if USE_CUSTOM_RAW else RAW_PAYLOAD_TEMPLATES.get(TEST)
    if not payload:
        raise SystemExit(f"[ERROR] Geen RAW payload voor TEST={TEST}. Pas CUSTOM_RAW_PAYLOAD of RAW_PAYLOAD_TEMPLATES aan.")

    headers = get_auth_header()
    headers.setdefault("Content-Type", "application/json")

    print(f"[INFO] MODE=raw | endpoint={RAW_ENDPOINT} | ENV={ENVIRONMENT}")
    print(f"[INFO] URL={url}")
    print(f"[INFO] Payload:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
        print(f"[INFO] HTTP {resp.status_code}")
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:
            print(resp.text)
            return
        print_result(data)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Netwerkfout: {e}")


def main():
    if MODE == "kind":
        run_kind()
    elif MODE == "raw":
        run_raw()
    else:
        raise SystemExit(f"[ERROR] MODE moet 'kind' of 'raw' zijn (nu: {MODE!r}).")


if __name__ == "__main__":
    main()
