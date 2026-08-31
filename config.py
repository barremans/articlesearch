# =============================================================================
# ArticleSearch
# File:    config.py
# Role:    Centrale configuratie — omgevingen (test/live), ConfigurationID's
#          per databron (API_ENVIRONMENTS) en OAuth-achtige clients per
#          databron (API_CLIENTS). ⚠️ Bevat base64-encoded client secrets —
#          zie §7 (Beveiliging) in het context-bestand.
# Version: 1.3.0
# Author:  Bart Bossuyt
# Changes: 1.3.0 — Prod Stock Overview (nieuwe search-type "Prod"): 2 nieuwe
#                   config-keys in API_ENVIRONMENTS["live"]:
#                   `prod_dataset_configP_id` ("BAEIG0", dataset opvragen/
#                   aanmaken/bijwerken) en `prod_stock_configP_id`
#                   ("VX3PMC", artikel-stock-overzicht per dataset). Nieuwe
#                   key `prod_dataset_import_path` (vast pad voor de
#                   create/update-call, buiten het generieke
#                   /api/datarequest-endpoint om — zie prod_info.py). 2
#                   nieuwe clients in API_CLIENTS: "ProdDataset" (client_id
#                   "Datasetprod") en "ProdStock" (client_id
#                   "ProdStockOverview"). Bevestigd door gebruiker:
#                   verwijderen van een dataset is niet mogelijk — enkel
#                   LOCK=1 zetten wanneer een dataset niet meer gebruikt
#                   wordt (geen aparte delete-config/endpoint nodig).
# Changes: 1.2.0 — PaymentsDue: nieuwe databron "Betalingsgedrag & Open-
#                   staande Posten" toegevoegd (Export-menu). 2 nieuwe
#                   config-keys in API_ENVIRONMENTS["live"]:
#                   `duepayment_detail_configP_id` ("UIY02H", 1 rij per
#                   klant/gemiddelden) en `duepayment_overview_configP_id`
#                   ("YCT5LR", 1 rij per document). 2 nieuwe clients in
#                   API_CLIENTS: "DuePaymentDetail" en "DuePaymentOverview"
#                   — elk hun eigen OAuth-client, enkel "live" (consistent
#                   met de overige niet-basis databronnen).
# Changes: 1.1.0 — ART-BP-1: nieuwe databron "ArtBpSearch" toegevoegd —
#                   artikels gekoppeld aan een leverancier (BP), opgevraagd
#                   via CardCode. Nieuwe config-key `artbp_configP_id`
#                   ("KX9RLR") in API_ENVIRONMENTS["live"], nieuwe client
#                   `API_CLIENTS["ArtBpSearch"]["live"]`. Enkel "live"
#                   voorzien (consistent met overige niet-basis databronnen
#                   zoals Project/Atp/Po/So/Bp/Cc/BpS/OE/VTA/PEP — geen
#                   test-config gekend/aangeleverd).
# Changes: 1.0.0 — Baseline: bestaande functionaliteit vóór introductie van
#                   versiebeheer in commentaar.
# =============================================================================
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
        "so_configP_CcV2": "0B7JWA",  #CreditControl data V2
        "so_configP_CcBpV2": "HG443N",  #CreditControl data V2
        "so_configP_OE": "4AA8DF",  #Open Elements data   
        "vta_config_id": "G6HH9T", #VTA Info    
        "pep_config_id": "FSOLI1", #Peppol fault info  
        "artbp_configP_id": "KX9RLR", #Artikels gekoppeld aan leverancier (ArtBpSearch)
        "duepayment_detail_configP_id": "UIY02H", #PaymentsDue - per klant/gemiddelden (Detail)
        "duepayment_overview_configP_id": "YCT5LR", #PaymentsDue - per document (Overview)
        "prod_dataset_configP_id": "BAEIG0",  #Prod Stock Overview - dataset opvragen/aanmaken/bijwerken
        "prod_stock_configP_id": "VX3PMC",    #Prod Stock Overview - artikel-stock-overzicht
        "prod_dataset_import_path": "/api/import/DATAPROD/U/dbname/SBOCGKLIVE",  #vast pad, geen /api/datarequest
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
    "CcV2": {
    "live": {
        "client_id": "CreditControl",
        "client_secret": "ODkyMjg1NmUtMTgxNy00MTdkLTgyNWMtZDZkMTIzYjgxOTU4"
    }
    },
        "CcBpV2": {
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
    }   ,
        "VTA": {
        "live": {
            "client_id": "VTA",
            "client_secret": "NjVhODc4NmYtZGQ5NC00MGRiLTk5OTItMGM1NWNkMDE3Yzg4"
        }
    } ,     
        "PEP": {
        "live": {
            "client_id": "SmartlynxStatusInv",
            "client_secret": "YTliODc0MDEtZjg5ZC00MDhiLTg3ZTUtN2U0M2Q0YjM1NzRk"
        }
    }                   ,
        "ArtBpSearch": {
        "live": {
            "client_id": "ArtBpSearch",
            "client_secret": "NjI2NmZhY2MtNGY0MC00YTViLTlkODUtYTRlMThiZGIxYjcx"
        }
    }                   ,
        "DuePaymentDetail": {
        "live": {
            "client_id": "DuePaymentDetail",
            "client_secret": "N2I3MDNjZjgtOTRmMy00NzY0LTk4MTYtYTY2N2IwMWQwZGZi"
        }
    }                   ,
        "DuePaymentOverview": {
        "live": {
            "client_id": "DuePaymentOverview",
            "client_secret": "ZTM3OTAwNDktMzg3Mi00MTQwLTkxMTMtZDljMDMyOTcwY2Qx"
        }
    }                   ,
        "ProdDataset": {
        "live": {
            "client_id": "Datasetprod",
            "client_secret": "Yzk0YjUwNzEtMzRkZC00Y2VhLTgwMzYtOWU4YjM1OTRkOWQ2"
        }
    }                   ,
        "ProdStock": {
        "live": {
            "client_id": "ProdStockOverview",
            "client_secret": "NmVlYWRlMjMtODk3ZC00MWM0LWE1ODktMjM0ZjBmMzdhYTkz"
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

# -----------------------------
# Netwerk / AD-status
# -----------------------------
OFFLINE_MODE = False