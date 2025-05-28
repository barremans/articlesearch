# config.py
from settings import load_environment

# Actieve omgeving: kies 'test' of 'live'
#ENVIRONMENT = "test"
#ENVIRONMENT = "live"
ENVIRONMENT = load_environment()

# URLs en configuraties per omgeving
API_ENVIRONMENTS = {
    "test": {
        "base_url": "https://api-test.cgk-group.com",
        "data_config_id": "0TY75H", #Article Search
        "stock_config_id": "7KQKVE"  #ZStockInfo
    },
    "live": {
        "base_url": "https://api.cgk-group.com",
        "data_config_id": "9423TC", # Article Search
        "stock_config_id": "6DIRXZ" #StockInfo
    }
}

# API clients per omgeving (meerdere services)
API_CLIENTS = {
    "ArticleSearch": {
        "test": {
            "client_id": "ArticleSearch",
            "client_secret": "MTdjMDdlNjEtMTg0NC00ZGZmLTlmYzEtODVjZmIyOTgxMmJl"
        },
        "live": {
            "client_id": "ArticleSearch",
            "client_secret": "NWRjZjQzNjktYWU2NC00MDIzLWFhYWMtOGEwMWEyNWNmZGE5"
        }
    },
    "StockInfo": {
        "test": {
            "client_id": "StockInfo",
            "client_secret": "ZDk0YmI3MmQtOTY2Yi00MTFlLTlhMDEtYTZjYTEyZWM0ZmQz"
        },
        "live": {
            "client_id": "StockInfo",
            "client_secret": "YjdiNjQ5ZGItNjM0ZS00MTYyLWI1NTMtOTYyYzRiZWY5OGEy"
        }
    },
        "OITMI": {
        "test": {
            "client_id": "OITMI",
            "client_secret": "ZDM3YTgxNzgtYjEzYS00NzhkLTg3NmYtZmVlODlkYTY5Mjlj"
        },
        "live": {
            "client_id": "OITMI",
            "client_secret": "M2YzN2Y5NTEtMTFjNS00YmJhLWIwNTItYjAwNThiOTcyNzdm"
        }
    }
#end
}

