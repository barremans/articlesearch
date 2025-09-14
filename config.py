# config.py
from settings import load_environment
import os  # <<< toegevoegd voor env vars

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
        "so_configP_id": "C80TSJ",  #Sales order data
        "bp_configP_Bp": "U63P1T",  #Bussiness partner min search data
        "so_configP_Bp": "OMW5IN",  #Bussiness partner  data
        "so_configP_Cc": "OLH3RP",  #CreditControl data
        "so_configP_OE": "4AA8DF",  #Open Elements data       
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
    },
    "Bp": {
        "live": {
            "client_id": "businesspartneru",
            "client_secret": "M2E2YzEyOGYtMjAyOS00YWU3LWFiZjMtMjg2MGE5MDBmZTQ1"
        }
    },
    "Cc": {
        "live": {
            "client_id": "CreditControl",
            "client_secret": "ODkyMjg1NmUtMTgxNy00MTdkLTgyNWMtZDZkMTIzYjgxOTU4"
        }
    },
    "BpS": {
        "live": {
            "client_id": "BpSearchMin",
            "client_secret": "NDQ4MDk0NTUtNzY4OC00ODEyLWE2ZWMtYTdiOTFhMjA1Yzc3"
        }
    }  ,
    "OE": {
        "live": {
            "client_id": "OpenElements",
            "client_secret": "YzRiOTZkNzQtNmZhMi00NjkzLWFhNzQtNGFiMTAwYzE1OTI1"
        }
    }                           
#end
}

# -----------------------------
# Credit Control tab settings
# -----------------------------
# Productiewachtwoord: kan je ook via env var CC_TAB_PASSWORD zetten op het systeem.
# (security_cc.password() leest eerst deze variabele en valt dan terug op de env var.)
CC_TAB_PASSWORD = os.getenv("CC_TAB_PASSWORD", "DcbBB12@@@@")

# Dev-bypass: zet TRUE via config of via env var CC_LOCK_DISABLED in {1,true,yes,y}
_env = os.getenv("CC_LOCK_DISABLED", "").strip().lower()
CC_LOCK_DISABLED = _env in ("1", "true", "yes", "y")
