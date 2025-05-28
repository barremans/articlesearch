# data_request.py
import json
import requests
import urllib3
from auth import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT
from settings import load_show_stock

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def send_data_request(zoekterm: str, mode: str) -> list:
    env_config = API_ENVIRONMENTS[ENVIRONMENT]
    url = f"{env_config['base_url']}/api/datarequest"
    config_id = env_config["data_config_id"]

    show_stock = load_show_stock()  # "R", "S", "B"

    payload = json.dumps({
        "ConfigurationID": config_id,
        "DatabaseName": "SBOCGKLIVE",  # eventueel instelbaar via config.py in de toekomst
        "DatabaseAlias": "",
        "MultiKey": {
            "@zoekterm": zoekterm,
            "@mode": mode,
            "@show_stock": show_stock
        }
    })

    headers = get_auth_header()

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Netwerkfout bij datarequest: {e}")

    if data.get("IsError"):
        raise Exception(f"API Error {data.get('ErrorCode')}: {data.get('ErrorMessage')}")

    return [item.get("item", {}) for item in data.get("Data", [])]
