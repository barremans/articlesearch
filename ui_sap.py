# =============================================================================
# ArticleSearch
# File:    ui_sap.py
# Role:    SapTab (QWidget) — toont de SAP-voorraadgegevens (per magazijn,
#          incl. berekende "VrijeStock") als tab in het Detail-venster
#          (ui_detail.py).
# Version: 1.1.0
# Author:  Bart Bossuyt
# Changes: 1.1.0 — QTYKLEUR-1-BUGFIX (analoog aan ui_main.py v1.15.0 en
#                   ui_lisa.py v1.1.0): Min.Whs is een instelling per
#                   Magazijn, niet per Locatie. De SAP-tab toont weliswaar
#                   al 1 rij per magazijn (i.p.v. per locatie zoals de
#                   LISA-tab), maar dezelfde onderliggende denkfout zat in
#                   de vergelijking als in ui_main.py/ui_lisa.py: geel
#                   werd puur per-rij bepaald. Nu expliciet gegroepeerd op
#                   Magazijn (via magazijn_totals-dict) vóór de
#                   Min.Whs-vergelijking, consistent met de andere twee
#                   bestanden — bij de huidige 1-rij-per-magazijn-
#                   structuur heeft dit in de praktijk hetzelfde
#                   eindresultaat, maar de logica is nu overal identiek
#                   opgebouwd (voorkomt toekomstige inconsistentie mocht
#                   de SAP-respons ooit meerdere rijen per magazijn gaan
#                   bevatten).
# Changes: 1.0.0 — Eerste keer onder versiebeheer. QTYKLEUR-1: de
#                   "Beschikbaar"-kolom kleurt geel (#fff3b0) wanneer
#                   Beschikbaar < Min.Whs. Ruwe key achter beide labels
#                   afgeleid uit SAP_HEADERS_MAP zelf, niet hardcoded.
# =============================================================================
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtGui import QColor

from settings import load_sap_headers_map

SAP_HEADERS_MAP = load_sap_headers_map()

# QTYKLEUR-1: zelfde geel als PROD_STOCK_HEDEN_YELLOW/
# ARTIKEL_QTY_ONDER_MINWHS_GEEL (ui_main.py) / BESCHIKBAAR_ONDER_MINWHS_GEEL
# (ui_lisa.py).
BESCHIKBAAR_ONDER_MINWHS_GEEL = QColor("#fff3b0")


def _raw_key_for_label(headers_map: dict, label: str):
    """
    QTYKLEUR-1: zoekt de ruwe data-key op waarvan de gemapte weergavetekst
    in headers_map exact overeenkomt met 'label'. Geeft None terug als het
    label niet voorkomt (bv. als de kolom ooit hernoemd wordt).
    """
    for raw_key, mapped_label in headers_map.items():
        if mapped_label == label:
            return raw_key
    return None


class SapTab(QWidget):
    def __init__(self, raw_data):
        super().__init__()
        layout = QVBoxLayout(self)
        table = QTableWidget()

        # Voorbereiden van data (bereken VrijeStock)
        data = []
        for entry in raw_data:
            vrije_stock = entry.get("OnHand", 0) - entry.get("IsCommited", 0)
            data.append({
                "WhsName": entry.get("WhsName", ""),
                "OnHand": entry.get("OnHand", 0),
                "IsCommited": entry.get("IsCommited", 0),
                "OnOrder": entry.get("OnOrder", 0),
                "MinStock": entry.get("MinStock", 0),
                "MaxStock": entry.get("MaxStock", 0),
                "VrijeStock": vrije_stock
            })

        headers = list(SAP_HEADERS_MAP.keys())

        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(headers))
            mapped_headers = [SAP_HEADERS_MAP.get(h, h) for h in headers]
            table.setHorizontalHeaderLabels(mapped_headers)

            # QTYKLEUR-1: kolomindex van "Beschikbaar" bepalen + ruwe keys
            # van "Min.Whs"/"Magazijn" om de gegroepeerde vergelijking mee
            # te maken.
            beschikbaar_key = _raw_key_for_label(SAP_HEADERS_MAP, "Beschikbaar")
            minwhs_key = _raw_key_for_label(SAP_HEADERS_MAP, "Min.Whs")
            magazijn_key = _raw_key_for_label(SAP_HEADERS_MAP, "Magazijn")
            try:
                beschikbaar_col = headers.index(beschikbaar_key) if beschikbaar_key else None
            except ValueError:
                beschikbaar_col = None

            # QTYKLEUR-1-BUGFIX: Beschikbaar eerst sommeren per Magazijn
            # (consistent met ui_main.py/ui_lisa.py) — pas dat totaal telt
            # mee voor de geel-vergelijking.
            magazijn_totals = {}
            if beschikbaar_key is not None and magazijn_key is not None:
                for rec in data:
                    mkey = rec.get(magazijn_key)
                    try:
                        beschikbaar_num = float(str(rec.get(beschikbaar_key, 0)).replace(",", "."))
                    except (TypeError, ValueError):
                        beschikbaar_num = 0.0
                    magazijn_totals[mkey] = magazijn_totals.get(mkey, 0.0) + beschikbaar_num

            for row, record in enumerate(data):
                for col, key in enumerate(headers):
                    val = str(record.get(key, ""))
                    item = QTableWidgetItem(val)
                    item.setToolTip(val)

                    # QTYKLEUR-1: gegroepeerde Beschikbaar (som binnen
                    # hetzelfde Magazijn) < Min.Whs => geel gemarkeerd.
                    if (
                        beschikbaar_col is not None
                        and col == beschikbaar_col
                        and minwhs_key is not None
                    ):
                        try:
                            minwhs_val = float(str(record.get(minwhs_key, "")).replace(",", "."))
                            if magazijn_key is not None:
                                groep_val = magazijn_totals.get(record.get(magazijn_key))
                            else:
                                groep_val = None
                            if groep_val is None:
                                groep_val = float(str(val).replace(",", "."))
                            if groep_val < minwhs_val:
                                item.setBackground(BESCHIKBAAR_ONDER_MINWHS_GEEL)
                                item.setToolTip(
                                    f"{val}\n⚠️ Totaal Beschikbaar voor dit magazijn "
                                    f"({groep_val:g}) < Min.Whs ({minwhs_val:g})"
                                )
                        except (TypeError, ValueError):
                            pass

                    table.setItem(row, col, item)
        else:
            table.setRowCount(1)
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Informatie"])
            table.setItem(0, 0, QTableWidgetItem("❌ Geen SAP data beschikbaar."))

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)