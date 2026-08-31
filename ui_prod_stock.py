# =============================================================================
# ArticleSearch
# File:    ui_prod_stock.py
# Role:    "Productie Stock Overview" — apart venster (QWidget), geopend
#          vanuit ui_main.py wanneer search-type "Prod" gekozen is en een
#          dataset geselecteerd werd. Toont het stock-overzicht (client
#          "ProdStockOverview") voor alle artikelen van de gekozen dataset.
#          Geen data bij openen — enkel op expliciete "Ophalen"-klik (zelfde
#          patroon als PaymentsDue/Open Elements). Magazijnfilter
#          (Stock_Algemeen/Stock_Antwerpen/Stock_Miami), standaardwaarde uit
#          settings (load_prod_default_warehouse()). MinSAP > 0 kleurt de
#          cel lichtgroen (zelfde stijl als MINWHS-KLEUR-1 in ui_main.py).
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Initiële versie.
# =============================================================================
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QFileDialog, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from prod_info import get_prod_stock_overview, parse_artnbr
from settings import load_prod_default_warehouse

logger = logging.getLogger("ArticleSearch.ProdStock")
if not logger.handlers:
    h = logging.StreamHandler()
    f = logging.Formatter("[%(levelname)s] %(asctime)s - [ArticleSearch.ProdStock] %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# De 3 magazijn-kolommen waarop gefilterd kan worden (op vraag van gebruiker,
# vaste lijst — niet dynamisch afgeleid uit de respons).
WAREHOUSE_COLUMNS = ["Stock_Algemeen", "Stock_Antwerpen", "Stock_Miami"]

# Kolomvolgorde + NL-labels voor het stock-overzicht (velden uit de
# ProdStockOverview-respons, zie search_prodArt.txt).
STOCK_COLUMNS = [
    ("ArtCode", "Art.Nr."),
    ("Omschrijving", "Omschrijving"),
    ("StockHeden", "Stock vandaag"),
    ("MinSAP", "Min. SAP"),
    ("MaxSAP", "Max. SAP"),
    ("MaxRek", "Max. rek"),
    ("TotaalStock", "Totaal stock"),
    ("Gereserveerd", "Gereserveerd"),
    ("InBestelling", "In bestelling"),
    ("Beschikbaar", "Beschikbaar"),
    ("KGOpVoorraad", "Kg op voorraad"),
    ("BENPlatenPerPallet", "Platen/pallet"),
    ("NietCgk", "Niet CGK"),
    ("Stock_Algemeen", "Stock Algemeen"),
    ("Stock_Antwerpen", "Stock Antwerpen"),
    ("Stock_Miami", "Stock Miami"),
    ("LISA_Qty", "LISA Qty"),
]

# Numerieke kolommen -> rechts uitlijnen
_NUMERIC_KEYS = {
    "StockHeden", "MinSAP", "MaxSAP", "MaxRek", "TotaalStock", "Gereserveerd",
    "InBestelling", "Beschikbaar", "KGOpVoorraad", "BENPlatenPerPallet",
    "Stock_Algemeen", "Stock_Antwerpen", "Stock_Miami", "LISA_Qty",
}

MIN_SAP_GREEN = QColor("#d9f2d9")


class ProdStockWindow(QWidget):
    """Onafhankelijk venster met het productie-stock-overzicht van 1 dataset."""

    def __init__(self, dataset: dict, parent=None):
        super().__init__(parent)
        self.dataset = dataset or {}
        self._raw_data = []
        self._filtered_data = []

        ds_name = self.dataset.get("DS_Name", "")
        ds_owner = self.dataset.get("DS_Owner", "")
        self.setWindowTitle(f"Productie Stock Overview — {ds_name} ({ds_owner})".strip())
        self.resize(1250, 650)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI-opbouw
    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        item_count = len(parse_artnbr(self.dataset.get("DS_ArtNbr", "")))
        self.info_label = QLabel(
            f"Dataset: <b>{self.dataset.get('DS_Name', '')}</b> &nbsp;|&nbsp; "
            f"Eigenaar: {self.dataset.get('DS_Owner', '') or '-'} &nbsp;|&nbsp; "
            f"Artikelen in dataset: {item_count}"
        )
        layout.addWidget(self.info_label)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Magazijn:"))
        self.warehouse_select = QComboBox()
        self.warehouse_select.addItem("Alle magazijnen", "")
        for wh in WAREHOUSE_COLUMNS:
            self.warehouse_select.addItem(wh.replace("Stock_", ""), wh)
        default_wh = load_prod_default_warehouse()
        idx = self.warehouse_select.findData(default_wh) if default_wh else 0
        self.warehouse_select.setCurrentIndex(idx if idx >= 0 else 0)
        self.warehouse_select.currentIndexChanged.connect(self._on_warehouse_changed)
        controls.addWidget(self.warehouse_select)

        controls.addSpacing(24)
        controls.addWidget(QLabel("Zoeken:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter op art.nr. of omschrijving…")
        self.search_input.textChanged.connect(self._apply_text_filter)
        controls.addWidget(self.search_input)

        controls.addStretch()

        self.refresh_button = QPushButton("Ophalen")
        self.refresh_button.clicked.connect(self.load_data)
        controls.addWidget(self.refresh_button)

        self.export_button = QPushButton("Exporteer naar Excel")
        self.export_button.clicked.connect(self._export_xlsx)
        controls.addWidget(self.export_button)

        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionsClickable(False)
        layout.addWidget(self.table)

        self.status_label = QLabel("Aantal artikelen: 0 — klik op 'Ophalen' om de data te laden.")
        layout.addWidget(self.status_label)

    # ------------------------------------------------------------------
    # Data laden
    # ------------------------------------------------------------------
    def load_data(self):
        items = parse_artnbr(self.dataset.get("DS_ArtNbr", ""))
        if not items:
            QMessageBox.information(self, "Geen artikelen", "Deze dataset bevat geen artikelnummers.")
            return

        self.refresh_button.setEnabled(False)
        self.status_label.setText("Bezig met ophalen…")
        QApplication.processEvents()

        try:
            self._raw_data = get_prod_stock_overview(items)
        except Exception as e:
            logger.error(f"Kon stock-overzicht niet ophalen: {e}")
            QMessageBox.critical(self, "Fout", f"Kon stock-overzicht niet ophalen:\n{e}")
            self._raw_data = []
        finally:
            self.refresh_button.setEnabled(True)

        self._apply_text_filter()

    # ------------------------------------------------------------------
    # Filtering (magazijn + zoekterm)
    # ------------------------------------------------------------------
    def _visible_warehouse_columns(self) -> list:
        selected = self.warehouse_select.currentData()
        if not selected:
            return list(WAREHOUSE_COLUMNS)
        return [selected]

    def _on_warehouse_changed(self, _index: int):
        self._apply_text_filter()

    def _apply_text_filter(self):
        term = self.search_input.text().strip().lower()
        if term:
            data = [
                r for r in self._raw_data
                if term in str(r.get("ArtCode", "") or "").lower()
                or term in str(r.get("Omschrijving", "") or "").lower()
            ]
        else:
            data = list(self._raw_data)
        self._filtered_data = data
        self._populate_table(data)

    # ------------------------------------------------------------------
    # Tabel vullen
    # ------------------------------------------------------------------
    def _populate_table(self, data: list):
        hidden_wh = set(WAREHOUSE_COLUMNS) - set(self._visible_warehouse_columns())
        columns = [(key, label) for key, label in STOCK_COLUMNS if key not in hidden_wh]

        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([label for _, label in columns])

        for row, rec in enumerate(data):
            for col, (key, _label) in enumerate(columns):
                val = rec.get(key)
                text = "" if val is None else str(val)
                item = QTableWidgetItem(text)

                if key in _NUMERIC_KEYS:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                # MinSAP > 0 -> lichtgroene achtergrond (analoog MINWHS-KLEUR-1)
                if key == "MinSAP":
                    try:
                        if val is not None and float(val) > 0:
                            item.setBackground(MIN_SAP_GREEN)
                            item.setToolTip("Min. SAP > 0")
                    except (TypeError, ValueError):
                        pass

                self.table.setItem(row, col, item)

        header = self.table.horizontalHeader()
        for i in range(len(columns)):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        self.table.resizeColumnsToContents()
        header.setStretchLastSection(True)

        self.status_label.setText(f"Aantal artikelen: {len(data)}")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _export_xlsx(self):
        if not self._filtered_data:
            QMessageBox.information(self, "Geen data", "Er is niets om te exporteren.")
            return

        default_name = f"prod_stock_{self.dataset.get('DS_Name', 'dataset')}.xlsx".replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporteer naar Excel", default_name, "Excel-bestand (*.xlsx)"
        )
        if not path:
            return

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Stock overzicht"

            hidden_wh = set(WAREHOUSE_COLUMNS) - set(self._visible_warehouse_columns())
            columns = [(key, label) for key, label in STOCK_COLUMNS if key not in hidden_wh]

            ws.append([label for _, label in columns])
            for rec in self._filtered_data:
                ws.append([rec.get(key) for key, _ in columns])

            wb.save(path)
            QMessageBox.information(self, "Export voltooid", f"Bestand opgeslagen:\n{path}")
        except Exception as e:
            logger.error(f"Fout bij export: {e}")
            QMessageBox.critical(self, "Fout bij export", str(e))
