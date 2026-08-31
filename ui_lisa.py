# =============================================================================
# ArticleSearch
# File:    ui_lisa.py
# Role:    LisaTab (QWidget) — toont de LISA-voorraadgegevens (per locatie/
#          magazijn) als tab in het Detail-venster (ui_detail.py).
# Version: 1.1.0
# Author:  Bart Bossuyt
# Changes: 1.1.0 — QTYKLEUR-1-BUGFIX (analoog aan ui_main.py v1.15.0):
#                   Min.Whs is een instelling per Magazijn, niet per
#                   Locatie — bij meerdere locaties binnen hetzelfde
#                   magazijn (bv. 3 rijen "Algemeen magazijn" voor
#                   152.COND: Beschikbaar 784/840/183, Min.Whs telkens
#                   500) kleurde de locatie met Beschikbaar=183 voorheen
#                   ten onrechte geel, ook al zat de som van de 3 locaties
#                   (1807) ruim boven Min.Whs (bevestigd met screenshot).
#                   Nieuwe groeperingslogica: Beschikbaar wordt eerst
#                   gesommeerd per Magazijn over alle rijen (er is hier
#                   maar 1 artikel per tabel, dus groeperen op Magazijn
#                   alleen volstaat — in tegenstelling tot de hoofdtabel
#                   in ui_main.py, die ook nog over meerdere artikelen
#                   loopt en dus op Art.Nr.+Magazijn moet groeperen), en
#                   pas dat magazijntotaal wordt vergeleken met Min.Whs.
# Changes: 1.0.0 — Eerste keer onder versiebeheer. QTYKLEUR-1 (analoog aan
#                   ui_main.py v1.14.0 en Prod Stock Overview): de
#                   "Beschikbaar"-kolom kleurt geel (#fff3b0) wanneer
#                   Beschikbaar < Min.Whs. De ruwe API-veldnamen achter de
#                   labels "Beschikbaar"/"Min.Whs" worden niet hardcoded,
#                   maar afgeleid uit LISA_HEADERS_MAP zelf (key waarvan
#                   de gemapte waarde overeenkomt met dat label) — robuust
#                   tegen een eventuele hernoeming van de onderliggende
#                   key in settings.py, zolang het weergegeven label
#                   ongewijzigd blijft.
# =============================================================================

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtGui import QColor

from settings import load_lisa_headers_map

LISA_HEADERS_MAP = load_lisa_headers_map()

# QTYKLEUR-1: zelfde geel als PROD_STOCK_HEDEN_YELLOW/
# ARTIKEL_QTY_ONDER_MINWHS_GEEL in ui_main.py.
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


class LisaTab(QWidget):
    def __init__(self, data):
        super().__init__()
        layout = QVBoxLayout(self)
        table = QTableWidget()
        headers = list(LISA_HEADERS_MAP.keys())

        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(headers))
            mapped_headers = [LISA_HEADERS_MAP.get(h, h) for h in headers]
            table.setHorizontalHeaderLabels(mapped_headers)

            # QTYKLEUR-1: kolomindex van "Beschikbaar" bepalen + ruwe keys
            # van "Min.Whs"/"Magazijn" om de gegroepeerde vergelijking mee
            # te maken.
            beschikbaar_key = _raw_key_for_label(LISA_HEADERS_MAP, "Beschikbaar")
            minwhs_key = _raw_key_for_label(LISA_HEADERS_MAP, "Min.Whs")
            magazijn_key = _raw_key_for_label(LISA_HEADERS_MAP, "Magazijn")
            try:
                beschikbaar_col = headers.index(beschikbaar_key) if beschikbaar_key else None
            except ValueError:
                beschikbaar_col = None

            # QTYKLEUR-1-BUGFIX: Beschikbaar eerst sommeren per Magazijn
            # (er is hier maar 1 artikel in de hele tabel, dus groeperen
            # op Magazijn alleen volstaat) — pas dat totaal telt mee voor
            # de geel-vergelijking, niet de individuele locatie.
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

                    # QTYKLEUR-1: gegroepeerde Beschikbaar (som over alle
                    # locaties binnen hetzelfde Magazijn) < Min.Whs => geel
                    # gemarkeerd + tooltip.
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
            table.setItem(0, 0, QTableWidgetItem("❌ Geen LISA data beschikbaar."))

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)