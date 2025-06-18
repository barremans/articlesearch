# auth.py
from config import API_CLIENTS, API_ENVIRONMENTS, ENVIRONMENT
from token_manager import TokenManager

# Eerst base_url ophalen
base_url = API_ENVIRONMENTS[ENVIRONMENT]["base_url"]
client_config = API_CLIENTS["ArticleSearch"][ENVIRONMENT]

# TokenManager instantie
article_token = TokenManager(
    client_id=client_config["client_id"],
    client_secret=client_config["client_secret"],
    base_url=base_url
)

def get_auth_header():
    return article_token.get_auth_header()

def preload_token():
    article_token.ensure_token()
