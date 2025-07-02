# ui_lastpurch.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from ui_po import PoWidget
from settings import load_field_labels

class LastPurchTab(QWidget):
    def __init__(self, data):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()

        # Labels ophalen
        labels_map = load_field_labels("last_purch")
        headers = list(labels_map.keys())
        mapped_headers = [labels_map.get(h, h) for h in headers]

        if data:
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(mapped_headers)
            for row, record in enumerate(data):
                for col, key in enumerate(headers):
                    val = str(record.get(key, ""))
                    item = QTableWidgetItem(val)
                    item.setToolTip(val)
                    self.table.setItem(row, col, item)
        else:
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Informatie"])
            self.table.setItem(0, 0, QTableWidgetItem("❌ Geen laatste aankoop data beschikbaar."))

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.table.cellDoubleClicked.connect(self.open_po_widget)

    def open_po_widget(self, row, col):
        docnr_col = None
        for i in range(self.table.columnCount()):
            if self.table.horizontalHeaderItem(i).text() == "DocNr":
                docnr_col = i
                break

        if docnr_col is None:
            return

        po_number = self.table.item(row, docnr_col).text()
        if not po_number:
            return

        self.po_widget = PoWidget()
        self.po_widget.po_input.setText(po_number)
        self.po_widget.load_data()

        self.po_widget.setWindowFlags(self.po_widget.windowFlags() | Qt.WindowStaysOnTopHint)
        self.po_widget.show()
        self.po_widget.raise_()
        self.po_widget.activateWindow()
