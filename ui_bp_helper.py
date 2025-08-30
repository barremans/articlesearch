# ui_bp_helper.py
from PySide6.QtWidgets import QLabel, QTextBrowser
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
import html


def map_card_type(value: str) -> str:
    if not value:
        return "-"
    return {"C": "Customer", "S": "Supplier"}.get(value.strip().upper(), value)


def make_value_label(bold: bool = True) -> QLabel:
    lbl = QLabel("-")
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    f = QFont(); f.setBold(bold)
    lbl.setFont(f)
    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return lbl


def make_caption_label(text: str, min_w: int = 120) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    lbl.setMinimumWidth(min_w)
    return lbl


def build_place(country: str | None, zip_code: str | None, city: str | None) -> str:
    c = (country or "").strip()
    z = (zip_code or "").strip()
    t = (city or "").strip()
    if not (c or z or t):
        return "-"
    return f"{(c + '-') if c else ''}{z}{(' ' + t) if t else ''}".strip()


def set_html_or_text(browser: QTextBrowser, value):
    if not value:
        browser.setHtml("<i>-</i>")
        return
    s = str(value)
    if "<" in s and ">" in s:
        browser.setHtml(s)
    else:
        browser.setHtml(f"<pre style='margin:0; white-space:pre-wrap;'>{html.escape(s)}</pre>")


def fmt_num(value) -> str:
    try:
        if value is None or value == "":
            return "-"
        # 12 500,00 met non-breaking spaces
        return f"{float(value):,.2f}".replace(",", " ").replace(".", ",").replace(" ", "\u00A0")
    except Exception:
        return str(value)


# ===================== NIEUW: generieke helpers =====================

def extract_bp_core(bp: dict) -> dict:
    """
    Neemt ofwel een vlakke BP-dict, of een wrapper:
      { "Data": [ { ...BP velden... } ] }
    en retourneert steeds het binnenste item (dict) met de BP velden.
    """
    if not isinstance(bp, dict):
        return {}
    data = bp.get("Data")
    if isinstance(data, list) and data:
        first = data[0]
        return first if isinstance(first, dict) else {}
    return bp


def rich_html(text: str | None, *, danger: bool = False, bold: bool = False) -> str:
    """
    Geeft eenvoudige HTML-formatting terug voor status/waarden.
    - danger=True → rood (CSS color #c00)
    - bold=True   → vet
    Combinaties zijn toegestaan.
    """
    if text is None:
        text = "-"
    s = html.escape(str(text))
    if danger and bold:
        return f'<b><span style="color:#c00">{s}</span></b>'
    if danger:
        return f'<span style="color:#c00">{s}</span>'
    if bold:
        return f"<b>{s}</b>"
    return s
