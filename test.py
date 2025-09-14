# test_api.py
# Run dit script in VS Code (Play-knop) om een JSON payload te posten naar de API

import json
import requests
import urllib3

from auth import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    env = API_ENVIRONMENTS[ENVIRONMENT]
    base = env["base_url"]
    url = f"{base}/api/datarequest"

    # >>>>>>>>>>>> PLAK HIER JE JSON PAYLOAD <<<<<<<<<<<<<<
    payload = {
            "ConfigurationID": "4AA8DF",
            "Key":"6"
    #"ConfigurationID": "OLH3RP",
    #"MultiKey":{
    #"@key": "K05036"
   # }
}
    
    
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    headers = get_auth_header()
    headers.setdefault("Content-Type", "application/json")

    print(f"[INFO] ENV={ENVIRONMENT}")
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

        print("---------- RESPONSE ----------")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        if data.get("IsError"):
            print(f"[WARN] API Error {data.get('ErrorCode')}: {data.get('ErrorMessage')}")

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Netwerkfout: {e}")


if __name__ == "__main__":
    main()
