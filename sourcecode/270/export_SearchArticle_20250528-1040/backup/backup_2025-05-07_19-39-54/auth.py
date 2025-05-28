import requests
import json
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = None
TOKEN_TYPE = None
EXPIRES_IN = None
TOKEN_TIMESTAMP = None
TOKEN_EXPIRY_BUFFER = 120

def get_token():
    global TOKEN, TOKEN_TYPE, EXPIRES_IN, TOKEN_TIMESTAMP

    url = "https://api-test.cgk-group.com/api/account/login?client_id=ArticleSearch&client_secret=MTdjMDdlNjEtMTg0NC00ZGZmLTlmYzEtODVjZmIyOTgxMmJl"
    payload = json.dumps({
        "client_id": "ArticleSearch",
        "client_secret": "MTdjMDdlNjEtMTg0NC00ZGZmLTlmYzEtODVjZmIyOTgxMmJl"
    })
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=payload, verify=False)
    data = response.json()
    TOKEN = data.get("Token")
    TOKEN_TYPE = data.get("TokenType")
    EXPIRES_IN = data.get("ExpiresIn")
    TOKEN_TIMESTAMP = time.time()

def is_token_expired():
    if not TOKEN or not TOKEN_TIMESTAMP:
        return True
    return (time.time() - TOKEN_TIMESTAMP) >= (EXPIRES_IN - TOKEN_EXPIRY_BUFFER)

def ensure_token():
    if is_token_expired():
        get_token()

def get_auth_header():
    ensure_token()
    return {
        'Authorization': f'{TOKEN_TYPE} {TOKEN}',
        'Content-Type': 'application/json'
    }
