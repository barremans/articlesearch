import requests
import json
import urllib3
import time

# Disable SSL warnings for self-signed certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global token variables
TOKEN = None
TOKEN_TYPE = None
EXPIRES_IN = None
TOKEN_TIMESTAMP = None

# Configurable expiration buffer
TOKEN_EXPIRY_BUFFER = 120  # seconds before actual expiry to refresh

def get_token():
    global TOKEN, TOKEN_TYPE, EXPIRES_IN, TOKEN_TIMESTAMP

    url = "https://api-test.cgk-group.com/api/account/login?client_id=ArticleSearch&client_secret=MTdjMDdlNjEtMTg0NC00ZGZmLTlmYzEtODVjZmIyOTgxMmJl"

    payload = json.dumps({
        "client_id": "ArticleSearch",
        "client_secret": "MTdjMDdlNjEtMTg0NC00ZGZmLTlmYzEtODVjZmIyOTgxMmJl"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload, verify=False)

    try:
        data = response.json()
        TOKEN = data.get("Token")
        TOKEN_TYPE = data.get("TokenType")
        EXPIRES_IN = data.get("ExpiresIn")
        TOKEN_TIMESTAMP = time.time()
        print("Access token retrieved.")
    except Exception as e:
        print("Failed to parse token from response:", e)
        print("Response text:", response.text)

def is_token_expired():
    if not TOKEN or not TOKEN_TIMESTAMP:
        return True
    return (time.time() - TOKEN_TIMESTAMP) >= (EXPIRES_IN - TOKEN_EXPIRY_BUFFER)

def ensure_token():
    if is_token_expired():
        print("Refreshing token...")
        get_token()

def use_token():
    ensure_token()

    if TOKEN:
        headers = {
            "Authorization": f"{TOKEN_TYPE} {TOKEN}"
        }
        url = "https://api-test.cgk-group.com/api/some/protected/endpoint"
        response = requests.get(url, headers=headers, verify=False)
        print("API Response:", response.text)
    else:
        print("Token not set.")

# Example usage
use_token()
