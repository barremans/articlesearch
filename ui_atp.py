#ui_atp.py
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QHeaderView
)
from PySide6.QtGui import QColor, QBrush, QFont, QKeySequence
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut

from atp_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT
from ui_po import PoWidget
from ui_so import SoWidget

class AtpWidget(QWidget):
    def __init__(self, itemcode, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ATP")
        self.resize(1000, 500)
        self.itemcode = itemcode

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Kies magazijn voor artikel: {itemcode}"))

        self.combo = QComboBox()
        self.combo.addItem("Algemeen magazijn", "01")
        self.combo.addItem("Magazijn Antwerpen", "03")
        self.combo.addItem("Magazijn Miami", "04")
        layout.addWidget(self.combo)

        self.button = QPushButton("Data ophalen")
        self.button.clicked.connect(self.load_data)
        layout.addWidget(self.button)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Row", "Doc", "Klant", "Orderdatum", "Leveringsdatum",
            "Besteld", "Bevestigd", "Beschikbaar"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.table)

        self.count_label = QLabel("Verkooporders: 0, Aankoop Bestelling: 0")
        layout.addWidget(self.count_label)

        # Dubbelklik activeren
        self.table.cellDoubleClicked.connect(self.handle_double_click)

        # --- Sneltoetsen ---
        QShortcut(QKeySequence(Qt.Key_PageUp), self).activated.connect(self._combo_previous)
        QShortcut(QKeySequence(Qt.Key_PageDown), self).activated.connect(self._combo_next)
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.load_data)

    def _combo_previous(self):
        current_index = self.combo.currentIndex()
        if current_index > 0:
            self.combo.setCurrentIndex(current_index - 1)

    def _combo_next(self):
        current_index = self.combo.currentIndex()
        if current_index < self.combo.count() - 1:
            self.combo.setCurrentIndex(current_index + 1)

    def load_data(self):
        whscode = self.combo.currentData()

        config_id = API_ENVIRONMENTS[ENVIRONMENT]["atp_configP_id"]
        url = "https://api.cgk-group.com/api/datarequest"

        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {
                "@IN_ITEMCODE": self.itemcode,
                "@IN_WHSCODE": whscode
            }
        }

        headers = get_auth_header()

        try:
            response = requests.post(url, headers=headers, json=payload, verify=False)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Fout", f"Request error: {e}")
            return

        if data.get("IsError"):
            QMessageBox.critical(self, "API Fout", data.get("ErrorMessage"))
            return

        rows = data.get("Data", [])
        self.table.setRowCount(len(rows))

        verkooporders_count = 0
        aankoop_count = 0
        total_rows = len(rows)

        for i, item in enumerate(rows):
            atp = item["atp"]
            doc = atp["Document"]

            if doc.startswith("OR"):
                verkooporders_count += 1
            elif doc.startswith("BE"):
                aankoop_count += 1

            def make_item(val, bold=False, background_color=None):
                txt = str(val or "-")
                item = QTableWidgetItem(txt)
                item.setToolTip(txt)
                font = QFont()
                font.setBold(bold)
                item.setFont(font)
                if background_color:
                    item.setBackground(QBrush(background_color))
                return item

            def format_date(d):
                if d and len(d) >= 10:
                    return f"{d[8:10]}-{d[5:7]}-{d[0:4]}"
                return "-"

            self.table.setItem(i, 0, make_item(atp["RowOrder"]))
            self.table.setItem(i, 1, make_item(doc))
            self.table.setItem(i, 2, make_item(atp.get("KlantLeverancier")))
            self.table.setItem(i, 3, make_item(format_date(atp["Orderdatum"])))
            self.table.setItem(i, 4, make_item(format_date(atp["Leveringsdatum"])))
            self.table.setItem(i, 5, make_item(atp.get("Besteld")))
            self.table.setItem(i, 6, make_item(atp.get("Bevestigd")))

            is_first_row = (i == 0)
            is_last_row = (i == total_rows - 1)
            bg_color = QColor("#c8f7c5") if doc.startswith("BE") else None
            beschikbaar_item = make_item(
                atp.get("Beschikbaar"),
                bold=(is_first_row or is_last_row),
                background_color=bg_color if doc.startswith("BE") else None
            )
            self.table.setItem(i, 7, beschikbaar_item)

        self.count_label.setText(f"Verkooporders: {verkooporders_count}, Aankoop Bestelling: {aankoop_count}")

    def handle_double_click(self, row, column):
        if column != 1:
            return

        doc_item = self.table.item(row, column)
        if not doc_item:
            return

        doc_text = doc_item.text().strip()
        if not doc_text:
            return

        # Verwijder eventuele dubbele of extra spaties
        doc_text = " ".join(doc_text.split())

        # Splits op spatie om nummer apart te halen
        parts = doc_text.split(" ")
        if len(parts) == 2:
            nummer = parts[1]
        else:
            nummer = doc_text[2:] if len(doc_text) > 2 else ""

        if doc_text.startswith("BE") and nummer:
            self.open_po_widget(nummer)
        elif doc_text.startswith("OR") and nummer:
            self.open_so_widget(nummer)


    def open_po_widget(self, po_number):
        self.po_widget = PoWidget()
        self.po_widget.setWindowFlags(self.po_widget.windowFlags() | Qt.WindowStaysOnTopHint)
        self.po_widget.po_input.setText(po_number)
        self.po_widget.load_data()
        self.po_widget.show()
        self.po_widget.raise_()
        self.po_widget.activateWindow()


    def open_so_widget(self, so_number):
        self.so_widget = SoWidget()
        self.so_widget.setWindowFlags(self.so_widget.windowFlags() | Qt.WindowStaysOnTopHint)
        self.so_widget.so_input.setText(so_number)
        self.so_widget.load_data()
        self.so_widget.show()
        self.so_widget.raise_()
        self.so_widget.activateWindow()

