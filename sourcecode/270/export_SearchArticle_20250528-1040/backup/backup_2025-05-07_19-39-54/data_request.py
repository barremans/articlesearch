import json
import requests
from auth import get_auth_header

def send_data_request(zoekterm: str, mode: str) -> list:
    url = "https://api-test.cgk-group.com/api/datarequest"

    payload = json.dumps({
        "ConfigurationID": "0TY75H",
        "DatabaseName": "SBOCGKLIVE",
        "DatabaseAlias": "",
        "MultiKey": {
            "@zoekterm": zoekterm,
            "@mode": mode
        }
    })

    headers = get_auth_header()
    response = requests.post(url, headers=headers, data=payload, verify=False)
    data = response.json()

    if data.get("IsError"):
        raise Exception(f"API Error {data.get('ErrorCode')}: {data.get('ErrorMessage')}")

    return [item["item"] for item in data.get("Data", [])]
