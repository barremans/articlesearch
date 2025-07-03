# ui_so.py

import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget
)
from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut

from atp_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT
from settings import load_field_labels

def format_date(date_str):
    if date_str and len(date_str) >= 10:
        return f"{date_str[8:10]}-{date_str[5:7]}-{date_str[0:4]}"
    return "-"

class SoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Verkooporder")
        self.resize(1400, 800)

        layout = QVBoxLayout(self)

        self.so_input = QLineEdit()
        self.so_input.setPlaceholderText("Geef SO-nummer in")
        layout.addWidget(QLabel("SO-nummer:"))
        layout.addWidget(self.so_input)

        self.fetch_button = QPushButton("Ophalen")
        self.fetch_button.clicked.connect(self.load_data)
        layout.addWidget(self.fetch_button)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(QLabel("Header info:"))
        layout.addWidget(self.result_text)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.rd_tab = QWidget()
        rd_layout = QVBoxLayout(self.rd_tab)
        self.rd_table = QTableWidget()
        rd_layout.addWidget(self.rd_table)
        self.tabs.addTab(self.rd_tab, "Orderlijnen")

        # --- Sneltoetsen ---
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.close)
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.load_data)

    def load_data(self):
        so_number = self.so_input.text().strip()
        if not so_number:
            QMessageBox.warning(self, "Fout", "Geef een geldig SO-nummer in.")
            return

        config_id = API_ENVIRONMENTS[ENVIRONMENT]["so_configP_id"]
        url = "https://api.cgk-group.com/api/datarequest"

        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {
                "@so": so_number
            }
        }

        headers = get_auth_header()

        try:
            response = requests.post(url, headers=headers, json=payload, verify=False)
            response.raise_for_status()
            data = response.json()

            if data.get("IsError"):
                QMessageBox.critical(self, "API Fout", data.get("ErrorMessage"))
                return

            doc_list = data.get("Data", [])
            if not doc_list:
                QMessageBox.information(self, "Geen data", "Geen verkooporder gevonden.")
                return

            doc_data = doc_list[0]

            self.show_header(doc_data)
            self.show_rd(doc_data.get("RD", []))

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Fout", f"Request error: {e}")

    def show_header(self, doc_data):
        lines = []
        lines.append(f"Ordernummer: {doc_data.get('DocNum')}")
        lines.append(f"Geannuleerd: {doc_data.get('CANCELED')}")
        lines.append(f"Status: {doc_data.get('DocStatus')}")
        lines.append(f"Datum: {format_date(doc_data.get('DocDate'))}")
        lines.append(f"Vervaldatum: {format_date(doc_data.get('DocDueDate'))}")
        lines.append(f"Klant: {doc_data.get('CardName')}")
        lines.append(f"BTW-nummer: {doc_data.get('LicTradNum')}")
        lines.append(f"Referentie: {doc_data.get('Ref1')}")
        lines.append(f"Opmerkingen: {doc_data.get('Comments')}")
        lines.append(f"Verkoper: {doc_data.get('SalesOwner')}")
        lines.append(f"Bevestigd: {doc_data.get('Confirmed')}")
        lines.append(f"Totaalbedrag: {doc_data.get('DocTotal')} {doc_data.get('DocCur')}")
        lines.append(f"BTW-bedrag: {doc_data.get('VatSum')}")

        self.result_text.setPlainText("\n".join(lines))

    def show_rd(self, rd_list):
        labels_map = load_field_labels("so_rd")
        headers = [
            labels_map.get("LineNum", "Regel"),
            labels_map.get("ItemCode", "Artikelcode"),
            labels_map.get("Dscription", "Omschrijving"),
            labels_map.get("Quantity", "Aantal"),
            labels_map.get("Price", "Prijs"),
            labels_map.get("DiscPrcnt", "Korting (%)"),
            labels_map.get("LineTotal", "Lijn totaal"),
            labels_map.get("WhsName", "Magazijn"),
            labels_map.get("ShipDate", "Verzenddatum"),
            labels_map.get("FreeTxt", "Vrije tekst")
        ]

        self.rd_table.setColumnCount(len(headers))
        self.rd_table.setHorizontalHeaderLabels(headers)
        self.rd_table.setRowCount(len(rd_list))

        header = self.rd_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        for row, line in enumerate(rd_list):
            self.rd_table.setItem(row, 0, QTableWidgetItem(str(line.get("LineNum"))))
            self.rd_table.setItem(row, 1, QTableWidgetItem(line.get("ItemCode", "")))
            self.rd_table.setItem(row, 2, QTableWidgetItem(line.get("Dscription", "")))
            self.rd_table.setItem(row, 3, QTableWidgetItem(str(line.get("Quantity"))))
            self.rd_table.setItem(row, 4, QTableWidgetItem(str(line.get("Price"))))
            self.rd_table.setItem(row, 5, QTableWidgetItem(str(line.get("DiscPrcnt"))))
            self.rd_table.setItem(row, 6, QTableWidgetItem(str(line.get("LineTotal"))))
            self.rd_table.setItem(row, 7, QTableWidgetItem(line.get("WhsName", "")))
            self.rd_table.setItem(row, 8, QTableWidgetItem(format_date(line.get("ShipDate"))))
            self.rd_table.setItem(row, 9, QTableWidgetItem(line.get("FreeTxt", "")))

        # Verwijder deze lijn:
        # self.rd_table.resizeColumnsToContents()

        # Stel eenmalig kolombreedtes in (optioneel, pas aan naar wens)
        self.rd_table.setColumnWidth(0, 60)    # Regel
        self.rd_table.setColumnWidth(1, 120)   # Artikelcode
        self.rd_table.setColumnWidth(2, 300)   # Omschrijving (stretch)
        self.rd_table.setColumnWidth(3, 70)    # Aantal
        self.rd_table.setColumnWidth(4, 80)    # Prijs
        self.rd_table.setColumnWidth(5, 80)    # Korting
        self.rd_table.setColumnWidth(6, 100)   # Lijn totaal
        self.rd_table.setColumnWidth(7, 100)   # Magazijn
        self.rd_table.setColumnWidth(8, 100)   # Verzenddatum
        self.rd_table.setColumnWidth(9, 120)   # Vrije tekst

        self.rd_table.horizontalHeader().setStretchLastSection(True)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = SoWidget()
    widget.show()
    sys.exit(app.exec())
