# ui_vta.py
import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QDialog, QFormLayout, QHBoxLayout
)
from PySide6.QtGui import QKeySequence, QShortcut, QColor, QBrush
from PySide6.QtCore import Qt, QEvent

from vta_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT


def format_date(date_str):
    """Formateer een datum yyyy-mm-dd naar dd-mm-yyyy."""
    if not date_str:
        return "-"
    if len(date_str) == 10 and date_str[2] == "/":  # al dd/mm/yyyy
        return date_str
    if len(date_str) >= 10:
        return f"{date_str[8:10]}-{date_str[5:7]}-{date_str[0:4]}"
    return "-"


class LineDetailDialog(QDialog):
    """Popup venster voor lijn-detailinfo."""

    def __init__(self, art_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lijn detail")
        self.resize(400, 300)

        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>Artikelinformatie</b>"))

        field_aliases = [
            ("SuppCatNum", "Leveranciersnummer"),
            ("CardCode", "Leveranciercode"),
            ("Last purchase date", "Laatste aankoopdatum"),
            ("Free stock Algemeen Whs01", "Vrij Algemeen (Whs01)"),
            ("Free stock Antwerpen Whs03", "Vrij Antwerpen (Whs03)"),
        ]

        for key, label in field_aliases:
            value = art_data.get(key, "-")
            if isinstance(value, float):
                value = f"{value:.2f}"
            layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))


class PoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTA")
        self.resize(1200, 800)

        layout = QVBoxLayout(self)

        # --- VTA input ---
        self.po_input = QLineEdit()
        self.po_input.setPlaceholderText("Geef VTA-nummer in")
        layout.addWidget(QLabel("VTA-nummer:"))
        layout.addWidget(self.po_input)

        # --- Ophalen knop ---
        self.fetch_button = QPushButton("Ophalen")
        self.fetch_button.clicked.connect(self.load_data)
        layout.addWidget(self.fetch_button)

        # --- Header info ---
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(QLabel("Header info:"))
        layout.addWidget(self.result_text)

        # --- Tabs ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # === Tab 1: ALL ===
        self.all_tab = QWidget()
        all_layout = QVBoxLayout(self.all_tab)

        # 🔍 Zoekveld
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Zoek artikel / omschrijving:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Typ om te filteren...")
        self.search_input.textChanged.connect(self.filter_all_table)
        search_layout.addWidget(self.search_input)
        all_layout.addLayout(search_layout)

        self.all_table = QTableWidget()
        all_layout.addWidget(self.all_table)
        self.tabs.addTab(self.all_tab, "All")

        # === Tab 2: OPEN ===
        self.open_tab = QWidget()
        open_layout = QVBoxLayout(self.open_tab)
        self.open_table = QTableWidget()
        open_layout.addWidget(self.open_table)
        self.tabs.addTab(self.open_tab, "Open")

        # --- Sneltoetsen ---
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.load_data)
        QShortcut(QKeySequence("Alt+A"), self).activated.connect(lambda: self.tabs.setCurrentWidget(self.all_tab))
        QShortcut(QKeySequence("Alt+O"), self).activated.connect(lambda: self.tabs.setCurrentWidget(self.open_tab))
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.close)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.clear_input)  # ✅ nieuw: wissen + focus

        # Data opslag voor lijn → ART mapping
        self.line_art_map_all = {}
        self.line_art_map_open = {}
        self.all_data_cache = []

        # Dubbelklik-event op artikelcode
        self.all_table.cellDoubleClicked.connect(lambda r, c: self.on_line_double_click(r, c, "all"))
        self.open_table.cellDoubleClicked.connect(lambda r, c: self.on_line_double_click(r, c, "open"))

    # --- Nieuw: invoerveld wissen ---
    def clear_input(self):
        """Leeg het invoerveld en zet de focus erop."""
        self.po_input.clear()
        self.po_input.setFocus()

    # --- Data ophalen ---
    def load_data(self):
        vta_number = self.po_input.text().strip()
        if not vta_number:
            QMessageBox.warning(self, "Fout", "Geef een geldig VTA-nummer in.")
            return

        config_id = API_ENVIRONMENTS[ENVIRONMENT]["vta_config_id"]
        url = "https://api.cgk-group.com/api/datarequest"

        payload = {"ConfigurationID": config_id, "Key": vta_number}
        headers = get_auth_header()

        try:
            response = requests.post(url, headers=headers, json=payload, verify=False)
            response.raise_for_status()
            data = response.json()

            if data.get("IsError"):
                QMessageBox.critical(self, "API Fout", data.get("ErrorMessage"))
                return

            data_list = data.get("Data", [])
            if not isinstance(data_list, list) or not data_list:
                QMessageBox.warning(self, "Fout", "Geen data gevonden voor dit VTA-nummer.")
                return

            self.show_header(data_list[0])
            self.all_data_cache = data_list

            self.show_all_lines(data_list)
            open_lines = [x for x in data_list if x.get("LineStatus") == "O"]
            self.show_open_lines(open_lines)

            if open_lines:
                self.tabs.setCurrentWidget(self.open_tab)
            else:
                self.tabs.setCurrentWidget(self.all_tab)

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Fout", f"Request error: {e}")

    # --- Header tonen ---
    def show_header(self, doc_data):
        lines = [
            f"VTA-nummer: {doc_data.get('VTA nummer', '-')}",
            f"Project: {doc_data.get('Project Number', '-')}",
            f"Projectleider: {doc_data.get('Projectleider', '-')}"
        ]
        self.result_text.setPlainText("\n".join(lines))

    # --- Tabel tonen ---
    def _setup_table(self, table, data_list, line_art_map):
        columns = [
            ("Benodigd op", "Benodigd op"),
            ("LineStatus", "Lijnstatus"),
            ("Artikelnummer", "Artikelnummer"),
            ("Artikel-/serviceomschrijving", "Omschrijving"),
            ("Benodigd", "Benodigd"),
            ("Open", "Open"),
            ("Picked", "Picked"),
            ("Status", "Status"),
            ("In magazijn", "In magazijn"),
            ("Vrij aantal", "Vrij aantal"),
            ("Bevestigd", "Bevestigd"),
            ("Aantal Bev.", "Aantal Bev."),
            ("In bestelling", "In bestelling"),
            ("Aantal in best.", "Aantal in bestelling"),
            ("RealLocation", "Location"),
        ]

        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([label for _, label in columns])
        table.setRowCount(len(data_list))
        line_art_map.clear()

        for row, line in enumerate(data_list):
            open_qty = float(line.get("Open", 0) or 0)
            status_value = str(line.get("Status", "")).upper()

            for col, (key, label) in enumerate(columns):
                value = line.get(key, "")
                if isinstance(value, float):
                    value = f"{value:.2f}"

                item = QTableWidgetItem(str(value))

                # 🎨 Alleen kleur toepassen op kolom "Status"
                if label == "Status":
                    if open_qty > 0:
                        item.setBackground(QBrush(QColor(200, 0, 0)))  # rood
                        item.setForeground(QBrush(QColor(255, 255, 255)))  # wit
                    elif status_value == "COMPLETE":
                        item.setBackground(QBrush(QColor(0, 200, 0)))  # groen
                        item.setForeground(QBrush(QColor(0, 0, 0)))  # zwart

                table.setItem(row, col, item)

            if "ART" in line and line["ART"]:
                line_art_map[row] = line["ART"][0]

        table.resizeColumnsToContents()
        for i, (_, label) in enumerate(columns):
            if label == "Omschrijving" and table.columnWidth(i) < 400:
                table.setColumnWidth(i, 400)
        table.horizontalHeader().setStretchLastSection(True)

    # --- Alle lijnen tonen ---
    def show_all_lines(self, data_list):
        self._setup_table(self.all_table, data_list, self.line_art_map_all)

    # --- Enkel open lijnen tonen ---
    def show_open_lines(self, data_list):
        self._setup_table(self.open_table, data_list, self.line_art_map_open)

    # --- Filterfunctie ---
    def filter_all_table(self):
        query = self.search_input.text().strip().lower()
        if not query:
            filtered = self.all_data_cache
        else:
            filtered = [
                x for x in self.all_data_cache
                if query in str(x.get("Artikelnummer", "")).lower()
                or query in str(x.get("Artikel-/serviceomschrijving", "")).lower()
            ]
        self.show_all_lines(filtered)

    # --- Dubbelklik op lijn ---
    def on_line_double_click(self, row, column, tab_type):
        if column != 2:
            return
        art_data = (
            self.line_art_map_all.get(row)
            if tab_type == "all"
            else self.line_art_map_open.get(row)
        )
        if not art_data:
            QMessageBox.information(self, "Info", "Geen detailinformatie beschikbaar voor deze lijn.")
            return
        dlg = LineDetailDialog(art_data, self)
        dlg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = PoWidget()
    widget.show()
    sys.exit(app.exec())
