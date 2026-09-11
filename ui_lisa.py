# =============================================================================
# ArticleSearch
# File:    ui_lisa.py
# Role:    LisaTab (QWidget) — toont de LISA-voorraadgegevens (per locatie/
#          magazijn) als tab in het Detail-venster (ui_detail.py).
# Version: 1.2.0
# Author:  Bart Bossuyt
# Changes: 1.2.0 — BUGFIX (backend-bug, bevestigd via live JSON-voorbeeld
#                   artikel 40.3.5.2): de LISA-sectie zelf levert
#                   QTYMININV/QTYMAXINV als som over ALLE magazijnen i.p.v.
#                   per magazijn opgesplitst (bv. beide op 15.0/28.0,
#                   terwijl Algemeen=10/20 en Antwerpen=5/8 de correcte
#                   per-magazijn waarden zijn) — de STOCK.SAP-sectie van
#                   dezelfde payload heeft dit wél correct
#                   (MinStock/MaxStock per WhsCode/WhsName). Nieuwe
#                   constructor-parameter `sap_data` (self.detail_data
#                   ["STOCK"]["SAP"], meegegeven vanuit ui_detail.py
#                   v1.4.0): een dict {WhsName: (MinStock, MaxStock)}
#                   wordt opgebouwd en gekoppeld aan elke LISA-rij via
#                   WHSNAME<->WhsName. Zowel de GETOONDE waarde in de
#                   Min.Whs/Max.Whs-kolommen als de vergelijking voor de
#                   QTYKLEUR-1-gele-markering gebruiken nu deze SAP-
#                   waarden i.p.v. de (foutieve) eigen LISA-velden.
#                   Terugval op de originele LISA-waarde blijft bestaan
#                   wanneer er geen sap_data is meegegeven of geen
#                   matchend magazijn gevonden wordt (bv. oudere aanroeper
#                   die nog geen sap_data doorgeeft) — dan een tooltip-
#                   waarschuwing i.p.v. stilzwijgend een foutieve waarde.
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


def _build_sap_minmax_map(sap_data: list) -> dict:
    """
    Bouwt {WhsName: (MinStock, MaxStock)} op uit de STOCK.SAP-sectie van
    dezelfde detailpayload — gebruikt als terugvalbron voor Min.Whs/
    Max.Whs, want de LISA-sectie zelf levert deze (bug) gesommeerd over
    alle magazijnen i.p.v. per magazijn (zie changelog v1.2.0 hierboven).
    """
    result = {}
    for rec in (sap_data or []):
        whs = rec.get("WhsName")
        if whs is None:
            continue
        try:
            min_val = float(rec.get("MinStock") or 0)
        except (TypeError, ValueError):
            min_val = None
        try:
            max_val = float(rec.get("MaxStock") or 0)
        except (TypeError, ValueError):
            max_val = None
        result[whs] = (min_val, max_val)
    return result


class LisaTab(QWidget):
    def __init__(self, data, sap_data: list = None):
        super().__init__()
        layout = QVBoxLayout(self)
        table = QTableWidget()
        headers = list(LISA_HEADERS_MAP.keys())

        sap_minmax = _build_sap_minmax_map(sap_data)

        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(headers))
            mapped_headers = [LISA_HEADERS_MAP.get(h, h) for h in headers]
            table.setHorizontalHeaderLabels(mapped_headers)

            # QTYKLEUR-1: kolomindex van "Beschikbaar" bepalen + ruwe keys
            # van "Min.Whs"/"Max.Whs"/"Magazijn" om de gegroepeerde
            # vergelijking + SAP-terugval mee te maken.
            beschikbaar_key = _raw_key_for_label(LISA_HEADERS_MAP, "Beschikbaar")
            minwhs_key = _raw_key_for_label(LISA_HEADERS_MAP, "Min.Whs")
            maxwhs_key = _raw_key_for_label(LISA_HEADERS_MAP, "Max.Whs")
            magazijn_key = _raw_key_for_label(LISA_HEADERS_MAP, "Magazijn")
            try:
                beschikbaar_col = headers.index(beschikbaar_key) if beschikbaar_key else None
            except ValueError:
                beschikbaar_col = None
            try:
                minwhs_col = headers.index(minwhs_key) if minwhs_key else None
            except ValueError:
                minwhs_col = None
            try:
                maxwhs_col = headers.index(maxwhs_key) if maxwhs_key else None
            except ValueError:
                maxwhs_col = None

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
                magazijn_val = record.get(magazijn_key) if magazijn_key is not None else None
                sap_min, sap_max = sap_minmax.get(magazijn_val, (None, None))

                for col, key in enumerate(headers):
                    # SAP-terugval: Min.Whs/Max.Whs tonen we uit de SAP-
                    # sectie (per magazijn correct) i.p.v. de eigen
                    # (foutieve, over alle magazijnen gesommeerde)
                    # LISA-waarde — met terugval op de originele LISA-
                    # waarde wanneer er geen match/sap_data is.
                    used_sap_fallback = False
                    if col == minwhs_col and sap_min is not None:
                        val = f"{sap_min:g}"
                        used_sap_fallback = True
                    elif col == maxwhs_col and sap_max is not None:
                        val = f"{sap_max:g}"
                        used_sap_fallback = True
                    else:
                        val = str(record.get(key, ""))

                    item = QTableWidgetItem(val)
                    if used_sap_fallback:
                        item.setToolTip(f"{val}\n(overgenomen uit SAP-tab — LISA levert dit veld foutief gesommeerd over alle magazijnen)")
                    else:
                        item.setToolTip(val)
                        if col in (minwhs_col, maxwhs_col) and (minwhs_col is not None or maxwhs_col is not None):
                            item.setToolTip(f"{val}\n⚠️ Geen SAP-terugvalwaarde gevonden voor dit magazijn — mogelijk foutief (zie QTYKLEUR-1 v1.2.0).")

                    # QTYKLEUR-1: gegroepeerde Beschikbaar (som over alle
                    # locaties binnen hetzelfde Magazijn) < Min.Whs (SAP-
                    # waarde, per magazijn correct) => geel gemarkeerd.
                    if (
                        beschikbaar_col is not None
                        and col == beschikbaar_col
                    ):
                        try:
                            minwhs_val = sap_min
                            if minwhs_val is None and minwhs_key is not None:
                                # laatste terugval: originele (mogelijk foutieve) LISA-waarde
                                minwhs_val = float(str(record.get(minwhs_key, "")).replace(",", "."))
                            if magazijn_key is not None:
                                groep_val = magazijn_totals.get(record.get(magazijn_key))
                            else:
                                groep_val = None
                            if groep_val is None:
                                groep_val = float(str(val).replace(",", "."))
                            if minwhs_val is not None and groep_val < minwhs_val:
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