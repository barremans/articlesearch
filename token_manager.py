# token_manager.py
import requests
import json
import time
import urllib3
import logging
import os
import base64

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
        self.base_url = base_url.rstrip("/")
        self.token = None
        self.token_type = "Bearer"
        self.expires_in = None          # seconden
        self.token_timestamp = None     # epoch seconds (wanneer ontvangen)
        self.token_exp_epoch = None     # absolute exp uit JWT (optioneel)
        self.token_expiry_buffer = 120  # seconden vervroegd vernieuwen

    # ----------------------------
    # Helpers
    # ----------------------------
    def _get_value(self, data: dict, candidates: list, aliases: dict | None = None):
        """
        Haal een waarde uit 'data' met robuuste key matching:
        1) probeer de opgegeven 'candidates' (exact),
        2) als niets, case-insensitive vergelijking op alle keys,
        3) als niets, probeer 'aliases' (bv. typefouten).
        """
        # 1) Exacte keys in volgorde
        for k in candidates:
            if k in data:
                return data.get(k)

        # 2) Case-insensitive fallback
        lower_map = {str(k).lower(): k for k in data.keys()}
        for k in candidates:
            lk = str(k).lower()
            if lk in lower_map:
                return data.get(lower_map[lk])

        # 3) Aliases (bv. typefouten of alternatieve namen)
        if aliases:
            for alias_key, real_keys in aliases.items():
                # alias exact
                if alias_key in data:
                    return data.get(alias_key)
                # alias case-insensitive
                alk = str(alias_key).lower()
                if alk in lower_map:
                    return data.get(lower_map[alk])
                # alias verwijst naar een of meerdere "echte" keys
                if isinstance(real_keys, (list, tuple)):
                    for rk in real_keys:
                        if rk in data:
                            return data.get(rk)
                        rkl = str(rk).lower()
                        if rkl in lower_map:
                            return data.get(lower_map[rkl])
                else:
                    rk = real_keys
                    if rk in data:
                        return data.get(rk)
                    rkl = str(rk).lower()
                    if rkl in lower_map:
                        return data.get(lower_map[rkl])

        return None

    def _try_parse_jwt_exp(self, token: str):
        """Probeer exp (epoch seconden) uit de JWT payload te halen en stel token_exp_epoch in."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return
            payload_b64 = parts[1]
            padding = '=' * (-len(payload_b64) % 4)  # base64url padding
            payload = base64.urlsafe_b64decode(payload_b64 + padding)
            data = json.loads(payload.decode("utf-8"))
            exp = data.get("exp")
            if isinstance(exp, (int, float)):
                self.token_exp_epoch = int(exp)
        except Exception:
            # Stil falen; we hebben elders fallbacks
            pass

    def get_token(self):
        url = f"{self.base_url}/api/account/login"
        payload = json.dumps({
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })
        headers = {'Content-Type': 'application/json'}

        try:
            logging.info(f"[{self.client_id}] Token aanvragen bij {url}...")
            response = requests.post(url, headers=headers, data=payload, verify=False, timeout=20)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"[{self.client_id}] Token aanvraag mislukt: {e}")
            raise
        except ValueError as e:
            logging.error(f"[{self.client_id}] Ongeldige JSON response: {e}")
            raise

        # ----------------------------
        # Nieuwe/oude/typfout veldnamen
        # ----------------------------
        access_token = self._get_value(
            data,
            candidates=["access_token", "AccessToken", "token", "Token"],
        )
        if not access_token:
            logging.error(f"[{self.client_id}] Ongeldige token response: geen access_token/Token veld. Response: {data}")
            raise ValueError("Ongeldige token response: 'access_token' ontbreekt")

        token_type = self._get_value(
            data,
            candidates=["token_type", "TokenType"],
            aliases={
                # ✅ Ondersteun 'Tokentype' (andere casing, typo)
                "Tokentype": ["token_type", "TokenType"]
            }
        ) or "Bearer"

        expires_in_val = self._get_value(
            data,
            candidates=["expires_in", "ExpiresIn"],
            aliases={
                # ✅ Ondersteun 'ExpresIn' (typo)
                "ExpresIn": ["expires_in", "ExpiresIn"]
            }
        )

        # ----------------------------
        # Toekennen & expiratie bepalen
        # ----------------------------
        self.token = access_token
        self.token_type = token_type
        self.token_timestamp = time.time()
        self.expires_in = None
        self.token_exp_epoch = None

        # Probeer expires_in te parsen
        if expires_in_val is not None:
            try:
                self.expires_in = int(expires_in_val)
            except Exception:
                logging.warning(f"[{self.client_id}] 'expires_in' niet naar int te casten: {expires_in_val}")

        # Als expires_in ontbreekt of faalt, gebruik JWT exp
        if self.expires_in is None:
            self._try_parse_jwt_exp(self.token)

        # Logging en laatste fallback
        if self.expires_in is not None:
            logging.info(f"[{self.client_id}] Token ontvangen (vervalt in {self.expires_in}s) | type={self.token_type}")
        elif self.token_exp_epoch is not None:
            logging.info(f"[{self.client_id}] Token ontvangen (JWT exp @ {self.token_exp_epoch}) | type={self.token_type}")
        else:
            # Veilige fallback (30 min)
            self.expires_in = 1800
            logging.warning(f"[{self.client_id}] Geen expires_in/ExpresIn of JWT exp; fallback naar {self.expires_in}s | type={self.token_type}")

    def is_expired(self):
        if not self.token:
            return True

        now = time.time()

        # Absolute exp uit JWT heeft voorrang
        if self.token_exp_epoch:
            return now >= (self.token_exp_epoch - self.token_expiry_buffer)

        # Relatieve expires_in fallback
        if not self.token_timestamp or not self.expires_in:
            return True

        return (now - self.token_timestamp) >= (self.expires_in - self.token_expiry_buffer)

    def ensure_token(self):
        if self.is_expired():
            logging.debug(f"[{self.client_id}] Token is verlopen of afwezig. Nieuw token ophalen...")
            self.get_token()

    def get_auth_header(self):
        self.ensure_token()
        return {
            'Authorization': f'{self.token_type} {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
