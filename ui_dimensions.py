 #=============================================================================
# ArticleSearch
# File:    ui_dimensions.py
# Role:    Widget voor de "Dimensions"-tab in DetailWindow (ui_detail.py).
#          Toont artikelafmetingen/-gewichten (MEASUREMENT_INFO uit de
#          ZStockInfoP-payload, config WEZ7CY) als Veld/Waarde-tabel,
#          analoog aan de bestaande LogisticsTab.
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Initiële versie. DimensionsTab-widget. DIMENSION_LABELS
#                   voor NL-labels per veld, UNIT_PAIRS om waarde + eenheid
#                   samen te voegen tot 1 leesbare cel (bv. "80 mm"),
#                   SKIP_FIELDS voor technische/irrelevante velden
#                   (unit-codes, UoM-metadata, CPQ-configuratievelden).
#                   Aanname: S=Verkoop-UoM, B=Verpakking-UoM, I=Inventaris-UoM
#                   (SAP B1-conventie) — te bevestigen door gebruiker indien
#                   dit in deze omgeving anders ligt.
# =============================================================================
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
)

# ---------------------------------------------------------------------------
# Vriendelijke Nederlandse labels voor de MEASUREMENT_INFO-velden.
# S = Verkoop-UoM, B = Verpakking/Bulk-UoM, I = Inventaris-UoM (SAP B1-conventie).
# Pas gerust aan indien de S/B/I-prefixen in jullie SAP-omgeving een andere
# betekenis hebben.
# ---------------------------------------------------------------------------
DIMENSION_LABELS = {
    "SHeight1": "Hoogte 1 (Verkoop)",
    "SHeight2": "Hoogte 2 (Verkoop)",
    "SWidth1": "Breedte 1 (Verkoop)",
    "SWidth2": "Breedte 2 (Verkoop)",
    "SLength1": "Lengte 1 (Verkoop)",
    "Slength2": "Lengte 2 (Verkoop)",
    "SVolume": "Volume (Verkoop)",
    "SWeight1": "Gewicht 1 (Verkoop)",
    "SWeight2": "Gewicht 2 (Verkoop)",

    "BHeight1": "Hoogte 1 (Verpakking)",
    "BHeight2": "Hoogte 2 (Verpakking)",
    "BWidth1": "Breedte 1 (Verpakking)",
    "BWidth2": "Breedte 2 (Verpakking)",
    "BLength1": "Lengte 1 (Verpakking)",
    "Blength2": "Lengte 2 (Verpakking)",
    "BVolume": "Volume (Verpakking)",
    "BWeight1": "Gewicht 1 (Verpakking)",
    "BWeight2": "Gewicht 2 (Verpakking)",

    "IWeight1": "Gewicht 1 (Inventaris)",
    "IWeight2": "Gewicht 2 (Inventaris)",
}

# Elk dimensieveld heeft een bijhorend *UnitName-veld dat we samenvoegen
# tot één leesbare waarde (bv. "80 mm").
UNIT_PAIRS = {
    "SHeight1": "SHght1UnitName", "SHeight2": "SHght2UnitName",
    "SWidth1": "SWdth1UnitName", "SWidth2": "SWdth2UnitName",
    "SLength1": "SLen1UnitName", "Slength2": "SLen2UnitName",
    "SVolume": "SVolUnitName",
    "SWeight1": "SWght1UnitName", "SWeight2": "SWght2UnitName",

    "BHeight1": "BHght1UnitName", "BHeight2": "BHght2UnitName",
    "BWidth1": "BWdth1UnitName", "BWidth2": "BWdth2UnitName",
    "BLength1": "BLen1UnitName", "Blength2": "BLen2UnitName",
    "BVolume": "BVolUnitName",
    "BWeight1": "BWght1UnitName", "BWeight2": "BWght2UnitName",

    "IWeight1": "IWght1UnitName", "IWeight2": "IWght2UnitName",
}

# Velden die NIET als aparte rij getoond worden: de *Unit/*UnitName-velden
# (worden samengevoegd bij hun waarde-veld) en algemene/irrelevante velden.
SKIP_FIELDS = {
    "ItemCode",
    "InvntryUom", "SUoMEntry", "SalesUomName", "PUoMEntry", "PurchaseUomName",

    "SHght1Unit", "SHght1UnitName", "SHght2Unit", "SHght2UnitName",
    "SWdth1Unit", "SWdth1UnitName", "SWdth2Unit", "SWdth2UnitName",
    "SLen1Unit", "SLen1UnitName", "SLen2Unit", "SLen2UnitName",
    "SVolUnit", "SVolUnitName",
    "SWght1Unit", "SWght1UnitName", "SWght2Unit", "SWght2UnitName",

    "BHght1Unit", "BHght1UnitName", "BHght2Unit", "BHght2UnitName",
    "BWdth1Unit", "BWdth1UnitName", "BWdth2Unit", "BWdth2UnitName",
    "BLen1Unit", "BLen1UnitName", "BLen2Unit", "BLen2UnitName",
    "BVolUnit", "BVolUnitName",
    "BWght1Unit", "BWght1UnitName", "BWght2Unit", "BWght2UnitName",

    "IWght1Unit", "IWght1UnitName", "IWght2Unit", "IWght2UnitName",

    # CPQ-configuratievelden -> niet gerelateerd aan fysieke afmetingen
    "U_CPQ_DIM0001", "U_CPQ_OPT0001", "U_CPQ_OPT0002", "U_CPQ_DIM00002",
}


def _format_value(key: str, value, record: dict) -> str:
    """Combineer een numerieke waarde met de bijhorende eenheid-naam (indien aanwezig)."""
    if value is None:
        return ""

    if isinstance(value, float):
        text = f"{value:g}"  # geen overbodige nullen (80.0 -> 80, 1.5 -> 1.5)
    else:
        text = str(value)

    unit_key = UNIT_PAIRS.get(key)
    unit_name = record.get(unit_key) if unit_key else None
    if unit_name:
        text = f"{text} {unit_name}"
    return text


class DimensionsTab(QWidget):
    """
    Toont artikel-afmetingen (MEASUREMENT_INFO uit de ZStockInfoP-payload)
    als Veld/Waarde-tabel, analoog aan de Logistiek-tab.
    """

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        table = QTableWidget()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        data = data or {}
        rows = []
        for key, value in data.items():
            if key in SKIP_FIELDS:
                continue
            label = DIMENSION_LABELS.get(key, key)
            rows.append((label, _format_value(key, value, data)))

        if not rows:
            table.setRowCount(1)
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Informatie"])
            table.setItem(0, 0, QTableWidgetItem("❌ Geen dimensiedata beschikbaar."))
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        else:
            table.setRowCount(len(rows))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Veld", "Waarde"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

            for r, (label, val) in enumerate(rows):
                label_item = QTableWidgetItem(label)
                value_item = QTableWidgetItem(val)
                value_item.setToolTip(val)
                table.setItem(r, 0, label_item)
                table.setItem(r, 1, value_item)

        layout.addWidget(table)
        self.setLayout(layout)