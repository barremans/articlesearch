# token_manager.py
import requests
import json
import time
import urllib3
import logging
import os
from config import API_ENVIRONMENTS, API_CLIENTS, ENVIRONMENT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "app.log"), mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class TokenManager:
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.token = None
        self.token_type = None
        self.expires_in = None
        self.token_timestamp = None
        self.token_expiry_buffer = 120  # seconden

    def get_token(self):
        url = f"{self.base_url}/api/account/login"
        payload = json.dumps({
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })
        headers = {'Content-Type': 'application/json'}

        try:
            logging.info(f"[{self.client_id}] Token aanvragen bij {url}...")
            response = requests.post(url, headers=headers, data=payload, verify=False)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"[{self.client_id}] Token aanvraag mislukt: {e}")
            raise

        try:
            data = response.json()
            self.token = data.get("Token")
            self.token_type = data.get("TokenType")
            self.expires_in = int(data.get("ExpiresIn"))
            self.token_timestamp = time.time()
            logging.info(f"[{self.client_id}] Token ontvangen (vervalt in {self.expires_in}s)")
        except Exception as e:
            logging.error(f"[{self.client_id}] Ongeldige token response: {e}")
            raise

    def is_expired(self):
        if not self.token or not self.token_timestamp or not self.expires_in:
            return True
        return (time.time() - self.token_timestamp) >= (self.expires_in - self.token_expiry_buffer)

    def ensure_token(self):
        if self.is_expired():
            logging.debug(f"[{self.client_id}] Token is verlopen of afwezig. Nieuw token ophalen...")
            self.get_token()

    def get_auth_header(self):
        self.ensure_token()
        return {
            'Authorization': f'{self.token_type} {self.token}',
            'Content-Type': 'application/json'
        }
