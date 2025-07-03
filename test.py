# test_po_request.py

import requests
import json
from atp_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT

def main():
    DEBUG = True

    # Haal juiste config ID op
    config_id = API_ENVIRONMENTS[ENVIRONMENT]["so_configP_id"]

    # API URL
    url = "https://api.cgk-group.com/api/datarequest"

    # Payload zoals je doorgaf
    payload = {
        "ConfigurationID": config_id,
        "MultiKey": {
            "@so": "250201242",
            "@status": "c"
        }
    }

    headers = get_auth_header()

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        data = response.json()

        if DEBUG:
            print("---------- RAW JSON DATA ----------")
            print(json.dumps(data, indent=4, ensure_ascii=False))

        if data.get("IsError"):
            print(f"API Error: {data.get('ErrorMessage')}")
        else:
            print("Data succesvol opgehaald.")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    main()
