# ui_po.py
import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem,
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

class PoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aankooporder")
        self.resize(1200, 800)

        layout = QVBoxLayout(self)

        self.po_input = QLineEdit()
        self.po_input.setPlaceholderText("Geef PO-nummer in")
        layout.addWidget(QLabel("PO-nummer:"))
        layout.addWidget(self.po_input)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Open aankooplijnen", "O")
        self.status_combo.addItem("Closed aankooplijnen", "C")
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_combo)

        self.fetch_button = QPushButton("Ophalen")
        self.fetch_button.clicked.connect(self.load_data)
        layout.addWidget(self.fetch_button)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(QLabel("Header info:"))
        layout.addWidget(self.result_text)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.por1_tab = QWidget()
        por1_layout = QVBoxLayout(self.por1_tab)
        self.por1_table = QTableWidget()
        por1_layout.addWidget(self.por1_table)
        self.tabs.addTab(self.por1_tab, "Aankooporderlijnen")

        self.go_tab = QWidget()
        go_layout = QVBoxLayout(self.go_tab)
        self.go_table = QTableWidget()
        go_layout.addWidget(self.go_table)
        self.tabs.addTab(self.go_tab, "Goederenontvangsten")

        # --- Sneltoetsen toevoegen ---
        QShortcut(QKeySequence(Qt.Key_PageUp), self).activated.connect(self._combo_previous)
        QShortcut(QKeySequence(Qt.Key_PageDown), self).activated.connect(self._combo_next)
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.load_data)
        QShortcut(QKeySequence("Alt+A"), self).activated.connect(lambda: self.tabs.setCurrentWidget(self.por1_tab))
        QShortcut(QKeySequence("Alt+G"), self).activated.connect(lambda: self.tabs.setCurrentWidget(self.go_tab))
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.close)

    def _combo_previous(self):
        current_index = self.status_combo.currentIndex()
        if current_index > 0:
            self.status_combo.setCurrentIndex(current_index - 1)

    def _combo_next(self):
        current_index = self.status_combo.currentIndex()
        if current_index < self.status_combo.count() - 1:
            self.status_combo.setCurrentIndex(current_index + 1)

    def load_data(self):
        po_number = self.po_input.text().strip()
        status = self.status_combo.currentData()

        if not po_number:
            QMessageBox.warning(self, "Fout", "Geef een geldig PO-nummer in.")
            return

        config_id = API_ENVIRONMENTS[ENVIRONMENT]["po_configP_id"]
        url = "https://api.cgk-group.com/api/datarequest"

        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {
                "@po": po_number,
                "@status": status.lower()
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

            doc_data = data.get("Data", {})
            self.show_header(doc_data)
            self.show_por1(doc_data.get("POR1", []))
            self.show_go(doc_data.get("GO", []))

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Fout", f"Request error: {e}")

    def show_header(self, doc_data):
        lines = []
        lines.append(f"Aankooporder -nummer: {doc_data.get('DocNum')}")
        lines.append(f"Geannuleerd: {doc_data.get('CANCELED')}")
        lines.append(f"Status: {doc_data.get('DocStatus')}")
        lines.append(f"Datum: {format_date(doc_data.get('DocDate'))}")
        lines.append(f"Vervaldatum: {format_date(doc_data.get('DocDueDate'))}")
        lines.append(f"Bevestigd: {doc_data.get('Confirmed')}")
        lines.append(f"Leveranciernaam: {doc_data.get('CardName')}")
        lines.append(f"BTW-nummer: {doc_data.get('LicTradNum')}")
        lines.append(f"Ref1: {doc_data.get('Ref1')}")
        lines.append(f"Opmerkingen: {doc_data.get('Comments')}")
        lines.append(f"Totaalbedrag: {doc_data.get('DocTotal')} {doc_data.get('DocCur')}")
        lines.append(f"BTW-bedrag: {doc_data.get('VatSum')}")

        self.result_text.setPlainText("\n".join(lines))

    def show_por1(self, por1_list):
        labels_map = load_field_labels("po_por1")
        headers = [
            labels_map.get("LineNum", "Regel"),
            labels_map.get("ItemCode", "Artikelcode"),
            labels_map.get("VendorNum", "VendorNr"),
            labels_map.get("Dscription", "Omschrijving"),
            labels_map.get("Quantity", "Aantal"),
            labels_map.get("Price", "Prijs"),
            labels_map.get("WhsName", "Magazijn"),
            labels_map.get("DocDate", "Datum"),
            labels_map.get("ShipDate", "Verzenddatum")
        ]

        self.por1_table.setColumnCount(len(headers))
        self.por1_table.setHorizontalHeaderLabels(headers)
        self.por1_table.setRowCount(len(por1_list))

        header = self.por1_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        for row, line in enumerate(por1_list):
            self.por1_table.setItem(row, 0, QTableWidgetItem(str(line.get("LineNum"))))
            self.por1_table.setItem(row, 1, QTableWidgetItem(line.get("ItemCode", "")))
            self.por1_table.setItem(row, 2, QTableWidgetItem(line.get("VendorNum", "")))
            self.por1_table.setItem(row, 3, QTableWidgetItem(line.get("Dscription", "")))
            self.por1_table.setItem(row, 4, QTableWidgetItem(str(line.get("Quantity"))))
            self.por1_table.setItem(row, 5, QTableWidgetItem(str(line.get("Price"))))
            self.por1_table.setItem(row, 6, QTableWidgetItem(line.get("WhsName", "")))
            self.por1_table.setItem(row, 7, QTableWidgetItem(format_date(line.get("DocDate"))))
            self.por1_table.setItem(row, 8, QTableWidgetItem(format_date(line.get("ShipDate"))))

        self.por1_table.setColumnWidth(0, 60)
        self.por1_table.setColumnWidth(1, 120)
        self.por1_table.setColumnWidth(2, 100)
        self.por1_table.setColumnWidth(3, 300)
        self.por1_table.setColumnWidth(4, 70)
        self.por1_table.setColumnWidth(5, 80)
        self.por1_table.setColumnWidth(6, 100)
        self.por1_table.setColumnWidth(7, 100)
        self.por1_table.setColumnWidth(8, 120)

        self.por1_table.horizontalHeader().setStretchLastSection(True)

    def show_go(self, go_list):
        labels_map = load_field_labels("po_go")
        headers = [
            labels_map.get("GO_DocNum", "GO Nr"),
            labels_map.get("GO_Date", "Datum"),
            labels_map.get("GOL_ItemCode", "Artikelcode"),
            labels_map.get("VendorNum", "VendorNr"),
            labels_map.get("GOL_Dscription", "Omschrijving"),
            labels_map.get("GOL_Quantity", "Aantal"),
            labels_map.get("GOL_OpenQty", "Open qty"),
            labels_map.get("GOL_LineStatus", "Status")
        ]

        self.go_table.setColumnCount(len(headers))
        self.go_table.setHorizontalHeaderLabels(headers)
        self.go_table.setRowCount(len(go_list))

        header_go = self.go_table.horizontalHeader()
        header_go.setSectionResizeMode(QHeaderView.Interactive)
        header_go.setSectionResizeMode(4, QHeaderView.Stretch)

        for row, go in enumerate(go_list):
            self.go_table.setItem(row, 0, QTableWidgetItem(str(go.get("GO_DocNum"))))
            self.go_table.setItem(row, 1, QTableWidgetItem(format_date(go.get("GO_Date"))))
            self.go_table.setItem(row, 2, QTableWidgetItem(go.get("GOL_ItemCode", "")))
            self.go_table.setItem(row, 3, QTableWidgetItem(go.get("VendorNum", "")))
            self.go_table.setItem(row, 4, QTableWidgetItem(go.get("GOL_Dscription", "")))
            self.go_table.setItem(row, 5, QTableWidgetItem(str(go.get("GOL_Quantity"))))
            self.go_table.setItem(row, 6, QTableWidgetItem(str(go.get("GOL_OpenQty"))))
            self.go_table.setItem(row, 7, QTableWidgetItem(go.get("GOL_LineStatus", "")))

        self.go_table.setColumnWidth(0, 80)
        self.go_table.setColumnWidth(1, 100)
        self.go_table.setColumnWidth(2, 120)
        self.go_table.setColumnWidth(3, 100)
        self.go_table.setColumnWidth(4, 300)
        self.go_table.setColumnWidth(5, 80)
        self.go_table.setColumnWidth(6, 90)
        self.go_table.setColumnWidth(7, 100)

        self.go_table.horizontalHeader().setStretchLastSection(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = PoWidget()
    widget.show()
    sys.exit(app.exec())
