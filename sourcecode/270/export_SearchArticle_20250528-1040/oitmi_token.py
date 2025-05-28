# oitmi_token.py
from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager

client_config = API_CLIENTS["OITMI"][ENVIRONMENT]
base_url = API_ENVIRONMENTS[ENVIRONMENT]["base_url"]

oitmi_token = TokenManager(
    client_id=client_config["client_id"],
    client_secret=client_config["client_secret"],
    base_url=base_url
)

def get_auth_header():
    return oitmi_token.get_auth_header()
