import requests
from cc_token import get_cc_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT

env_cfg = API_ENVIRONMENTS.get(ENVIRONMENT, {})
url = env_cfg["base_url"].rstrip("/") + "/api/datarequest"

payload = {
    "ConfigurationID": "0B7JWA",  # jouw V2-config
    "MultiKey": {
        "@CardCode": "K06714",
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
}

print("URL:", url)
print("Payload:", payload)

resp = requests.post(url, headers=get_cc_auth_header(), json=payload, verify=False, timeout=30)
print("HTTP status:", resp.status_code)
print("Response text (eerste 1000 chars):")
print(resp.text[:1000])
