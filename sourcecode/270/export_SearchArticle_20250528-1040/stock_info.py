# stock_info.py
import json
import requests
import urllib3
from stock_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_item_detail_stockinfo(item_code: str) -> dict:
    env_config = API_ENVIRONMENTS[ENVIRONMENT]
    url = f"{env_config['base_url']}/api/datarequest"
    config_id = env_config["stock_config_id"]

    payload = json.dumps({
        "ConfigurationID": config_id,
        "Key": item_code
    })

    headers = get_auth_header()

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Fout tijdens verzoek naar stockinfo: {e}")

    if data.get("IsError"):
        raise ValueError(f"API-fout: {data.get('ErrorMessage')}")

    detail = data.get("Data")
    if not isinstance(detail, dict):
        raise TypeError("Detailresponse is geen dictionary.")

    return detail
