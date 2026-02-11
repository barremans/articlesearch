# ui_docs_schema.py
#v1.0.1
from __future__ import annotations
import pandas as pd
import unicodedata

# ---- Zichtbare kolommen (zelfde voor Sales & Purchase) ----
VISIBLE_ORDER = [
    "DocNum", "CardCode", "CardName",
    "DocDate", "DocDueDate",
    "DocTotal", "PaidSum", "Outstanding",
    "OrderCount", "MaandenOud",
    "SalesOwner", "DocOwner",
    "Comments", "ProjectBased", 
]

# Alles buiten VISIBLE_ORDER tonen we niet.
HIDE_COLS = {
    "VATNbr", "DocEntry", "Comments", "Partner", "Vendor",
    "Buyer", "DeliveryCount", "DownPaymentCount", "ReturnCount",
    "InvoiceCount", "PurchaseOrderCount", "ReceiptCount",
}

# ---- Vertalingen voor UI ----
TRANSLATIONS = {
    "DocNum": "Documentnummer",
    "CardCode": "Relatiecode",
    "CardName": "Relatienaam",
    "DocDate": "Documentdatum",
    "DocDueDate": "Vervaldatum",
    "DocTotal": "Totaalbedrag",
    "PaidSum": "Betaald",
    "Outstanding": "Openstaand",
    "OrderCount": "Aantal orders",
    "MaandenOud": "Leeftijd (mnd)",
    "SalesOwner": "Verkoper",
    "DocOwner": "Documenteigenaar",
    "Comments": "Opmerkingen",     
    "ProjectBased": "Projectgebonden", 
}

def get_visible_labels() -> list[str]:
    """Geef de zichtbare kolomnamen met vertalingen."""
    return [TRANSLATIONS.get(c, c) for c in VISIBLE_ORDER]

# ---- Sorteerstand (kan door ui_docs gezet worden) ----
_SORT_MODE = "cardname"  # standaard gevraagd: CardName → DocDueDate ↑ → MaandenOud ↑

def set_sort_mode(mode: str) -> None:
    global _SORT_MODE
    mode = (mode or "").lower().strip()
    if mode not in {"cardname", "cardcode", "docowner", "salesowner", "maandenoud"}:
        mode = "cardname"
    _SORT_MODE = mode

# ---------- helpers ----------
def _norm_name(x) -> str:
    """Maak naam sorteer-vriendelijk: trim, casefold, accenten weg."""
    if pd.isna(x):
        return ""
    s = str(x).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.casefold()

def _coerce_for_sort(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "MaandenOud" in out.columns:
        out["MaandenOud"] = pd.to_numeric(out["MaandenOud"], errors="coerce")
    for c in ("DocDate", "DocDueDate"):
        if c in out.columns and not pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = pd.to_datetime(out[c], errors="coerce")
    return out

def _stable_sort(df: pd.DataFrame, by: list[str], asc: list[bool]) -> pd.DataFrame:
    return df.sort_values(by=by, ascending=asc, na_position="last", kind="mergesort").reset_index(drop=True)

def _sort_df(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    df2 = _coerce_for_sort(df)

    if "CardName" in df2.columns:
        df2["__k_cardname"] = df2["CardName"].map(_norm_name)
    else:
        df2["__k_cardname"] = ""

    if mode == "cardname":
        keys = ["__k_cardname", "DocDueDate", "MaandenOud", "CardCode", "DocNum"]
        asc  = [True,           True,         True,          True,      True]
    elif mode == "cardcode":
        keys = ["CardCode", "__k_cardname", "DocDueDate", "MaandenOud", "DocNum"]
        asc  = [True,       True,           True,         True,         True]
    elif mode == "docowner":
        keys = ["DocOwner", "__k_cardname", "DocDueDate", "MaandenOud", "DocNum"]
        asc  = [True,       True,           True,         True,         True]
    elif mode == "salesowner":
        keys = ["SalesOwner", "__k_cardname", "DocDueDate", "MaandenOud", "DocNum"]
        asc  = [True,         True,           True,         True,         True]
    elif mode == "maandenoud":
        keys = ["MaandenOud", "DocDueDate", "CardCode", "DocNum"]
        asc  = [True,         True,        True,       True]
    else:
        keys = ["__k_cardname", "DocDueDate", "MaandenOud", "CardCode", "DocNum"]
        asc  = [True,           True,         True,          True,      True]

    keys_exist = [k for k in keys if k in df2.columns]
    asc_trim   = [asc[i] for i, k in enumerate(keys) if k in df2.columns]
    if keys_exist:
        df2 = _stable_sort(df2, keys_exist, asc_trim)

    if "__k_cardname" in df2.columns:
        df2 = df2.drop(columns=["__k_cardname"])

    return df2

def apply_schema(df: pd.DataFrame, section_code: str) -> pd.DataFrame:
    """Behoud enkel VISIBLE_ORDER (in vaste volgorde) en sorteer volgens _SORT_MODE."""
    cols = [c for c in VISIBLE_ORDER if c in df.columns]
    df2 = df[cols].copy()
    return _sort_df(df2, _SORT_MODE)
