# oitmi_api.py
import requests
from oitmi_token import get_auth_header


def fetch_detail_data(item_code: str) -> dict:
    url = f"https://api.cgk-group.com/api/detail/OITMI/{item_code}/dbname/SBOCGKLIVE"
    headers = get_auth_header()
    response = requests.get(url, headers=headers, timeout=20, verify=False)
    response.raise_for_status()
    return response.json()
