# data_request.py

import json
import requests
import urllib3
from auth import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT
from settings import load_show_stock

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def send_data_request(
    zoekterm: str,
    mode: str,
    project_search: bool = False,
    is_closed: str = ""
):
    """
    Als project_search==True: return het Data-object (dict).
    Anders: return een lijst van item-dicts.
    """
    env = API_ENVIRONMENTS[ENVIRONMENT]
    base = env["base_url"]

    # Kies juiste config-ID
    config_key = "project_configP_id" if project_search else "data_config_id"
    config_id = env[config_key]

    url = f"{base}/api/datarequest"
    if project_search:
        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {
                "@prjID":    zoekterm,
                "@is_closed": is_closed
            }
        }
    else:
        payload = {
            "ConfigurationID": config_id,
            "DatabaseName":    "SBOCGKLIVE",
            "DatabaseAlias":   "",
            "MultiKey": {
                "@zoekterm":   zoekterm,
                "@mode":       mode,
                "@show_stock": load_show_stock()
            }
        }

    headers = get_auth_header()
    body = json.dumps(payload)

    try:
        resp = requests.post(url, headers=headers, data=body, verify=False)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.RequestException as e:
        typ = "project-search" if project_search else "standaard-search"
        raise RuntimeError(f"Netwerkfout bij {typ}: {e}")

    if result.get("IsError"):
        code = result.get("ErrorCode")
        msg  = result.get("ErrorMessage")
        raise RuntimeError(f"API Error {code}: {msg}")

    data = result.get("Data")

    if project_search:
        # Data is een dict met je project-info
        return data or {}
    else:
        # Data is een lijst van items
        return [itm.get("item", {}) for itm in (data or [])]
