# ui_labels.py
from __future__ import annotations
import os
from typing import Dict
import pandas as pd

_LANG = os.environ.get("DOCS_LANG", "nl").lower()
if _LANG not in {"nl","en"}:
    _LANG = "nl"

def set_language(lang: str) -> None:
    global _LANG
    _LANG = (lang or "nl").lower()
    if _LANG not in {"nl","en"}:
        _LANG = "nl"

def current_language() -> str:
    return _LANG

_COLS: Dict[str, Dict[str, str]] = {
    "nl": {
        "DocNum": "Documentnr",
        "CardCode": "Relatiecode",
        "CardName": "Naam",
        "DocDate": "Documentdatum",
        "DocDueDate": "Vervaldatum",
        "DocTotal": "Totaal",
        "PaidSum": "Betaald",
        "Outstanding": "Openstaand",
        "OrderCount": "Aantal regels",
        "MaandenOud": "Maanden oud",
        "SalesOwner": "Verkoopverantw.",
        "DocOwner": "Doc-eigenaar",
        # Summary kolommen
        "Section": "Sectie",
        "Section (decoded)": "Sectie (omschrijving)",
        "Count": "Aantal",
        "Total DocTotal": "Som totaal",
        "Total Outstanding": "Som openstaand",
        "Earliest Due": "Eerste vervaldatum",
        "Latest Due": "Laatste vervaldatum",
        "SalesOpen": "Open verkoop",
        "PurchaseOpen": "Open aankoop",
    },
    "en": {
        "DocNum": "Document No.",
        "CardCode": "BP Code",
        "CardName": "Name",
        "DocDate": "Document Date",
        "DocDueDate": "Due Date",
        "DocTotal": "Total",
        "PaidSum": "Paid",
        "Outstanding": "Outstanding",
        "OrderCount": "Line Count",
        "MaandenOud": "Months old",
        "SalesOwner": "Sales owner",
        "DocOwner": "Doc owner",
        # Summary columns
        "Section": "Section",
        "Section (decoded)": "Section (description)",
        "Count": "Count",
        "Total DocTotal": "Sum total",
        "Total Outstanding": "Sum outstanding",
        "Earliest Due": "Earliest due",
        "Latest Due": "Latest due",
        "SalesOpen": "Sales open",
        "PurchaseOpen": "Purchase open",
    },
}

def col_label(key: str) -> str:
    return _COLS.get(_LANG, {}).get(key, key)

def translate_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = _COLS.get(_LANG, {})
    rename = {c: mapping[c] for c in df.columns if c in mapping}
    return df.rename(columns=rename) if rename else df

_SECTION_META = {
    "OSO": {"nl": ("Open verkooporder", "Verkoop", "Order"),
            "en": ("Open sales order", "Sales", "Order")},
    "OSDL": {"nl": ("Open leveringen (verkoop)", "Verkoop", "Levering"),
             "en": ("Open deliveries (sales)", "Sales", "Delivery")},
    "OSR": {"nl": ("Open retouren (verkoop)", "Verkoop", "Retour"),
            "en": ("Open returns (sales)", "Sales", "Return")},
    "OSDP": {"nl": ("Open voorschotten (verkoop)", "Verkoop", "Voorschot"),
             "en": ("Open down payments (sales)", "Sales", "DownPayment")},
    "OSI": {"nl": ("Open verkoopfacturen", "Verkoop", "Factuur"),
            "en": ("Open sales invoices", "Sales", "Invoice")},
    "OPO": {"nl": ("Open aankooporder", "Aankoop", "Order"),
            "en": ("Open purchase order", "Purchase", "Order")},
    "OPDL": {"nl": ("Open ontvangsten (aankoop)", "Aankoop", "Ontvangst"),
             "en": ("Open receipts (purchase)", "Purchase", "Receipt")},
    "OPR": {"nl": ("Open retouren (aankoop)", "Aankoop", "Retour"),
            "en": ("Open returns (purchase)", "Purchase", "Return")},
    "OPI": {"nl": ("Open aankoopfacturen", "Aankoop", "Factuur"),
            "en": ("Open purchase invoices", "Purchase", "Invoice")},
}

def section_full_label(code: str) -> str:
    meta = _SECTION_META.get(code, {})
    tup = meta.get(_LANG)
    if not tup:
        return code
    human, dom, doc = tup
    return f"{code} — {human} ({dom} / {doc})"

_UI = {
    "nl": {
        "group_count": "Aantal",
        "group_export": "Export-bereik",
        "group_options": "Opties — groepering/sortering",
        "opt_cardname": "CardName",
        "opt_cardcode": "CardCode",
        "opt_docowner": "DocOwner → Naam + Vervaldatum ↑",
        "opt_salesowner": "SalesOwner → Naam + Vervaldatum ↑",
        "opt_maanden": "Maanden oud ↓, Vervaldatum ↑",
        "rb_current": "Huidige tab",
        "rb_all": "Alle tabs",
        "rb_sales": "Sales (OSO/OSDL/OSDP/OSR/OSI)",
        "rb_purchase": "Purchase (OPO/OPDL/OPR/OPI)",
        "btn_fetch": "Ophalen",
        "btn_export": "Exporteer…",
        "btn_export_all": "Exporteer alles",
        "tab_summary": "Samenvatting",
        "sub_sales_sections": "Secties (Sales)",
        "sub_customers": "Per klant",
        "sub_purchase_sections": "Secties (Purchase)",
        "sub_docowner": "Per DocOwner",
        "sub_salesowner": "Per SalesOwner (Sales)",
        "sub_buyer": "Per Buyer (Purchase)",
        "sep_sales": "— Verkoop —",
        "sep_summary": "— Samenvatting —",
        "sep_purchase": "— Aankoop —",
    },
    "en": {
        "group_count": "Count",
        "group_export": "Export range",
        "group_options": "Options — grouping/sorting",
        "opt_cardname": "CardName",
        "opt_cardcode": "CardCode",
        "opt_docowner": "DocOwner → Name + DueDate ↑",
        "opt_salesowner": "SalesOwner → Name + DueDate ↑",
        "opt_maanden": "Months old ↓, DueDate ↑",
        "rb_current": "Current tab",
        "rb_all": "All tabs",
        "rb_sales": "Sales (OSO/OSDL/OSDP/OSR/OSI)",
        "rb_purchase": "Purchase (OPO/OPDL/OPR/OPI)",
        "btn_fetch": "Fetch",
        "btn_export": "Export…",
        "btn_export_all": "Export all",
        "tab_summary": "Summary",
        "sub_sales_sections": "Sections (Sales)",
        "sub_customers": "By customer",
        "sub_purchase_sections": "Sections (Purchase)",
        "sub_docowner": "By DocOwner",
        "sub_salesowner": "By SalesOwner (Sales)",
        "sub_buyer": "By Buyer (Purchase)",
        "sep_sales": "— Sales —",
        "sep_summary": "— Summary —",
        "sep_purchase": "— Purchase —",
    },
}

def ui(key: str) -> str:
    return _UI.get(_LANG, {}).get(key, key)
