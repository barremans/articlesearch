# =============================================================================
# ArticleSearch
# File:    settings.py
# Role:    Persistente gebruikersinstellingen (settings.json) — environment,
#          show_stock, kolomheaders, taal, BP-default-type, label-
#          instellingen, default search-type, tab-volgorde, QSS-paden.
# Version: 1.1.0
# Author:  Bart Bossuyt
# Changes: 1.1.0 — BUGFIX: default_search_type gebruikte "Standaard" als
#                   geldige/standaardwaarde, terwijl de combobox in
#                   ui_main.py (self.search_type_select) als itemtekst
#                   "Artikel" gebruikt — de opgeslagen standaard-zoektype-
#                   instelling kon hierdoor nooit effectief matchen met de
#                   UI. Aangepast: DEFAULT_SETTINGS["default_search_type"],
#                   load_default_search_type() en save_default_search_type()
#                   gebruiken nu "Artikel" i.p.v. "Standaard". Bestaande
#                   settings.json met de oude waarde "Standaard" valt
#                   automatisch terug op "Artikel" via de validatie in
#                   load_default_search_type() — geen migratie nodig.
# Changes: 1.0.0 — Baseline: bestaande functionaliteit vóór introductie van
#                   versiebeheer in commentaar. Voorgeschiedenis niet
#                   gedocumenteerd per deelversie — vanaf nu wel.
# =============================================================================
import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "default_search_type": "Artikel",
    "environment": "live",
    "show_stock": "S",
    "detail_modal": False,
    "language": "NL",
    "tab_order": ["vta", "install", "vta_cert", "art"],
    "bp_default_type": "",  # <-- NIEUW: default BP-type ("", "C", "S")
    "label_settings": {
        "LABEL_WIDTH": 85.0,
        "LABEL_HEIGHT": 25.0,
        "BARCODE_TOP": 12.0,
        "BARCODE_LEFT": 25.0,
        "BARCODE_WIDTH_SCALE": 0.15,
        "BARCODE_HEIGHT_SCALE": 0.2,
        "ART_TOP": 13.0,
        "ART_LEFT": 40.0,
        "DESCRIPTION_TOP": 10.0,
        "DESCRIPTION_LEFT": 5.0,
        "DESCRIPTION_WIDTH": 60.0,
        "DATE_TOP": 3.0,
        "DATE_LEFT": 5.0,
        "INBOUND_TOP": 3.0,
        "INBOUND_LEFT": 50.0,
        "FONT_SIZE_ART": 7.0,
        "FONT_SIZE_DESCRIPTION": 9.0,
        "FONT_SIZE_SUPPLIER": 7.0,
        "FONT_SIZE_INBOUND": 7.0,
        "FONT_SIZE_DATE": 7.0
    },
    "field_labels": {
        "logistics": {
            "TrnspName": "Transportwijze",
            "LeadTime": "Levertijd (dagen)",
            "MinOrdrQty": "Minimum bestelhoeveelheid",
            "MinLevel": "Min. art.voorraad",
            "MaxLevel": "Max. art.voorraad",
            "OnHand": "Op voorraad",
            "IsCommited": "Gereserveerd",
            "OnOrder": "In bestelling",
            "DefaultWhs": "Standaard magazijn",
            "PreferredSupp": "Voorkeursleverancier",
            "CardName": "Leverancier naam",
            "SuppCatNum": "Artikelnummer leverancier",
            "Counted": "Getelde hoeveelheid"
        },
        "po_por1": {
            "LineNum": "Regel",
            "ItemCode": "Artikelcode",
            "VendorNum": "VendorNr",
            "Dscription": "Omschrijving",
            "Quantity": "Aantal",
            "Price": "Prijs",
            "WhsName": "Magazijn",
            "DocDate": "Datum",
            "ShipDate": "Verzenddatum"
        },
        "po_go": {
            "GO_DocNum": "GO Nr",
            "GO_Date": "Datum",
            "GOL_ItemCode": "Artikelcode",
            "VendorNum": "VendorNr",
            "GOL_Dscription": "Omschrijving",
            "GOL_Quantity": "Aantal",
            "GOL_OpenQty": "Open qty",
            "GOL_LineStatus": "Status"
        },
        "last_purch": {
            "DocNum": "DocNr",
            "DocDate": "Datum",
            "ItemCode": "Art.Nr.",
            "Dscription": "Omschrijving",
            "Quantity": "Aantal",
            "ShipDate": "Leverdatum",
            "VendorNum": "Vendor nr.",
            "BaseCard": "BaseCard",
            "CardName": "Leverancier",
            "WhsName": "Magazijn"
        },
        "purchase": {
            "Price": "Prijs",
            "Currency": "Munt",
            "BuyUnitMsr": "Koop eenh.",
            "NumInBuy": "Aantal/koop",
            "PurPackMsr": "Pak-eenh.",
            "PurPackUn": "Pak-un.",
            "LastPurPrc": "Laatste prijs"
        },
        "lisa": {
            "LOCNAME": "Locatie",
            "WHSNAME": "Magazijn",
            "QUANTITY": "Beschikbaar",
            "QTYRESERVED": "Gereserveerd",
            "QTYMININV": "Min.Whs",
            "QTYMAXINV": "Max.Whs"
        },
        "sap": {
            "WhsName": "Magazijn",
            "OnHand": "Beschikbaar",
            "IsCommited": "Gereserveerd",
            "OnOrder": "Besteld",
            "MinStock": "Min.Whs",
            "MaxStock": "Max.Whs",
            "VrijeStock": "Vrij"
        },
        "sales": {
            "Price": "Prijs",
            "Currency": "Munt",
            "SalUnitMsr": "Verkoop eenh.",
            "NumInSale": "Aantal/verkoop",
            "SalPackMsr": "Pak-eenh.",
            "SalPackUn": "Pak-un."
        },
        "so_rd": {
            "LineNum": "Regel",
            "ItemCode": "Artikelcode",
            "Dscription": "Omschrijving",
            "Quantity": "Aantal",
            "Price": "Prijs",
            "DiscPrcnt": "Korting (%)",
            "LineTotal": "Lijn totaal",
            "WhsName": "Magazijn",
            "ShipDate": "Verzenddatum",
            "FreeTxt": "Vrije tekst"
        },            
        "ui_texts_main": {
            "label_search_term": "Zoekterm:",
            "label_search_type": "Search-type:",
            "label_mode": "Zoekmodus:",
            "label_show_stock": "Toon voorraad:",
            "button_search": "Zoeken",
            "button_collect": "Voeg toe aan lijst",
            "button_clear": "Leeg lijst",
            "button_show_list": "Toon lijst",
            "checkbox_select_all": "Selecteer alles",
            "label_results": "Resultaten:",
            "label_result_count": "Aantal resultaten: {count}",
            "dialog_no_rows_title": "Geen data",
            "dialog_no_rows_text": "Er staan geen rijen om te verzamelen.",
            "dialog_nothing_checked": "Vink eerst één of meerdere vakjes aan om toe te voegen.",
            "dialog_list_already_empty": "De lijst is al leeg.",
            "info_list_cleared": "De verzamelde rijen zijn verwijderd en alle vakjes zijn uitgevinkt.",
            "COLUMN_HEADERS_S": {
                "ItemCode": "Art.Nr.",
                "ItemName": "Omschrijving",
                "SUPPLIERIDPRODUCT": "Vendor Nr.",
                "QUANTITY": "Qty",
                "WHSNAME": "Magazijn",
                "LOCNAME": "Loc.",
                "QTYMININV": "Min.Whs",
                "QTYMAXINV": "Max.Whs",
                "SUPPLIERNAME": "Leverancier",
                "PRICESUPPLIER": "Prijs",
                "NOTE": "Opmerking"
            },
            "COLUMN_HEADERS_DEFAULT": {
                "ItemCode": "Art.Nr.",
                "ItemName": "Omschrijving",
                "SuppCatNum": "Vendor Nr."
            }
        }
    },
    "main_qss_path": "",
    "detail_qss_path": "",
    "upload_qss_path": "",
    "project_tab_order": ["art", "install", "vta", "vta_cert"]
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = {**DEFAULT_SETTINGS, **data}

            # Deep merge voor nested dicts
            if "label_settings" in data:
                merged["label_settings"] = {
                    **DEFAULT_SETTINGS["label_settings"],
                    **data["label_settings"]
                }

            if "field_labels" in data:
                merged["field_labels"] = {
                    **DEFAULT_SETTINGS["field_labels"],
                    **data["field_labels"]
                }

            if "tab_order" not in merged:
                merged["tab_order"] = DEFAULT_SETTINGS["tab_order"]

            if "project_tab_order" not in merged:
                merged["project_tab_order"] = DEFAULT_SETTINGS["project_tab_order"]

            if "language" not in merged:
                merged["language"] = DEFAULT_SETTINGS["language"]

            if "bp_default_type" not in merged:
                merged["bp_default_type"] = DEFAULT_SETTINGS["bp_default_type"]

            # Zorg dat alle QSS paths aanwezig zijn
            for key in ("main_qss_path", "detail_qss_path", "upload_qss_path"):
                if key not in merged:
                    merged[key] = DEFAULT_SETTINGS[key]

            save_settings(merged)
            return merged
    except Exception:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        
def save_language(lang: str):
    settings = load_settings()
    settings["language"] = lang
    save_settings(settings)        
        
def load_language() -> str:
    return load_settings().get("language", DEFAULT_SETTINGS["language"])        

def load_field_labels(context: str) -> dict:
    return load_settings().get("field_labels", {}).get(context, {})

def load_environment():
    return load_settings().get("environment", DEFAULT_SETTINGS["environment"])

def save_environment(env: str):
    settings = load_settings()
    settings["environment"] = env
    save_settings(settings)

def load_show_stock():
    return load_settings().get("show_stock", DEFAULT_SETTINGS["show_stock"])

def save_show_stock(val: str):
    # Optionele guard: alleen R/S/B toelaten
    if val not in ("R", "S", "B"):
        return
    settings = load_settings()
    settings["show_stock"] = val
    save_settings(settings)

def load_detail_modal() -> bool:
    return load_settings().get("detail_modal", DEFAULT_SETTINGS["detail_modal"])

def save_detail_modal(val: bool):
    settings = load_settings()
    settings["detail_modal"] = val
    save_settings(settings)

def load_default_search_type() -> str:
    val = load_settings().get("default_search_type", DEFAULT_SETTINGS["default_search_type"])
    # alleen geldige types toelaten — moet matchen met de itemtekst in
    # ui_main.py: self.search_type_select.addItems(["Artikel", "Project", "BP", "VTA"])
    return val if val in ("Artikel", "Project", "BP", "VTA") else "Artikel"

def save_default_search_type(val: str):
    if val not in ("Artikel", "Project", "BP", "VTA"):
        val = "Artikel"
    settings = load_settings()
    settings["default_search_type"] = val
    save_settings(settings)

def load_tab_order() -> list:
    return load_settings().get("tab_order", DEFAULT_SETTINGS["tab_order"])

def save_tab_order(order: list):
    settings = load_settings()
    settings["tab_order"] = order
    save_settings(settings)

def load_label_settings() -> dict:
    return load_settings().get("label_settings", DEFAULT_SETTINGS["label_settings"])

def save_label_settings(new_settings: dict):
    settings = load_settings()
    settings["label_settings"] = {
        **DEFAULT_SETTINGS["label_settings"],
        **new_settings
    }
    save_settings(settings)

def load_main_qss_path() -> str:
    return load_settings().get("main_qss_path", DEFAULT_SETTINGS["main_qss_path"])

def save_main_qss_path(path: str):
    settings = load_settings()
    settings["main_qss_path"] = path
    save_settings(settings)

def load_detail_qss_path() -> str:
    return load_settings().get("detail_qss_path", DEFAULT_SETTINGS["detail_qss_path"])

def save_detail_qss_path(path: str):
    settings = load_settings()
    settings["detail_qss_path"] = path
    save_settings(settings)

def load_upload_qss_path() -> str:
    return load_settings().get("upload_qss_path", DEFAULT_SETTINGS["upload_qss_path"])

def save_upload_qss_path(path: str):
    settings = load_settings()
    settings["upload_qss_path"] = path
    save_settings(settings)

def load_ui_texts_main() -> dict:
    return load_settings().get("field_labels", {}).get("ui_texts_main", {})

def load_column_headers_s():
    ui_texts = load_ui_texts_main()
    return ui_texts.get("COLUMN_HEADERS_S", {})

def load_column_headers_default():
    ui_texts = load_ui_texts_main()
    return ui_texts.get("COLUMN_HEADERS_DEFAULT", {})

def load_lisa_headers_map():
    return load_settings().get("field_labels", {}).get("lisa", {})

def load_sap_headers_map():
    return load_settings().get("field_labels", {}).get("sap", {})

def load_sales_headers_map():
    return load_settings().get("field_labels", {}).get("sales", {})

# --- NIEUW: BP default type opslaan/laden ---
def load_bp_default_type() -> str:
    """Geeft het standaard BP-type terug: '', 'C' of 'S'."""
    val = load_settings().get("bp_default_type", DEFAULT_SETTINGS["bp_default_type"])
    return val if val in ("", "C", "S") else ""

def save_bp_default_type(val: str):
    """Bewaar standaard BP-type (alleen '', 'C', 'S' toegestaan)."""
    if val not in ("", "C", "S"):
        return
    settings = load_settings()
    settings["bp_default_type"] = val
    save_settings(settings)
