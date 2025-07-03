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
        "stock_config_id": "7KQKVE",  #ZStockInfo
        "stock_configP_id": "YZ4KLG"  #ZStockInfoP
    },
    "live": {
        "base_url": "https://api.cgk-group.com",
        "data_config_id": "9423TC", # Article Search
        "stock_config_id": "6DIRXZ", #StockInfo
        "stock_configP_id": "WEZ7CY",  #ZStockInfoP
        "project_configP_id": "AXF4GX", #Project data
        "atp_configP_id": "1IZDVW",  #Atp data
        "po_configP_id": "3EGOKM",  #Purchase order data
        "so_configP_id": "C80TSJ"  #Sales order data
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
        "StockInfoP": {
        "test": {
            "client_id": "StockInfoP",
            "client_secret": "ZDEwNGI3Y2QtOTU0Ny00Y2NiLTgwM2YtNDEwYzAyNGU3NWI3"
        },
        "live": {
            "client_id": "StockInfoP",
            "client_secret": "ZWVkYTQwYTUtYzdlMy00Y2NlLWExM2QtZDdhNGVkYTBjMjFk"
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
    },
        "Project": {
        "live": {
            "client_id": "Project",
            "client_secret": "OTE4YmZjMjUtZjE5ZC00YzQ5LTlhN2YtNWQ2MTYwYjQ2ZGVh"
        }
    },
        "Atp": {
        "live": {
            "client_id": "AtpWhs",
            "client_secret": "YmFmYzEzYWEtNmRmNS00Nzg4LThiMGUtM2VjYjdjNmRiZDAw"
        }
    },
        "Po": {
        "live": {
            "client_id": "PurchaseOrder",
            "client_secret": "ZTViM2FiZGYtMGNmMy00ZjY1LThjYjctZWY5MmE0NjdjMzc1"
        }
    },
        "So": {
        "live": {
            "client_id": "SalesOrder",
            "client_secret": "YWRiMjcxZWMtZDhhOS00YzNjLWIwOGMtMjIzOTEwYjEwMjUx"
        }
    }                    
#end
}

